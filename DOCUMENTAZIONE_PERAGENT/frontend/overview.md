# Frontend Overview

Documenti di riferimento:

- `AGENTS.md` → sezioni "Project Structure" e "Coding Style" per Next.js/Tailwind.
- `frontend/README.md` (se presente) + `LOCAL_SETUP_GUIDE.md` per comandi `npm run dev/build/lint`.
- `frontend/src/app/courses/[id]/study/page.tsx` → layout Lettore+Chat.
- `frontend/src/components/EnhancedPDFReader.tsx` → annotazioni, note condivise.
- `frontend/src/components/IntegratedChatTutor.tsx` → invio chat, note, profilo utente.
- `frontend/src/components/books/BookDetailClient.tsx` → navigazione materiali.

Elementi principali:
1. **Routing** – Next.js App Router in `frontend/src/app`. Le pagine corso includono sottopagine `chat`, `study`, `books`, ecc.
2. **State/UI** – Hooks personalizzati (`src/hooks`) e componenti condivisi (`src/components/ui`).
3. **API base URL** – `process.env.NEXT_PUBLIC_API_URL` (default `http://localhost:8001`).
4. **PDF Reader** – usa `react-pdf` + `CustomHighlight`; salva note via `/annotations` e al bisogno invia eventi al Tutor.
