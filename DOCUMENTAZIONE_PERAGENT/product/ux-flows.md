# Flussi Prodotto & UX

Documenti utili:
- `docs/ROADMAP.md` – iniziative pianificate (mindmap, tutor, planner).
- `docs/FAQ.md` – FAQ funzionali.
- `docs/IMPLEMENTATION_SUMMARY.md` – stato feature principali.
- `docs/COGNITIVE_LEARNING_ROADMAP.md` – strategie pedagogiche.

Flussi chiave:
1. **Onboarding corso** – creare corso → caricare PDF in `BookDetailClient` → aprire "Studio Integrato".
2. **Studio guidato** – pagina `study` con layout dinamico (split/pdf/chat focus), annotazioni in tempo reale, salvataggio note e refresh materiali.
3. **Tutor conversazionale** – `IntegratedChatTutor` mostra confidence, suggerimenti, note rapide e cronologia sorgenti.
4. **Apprendimento attivo** – API per spaced repetition, active recall, dual coding disponibili in `backend/main.py` e surface tramite pagine `/practice`, `/quiz`, `study-planner`.
