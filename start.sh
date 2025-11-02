#!/bin/bash

# =============================================
# Tutor-AI Docker Management Script
# Enhanced startup script with better error handling
# =============================================

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Logo
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
echo "║                    ADVANCED STUDY SYSTEM                    ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Function to print colored output
print_status() {
    echo -e "${CYAN}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${PURPLE}[SYSTEM]${NC} $1"
}

# Check if Docker is installed and running
check_docker() {
    print_header "Checking Docker environment..."

    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi

    if ! docker info &> /dev/null; then
        print_error "Docker is not running. Please start Docker daemon."
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null && ! command -v docker &> /dev/null compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose."
        exit 1
    fi

    # Set docker compose command
    if command -v docker-compose &> /dev/null; then
        DOCKER_COMPOSE="docker-compose"
    else
        DOCKER_COMPOSE="docker compose"
    fi

    print_success "Docker environment is ready"
}

# Check system resources
check_system_resources() {
    print_header "Checking system resources..."

    # Check available memory
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        AVAILABLE_MEM=$(free -g | awk '/^Mem:/{print $7}')
        if [[ $AVAILABLE_MEM -lt 4 ]]; then
            print_warning "Less than 4GB of available RAM detected. Performance may be affected."
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        AVAILABLE_MEM=$(sysctl -n hw.memsize | awk '{print int($1/1024/1024/1024)}')
        if [[ $AVAILABLE_MEM -lt 8 ]]; then
            print_warning "Less than 8GB of RAM detected. Performance may be affected."
        fi
    fi

    # Check available disk space
    AVAILABLE_SPACE=$(df . | tail -1 | awk '{print $4}')
    if [[ $AVAILABLE_SPACE -lt 2097152 ]]; then  # 2GB in KB
        print_warning "Less than 2GB of available disk space. Consider freeing up space."
    fi

    print_success "System resources check completed"
}

# Create necessary directories
create_directories() {
    print_header "Creating necessary directories..."

    mkdir -p data/uploads
    mkdir -p data/vector_db
    mkdir -p data/courses
    mkdir -p logs

    # Set proper permissions
    chmod 755 data
    chmod 755 data/uploads
    chmod 755 data/vector_db
    chmod 755 data/courses
    chmod 755 logs

    print_success "Directories created and permissions set"
}

# Clean up function
cleanup() {
    print_header "Cleaning up..."

    # Remove stopped containers
    $DOCKER_COMPOSE rm -f 2>/dev/null || true

    # Clean up unused images and volumes
    docker image prune -f 2>/dev/null || true
    docker volume prune -f 2>/dev/null || true

    print_success "Cleanup completed"
}

# Stop all services
stop_services() {
    print_header "Stopping all services..."

    $DOCKER_COMPOSE down
    print_success "All services stopped"
}

# Build services
build_services() {
    print_header "Building Docker images..."

    # Build without cache to ensure fresh builds
    $DOCKER_COMPOSE build --no-cache

    print_success "Docker images built successfully"
}

# Start services
start_services() {
    print_header "Starting Tutor-AI services..."

    $DOCKER_COMPOSE up -d

    print_success "Services starting..."

    # Wait for services to be healthy
    wait_for_services
}

# Wait for services to be healthy
wait_for_services() {
    print_header "Waiting for services to be ready..."

    local max_attempts=30
    local attempt=0

    while [[ $attempt -lt $max_attempts ]]; do
        if $DOCKER_COMPOSE ps | grep -q "healthy\|Up"; then
            local healthy_count=$($DOCKER_COMPOSE ps | grep -c "healthy\|Up" || echo "0")
            local total_count=$($DOCKER_COMPOSE ps | grep -c "tutor-ai" || echo "0")

            if [[ $healthy_count -eq $total_count ]] && [[ $total_count -gt 0 ]]; then
                print_success "All services are healthy and ready!"
                show_service_status
                return 0
            fi
        fi

        attempt=$((attempt + 1))
        echo -n "."
        sleep 2
    done

    echo
    print_error "Services did not become healthy within expected time."
    show_service_status
    return 1
}

# Show service status
show_service_status() {
    print_header "Service Status:"
    echo
    $DOCKER_COMPOSE ps
    echo

    print_header "Access URLs:"
    echo -e "${GREEN}• Frontend:${NC} http://localhost:3000"
    echo -e "${GREEN}• Backend API:${NC} http://localhost:8000"
    echo -e "${GREEN}• API Documentation:${NC} http://localhost:8000/docs"
    echo -e "${GREEN}• Redis:${NC} localhost:6379"
    echo
}

# Show logs
show_logs() {
    print_header "Showing service logs..."
    $DOCKER_COMPOSE logs -f
}

# Health check
health_check() {
    print_header "Performing health check..."

    # Check backend
    if curl -s http://localhost:8000/health > /dev/null; then
        print_success "Backend is responding"
    else
        print_error "Backend is not responding"
        return 1
    fi

    # Check frontend
    if curl -s http://localhost:3000 > /dev/null; then
        print_success "Frontend is responding"
    else
        print_error "Frontend is not responding"
        return 1
    fi

    print_success "All health checks passed"
}

# Development mode
dev_mode() {
    print_header "Starting in development mode..."

    # Start backend and database
    $DOCKER_COMPOSE up -d backend redis

    # Start frontend in development mode
    print_status "Starting frontend in development mode..."
    cd frontend && npm run dev

    # Cleanup on exit
    $DOCKER_COMPOSE down
}

# Production mode
prod_mode() {
    print_header "Starting in production mode..."

    cleanup
    create_directories
    build_services
    start_services
}

# Show help
show_help() {
    echo -e "${CYAN}Tutor-AI Docker Management Script${NC}"
    echo
    echo "Usage: $0 [COMMAND]"
    echo
    echo "Commands:"
    echo -e "  ${GREEN}start${NC}        Start all services in production mode"
    echo -e "  ${GREEN}dev${NC}          Start in development mode (frontend dev server)"
    echo -e "  ${GREEN}stop${NC}         Stop all services"
    echo -e "  ${GREEN}restart${NC}      Restart all services"
    echo -e "  ${GREEN}build${NC}        Build Docker images"
    echo -e "  ${GREEN}clean${NC}        Clean up containers and images"
    echo -e "  ${GREEN}logs${NC}         Show service logs"
    echo -e "  ${GREEN}status${NC}       Show service status"
    echo -e "  ${GREEN}health${NC}       Perform health check"
    echo -e "  ${GREEN}update${NC}       Pull latest changes and rebuild"
    echo -e "  ${GREEN}help${NC}         Show this help message"
    echo
    echo "Examples:"
    echo "  $0 start          # Start production environment"
    echo "  $0 dev            # Start development environment"
    echo "  $0 logs           # View logs"
    echo "  $0 stop           # Stop all services"
    echo
}

# Update application
update_app() {
    print_header "Updating application..."

    # Stop services
    stop_services

    # Pull latest changes if git repo
    if [[ -d .git ]]; then
        print_status "Pulling latest changes..."
        git pull origin main
    fi

    # Rebuild and start
    build_services
    start_services

    print_success "Application updated successfully"
}

# Main script logic
main() {
    # Check Docker first
    check_docker

    # Parse command
    case "${1:-start}" in
        "start")
            check_system_resources
            create_directories
            prod_mode
            ;;
        "dev")
            check_system_resources
            create_directories
            dev_mode
            ;;
        "stop")
            stop_services
            ;;
        "restart")
            stop_services
            prod_mode
            ;;
        "build")
            create_directories
            build_services
            ;;
        "clean")
            cleanup
            ;;
        "logs")
            show_logs
            ;;
        "status")
            show_service_status
            ;;
        "health")
            health_check
            ;;
        "update")
            update_app
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            print_error "Unknown command: $1"
            show_help
            exit 1
            ;;
    esac
}

# Trap cleanup on script exit
trap cleanup EXIT

# Run main function with all arguments
main "$@"