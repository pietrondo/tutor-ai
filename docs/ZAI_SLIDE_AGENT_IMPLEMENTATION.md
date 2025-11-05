# ZAI Slide Agent Integration – Tutor-AI

## Overview

Tutor-AI uses the **Z.AI GLM Slide/Poster Agent (`slides_glm_agent`)** to generate rich presentations (HTML + PDF) on demand.
The backend handles streaming responses, persists assets locally, and exposes download URLs for the frontend.

This document captures the latest implementation and operational notes.

---

## Configuration

Environment variables (set in `backend/.env`, mounted in Docker):

```
LLM_TYPE=zai
ZAI_API_KEY=<your_key>
ZAI_MODEL=glm-4.5
ZAI_BASE_URL=https://api.z.ai/api/paas/v4/
```

Ensure the Z.AI account has sufficient balance; otherwise requests will fail with error code `1113`.

---

## API Flow

### Backend Endpoint

```
POST /slides/generate
```

Request body (`SlideGenerationRequest`):

```jsonc
{
  "course_id": "course-123",
  "book_id": "optional-book-id",
  "topic": "Circular Economy",
  "description": "optional custom prompt",
  "num_slides": 8,
  "style": "modern",
  "audience": "university"
}
```

### High-Level Steps

1. **RAG Context (optional)** – When `book_id` is provided, the service injects retrieved course snippets into the prompt.
2. **GLM Slide Agent Call** – `llm_service.generate_slides_with_glm_slide_agent` posts to `https://api.z.ai/api/v1/agents`
   and consumes the streaming SSE response.
3. **Async Polling** – If the agent returns `status=pending`, the service polls
   `POST /v1/agents/get-async-result` until success or timeout.
4. **Conversation Export** – When no PDF URL is present, the service calls
   `POST /v1/agents/conversation` with `{ "custom_variables": { "include_pdf": true } }`
   to request final assets.
5. **Asset Persistence** – HTML/PDF responses are saved under `data/slides/`.
   The backend also exposes `/slides/static/<filename>` for direct downloads.
6. **Response Serialization** – The endpoint stores the full generation in JSON (`data/slide_generations.json`)
   and returns URLs plus metadata to the client.

---

## Key Modules & Responsibilities

| File | Responsibility |
|------|----------------|
| `backend/services/llm_service.py` | Handles requests to Z.AI agent, SSE parsing, async polling, asset download, and metadata extraction. |
| `backend/app/api/slides.py` | Coordinates RAG context, orchestrates the generation flow, persists storage, and returns slide URLs. |
| `backend/main.py` | Mounts static routes (`/slides/static`) so locally saved PDFs/HTML files are downloadable. |

---

## Response Payload

Example of returned JSON from `POST /slides/generate` (success):

```jsonc
{
  "success": true,
  "slide_id": "uuid",
  "topic": "Circular Economy",
  "slide_urls": [
    "https://storage.z.ai/.../slides.pdf",
    "/slides/static/Circular_Economy_20251105_123456.pdf",
    "https://cdn.z.ai/slide_image.png"
  ],
  "download_urls": [
    "https://storage.z.ai/.../slides.pdf",
    "/slides/static/Circular_Economy_20251105_123456.pdf"
  ],
  "metadata": {
    "generation_method": "zai_glm_slide_agent",
    "num_slides": 8,
    "style": "modern",
    "pdf_url": "https://storage.z.ai/.../slides.pdf",
    "pdf_local_url": "/slides/static/Circular_Economy_20251105_123456.pdf",
    "html_local_url": "/slides/static/Circular_Economy_20251105_123456.html",
    "image_count": 6,
    "conversation_id": "1762..."
  }
}
```

All local assets live in `data/slides/`; the storage record contains the file system path (`slide_pdf_path`) in addition to the public URLs.

---

## Streaming & Parsing Notes

* `_request_agent_stream` converts the SSE feed to a list of JSON events.
* `_parse_glm_slide_agent_messages` accepts either a single event or an array of events and extracts:
  * HTML fragments (`output` from tool calls)
  * `file_url` entries (PDF export)
  * `image_url` entries (generated slide previews)
  * free-form text fragments
* `_poll_glm_slide_async_result` retries the async endpoint up to 10 times (3s interval).

---

## Static Asset Serving

`backend/main.py` mounts:

```
/uploads        -> data/uploads
/slides/static  -> data/slides
```

This allows the frontend (and API consumers) to download any generated PDF/HTML via HTTP:

```
GET http://localhost:8000/slides/static/<filename>
```

Ensure the reverse proxy (if any) forwards this path.

---

## Error Handling

| Scenario | Outcome |
|----------|---------|
| Invalid API key / missing key | Request fails before hitting GLM agent (`ZAI API not available`). |
| Account out of balance | Z.AI returns `status: failed` with error code `1113`; backend propagates `"Your account balance is insufficient..."`. |
| Async timeout | After 10 polling attempts the backend returns `Slide generation timed out during async polling`. |
| Download failure | Saves metadata without the PDF; logs warning. |
| Parsing failure | Falls back to joining raw text fragments to ensure non-empty response. |

Errors are logged under `services.llm_service` and returned to the caller with `detail`.

---

## Manual Testing Checklist

1. Export your Z.AI key to `.env` and confirm `LLM_TYPE=zai`.
2. `docker-compose build` and `docker-compose up -d`.
3. `curl -X POST http://localhost:8000/slides/generate -H "Content-Type: application/json" -d '{...}'`
4. Inspect `data/slides/` for new files and verify downloads via `/slides/static/...`.
5. Check `data/slide_generations.json` for metadata persistence.

---

## Troubleshooting

* **500 “Your account balance is insufficient.”** – Recharge Z.AI credits.
* **PDF not downloadable** – Ensure FastAPI static mount is active; confirm file exists in `data/slides`.
* **Frontend still sees old mock data** – Confirm `LLM_TYPE` is `zai` and restart containers.
* **Slow responses** – Z.AI slide generation can take 30–60 seconds; increase timeouts if needed.

---

## TODO / Ideas

* Add automated integration tests with a mocked GLM Slide Agent response.
* Provide an authenticated download endpoint to avoid exposing `/slides/static` publicly.
* Cache conversation snapshots to avoid repeated exports when re-downloading the same slide.

---

_Last updated: 2025-11-04_
