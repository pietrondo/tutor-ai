#!/bin/bash

# ===============================================
#  Tutor-AI - Startup Script Semplificato
#  Avvio rapido per sviluppo locale con un solo comando
# ===============================================

set -e

# Colori
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_logo() {
    if $SKIP_LOGO; then
        return
    fi
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                                                              ║"
    echo "║    ████████╗ █████╗ ███╗   ██╗██╗  ██╗    ██████╗ ███████╗  ║"
    echo "║    ╚══██╔══╝██╔══██╗████╗  ██║██║ ██╔╝    ██╔══██╗██╔════╝  ║"
    echo "║       ██║   ███████║██╔██╗ ██║█████╔╝     ██████╔╝█████╗    ║"
    echo "║       ██║   ██╔══██║██║╚██╗██║██╔═██╗     ██╔══██╗██╔══╝    ║"
    echo "║       ██║   ██║  ██║██║ ╚████║██║  ██╗    ██████╔╝███████╗  ║"
    echo "║       ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝    ╚═════╝ ╚══════╝  ║"
    echo "║                                                              ║"
    echo "║                   🧠 COGNITIVE LEARNING ENGINE               ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Funzioni
print_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

MODE="dev"
FORCE_REBUILD=false
SKIP_HEALTH=false
SKIP_LOGO=false
COMPOSE_FILES=""

print_usage() {
    cat <<'EOU'
Uso: ./start.sh [modalità] [opzioni]

Modalità disponibili:
  dev (default)   Avvio ambiente di sviluppo con hot reload
  simple          Stack docker minimale
  prod            Configurazione ottimizzata per produzione
  stop/clean/logs/status (come in precedenza)

Opzioni:
  --build, -b     Ricostruisce e ricrea i container (utile dopo modifiche code base)
  --no-health     Salta l'health check (per start rapidissimi)
  --no-logo       Nasconde il banner ASCII
  --help          Mostra questo messaggio

Esempi:
  ./start.sh                      # avvio dev standard
  ./start.sh dev --build          # rebuild rapido dopo modifiche
  ./start.sh prod --no-health     # avvio produzione senza health check
EOU
}

parse_args() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            dev|development)
                MODE="dev"
                ;;
            simple)
                MODE="simple"
                ;;
            prod|production)
                MODE="prod"
                ;;
            stop|clean|logs|status)
                MODE="$1"
                ;;
            --build|-b)
                FORCE_REBUILD=true
                ;;
            --no-health)
                SKIP_HEALTH=true
                ;;
            --no-logo)
                SKIP_LOGO=true
                ;;
            --help|-h)
                print_usage
                exit 0
                ;;
            *)
                echo "Argomento non valido: $1"
                print_usage
                exit 1
                ;;
        esac
        shift
    done
}

# Verifica Docker
check_docker() {
    print_info "Verifica Docker..."

    if ! command -v docker &> /dev/null; then
        print_error "Docker non è installato"
        exit 1
    fi

    if ! docker info &> /dev/null; then
        print_error "Docker non è in esecuzione"
        exit 1
    fi

    # Determina docker compose command
    if command -v docker-compose &> /dev/null; then
        DOCKER_COMPOSE="docker-compose"
    else
        DOCKER_COMPOSE="docker compose"
    fi

    print_success "Docker pronto"
}

# Crea directory necessarie
create_directories() {
    print_info "Creazione directory..."

    mkdir -p data/{uploads,vector_db,courses,chat_sessions}
    mkdir -p logs

    # File .env se non esiste
    if [ ! -f "./backend/.env" ]; then
        print_warning "Creo template .env..."
        cat > ./backend/.env << 'EOF'
# Tutor-AI Environment Configuration
DEBUG=true
ENVIRONMENT=development
LOG_LEVEL=debug

# API Configuration
OPENAI_API_KEY=your_openai_key_here
ZAI_API_KEY=your_zai_key_here

# Database
REDIS_URL=redis://redis:6379
DATABASE_URL=sqlite:///./data/app.db

# CORS
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# File Storage
UPLOAD_DIR=./data/uploads
VECTOR_DB_PATH=./data/vector_db

# API Configuration
API_HOST=0.0.0.0
API_PORT=8001
EOF
        print_warning "Configura le tue API keys in backend/.env"
    fi

    print_success "Directory create"
}

# Seleziona mode e file compose
select_mode() {
    case "$MODE" in
        "dev"|"development")
            print_info "Modalità SVILUPPO con hot reload"
            COMPOSE_FILES="-f docker-compose.yml -f docker-compose.dev.yml"
            FRONTEND_PORT=3000
            ;;
        "simple")
            print_info "Modalità SEMPLIFICATA"
            COMPOSE_FILES="-f docker-compose.simple.yml"
            FRONTEND_PORT=3000
            ;;
        "prod"|"production")
            print_info "Modalità PRODUZIONE"
            COMPOSE_FILES="-f docker-compose.yml -f docker-compose.optimized.yml"
            FRONTEND_PORT=3000
            ;;
        "stop")
            print_info "Arresto servizi..."
            $DOCKER_COMPOSE $COMPOSE_FILES down 2>/dev/null || $DOCKER_COMPOSE down 2>/dev/null || true
            print_success "Servizi arrestati"
            exit 0
            ;;
        "clean")
            print_info "Pulizia completa..."
            $DOCKER_COMPOSE down -v --remove-orphans 2>/dev/null || true
            docker system prune -f
            docker volume prune -f
            print_success "Pulizia completata"
            exit 0
            ;;
        "logs")
            print_info "Visualizzazione log..."
            $DOCKER_COMPOSE logs -f
            exit 0
            ;;
        "status")
            print_info "Stato servizi:"
            $DOCKER_COMPOSE ps
            echo
            echo "URL di accesso:"
            echo "  • Frontend: http://localhost:3000"
            echo "  • Backend:  http://localhost:8001"
            echo "  • API Docs: http://localhost:8001/docs"
            exit 0
            ;;
        *)
            echo "Uso: $0 [dev|simple|prod|stop|clean|logs|status]"
            echo ""
            echo "Modalità:"
            echo "  dev       - Sviluppo con hot reload (default)"
            echo "  simple    - Configurazione semplificata"
            echo "  prod      - Produzione ottimizzata"
            echo "  stop      - Arresta tutti i servizi"
            echo "  clean     - Pulizia container e immagini"
            echo "  logs      - Mostra log in tempo reale"
            echo "  status    - Mostra stato servizi"
            exit 1
            ;;
    esac
}

# Avvia servizi
start_services() {
    print_info "Avvio servizi Docker..."

    if $FORCE_REBUILD; then
        $DOCKER_COMPOSE $COMPOSE_FILES up -d --build --force-recreate
    else
        $DOCKER_COMPOSE $COMPOSE_FILES up -d
    fi

    if [ $? -eq 0 ]; then
        print_success "Servizi avviati!"
    else
        print_error "Errore avvio servizi"
        exit 1
    fi
}

# Health check
health_check() {
    if $SKIP_HEALTH; then
        print_warning "Health check saltato (--no-health)"
        return
    fi

    print_info "Attesa servizi pronti..."

    local max_attempts=30
    local attempt=0

    while [ $attempt -lt $max_attempts ]; do
        if curl -s http://localhost:8001/health > /dev/null 2>&1; then
            print_success "Backend pronto!"
            break
        fi

        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done

    echo

    if [ $attempt -eq $max_attempts ]; then
        print_warning "Backend non risponde, ma i container sono in esecuzione"
    fi
}

# Mostra informazioni
show_info() {
    echo
    print_success "🚀 Tutor-AI è pronto!"
    echo
    echo "╔═══════════════════════════════════════════════════════════════╗"
    echo "║                     🌐 ACCESS URLS                          ║"
    echo "╠═══════════════════════════════════════════════════════════════╣"
    echo "║  • Frontend:      http://localhost:$FRONTEND_PORT              ║"
    echo "║  • Backend API:   http://localhost:8001                       ║"
    echo "║  • API Docs:      http://localhost:8001/docs                  ║"
    echo "║  • Redis:         localhost:6379                             ║"
    echo "╚═══════════════════════════════════════════════════════════════╝"
    echo
    echo "╔═══════════════════════════════════════════════════════════════╗"
    echo "║                     🛠️ COMANDI UTILI                         ║"
    echo "╠═══════════════════════════════════════════════════════════════╣"
    echo "║  • Stop:          ./start.sh stop                            ║"
    echo "║  • Logs:          ./start.sh logs                            ║"
    echo "║  • Status:        ./start.sh status                          ║"
    echo "║  • Clean:         ./start.sh clean                           ║"
    echo "║  • Restart:       ./start.sh dev                             ║"
    echo "╚═══════════════════════════════════════════════════════════════╝"
    echo

    if [ "$MODE" = "dev" ]; then
        print_info "💡 Hot reload attivo - I cambiamenti si applicano automaticamente"
    fi

    if [ ! -f "./backend/.env" ] || grep -q "your_.*_key_here" "./backend/.env"; then
        print_warning "⚠️  Configura le tue API keys in backend/.env per funzionalità complete"
    fi
}

# Main
main() {
    parse_args "$@"

    local is_start_mode=true
    case "$MODE" in
        stop|clean|logs|status)
            is_start_mode=false
            ;;
    esac

    if $is_start_mode; then
        print_logo
    fi

    echo
    if $is_start_mode; then
        print_info "Avvio Tutor-AI in modalità: $MODE"
        if $FORCE_REBUILD; then
            print_info "Opzione rebuild attiva: verrà eseguito docker compose up -d --build --force-recreate"
        fi
    else
        print_info "Esecuzione comando: $MODE"
    fi
    echo

    check_docker
    if $is_start_mode; then
        create_directories
    fi
    select_mode
    if $is_start_mode; then
        start_services
        health_check
        show_info
    fi
}

# Trap per cleanup
trap 'echo -e "\n${YELLOW}Interruzione ricevuta${NC}"; exit 0' INT TERM

# Esegui
main "$@"
