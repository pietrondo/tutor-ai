#!/bin/bash

# 🚀 Tutor AI - Dependencies Rebuild Script
# Use ONLY when requirements.txt or package.json changes
# This script WILL re-download PyTorch and other large dependencies

set -e

echo "🔄 Tutor AI - Dependencies Rebuild"
echo "================================="
echo "⚠️  WARNING: This will re-download PyTorch (~2GB)"
echo "📋 Use this script ONLY when:"
echo "   • requirements.txt changed"
echo "   • package.json changed"
echo "   • You need to update Python/Node dependencies"
echo ""
read -p "Continue? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Cancelled"
    exit 1
fi

# Clean up processes
echo "🧹 Cleaning up existing processes..."
pkill -9 -f "python.*main" 2>/dev/null || true
pkill -9 -f "next.*dev" 2>/dev/null || true

# Stop containers
echo "⏹️  Stopping containers..."
docker-compose -f docker-compose.yml -f docker-compose.dev.yml down --volumes --remove-orphans

# Clean pip cache to force re-download
echo "🗑️  Cleaning pip cache (forcing PyTorch re-download)..."
docker builder prune -af

# Clean npm cache
echo "🗑️  Cleaning npm cache..."
docker run --rm -v tutor-ai-frontend_node_modules:/node_modules node:20-alpine npm cache clean --force 2>/dev/null || true

# Full rebuild with fresh cache
echo "🔨 Full dependency rebuild..."
echo "   • This WILL take 5-10 minutes"
echo "   • PyTorch CUDA libraries will be re-downloaded"
echo "   • All dependencies will be freshly installed"

DOCKER_BUILDKIT=1 docker-compose -f docker-compose.yml -f docker-compose.dev.yml build --no-cache --parallel

# Start services
echo "🚀 Starting services..."
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# Extended wait time for fresh builds
echo "⏳ Waiting for services to initialize (extended time for fresh build)..."
sleep 30

# Health checks
echo "🏥 Checking service health..."
max_attempts=15
attempt=1

while [ $attempt -le $max_attempts ]; do
    echo "Health check attempt $attempt/$max_attempts..."

    backend_healthy=false
    frontend_healthy=false

    if curl -s http://localhost:8001/health > /dev/null 2>&1; then
        echo "✅ Backend is healthy"
        backend_healthy=true
    else
        echo "⏳ Backend still starting..."
    fi

    if curl -s http://localhost:3000 > /dev/null 2>&1; then
        echo "✅ Frontend is responding"
        frontend_healthy=true
    else
        echo "⏳ Frontend still starting..."
    fi

    if [ "$backend_healthy" = true ] && [ "$frontend_healthy" = true ]; then
        echo ""
        echo "🎉 Dependencies rebuild complete!"
        echo "📍 Frontend: http://localhost:3000"
        echo "📍 Backend:  http://localhost:8001"
        echo "📍 API Docs: http://localhost:8001/docs"
        echo ""
        echo "💡 For future code changes, use: ./docker-restart.sh (much faster!)"
        exit 0
    fi

    sleep 15
    attempt=$((attempt + 1))
done

echo ""
echo "⚠️  Services are starting but may need more time"
echo "📍 Frontend: http://localhost:3000"
echo "📍 Backend:  http://localhost:8001"
echo "📍 API Docs: http://localhost:8001/docs"
echo ""
echo "💡 Check logs with: docker-compose logs -f"
echo "💡 For code changes only: ./docker-restart.sh (preserves dependencies)"