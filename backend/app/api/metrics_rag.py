from fastapi import APIRouter, Response
from typing import Dict, Any
import os
from services.metrics import metrics

try:
    from services.rag_service import RAGService
    from services.rag_service import get_rag_service  # provider if available
except Exception:
    RAGService = None
    get_rag_service = None

router = APIRouter(prefix="/metrics", tags=["metrics"])

def _get_rag() -> Any:
    if get_rag_service is not None:
        try:
            return get_rag_service()
        except Exception:
            pass
    # Fallback: create a local instance if needed
    try:
        return RAGService()
    except Exception:
        return None

@router.get("/rag")
async def get_rag_metrics() -> Dict[str, Any]:
    rag = _get_rag()
    if rag is None:
        return {"status": "unavailable"}
    mode = os.getenv("RAG_MODE", "hybrid")
    cache_size = len(getattr(rag, "query_cache", {}))
    return {
        "status": "ok",
        "mode": mode,
        "retrieval_count": int(getattr(rag, "retrieval_count", 0)),
        "average_retrieval_time_ms": float(getattr(rag, "average_retrieval_time", 0.0)),
        "query_cache_size": cache_size
    }

@router.get("/prometheus")
async def get_prometheus_metrics():
    content_type, payload = metrics.export_prometheus()
    return Response(content=payload, media_type=content_type)

@router.get("/metrics")
async def get_root_metrics():
    content_type, payload = metrics.export_prometheus()
    return Response(content=payload, media_type=content_type)
