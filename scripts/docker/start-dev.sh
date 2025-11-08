#!/bin/bash

# Script per avviare l'ambiente di sviluppo ottimizzato
# Usa bind mount per hot reload e zero rebuild

set -e

echo "🚀 Avviando ambiente di sviluppo Tutor-AI..."

# Controlla se Docker è in esecuzione
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker non è in esecuzione. Avvia Docker prima di continuare."
    exit 1
fi

# Controlla se esistono i file .env
if [ ! -f "./backend/.env" ]; then
    echo "⚠️  File ./backend/.env non trovato. Creando template..."
    cat > ./backend/.env << EOF
# Environment variables per development
DEBUG=true
ENVIRONMENT=development
LOG_LEVEL=debug

# API Keys (da configurare)
OPENAI_API_KEY=your_openai_key_here
ZAI_API_KEY=your_zai_key_here

# Database
REDIS_URL=redis://redis:6379

# CORS
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,http://localhost:5000,http://127.0.0.1:5000
EOF
    echo "✅ Template .env creato. Modificalo con le tue API keys."
fi

echo "📦 Build immagini Docker con cache..."
docker-compose -f docker-compose.yml -f docker-compose.dev.yml build

echo "🔥 Avviando servizi con hot reload..."
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

echo "✅ Servizi avviati!"
echo "📱 Frontend: http://localhost:5000"
echo "🔧 Backend API: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo ""
echo "💡 I cambiamenti al codice si applicano automaticamente (hot reload)"
echo "🛑 Per fermare: Ctrl+C oppure 'docker-compose -f docker-compose.yml -f docker-compose.dev.yml down'"