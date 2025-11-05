# Study Mindmap System

## Overview

Tutor-AI now generates **structured study mindmaps** that blend course materials, RAG context, and AI guidance. The system produces both rich JSON (for interactive rendering) and markdown (for exports) and supports iterative expansion with the `/mindmap/expand` endpoint.

Key improvements:

- Deterministic JSON schema (`title`, `overview`, `nodes`, `study_plan`, `references`).
- Each node includes actionable `study_actions`, AI usage hints, and references.
- Optional AI-driven expansion that appends new sub-concepts on demand.
- `/slides/static` exposure makes saved HTML/PDF assets downloadable; mindmaps reuse the same approach to serve static artefacts.
- Mindmaps can be persisted under `data/courses/<course_id>/books/<book_id>/mindmaps.json` via `POST /courses/{course}/books/{book}/mindmaps`.

## API Contracts

### `POST /mindmap`

**Request**

```jsonc
{
  "course_id": "course-123",
  "book_id": "book-456",
  "topic": "Fisica Quantistica",
  "focus_areas": ["principi fondamentali", "applicazioni", "esperimenti storici"]
}
```

**Response**

```jsonc
{
  "success": true,
  "mindmap": {
    "title": "Fisica Quantistica",
    "overview": "Sintesi...",
    "nodes": [
      {
        "id": "principi-base",
        "title": "Principi base",
        "summary": "",
        "ai_hint": "Chiedi all'assistente di generare esempi su...",
        "study_actions": ["Rivedi il capitolo 2", "Sintetizza il principio di indeterminazione"],
        "priority": 3,
        "references": ["dispensa_cap2.pdf"],
        "children": [ ... ]
      }
    ],
    "study_plan": [
      {
        "phase": "Fase 1 - Comprensione",
        "objective": "Acquisire i concetti fondamentali",
        "activities": ["Leggi il capitolo", "Chiedi un riassunto critico all'AI"],
        "ai_support": "Usa l'assistente per generare flashcard",
        "duration_minutes": 45
      }
    ],
    "references": ["dispensa_cap2.pdf", "lezione3.md"]
  },
  "markdown": "# Fisica Quantistica...",
  "study_plan": [...],
  "references": [...],
  "sources": [...],
  "metadata": {
    "course_id": "course-123",
    "book_id": "book-456",
    "generated_at": "2025-11-04T16:25:12.394Z",
    "source_count": 4
  }
}
```

If JSON parsing fails, the backend falls back to parsing the markdown response, guaranteeing a structured payload.

### `POST /mindmap/expand`

Expands a single node with context-aware sub-concepts.

**Request**

```jsonc
{
  "course_id": "course-123",
  "book_id": "book-456",
  "node_text": "Principi base",
  "node_context": "Fisica Quantistica > Principi base",
  "max_children": 4
}
```

**Response**

```jsonc
{
  "success": true,
  "expanded_nodes": [
    {
      "id": "principi-base-incertezza",
      "title": "Principio di indeterminazione",
      "summary": "Breve descrizione...",
      "ai_hint": "Chiedi all'assistente di creare quiz sul principio",
      "study_actions": [
        "Confronta esempi concreti",
        "Genera flashcard con l'AI"
      ],
      "priority": 2,
      "references": ["dispensa_cap3.pdf"]
    }
  ],
  "sources_used": ["Fonte 1", "Fonte 2"],
  "query_time": 2.13,
  "generation_method": "rag_expansion"
}
```

Fallback logic ensures a meaningful list of children even if the LLM fails.

### `POST /courses/{course_id}/books/{book_id}/mindmaps`

Persists generated maps. Payload mirrors the new structure:

```jsonc
{
  "title": "Fisica Quantistica",
  "content_markdown": "# Fisica Quantistica...",
  "structured_map": { ... },
  "metadata": {
    "course_id": "course-123",
    "book_id": "book-456",
    "references": [...],
    "sources": [...]
  }
}
```

Legacy mindmaps (stored as plain strings) are still readable; the API auto-fills empty structures when loading older records.

## Frontend Experience

- `MindmapExplorer` renders the hierarchical map, displays summaries, study actions, AI hints, and allows inline expansion.
- Users can regenerate, expand nodes with AI, download markdown, and save the map to the course.
- Study-plan phases are surfaced alongside references and global AI suggestions.

## Implementation Notes

- Helper utilities (`_normalize_mindmap_payload`, `_mindmap_to_markdown`, `_parse_markdown_to_structure`) guarantee consistent payloads even with imperfect LLM output.
- IDs are slugified and deduplicated to keep React rendering stable.
- Markdown export is kept in sync with the JSON payload for interoperability.

_Last updated: 2025-11-04_
