# Chat & Study UI Flow

- **Studio integrato** (`/courses/[id]/study`)
  - Carica corso + libri via `/courses/{id}`.
  - Mantiene query param `book`/`pdf` per sincronizzare lettore e chat.
  - `EnhancedPDFReader` → `onAnnotationCreate` per aggiornare liste recenti e mostrare snack bar.
  - `IntegratedChatTutor` → inizializza sessione (`/api/chat/initialize`), invia messaggi a `/chat` includendo `book_id`, `user_id` e preferenze (note/annotazioni incluse).

- **Annotazioni**
  - Salvataggio: `POST /annotations` con `share_with_ai` quando l'utente abilita la spunta.
  - Recupero per UI: `GET /annotations/{user}/{pdf}?course_id&book_id` e `GET /api/books/{book}/annotations/recent` (riassunto in sidebar chat).

- **Chat Tutor**
  - Mostra `sources` e `confidence` (vedi `IntegratedChatTutor.tsx` line ~320+).
  - Può creare note rapide (`/api/notes/from-chat`).
  - Riconferma contesto libro se `bookId` cambia (prop drilling dal parent).
