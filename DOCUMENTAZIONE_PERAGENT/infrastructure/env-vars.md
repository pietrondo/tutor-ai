# Variabili d'Ambiente Principali

| Ambito | Variabili | Note |
| --- | --- | --- |
| Backend server | `API_HOST`, `API_PORT=8001`, `CORS_ORIGINS`, `UPLOAD_DIR`, `VECTOR_DB_PATH` | Definiti in `.env` backend e `CLAUDE.md` |
| DB/Cache | `DATABASE_URL` (sqlite), `REDIS_URL` (per cache RAG) | Redis necessario per `retrieve_context_cached` |
| LLM | vedi `DOCUMENTAZIONE_PERAGENT/ai/models.md` | Provider switching |
| Frontend | `NEXT_PUBLIC_API_URL=http://localhost:8001`, `NODE_ENV`, `PORT=3000` | Next.js client-side usa solo variabili `NEXT_PUBLIC_` |
| Feature flags | `BUDGET_MODE`, `LLM_TYPE`, `LOCAL_LLM_MODEL` | Attivano comportamenti condizionali |

Per ambienti personali copiare `backend/.env.example` → `.env` e `frontend/.env.local`. Non committare file `.env`.
