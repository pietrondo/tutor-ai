#!/bin/bash

# 🚀 Tutor AI - Docker Stop Script
# Clean stop of all services

set -e

echo "⏹️  Tutor AI - Stopping Services"
echo "==============================="

# Clean up any existing processes first
echo "🧹 Cleaning up existing processes..."
pkill -9 -f "python.*main" 2>/dev/null || true
pkill -9 -f "next.*dev" 2>/dev/null || true

# Stop Docker containers
echo "🛑 Stopping Docker containers..."
docker-compose -f docker-compose.yml -f docker-compose.dev.yml down --remove-orphans

# Verify containers are stopped
echo "✅ Verifying containers are stopped..."
if ! docker-compose -f docker-compose.yml -f docker-compose.dev.yml ps -q | grep -q .; then
    echo "✅ All containers stopped successfully"
else
    echo "⚠️  Some containers may still be running"
    docker-compose -f docker-compose.yml -f docker-compose.dev.yml ps
fi

# Check if ports are freed
echo "🔍 Checking if ports are freed..."
if lsof -i :3000 2>/dev/null | grep -q .; then
    echo "⚠️  Port 3000 may still be in use:"
    lsof -i :3000
else
    echo "✅ Port 3000 is free"
fi

if lsof -i :8001 2>/dev/null | grep -q .; then
    echo "⚠️  Port 8001 may still be in use:"
    lsof -i :8001
else
    echo "✅ Port 8001 is free"
fi

echo ""
echo "🎉 All services stopped successfully!"
echo ""
echo "💡 To restart: ./docker-restart.sh"
echo "💡 To check status: ./docker-status.sh"