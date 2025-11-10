# Setup & Infrastructure

## Local Development
- Script: `./setup.sh` (crea venv Python + `npm install`).
- Backend: `cd backend && source venv/bin/activate && uvicorn main:app --reload --port 8001`.
- Frontend: `cd frontend && npm run dev -- --port 3000`.
- Env file: duplicare `backend/.env.example` e `frontend/.env.local` (vedi `AGENTS.md`, `LOCAL_SETUP_GUIDE.md`).

### start.sh (workflow rapido)
`./start.sh` gestisce l'intero stack Docker. Opzioni utili introdotte:

| Opzione | Effetto |
| --- | --- |
| `dev` (default) | Avvio ambiente con hot reload |
| `build` | Solo compilazione immagini Docker (equivalente a `docker compose build`) |
| `--build` / `-b` | Durante `dev/simple/prod` forza `up -d --build --force-recreate`; nel comando `build` aggiunge `--no-cache` |
| `--no-health` | Salta l'health check per avvii più veloci |
| `--no-logo` | Nasconde il banner |
| `stop`, `clean`, `logs`, `status` | Restano disponibili come prima |

Esempi: `./start.sh dev --build`, `./start.sh prod --no-health`, `./start.sh build -b` (build immagini senza cache).

## Docker / Compose
- File principali: `docker-compose.yml`, `docker-compose.dev.yml`, `docker-compose.simple.yml`.
- Porta obbligatoria backend `8001`, frontend `3000` (riassunto in `CLAUDE.md` → sezione Port Configuration).
- Volume dati: `./data` (corsi, annotazioni, vector db). Evitare di committare file generati.

## Struttura dati runtime
```
data/
 ├── courses/<course_id>/books/<book_id>/*.pdf
 ├── annotations/<user>/<course>/<book>/<pdf>.json
 ├── chat_sessions/
 ├── vector_db/
```

## Strumenti utili
- `scripts/` contiene utility per indicizzare PDF, generare mindmap, ecc.
- `docs/DOCKER_README.md`, `DOCS/LOCAL_SETUP_GUIDE.md` per istruzioni dettagliate.
