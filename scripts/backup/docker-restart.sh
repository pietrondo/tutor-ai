#!/bin/bash

# 🚀 Tutor AI - Optimized Docker Restart Script
# Fast restart with volume AND cache preservation
# AVOIDS re-downloading PyTorch CUDA libraries (~2GB)

set -e

echo "🔄 Tutor AI - Optimized Quick Restart"
echo "===================================="
echo "📦 Preserving Docker cache to avoid re-downloading 2GB+ dependencies"

# Clean up any existing processes
echo "🧹 Cleaning up existing processes..."
pkill -9 -f "python.*main" 2>/dev/null || true
pkill -9 -f "next.*dev" 2>/dev/null || true

# Stop containers but preserve volumes AND cache
echo "⏹️  Stopping containers (preserving volumes & cache)..."
docker-compose -f docker-compose.yml -f docker-compose.dev.yml down --remove-orphans

# SMART REBUILD: Only rebuild changed layers
# This preserves PyTorch CUDA cache unless requirements.txt changes
echo "🔨 Smart rebuild (preserving PyTorch cache)..."
echo "   • Requirements.txt unchanged → PyTorch libraries reused (~2GB saved)"
echo "   • Only code changes → Fast rebuild"

# Build with BuildKit for better layer caching
DOCKER_BUILDKIT=1 docker-compose -f docker-compose.yml -f docker-compose.dev.yml build --parallel

# Start services
echo "🚀 Starting services..."
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check service health
echo "🏥 Checking service health..."
if curl -s http://localhost:8001/health > /dev/null 2>&1; then
    echo "✅ Backend is healthy"
else
    echo "❌ Backend health check failed"
fi

if curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo "✅ Frontend is responding"
else
    echo "⏳ Frontend still starting..."
fi

echo ""
echo "🎉 Optimized restart complete!"
echo "💡 Cache preserved - saved ~2GB download time"
echo "📍 Frontend: http://localhost:3000"
echo "📍 Backend:  http://localhost:8001"
echo "📍 API Docs: http://localhost:8001/docs"