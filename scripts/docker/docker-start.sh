#!/bin/bash

# Script ottimizzato per avvio Docker su WSL2/Linux
# Optimized Docker startup script for WSL2/Linux
#
# Caratteristiche / Features:
# - Avvio rapido con container esistenti
# - Health check automatici
# - Gestione errori robusta
# - Logging dettagliato
# - Configurazione rete WSL2 ottimizzata

set -e  # Exit on error

# Colori per output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
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

log_step() {
    echo -e "${CYAN}[STEP]${NC} $1"
}

# Configurazione
PROJECT_NAME="tutor-ai"
COMPOSE_FILE="docker-compose.yml"
LOG_DIR="$HOME/.docker-logs/$PROJECT_NAME"
HEALTH_CHECK_TIMEOUT=60
HEALTH_CHECK_INTERVAL=5

# Directory del progetto
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Creazione directory log
mkdir -p "$LOG_DIR"

# Variabili di stato
STATUS_FILE="/tmp/$PROJECT_NAME.status"
BACKEND_CONTAINER="$PROJECT_NAME-backend"
FRONTEND_CONTAINER="$PROJECT_NAME-frontend"
REDIS_CONTAINER="$PROJECT_NAME-redis"

# Funzione per verificare prerequisiti
check_prerequisites() {
    log_step "Verifica prerequisiti..."

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

    # Check docker-compose file
    if [ ! -f "$COMPOSE_FILE" ]; then
        log_error "File $COMPOSE_FILE non trovato nella directory corrente."
        exit 1
    fi

    log_success "Prerequisiti verificati"
}

# Funzione per ottimizzare rete WSL2
optimize_wsl2_network() {
    log_step "Ottimizzazione configurazione rete WSL2..."

    # Imposta variabili d'ambiente per WSL2
    export DOCKER_HOST="unix:///var/run/docker.sock"
    export COMPOSE_PROJECT_NAME="$PROJECT_NAME"

    # Configura DNS per WSL2 (se necessario)
    if grep -q "Microsoft" /proc/version 2>/dev/null; then
        log_info "Rilevato ambiente WSL2, ottimizzazione rete..."
        # Forza uso di localhost per networking
        export HOST_IP="127.0.0.1"
    fi

    log_success "Configurazione rete ottimizzata"
}

# Funzione per controllare se i container sono già in esecuzione
check_running_containers() {
    log_step "Verifica container in esecuzione..."

    local running_containers=0
    local containers=("$BACKEND_CONTAINER" "$FRONTEND_CONTAINER" "$REDIS_CONTAINER")

    for container in "${containers[@]}"; do
        if docker ps --format "table {{.Names}}" | grep -q "$container"; then
            log_info "Container $container già in esecuzione"
            ((running_containers++))
        fi
    done

    echo "$running_containers"
}

# Funzione per health check di un container
wait_for_container_health() {
    local container_name="$1"
    local timeout="$2"
    local interval="$3"
    local elapsed=0

    log_info "Attesa health check per $container_name..."

    while [ $elapsed -lt $timeout ]; do
        if docker ps --format "table {{.Names}}\t{{.Status}}" | grep "$container_name" | grep -q "healthy"; then
            log_success "$container_name è healthy"
            return 0
        fi

        # Check se container è in errore
        if docker ps -a --format "table {{.Names}}\t{{.Status}}" | grep "$container_name" | grep -q "Exited"; then
            log_error "$container_name è uscito con errore"
            return 1
        fi

        sleep $interval
        elapsed=$((elapsed + interval))
        echo -n "."
    done

    echo ""
    log_error "Timeout attesa health check per $container_name"
    return 1
}

# Funzione per avvio servizi con docker-compose
start_services() {
    log_step "Avvio servizi Docker Compose..."

    # Usa docker-compose o docker compose a seconda della versione
    if command -v docker-compose &> /dev/null; then
        COMPOSE_CMD="docker-compose"
    else
        COMPOSE_CMD="docker compose"
    fi

    # Avvio con build se necessario
    if ! docker images | grep -q "$PROJECT_NAME"; then
        log_warning "Immagini Docker non trovate, eseguo build..."
        ./docker-build.sh
    fi

    # Avvio servizi
    log_info "Avvio dei servizi in background..."
    $COMPOSE_CMD -f "$COMPOSE_FILE" up -d --remove-orphans

    if [ $? -eq 0 ]; then
        log_success "Servizi avviati con successo"
    else
        log_error "Errore durante l'avvio dei servizi"
        exit 1
    fi
}

# Funzione per riavvio servizi
restart_services() {
    log_step "Riavvio servizi Docker..."

    # Stop servizi
    log_info "Arresto servizi esistenti..."
    if command -v docker-compose &> /dev/null; then
        docker-compose -f "$COMPOSE_FILE" down
    else
        docker compose -f "$COMPOSE_FILE" down
    fi

    # Attendi qualche secondo per cleanup completo
    sleep 3

    # Riavvio
    start_services
}

# Funzione per verifica post-avvio
verify_startup() {
    log_step "Verifica post-avvio..."

    # Verifica backend health
    if ! wait_for_container_health "$BACKEND_CONTAINER" "$HEALTH_CHECK_TIMEOUT" "$HEALTH_CHECK_INTERVAL"; then
        log_error "Backend non è diventato healthy"
        return 1
    fi

    # Verifica Redis
    if ! wait_for_container_health "$REDIS_CONTAINER" 30 5; then
        log_warning "Redis health check fallito, ma può essere normale per Redis"
    fi

    # Verifica frontend (senza health check specifico)
    if docker ps --format "table {{.Names}}" | grep -q "$FRONTEND_CONTAINER"; then
        log_success "Frontend in esecuzione"
    else
        log_error "Frontend non è in esecuzione"
        return 1
    fi

    return 0
}

# Funzione per mostrare status servizi
show_services_status() {
    echo ""
    log_step "Status Servizi:"
    echo ""

    if command -v docker-compose &> /dev/null; then
        docker-compose -f "$COMPOSE_FILE" ps
    else
        docker compose -f "$COMPOSE_FILE" ps
    fi

    echo ""
    log_info "URL di accesso:"
    echo "  • Backend API: http://localhost:8000"
    echo "  • Frontend:    http://localhost:3000"
    echo "  • API Docs:    http://localhost:8000/docs"
    echo "  • Redis:       localhost:6379"
    echo ""

    log_info "Comandi utili:"
    echo "  • Logs:        ./docker-logs.sh"
    echo "  • Stop:        ./docker-stop.sh"
    echo "  • Restart:     ./docker-start.sh --restart"
    echo "  • Status:      docker ps"
}

# Funzione per gestire segnali (Ctrl+C)
cleanup_on_exit() {
    log_warning "Interruzione ricevuta, pulizia in corso..."
    # Non fermare i container qui, lasciarli running
    log_info "Container rimangono in esecuzione. Usare ./docker-stop.sh per fermarli."
    exit 0
}

# Funzione per show help
show_help() {
    echo "Script Docker Start Ottimizzato per $PROJECT_NAME"
    echo ""
    echo "Uso: $0 [OPZIONI]"
    echo ""
    echo "Opzioni:"
    echo "  -h, --help      Mostra questo help"
    echo "  -r, --restart   Forza riavvio completo dei servizi"
    echo "  -b, --build     Esegue build prima dell'avvio"
    echo "  -c, --check     Solo verifica stato servizi"
    echo "  -v, --verbose   Output dettagliato"
    echo "  --no-health     Salta health check"
    echo ""
    echo "Esempi:"
    echo "  $0                # Avvio normale"
    echo "  $0 --restart      # Riavvio completo"
    echo "  $0 --build        # Build + avvio"
    echo "  $0 --check        # Solo verifica status"
}

# Funzione principale
main() {
    local RESTART=false
    local BUILD_FIRST=false
    local CHECK_ONLY=false
    local VERBOSE=false
    local SKIP_HEALTH=false

    # Setup signal handlers
    trap cleanup_on_exit SIGINT SIGTERM

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -r|--restart)
                RESTART=true
                shift
                ;;
            -b|--build)
                BUILD_FIRST=true
                shift
                ;;
            -c|--check)
                CHECK_ONLY=true
                shift
                ;;
            -v|--verbose)
                VERBOSE=true
                set -x  # Enable verbose output
                shift
                ;;
            --no-health)
                SKIP_HEALTH=true
                shift
                ;;
            *)
                log_error "Opzione sconosciuta: $1"
                show_help
                exit 1
                ;;
        esac
    done

    log_info "Inizio avvio Docker per $PROJECT_NAME"

    # Verifica prerequisiti
    check_prerequisites

    # Ottimizza rete WSL2
    optimize_wsl2_network

    # Solo verifica status
    if [ "$CHECK_ONLY" = true ]; then
        show_services_status
        exit 0
    fi

    # Check container già in esecuzione
    local running_count=$(check_running_containers)

    if [ "$running_count" -gt 0 ] && [ "$RESTART" = false ]; then
        log_info "Trovati $running_count container già in esecuzione"

        if [ "$running_count" -eq 3 ]; then
            log_success "Tutti i container sono già in esecuzione"

            if [ "$SKIP_HEALTH" = false ]; then
                verify_startup
            fi

            show_services_status
            exit 0
        else
            log_warning "Alcuni container non sono in esecuzione, procedo con avvio..."
        fi
    fi

    # Build se richiesto
    if [ "$BUILD_FIRST" = true ]; then
        log_info "Eseguo build prima dell'avvio..."
        ./docker-build.sh
    fi

    # Avvio o riavvio servizi
    if [ "$RESTART" = true ] || [ "$running_count" -gt 0 ]; then
        restart_services
    else
        start_services
    fi

    # Verifica post-avvio
    if [ "$SKIP_HEALTH" = false ]; then
        if ! verify_startup; then
            log_error "Verifica post-avvio fallita"
            log_info "Controllare i log con: ./docker-logs.sh"
            exit 1
        fi
    fi

    # Mostra status finale
    show_services_status

    log_success "Avvio completato con successo!"

    # Salva stato
    echo "running" > "$STATUS_FILE"
    echo "$(date)" >> "$STATUS_FILE"
}

# Esegui main function con tutti gli argomenti
main "$@"