# Backend Endpoints

| Area | Endpoint | Descrizione | Documento originale |
| --- | --- | --- | --- |
| Chat | `POST /chat` | Chat legacy con cache RAG | `backend/main.py:1981+` |
| Chat avanzata | `POST /course-chat` | Sessioni personalizzate, preferenze difficoltà | `backend/main.py:2037+` |
| Annotazioni | `/annotations` CRUD | Evidenziazioni, note, export/import | `backend/main.py:3787+`, `services/annotation_service.py` |
| Note/Profilo | `/api/notes/...` `/api/learning/profile` | Supporto a IntegratedChatTutor | `backend/main.py` sez. API Models |
| Studio | `/courses`, `/courses/{id}` | Caricamento corsi/libri/materiali | `services/course_service.py`, `docs/README.md` |
| AI utilities | `/api/dual-coding`, `/api/active-recall`, ecc. | Funzioni cognitive | `backend/main.py` (sezioni modellate) |

Per l'elenco completo consultare `docs/API_REFERENCE.md` (se presente) oppure generare `uvicorn main:app --reload` e aprire `http://localhost:8001/docs`.
