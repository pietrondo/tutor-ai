#!/bin/bash

# Script per visualizzare logs Docker su WSL2/Linux
# Docker logs viewer script for WSL2/Linux
#
# Caratteristiche / Features:
# - Logs colorati e formattati
# - Filtraggio per servizio
# - Follow mode
# - Export logs

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

# Configurazione
PROJECT_NAME="tutor-ai"
COMPOSE_FILE="docker-compose.yml"
LOG_DIR="$HOME/.docker-logs/$PROJECT_NAME"

# Directory del progetto
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Creazione directory log
mkdir -p "$LOG_DIR"

# Funzione per show help
show_help() {
    echo "Script Docker Logs per $PROJECT_NAME"
    echo ""
    echo "Uso: $0 [OPZIONI] [SERVIZIO]"
    echo ""
    echo "Opzioni:"
    echo "  -h, --help      Mostra questo help"
    echo "  -f, --follow    Follow mode (tail -f)"
    echo "  -t, --tail N    Mostra ultime N righe (default: 100)"
    echo "  -e, --export    Export logs su file"
    echo "  -a, --all       Tutti i servizi (default)"
    echo "  --since TIME    Mostra logs da TIME (es: 1h, 30m, 2023-01-01T10:00:00)"
    echo "  --until TIME    Mostra logs fino a TIME"
    echo ""
    echo "Servizi:"
    echo "  backend         Solo backend logs"
    echo "  frontend        Solo frontend logs"
    echo "  redis           Solo redis logs"
    echo ""
    echo "Esempi:"
    echo "  $0                # Logs di tutti i servizi"
    echo "  $0 -f backend     # Follow backend logs"
    echo "  $0 -t 50 frontend # Ultime 50 righe frontend"
    echo "  $0 --export       # Export logs su file"
}

# Funzione per ottenere logs di un servizio
get_service_logs() {
    local service="$1"
    local follow="$2"
    local tail="$3"
    local since="$4"
    local until="$5"
    local export_file="$6"

    local container_name="$PROJECT_NAME-$service"

    # Build docker logs command
    local logs_cmd="docker logs"

    if [ "$follow" = true ]; then
        logs_cmd="$logs_cmd -f"
    fi

    if [ -n "$tail" ]; then
        logs_cmd="$logs_cmd --tail $tail"
    fi

    if [ -n "$since" ]; then
        logs_cmd="$logs_cmd --since '$since'"
    fi

    if [ -n "$until" ]; then
        logs_cmd="$logs_cmd --until '$until'"
    fi

    logs_cmd="$logs_cmd $container_name"

    # Execute command
    if [ -n "$export_file" ]; then
        log_info "Export logs per $service su $export_file"
        eval "$logs_cmd" > "$export_file" 2>&1
        log_success "Logs esportati su $export_file"
    else
        # Add header per service
        echo ""
        echo -e "${CYAN}=== LOGS $service ===${NC}"
        echo ""

        eval "$logs_cmd" 2>&1 || log_warning "Nessun log trovato per $service"
    fi
}

# Funzione per logs di tutti i servizi
get_all_logs() {
    local follow="$1"
    local tail="$2"
    local since="$3"
    local until="$4"
    local export_file="$5"

    local services=("backend" "frontend" "redis")

    if [ "$follow" = true ]; then
        # Follow mode: usa docker-compose logs
        if command -v docker-compose &> /dev/null; then
            local compose_cmd="docker-compose -f $COMPOSE_FILE logs -f"
        else
            local compose_cmd="docker compose -f $COMPOSE_FILE logs -f"
        fi

        if [ -n "$tail" ]; then
            compose_cmd="$compose_cmd --tail=$tail"
        fi

        if [ -n "$since" ]; then
            compose_cmd="$compose_cmd --since=$since"
        fi

        if [ -n "$until" ]; then
            compose_cmd="$compose_cmd --until=$until"
        fi

        eval "$compose_cmd"
    else
        # Non-follow mode: mostra logs di ogni servizio
        for service in "${services[@]}"; do
            get_service_logs "$service" false "$tail" "$since" "$until" ""
        done
    fi
}

# Funzione principale
main() {
    local FOLLOW=false
    local TAIL="100"
    local EXPORT=false
    local SERVICE=""
    local SINCE=""
    local UNTIL=""
    local ALL_SERVICES=true

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -f|--follow)
                FOLLOW=true
                shift
                ;;
            -t|--tail)
                TAIL="$2"
                shift 2
                ;;
            -e|--export)
                EXPORT=true
                shift
                ;;
            -a|--all)
                ALL_SERVICES=true
                shift
                ;;
            --since)
                SINCE="$2"
                shift 2
                ;;
            --until)
                UNTIL="$2"
                shift 2
                ;;
            backend|frontend|redis)
                SERVICE="$1"
                ALL_SERVICES=false
                shift
                ;;
            *)
                log_error "Opzione sconosciuta: $1"
                show_help
                exit 1
                ;;
        esac
    done

    # Export setup
    local export_file=""
    if [ "$EXPORT" = true ]; then
        local timestamp=$(date +"%Y%m%d_%H%M%S")
        if [ -n "$SERVICE" ]; then
            export_file="$LOG_DIR/${SERVICE}_${timestamp}.log"
        else
            export_file="$LOG_DIR/all_${timestamp}.log"
        fi
    fi

    log_info "Visualizzazione logs Docker per $PROJECT_NAME"

    # Get logs
    if [ "$ALL_SERVICES" = true ]; then
        get_all_logs "$FOLLOW" "$TAIL" "$SINCE" "$UNTIL" "$export_file"
    else
        get_service_logs "$SERVICE" "$FOLLOW" "$TAIL" "$SINCE" "$UNTIL" "$export_file"
    fi

    if [ "$EXPORT" = true ] && [ -n "$export_file" ]; then
        log_success "Logs esportati in: $export_file"
    fi
}

main "$@"