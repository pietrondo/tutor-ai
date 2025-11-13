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

### 🚀 Quick Start with Unified Script (RECOMMENDED)

```bash
# Clone the repository
git clone <repository-url>
cd tutor-ai

# Start everything with one command
./start.sh dev

# Access the application
# Frontend: http://localhost:3001
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

**⚠️ IMPORTANT**: Docker containers are typically already running with `./start.sh dev`.
When performing tests or modifications, remember this and avoid generating new versions.
Instead, optimize the existing `start.sh` script or check if services are already running before attempting restarts.

## 🧪 Docker Testing Infrastructure

Tutor-AI includes comprehensive Docker testing infrastructure for system validation:

### Test Suites Available
- **Docker System Tests** (`tests/docker/docker_system_test.py`) - 34 tests covering containers, networking, volumes, and performance
- **E2E Integration Tests** (`tests/docker/e2e_integration_test.py`) - Complete workflow testing
- **Materials Validation Tests** (`tests/connectivity/materials_validation_test.py`) - File system and API validation
- **Docker Test Runner** (`tests/docker/run_docker_tests.sh`) - Master test orchestrator with diagnostics

### Running Docker Tests
```bash
# Run all Docker tests
./tests/docker/run_docker_tests.sh

# Quick tests only
./tests/docker/run_docker_tests.sh --quick

# Skip prerequisites and status checks
./tests/docker/run_docker_tests.sh --no-prereqs --no-status

# Run Docker diagnostics only
./tests/docker/run_docker_tests.sh --diagnostics
```

### Current Test Status ✅
- **Docker System Tests**: 73.5% success rate (25/34 tests passed)
- **Materials Validation**: 89.6% success rate (43/48 tests passed)
- **Backend Performance**: 2ms response time
- **Materials Available**: 48 PDF files (100% accessible)
- **API Endpoints**: Fully functional with 3 courses and 5 books

## 🆕 What’s New (RAG & Mindmap Enhancements)

- RAG Retrieval (Local‑Only)
  - Hybrid ranking (semantic + lexical) with FAISS pre‑selection when available
  - Clean text segmentation (`segments`) and source deduplication for higher precision
  - Adaptive chunking for very long texts to reduce CPU/memory footprint
  - Query caching (TTL 600s) with LRU eviction to speed repeated queries
- Generative Pipeline
  - Title refinement with LLM + stopword removal and safe timeout fallback (700ms)
  - Second pass NLP on titles (POS tagging + lemmatization/stemming + concept ranking)
  - Node fields extended with `recurrence` (dedup strength) and `synonyms` (merged variants)
- Mindmap UX
  - Inline tooltip on node title hover showing fused synonyms and origin references (cached client‑side TTL 1h)
  - Auto layout + zoom‑to‑fit once nodes load; compact rendering of summaries/activities
  - Sorted by priority and, on tie, by recurrence
- Metrics & Monitoring
  - Prometheus export: `GET /metrics` and `GET /metrics/prometheus`
  - RAG metrics: requests, cache hits, LLM timeouts, latency histogram

### Technical References

- Retrieval & NLP
  - `backend/services/rag_service.py`: hybrid similarity, FAISS pre‑selection, caching, segments
  - `backend/services/nlp_utils.py`: extract_nouns, normalize_terms (Snowball), rank_concepts (TF‑IDF)
  - `backend/app/api/mindmap_expand.py`: LLM title refinement, NLP pass, dedup (Jaro‑Winkler), recurrence/synonyms
- Frontend
  - `frontend/src/components/MindmapExplorer.tsx`: tooltip inline, sorting, compact text
  - `frontend/src/types/mindmap.ts`: `recurrence`, `synonyms` types
- Metrics
  - `backend/services/metrics.py`: Prometheus registry and JSON fallback
  - `backend/app/api/metrics_rag.py`: endpoints `/metrics/rag`, `/metrics/prometheus`, `/metrics`

## 📘 Usage Guide (Updated)

### Mindmap Generation (Book/PDF)

- Book scope
  - Endpoint: `POST /mindmap/generate` with body `{ course_id, book_id, scope: "book" }`
  - Behavior: aggregates concepts via RAG; titles refined (LLM + NLP); nodes include `recurrence`, `synonyms`
- PDF scope
  - Endpoint: `POST /mindmap/generate` with body `{ course_id, book_id, scope: "pdf", pdf_filename }`
  - Behavior: concepts from current PDF with concise titles and 2–3 sub‑nodes
- Legacy
  - `POST /mindmap` forwards to `/mindmap/generate`

### Tooltip & Caching

- Hover a node title to see fused synonyms and origin references (document/chunk), cached via LocalStorage TTL 1h
- Panel on the right also shows synonyms and references for the selected node

### Metrics Endpoints

- Prometheus scraping: `GET /metrics` or `GET /metrics/prometheus`
- RAG JSON: `GET /metrics/rag` → `{ mode, retrieval_count, average_retrieval_time_ms, query_cache_size }`

## 🧩 Examples

### Generate a Book Mindmap

```bash
curl -X POST http://localhost:8000/mindmap/generate \
  -H "Content-Type: application/json" \
  -d '{
    "course_id": "90a903c0-4ef6-4415-ae3b-9dbc70ad69a9",
    "book_id": "f92fed02-ecc3-48ea-b7af-7570464a2919",
    "scope": "book"
  }'
```

### Check Prometheus Metrics

```bash
curl http://localhost:8000/metrics
curl http://localhost:8000/metrics/rag
```

### Frontend Tooltip Behavior

- Hover the node title in the list to display synonyms and origin references overlay

## 📦 New Dependencies & System Requirements

- Optional (auto‑detected, safe fallbacks):
  - spaCy + Italian model (`it_core_news_sm`) for POS tagging
  - NLTK + SnowballStemmer for Italian stemming
  - scikit‑learn (TF‑IDF & cosine similarity)
  - FAISS for fast ANN pre‑selection (IndexFlatIP)
  - prometheus‑client for metrics export
- No remote LLM required for RAG: embeddings and retrieval are local
- LLM provider should be set to “local” in settings

## 🔄 Compatibility & Migration

- Backwards‑compatible APIs:
  - `POST /mindmap` remains available (forwarding to new generator)
  - Frontend types extended (`recurrence`, `synonyms`); existing consumers continue to work
- Migration Steps (optional features)
  - Install optional NLP libs:
    - `pip install spacy it-core-news-sm nltk scikit-learn`
    - `python -m spacy download it_core_news_sm`
  - FAISS install (optional): `pip install faiss-cpu`
  - Metrics: `pip install prometheus-client`
  - Ensure environment permits local LLM provider settings and timeouts

## 📄 Documentation & Versioning

- File format preserved; additions are in “What’s New”, “Usage Guide”, “Examples”, “Dependencies”, “Compatibility & Migration”
- Cross‑references included to backend/frontend files and endpoints
- Version entry: RAG & Mindmap Enhancements (2025‑11)
- PDF export (recommended):
  - Using pandoc: `pandoc CLAUDE.md -o docs/CLAUDE.pdf`
  - Or any Markdown to PDF pipeline in CI/CD


### Test Coverage
- ✅ Docker daemon and images
- ✅ Container health and connectivity
- ✅ Data persistence and volumes
- ✅ API functionality and documentation
- ✅ Materials system and file access
- ✅ Performance metrics
- ⚠️ Frontend networking (WSL2 limitation documented)

### Troubleshooting with Tests
```bash
# Check system status quickly
./tests/docker/run_docker_tests.sh --quick

# Run materials validation if file issues suspected
python3 tests/connectivity/materials_validation_test.py

# Run full diagnostics for comprehensive analysis
./tests/docker/run_docker_tests.sh --diagnostics
```

### Other Start Options

#### Docker Setup (Manual)
```bash
# Start development environment
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build

# Stop services
docker-compose down
```

#### Local Development (Advanced)
```bash
# Backend (requires Python 3.9+)
cd backend
pip install -r requirements.txt
python3 main.py  # Runs on port 8000

# Frontend (requires Node.js 18+)
cd ../frontend
npm install
npm run dev  # Runs on port 3000
```

### Environment Configuration
Copy `.env.example` to `backend/.env` and configure API keys:
```env
# AI Providers (choose at least one)
OPENAI_API_KEY=your_openai_key_here
ZAI_API_KEY=your_zai_key_here

# Optional: Local LLM
LOCAL_LLM_URL=http://localhost:11434/v1
```

### 🔥 Port Configuration - CRITICAL

**IMPORTANT**: Tutor-AI uses specific ports to avoid conflicts:
- **Frontend**: `http://localhost:3001` (NEVER 3000 or 4000)
- **Backend**: `http://localhost:8000` (NOT 8001)
- **API Docs**: `http://localhost:8000/docs`

If you see different ports, something is wrong! See Port Configuration section below.

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
- **📖 Direct PDF Reading System**: One-click PDF access from any page with intelligent navigation

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
- `GET /courses/{id}/materials` - List all course materials with direct reading URLs
- `GET /courses/{id}/books/{book_id}/materials` - Get book-specific materials with navigation

## 📖 Direct PDF Reading System

### Quick PDF Access
Tutor-AI provides **one-click PDF reading** access from any page with intelligent navigation:

#### **Book Detail Page** (`/courses/{id}/books/{bookId}`)
- **Read PDF buttons**: Each PDF has direct "Read PDF" button for full workspace access
- **Study Workspace**: Alternative "Study Workspace" button for integrated study mode
- **Download options**: Direct download available for offline access

#### **Course Cards** (`/courses/{id}`)
- **Read PDF button**: Direct access to book's PDF reading interface
- **Smart routing**: Automatically opens to book detail page for PDF selection
- **Multi-PDF support**: Handles books with single or multiple PDFs

#### **Materials Workspace** (`/courses/{id}/materials/{filename}`)
- **PDF navigation**: "Altri PDF in questo libro" section for quick switching
- **Progress tracking**: Shows "1 di X" PDF position within book
- **Context preservation**: Maintains book context for AI chat integration
- **Responsive design**: Works seamlessly on desktop and mobile

### URL Structure
```typescript
// Direct PDF reading links
/courses/{courseId}/materials/{filename}?book={bookId}

// Examples
/courses/abc-123/materials/capitolo1.pdf?book=book-456
/courses/def-789/materials/manual.pdf?book=book-789
```

### User Workflow
1. **Navigate to course** → See book cards with "Read PDF" buttons
2. **Click "Read PDF"** → Opens full PDF reader workspace immediately
3. **In workspace** → Navigate between related PDFs using footer navigation
4. **Quick access** → Zero intermediate steps between course and PDF reading

### Enhanced API Support
- `GET /courses/{id}/materials` - All course materials with direct reading URLs
- `GET /courses/{id}/books/{bookId}/materials` - Book-specific materials with navigation
- **Response includes**: `read_url`, `download_url`, `book_id` for complete navigation

### AI Integration
- **Context-aware chat**: AI tutor knows which PDF/book is currently open
- **Seamless switching**: Chat context preserved when navigating between PDFs
- **Annotation support**: Personal notes shared with AI for enhanced tutoring

### AI Chat & RAG
- `POST /chat` - Chat with AI tutor
- `POST /course-chat` - Enhanced course-specific chat with session management
- `POST /search` - Advanced document search
- `POST /mindmap` - Generate mind maps
- `POST /quiz` - Generate quizzes

#### Book-Aware Retrieval Pipeline
- The study workspace (`/courses/[id]/study`) keeps the active `book` and `pdf` in the URL; the chat widget reads those params and always sends `book_id` with each `/chat` request.
- `RAGService.retrieve_context` now filters by `book_id` when the vector database is available and, if it is not, transparently falls back to on-the-fly chunking/embedding of the PDFs stored under `data/courses/<course>/books/<bookId>/`.
- Every retrieval response carries a `scope` payload (course name, book title, materials used, strategy) so that `LLMService` can inject the current book information into the system prompt regardless of the provider in use (OpenAI, ZAI, OpenRouter, Ollama/LmStudio, etc.).
- If no indexed chunks match the active book, the backend returns a clear message and keeps the session scoped, avoiding leaks from other books or courses.
- The enhanced PDF reader lets learners highlight or annotate pages; saved notes marked `share_with_ai` (toggle in the UI) are appended to the retrieval context so the tutor model can cite personal insights together with book excerpts.

#### PDF Annotation Workflow
1. **Reader UX** – Inside `/courses/[id]/study`, the `EnhancedPDFReader` exposes highlight/underline/note tools. Creating a selection opens a side panel where the learner writes a note and decides whether to “Condividi con il tutor AI”.
2. **Persistence** – Each note is saved to `data/annotations/<user>/<course>/<book>/<pdf>.json` with `share_with_ai`, page metadata, and tags. Updates/deletes happen through `/annotations` endpoints.
3. **Retrieval Merge** – During `RAGService.retrieve_context*` the system first pulls the normal book chunks, then prepends any shared annotations (scoped to the current course/book) as “NOTE PERSONALI DELLO STUDENTE” with synthetic sources.
4. **Prompting** – `LLMService.generate_response` reads the merged context and `scope` metadata so the downstream LLM knows which book is open and which personal notes it can safely reference.
5. **Chat Feedback Loop** – When “share with tutor” is active, the reader also emits a `pdf_annotation` event to the chat pane, giving immediate confirmation that the note can be used in the next question.

### Cognitive Learning APIs
- `POST /api/spaced-repetition/card` - Create learning card
- `GET /api/spaced-repetition/cards/due/{course_id}` - Get due cards for review
- `POST /api/active-recall/generate-questions` - Generate multi-format questions
- `POST /api/dual-coding/create` - Create integrated visual-verbal content

## ⚙️ Configuration

### DOCUMENTAZIONE_PERAGENT

Gli agent trovano una vista per argomenti in `DOCUMENTAZIONE_PERAGENT/`:

- `backend/` – overview servizi FastAPI, endpoint, guide RAG/annotazioni.
- `frontend/` – layout Next.js, lettore PDF, chat tutor.
- `ai/` – provider LLM supportati e orchestrazione RAG.
- `infrastructure/` – setup locale/Docker, variabili d'ambiente, struttura dati runtime.
- `product/` – roadmap UX, flussi di studio e gestione contenuti.

Ogni file contiene riferimenti (link relativi) ai documenti ufficiali (`docs/*.md`, `AGENTS.md`, ecc.) quindi basta aprire la cartella per capire dove reperire il dettaglio completo.

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
API_PORT=8000

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
NODE_ENV=development
PORT=3000
```

## 🔧 Port Configuration

**CRITICAL**: Maintain consistent port configuration to avoid connection issues:

### Standard Ports (NEVER CHANGE THESE)
- **Backend API**: Port `8000` (NOT 8001)
- **Frontend**: Port `3001` (NOT 3000 or 4000)
- **Redis**: Port `6379`
- **CORS Origins**: `http://localhost:3001,http://127.0.0.1:3001`

### Port Configuration Files
- **docker-compose.yml**: Backend service uses `8000:8000`, Frontend uses `3001:3000`
- **docker-compose.dev.yml**: Backend service uses `8000:8000`, Frontend uses `3001:3000`
- **docker-compose.simple.yml**: Backend service uses `8000:8000`, Frontend uses `3001:3000`
- **docker-compose.optimized.yml**: Backend service uses `8001:8001`, Frontend uses `3001:3000`
- **backend/Dockerfile**: EXPOSE and CMD use port `8001`
- **backend/main.py**: `uvicorn.run(app, host="0.0.0.0", port=8001)`
- **backend/.env.example**: `PORT=8001`
- **start.sh**: All port references updated to `8001` (backend) and `3001` (frontend)
- **frontend/.env.local**: `NEXT_PUBLIC_API_URL=http://localhost:8000`
- **frontend/next.config.js**: Backend URL points to port `8001`
- **.env.example**: `NEXT_PUBLIC_API_URL=http://localhost:8000`

### URL Endpoints
- **Backend Health**: `http://localhost:8001/health`
- **Frontend App**: `http://localhost:3001`
- **API Docs**: `http://localhost:8000/docs`

### ⚠️ Common Port Issues and Solutions

#### Problem: Frontend shows 404 errors or can't connect to backend
**Solution**: Check that:
1. Backend is running on port `8001` (NOT 8000)
2. Frontend environment points to `http://localhost:8001`
3. CORS origins include `http://localhost:3001,http://127.0.0.1:3001`

#### Problem: Port conflicts with other services
**Solution**:
```bash
# Check what's running on ports
ss -tulpn | grep :3001  # Should show only tutor-ai-frontend
ss -tulpn | grep :8001  # Should show only tutor-ai-backend

# Kill conflicting processes
sudo fuser -k 3001/tcp  # If something else is using port 3001
sudo fuser -k 8001/tcp  # If something else is using port 8001
```

#### Problem: Multiple services running on different ports
**Solution**: Stop all services and restart correctly:
```bash
./start.sh stop      # Stop all services
./start.sh dev       # Restart with correct ports
```

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

## 📦 Politica Librerie JavaScript Locali

### 🎋 Dichiarazione Politica
**Tutte le librerie JavaScript devono essere scaricate e mantenute localmente** per garantire affidabilità, sicurezza e capacità offline dell'applicazione.

### ✅ Benefici
- **Affidabilità**: Nessuna dipendenza da CDN esterni che possono essere offline o lenti
- **Sicurezza**: Controllo completo sulle versioni delle librerie e assenza di rischi di supply chain attacks
- **Performance**: Caricamento più rapido senza latenza di rete esterna
- **Offline Capability**: L'applicazione funziona completamente senza connessione internet
- **Version Consistency**: Assicura che tutti gli ambienti usino le stesse versioni delle librerie

### 🚀 Implementazione Esempio: PDF.js
**Caso di studio**: La migrazione da CDN a locale per PDF.js worker

#### ❌ Configurazione CDN (Problema):
```typescript
// CAUSA ERRORI: Dipende da CDN esterno
pdfjs.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjs.version}/pdf.worker.min.js`;
```

#### ✅ Configurazione Locale (Soluzione):
```typescript
// CONFIGURAZIONE CORRETTA: Usa worker locale
if (typeof window !== 'undefined') {
  pdfjs.GlobalWorkerOptions.workerSrc = '/pdf.worker.min.js';
}
```

**Risultati**:
- ✅ Errore "Failed to fetch dynamically imported module" eliminato
- ✅ PDF funziona offline
- ✅ Performance migliorata
- ✅ Nessuna dipendenza esterna

### 📋 Checklist per Nuove Librerie
Quando si aggiunge una nuova libreria JavaScript:

1. **Verifica disponibilità locale**: Controlla se la libreria è già in `node_modules/`
2. **Copia in public/**: Estrai i file necessari in `public/libraries/` o percorso appropriato
3. **Aggiorna configurazione**: Modifica i percorsi per usare file locali invece di CDN
4. **Test offline**: Verifica che la funzionalità funzioni senza connessione internet
5. **Documenta**: Aggiungi nota in questo documento per riferimento futuro

### 🔧 Processo di MIGRAZIONE CDN → LOCALE
1. **Identifica dipendenze CDN**: Cerca pattern come `//cdnjs.cloudflare.com/` o `//unpkg.com/`
2. **Verifica versione locale**: Controlla versione corrispondente in `node_modules/`
3. **Crea directory locale**: Organizza le librerie in `public/libraries/[nome]/`
4. **Aggiorna riferimenti**: Sostituisci URL CDN con percorsi locali
5. **Test funzionalità**: Verifica che tutto funzioni correttamente
6. **Rimuove riferimenti CDN**: Elimina vecchi URL esterni dal codice

### 📁 Struttura Directory Consigliata
```
frontend/public/
├── libraries/           # Librerie JavaScript esterne
│   ├── pdfjs/          # PDF.js files
│   ├── chartjs/        # Chart libraries
│   └── [other]/        # Altre librerie
└── pdf.worker.min.js   # Worker PDF.js (esistente)
```

## 🛠️ Development Guidelines

### Quick Start with Unified Script

**The easiest way to start Tutor-AI:**

```bash
./start.sh dev    # Start development environment
./start.sh status # Check status
./start.sh stop   # Stop all services
./start.sh logs   # View logs
```

**Available Commands:**
- `./start.sh dev` - Development with hot reload (default)
- `./start.sh simple` - Simplified configuration
- `./start.sh prod` - Production optimized
- `./start.sh stop` - Stop all services
- `./start.sh clean` - Complete cleanup
- `./start.sh logs` - Show real-time logs
- `./start.sh status` - Show service status

## 🔍 Enhanced Logging System

Tutor-AI includes a comprehensive logging infrastructure for debugging, monitoring, and analytics. The system provides structured logging, performance monitoring, and real-time analysis capabilities.

### 🚀 Key Features

#### **Backend Logging (Python/FastAPI)**
- **Structured Logging**: JSON-formatted logs with correlation IDs for request tracing
- **Multiple Log Levels**: DEBUG, INFO, WARN, ERROR, FATAL with environment-specific filtering
- **Performance Monitoring**: Automatic timing of API requests, database operations, and service calls
- **Security Event Tracking**: Automated detection and logging of security threats
- **Error Analytics**: Comprehensive error tracking with categorization and trend analysis
- **Log Rotation**: Automatic log file management with configurable retention policies

#### **Frontend Logging (Next.js/React)**
- **Centralized Logger**: Consistent logging interface across all components
- **Performance Metrics**: Component render timing and user interaction tracking
- **Error Boundary Integration**: Automatic error capturing and reporting
- **Remote Logging**: Optional remote log aggregation and analysis
- **Development vs Production**: Different logging strategies for different environments

#### **API Request/Response Logging**
- **Complete Request Tracking**: Full HTTP request logging with headers and metadata
- **Response Analytics**: Response time, size, and status code tracking
- **Client Information**: IP address, user agent, and device detection
- **Security Monitoring**: Automatic threat detection (SQL injection, XSS, path traversal)
- **Correlation IDs**: End-to-end request tracing across services

### 📁 Log File Structure

```
logs/
├── tutor-ai-backend.log           # Main application logs
├── tutor-ai-backend-errors.log    # Error-specific logs
├── tutor-ai-backend-security.log  # Security event logs
└── frontend/                      # Frontend logs (if configured)
    ├── app.log
    └── errors.log
```

### 🛠️ Log Analysis Tools

#### **Comprehensive Log Analyzer**
```bash
# Real-time log monitoring
python scripts/log_analyzer.py monitor --filters "ERROR" "security"

# Analyze logs from last 24 hours
python scripts/log_analyzer.py analyze --hours 24 --format json

# Error statistics and trends
python scripts/log_analyzer.py errors --hours 48

# Search for specific patterns
python scripts/log_analyzer.py search --pattern "database.*timeout" --context 5

# Export logs for analysis
python scripts/log_analyzer.py export --output logs_export.json --format json

# Clean up old log files
python scripts/log_analyzer.py cleanup --days 30 --dry-run
```

#### **Docker Log Integration**
```bash
# View container logs with correlation IDs
docker-compose logs -f backend | grep "correlation_id"

# Monitor specific log levels
docker-compose logs backend | grep "ERROR\|FATAL"

# Follow logs with timestamp formatting
docker-compose logs -f --timestamps backend
```

### 🔧 Configuration

#### **Environment Variables**
```env
# Backend Logging Configuration
LOG_LEVEL=INFO                    # DEBUG, INFO, WARN, ERROR, FATAL
LOG_DIR=./logs                   # Log directory path
ENVIRONMENT=development          # development, staging, production
ENABLE_PERFORMANCE_LOGGING=true
ENABLE_SECURITY_LOGGING=true

# Frontend Logging Configuration
NEXT_PUBLIC_LOG_LEVEL=info
NEXT_PUBLIC_ENABLE_ANALYTICS=false
NEXT_PUBLIC_LOG_ENDPOINT=
```

#### **Service Integration**
```python
# Backend - Enhanced logging in services
from backend.logging_config import get_logger, LoggedTimer

logger = get_logger(__name__)

with LoggedTimer("database_query", logger=logger):
    result = await database.query(...)

logger.info("Operation completed", extra={
    "operation": "user_login",
    "user_id": user.id,
    "success": True
})
```

```typescript
// Frontend - Centralized logging
import { logger, createTimer } from '@/lib/logger'

// Basic logging
logger.info("User action", { action: "button_click", component: "ChatInterface" })

// Performance timing
const timer = createTimer("api_request")
try {
  const response = await api.call(...)
  timer.end({ endpoint: "/chat", status: response.status })
} catch (error) {
  timer.end({ success: false, error: error.message })
}
```

### 📊 Log Analysis Examples

#### **Debugging API Issues**
```bash
# Find slow API requests
python scripts/log_analyzer.py search --pattern "duration_ms.*[0-9]{4,}"

# Track specific correlation ID
python scripts/log_analyzer.py search --pattern "correlation_id.*abc123"

# Monitor error rates
python scripts/log_analyzer.py errors --hours 1
```

#### **Security Monitoring**
```bash
# Check for security events
python scripts/log_analyzer.py search --pattern "security_event"

# Monitor suspicious IPs
python scripts/log_analyzer.py security --hours 24

# Find authentication failures
python scripts/log_analyzer.py search --pattern "authentication.*failed"
```

#### **Performance Analysis**
```bash
# Analyze API performance
python scripts/log_analyzer.py performance --hours 6

# Find database performance issues
python scripts/log_analyzer.py search --pattern "database_query.*duration_ms"

# Monitor memory usage patterns
python scripts/log_analyzer.py search --pattern "memory_used"
```

### 🚨 Alerting and Monitoring

#### **Error Rate Monitoring**
```bash
# Check error rates in real-time
watch -n 60 'python scripts/log_analyzer.py errors --hours 1 | grep "Error rate"'
```

#### **Performance Alerts**
```bash
# Monitor for slow requests
python scripts/log_analyzer.py search --pattern "slow_request" | tail -f
```

#### **Security Alerts**
```bash
# Monitor security events
python scripts/log_analyzer.py monitor --filters "security_event" "suspicious_activity"
```

### 🔍 Log Formats

#### **Structured JSON Format**
```json
{
  "timestamp": "2024-01-15T10:30:45.123Z",
  "level": "INFO",
  "logger": "LLMService",
  "message": "API request completed successfully",
  "correlation_id": "abc12345",
  "operation": "llm_generate",
  "duration_ms": 1250,
  "tokens_used": 150,
  "model": "gpt-4",
  "metadata": {
    "endpoint": "/chat",
    "user_id": "user_456",
    "request_id": "req_789"
  }
}
```

#### **Security Event Format**
```json
{
  "timestamp": "2024-01-15T10:30:45.123Z",
  "level": "WARNING",
  "logger": "security",
  "event_type": "sql_injection_attempt",
  "description": "SQL injection pattern detected",
  "client_ip": "192.168.1.100",
  "user_agent": "Mozilla/5.0...",
  "severity": "WARNING",
  "metadata": {
    "pattern": "union select",
    "endpoint": "/api/search",
    "request_params": "query=UNION SELECT * FROM users"
  }
}
```

### 📈 Analytics and Insights

The logging system provides comprehensive analytics:

- **Request Volume**: Track API usage patterns and peak hours
- **Error Trends**: Identify recurring issues and error rates
- **Performance Metrics**: Monitor response times and system bottlenecks
- **User Behavior**: Analyze user actions and interaction patterns
- **Security Events**: Track potential threats and suspicious activities
- **System Health**: Monitor overall system performance and stability

### 🛠️ Best Practices

1. **Use Structured Logging**: Always include relevant context and metadata
2. **Correlation IDs**: Use correlation IDs for end-to-end request tracing
3. **Appropriate Log Levels**: Choose appropriate log levels (DEBUG for development, INFO for production)
4. **Security**: Never log sensitive information (passwords, tokens, PII)
5. **Performance**: Monitor performance impact of logging in production
6. **Log Rotation**: Configure appropriate log retention policies
7. **Monitoring**: Set up automated monitoring and alerting for critical events

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

### ⚠️ CRITICAL: Frontend 404 Errors on Dynamic Routes
**Problem**: URLs like `/courses/[id]/books/[bookId]` return 404
**Root Cause**: Using production Docker configuration instead of development
**SOLUTION**:

#### ✅ PERMANENT FIX:
```bash
# Stop all services
./start.sh stop

# Start with DEVELOPMENT configuration (REQUIRED)
./start.sh dev
```

#### ✅ VERIFICATION:
- ✅ Homepage: `http://localhost:3000` (200 OK)
- ✅ Courses: `http://localhost:3000/courses` (200 OK)
- ✅ Course detail: `http://localhost:3000/courses/[id]` (200 OK)
- ✅ Books listing: `http://localhost:3000/courses/[id]/books` (200 OK)
- ✅ Backend: `http://localhost:8001/health` (200 OK)

#### ✅ WORKING BOOK ACCESS (Temporary Fix):
```bash
# Access book functionality via these working URLs:
http://localhost:3000/chat?course=COURSE_ID&book=BOOK_ID
http://localhost:3000/courses/COURSE_ID/study?book=BOOK_ID&pdf=filename.pdf
```

#### ❌ NEVER USE:
```bash
# These commands use PRODUCTION config and break dynamic routing:
docker-compose up
docker-compose.yml without docker-compose.dev.yml
```

#### 🔧 TECHNICAL EXPLANATION:
- **Production**: Builds frontend code into Docker image, no hot reload, breaks dynamic routes
- **Development**: Mounts source code volumes, enables hot reload, fixes dynamic routes
- **File Structure**: Dynamic routes `/courses/[id]/books/[bookId]/page.tsx` work correctly in dev mode

This is the **permanent solution** - always use `./start.sh dev` for development.

#### 🔁 Mindmap 404 Regression Tests
- Test suite: `frontend/src/components/books/__tests__/MindmapLinks.test.tsx`
- Scope: verifies the “Mappa Concettuale” quick action links to `/courses/{courseId}/books/{bookId}/mindmap` and that both `courses/.../mindmap` and `book-detail/.../mindmap` routes render the shared `MindmapClient` (prevents silent 404s on future refactors).
- Run locally with `cd frontend && npm run test -- MindmapLinks --runInBand` to keep Jest in a single worker (avoids sporadic Next/Jest worker crashes on Windows).
- CI note: include this spec whenever debugging navigation regressions related to concept maps; it fails fast if a link or route mapping is removed.

**Problem**: Frontend shows 404 errors or can't connect to backend
**Solution**:
1. Ensure backend is healthy: `curl http://localhost:8001/health`
2. Check CORS origins include: `http://localhost:3000,http://127.0.0.1:3000`
3. Verify frontend `.env` has: `NEXT_PUBLIC_API_URL=http://localhost:8000`

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

## 🧪 Testing & Validation

Tutor-AI includes comprehensive testing infrastructure to validate connectivity, API endpoints, and dynamic routes.

### 🚀 Quick Test Commands

```bash
# Run all tests (recommended after changes)
./tests/run_all_tests.sh

# Run quick connectivity tests
./tests/run_all_tests.sh --quick

# Run specific test suites
./tests/run_all_tests.sh --connectivity  # Connectivity & health checks
./tests/run_all_tests.sh --api          # API endpoints & CORS
./tests/run_all_tests.sh --routes       # Dynamic routes validation
```

### 📁 Test Structure

```
tests/
├── README.md                           # Complete test documentation
├── run_all_tests.sh                    # Master test runner
└── connectivity/                       # Test suite directory
    ├── connectivity_test.sh           # Basic connectivity & health checks
    ├── api_test.py                    # API endpoints & CORS testing
    └── dynamic_routes_test.py         # Dynamic routes validation
```

### 🔍 Test Coverage

- **Container Health**: Docker container status and health checks
- **API Endpoints**: All REST API endpoints and CORS configuration
- **Dynamic Routes**: Frontend routes including course, book, and material pages
- **Connectivity**: Frontend-backend communication and database connections
- **File Operations**: Upload endpoints and material access

### 📊 Test Results

Tests provide detailed reports including:
- Pass/fail status for each test
- HTTP response codes and error messages
- Performance metrics (response times)
- Success rate percentage

### 🛠️ Troubleshooting Tests

If tests fail:
1. Check service status: `docker-compose ps`
2. Verify ports: `ss -tulpn | grep -E ':(3001|8001)'`
3. Restart services: `./start.sh dev`
4. Check logs: `docker-compose logs [service]`

### 📋 Pre-Deployment Checklist

Before deploying or after major changes:
1. ✅ Run all tests: `./tests/run_all_tests.sh`
2. ✅ Verify container health: `docker-compose ps`
3. ✅ Test critical user workflows manually
4. ✅ Check dynamic routes functionality
5. ✅ Validate file upload and chat features

**For complete testing documentation**, see [tests/README.md](./tests/README.md)

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
- **PDF Functionality**: Fully working with port consistency fixes ✅
- **File System Access**: Resolved illegal path errors ✅
- **Material Loading**: Fixed book detail page routing ✅

## 🔧 Recent Fixes (November 2025)

### Port Configuration Standardization
- **Backend**: Fixed all references from port 8001 → 8000
- **Frontend**: Updated 25+ component files with hardcoded ports
- **API Configuration**: Consistent port 8000 across all services
- **Proxy Routes**: Added `/course-files` proxy in Next.js config

### PDF Loading Issues Resolved
- **File System Access**: Fixed "Unable to add filesystem: <illegal path>" errors
- **Material Loading**: Fixed "Libro non trovato" errors in workspace
- **Book Detail Pages**: Fixed routing by updating course data fetching
- **Backend Data**: Fixed course_service.py to generate correct URLs

### Testing Infrastructure
- **PDF Test Suite**: Created comprehensive PDF functionality tests (`tests/pdf_functionality_test.py`)
- **Browser Tests**: JavaScript-based testing for PDF loading (`tests/browser_pdf_test.js`)
- **API Validation**: Port consistency and endpoint verification

---

<div align="center">

**🚀 Version: 2.0.0** • **📅 Updated: 2025-11-08** • **⭐ MIT License**

*For complete documentation, see [CLAUDE_DETAILED.md](./CLAUDE_DETAILED.md)*

</div>
