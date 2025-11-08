# Tutor-AI Project Instructions

## Architecture Overview

**Tutor-AI** is a bilingual (Italian/English) RAG-based learning platform with:
- **Backend**: FastAPI (Python 3.11+) with modular services under `backend/services/`
- **Frontend**: Next.js 16 (TypeScript) with App Router, running on port 5000
- **Vector DB**: ChromaDB (persistent in `data/vector_db/`)
- **Cache**: Redis for query/embedding caching
- **LLM Providers**: Z.AI (primary via `glm-4.5`/`glm-4.6`), OpenAI, Ollama
- **Storage**: JSON files in `data/` for study tracking, concept maps, slide generations

### Service-Oriented Backend

All core logic lives in `backend/services/` with dependency injection patterns:
- `rag_service.py` - ChromaDB embeddings with `intfloat/multilingual-e5-large`, lazy-loads CUDA models
- `llm_service.py` - Multi-provider LLM abstraction (Z.AI models in `ZAI_MODELS` dict, OpenAI, Ollama)
- `course_service.py` - CRUD for courses stored in `data/courses/`
- `study_tracker.py` - JSON-based session tracking with analytics
- `concept_map_service.py` - D3.js mindmap generation with node expansion
- `pdf_generator.py` - HTML→PDF conversion for slides via Z.AI agents
- `cache_service.py` - Redis wrapper with TTL, hashing, and circuit breaker patterns
- `hybrid_search_service.py` - Combines semantic + BM25 search with re-ranking

API routers are mounted in `backend/main.py` via `app.include_router()` from `app/api/` subdirectories.

### Frontend Architecture

Next.js App Router structure:
- Routes: `src/app/` (e.g., `courses/[id]/`, `chat/[courseId]/`)
- Components: `src/components/` (e.g., `CourseCard.tsx`, `StatsOverview.tsx`)
- API calls: Direct fetch to `http://localhost:8000` (configure with `NEXT_PUBLIC_API_URL`)
- Styling: Tailwind CSS with custom gradients (blue→purple theme)
- State: React hooks (no global store; props drilling or context)

## Development Workflows

### Quick Start Commands

```powershell
# Backend setup (Windows PowerShell)
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env  # Edit with your API keys
python main.py  # Runs on http://localhost:8000

# Frontend setup
cd frontend
npm install
npm run dev  # Runs on http://localhost:5000
```

### Docker Development (Recommended)

```powershell
# Zero-rebuild dev mode with hot reload
.\start-dev.sh
# OR manually:
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# Production build:
docker-compose -f docker-compose.yml up
```

**Key Docker patterns:**
- `docker-compose.dev.yml` bind-mounts source code for hot reload (no rebuild on code changes)
- Volumes: `apt_cache`, `rag_data`, `redis_data` persist between runs
- GPU support configured via `nvidia-docker` for embedding models

### Testing

```powershell
# Frontend tests (Jest + Testing Library)
cd frontend
npm run test          # Run tests
npm run test:coverage # Coverage report

# Backend tests (pytest - manual)
cd backend
pytest backend/test_*.py
```

**No backend test suite exists yet.** When creating tests, use:
- `backend/tests/` directory
- Mock Chroma/Redis/OpenAI with `unittest.mock` or `pytest-mock`

## Project-Specific Conventions

### Backend Patterns

1. **Service initialization:** Services use lazy loading for heavy resources (embeddings models, LLM clients). Check `_load_embedding_model()` pattern in `rag_service.py`.

2. **LLM model selection:** The `ZAI_MODELS` dict in `llm_service.py` maps model names to capabilities (`supports_agents`, `supports_thinking`, `cost_per_1k_tokens`). Always validate model names against this dict.

3. **File path sanitization:** Use `utils/security.py` functions:
   ```python
   from utils.security import sanitize_filename, validate_file_path
   safe_name = sanitize_filename(user_input)
   validate_file_path(path, allowed_dir="data/uploads")
   ```

4. **Error handling:** Import from `utils/exceptions.py`:
   ```python
   from utils.exceptions import ValidationError, safe_execute
   async with safe_execute("operation_name"):
       # code that might fail
   ```

5. **Logging:** Use `structlog` with contextual info:
   ```python
   import structlog
   logger = structlog.get_logger()
   logger.info("Processing document", course_id=course_id, pages=page_count)
   ```

6. **Redis caching:** Services that need caching call `_init_cache_service()` and use:
   ```python
   cache_key = f"query:{course_id}:{hash(query)}"
   result = await self.cache_service.get(cache_key)
   if not result:
       result = expensive_operation()
       await self.cache_service.set(cache_key, result, ttl=3600)
   ```

### Frontend Patterns

1. **Component structure:** Functional components with TypeScript interfaces:
   ```tsx
   interface CourseCardProps {
     id: string
     name: string
     // ... fields match backend Course model
   }
   export const CourseCard: React.FC<CourseCardProps> = ({ id, name }) => { ... }
   ```

2. **API calls:** Direct fetch with error handling in `useEffect`:
   ```tsx
   const [data, setData] = useState<Course[]>([])
   const [loading, setLoading] = useState(true)
   
   useEffect(() => {
     fetch('http://localhost:8000/courses')
       .then(res => res.json())
       .then(data => setData(data.courses || []))
       .catch(console.error)
       .finally(() => setLoading(false))
   }, [])
   ```

3. **Styling:** Use Tailwind with consistent color scheme:
   - Primary: `bg-gradient-to-r from-blue-600 to-purple-600`
   - Cards: `bg-white rounded-xl shadow-lg`
   - Loading states: `animate-spin border-blue-600`

4. **File naming:** PascalCase for components (`CourseCard.tsx`), kebab-case for pages (`[courseId]/page.tsx`)

### Italian Language Considerations

The system is optimized for Italian academic content:
- Embedding model: `intfloat/multilingual-e5-large` (best for Italian 2025)
- Chunk size: 800 tokens (optimal for Italian syntax)
- Title cleaning in `main.py` removes common Italian document artifacts (`"estratto da"`, `"tratto da"`, university names)
- When generating prompts for Z.AI, include `"Rispondi in italiano"` for Italian responses

### Z.AI Integration Specifics

**Model selection logic** (from `llm_service.py`):
- `glm-4.6` - Complex reasoning, slide generation, agentic tasks (most expensive)
- `glm-4.5` - **Default for slides**, balanced cost/performance
- `glm-4.5-air` - Quick drafts, chat, quiz (cheapest)
- `glm-4.5v` - Vision capabilities for document analysis

**API patterns:**
```python
# Z.AI agent invocation (see backend/app/api/slides.py)
response = requests.post(
    f"{ZAI_BASE_URL}/agents",
    headers={"Authorization": f"Bearer {ZAI_API_KEY}"},
    json={
        "agent_id": "slides_glm_agent",
        "messages": [{"role": "user", "content": prompt}],
        "stream": False
    }
)
```

**Key env vars:**
```bash
LLM_TYPE=zai
ZAI_API_KEY=your_key
ZAI_MODEL=glm-4.5
ZAI_BASE_URL=https://api.z.ai/api/paas/v4/
```

## Common Pitfalls

1. **Port conflicts:** Frontend runs on 5000 (not 3000) to avoid Airplay conflicts on macOS. Backend on 8000.

2. **Path separators:** Codebase has mixed Linux/Windows path handling. Use `pathlib.Path()` for cross-platform safety.

3. **GPU memory:** The embedding model (`multilingual-e5-large`) needs ~2GB VRAM. It auto-detects CUDA but falls back to CPU if unavailable.

4. **ChromaDB compatibility:** Collections use `where={"course_id": id}` syntax (newer API). Avoid deprecated `where_document=`.

5. **Redis availability:** Backend will fail to start if Redis isn't running. Docker setup handles this with `depends_on` healthchecks.

6. **Z.AI rate limits:** No explicit retry logic exists yet. If you get 429s, implement exponential backoff in `llm_service.py`.

## Key Files to Reference

- `AGENTS.md` - Repository guidelines (commit style, PR process)
- `backend/services/llm_service.py` - LLM provider abstraction layer
- `backend/main.py` - API endpoint definitions and router mounting
- `docs/ZAI_SLIDE_AGENT_DOCUMENTATION.md` - Complete Z.AI integration guide
- `frontend/src/components/` - UI component library
- `docker-compose.dev.yml` - Development override for hot reload

## Extending the System

### Adding a new API endpoint:

1. Create router in `backend/app/api/new_feature.py`:
   ```python
   from fastapi import APIRouter
   router = APIRouter(prefix="/new-feature", tags=["feature"])
   
   @router.get("/")
   async def list_items():
       return {"items": []}
   ```

2. Mount in `backend/main.py`:
   ```python
   from app.api.new_feature import router as new_feature_router
   app.include_router(new_feature_router)
   ```

### Adding a new service:

1. Create `backend/services/my_service.py`:
   ```python
   class MyService:
       def __init__(self):
           self.cache_service = None  # Lazy load
       
       def _init_cache_service(self):
           from services.cache_service import get_cache_service
           if not self.cache_service:
               self.cache_service = get_cache_service()
   ```

2. Import in `main.py` and instantiate at module level (cached singleton pattern)

### Adding frontend features:

1. Create component in `frontend/src/components/Feature.tsx`
2. Add route in `frontend/src/app/feature/page.tsx`
3. Use existing components from `ui/Button.tsx`, `ui/Card.tsx` for consistency

## Environment Configuration

Required `.env` variables (see `backend/.env.example`):
```bash
# LLM Provider (choose one)
LLM_TYPE=zai|openai|local

# Z.AI (recommended)
ZAI_API_KEY=
ZAI_MODEL=glm-4.5
ZAI_BASE_URL=https://api.z.ai/api/paas/v4/

# OpenAI (alternative)
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o

# Ollama (local alternative)
LOCAL_LLM_URL=http://localhost:11434/v1
LOCAL_LLM_MODEL=llama3.1

# Infrastructure
REDIS_URL=redis://localhost:6379
```

Frontend `.env.local`:
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```
