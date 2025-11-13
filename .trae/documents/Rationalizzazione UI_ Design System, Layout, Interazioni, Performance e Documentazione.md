## Obiettivi
- Unificare stile e componenti con un Design System coerente e accessibile (WCAG AA).
- Stabilizzare layout responsive, gerarchie visive e spaziatura.
- Standardizzare stati interattivi, transizioni e feedback.
- Migliorare performance visive e UX con ottimizzazioni mirate.
- Documentare scelte e creare storie dei componenti.

## Contesto Attuale (Frontend)
- Next.js App Router: `frontend/src/app` con pagine corpose (es. `courses/[id]/page.tsx`, `settings/page.tsx`).
- Componenti: `frontend/src/components` (es. `BookCard.tsx`, `CourseCard.tsx`, `ChatWrapper.tsx`, `PDFViewer.tsx`, `EnhancedPDFReader.tsx`, `VisualMindmap.tsx`, `concept-map/*`, `ui/*`).
- Styling: Tailwind v4 (`frontend/tailwind.config.ts`) + `globals.css` con ampio set di token in CSS variables.
- Librerie UI: Radix UI (tabs/progress), `lucide-react`, `@heroicons/react`, `framer-motion`. Storybook assente.

## Fase 1 — Design System (Fondazioni)
- Tokens centralizzati
  - Consolidare i CSS variables in `frontend/src/app/globals.css` per: colori (`primary`, `neutral`, `accent`, `success`, `warning`, `danger`), tipografia (scale, line-height), spaziatura, raggi, ombre, transizioni.
  - Allineare `frontend/tailwind.config.ts` per referenziare i tokens (es. colori e scale) e ridurre duplicazioni.
  - Palette WCAG AA: definire toni e contrasto per tema chiaro/scuro con coppie testo/sfondo e stati (hover/active/focus). Esempio categorie: `primary`, `surface`, `content`, `border`, `muted`, `info/success/warning/danger`.
- Tipografia
  - Adottare `next/font` in `frontend/src/app/layout.tsx` per font principali (Inter, JetBrains Mono) con fallback sicuri.
  - Introdurre gerarchie chiare: titoli (H1–H6), corpo, didascalie, monospazio; creare componenti `Typography` con varianti (display, title, body, caption, code).
- Primitivi UI
  - Standardizzare componenti base in `frontend/src/components/ui/` (o nuova cartella `design-system/` se opportuno): `Button`, `Input`, `Textarea`, `Select`, `Card`, `Modal`, `Tabs` (wrapping Radix), `Toast` (Radix), `Progress`.
  - Varianti e stati predefiniti: `primary`, `secondary`, `ghost`, `destructive`, `success`, con `disabled`, `loading`.

## Fase 2 — Layout e Gerarchie Visive
- Griglia responsive
  - Introdurre un sistema 12 colonne via utilità Tailwind (grid/cols/gap) e container con breakpoints coerenti.
  - Componenti layout: `AppShell` (header, sidebar, content), `PageHeader`, `PageSection`, `PageGrid` per riuso.
- Bilanciamento visivo
  - Definire scala spaziatura (tokens) e regole di allineamento; ottimizzare spazio negativo su sezioni dense.
  - Applicare gerarchie visive con dimensioni/contrasto/posizionamento consistenti nelle pagine principali.
- Refactor mirati
  - Spezzare componenti/pagine molto grandi per separare presentazione, interazioni e dati:
    - `frontend/src/components/VisualMindmap.tsx` (subcomponenti: layout, nodo, pannelli, interazioni).
    - `frontend/src/components/ChatWrapper.tsx` (message list, input, sidebar/mindmap, hooks LLM).
    - Pagine corpose: `study-planner/page.tsx`, `courses/[id]/page.tsx`, `settings/page.tsx`, `search/page.tsx`.

## Fase 3 — Interazioni e Micro‑Interazioni
- Stati interattivi standard
  - Focus ring consistente: `focus-visible` con ring e offset basati su tokens; contrasto AA assicurato.
  - Hover/active/pressed uniformi su `Button`, `Link`, `Card`, controlli form; `aria-*` e `role` dove necessario.
- Transizioni fluide
  - Durate/easing standard (tokens: `fast`, `normal`, `slow` + cubic-bezier coerente).
  - Animare solo `transform`/`opacity`; evitare `width/height/left/top` per minimizzare reflow.
  - Usare `framer-motion` solo dove serve (tooltip complessi, espansioni), altrove CSS transitions.
- Feedback immediato
  - Introduzione `Toast`/`Snackbar` con Radix; indicatori di progresso e `Skeleton` caricamento.
  - Stati `pending/success/error` standardizzati in azioni critiche (upload, annotazioni PDF, chat invio).

## Fase 4 — Performance Visive
- Risorse grafiche
  - `next/image` per raster (con `remotePatterns` già configurato in `frontend/next.config.js`); `priority` sopra‑the‑fold; `loading="lazy"` altrove.
  - SVG inline/icon libs per vettoriali; audit delle dimensioni e deduplicazioni.
- Minimizzare repaint/reflow
  - `content-visibility: auto` su liste/pannelli estesi; `will-change: transform` solo prima di animazioni.
  - Evitare layout thrashing; batch degli aggiornamenti di stato nelle UI ad alta frequenza (mindmap, annotazioni).
- Progressive enhancement
  - Semantica HTML + ARIA completa, fallback funzionali senza JS pesante.
  - `next/dynamic` già presente: rafforzare per componenti pesanti (`PDFViewer`, `Mindmap`), con placeholder/skeleton.

## Fase 5 — Documentazione e Storie
- Storybook
  - Aggiungere configurazione base (`.storybook/main.ts`, `preview.ts`) e storie per `Button`, `Card`, `Typography`, `Input`, `Tabs`, `Modal`, `Toast` con varianti/stati e tema chiaro/scuro.
- Linee guida
  - Documentare scelte in `docs/design/` (palette, tipografia, layout, interazioni, accessibilità) con esempi d’uso ed estensione.
  - Checklist WCAG (contrasto, focus, tastiera, annunci ARIA) e best practice performance (immagini, transizioni, code splitting).

## File/Entry Points Coinvolti
- `frontend/src/app/globals.css` — tokens e temi; focus ring; transizioni.
- `frontend/tailwind.config.ts` — allineamento tema e scale; dark mode.
- `frontend/src/app/layout.tsx` — integrazione `next/font`, tema e shell base.
- `frontend/src/components/ui/*` — standardizzazione componenti e varianti; Radix wrappers (`tabs.tsx`, `progress.tsx`).
- Pagine da razionalizzare: `frontend/src/app/study-planner/page.tsx`, `frontend/src/app/courses/[id]/page.tsx`, `frontend/src/app/settings/page.tsx`, `frontend/src/app/search/page.tsx`, `frontend/src/app/courses/[id]/materials/[filename]/workspace.tsx`.
- Componenti grandi: `frontend/src/components/VisualMindmap.tsx`, `frontend/src/components/ChatWrapper.tsx`, `frontend/src/components/PDFViewer.tsx`, `frontend/src/components/EnhancedPDFReader.tsx`, `frontend/src/components/concept-map/*`.
- `frontend/next.config.js` — immagini, ottimizzazioni (`optimizePackageImports`).

## Criteri di Accettazione
- Contrasto WCAG AA verificato per testo/controlli in tema chiaro/scuro.
- Focus/keyboard navigation completi su tutti i componenti interattivi.
- Performance: LCP < 2.5s sulle pagine principali, transizioni fluide senza jank.
- Copertura storie: componenti base con varianti/stati documentati e testati visivamente.
- Coerenza visiva: gerarchie tipografiche e spaziatura uniformi tra pagine.

## Roadmap Operativa
1. Fondazioni (tokens, tipografia, focus ring) — aggiornare `globals.css`, `tailwind.config.ts`, `layout.tsx`.
2. Primitivi UI e varianti — consolidare in `components/ui/` e applicare nei componenti esistenti.
3. Layout/AppShell — introdurre griglia e rifattorizzare le pagine ad alto impatto.
4. Interazioni e feedback — micro‑interazioni, toast, skeleton.
5. Performance pass — immagini, content‑visibility, dynamic imports.
6. Documentazione e Storybook — storie e guide d’uso/estensione.

Conferma e preferenze: se vuoi, posso proporre una palette iniziale AA e una scala tipografica concreta da applicare subito, oppure procedere direttamente con l’implementazione della Fase 1.