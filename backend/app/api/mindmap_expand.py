from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any, Set
import json
import re
import unicodedata
from datetime import datetime

from services.llm_service import LLMService
from services.rag_service import RAGService

router = APIRouter(prefix="/mindmap", tags=["mindmap"])

class MindmapExpandRequest(BaseModel):
    course_id: str
    book_id: Optional[str] = None
    node_text: str
    node_context: str
    max_children: int = 5

class ExpandedMindmapNode(BaseModel):
    id: str
    title: str
    summary: Optional[str] = ""
    ai_hint: Optional[str] = ""
    study_actions: List[str] = []
    priority: Optional[int] = None
    references: List[str] = []

class MindmapExpandResponse(BaseModel):
    success: bool
    expanded_nodes: List[ExpandedMindmapNode]
    sources_used: List[str] = []
    query_time: float = 0
    generation_method: str = "rag_expansion"


def _slugify_text(text: str, fallback: str = "node") -> str:
    if not text:
        return fallback
    normalized = unicodedata.normalize("NFKD", str(text)).encode("ascii", "ignore").decode("ascii")
    cleaned = re.sub(r"[^a-zA-Z0-9\\s-]", "", normalized).strip().lower()
    cleaned = re.sub(r"[\\s_-]+", "-", cleaned)
    return cleaned or fallback

def _extract_json_array(raw_text: str) -> List[Dict[str, Any]]:
    """
    Try to extract a JSON array from an LLM response. Falls back to an empty list.
    """
    if not raw_text:
        return []

    text = raw_text.strip()
    if "```" in text:
        fence_start = text.find("```")
        fence_end = text.rfind("```")
        if fence_end > fence_start:
            snippet = text[fence_start + 3:fence_end]
            # Remove potential language hint (e.g. ```json)
            text = snippet.strip()
            if text.lower().startswith("json"):
                text = text[4:].strip()

    parse_candidates = [text]

    # Add bracket slicing fallback
    start = text.find("[")
    end = text.rfind("]")
    if start != -1 and end != -1:
        parse_candidates.append(text[start : end + 1])

    for candidate in parse_candidates:
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, list):
                return [item for item in parsed if isinstance(item, dict)]
        except Exception:
            continue

    return []

def _format_sources(sources: Optional[List[Dict[str, Any]]]) -> List[str]:
    """
    Format RAG metadata into human readable references for the client.
    """
    formatted: List[str] = []
    if not sources:
        return formatted

    for source in sources:
        if not isinstance(source, dict):
            continue
        name = str(source.get("source") or source.get("document") or "").strip()
        if not name:
            name = "Fonte sconosciuta"

        chunk_idx = source.get("chunk_index")
        if isinstance(chunk_idx, int):
            label = f"{name} (chunk {chunk_idx + 1})"
        else:
            label = name

        score = source.get("relevance_score")
        if isinstance(score, (int, float)):
            label = f"{label} - rilevanza {score:.2f}"

        formatted.append(label)

    # Preserve order but limit duplicates
    seen = set()
    unique = []
    for entry in formatted:
        if entry in seen:
            continue
        seen.add(entry)
        unique.append(entry)
    return unique

def get_llm_service() -> LLMService:
    return LLMService()

def get_rag_service() -> RAGService:
    return RAGService()

@router.post("/expand", response_model=MindmapExpandResponse)
async def expand_mindmap_node(
    request: MindmapExpandRequest,
    llm_service: LLMService = Depends(get_llm_service),
    rag_service: RAGService = Depends(get_rag_service)
):
    """
    Expand a mindmap node using RAG + AI to generate relevant sub-concepts
    """
    try:
        start_time = datetime.now()

        # Build search query for RAG
        search_query = f"{request.node_text} {request.node_context}".strip()

        # Search for relevant content using RAG
        context_content = ""
        sources_used: List[str] = []

        rag_context = await rag_service.retrieve_context(
            query=search_query,
            course_id=request.course_id,
            book_id=request.book_id,
            k=max(request.max_children * 2, 6)
        )

        context_content = rag_context.get("text", "") if isinstance(rag_context, dict) else ""
        sources_used = _format_sources(rag_context.get("sources") if isinstance(rag_context, dict) else [])

        instructions = f"""
Sei un assistente accademico specializzato in mappe concettuali. Espandi il nodo indicato con sotto-concetti concreti.

DEVI restituire esclusivamente un array JSON valido di oggetti con questo schema:
[
  {{
    "title": "Titolo specifico del sotto-concetto",
    "summary": "Descrizione sintetica (max 2 frasi)",
    "ai_hint": "Suggerimento pratico su come utilizzare l'assistente AI",
    "study_actions": ["Attività concreta 1", "Attività concreta 2"],
    "priority": 1,
    "references": ["Fonte o capitolo rilevante"]
  }}
]

Requisiti:
- Genera esattamente {request.max_children} elementi.
- Ogni elemento deve essere specifico e applicabile da uno studente universitario.
- "study_actions" devono essere azioni studentesche e concrete (es: "Crea una sintesi", "Chiedi all'AI quiz sulla formula X").
- "ai_hint" deve spiegare come usare l'AI per approfondire quel sotto-concetto.
- Usa i materiali forniti quando disponibili.

Nodo principale: {request.node_text}
Contesto gerarchico: {request.node_context}

Contenuto RAG (se disponibile):
{context_content or 'Nessun contenuto RAG disponibile.'}
""".strip()

        raw_response = await llm_service.generate_response(
            query=instructions,
            context={"text": context_content, "sources": sources_used},
            course_id=request.course_id
        )

        parsed_items = _extract_json_array(raw_response)

        used_ids: Dict[str, int] = {}
        seen_titles: Set[str] = set()

        def next_node_id(title: str) -> str:
            base = _slugify_text(title)
            counter = used_ids.get(base, 0)
            used_ids[base] = counter + 1
            return base if counter == 0 else f"{base}-{counter + 1}"

        expanded_nodes: List[ExpandedMindmapNode] = []

        for item in parsed_items:
            if not isinstance(item, dict):
                continue
            title = str(item.get("title") or item.get("label") or "").strip()
            if not title:
                continue
            # Skip duplicate titles regardless of casing
            lower_title = title.lower()
            if lower_title in seen_titles:
                continue
            seen_titles.add(lower_title)

            node_id = next_node_id(title)
            priority = item.get("priority")
            if isinstance(priority, (int, float)):
                priority = int(priority)
            elif isinstance(priority, str) and priority.isdigit():
                priority = int(priority)
            else:
                priority = None
            expanded_nodes.append(ExpandedMindmapNode(
                id=node_id,
                title=title,
                summary=str(item.get("summary") or item.get("description") or "").strip(),
                ai_hint=str(item.get("ai_hint") or item.get("aiGuidance") or "").strip(),
                study_actions=[str(act).strip() for act in (item.get("study_actions") or item.get("activities") or []) if str(act).strip()],
                priority=priority,
                references=[str(ref).strip() for ref in (item.get("references") or []) if str(ref).strip()]
            ))

        # Enrich nodes with defaults when needed
        for node in expanded_nodes:
            if not node.study_actions:
                node.study_actions = [
                    f"Rivedi il concetto chiave '{node.title}' confrontandolo con gli appunti di corso.",
                    "Chiedi all'assistente AI un quiz mirato da 3 domande su questo sotto-concetto."
                ]
            if not node.ai_hint:
                node.ai_hint = "Utilizza l'assistente AI per generare esempi applicativi e domande di autovalutazione."

        if not expanded_nodes:
            for index in range(request.max_children):
                base_id = next_node_id(f"{request.node_text}-{index + 1}")
                expanded_nodes.append(ExpandedMindmapNode(
                    id=base_id,
                    title=f"Approfondimento {index + 1}: {request.node_text}",
                    summary=f"Analizza un aspetto specifico di {request.node_text} al livello {index + 1}.",
                    ai_hint="Chiedi all'assistente di generare esempi o domande pratiche su questo sotto-concetto.",
                    study_actions=[
                        "Rivedi le note del corso relative a questo tema.",
                        "Sintetizza i concetti chiave in 5 frasi e verifica con l'assistente AI."
                    ],
                    priority=None,
                    references=[]
                ))

        # Trim or pad to exact max_children
        if len(expanded_nodes) > request.max_children:
            expanded_nodes = expanded_nodes[:request.max_children]
        while len(expanded_nodes) < request.max_children:
            index = len(expanded_nodes)
            fallback_id = next_node_id(f"{request.node_text}-extra-{index + 1}")
            expanded_nodes.append(ExpandedMindmapNode(
                id=fallback_id,
                title=f"Estensione {index + 1}: {request.node_text}",
                summary=f"Esplora ulteriormente {request.node_text} considerando casi applicativi pratici.",
                ai_hint="Chiedi all'AI di produrre un caso studio o un quiz rapido.",
                study_actions=["Identifica un esempio applicativo reale.", "Confrontalo con le spiegazioni fornite dall'assistente AI."],
                priority=None,
                references=[]
            ))

        query_time = (datetime.now() - start_time).total_seconds()

        return MindmapExpandResponse(
            success=True,
            expanded_nodes=expanded_nodes,
            sources_used=sources_used,
            query_time=query_time,
            generation_method="rag_expansion"
        )

    except Exception as e:
        print(f"Error in mindmap expansion: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to expand mindmap node: {str(e)}")

@router.get("/status")
async def get_mindmap_status():
    """
    Check mindmap expansion service status
    """
    return {
        "status": "active",
        "features": {
            "rag_expansion": True,
            "ai_generation": True,
            "context_aware": True,
            "source_tracking": True
        },
        "max_expansions_per_request": 10,
        "supported_node_types": ["concept", "topic", "definition", "example"]
    }
