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
SCRIPT_START=$(date +%s)

# Colori per output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Utility - timestamp
timestamp() {
    date "+%Y-%m-%d %H:%M:%S"
}

# Logging functions
log_info() {
    echo -e "$(timestamp) ${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "$(timestamp) ${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "$(timestamp) ${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "$(timestamp) ${RED}[ERROR]${NC} $1"
}

# Configurazione
PROJECT_NAME="tutor-ai"
BACKEND_DIR="backend"
FRONTEND_DIR="frontend"
BUILD_CACHE_DIR="$HOME/.docker-build-cache/$PROJECT_NAME"
BUILDX_BUILDER_NAME="tutor-ai-builder"
BASE_IMAGES=("python:3.11-slim" "node:20-alpine")
STATUS_INTERVAL=${STATUS_INTERVAL:-30}
HEARTBEAT_INTERVAL=${HEARTBEAT_INTERVAL:-300}
USE_NODE_CACHE=${USE_NODE_CACHE:-0}

BACKEND_STATUS_FILE="$BUILD_CACHE_DIR/backend.status"
FRONTEND_STATUS_FILE="$BUILD_CACHE_DIR/frontend.status"

format_duration() {
    local total_seconds=$1
    local hours=$((total_seconds / 3600))
    local minutes=$(((total_seconds % 3600) / 60))
    local seconds=$((total_seconds % 60))

    if [ $hours -gt 0 ]; then
        printf "%02dh %02dm %02ds" "$hours" "$minutes" "$seconds"
    elif [ $minutes -gt 0 ]; then
        printf "%02dm %02ds" "$minutes" "$seconds"
    else
        printf "%02ds" "$seconds"
    fi
}

write_status() {
    local component=$1
    local stage=$2
    local file="$BACKEND_STATUS_FILE"
    if [ "$component" = "frontend" ]; then
        file="$FRONTEND_STATUS_FILE"
    fi
    printf "%s" "$stage" > "$file"
}

read_status() {
    local component=$1
    local file="$BACKEND_STATUS_FILE"
    if [ "$component" = "frontend" ]; then
        file="$FRONTEND_STATUS_FILE"
    fi
    if [ -f "$file" ]; then
        cat "$file"
    else
        printf "unknown"
    fi
}

describe_stage() {
    case $1 in
        queued) echo "in coda" ;;
        starting) echo "avvio" ;;
        copy_node_modules) echo "copia cache node_modules" ;;
        docker_build) echo "docker build" ;;
        completed) echo "completato" ;;
        failed) echo "errore" ;;
        *) echo "$1" ;;
    esac
}

# Creazione directory cache
rm -f "$BACKEND_STATUS_FILE" "$FRONTEND_STATUS_FILE"
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

    # Ottimizzazioni performance per WSL2
    export DOCKER_BUILDKIT_CACHE_DIR="$BUILD_CACHE_DIR"
    export DOCKER_CLI_EXPERIMENTAL=enabled

    # Impostazioni per ridurre I/O su WSL2
    export DOCKER_BUILDKIT_STEP_TIMEOUT=600
    export DOCKER_BUILDKIT_HISTORY_MAX=5

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
    mkdir -p "$BUILD_CACHE_DIR/backend-cache"
    mkdir -p "$BUILD_CACHE_DIR/frontend-cache"

    # Crea file di cache marker
    echo "$(date)" > "$BUILD_CACHE_DIR/.last_build"

    log_success "Cache preparata"
}

ensure_buildx_builder() {
    if ! docker buildx version >/dev/null 2>&1; then
        log_warning "docker buildx non disponibile - uso il builder classico di Docker."
        return 1
    fi

    if docker buildx inspect "$BUILDX_BUILDER_NAME" >/dev/null 2>&1; then
        log_info "Riutilizzo builder cache $BUILDX_BUILDER_NAME"
        docker buildx use "$BUILDX_BUILDER_NAME" >/dev/null 2>&1 || true
        docker buildx inspect "$BUILDX_BUILDER_NAME" --bootstrap >/dev/null 2>&1 || true
        return 0
    fi

    log_info "Creazione builder dedicato con driver docker-container e cache persistente..."
    docker buildx create \
        --name "$BUILDX_BUILDER_NAME" \
        --driver docker-container \
        --driver-opt network=host \
        --driver-opt image=moby/buildkit:rootless \
        --use >/dev/null

    docker buildx inspect "$BUILDX_BUILDER_NAME" --bootstrap >/dev/null
}

warm_base_images() {
    log_info "Pre-pull immagini base per ridurre cache miss..."
    for image in "${BASE_IMAGES[@]}"; do
        if docker image inspect "$image" >/dev/null 2>&1; then
            continue
        fi

        log_info "Download immagine base $image..."
        if docker pull "$image" >/dev/null 2>&1; then
            log_success "Immagine $image pronta nella cache locale"
        else
            log_warning "Impossibile scaricare $image, proseguo comunque"
        fi
    done
}

BACKEND_SNAPSHOT_FILE="$BUILD_CACHE_DIR/backend.snapshot"
FRONTEND_SNAPSHOT_FILE="$BUILD_CACHE_DIR/frontend.snapshot"
BACKEND_EXCLUDES=( "./venv/*" "./.venv/*" "./__pycache__/*" "./.mypy_cache/*" "./.pytest_cache/*" "./data/*" )
FRONTEND_EXCLUDES=( "./node_modules/*" "./.next/*" "./dist/*" "./out/*" "./.turbo/*" )
NEXT_BACKEND_HASH=""
NEXT_FRONTEND_HASH=""
SMART_SKIP_BUILD=false

calculate_directory_hash() {
    local dir="$1"
    shift
    local excludes=("$@")

    log_info "Calcolo hash per directory $dir..."
    if [ ! -d "$dir" ]; then
        echo ""
        return
    fi

    pushd "$dir" > /dev/null || return 1

    local find_cmd=(find . -type f)
    for pattern in "${excludes[@]}"; do
        find_cmd+=(-not -path "$pattern")
    done

    local tmp_list
    tmp_list=$(mktemp)

    "${find_cmd[@]}" -print0 | sort -z > "$tmp_list"

    if [ ! -s "$tmp_list" ]; then
        rm -f "$tmp_list"
        popd > /dev/null
        echo "empty"
        return
    fi

    local hash_value
    hash_value=$(
        while IFS= read -r -d '' file; do
            sha1sum "$file"
        done < "$tmp_list" | sha1sum | awk '{print $1}'
    )

    rm -f "$tmp_list"
    popd > /dev/null
    echo "$hash_value"
}

detect_smart_targets() {
    log_info "Modalità smart build attiva: rilevamento modifiche nei servizi..."

    SMART_SKIP_BUILD=false
    NEXT_BACKEND_HASH=""
    NEXT_FRONTEND_HASH=""

    local backend_hash frontend_hash
    backend_hash=$(calculate_directory_hash "$BACKEND_DIR" "${BACKEND_EXCLUDES[@]}")
    frontend_hash=$(calculate_directory_hash "$FRONTEND_DIR" "${FRONTEND_EXCLUDES[@]}")

    local previous_backend_hash=""
    if [ -f "$BACKEND_SNAPSHOT_FILE" ]; then
        previous_backend_hash=$(cat "$BACKEND_SNAPSHOT_FILE")
    fi

    local previous_frontend_hash=""
    if [ -f "$FRONTEND_SNAPSHOT_FILE" ]; then
        previous_frontend_hash=$(cat "$FRONTEND_SNAPSHOT_FILE")
    fi

    BUILD_BACKEND=false
    BUILD_FRONTEND=false

    if [ -z "$backend_hash" ] || [ "$backend_hash" = "empty" ]; then
        log_warning "Impossibile calcolare hash backend - forzo rebuild backend."
        BUILD_BACKEND=true
    elif [ -z "$previous_backend_hash" ]; then
        log_info "Nessun snapshot backend precedente trovato: eseguo build backend."
        BUILD_BACKEND=true
    elif [ "$backend_hash" != "$previous_backend_hash" ]; then
        log_info "Modifiche backend rilevate rispetto all'ultima build."
        BUILD_BACKEND=true
    else
        log_info "Backend invariato rispetto all'ultima build - salto rebuild."
    fi

    if [ "$BUILD_BACKEND" = true ]; then
        NEXT_BACKEND_HASH="$backend_hash"
    fi

    if [ -z "$frontend_hash" ] || [ "$frontend_hash" = "empty" ]; then
        log_warning "Impossibile calcolare hash frontend - forzo rebuild frontend."
        BUILD_FRONTEND=true
    elif [ -z "$previous_frontend_hash" ]; then
        log_info "Nessun snapshot frontend precedente trovato: eseguo build frontend."
        BUILD_FRONTEND=true
    elif [ "$frontend_hash" != "$previous_frontend_hash" ]; then
        log_info "Modifiche frontend rilevate rispetto all'ultima build."
        BUILD_FRONTEND=true
    else
        log_info "Frontend invariato rispetto all'ultima build - salto rebuild."
    fi

    if [ "$BUILD_BACKEND" = false ] && [ "$BUILD_FRONTEND" = false ]; then
        SMART_SKIP_BUILD=true
    fi
}

update_snapshot() {
    local component=$1
    local hash_value=$2
    local snapshot_file="$BUILD_CACHE_DIR/${component}.snapshot"

    if [ -z "$hash_value" ]; then
        if [ "$component" = "backend" ]; then
            hash_value=$(calculate_directory_hash "$BACKEND_DIR" "${BACKEND_EXCLUDES[@]}")
        else
            hash_value=$(calculate_directory_hash "$FRONTEND_DIR" "${FRONTEND_EXCLUDES[@]}")
        fi
    fi

    if [ -n "$hash_value" ]; then
        echo "$hash_value" > "$snapshot_file"
    fi
}

# Funzione per build backend con cache ottimizzata
build_backend() {
    log_info "Building backend con cache ottimizzata e persistente..."
    log_info "Questa operazione potrebbe richiedere alcuni minuti per il download delle dipendenze..."
    local backend_start=$(date +%s)

    write_status backend starting
    trap 'write_status backend failed' ERR

    pushd "$BACKEND_DIR" > /dev/null

    local cache_flags=()
    if [ "$USE_CACHE" = true ]; then
        cache_flags+=(
            --cache-from "type=local,src=$BUILD_CACHE_DIR/backend-cache"
            --cache-to "type=local,dest=$BUILD_CACHE_DIR/backend-cache,mode=max"
        )
    else
        cache_flags+=(--no-cache)
    fi

    # Build con cache ottimizzata per WSL2
    echo -e "\n${BLUE}=== INIZIO BUILD BACKEND ===${NC}"
    docker buildx build \
        --builder "$BUILDX_BUILDER_NAME" \
        --build-arg BUILDKIT_INLINE_CACHE=1 \
        "${cache_flags[@]}" \
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

    popd > /dev/null
    local backend_end=$(date +%s)
    local backend_duration=$((backend_end - backend_start))
    write_status backend completed
    trap - ERR
    log_success "Backend build completato in ${backend_duration}s (cache salvata in $BUILD_CACHE_DIR/backend-cache)"
}

# Funzione per build frontend con cache ottimizzata
build_frontend() {
    log_info "Building frontend con cache ottimizzata e persistente..."
    local frontend_start=$(date +%s)

    write_status frontend starting
    trap 'write_status frontend failed' ERR

    pushd "$FRONTEND_DIR" > /dev/null

    # Prepara cache node_modules (salta se USE_NODE_CACHE=0)
    if [ -d "node_modules" ]; then
        if [ "${USE_NODE_CACHE}" = "0" ]; then
            log_warning "Caching node_modules disabilitato (USE_NODE_CACHE=0)"
        else
            write_status frontend copy_node_modules
            log_info "Caching node_modules esistenti..."
            local cache_copy_start=$(date +%s)
            local NODE_SIZE=$(du -sh node_modules 2>/dev/null | cut -f1)
            log_info "Dimensione node_modules: ${NODE_SIZE:-sconosciuta} - avvio copia verso cache..."
            local node_cache_target="$BUILD_CACHE_DIR/node-cache/node_modules"
            rm -rf "$node_cache_target"
            mkdir -p "$node_cache_target"
            if command -v rsync >/dev/null 2>&1; then
                rsync -a --delete --info=progress2 node_modules/ "$node_cache_target/" 2>&1 | while IFS= read -r line; do
                    if [[ $line =~ ^[0-9] ]]; then
                        log_info "Copia node_modules: $line"
                    else
                        echo "$line"
                    fi
                done
                COPY_STATUS=${PIPESTATUS[0]}
            else
                (cp -a node_modules/. "$node_cache_target/") &
                local copy_pid=$!
                local last_report=$cache_copy_start
                COPY_STATUS=0
                local elapsed=0
                while kill -0 "$copy_pid" 2>/dev/null; do
                    sleep 5
                    local now=$(date +%s)
                    elapsed=$((now - cache_copy_start))
                    if (( now - last_report >= 5 )); then
                        local partial_size="sconosciuta"
                        if [ -d "$node_cache_target" ]; then
                            partial_size=$(du -sh "$node_cache_target" 2>/dev/null | cut -f1)
                        fi
                        log_info "Copia node_modules in corso... ${elapsed}s trascorsi (parziale: $partial_size)"
                        last_report=$now
                    fi
                done
                wait "$copy_pid" || COPY_STATUS=$?
            fi

            if [ "${COPY_STATUS:-0}" -eq 0 ]; then
                local cache_copy_end=$(date +%s)
                local cache_copy_duration=$((cache_copy_end - cache_copy_start))
                log_success "Cache node_modules aggiornata in ${cache_copy_duration}s"
            else
                log_warning "Impossibile aggiornare la cache node_modules"
            fi
        fi
    fi

    write_status frontend docker_build

    local cache_flags=()
    if [ "$USE_CACHE" = true ]; then
        cache_flags+=(
            --cache-from "type=local,src=$BUILD_CACHE_DIR/frontend-cache"
            --cache-to "type=local,dest=$BUILD_CACHE_DIR/frontend-cache,mode=max"
        )
    else
        cache_flags+=(--no-cache)
    fi

    # Build con cache persistente su filesystem locale
    echo -e "\n${BLUE}=== INIZIO BUILD FRONTEND ===${NC}"
    log_info "Avvio docker build frontend..."
    docker buildx build \
        --builder "$BUILDX_BUILDER_NAME" \
        --build-arg BUILDKIT_INLINE_CACHE=1 \
        --build-arg NODE_ENV=production \
        "${cache_flags[@]}" \
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

    popd > /dev/null
    local frontend_end=$(date +%s)
    local frontend_duration=$((frontend_end - frontend_start))
    write_status frontend completed
    trap - ERR
    log_success "Frontend build completato in ${frontend_duration}s (cache salvata in $BUILD_CACHE_DIR/frontend-cache)"
}

# Funzione per build parallelo
build_parallel() {
    log_info "Avvio build parallelo backend e frontend..."
    echo -e "\n${YELLOW}=== BUILD PARALLELO IN CORSO ===${NC}"
    echo -e "${BLUE}▶ Backend e Frontend vengono costruiti simultaneamente${NC}"
    echo -e "${BLUE}▶ I messaggi di entrambi i build appariranno qui sotto${NC}"
    echo ""

    # Build in background
    local backend_start_ts=$(date +%s)
    write_status backend queued
    build_backend &
    BACKEND_PID=$!

    local frontend_start_ts=$(date +%s)
    write_status frontend queued
    build_frontend &
    FRONTEND_PID=$!

    # Monitoraggio progresso build parallelo
    echo -e "${YELLOW}=== ATTESA COMPLETAMENTO BUILD ===${NC}"

    # Controlla periodicamente lo stato dei processi
    local last_report=$(date +%s)
    local last_message=""
    local last_message_time=0
    while kill -0 $BACKEND_PID 2>/dev/null || kill -0 $FRONTEND_PID 2>/dev/null; do
        sleep 2
        local now=$(date +%s)
        if (( now - last_report >= STATUS_INTERVAL )); then
            local BACKEND_RUNNING=false
            local FRONTEND_RUNNING=false

            if kill -0 $BACKEND_PID 2>/dev/null; then
                BACKEND_RUNNING=true
            fi

            if kill -0 $FRONTEND_PID 2>/dev/null; then
                FRONTEND_RUNNING=true
            fi

            local backend_stage=$(read_status backend)
            local frontend_stage=$(read_status frontend)

            local backend_elapsed=$((now - backend_start_ts))
            local frontend_elapsed=$((now - frontend_start_ts))

            local backend_state_label=$([ "$BACKEND_RUNNING" = true ] && echo "in corso" || echo "completato")
            local frontend_state_label=$([ "$FRONTEND_RUNNING" = true ] && echo "in corso" || echo "completato")

            local backend_stage_desc=$(describe_stage "$backend_stage")
            local frontend_stage_desc=$(describe_stage "$frontend_stage")

            local message="Stato build → Backend: ${backend_state_label} (fase: ${backend_stage_desc}, elapsed: $(format_duration "$backend_elapsed")) | Frontend: ${frontend_state_label} (fase: ${frontend_stage_desc}, elapsed: $(format_duration "$frontend_elapsed"))"
            local should_log=false
            if [ "$message" != "$last_message" ]; then
                should_log=true
            elif (( now - last_message_time >= HEARTBEAT_INTERVAL )); then
                should_log=true
            fi
            if [ "$should_log" = true ]; then
                log_info "$message"
                last_message="$message"
                last_message_time=$now
            fi
            last_report=$now
        fi
    done

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
    local check_backend=$1
    local check_frontend=$2

    log_info "Verifica build completato..."

    if [ "$check_backend" = true ]; then
        if ! docker image inspect "$PROJECT_NAME-backend:latest" &> /dev/null; then
            log_error "Backend image non trovata"
            return 1
        fi
    fi

    if [ "$check_frontend" = true ]; then
        if ! docker image inspect "$PROJECT_NAME-frontend:latest" &> /dev/null; then
            log_error "Frontend image non trovata"
            return 1
        fi
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
    echo "  --smart        Abilita rilevamento automatico delle modifiche (default)"
    echo "  --no-smart     Disabilita lo smart build (ricostruisce sempre i target selezionati)"
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
    BUILD_BACKEND=true
    BUILD_FRONTEND=true
    CLEANUP_ONLY=false
    USE_CACHE=true
    FORCE_REBUILD=false
    SHOW_CACHE_STATS=false
    SMART_MODE=true
    EXPLICIT_COMPONENT_SELECTION=false
    SMART_SKIP_BUILD=false
    NEXT_BACKEND_HASH=""
    NEXT_FRONTEND_HASH=""

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
                BUILD_BACKEND=true
                BUILD_FRONTEND=false
                EXPLICIT_COMPONENT_SELECTION=true
                shift
                ;;
            -f|--frontend)
                BUILD_BACKEND=false
                BUILD_FRONTEND=true
                EXPLICIT_COMPONENT_SELECTION=true
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
            --smart)
                SMART_MODE=true
                shift
                ;;
            --no-smart)
                SMART_MODE=false
                shift
                ;;
            *)
                log_error "Opzione sconosciuta: $1"
                show_help
                exit 1
                ;;
        esac
    done

    if [ "$CLEANUP_ONLY" != true ] && [ "$SHOW_CACHE_STATS" != true ] && \
       [ "$SMART_MODE" = true ] && [ "$FORCE_REBUILD" = false ] && \
       [ "$EXPLICIT_COMPONENT_SELECTION" = false ]; then
        detect_smart_targets
        if [ "$SMART_SKIP_BUILD" = true ]; then
            log_success "Nessuna modifica rilevata dalle ultime immagini: niente da ricostruire (usa --force per forzare)."
            exit 0
        fi
    fi

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

    ensure_buildx_builder
    warm_base_images

    local EXPECT_BACKEND_IMAGE=$BUILD_BACKEND
    local EXPECT_FRONTEND_IMAGE=$BUILD_FRONTEND

    if [ "$EXPLICIT_COMPONENT_SELECTION" = false ]; then
        EXPECT_BACKEND_IMAGE=true
        EXPECT_FRONTEND_IMAGE=true
    fi

    log_info "Componenti da buildare → backend: $BUILD_BACKEND | frontend: $BUILD_FRONTEND"

    # Esegui build
    local START_TIME=$(date +%s)

    if [ "$BUILD_BACKEND" = true ] && [ "$BUILD_FRONTEND" = true ]; then
        build_parallel
        update_snapshot "backend" "$NEXT_BACKEND_HASH"
        update_snapshot "frontend" "$NEXT_FRONTEND_HASH"
    elif [ "$BUILD_BACKEND" = true ]; then
        build_backend
        update_snapshot "backend" "$NEXT_BACKEND_HASH"
    elif [ "$BUILD_FRONTEND" = true ]; then
        build_frontend
        update_snapshot "frontend" "$NEXT_FRONTEND_HASH"
    else
        log_success "Nessun componente selezionato per la build. Nulla da fare."
        exit 0
    fi

    # Verifica build
    verify_build "$EXPECT_BACKEND_IMAGE" "$EXPECT_FRONTEND_IMAGE"

    local END_TIME=$(date +%s)
    local DURATION=$((END_TIME - START_TIME))
    local TOTAL_RUNTIME=$((END_TIME - SCRIPT_START))

    log_success "Build completato in ${DURATION}s (runtime totale script: ${TOTAL_RUNTIME}s)"

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

    rm -f "$BACKEND_STATUS_FILE" "$FRONTEND_STATUS_FILE"
}

# Esegui main function con tutti gli argomenti
main "$@"
