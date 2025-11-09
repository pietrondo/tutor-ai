# RAG + LLM Stack

## Retrieval
- **Vector DB**: `chromadb` (disabilitabile); fallback a chunking locale in `RAGService`.
- **Chunk cache**: `book_chunk_cache` limita a 1.2k chunk per volume.
- **Annotations merge**: `_merge_user_annotations()` antepone "NOTE PERSONALI" se `share_with_ai` attivo.
- **Cache layer**: `retrieve_context_cached` usa Redis (`services/cache_service.py`) e aggiunge annotation merge fuori dalla cache.
- **Offline fallback**: se il download del modello SentenceTransformer fallisce (es. niente accesso a HuggingFace) il servizio passa automaticamente a una similarità lessicale (tokenizzazione semplice + coseno) così il tutor continua a citare il libro selezionato e le note condivise.

## Generation
- `LLMService` supporta provider `openai`, `zai`, `openrouter`, `ollama`, `lmstudio`, `local`.
- `ModelSelector` sceglie modello in base a `context_size` e `budget_mode`.
- Prompt system include:
  - lingua italiana obbligatoria
  - contesto corso/libro da `scope`
  - linee guida pedagogiche

## Interazione con frontend
- `IntegratedChatTutor` → `POST /chat` (legacy) o `/course-chat` (avanzato). Passare sempre `user_id` e `book_id` per sfruttare RAG scoped + note personali.
- Per debug: `http://localhost:8001/docs` ↑ endpoints; `logs/` contiene eventuali errori RAG/LLM.
