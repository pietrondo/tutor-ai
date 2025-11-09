# Backend Overview

Documenti chiave:

- `AGENTS.md` → sezioni "Repository Guidelines" e "Backend" per convenzioni generali.
- `backend/README.md` (se presente) e `README.md` root per comandi di sviluppo rapidi.
- `backend/main.py` → definisce FastAPI app, endpoint `/chat`, `/course-chat`, annotazioni, ecc.
- `backend/services/`:
  - `rag_service.py` → pipeline RAG ibrida + integrazione annotazioni (`share_with_ai`).
  - `llm_service.py` → orchestrazione provider (OpenAI/ZAI/OpenRouter/local) e prompt contestualizzati.
  - `course_service.py`, `book_service.py` → gestione corsi/libri/materiali.
  - `annotation_service.py` → salvataggio e ricerca note PDF.
- `docs/LOCAL_SETUP_GUIDE.md` e `docs/DOCKER_README.md` per esecuzione API.

Flusso principale:
1. Frontend invia `/chat` con `course_id`, `book_id`, `user_id`.
2. `RAGService.retrieve_context_cached` filtra i chunk del libro e aggiunge le annotazioni `share_with_ai`.
3. `LLMService.generate_response` inserisce il contesto/`scope` nel system prompt.
4. `annotation_service` fornisce note recenti anche a `/api/books/{book_id}/annotations/recent`.
