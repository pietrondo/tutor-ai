# Repository Guidelines

## Project Structure & Module Organization
- `backend/` contains the FastAPI app (`main.py`) and service layer under `services/` for RAG, LLM, course, and study tracking logic. Keep new service modules colocated here.
- `frontend/` houses the Next.js UI; route handlers live in `src/app`, shared widgets in `src/components`, stateful helpers in `src/hooks`, and domain utilities in `src/lib`. Assets belong in `public/`.
- `data/` stores course uploads, the Chroma vector database, and study tracking JSON; treat it as runtime storage and keep large files out of git.
- `docs/` centralizes product briefs; place additional design specs or ADRs alongside existing documents.

## Build, Test, and Development Commands
- `./setup.sh` prepares directories, the Python venv, and npm packages on a fresh checkout.
- `cd backend && source venv/bin/activate && python main.py` spins up the API on `http://localhost:8000`; use `uvicorn main:app --reload` during iterative work.
- `cd frontend && npm run dev` launches the Next.js dev server at `http://localhost:3000`.
- `cd frontend && npm run build` creates the production bundle; follow with `npm run start` for a local preview.
- `cd frontend && npm run lint` runs ESLint/Next lint checks, and `npm run test` or `npm run test:coverage` executes the Jest suite.

## Coding Style & Naming Conventions
- Python code follows PEP 8 with 4-space indentation, type hints, and service classes that encapsulate external integrations; prefer dependency injection over module-level globals when extending.
- TypeScript code should remain in strict mode, use 2-space indentation, functional components, and PascalCase filenames (e.g., `CourseCard.tsx`); hooks live in `src/hooks` and start with `use`.
- Enforce formatting via ESLint and Prettier (`npm run lint` or your editor integration); keep Tailwind class stacks consistent with existing gradients and utility ordering.

## Testing Guidelines
- Frontend tests reside under `frontend/src/{app,components}/__tests__` with filenames ending in `.test.tsx`; colocate new specs beside the component under test.
- Prefer React Testing Library patterns (query by role/text, avoid snapshots) and cover new UI states before opening a PR.
- No backend test suite exists yet; when adding one, place pytest modules in `backend/tests/` and mock external services such as Chroma or OpenAI.

## Commit & Pull Request Guidelines
- Use concise, imperative commit subjects that call out the scope (e.g., `frontend: add course progress chart`); keep commits focused and include context in the body when touching multiple layers.
- PRs should describe the change, list manual/automated tests run, link related issues, and include screenshots or recordings for UI updates.
- Confirm `.env` values are excluded, scrub sensitive data from logs, and mention any migrations or data seeding steps reviewers must perform.

## Security & Configuration Tips
- Duplicate `backend/.env.example` to `.env` and populate API keys locally; never commit secrets or the generated `data/` artifacts.
- When using local LLM endpoints, document the `LLM_TYPE` and URLs in the PR description so reviewers can reproduce the setup.
