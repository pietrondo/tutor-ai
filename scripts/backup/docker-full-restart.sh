#!/bin/bash

# 🚀 Tutor AI - Full Docker Restart Script
# Complete restart with cleanup and optimization

set -e

echo "🔄 Tutor AI - Full Restart with Cleanup"
echo "======================================"

# Clean up any existing processes
echo "🧹 Cleaning up existing processes..."
pkill -9 -f "python.*main" 2>/dev/null || true
pkill -9 -f "next.*dev" 2>/dev/null || true

# Stop and remove containers
echo "⏹️  Stopping and removing containers..."
docker-compose -f docker-compose.yml -f docker-compose.dev.yml down --volumes --remove-orphans

# SMART CLEAN: Remove containers but keep expensive caches
echo "🗑️  Smart cleanup (preserving PyTorch cache)..."
echo "   • Removing containers and orphaned images"
echo "   • KEEPING pip cache with PyTorch (~2GB)"
echo "   • KEEPING apt cache for faster rebuilds"

# Remove containers and orphaned images but preserve build cache
docker system prune -f --volumes --filter "label!=cache.keep"
docker network prune -f

# SMART FULL REBUILD: Clean but preserve large dependencies
echo "🔨 Smart full rebuild (preserving PyTorch cache)..."
echo "   • NOT using --no-cache to preserve pip cache layers"
echo "   • PyTorch CUDA libraries will be reused if requirements.txt unchanged"

# Build with cache preservation (no --no-cache flag!)
DOCKER_BUILDKIT=1 docker-compose -f docker-compose.yml -f docker-compose.dev.yml build --parallel

# Start services
echo "🚀 Starting services..."
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 15

# Check service health
echo "🏥 Checking service health..."
max_attempts=10
attempt=1

while [ $attempt -le $max_attempts ]; do
    echo "Health check attempt $attempt/$max_attempts..."

    backend_healthy=false
    frontend_healthy=false

    if curl -s http://localhost:8001/health > /dev/null 2>&1; then
        echo "✅ Backend is healthy"
        backend_healthy=true
    else
        echo "❌ Backend not ready yet"
    fi

    if curl -s http://localhost:3000 > /dev/null 2>&1; then
        echo "✅ Frontend is responding"
        frontend_healthy=true
    else
        echo "⏳ Frontend still starting..."
    fi

    if [ "$backend_healthy" = true ] && [ "$frontend_healthy" = true ]; then
        echo ""
        echo "🎉 Full restart complete!"
        echo "📍 Frontend: http://localhost:3000"
        echo "📍 Backend:  http://localhost:8001"
        echo "📍 API Docs: http://localhost:8001/docs"
        exit 0
    fi

    sleep 10
    attempt=$((attempt + 1))
done

echo ""
echo "⚠️  Services are starting but may need more time"
echo "📍 Frontend: http://localhost:3000"
echo "📍 Backend:  http://localhost:8001"
echo "📍 API Docs: http://localhost:8001/docs"
echo ""
echo "💡 Check logs with: docker-compose logs -f"