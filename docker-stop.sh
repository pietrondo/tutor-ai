#!/bin/bash

# Script per arresto Docker su WSL2/Linux
# Docker stop script for WSL2/Linux
#
# Caratteristiche / Features:
# - Arresto graceful dei servizi
# - Cleanup opzionale
# - Logging dettagliato
# - Supporto per singoli servizi

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
COMPOSE_FILE="docker-compose.yml"
STATUS_FILE="/tmp/$PROJECT_NAME.status"
LOG_DIR="$HOME/.docker-logs/$PROJECT_NAME"

# Directory del progetto
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Funzione per fermare tutti i servizi
stop_all_services() {
    log_info "Arresto di tutti i servizi..."

    if command -v docker-compose &> /dev/null; then
        docker-compose -f "$COMPOSE_FILE" down
    else
        docker compose -f "$COMPOSE_FILE" down
    fi

    log_success "Servizi arrestati"
}

# Funzione per fermare singolo servizio
stop_service() {
    local service_name="$1"
    log_info "Arresto servizio: $service_name"

    if command -v docker-compose &> /dev/null; then
        docker-compose -f "$COMPOSE_FILE" stop "$service_name"
    else
        docker compose -f "$COMPOSE_FILE" stop "$service_name"
    fi

    log_success "Servizio $service_name arrestato"
}

# Funzione per cleanup completo
cleanup_full() {
    log_info "Cleanup completo di Docker..."

    # Rimuovi container, network, volumes
    if command -v docker-compose &> /dev/null; then
        docker-compose -f "$COMPOSE_FILE" down -v --remove-orphans
    else
        docker compose -f "$COMPOSE_FILE" down -v --remove-orphans
    fi

    # Rimuovi immagini del progetto
    log_info "Rimozione immagini Docker del progetto..."
    docker images | grep "$PROJECT_NAME" | awk '{print $3}' | xargs -r docker rmi -f

    # Rimuovi file di stato
    rm -f "$STATUS_FILE"

    log_success "Cleanup completo terminato"
}

# Funzione per show help
show_help() {
    echo "Script Docker Stop per $PROJECT_NAME"
    echo ""
    echo "Uso: $0 [OPZIONI] [SERVIZIO]"
    echo ""
    echo "Opzioni:"
    echo "  -h, --help      Mostra questo help"
    echo "  -c, --cleanup   Cleanup completo (container, immagini, volumi)"
    echo "  -f, --force     Forza arresto immediato"
    echo ""
    echo "Servizi (opzionale):"
    echo "  backend         Solo backend"
    echo "  frontend        Solo frontend"
    echo "  redis           Solo redis"
    echo ""
    echo "Esempi:"
    echo "  $0                # Arresta tutti i servizi"
    echo "  $0 --cleanup      # Cleanup completo"
    echo "  $0 backend        # Arresta solo backend"
}

# Funzione principale
main() {
    local CLEANUP=false
    local FORCE=false
    local SERVICE=""

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -c|--cleanup)
                CLEANUP=true
                shift
                ;;
            -f|--force)
                FORCE=true
                shift
                ;;
            backend|frontend|redis)
                SERVICE="$1"
                shift
                ;;
            *)
                log_error "Opzione sconosciuta: $1"
                show_help
                exit 1
                ;;
        esac
    done

    log_info "Inizio arresto Docker per $PROJECT_NAME"

    if [ "$CLEANUP" = true ]; then
        cleanup_full
        exit 0
    fi

    if [ -n "$SERVICE" ]; then
        stop_service "$SERVICE"
    else
        stop_all_services
    fi

    # Rimuovi file di stato
    rm -f "$STATUS_FILE"

    log_success "Arresto completato"
}

main "$@"