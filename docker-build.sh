#!/bin/bash

# Script ottimizzato per building Docker su WSL2/Linux
# Optimized Docker build script for WSL2/Linux
#
# Caratteristiche / Features:
# - Cache ottimizzato per dependencies Python/Node.js
# - Parallelo building dove possibile
# - Cleanup automatico
# - Verifica prerequisiti

set -e  # Exit on error

# Colori per output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Configurazione
PROJECT_NAME="tutor-ai"
BACKEND_DIR="backend"
FRONTEND_DIR="frontend"
BUILD_CACHE_DIR="$HOME/.docker-build-cache/$PROJECT_NAME"

# Creazione directory cache
mkdir -p "$BUILD_CACHE_DIR"

# Funzione per verificare prerequisiti
check_prerequisites() {
    log_info "Verifica prerequisiti..."

    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker non è installato. Installare Docker prima di continuare."
        exit 1
    fi

    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose non è installato. Installare Docker Compose prima di continuare."
        exit 1
    fi

    # Check if Docker daemon is running
    if ! docker info &> /dev/null; then
        log_error "Docker daemon non è in esecuzione. Avviare Docker e riprovare."
        exit 1
    fi

    log_success "Prerequisiti verificati"
}

# Funzione per ottimizzare Docker per WSL2
optimize_docker_wsl2() {
    log_info "Ottimizzazione configurazione Docker per WSL2..."

    # Imposta .dockerenv in modo appropriato per WSL2
    export DOCKER_BUILDKIT=1
    export COMPOSE_DOCKER_CLI_BUILD=1

    # Configura cache directory per build
    export DOCKER_BUILDKIT_CACHE_DIR="$BUILD_CACHE_DIR"

    log_success "Docker ottimizzato per WSL2"
}

# Funzione per pulire vecchi container e immagini (opzionale)
cleanup_docker() {
    log_info "Pulizia container e immagini non utilizzate..."

    # Rimuovi container fermati
    if [ "$(docker ps -a -q)" ]; then
        docker container prune -f
    fi

    # Rimuovi immagini dangling
    if [ "$(docker images -f "dangling=true" -q)" ]; then
        docker image prune -f
    fi

    log_success "Pulizia completata"
}

# Funzione per creare cache per dependencies
create_build_cache() {
    log_info "Preparazione cache per dependencies..."

    # Cache directory per Python packages
    mkdir -p "$BUILD_CACHE_DIR/python-cache"
    mkdir -p "$BUILD_CACHE_DIR/node-cache"

    # Crea file di cache marker
    echo "$(date)" > "$BUILD_CACHE_DIR/.last_build"

    log_success "Cache preparata"
}

# Funzione per build backend con cache ottimizzata
build_backend() {
    log_info "Building backend con cache ottimizzata e persistente..."
    log_info "Questa operazione potrebbe richiedere alcuni minuti per il download delle dipendenze..."

    cd "$BACKEND_DIR"

    # Crea builder con cache persistente se non esiste
    if ! docker buildx ls | grep -q "tutor-ai-builder"; then
        log_info "Creazione builder con cache persistente..."
        docker buildx create --name tutor-ai-builder --use --bootstrap --driver=docker-container \
            --buildkitd-flags '--allow-insecure-entitlement security.insecure'
    fi

    # Usa builder con cache persistente
    docker buildx use tutor-ai-builder

    # Build con cache persistente su filesystem locale
    echo -e "\n${BLUE}=== INIZIO BUILD BACKEND ===${NC}"
    docker buildx build \
        --build-arg BUILDKIT_INLINE_CACHE=1 \
        --cache-from type=local,src="$BUILD_CACHE_DIR/backend-cache" \
        --cache-to type=local,dest="$BUILD_CACHE_DIR/backend-cache",mode=max \
        --tag "$PROJECT_NAME-backend:latest" \
        --tag "$PROJECT_NAME-backend:cache" \
        --progress=plain \
        --load \
        -f Dockerfile \
        . 2>&1 | while IFS= read -r line; do
            if [[ $line == *"Downloading"* ]] || [[ $line == *"Collecting"* ]] || [[ $line == *"Installing"* ]]; then
                echo -e "${BLUE}[PROGRESS]${NC} $line"
            elif [[ $line == *"Successfully built"* ]] || [[ $line == *"Successfully tagged"* ]]; then
                echo -e "${GREEN}[SUCCESS]${NC} $line"
            elif [[ $line == *"ERROR"* ]]; then
                echo -e "${RED}[ERROR]${NC} $line"
            elif [[ $line == *"WARNING"* ]]; then
                echo -e "${YELLOW}[WARNING]${NC} $line"
            else
                echo "$line"
            fi
        done
    echo -e "\n${GREEN}=== BUILD BACKEND COMPLETATO ===${NC}"

    cd ..
    log_success "Backend build completato con cache salvata in $BUILD_CACHE_DIR/backend-cache"
}

# Funzione per build frontend con cache ottimizzata
build_frontend() {
    log_info "Building frontend con cache ottimizzata e persistente..."

    cd "$FRONTEND_DIR"

    # Prepara cache node_modules
    if [ -d "node_modules" ]; then
        log_info "Caching node_modules esistenti..."
        cp -r node_modules "$BUILD_CACHE_DIR/node-cache/" 2>/dev/null || true
    fi

    # Usa builder con cache persistente
    docker buildx use tutor-ai-builder

    # Build con cache persistente su filesystem locale
    echo -e "\n${BLUE}=== INIZIO BUILD FRONTEND ===${NC}"
    docker buildx build \
        --build-arg BUILDKIT_INLINE_CACHE=1 \
        --build-arg NODE_ENV=production \
        --cache-from type=local,src="$BUILD_CACHE_DIR/frontend-cache" \
        --cache-to type=local,dest="$BUILD_CACHE_DIR/frontend-cache",mode=max \
        --tag "$PROJECT_NAME-frontend:latest" \
        --tag "$PROJECT_NAME-frontend:cache" \
        --progress=plain \
        --load \
        -f Dockerfile \
        . 2>&1 | while IFS= read -r line; do
            if [[ $line == *"Downloading"* ]] || [[ $line == *"npm"* ]] || [[ $line == *"yarn"* ]] || [[ $line == *"node_modules"* ]]; then
                echo -e "${BLUE}[PROGRESS]${NC} $line"
            elif [[ $line == *"Successfully built"* ]] || [[ $line == *"Successfully tagged"* ]]; then
                echo -e "${GREEN}[SUCCESS]${NC} $line"
            elif [[ $line == *"ERROR"* ]]; then
                echo -e "${RED}[ERROR]${NC} $line"
            elif [[ $line == *"WARNING"* ]]; then
                echo -e "${YELLOW}[WARNING]${NC} $line"
            else
                echo "$line"
            fi
        done
    echo -e "\n${GREEN}=== BUILD FRONTEND COMPLETATO ===${NC}"

    cd ..
    log_success "Frontend build completato con cache salvata in $BUILD_CACHE_DIR/frontend-cache"
}

# Funzione per build parallelo
build_parallel() {
    log_info "Avvio build parallelo backend e frontend..."
    echo -e "\n${YELLOW}=== BUILD PARALLELO IN CORSO ===${NC}"
    echo -e "${BLUE}▶ Backend e Frontend vengono costruiti simultaneamente${NC}"
    echo -e "${BLUE}▶ I messaggi di entrambi i build appariranno qui sotto${NC}"
    echo ""

    # Build in background
    build_backend &
    BACKEND_PID=$!

    build_frontend &
    FRONTEND_PID=$!

    # Monitoraggio progresso build parallelo
    echo -e "${YELLOW}=== ATTESA COMPLETAMENTO BUILD ===${NC}"

    # Controlla periodicamente lo stato dei processi
    while kill -0 $BACKEND_PID 2>/dev/null || kill -0 $FRONTEND_PID 2>/dev/null; do
        sleep 2
        local BACKEND_RUNNING=false
        local FRONTEND_RUNNING=false

        if kill -0 $BACKEND_PID 2>/dev/null; then
            BACKEND_RUNNING=true
        fi

        if kill -0 $FRONTEND_PID 2>/dev/null; then
            FRONTEND_RUNNING=true
        fi

        echo -e "\r${BLUE}[PROGRESS]${NC} Stato: Backend[$([ "$BACKEND_RUNNING" = true ] && echo "In corso" || echo "Completato")] | Frontend[$([ "$FRONTEND_RUNNING" = true ] && echo "In corso" || echo "Completato")]" | tr -d '\n'
    done
    echo ""

    # Attendi completamento effettivo e raccogli stati
    local BACKEND_STATUS=0
    local FRONTEND_STATUS=0

    wait $BACKEND_PID
    BACKEND_STATUS=$?
    if [ $BACKEND_STATUS -eq 0 ]; then
        echo -e "\n${GREEN}✓ Backend build completato con successo${NC}"
    else
        echo -e "\n${RED}✗ Backend build fallito (exit code: $BACKEND_STATUS)${NC}"
    fi

    wait $FRONTEND_PID
    FRONTEND_STATUS=$?
    if [ $FRONTEND_STATUS -eq 0 ]; then
        echo -e "${GREEN}✓ Frontend build completato con successo${NC}"
    else
        echo -e "${RED}✗ Frontend build fallito (exit code: $FRONTEND_STATUS)${NC}"
    fi

    if [ $BACKEND_STATUS -eq 0 ] && [ $FRONTEND_STATUS -eq 0 ]; then
        echo -e "\n${GREEN}=== BUILD PARALLELO COMPLETATO CON SUCCESSO ===${NC}"
    else
        echo -e "\n${RED}=== BUILD PARALLELO COMPLETATO CON ERRORI ===${NC}"
        return 1
    fi
}

# Funzione per verificare build
verify_build() {
    log_info "Verifica build completato..."

    # Verifica immagini
    if ! docker image inspect "$PROJECT_NAME-backend:latest" &> /dev/null; then
        log_error "Backend image non trovata"
        return 1
    fi

    if ! docker image inspect "$PROJECT_NAME-frontend:latest" &> /dev/null; then
        log_error "Frontend image non trovata"
        return 1
    fi

    log_success "Verifica build completata con successo"
}

# Funzione per mostrare statistiche cache
show_cache_stats() {
    log_info "Statistiche cache Docker:"

    if [ -d "$BUILD_CACHE_DIR" ]; then
        local CACHE_SIZE=$(du -sh "$BUILD_CACHE_DIR" 2>/dev/null | cut -f1)
        echo -e "  Cache directory: ${GREEN}$BUILD_CACHE_DIR${NC}"
        echo -e "  Cache size: ${GREEN}${CACHE_SIZE}${NC}"

        if [ -d "$BUILD_CACHE_DIR/backend-cache" ]; then
            local BACKEND_SIZE=$(du -sh "$BUILD_CACHE_DIR/backend-cache" 2>/dev/null | cut -f1)
            echo -e "  Backend cache: ${GREEN}${BACKEND_SIZE}${NC}"
        fi

        if [ -d "$BUILD_CACHE_DIR/frontend-cache" ]; then
            local FRONTEND_SIZE=$(du -sh "$BUILD_CACHE_DIR/frontend-cache" 2>/dev/null | cut -f1)
            echo -e "  Frontend cache: ${GREEN}${FRONTEND_SIZE}${NC}"
        fi

        if [ -d "$BUILD_CACHE_DIR/node-cache" ]; then
            local NODE_SIZE=$(du -sh "$BUILD_CACHE_DIR/node-cache" 2>/dev/null | cut -f1)
            echo -e "  Node cache: ${GREEN}${NODE_SIZE}${NC}"
        fi
    else
        echo -e "  ${YELLOW}Nessuna cache trovata${NC}"
    fi
}

# Funzione per show help
show_help() {
    echo "Script Docker Build Ottimizzato per $PROJECT_NAME"
    echo ""
    echo "Uso: $0 [OPZIONI]"
    echo ""
    echo "Opzioni:"
    echo "  -h, --help     Mostra questo help"
    echo "  -c, --cleanup  Esegue solo pulizia Docker"
    echo "  -b, --backend  Build solo backend"
    echo "  -f, --frontend Build solo frontend"
    echo "  -p, --parallel Build parallelo (default)"
    echo "  --no-cache     Build senza cache"
    echo "  --force        Forza rebuild completo"
    echo "  --cache-stats  Mostra statistiche cache"
    echo ""
    echo "Esempi:"
    echo "  $0                # Build parallelo completo"
    echo "  $0 --backend      # Solo backend"
    echo "  $0 --cleanup      # Solo pulizia"
    echo "  $0 --force        # Force rebuild completo"
    echo "  $0 --cache-stats  # Statistiche cache"
}

# Funzione principale
main() {
    local BUILD_BACKEND=true
    local BUILD_FRONTEND=true
    local CLEANUP_ONLY=false
    local USE_CACHE=true
    local FORCE_REBUILD=false
    local SHOW_CACHE_STATS=false

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -c|--cleanup)
                CLEANUP_ONLY=true
                shift
                ;;
            -b|--backend)
                BUILD_FRONTEND=false
                shift
                ;;
            -f|--frontend)
                BUILD_BACKEND=false
                shift
                ;;
            -p|--parallel)
                # Default behavior
                shift
                ;;
            --no-cache)
                USE_CACHE=false
                shift
                ;;
            --force)
                FORCE_REBUILD=true
                shift
                ;;
            --cache-stats)
                SHOW_CACHE_STATS=true
                shift
                ;;
            *)
                log_error "Opzione sconosciuta: $1"
                show_help
                exit 1
                ;;
        esac
    done

    log_info "Inizio Docker build per $PROJECT_NAME"

    # Verifica prerequisiti
    check_prerequisites

    # Show cache stats se richiesto
    if [ "$SHOW_CACHE_STATS" = true ]; then
        show_cache_stats
        exit 0
    fi

    # Cleanup solo se richiesto
    if [ "$CLEANUP_ONLY" = true ]; then
        cleanup_docker
        log_success "Cleanup completato"
        exit 0
    fi

    # Ottimizza Docker per WSL2
    optimize_docker_wsl2

    # Cleanup preliminare (se force rebuild)
    if [ "$FORCE_REBUILD" = true ]; then
        log_warning "Force rebuild attivato - pulizia container e immagini..."
        cleanup_docker
    fi

    # Prepara cache
    if [ "$USE_CACHE" = true ]; then
        create_build_cache
    fi

    # Esegui build
    local START_TIME=$(date +%s)

    if [ "$BUILD_BACKEND" = true ] && [ "$BUILD_FRONTEND" = true ]; then
        build_parallel
    elif [ "$BUILD_BACKEND" = true ]; then
        build_backend
    elif [ "$BUILD_FRONTEND" = true ]; then
        build_frontend
    fi

    # Verifica build
    verify_build

    local END_TIME=$(date +%s)
    local DURATION=$((END_TIME - START_TIME))

    log_success "Build completato in ${DURATION} secondi"

    # Mostra informazioni sulle immagini create
    echo ""
    log_info "Immagini create:"
    docker images | grep "$PROJECT_NAME" || true

    # Mostra riepilogo finale dettagliato
    echo ""
    echo -e "${GREEN}=== RIEPILOGO FINALE ===${NC}"

    # Verifica dimensioni immagini
    local BACKEND_SIZE=$(docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}" | grep "$PROJECT_NAME-backend" | grep "latest" | awk '{print $3}' | head -1)
    local FRONTEND_SIZE=$(docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}" | grep "$PROJECT_NAME-frontend" | grep "latest" | awk '{print $3}' | head -1)

    echo -e "${BLUE}▶ Backend:${NC} $PROJECT_NAME-backend:latest ${GREEN}($BACKEND_SIZE)${NC}"
    echo -e "${BLUE}▶ Frontend:${NC} $PROJECT_NAME-frontend:latest ${GREEN}($FRONTEND_SIZE)${NC}"

    # Mostra cache utilizzata
    if [ -d "$BUILD_CACHE_DIR" ]; then
        local CACHE_SIZE=$(du -sh "$BUILD_CACHE_DIR" 2>/dev/null | cut -f1)
        echo -e "${BLUE}▶ Cache utilizzata:${NC} ${GREEN}$CACHE_SIZE${NC} in $BUILD_CACHE_DIR"
    fi

    echo ""
    echo -e "${GREEN}✓ Build completato! Ora puoi eseguire:${NC}"
    echo -e "   ${YELLOW}docker-compose up${NC}     # Avvia i servizi"
    echo -e "   ${YELLOW}docker-compose up -d${NC}  # Avvia in background"
    echo ""
}

# Esegui main function con tutti gli argomenti
main "$@"