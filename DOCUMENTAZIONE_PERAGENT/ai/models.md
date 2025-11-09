# Modelli e Provider

| Provider | Env vars principali | File di riferimento |
| --- | --- | --- |
| OpenAI | `LLM_TYPE=openai`, `OPENAI_API_KEY`, `OPENAI_MODEL` | `backend/services/llm_service.py`, `docs/LOCAL_SETUP_GUIDE.md` |
| ZAI Model API | `LLM_TYPE=zai`, `ZAI_API_KEY`, `ZAI_MODEL`, `ZAI_BASE_URL` | `services/llm_service.py`, `ZAI_INTEGRATION.md` |
| OpenRouter | `LLM_TYPE=openrouter`, `OPENROUTER_API_KEY`, `OPENROUTER_MODEL` | `services/llm_service.py` |
| Ollama | `LLM_TYPE=ollama`, `LOCAL_LLM_URL`, `LOCAL_LLM_MODEL` | `services/llm_service.py`, `LOCAL_SETUP_GUIDE.md` |
| LM Studio | `LLM_TYPE=lmstudio`, `LOCAL_LLM_URL`, `LOCAL_LLM_MODEL` | idem |
| Legacy local | `LLM_TYPE=local`, `LOCAL_LLM_URL`, `LOCAL_LLM_MODEL` | solo fallback |

Suggerimenti:
- Impostare `BUDGET_MODE=true` per forzare la scelta di modelli più economici.
- Monitorare `logs/` per errori di time-out; `services/llm_service.py` logga provider e modello effettivo.
- Aggiornare `CLAUDE.md` e `AGENTS.md` se si aggiungono provider/custom prompt.
