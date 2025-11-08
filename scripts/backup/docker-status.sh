#!/bin/bash

# 🚀 Tutor AI - Docker Status Check Script
# Check container status, logs, and health

echo "📊 Tutor AI - Docker Status"
echo "=========================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running"
    exit 1
fi

echo "🐳 Container Status:"
echo "===================="
docker-compose -f docker-compose.yml -f docker-compose.dev.yml ps

echo ""
echo "🏥 Health Checks:"
echo "================"

# Backend health check
echo -n "Backend (http://localhost:8001/health): "
if curl -s http://localhost:8001/health 2>/dev/null | grep -q "healthy\|OK\|status.*ok"; then
    echo "✅ Healthy"
else
    echo "❌ Unhealthy or not responding"
fi

# Frontend health check
echo -n "Frontend (http://localhost:3000): "
if curl -s http://localhost:3000 2>/dev/null | grep -q "html\|HTML\|DOCTYPE"; then
    echo "✅ Responding"
else
    echo "❌ Not responding"
fi

echo ""
echo "📝 Recent Logs (last 20 lines each):"
echo "===================================="

echo "--- Backend Logs ---"
docker-compose -f docker-compose.yml -f docker-compose.dev.yml logs --tail=20 backend 2>/dev/null | tail -20

echo ""
echo "--- Frontend Logs ---"
docker-compose -f docker-compose.yml -f docker-compose.dev.yml logs --tail=20 frontend 2>/dev/null | tail -20

echo ""
echo "--- Redis Logs ---"
docker-compose -f docker-compose.yml -f docker-compose.dev.yml logs --tail=10 redis 2>/dev/null | tail -10

echo ""
echo "💡 Quick Actions:"
echo "================="
echo "• View all logs: docker-compose -f docker-compose.yml -f docker-compose.dev.yml logs -f"
echo "• Restart services: ./docker-restart.sh"
echo "• Stop services: ./docker-stop.sh"
echo "• Full reset: ./docker-emergency-reset.sh"