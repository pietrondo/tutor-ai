#!/bin/bash

# 🚀 Tutor AI - Unified Docker Management Script
# Single script for all Docker operations with optimized caching
# Port 8001 for backend, 3000 for frontend

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}🔧 $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Function to show usage
show_usage() {
    echo "🚀 Tutor AI - Docker Management Script"
    echo "======================================"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  start         Start services (quick restart with cache preservation)"
    echo "  restart       Quick restart with cache preservation (default)"
    echo "  full          Full restart with cleanup (preserves PyTorch cache)"
    echo "  rebuild       Rebuild dependencies (re-downloads PyTorch - SLOW)"
    echo "  stop          Stop all services"
    echo "  status        Check service status and show logs"
    echo "  logs          Show service logs"
    echo "  emergency     Emergency reset (complete cleanup)"
    echo "  help          Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0            # Default: quick restart"
    echo "  $0 start      # Start services"
    echo "  $0 full       # Full restart with cleanup"
    echo "  $0 rebuild    # Rebuild when requirements.txt changes"
    echo ""
    echo "📍 URLs:"
    echo "  Frontend:     http://localhost:3000"
    echo "  Backend:      http://localhost:8001"
    echo "  API Docs:     http://localhost:8001/docs"
}

# Function to clean up processes
cleanup_processes() {
    print_status "Cleaning up existing processes..."
    pkill -9 -f "python.*main" 2>/dev/null || true
    pkill -9 -f "next.*dev" 2>/dev/null || true
}

# Function to check service health
check_service_health() {
    local max_attempts=${1:-5}
    local attempt=1

    while [ $attempt -le $max_attempts ]; do
        echo "Health check attempt $attempt/$max_attempts..."

        backend_healthy=false
        frontend_healthy=false

        if curl -s http://localhost:8001/health > /dev/null 2>&1; then
            print_success "Backend is healthy"
            backend_healthy=true
        else
            print_warning "Backend not ready yet"
        fi

        if curl -s http://localhost:3000 > /dev/null 2>&1; then
            print_success "Frontend is responding"
            frontend_healthy=true
        else
            print_warning "Frontend still starting..."
        fi

        if [ "$backend_healthy" = true ] && [ "$frontend_healthy" = true ]; then
            return 0
        fi

        sleep 10
        attempt=$((attempt + 1))
    done

    print_warning "Services are starting but may need more time"
    return 1
}

# Function to start services
start_services() {
    print_status "Starting Tutor AI services..."

    # Build with cache preservation
    echo "🔨 Building services (preserving PyTorch cache)..."
    DOCKER_BUILDKIT=1 docker-compose -f docker-compose.yml -f docker-compose.dev.yml build --parallel

    # Start services
    echo "🚀 Starting services..."
    docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

    # Wait for services to be ready
    echo "⏳ Waiting for services to be ready..."
    sleep 10

    # Check health
    if check_service_health 5; then
        print_success "All services started successfully!"
    fi

    echo ""
    echo "📍 Services URLs:"
    echo "  Frontend:     http://localhost:3000"
    echo "  Backend:      http://localhost:8001"
    echo "  API Docs:     http://localhost:8001/docs"
}

# Function to restart services (quick)
restart_services() {
    print_status "Quick restart with cache preservation"
    echo "📦 Preserving Docker cache to avoid re-downloading 2GB+ dependencies"

    cleanup_processes

    # Stop containers but preserve volumes AND cache
    echo "⏹️  Stopping containers (preserving volumes & cache)..."
    docker-compose -f docker-compose.yml -f docker-compose.dev.yml down --remove-orphans

    start_services

    print_success "Quick restart complete!"
    echo "💡 Cache preserved - saved ~2GB download time"
}

# Function to full restart
full_restart() {
    print_status "Full restart with cleanup"

    cleanup_processes

    # Stop and remove containers
    echo "⏹️  Stopping and removing containers..."
    docker-compose -f docker-compose.yml -f docker-compose.dev.yml down --volumes --remove-orphans

    # Smart cleanup: remove containers but keep expensive caches
    echo "🗑️  Smart cleanup (preserving PyTorch cache)..."
    docker system prune -f --volumes --filter "label!=cache.keep"
    docker network prune -f

    start_services

    print_success "Full restart complete!"
}

# Function to rebuild dependencies
rebuild_dependencies() {
    print_warning "⚠️  This will re-download ALL dependencies (2GB+ PyTorch)"
    read -p "Are you sure? (y/N): " -n 1 -r
    echo

    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_status "Rebuild cancelled"
        return 0
    fi

    print_status "Rebuilding dependencies (this will take 5-10 minutes)..."

    cleanup_processes

    # Complete cleanup including cache
    echo "🗑️  Complete cleanup (removing all cache)..."
    docker-compose -f docker-compose.yml -f docker-compose.dev.yml down --volumes --remove-orphans
    docker system prune -af --volumes

    # Rebuild without cache
    echo "🔨 Rebuilding from scratch (re-downloading PyTorch)..."
    DOCKER_BUILDKIT=1 docker-compose -f docker-compose.yml -f docker-compose.dev.yml build --no-cache --parallel

    # Start services
    echo "🚀 Starting services..."
    docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

    # Wait and check health
    echo "⏳ Waiting for services to be ready..."
    sleep 15
    check_service_health 10

    print_success "Dependency rebuild complete!"
}

# Function to stop services
stop_services() {
    print_status "Stopping all services..."

    cleanup_processes
    docker-compose -f docker-compose.yml -f docker-compose.dev.yml down --remove-orphans

    print_success "All services stopped"
}

# Function to show status
show_status() {
    print_status "Checking service status..."

    echo ""
    echo "🐳 Docker Containers:"
    docker-compose -f docker-compose.yml -f docker-compose.dev.yml ps

    echo ""
    echo "🏥 Service Health:"
    if curl -s http://localhost:8001/health > /dev/null 2>&1; then
        print_success "Backend (port 8001): Healthy"
    else
        print_error "Backend (port 8001): Not responding"
    fi

    if curl -s http://localhost:3000 > /dev/null 2>&1; then
        print_success "Frontend (port 3000): Responding"
    else
        print_error "Frontend (port 3000): Not responding"
    fi

    echo ""
    echo "📊 Resource Usage:"
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"

    echo ""
    echo "📍 URLs:"
    echo "  Frontend:     http://localhost:3000"
    echo "  Backend:      http://localhost:8001"
    echo "  API Docs:     http://localhost:8001/docs"
}

# Function to show logs
show_logs() {
    print_status "Showing service logs..."
    docker-compose -f docker-compose.yml -f docker-compose.dev.yml logs -f
}

# Function for emergency reset
emergency_reset() {
    print_warning "⚠️  EMERGENCY RESET - This will remove ALL Docker data"
    read -p "Are you absolutely sure? This cannot be undone! (y/N): " -n 1 -r
    echo

    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_status "Emergency reset cancelled"
        return 0
    fi

    print_status "Performing emergency reset..."

    cleanup_processes

    # Stop everything
    docker-compose -f docker-compose.yml -f docker-compose.dev.yml down --volumes --remove-orphans

    # Remove all Docker data
    echo "🗑️  Removing all Docker containers, images, and volumes..."
    docker system prune -af --volumes
    docker volume prune -af
    docker network prune -af

    # Clean up any remaining files
    rm -rf frontend/.next data/vector_db/* 2>/dev/null || true

    print_success "Emergency reset complete!"
    print_status "Run '$0 start' to begin fresh setup"
}

# Main script logic
case "${1:-restart}" in
    "start"|"up")
        start_services
        ;;
    "restart"|"reload")
        restart_services
        ;;
    "full"|"clean")
        full_restart
        ;;
    "rebuild"|"rebuild-deps")
        rebuild_dependencies
        ;;
    "stop"|"down")
        stop_services
        ;;
    "status"|"ps")
        show_status
        ;;
    "logs")
        show_logs
        ;;
    "emergency"|"reset")
        emergency_reset
        ;;
    "help"|"-h"|"--help")
        show_usage
        ;;
    *)
        print_error "Unknown command: $1"
        echo ""
        show_usage
        exit 1
        ;;
esac