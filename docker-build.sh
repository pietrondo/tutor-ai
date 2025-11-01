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
    log_info "Building backend con cache ottimizzata..."

    cd "$BACKEND_DIR"

    # Usa BuildKit per cache ottimizzata
    DOCKER_BUILDKIT=1 docker build \
        --build-arg BUILDKIT_INLINE_CACHE=1 \
        --cache-from "$PROJECT_NAME-backend:cache" \
        --cache-to "$PROJECT_NAME-backend:cache" \
        --tag "$PROJECT_NAME-backend:latest" \
        --tag "$PROJECT_NAME-backend:cache" \
        -f Dockerfile \
        .

    cd ..
    log_success "Backend build completato"
}

# Funzione per build frontend con cache ottimizzata
build_frontend() {
    log_info "Building frontend con cache ottimizzata..."

    cd "$FRONTEND_DIR"

    # Prepara cache node_modules
    if [ -d "node_modules" ]; then
        log_info "Caching node_modules esistenti..."
        cp -r node_modules "$BUILD_CACHE_DIR/node-cache/" 2>/dev/null || true
    fi

    # Usa BuildKit per cache ottimizzata
    DOCKER_BUILDKIT=1 docker build \
        --build-arg BUILDKIT_INLINE_CACHE=1 \
        --build-arg NODE_ENV=production \
        --cache-from "$PROJECT_NAME-frontend:cache" \
        --cache-to "$PROJECT_NAME-frontend:cache" \
        --tag "$PROJECT_NAME-frontend:latest" \
        --tag "$PROJECT_NAME-frontend:cache" \
        -f Dockerfile \
        .

    cd ..
    log_success "Frontend build completato"
}

# Funzione per build parallelo
build_parallel() {
    log_info "Avvio build parallelo backend e frontend..."

    # Build in background
    build_backend &
    BACKEND_PID=$!

    build_frontend &
    FRONTEND_PID=$!

    # Attendi completamento
    wait $BACKEND_PID
    log_success "Backend build completato"

    wait $FRONTEND_PID
    log_success "Frontend build completato"

    log_success "Build parallelo completato"
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
    echo ""
    echo "Esempi:"
    echo "  $0                # Build parallelo completo"
    echo "  $0 --backend      # Solo backend"
    echo "  $0 --cleanup      # Solo pulizia"
    echo "  $0 --force        # Force rebuild completo"
}

# Funzione principale
main() {
    local BUILD_BACKEND=true
    local BUILD_FRONTEND=true
    local CLEANUP_ONLY=false
    local USE_CACHE=true
    local FORCE_REBUILD=false

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
}

# Esegui main function con tutti gli argomenti
main "$@"