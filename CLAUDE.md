# 🎓 Tutor AI - Claude AI Assistant Documentation

<div align="center">

![Tutor AI Logo](https://img.shields.io/badge/Tutor-AI-Blue?style=for-the-badge&logo=openai&logoColor=white)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Next.js](https://img.shields.io/badge/Next.js-16.0.1-black?logo=next.js)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115.0-green?logo=fastapi)](https://fastapi.tiangolo.com/)

**An intelligent tutoring system for university courses with AI-powered learning**

[Quick Start](#-quick-start) • [Features](#-features) • [Architecture](#-architecture--technology-stack) • [API Docs](#-api-endpoints) • [Development](#-development-guidelines)

</div>

## 📋 Documentation Structure

- **[CLAUDE_QUICKSTART.md](./CLAUDE_QUICKSTART.md)** - Quick start guide & setup
- **[CLAUDE_DETAILED.md](./CLAUDE_DETAILED.md)** - Complete system documentation
- **[CLAUDE.md](./CLAUDE.md)** - This file - essential overview

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Node.js 18+
- Docker & Docker Compose (recommended)

### Docker Setup (Recommended)
```bash
# Clone and start
git clone <repository-url>
cd tutor-ai
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build

# Access
# Frontend: http://localhost:3000
# Backend: http://localhost:8001
```

### Local Development
```bash
# Backend
cd backend && pip install -r requirements.txt && python3 main.py &

# Frontend
cd ../frontend && npm install && npm run dev
```

### Environment Configuration
Copy `.env.example` to `.env` and configure API keys:
```env
OPENAI_API_KEY=your_key
OPENROUTER_API_KEY=your_key
ZAI_API_KEY=your_key
LOCAL_LLM_URL=http://localhost:11434/v1
```

## ✨ Key Features

### 🎯 Core Capabilities
- **🤖 Multi-Provider AI Support**: OpenAI, OpenRouter, Z.AI, local models (Ollama/LM Studio)
- **📚 Intelligent Document Processing**: PDF upload, OCR, text extraction, vector indexing
- **💬 Context-Aware AI Chat**: RAG-powered conversations with source attribution
- **📊 Advanced Learning Analytics**: Progress tracking, concept mastery, performance insights
- **🧠 Cognitive Learning Engine**: Evidence-based learning principles (Spaced Repetition, Active Recall, Dual Coding)
- **🎨 Interactive Visualizations**: Concept maps, learning charts, progress dashboards
- **📝 Smart Assessment**: Auto-generated quizzes with multiple difficulty levels and formats
- **🔄 Real-time Collaboration**: Session management and learning history tracking

### 🚀 Advanced Features
- **🗺️ Visual Mind Mapping**: Interactive concept maps with progress tracking
- **📄 Slide Generation**: AI-powered presentation creation
- **🎯 Personalized Learning Paths**: Adaptive study plans based on performance
- **📈 Multi-modal Learning**: Support for text, visual, and interactive content
- **🔍 Advanced Search**: Hybrid semantic and keyword search across materials
- **📱 Responsive Design**: Mobile-friendly interface for learning on-the-go

## 🏗️ Architecture & Technology Stack

### Backend (Python/FastAPI)
- **Framework**: FastAPI 0.115.0 with Uvicorn server
- **AI/ML Stack**: LangChain 0.3.0, ChromaDB 0.5.20, Sentence Transformers 3.3.1, PyTorch 2.5.1
- **Document Processing**: PyMuPDF, PyPDF2, pdfplumber, Tesseract, EasyOCR, OpenCV
- **Database**: SQLAlchemy 2.0.36 with aiosqlite
- **Caching**: Redis 5.2.0
- **Async Support**: Full async/await implementation

### Frontend (Next.js/React)
- **Framework**: Next.js 16.0.1 with React 19.2.0
- **Language**: TypeScript 5.6.3
- **Styling**: TailwindCSS 4.1.16 with custom components
- **State Management**: Zustand 5.0.1 + TanStack React Query 5.62.0
- **UI Components**: Headless UI 2.2.9, Radix UI primitives, Heroicons 2.2.0, Lucide React
- **Visualization**: D3.js 7.9.0, ReactFlow 11.11.4, Recharts 3.3.0
- **PDF Rendering**: ReactPDF 9.2.1 and PDF.js 4.10.38

## 📁 Project Structure

```
tutor-ai/
├── backend/                    # Python FastAPI backend
│   ├── services/               # Core business logic
│   │   ├── rag_service.py     # RAG system implementation
│   │   ├── llm_service.py     # LLM integration
│   │   ├── course_service.py  # Course management
│   │   └── study_tracker.py   # Progress tracking
│   ├── models/                # Data models and schemas
│   ├── utils/                 # Utility functions
│   └── main.py               # FastAPI application entry point
├── frontend/                  # Next.js frontend
│   ├── src/
│   │   ├── app/              # Next.js App Router pages
│   │   │   └── courses/      # Course-related pages
│   │   ├── components/       # Reusable React components
│   │   │   ├── BookCard.tsx
│   │   │   ├── CourseCard.tsx
│   │   │   └── ChatInterface.tsx
│   │   ├── lib/              # Utility libraries
│   │   └── hooks/            # Custom React hooks
│   └── public/               # Static assets
├── data/                     # Local data storage
│   ├── courses/              # Course data and materials
│   ├── vector_db/            # ChromaDB vector storage
│   ├── tracking/             # Study progress data
│   └── uploads/              # File upload storage
└── docker-compose*.yml       # Docker configurations
```

## 🧠 Cognitive Learning Engine (CLE)

Advanced **Cognitive Learning Engine** based on evidence-based cognitive science principles (2024-2025 research):

### ✅ Completed Phases
1. **Spaced Repetition System** - Enhanced SM-2 algorithm with auto-generation
2. **Active Recall Engine** - Multi-format questions across Bloom's taxonomy
3. **Dual Coding Service** - Visual-verbal integration with 10 element types

### 🔄 Upcoming Phases
- Phase 4: Interleaved Practice Scheduler
- Phase 5: Metacognition Framework
- Phase 6: Elaboration Network

## 📚 Core API Endpoints

### Course Management
- `GET /courses` - List all courses
- `POST /courses` - Create new course
- `GET /courses/{id}` - Get course details
- `PUT /courses/{id}` - Update course
- `DELETE /courses/{id}` - Delete course

### Document Management
- `POST /courses/{id}/upload` - Upload PDF documents
- `GET /courses/{id}/books` - List course books
- `PUT /courses/{id}/books/{book_id}` - Update book metadata
- `DELETE /courses/{id}/books/{book_id}` - Delete book

### AI Chat & RAG
- `POST /chat` - Chat with AI tutor
- `POST /course-chat` - Enhanced course-specific chat with session management
- `POST /search` - Advanced document search
- `POST /mindmap` - Generate mind maps
- `POST /quiz` - Generate quizzes

### Cognitive Learning APIs
- `POST /api/spaced-repetition/card` - Create learning card
- `GET /api/spaced-repetition/cards/due/{course_id}` - Get due cards for review
- `POST /api/active-recall/generate-questions` - Generate multi-format questions
- `POST /api/dual-coding/create` - Create integrated visual-verbal content

## ⚙️ Configuration

### Environment Variables
```env
# Backend
LLM_TYPE=openai
OPENAI_API_KEY=your_api_key
OPENAI_MODEL=gpt-4o
LOCAL_LLM_URL=http://localhost:11434/v1
DATABASE_URL=sqlite:///./data/app.db
REDIS_URL=redis://localhost:6379
UPLOAD_DIR=./data/uploads
VECTOR_DB_PATH=./data/vector_db
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
API_HOST=0.0.0.0
API_PORT=8001

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8001
NODE_ENV=development
PORT=3000
```

## 🔧 Port Configuration

**CRITICAL**: Maintain consistent port configuration to avoid connection issues:

### Standard Ports (NEVER CHANGE THESE)
- **Backend API**: Port `8001` (NOT 8000)
- **Frontend**: Port `3000` (NOT 5000)
- **Redis**: Port `6379`
- **CORS Origins**: `http://localhost:3000,http://127.0.0.1:3000`

### Port Configuration Files
- **docker-compose.yml**: Backend service uses `8001:8001`
- **docker-compose.dev.yml**: Backend service uses `8001:8001`
- **backend/Dockerfile**: EXPOSE and CMD use port `8001`
- **backend/main.py**: `uvicorn.run(app, host="0.0.0.0", port=8001)`
- **frontend/.env.local**: `NEXT_PUBLIC_API_URL=http://localhost:8001`
- **frontend/next.config.js**: Backend URL points to port `8001`
- **.env.example**: `NEXT_PUBLIC_API_URL=http://localhost:8001`

### URL Endpoints
- **Backend Health**: `http://localhost:8001/health`
- **Frontend App**: `http://localhost:3000`
- **API Docs**: `http://localhost:8001/docs`

## 🐳 Docker Commands

### 🚀 Unified Docker Management Script

**IMPORTANT**: Use the single unified Docker script for all operations:

```bash
# Single script for all Docker operations
./docker.sh [COMMAND]
```

**Available Commands:**
- `./docker.sh` or `./docker.sh restart` - Quick restart with cache preservation
- `./docker.sh start` - Start services
- `./docker.sh full` - Full restart with cleanup (preserves PyTorch cache)
- `./docker.sh rebuild` - Rebuild dependencies (re-downloads 2GB+ PyTorch)
- `./docker.sh stop` - Stop all services cleanly
- `./docker.sh status` - Check service status and show logs
- `./docker.sh logs` - Show service logs
- `./docker.sh emergency` - Emergency reset (complete cleanup)
- `./docker.sh help` - Show help message

**🚀 Cache Optimization Strategy (CRITICAL for Performance):**

The unified script is optimized to **avoid re-downloading PyTorch CUDA libraries (~2GB)**:

- **`./docker.sh restart`** - **NEVER re-downloads** PyTorch unless `requirements.txt` changed
  - Rebuilds only code changes (seconds vs minutes)
  - Preserves pip cache where PyTorch is stored
  - Uses BuildKit for intelligent layer caching

- **`./docker.sh full`** - **PRESERVES** PyTorch cache during cleanup
  - Cleans containers but keeps pip cache
  - Does NOT use `--no-cache` flag
  - Only rebuilds if dependencies actually changed

- **`./docker.sh rebuild`** - **ONLY** when dependencies change
  - Re-downloads PyTorch and all libraries
  - Takes 5-10 minutes due to 2GB+ downloads
  - Interactive confirmation before proceeding

**🔥 Performance Impact:**
- **Code changes only**: ~10-30 seconds (cache preserved)
- **Dependency changes**: ~5-10 minutes (2GB+ download)
- **Without cache optimization**: Every rebuild = 5-10 minutes ❌

**Examples:**
```bash
# Development workflow
./docker.sh                    # Quick restart (most common)
./docker.sh status             # Check if services are running
./docker.sh logs               # View logs
./docker.sh stop               # Stop when done

# Maintenance workflow
./docker.sh full               # When services act weird
./docker.sh rebuild            # Only when requirements.txt changes
./docker.sh emergency          # Last resort cleanup
```

**📁 Script Organization:**
- **Old scripts**: Moved to `scripts/backup/` for reference
- **New unified script**: `./docker.sh` in project root
- **All functionality**: Consolidated into single script with subcommands

### Manual Docker Commands

#### Development Environment
```bash
# Start with hot reload
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# Rebuild and start
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build

# Start in background
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

#### Complete Reset (When Issues Occur)
```bash
docker-compose down --volumes --remove-orphans
docker system prune -f
pkill -9 -f "python.*main" && pkill -9 -f "next.*dev"
rm -rf frontend/.next data/vector_db/*
docker-compose up --build
```

**⚠️ Avoid Manual Commands - Use Unified Script Instead**
Manual commands don't preserve cache optimization. Always prefer the unified `./docker.sh` script.

### 🎯 Docker Cache Best Practices

**When to Use Each Command:**

| Situation | Command to Use | Time | Why |
|-----------|---------------|------|-----|
| **Code changes only** | `./docker.sh restart` | 10-30s | Preserves PyTorch cache |
| **Minor issues** | `./docker.sh full` | 1-2min | Cleans containers, keeps cache |
| **requirements.txt changed** | `./docker.sh rebuild` | 5-10min | Re-downloads dependencies |
| **Major issues** | `./docker.sh emergency` | 10-15min | Complete reset |
| **Checking status** | `./docker.sh status` | 5s | Health monitoring |

**🔥 Cache Optimization Technical Details:**

1. **Dockerfile Optimization**: The backend Dockerfile uses multi-stage builds with cache mounts:
   ```dockerfile
   RUN --mount=type=cache,target=/root/.cache/pip \
       pip install -r requirements.txt
   ```

2. **BuildKit Integration**: All scripts use `DOCKER_BUILDKIT=1` for:
   - Better layer caching
   - Parallel builds
   - Cache export/import capabilities

3. **Pip Cache Preservation**: PyTorch (~2GB) is cached in `/root/.cache/pip` and preserved across restarts

4. **Layer Ordering**: Dockerfile layers are optimized to rebuild only when necessary:
   - System packages (rarely change)
   - Python dependencies (only when requirements.txt changes)
   - Application code (changes frequently)

**💡 Pro Tips:**
- **Never** use `--no-cache` unless updating dependencies
- **Always** use `./docker.sh restart` for development
- **Check** if `requirements.txt` changed before using `./docker.sh rebuild`
- **Monitor** cache usage with `docker system df`

## 🛠️ Development Guidelines

### Backend Development
- Use async/await for all I/O operations
- Follow FastAPI best practices for API design
- Implement proper error handling and logging
- Use Pydantic for data validation
- Keep service classes focused and single-purpose

### Frontend Development
- Use TypeScript for all new code
- Follow React best practices and hooks
- Implement proper error boundaries
- Use TailwindCSS for styling
- Ensure responsive design for all screen sizes

## 🆘 Common Issues & Solutions

### Docker Issues
**Problem**: Container fails to start with permission errors
**Solution**:
```bash
docker-compose down --volumes --remove-orphans
sudo chown -R $USER:$USER data/
docker-compose up --build
```

### Port Conflicts
**Problem**: Frontend shows 404 errors
**Solution**: Ensure ports 3000 (frontend) and 8001 (backend) are available

### AI Provider Issues
**Problem**: OpenAI API key not working
**Solution**: Verify key is correct, check `.env` file, ensure network connectivity

**Problem**: Local LLM not connecting
**Solution**: Verify Ollama/LM Studio is running, check model is downloaded

### Port Configuration Issues
**Problem**: Backend container unhealthy despite running
**Solution**:
1. Check if ports are consistent: Backend must use port 8001 in ALL files
2. Verify `backend/Dockerfile` EXPOSE and CMD use port 8001
3. Verify `docker-compose.yml` and `docker-compose.dev.yml` map 8001:8001
4. Restart containers: `./docker.sh restart`

**Problem**: Frontend shows 404 errors or can't connect to backend
**Solution**:
1. Ensure backend is healthy: `curl http://localhost:8001/health`
2. Check CORS origins include: `http://localhost:3000,http://127.0.0.1:3000`
3. Verify frontend `.env` has: `NEXT_PUBLIC_API_URL=http://localhost:8001`

### Document Processing Issues
**Problem**: PDF upload fails
**Solution**: Check file size (< 50MB), ensure PDF is not password protected

## 🔧 Troubleshooting Avanzato

### Problemi Ricorrenti e Soluzioni Uniformate

#### 1. Errori di Connessione Frontend-Backend
**Sintomi**:
- `GET http://localhost:8000/courses net::ERR_CONNECTION_REFUSED`
- `WebSocket connection to 'ws://localhost:3001/_next/webpack-hmr' failed`

**Causa Comune**: Il frontend ha cached configurazioni di porte errate (8000 invece di 8001, 3001 invece di 3000)

**Soluzione Standardizzata**:
```bash
# 1. Pulisci cache Docker e Next.js
docker-compose down frontend
rm -rf frontend/.next frontend/node_modules/.cache
docker system prune -f --volumes

# 2. Ricostruisci completamente
./docker.sh rebuild  # SOLO se necessario, altrimenti ./docker.sh restart

# 3. Verifica configurazione porte
grep -r "8000" frontend/src/  # Dovrebbe trovare solo riferimenti non-URL
grep -r "NEXT_PUBLIC_API_URL" frontend/  # Dovrebbe puntare a :8001
```

#### 2. Errori di Sintassi JavaScript/TypeScript
**Sintomi**:
- `Parsing ecmascript source code failed`
- `Expected ';', '}' or <eof>`

**Causa Comune**: Errori di sintassi in componenti React (es. dimenticare parentesi nelle arrow functions)

**Soluzione Standardizzata**:
```bash
# 1. Identifica file problematico dall'errore
# 2. Correggi sintassi (es: map(() => { invece di map(() => ({
# 3. Riavvia frontend solo
docker-compose restart frontend
```

#### 3. Problemi di Permessi Directory Backend
**Sintomi**:
- `PermissionError: [Errno 13] Permission denied: '/data'`
- Backend in restart loop

**Causa Comune**: Directory `./data` non esiste o permessi errati

**Soluzione Standardizzata**:
```bash
# 1. Crea directory con permessi corretti
mkdir -p ./data
chmod -R 777 ./data

# 2. Riavvia backend
docker-compose restart backend
```

#### 4. Container Backend Unhealthy
**Sintomi**:
- Backend shows "health: starting" ma non diventa mai healthy
- `curl http://localhost:8001/health` non risponde

**Soluzione Standardizzata**:
```bash
# 1. Controlla logs backend
docker-compose logs backend --tail 20

# 2. Se ci sono errori di avvio, risolvi e riavvia
./docker.sh restart

# 3. Se persiste, pulisci e ricostruisci
./docker.sh full
```

### Flusso di Troubleshooting Standard

**Step 1: Diagnosi Rapida**
```bash
./docker.sh status  # Verifica stato servizi
curl -s http://localhost:8001/health  # Test backend
curl -s -I http://localhost:3000 | head -1  # Test frontend
```

**Step 2: Identifica Problema**
- Se backend non risponde: `docker-compose logs backend`
- Se frontend non si connette: Controlla configurazione porte
- Se entrambi down: `./docker.sh restart`

**Step 3: Soluzione Mirata**
- Usa la soluzione specifica per il tipo di problema
- Evita sempre `./docker.sh rebuild` se non strettamente necessario

**Step 4: Verifica Finale**
```bash
./docker.sh status
curl -s http://localhost:8001/courses | jq '.courses | length'  # Test API
```

### Comandi di Emergenza
```bash
# Reset completo (ultima risorsa)
./docker.sh emergency

# Forza rebuild dependencies (solo se requirements.txt changes)
./docker.sh rebuild

# Pulizia cache mantenendo dati
./docker.sh full
```

### Checklist Pre-Avvio
✅ Directory `./data` esiste con permessi 777
✅ File `.env` configurato correttamente
✅ Niente processi su porte 8000/3001
✅ porte 8001/3000 libere
✅ `./docker.sh status` mostra tutti healthy

## 📖 Additional Resources

- **Complete Documentation**: [CLAUDE_DETAILED.md](./CLAUDE_DETAILED.md)
- **Quick Start Guide**: [CLAUDE_QUICKSTART.md](./CLAUDE_QUICKSTART.md)
- **Cognitive Learning Engine**: See detailed implementation in CLAUDE_DETAILED.md
- **API Reference**: Complete API documentation available in CLAUDE_DETAILED.md

## 🚀 Current Status

- **Cognitive Learning Engine**: Phases 1-3 Complete ✅
- **Authentication**: Removed for simplified local development
- **Course-Specific Chatbot**: Enhanced with session management
- **Local Setup**: Optimized for zero-config development
- **Performance**: <2s response time, 99.9% uptime target

---

<div align="center">

**🚀 Version: 2.0.0** • **📅 Updated: 2025-11-08** • **⭐ MIT License**

*For complete documentation, see [CLAUDE_DETAILED.md](./CLAUDE_DETAILED.md)*

</div>