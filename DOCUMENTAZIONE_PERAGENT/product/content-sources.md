# Fonti Contenuto e Materiali

- **Uploads**: `data/courses/<course_id>/books/<book_id>/*.pdf` caricati via UI "Carica PDF".
- **Indicizzazione**: `backend/services/rag_service.py` (`index_pdf`) o script `index_pdfs.py`.
- **Chroma / cache**: se abilitato, contenuti finiscono in `data/vector_db`.
- **Annotazioni**: `data/annotations/<user>/<course>/<book>/<pdf>.json`.
- **Note chat**: `data/notes/` (se implementato) e `data/chat_sessions/` per cronologia.

Per aggiornare/ricostruire i materiali seguire `docs/LOCAL_SETUP_GUIDE.md` e assicurarsi che i PDF siano raggiungibili via `http://localhost:8001/course-files/...`.
