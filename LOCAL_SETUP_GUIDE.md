# 🚀 Guida Setup Locale - Tutor AI
*Setup semplificato per sviluppo locale senza autenticazione*

## 📋 Overview

Tutor AI può essere eseguito localmente con configurazione minima. L'autenticazione è stata disabilitata per facilitare lo sviluppo e il testing.

## 🎯 Caratteristiche del Setup Locale

### ✅ **Abilitato:**
- Tutte le funzionalità core AI (RAG, chat, quiz, mindmap)
- Caricamento e elaborazione documenti
- Ricerca avanzata
- Analytics di studio
- Export funzionalità
- Temi chiaro/scuro

### ❌ **Disabilitato:**
- Autenticazione utenti
- Social features
- Collaborazione multiutente
- Notifiche email
- Funzionalità enterprise

## 🚀 Setup Rapido

### 1. Prerequisiti

```bash
# Python 3.8+
python --version

# Node.js 18+
node --version
npm --version

# Docker (opzionale, per containerizzazione)
docker --version
```

### 2. Clona il Repository

```bash
git clone <repository-url>
cd tutor-ai
```

### 3. Setup Backend

```bash
cd backend

# Crea ambiente virtuale
python -m venv venv

# Attiva ambiente
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# Installa dipendenze
pip install -r requirements.txt

# Configura le variabili d'ambiente
cp .env.example .env
```

### 4. Configura le Credenziali LLM

Modifica il file `.env` nel backend:

```env
# Scegli tra OpenAI o LLM locale
LLM_TYPE=openai

# Opzione 1: OpenAI
OPENAI_API_KEY=la_tua_chiave_api
OPENAI_MODEL=gpt-4o

# Opzione 2: LLM Locale (Ollama)
# LLM_TYPE=local
# LOCAL_LLM_URL=http://localhost:11434/v1
# LOCAL_LLM_MODEL=llama3.1

# Database (auto-creato)
DATABASE_URL=sqlite:///./data/app.db

# Storage locale
UPLOAD_DIR=./data/uploads
VECTOR_DB_PATH=./data/vector_db
```

### 5. Setup Frontend

```bash
cd frontend

# Installa dipendenze
npm install

# Oppure con yarn
yarn install
```

### 6. Avvia le Applicazioni

In due terminali separati:

```bash
# Terminal 1: Backend
cd backend
python main.py

# Terminal 2: Frontend
cd frontend
npm run dev
```

L'applicazione sarà disponibile su:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000

## 🔧 Configurazioni LLM

### OpenAI Setup

1. Vai su [OpenAI Platform](https://platform.openai.com/)
2. Crea un account e ottieni la tua API key
3. Aggiungi la key nel file `.env`

### LLM Locale (Ollama)

1. Installa Ollama:
   ```bash
   curl -fsSL https://ollama.ai/install.sh | sh
   ```

2. Scarica un modello:
   ```bash
   ollama pull llama3.1
   ollama pull mistral
   ```

3. Configura le variabili d'ambiente:
   ```env
   LLM_TYPE=local
   LOCAL_LLM_URL=http://localhost:11434/v1
   LOCAL_LLM_MODEL=llama3.1
   ```

### LM Studio Setup

1. Scarica e installa LM Studio
2. Carica un modello LLM
3. Avvia il server locale (di solito su http://localhost:1234)
4. Configura l'URL nel file `.env`

## 🐳 Docker Setup (Opzionale)

Per un setup più pulito, usa Docker:

```bash
# Avvia tutto con Docker Compose
docker-compose -f docker-compose.dev.yml up

# oppure build e avvia
docker-compose -f docker-compose.dev.yml up --build
```

## 📚 Uso Base

### 1. Crea un Corso

1. Vai su http://localhost:3000
2. Clicca "Nuovo Corso"
3. Inserisci nome, descrizione e materia
4. Salva il corso

### 2. Carica Materiali

1. Seleziona il corso creato
2. Vai alla sezione "Materiali"
3. Trascina i file PDF o clicca per selezionarli
4. Attendi l'indicizzazione automatica

### 3. Chatta con il Tutor AI

1. Seleziona un corso con materiali caricati
2. Clicca "Chat con Tutor"
3. Fai domande sui contenuti del corso
4. Il tutor risponderà basandosi sui tuoi materiali

### 4. Genera Quiz

1. Clicca "Crea Quiz" nel corso
2. Scegli argomento e difficoltà
3. Il sistema genererà domande basate sui materiali
4. Rispondi e verifica le tue conoscenze

### 5. Esplora Mappe Concettuali

1. Clicca "Mappa Concettuale"
2. Inserisci un argomento
3. L'AI genererà una mappa interattiva
4. Esplora i concetti e le loro relazioni

## 🗂️ Struttura File

```
tutor-ai/
├── backend/                 # Backend FastAPI
│   ├── services/           # Servizi AI e business logic
│   │   ├── rag_service.py     # Sistema RAG
│   │   ├── llm_service.py     # Integrazione LLM
│   │   ├── course_service.py  # Gestione corsi
│   │   └── study_tracker.py    # Tracking progressi
│   ├── utils/              # Utility functions
│   │   └── error_handlers.py  # Error management
│   ├── middleware/         # Middleware
│   │   └── rate_limiter.py    # Rate limiting
│   └── main.py             # Entry point
├── frontend/               # Frontend Next.js
│   ├── src/
│   │   ├── app/           # Pagine
│   │   ├── components/    # Componenti React
│   │   ├── types/         # TypeScript definitions
│   │   ├── lib/           # Utility e config
│   │   └── hooks/         # React hooks
│   └── package.json
└── data/                   # Dati locali
    ├── courses/           # Corsi e materiali
    ├── vector_db/         # Database vettoriale
    └── uploads/           # File caricati
```

## 🔒 Sicurezza (Setup Locale)

### 🛡️ **Protezioni Attive:**
- Validazione input file upload
- CORS configuration
- Rate limiting permissivo
- Error sanitization

### 🔓 **Semplificato per Locale:**
- No autenticazione richiesta
- No password requirements
- Accesso diretto a tutte le funzionalità
- Limiti di upload più permissivi

## 📊 Performance e Limitazioni

### Performance
- **Vector Database**: ChromaDB per ricerca semantica
- **File Processing**: Asincrono con progress tracking
- **Rate Limiting**: Protezione base per API
- **Caching**: Redis opzionale per performance

### Limitazioni Locali
- Single user (multi-threading, non multi-user)
- Database locale (sqlite)
- No cloud synchronization
- No email notifications
- No collaborative features

## 🐛 Troubleshooting

### Problemi Comuni

**Backend non parte:**
```bash
# Verifica dipendenze Python
pip install -r requirements.txt

# Verifica ambiente virtuale
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows
```

**LLM non risponde:**
```bash
# Verifica API key OpenAI
# Oppure controlla che Ollama sia in esecuzione:
ollama list

# Testa Ollama:
curl http://localhost:11434/api/generate
```

**Frontend non si connette:**
- Assicurati che il backend sia in esecuzione su porta 8000
- Controlla le CORS configuration nel backend
- Verifica network tab nel browser

**File upload non funziona:**
- Controlla che la cartella `data/uploads` esista
- Verifica i permessi di scrittura
- Controlla i log del backend per errori specifici

## 🚀 Suggerimenti Sviluppo

### 1. **Monito del Performance**
```bash
# Backend logs
python main.py

# Frontend development mode
npm run dev

# Controlla utilizzo risorse
htop  # o Activity Monitor su Windows/Mac
```

### 2. **Database Management**
```bash
# Esplora database SQLite
sqlite3 data/app.db

# Tabelle disponibili
.tables

# Query esempio
SELECT * FROM courses;
```

### 3. **Testing**
```bash
# Test backend
cd backend
python -m pytest

# Test frontend
cd frontend
npm test
```

## 🔄 Aggiornamenti

Per aggiornare l'applicazione:

```bash
# Aggiorna dipendenze backend
cd backend
pip install -r requirements.txt --upgrade

# Aggiorna dipendenze frontend
cd frontend
npm update
```

## 📞 Supporto

Per problemi o domande:

1. Controlla i log del backend e del browser
2. Verifica la configurazione nel file `.env`
3. Consulta la documentazione in `/docs`
4. Crea una issue su GitHub

---

**Tutor AI** - Il tuo compagno di studio intelligente per l'università! 🎓✨

*Setup locale ottimizzato per sviluppo e testing veloce*