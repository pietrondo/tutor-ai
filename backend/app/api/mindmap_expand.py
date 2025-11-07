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

def _clean_node_title(title: str) -> str:
    """
    Clean node title by removing URLs, references, and technical identifiers
    """
    print(f"🧹 DEBUG: Cleaning title: {title}")

    if not title or not isinstance(title, str):
        print("❌ DEBUG: Invalid title, returning 'Concetto'")
        return "Concetto"

    original_title = title.lower()  # Keep for fallback detection
    cleaned = title.strip()

    print(f"📝 DEBUG: Original title: {original_title}")
    print(f"🔍 DEBUG: Initial cleaned: {cleaned}")

    # Step 1: Remove URLs completely
    cleaned = re.sub(r'https?://[^\s\)\]]+', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'www\.[^\s\)\]]+', '', cleaned, flags=re.IGNORECASE)

    print(f"🌐 DEBUG: After URL removal: {cleaned}")

    # Step 2: Remove domain patterns aggressively (com, it, org sequences)
    # This handles patterns like "com it docs sebastiano-caboto-libro"
    cleaned = re.sub(r'\b[a-z-]+\s+(com|it|org|net|gov|edu)\s+[a-z-]+\b', '', cleaned, flags=re.IGNORECASE)
    # Also handle patterns where words with dashes follow domain names
    cleaned = re.sub(r'(com|it|org|net|gov|edu)\s+[\w-]*docs?[\w-]*', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'[\w-]*docs?[\w-]*\s+(com|it|org|net|gov|edu)', '', cleaned, flags=re.IGNORECASE)

    # Step 3: Remove common technical words and document references
    tech_words = ['docs', 'document', 'file', 'pdf', 'doc', 'down', 'upload', 'download']
    for word in tech_words:
        cleaned = re.sub(rf'\b{re.escape(word)}\b', '', cleaned, flags=re.IGNORECASE)

    # Step 4: Remove page/position references
    cleaned = re.sub(r'page:\s*\d+', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'pos:\s*\d+', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\(?\s*page:\s*\d+\s*,\s*pos:\s*\d+\s*\)?', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\([^)]*page[^)]*\)', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\([^)]*pos[^)]*\)', '', cleaned, flags=re.IGNORECASE)

    # Step 5: Remove bracketed references
    cleaned = re.sub(r'\[([^\]]+)\]', '', cleaned)

    # Step 6: Remove document references
    cleaned = re.sub(r'\(.*?documento.*?\)', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\(.*?posizione.*?\)', '', cleaned, flags=re.IGNORECASE)

    # Step 7: Remove "tratto da" and "estratto da"
    cleaned = re.sub(r'(tratto|estratto)\s+da\s*:.*', '', cleaned, flags=re.IGNORECASE)

    # Step 8: Remove file/document references with separators
    cleaned = re.sub(r'\b(file|documento|pdf|doc)\s*[:\-]?\s*[^\s]*', '', cleaned, flags=re.IGNORECASE)

    # Step 9: Remove hexadecimal IDs and long numbers
    cleaned = re.sub(r'\b[a-f0-9]{6,}\b', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\b\d{6,}\b', '', cleaned)

    # Step 10: Remove technical reference markers
    cleaned = re.sub(r'\b(doc|ref|source|id)\s*[:\-]?\s*[^\s]*', '', cleaned, flags=re.IGNORECASE)

    # Step 11: Remove libro + number patterns
    cleaned = re.sub(r'libro\s+\d+', '', cleaned, flags=re.IGNORECASE)

    # Step 12: Clean up empty parentheses and brackets
    cleaned = re.sub(r'\(\s*\)', '', cleaned)
    cleaned = re.sub(r'\[\s*\]', '', cleaned)

    # Step 13: Remove trailing punctuation and separators
    cleaned = re.sub(r'[\.\,\;]+$', '', cleaned)

    # Step 14: Clean up whitespace and punctuation (more comprehensive)
    cleaned = re.sub(r'\s+', ' ', cleaned)
    cleaned = re.sub(r'^[,\s:;\-_\.\)\]\[]+|[,\s:;\-_\.\(\[\]]+$', '', cleaned)

    cleaned = cleaned.strip()

    # Step 15: If still contains domain-like patterns, extract meaningful content
    if 'com' in cleaned.lower() or 'it' in cleaned.lower() or 'org' in cleaned.lower():
        # Extract meaningful words (longer than 2 characters, not domain names)
        words = cleaned.split()
        meaningful_words = []
        for word in words:
            word_lower = word.lower().strip('.,;:_-')
            if (len(word_lower) > 2 and
                word_lower not in ['com', 'it', 'org', 'net', 'gov', 'edu', 'http', 'https', 'www'] and
                not re.match(r'^[a-f0-9]{6,}$', word_lower)):
                meaningful_words.append(word)

        if meaningful_words:
            cleaned = ' '.join(meaningful_words)

    cleaned = cleaned.strip()

    # Step 16: Convert hyphens to spaces and normalize
    cleaned = re.sub(r'[-_]+', ' ', cleaned)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()

    # Step 17: Final fallback - if still too short or contains technical patterns, provide meaningful fallback
    if (len(cleaned) < 3 or
        'libro' in cleaned.lower() or
        re.search(r'\b[a-z]+-[a-z]+(?:-[a-z]+)*\b', cleaned)):  # Pattern like word-word or word-word-word

        if 'caboto' in original_title:
            cleaned = 'Viaggi di Esplorazione'
        elif 'sebastiano' in original_title:
            cleaned = 'Figure Storiche'
        elif 'scoperta' in original_title:
            cleaned = 'Scoperte Geografiche'
        elif 'viaggio' in original_title:
            cleaned = 'Esplorazioni'
        elif 'docs' in original_title or 'document' in original_title:
            cleaned = 'Documentazione Storica'
        elif 'storia' in original_title:
            cleaned = 'Contesto Storico'
        elif 'geografia' in original_title:
            cleaned = 'Geografia'
        else:
            cleaned = 'Concetto Principale'

    print(f"✅ DEBUG: Final cleaned title: '{cleaned}'")
    print(f"🔍 DEBUG: Length check - original: {len(title)}, cleaned: {len(cleaned)}")
    return cleaned

def _generate_intelligent_fallback_nodes(node_text: str, node_context: str, max_children: int) -> List[Dict[str, Any]]:
    """
    Generate intelligent fallback nodes based on the concept and context
    when no RAG content is available
    """
    print(f"🧠 Generating intelligent fallback nodes for: {node_text}")

    # Common concept templates for different academic subjects
    concept_templates = {
        # Historical concepts
        "storia": [
            {"title": "Contesto Storico", "summary": f"Analizza il periodo storico in cui si inserisce {node_text}", "priority": 1},
            {"title": "Cause Principali", "summary": f"Identifica le cause e i fattori che hanno portato a {node_text}", "priority": 1},
            {"title": "Sviluppo Cronologico", "summary": f"Segui l'evoluzione temporale di {node_text}", "priority": 2},
            {"title": "Conseguenze", "summary": f"Esamina gli effetti e le implicazioni di {node_text}", "priority": 2},
            {"title": "Figure Chiave", "summary": f"Identifica i protagonisti principali legati a {node_text}", "priority": 3}
        ],

        # Geographic concepts
        "geografia": [
            {"title": "Caratteristiche Fisiche", "summary": f"Analizza le caratteristiche geografiche e fisiche di {node_text}", "priority": 1},
            {"title": "Localizzazione", "summary": f"Esamina la posizione geografica e i confini di {node_text}", "priority": 1},
            {"title": "Clima e Ambiente", "summary": f"Studia le condizioni climatiche e ambientali di {node_text}", "priority": 2},
            {"title": "Popolazione e Cultura", "summary": f"Analizza gli aspetti demografici e culturali di {node_text}", "priority": 2},
            {"title": "Importanza Strategica", "summary": f"Valuta la rilevanza strategica di {node_text}", "priority": 3}
        ],

        # General academic concepts
        "generale": [
            {"title": "Definizione e Concetto", "summary": f"Approfondisci il significato e la definizione di {node_text}", "priority": 1},
            {"title": "Caratteristiche Principali", "summary": f"Identifica le caratteristiche distintive di {node_text}", "priority": 1},
            {"title": "Applicazioni Pratiche", "summary": f"Esamina come {node_text} si applica in contesti reali", "priority": 2},
            {"title": "Relazioni con Altri Concetti", "summary": f"Analizza i collegamenti tra {node_text} e concetti correlati", "priority": 2},
            {"title": "Implicazioni e Significato", "summary": f"Valuta l'importanza e le implicazioni di {node_text}", "priority": 3}
        ]
    }

    # Determine the best template based on keywords
    text_lower = node_text.lower()
    context_lower = node_context.lower()

    template_key = "generale"
    if any(keyword in text_lower + context_lower for keyword in ["storia", "storico", "evoluzione", "periodo", "epoca"]):
        template_key = "storia"
    elif any(keyword in text_lower + context_lower for keyword in ["geografia", "territorio", "luogo", "regione", "paese"]):
        template_key = "geografia"

    # Get the appropriate template
    base_template = concept_templates[template_key][:max_children]

    # Customize the template with the specific concept
    fallback_nodes = []
    for i, template in enumerate(base_template):
        fallback_nodes.append({
            "title": template["title"],
            "summary": template["summary"],
            "ai_hint": f"Chiedi all'assistente AI di approfondire {template['title'].lower()} con esempi specifici e dettagli",
            "study_actions": [
                f"Ricerca informazioni specifiche su {template['title'].lower()}",
                f"Prepara una sintesi su {template['title'].lower()} e confrontala con l'assistente AI"
            ],
            "priority": template["priority"]
        })

    print(f"✅ Generated {len(fallback_nodes)} intelligent fallback nodes using {template_key} template")
    return fallback_nodes

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

        # Debug logging to verify book_id is being used correctly
        print(f"🔍 Mindmap expansion - Course: {request.course_id}, Book: {request.book_id}")
        print(f"🔍 Search query: '{search_query}'")

        context_content = rag_context.get("text", "") if isinstance(rag_context, dict) else ""
        sources_used = _format_sources(rag_context.get("sources") if isinstance(rag_context, dict) else [])

        print(f"📊 RAG context found: {len(context_content)} characters")
        print(f"📚 Sources found: {len(sources_used)}")
        print(f"🔍 RAG response keys: {list(rag_context.keys()) if isinstance(rag_context, dict) else 'Not a dict'}")
        if len(context_content) > 0:
            print(f"📝 RAG context preview: {context_content[:200]}...")
        else:
            print("⚠️ No RAG context retrieved - this may cause duplicate fallback nodes")

        # Enhanced prompt that works better without RAG content
        has_rag_content = bool(context_content and len(context_content.strip()) > 50)

        if has_rag_content:
            instructions = f"""
Sei un assistente accademico specializzato in mappe concettuali. Espandi il nodo indicato con sotto-concetti logicamente strutturati basandoti sul contenuto fornito.

DEVI restituire esclusivamente un array JSON valido di oggetti con questo schema:
[
  {{
    "title": "Titolo specifico del sotto-concetto",
    "summary": "Descrizione sintetica che chiarisce il concetto (max 2 frasi)",
    "ai_hint": "Suggerimento pratico su come approfondire con l'assistente AI",
    "study_actions": ["Azione concreta 1", "Azione concreta 2"],
    "priority": 1
  }}
]

Requisiti FONDAMENTALI:
- Genera esattamente {request.max_children} elementi logicamente collegati
- I sotto-concetti devono essere specifici e gerarchicamente coerenti
- IMPORTANTE: NON includere MAI URL, link web, riferimenti a pagine, o citazioni di documenti
- IMPORTANTE: NON fare copia-incolla di frasi che contengono link o riferimenti esterni
- "study_actions": azioni studentesche concrete e misurabili
- "ai_hint": come usare l'AI per approfondire quel sotto-concetto specifico
- "priority": 1 (alta), 2 (media), 3 (bassa) - basata sull'importanza gerarchica
- NON includere campi "references" o fonti esterne
- Concentrati su contenuti accademici strutturati

Nodo principale: {request.node_text}
Contesto gerarchico: {request.node_context}

Contenuto RAG da utilizzare:
{context_content}

ATTENZIONE: Estrai solo i CONCETTI accademici rilevanti dal contenuto RAG, ignora completamente i riferimenti alle fonti!
""".strip()
        else:
            # Enhanced prompt for when no RAG content is available
            instructions = f"""
Sei un assistente accademico esperto in mappe concettuali. Genera sotto-concetti logicamente strutturati per il nodo indicato.

DEVI restituire esclusivamente un array JSON valido di oggetti con questo schema:
[
  {{
    "title": "Titolo specifico del sotto-concetto",
    "summary": "Descrizione sintetica che chiarisce il concetto (max 2 frasi)",
    "ai_hint": "Suggerimento pratico su come approfondire con l'assistente AI",
    "study_actions": ["Azione concreta 1", "Azione concreta 2"],
    "priority": 1
  }}
]

Linee guida per la generazione:
- Genera esattamente {request.max_children} sotto-concetti accademicamente validi
- Baseati sul contesto "{request.node_context}" e il concetto "{request.node_text}"
- Se è un concetto storico: includi aspetti come "Contesto storico", "Cause principali", "Sviluppo cronologico", "Conseguenze", "Figure chiave"
- Se è un concetto geografico: includi "Caratteristiche fisiche", "Localizzazione", "Clima e ambiente", "Importanza strategica"
- Per concetti generali: includi "Definizione", "Caratteristiche principali", "Applicazioni pratiche", "Relazioni con altri concetti"
- Ogni titolo deve essere specifico e accademicamente rilevante
- Le "study_actions" devono essere azioni concrete che lo studente può intraprendere
- Assegna priorità realistiche (1=alta, 2=media, 3=bassa)

Nodo principale: {request.node_text}
Contesto gerarchico: {request.node_context}

IMPORTANTE: Non creare nodi generici come "Approfondimento 1", "Approfondimento 2". Sii specifico e accademico.
""".strip()

        raw_response = await llm_service.generate_response(
            query=instructions,
            context={"text": context_content, "sources": sources_used},
            course_id=request.course_id
        )

        print(f"🤖 AI Raw Response (first 500 chars): {raw_response[:500]}...")
        print(f"🤖 AI Response length: {len(raw_response)} characters")

        parsed_items = _extract_json_array(raw_response)
        print(f"📊 Parsed {len(parsed_items)} items from AI response")
        print(f"🔍 Parsed items debug: {parsed_items[:2] if parsed_items else 'No items'}")  # Show first 2 items

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
                print(f"🔄 Skipping duplicate title: '{title}'")
                continue
            seen_titles.add(lower_title)
            print(f"✅ Processing unique title: '{title}'")

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
                title=_clean_node_title(title),  # Apply cleaning function
                summary=str(item.get("summary") or item.get("description") or "").strip(),
                ai_hint=str(item.get("ai_hint") or item.get("aiGuidance") or "").strip(),
                study_actions=[str(act).strip() for act in (item.get("study_actions") or item.get("activities") or []) if str(act).strip()],
                priority=priority,
                references=[]  # Remove references from expanded nodes
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

        print(f"🔍 Expanded nodes count before fallback check: {len(expanded_nodes)}")
        if not expanded_nodes:
            # Generate intelligent fallback nodes based on the concept
            print("🚨 No expanded nodes found, triggering intelligent fallback...")
            clean_node_text = _clean_node_title(request.node_text)
            fallback_nodes = _generate_intelligent_fallback_nodes(clean_node_text, request.node_context, request.max_children)

            for index, fallback_node in enumerate(fallback_nodes):
                base_id = next_node_id(fallback_node["title"])
                expanded_nodes.append(ExpandedMindmapNode(
                    id=base_id,
                    title=fallback_node["title"],
                    summary=fallback_node["summary"],
                    ai_hint=fallback_node["ai_hint"],
                    study_actions=fallback_node["study_actions"],
                    priority=fallback_node["priority"],
                    references=[]
                ))

        # Trim or pad to exact max_children
        if len(expanded_nodes) > request.max_children:
            expanded_nodes = expanded_nodes[:request.max_children]
        while len(expanded_nodes) < request.max_children:
            index = len(expanded_nodes)
            fallback_id = next_node_id(f"{request.node_text}-extra-{index + 1}")
            clean_node_text = _clean_node_title(request.node_text)
            expanded_nodes.append(ExpandedMindmapNode(
                id=fallback_id,
                title=f"Estensione {index + 1}: {clean_node_text}",
                summary=f"Esplora ulteriormente {clean_node_text} considerando casi applicativi pratici.",
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

class MindmapEditRequest(BaseModel):
    course_id: str
    book_id: Optional[str] = None
    node_id: str
    current_title: str
    current_summary: str = ""
    edit_instruction: str

class MindmapEditResponse(BaseModel):
    success: bool
    edited_node: ExpandedMindmapNode
    sources_used: List[str] = []
    query_time: float = 0
    generation_method: str = "ai_edit"

@router.post("/edit", response_model=MindmapEditResponse)
async def edit_mindmap_node(
    request: MindmapEditRequest,
    llm_service: LLMService = Depends(get_llm_service),
    rag_service: RAGService = Depends(get_rag_service)
):
    """
    Edit a mindmap node using AI based on user instructions
    """
    try:
        start_time = datetime.now()

        # Build search query for RAG
        search_query = f"{request.current_title} {request.current_summary} {request.edit_instruction}".strip()

        # Search for relevant content using RAG
        context_content = ""
        sources_used: List[str] = []

        rag_context = await rag_service.retrieve_context(
            query=search_query,
            course_id=request.course_id,
            book_id=request.book_id,
            k=6
        )

        context_content = rag_context.get("text", "") if isinstance(rag_context, dict) else ""
        sources_used = _format_sources(rag_context.get("sources") if isinstance(rag_context, dict) else [])

        instructions = f"""
Sei un assistente accademico specializzato. Modifica il nodo della mappa concettuale secondo le istruzioni dell'utente.

DEVI restituire esclusivamente un oggetto JSON valido con questo schema:
{{
  "title": "Titolo modificato del nodo",
  "summary": "Descrizione sintetica che chiarisce il concetto (max 2 frasi)",
  "ai_hint": "Suggerimento pratico su come approfondire con l'assistente AI",
  "study_actions": ["Azione concreta 1", "Azione concreta 2"],
  "priority": 1
}}

Requisiti:
- Segui attentamente l'istruzione dell'utente: "{request.edit_instruction}"
- Mantieni la coerenza accademica e gerarchica
- "study_actions": azioni studentesche concrete e misurabili
- "ai_hint": come usare l'AI per approfondire questo nodo
- "priority": 1 (alta), 2 (media), 3 (bassa)
- NON includere referenze esterne

Contenuto corrente del nodo:
Titolo: {request.current_title}
Summary: {request.current_summary}

Contenuto RAG (se disponibile):
{context_content or 'Nessun contenuto RAG disponibile.'}
""".strip()

        raw_response = await llm_service.generate_response(
            query=instructions,
            context={"text": context_content, "sources": sources_used},
            course_id=request.course_id
        )

        # Try to extract JSON object (not array)
        parsed_item = None
        try:
            # Remove ```json and ``` if present
            if "```" in raw_response:
                start = raw_response.find("```")
                end = raw_response.rfind("```")
                if end > start:
                    snippet = raw_response[start + 3:end].strip()
                    if snippet.lower().startswith("json"):
                        snippet = snippet[4:].strip()
                    raw_response = snippet

            # Find JSON object boundaries
            start = raw_response.find("{")
            end = raw_response.rfind("}")
            if start != -1 and end != -1:
                json_str = raw_response[start:end + 1]
                parsed_item = json.loads(json_str)
        except Exception as e:
            print(f"Error parsing AI edit response: {e}")

        # Fallback if parsing fails
        if not parsed_item or not isinstance(parsed_item, dict):
            parsed_item = {
                "title": request.current_title,
                "summary": request.current_summary,
                "ai_hint": "Utilizza l'assistente AI per approfondire questo concetto.",
                "study_actions": ["Rivedi il concetto", "Chiedi chiarimenti all'AI"],
                "priority": 2
            }

        # Extract and validate data
        title = str(parsed_item.get("title") or request.current_title).strip()
        summary = str(parsed_item.get("summary") or request.current_summary).strip()
        ai_hint = str(parsed_item.get("ai_hint") or "Utilizza l'assistente AI per approfondire questo concetto.").strip()

        study_actions = []
        raw_actions = parsed_item.get("study_actions", [])
        if isinstance(raw_actions, list):
            study_actions = [str(act).strip() for act in raw_actions if str(act).strip()]

        if not study_actions:
            study_actions = ["Rivedi il concetto chiave", "Chiedi chiarimenti all'assistente AI"]

        priority = parsed_item.get("priority")
        if isinstance(priority, (int, float)):
            priority = int(priority)
        elif isinstance(priority, str) and priority.isdigit():
            priority = int(priority)
        else:
            priority = 2

        edited_node = ExpandedMindmapNode(
            id=request.node_id,
            title=title,
            summary=summary,
            ai_hint=ai_hint,
            study_actions=study_actions,
            priority=priority,
            references=[]
        )

        query_time = (datetime.now() - start_time).total_seconds()

        return MindmapEditResponse(
            success=True,
            edited_node=edited_node,
            sources_used=sources_used,
            query_time=query_time,
            generation_method="ai_edit"
        )

    except Exception as e:
        print(f"Error in mindmap node edit: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to edit mindmap node: {str(e)}")

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
            "source_tracking": True,
            "node_editing": True
        },
        "max_expansions_per_request": 10,
        "supported_node_types": ["concept", "topic", "definition", "example"]
    }
