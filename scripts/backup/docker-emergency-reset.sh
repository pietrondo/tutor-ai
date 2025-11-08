#!/bin/bash

# 🚀 Tutor AI - Emergency Reset Script
# Complete cleanup when everything else fails
# WARNING: This will delete all data!

set -e

echo "🚨 Tutor AI - Emergency Reset"
echo "============================"
echo "⚠️  WARNING: This will delete ALL data!"
echo "⏱️  You have 10 seconds to cancel (Ctrl+C)..."
sleep 10

echo "🔥 Starting emergency reset..."

# Kill all related processes
echo "💀 Killing all related processes..."
pkill -9 -f "python.*main" 2>/dev/null || true
pkill -9 -f "next.*dev" 2>/dev/null || true
pkill -9 -f "uvicorn" 2>/dev/null || true
pkill -9 -f "node.*next" 2>/dev/null || true

# Stop and remove all containers
echo "🗑️  Removing all containers..."
docker-compose -f docker-compose.yml -f docker-compose.dev.yml down --volumes --remove-orphans 2>/dev/null || true

# Remove all Tutor AI related containers
echo "🧹 Removing Tutor AI containers..."
docker ps -a | grep tutor-ai | awk '{print $1}' | xargs -r docker rm -f 2>/dev/null || true

# Remove all related images
echo "🖼️  Removing Tutor AI images..."
docker images | grep tutor-ai | awk '{print $3}' | xargs -r docker rmi -f 2>/dev/null || true

# Clean up Docker completely
echo "🧼 Deep Docker cleanup..."
docker system prune -af --volumes 2>/dev/null || true
docker network prune -f 2>/dev/null || true
docker volume prune -f 2>/dev/null || true
docker builder prune -af 2>/dev/null || true

# Remove local data directories
echo "📁 Removing local data..."
rm -rf data/vector_db/*
rm -rf data/uploads/*
rm -rf data/tracking/*
rm -rf data/courses/*
rm -rf data/cache/*
rm -rf data/book_concept_cache.json
rm -rf data/cache_metrics.json
rm -rf data/concept_maps_backup.json

# Remove frontend build cache
echo "🏗️  Removing frontend cache..."
rm -rf frontend/.next
rm -rf frontend/node_modules/.cache

# Create fresh data directories
echo "📂 Creating fresh directories..."
mkdir -p data/vector_db
mkdir -p data/uploads
mkdir -p data/tracking
mkdir -p data/courses
mkdir -p data/cache

# Fix permissions
echo "🔐 Fixing permissions..."
chmod -R 755 data/
chmod -R 755 frontend/

echo ""
echo "🎉 Emergency reset complete!"
echo ""
echo "🚀 Starting fresh build..."
echo "========================="

# Fresh rebuild and start
DOCKER_BUILDKIT=1 docker-compose -f docker-compose.yml -f docker-compose.dev.yml build --no-cache --parallel

echo "🚀 Starting services..."
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# Wait for services
echo "⏳ Waiting for services to initialize..."
sleep 20

# Final health check
echo "🏥 Final health check..."
if curl -s http://localhost:8001/health > /dev/null 2>&1; then
    echo "✅ Backend is healthy"
else
    echo "⚠️  Backend may need more time to start"
fi

if curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo "✅ Frontend is responding"
else
    echo "⚠️  Frontend may need more time to start"
fi

echo ""
echo "🎉 Emergency reset and restart complete!"
echo "📍 Frontend: http://localhost:3000"
echo "📍 Backend:  http://localhost:8001"
echo "📍 API Docs: http://localhost:8001/docs"
echo ""
echo "💡 Check logs with: docker-compose logs -f"
echo "💡 Next time use: ./docker-restart.sh for quick restarts"