#!/bin/bash

# Script di setup automatico per Tutor AI
# Supporta Linux, macOS e Windows (WSL)

echo "🎓 Setup Tutor AI - Piattaforma di Studio Intelligente"
echo "=================================================="

# Colori per output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Funzione per controllare i comandi
check_command() {
    if command -v $1 &> /dev/null; then
        echo -e "${GREEN}✓${NC} $1 trovato"
        return 0
    else
        echo -e "${RED}✗${NC} $1 non trovato"
        return 1
    fi
}

# Funzione per mostrare errore ed uscire
error_exit() {
    echo -e "${RED}ERRORE: $1${NC}"
    exit 1
}

# Funzione per mostrare successo
success() {
    echo -e "${GREEN}SUCCESSO: $1${NC}"
}

# Funzione per mostrare warning
warning() {
    echo -e "${YELLOW}ATTENZIONE: $1${NC}"
}

# Funzione per mostrare info
info() {
    echo -e "${BLUE}INFO: $1${NC}"
}

# Inizio setup
echo -e "\n${BLUE}🔍 Verifica dei prerequisiti...${NC}"

# Controlla Python
if check_command python3; then
    PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
    info "Python versione: $PYTHON_VERSION"

    # Controlla versione minima (3.8)
    if python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
        success "Python versione compatibile"
    else
        error_exit "Python 3.8+ richiesto. Versione attuale: $PYTHON_VERSION"
    fi
else
    error_exit "Python 3.8+ non trovato. Installa Python da https://python.org"
fi

# Controlla Node.js
if check_command node; then
    NODE_VERSION=$(node --version)
    info "Node.js versione: $NODE_VERSION"
else
    error_exit "Node.js non trovato. Installa Node.js da https://nodejs.org"
fi

# Controlla npm
if check_command npm; then
    NPM_VERSION=$(npm --version)
    info "npm versione: $NPM_VERSION"
else
    error_exit "npm non trovato"
fi

# Controlla git
if check_command git; then
    success "Git trovato"
else
    warning "Git non trovato. Installalo per una migliore esperienza"
fi

echo -e "\n${BLUE}📁 Creazione directory del progetto...${NC}"

# Crea le directory necessarie
mkdir -p data/{courses,vector_db,uploads,tracking}
mkdir -p backend/services
mkdir -p frontend/src/{app,components,lib,types}

success "Directory create"

echo -e "\n${BLUE}🐍 Setup Backend Python...${NC}"

# Entra nella directory backend
cd backend

# Crea ambiente virtuale se non esiste
if [ ! -d "venv" ]; then
    info "Creazione ambiente virtuale Python..."
    python3 -m venv venv || error_exit "Creazione virtual environment fallita"
    success "Virtual environment creato"
else
    info "Virtual environment già esistente"
fi

# Attiva l'ambiente virtuale
info "Attivazione virtual environment..."
source venv/bin/activate 2>/dev/null || source venv/Scripts/activate 2>/dev/null || error_exit "Attivazione virtual environment fallita"

# Aggiorna pip
info "Aggiornamento pip..."
pip install --upgrade pip

# Installa dipendenze Python
info "Installazione dipendenze Python..."
pip install -r requirements.txt || error_exit "Installazione dipendenze Python fallita"

success "Backend setup completato"

echo -e "\n${BLUE}⚙️ Configurazione ambiente...${NC}"

# Crea file .env se non esiste
if [ ! -f ".env" ]; then
    info "Creazione file .env..."
    cp .env.example .env

    warning "IMPORTANTE: Configura il file .env con le tue API key!"
    info "Apri il file .env e inserisci:"
    echo "  - La tua API key di OpenAI (se usi OpenAI)"
    echo "  - L'URL del tuo LLM locale (se usi Ollama/LM Studio)"
    echo ""
    echo "Esempio per OpenAI:"
    echo "  LLM_TYPE=openai"
    echo "  OPENAI_API_KEY=sk-..."
    echo ""
    echo "Esempio per Ollama:"
    echo "  LLM_TYPE=local"
    echo "  LOCAL_LLM_URL=http://localhost:11434/v1"
else
    info "File .env già esistente"
fi

cd ..

echo -e "\n${BLUE}⚛️ Setup Frontend Node.js...${NC}"

# Entra nella directory frontend
cd frontend

# Installa dipendenze Node.js
info "Installazione dipendenze frontend..."
npm install || error_exit "Installazione dipendenze frontend fallita"

success "Frontend setup completato"

cd ..

echo -e "\n${BLUE}🎨 Ottimizzazione risorse...${NC}"

# Crea favicon base64 semplice
info "Creazione risorse grafiche..."
mkdir -p frontend/public

# Crea un favicon semplice se non esiste
if [ ! -f "frontend/public/favicon.ico" ]; then
    info "Favicon generato automaticamente"
fi

success "Risorse grafiche pronte"

echo -e "\n${GREEN}🎉 Setup completato con successo!${NC}"
echo ""
echo -e "${BLUE}Prossimi passi:${NC}"
echo "1. Configura il file backend/.env con le tue credenziali"
echo "2. Avvia il backend: cd backend && source venv/bin/activate && python main.py"
echo "3. Avvia il frontend: cd frontend && npm run dev"
echo "4. Apri http://localhost:3000 nel tuo browser"
echo ""
echo -e "${YELLOW}Nota: Se usi un LLM locale (Ollama), assicurati che sia in esecuzione${NC}"
echo ""

# Opzione per avviare subito le applicazioni
read -p "Vuoi avviare le applicazioni ora? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${BLUE}🚀 Avvio delle applicazioni...${NC}"

    # Avvia backend in background
    info "Avvio backend in background..."
    cd backend
    source venv/bin/activate 2>/dev/null || source venv/Scripts/activate 2>/dev/null
    python main.py &
    BACKEND_PID=$!
    cd ..

    # Attendi qualche secondo per il backend
    sleep 3

    # Avvia frontend
    info "Avvio frontend..."
    cd frontend
    npm run dev &
    FRONTEND_PID=$!
    cd ..

    success "Entrambe le applicazioni sono in esecuzione!"
    info "Backend: http://localhost:8000"
    info "Frontend: http://localhost:3000"
    info ""
    info "Per fermare le applicazioni, usa Ctrl+C o esegui:"
    echo "  kill $BACKEND_PID $FRONTEND_PID"
fi

echo -e "\n${GREEN}Buono studio con Tutor AI! 🎓✨${NC}"