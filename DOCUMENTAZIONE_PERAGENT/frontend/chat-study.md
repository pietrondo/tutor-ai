# Chat & Study UI Flow

- **Studio integrato** (`/courses/[id]/study`)
  - Carica corso + libri via `/courses/{id}`.
  - Mantiene query param `book`/`pdf` per sincronizzare lettore e chat.
  - `EnhancedPDFReader` → usa `react-pdf`; worker configurato via CDN fallback. È possibile evidenziare/sottolineare/note con toggle “Condividi con il tutor AI”; il salvataggio passa da `/annotations` con `share_with_ai=true`.
  - `IntegratedChatTutor` → inizializza sessione (`/api/chat/initialize`), invia messaggi a `/chat` includendo `book_id`, `user_id` e preferenze (note/annotazioni incluse).

- **Annotazioni**
  - Salvataggio: `POST /annotations` con `share_with_ai` quando l'utente abilita la spunta.
  - Recupero per UI: `GET /annotations/{user}/{pdf}?course_id&book_id` e `GET /api/books/{book}/annotations/recent` (riassunto in sidebar chat).
  - Upload PDF nella pagina libro usa ora un input nascosto referenziato via `useRef`, così il bottone “Carica PDF” resta cliccabile anche con il componente `Button`.

- **Chat Tutor**
  - Mostra `sources` e `confidence` (vedi `IntegratedChatTutor.tsx` line ~320+).
  - Può creare note rapide (`/api/notes/from-chat`).
  - Riconferma contesto libro se `bookId` cambia (prop drilling dal parent).
