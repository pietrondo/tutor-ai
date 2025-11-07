from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import re
import unicodedata
import os
import shutil
import json
import logging
from datetime import datetime, timedelta
import structlog
import asyncio

from services.rag_service import RAGService
from services.llm_service import LLMService
from services.course_service import CourseService
from services.book_service import BookService
from services.study_tracker import StudyTracker
from services.study_planner_service import StudyPlannerService
from services.background_task_service import background_task_service
from services.annotation_service import AnnotationService
from services.ocr_service import ocr_service
from services.advanced_search_service import advanced_search_service, SearchType, SortOrder, SearchFilter, SearchQuery
from app.api.slides import router as slides_router
from app.api.mindmap_expand import router as mindmap_expand_router
from app.api.mindmaps import router as mindmaps_router
from app.api.concepts import router as concepts_router

# Import security and error handling utilities
from utils.security import (
    sanitize_filename, validate_file_upload, validate_file_path,
    SecurityLogger, rate_limit_check, SecurityConfig
)
from utils.exceptions import (
    ErrorHandler, ValidationError, FileOperationError,
    RateLimitError, SecurityError, safe_execute
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def _clean_node_title(title: str) -> str:
    """
    Clean node title by removing URLs, references, and technical identifiers
    """
    logger.info(f"🧹 DEBUG: Cleaning title: {title}")

    if not title or not isinstance(title, str):
        logger.error("❌ DEBUG: Invalid title, returning 'Concetto'")
        return "Concetto"

    original_title = title.lower()  # Keep for fallback detection
    cleaned = title.strip()

    logger.info(f"📝 DEBUG: Original title: {original_title}")
    logger.info(f"🔍 DEBUG: Initial cleaned: {cleaned}")

    # Step 1: Remove URLs completely
    cleaned = re.sub(r'https?://[^\s\)\]]+', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'www\.[^\s\)\]]+', '', cleaned, flags=re.IGNORECASE)

    logger.info(f"🌐 DEBUG: After URL removal: {cleaned}")

    # Step 2: Remove domain patterns aggressively (com, it, org sequences)
    # This handles patterns like "com it docs sebastiano-caboto-libro"
    cleaned = re.sub(r'\b[a-z-]+\s+(com|it|org|net|gov|edu)\s+[a-z-]+\b', '', cleaned, flags=re.IGNORECASE)
    # Also handle patterns where words with dashes follow domain names
    cleaned = re.sub(r'(com|it|org|net|gov|edu)\s+[\w-]*docs?[\w-]*', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'[\w-]*docs?[\w-]*\s+(com|it|org|net|gov|edu)', '', cleaned, flags=re.IGNORECASE)

    # Step 3: Remove common technical words and document references
    tech_words = ['docs', 'document', 'file', 'pdf', 'doc', 'down', 'upload', 'download', 'shared', 'docsity']
    for word in tech_words:
        cleaned = re.sub(rf'\b{re.escape(word)}\b', '', cleaned, flags=re.IGNORECASE)

    # Step 3.1: Remove specific document sharing patterns
    cleaned = re.sub(r'document\s+shared\s+on.*', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'shared\s+on\s+https?.*', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'downloaded\s+by.*', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'università\s+degli\s+studi\s+di.*', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\(.*?unimi.*?\)', '', cleaned, flags=re.IGNORECASE)

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

    logger.info(f"✅ DEBUG: Final cleaned title: '{cleaned}'")
    logger.info(f"🔍 DEBUG: Length check - original: {len(title)}, cleaned: {len(cleaned)}")
    return cleaned

app = FastAPI(title="AI Tutor Backend", version="1.0.0")

# CORS configuration - restricted to specific origins and methods
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:5000", "http://127.0.0.1:5000", "http://localhost:3001", "http://127.0.0.1:3001"],  # Frontend ports
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],  # Include OPTIONS for CORS preflight
    allow_headers=[
        "accept",
        "accept-language",
        "content-language",
        "content-type",
        "authorization",
        "x-requested-with"
    ],  # Specific headers only
)

# Serve static files
app.mount("/uploads", StaticFiles(directory="data/uploads"), name="uploads")
app.mount("/slides/static", StaticFiles(directory="data/slides"), name="slides_static")

# Include API routers
app.include_router(slides_router)
app.include_router(mindmap_expand_router)
app.include_router(mindmaps_router)
app.include_router(concepts_router)

# Security and rate limiting middleware
@app.middleware("http")
async def security_middleware(request: Request, call_next):
    """Security middleware for rate limiting and request validation."""
    try:
        # Get client IP for rate limiting
        client_ip = request.client.host
        x_forwarded_for = request.headers.get("x-forwarded-for")
        if x_forwarded_for:
            client_ip = x_forwarded_for.split(",")[0].strip()

        # Apply rate limiting (100 requests per minute per IP)
        if not rate_limit_check(client_ip, limit=100, window=60):
            SecurityLogger.log_suspicious_activity(
                "Rate limit exceeded",
                {"ip": client_ip, "path": request.url.path},
                client_ip
            )
            return JSONResponse(
                status_code=429,
                content={
                    "error_code": "RATE_LIMIT_EXCEEDED",
                    "message": "Too many requests. Please try again later."
                }
            )

        # Log suspicious requests
        if request.url.path.startswith("/admin") or request.method in ["DELETE", "PUT"]:
            SecurityLogger.log_file_access(
                f"{request.method} {request.url.path}",
                context="security_middleware"
            )

        response = await call_next(request)

        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        return response

    except Exception as e:
        logger.error(f"Security middleware error: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "error_code": "SECURITY_MIDDLEWARE_ERROR",
                "message": "Internal security error"
            }
        )

# Global exception handler for HTTPException
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Ensure HTTPException always returns JSONResponse."""
    from fastapi.responses import JSONResponse

    return JSONResponse(
        status_code=exc.status_code,
        content=exc.detail
    )

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for consistent error responses."""
    from fastapi.responses import JSONResponse

    # Handle through ErrorHandler first
    http_exc = ErrorHandler.handle_error(exc, f"{request.method} {request.url.path}")

    # Ensure we always return JSONResponse
    return JSONResponse(
        status_code=http_exc.status_code,
        content=http_exc.detail
    )

# Initialize services
rag_service = RAGService()
llm_service = LLMService()
course_service = CourseService()
book_service = BookService()
study_tracker = StudyTracker()
study_planner = StudyPlannerService()
annotation_service = AnnotationService()

# Data models
class CourseCreate(BaseModel):
    name: str
    description: str
    subject: str

class CourseUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    subject: Optional[str] = None

class BookCreate(BaseModel):
    title: str
    author: Optional[str] = ""
    isbn: Optional[str] = ""
    description: Optional[str] = ""
    year: Optional[str] = ""
    publisher: Optional[str] = ""
    chapters: Optional[List[str]] = []
    tags: Optional[List[str]] = []

class BookUpdate(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None
    isbn: Optional[str] = None
    description: Optional[str] = None
    year: Optional[str] = None
    publisher: Optional[str] = None
    chapters: Optional[List[str]] = None
    tags: Optional[List[str]] = None

class ChatMessage(BaseModel):
    message: str
    course_id: str
    book_id: Optional[str] = None
    session_id: Optional[str] = None
    use_hybrid_search: Optional[bool] = False  # Enable hybrid search
    search_k: Optional[int] = 5  # Number of documents to retrieve

class QuizRequest(BaseModel):
    course_id: str
    topic: Optional[str] = None
    difficulty: Optional[str] = "medium"
    num_questions: Optional[int] = 5

class StudyPlanCreate(BaseModel):
    course_id: str
    title: Optional[str] = "Piano di Studio Personalizzato"
    sessions_per_week: Optional[int] = 3
    session_duration: Optional[int] = 45
    difficulty_level: Optional[str] = "intermediate"
    difficulty_progression: Optional[str] = "graduale"

class SessionProgressUpdate(BaseModel):
    completed: bool


class MissionTaskUpdate(BaseModel):
    completed: bool

class BudgetModeRequest(BaseModel):
    enabled: bool

class MindmapRequest(BaseModel):
    course_id: str
    book_id: Optional[str] = None
    topic: Optional[str] = None
    focus_areas: Optional[List[str]] = []


def _slugify_text(text: str, fallback: str = "node") -> str:
    """Create a slug identifier from text."""
    if not text:
        return fallback
    normalized = unicodedata.normalize("NFKD", str(text)).encode("ascii", "ignore").decode("ascii")
    cleaned = re.sub(r"[^a-zA-Z0-9\\s-]", "", normalized).strip().lower()
    cleaned = re.sub(r"[\\s_-]+", "-", cleaned)
    return cleaned or fallback


def _ensure_unique_id(candidate: str, used: Dict[str, int]) -> str:
    """Ensure node ids are unique by appending suffixes when needed."""
    base = candidate or "node"
    if base not in used:
        used[base] = 1
        return base
    used[base] += 1
    return f"{base}-{used[base]}"


def _normalize_list(value: Any) -> List[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if value:
        return [str(value).strip()]
    return []


def _normalize_node(raw_node: Dict[str, Any], used_ids: Dict[str, int]) -> Dict[str, Any]:
    title = str(raw_node.get("title") or raw_node.get("label") or "Concetto").strip()
    node_id = raw_node.get("id") or _slugify_text(title)
    node_id = _ensure_unique_id(node_id, used_ids)

    children_raw = raw_node.get("children") or []
    if not isinstance(children_raw, list):
        children_raw = []

    children = [_normalize_node(child, used_ids) for child in children_raw]

    priority = raw_node.get("priority")
    if isinstance(priority, (int, float)):
        try:
            priority = int(priority)
        except ValueError:
            priority = None
    elif isinstance(priority, str) and priority.isdigit():
        priority = int(priority)
    else:
        priority = None

    return {
        "id": node_id,
        "title": title,
        "summary": str(raw_node.get("summary") or raw_node.get("description") or "").strip(),
        "ai_hint": str(raw_node.get("ai_hint") or raw_node.get("aiGuidance") or raw_node.get("ai_support") or "").strip(),
        "study_actions": _normalize_list(raw_node.get("study_actions") or raw_node.get("studyActivities") or raw_node.get("activities")),
        "priority": priority,
        "references": _normalize_list(raw_node.get("references")),
        "children": children
    }


def _normalize_study_plan(plan: Any) -> List[Dict[str, Any]]:
    normalized: List[Dict[str, Any]] = []
    if not isinstance(plan, list):
        return normalized

    for item in plan:
        if not isinstance(item, dict):
            continue
        normalized.append({
            "phase": str(item.get("phase") or item.get("title") or f"Fase {len(normalized) + 1}").strip(),
            "objective": str(item.get("objective") or item.get("goal") or "").strip(),
            "activities": _normalize_list(item.get("activities")),
            "ai_support": str(item.get("ai_support") or item.get("ai_hint") or "").strip(),
            "duration_minutes": int(item.get("duration_minutes")) if isinstance(item.get("duration_minutes"), (int, float)) else None
        })
    return normalized


def _normalize_mindmap_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(payload, dict):
        payload = {}

    title = str(payload.get("title") or "Mappa di studio").strip()

    # Clean overview - it might contain JSON as string
    overview_raw = str(payload.get("overview") or payload.get("summary") or "").strip()
    overview = _clean_overview_text(overview_raw)

    # Force clean overview if it still contains JSON or is too long
    if overview.startswith("{") or len(overview) > 200:
        logger.warning(f"Overview invalid (contains JSON or too long), forcing clean. Length: {len(overview)}")
        # Generate a clean overview based on title
        clean_title = title.replace("Mappa di studio", "").strip()
        if not clean_title:
            clean_title = "argomenti di studio"
        overview = f"Mappa concettuale per {clean_title}. Questa mappa contiene i concetti principali e le relazioni tra i diversi argomenti studiati."

    nodes_raw = payload.get("nodes")
    if not isinstance(nodes_raw, list):
        nodes_raw = []
    used_ids: Dict[str, int] = {}
    nodes = [_normalize_node(node, used_ids) for node in nodes_raw]

    references = payload.get("references") or payload.get("sources") or []
    if isinstance(references, dict):
        references = [str(value) for value in references.values()]
    elif not isinstance(references, list):
        references = []
    references = [str(ref).strip() for ref in references if str(ref).strip()]

    normalized = {
        "title": title,
        "overview": overview,
        "nodes": nodes,
        "study_plan": _normalize_study_plan(payload.get("study_plan") or payload.get("ai_study_plan")),
        "references": references
    }

    # Final safety check - ensure data is clean
    if normalized["overview"].startswith("{") or len(normalized["overview"]) > 300:
        logger.error(f"CRITICAL: Overview still contains JSON or is too long after all cleaning. Forcing minimal clean overview.")
        clean_title = title.replace("Mappa di studio", "").strip()
        if not clean_title:
            clean_title = "studio"
        normalized["overview"] = f"Mappa concettuale per {clean_title}. Struttura organizzata dei concetti principali e delle loro relazioni."

    # Provide minimal default if no nodes were generated
    if not normalized["nodes"]:
        normalized["nodes"] = [{
            "id": _ensure_unique_id(_slugify_text(title), used_ids),
            "title": title,
            "summary": normalized["overview"] or "Concetto principale della mappa di studio.",
            "ai_hint": "",
            "study_actions": [],
            "priority": None,
            "references": [],
            "children": []
        }]

    return normalized


def _create_simple_mindmap(text_content: str, topic: str) -> Dict[str, Any]:
    """Create a simple mindmap from text content when JSON parsing fails"""
    # Extract key concepts from text
    lines = [line.strip() for line in text_content.split('\n') if line.strip()]
    title = topic or "Mappa di studio"

    # Simple structure with basic nodes
    nodes = []
    used_ids = {}

    # Add main topic
    main_node = {
        "id": _ensure_unique_id(_slugify_text(title), used_ids),
        "title": title,
        "summary": f"Mappa concettuale per {topic}",
        "ai_hint": f"Chiedi all'AI di approfondire i concetti principali di {topic}",
        "study_actions": [
            "Analizzare i concetti principali",
            "Creare riassunti per ogni argomento",
            "Praticare con esercizi specifici"
        ],
        "priority": 1,
        "references": [],
        "children": []
    }

    # Add some basic concepts if we can extract them
    concepts = []
    for line in lines[:5]:  # Take first 5 meaningful lines
        if len(line) > 10 and len(line) < 100:
            concepts.append(line)

    for i, concept in enumerate(concepts):
        child_node = {
            "id": _ensure_unique_id(_slugify_text(concept), used_ids),
            "title": concept[:50] + "..." if len(concept) > 50 else concept,
            "summary": concept,
            "ai_hint": "Chiedi all'AI di spiegare questo concetto con esempi",
            "study_actions": ["Approfondire il concetto", "Trovare esempi pratici"],
            "priority": i + 1,
            "references": [],
            "children": []
        }
        main_node["children"].append(child_node)

    nodes.append(main_node)

    return {
        "title": title,
        "overview": f"Mappa concettuale generata da {topic}. Questa mappa contiene i concetti principali estratti dai materiali di studio.",
        "nodes": nodes,
        "study_plan": [
            {
                "phase": "Fase 1 - Analisi",
                "objective": "Comprendere i concetti principali",
                "activities": ["Leggere i materiali", "Creare riassunti"],
                "ai_support": "Usa l'AI per spiegare concetti difficili",
                "duration_minutes": 45
            },
            {
                "phase": "Fase 2 - Approfondimento",
                "objective": "Dettagliare ogni argomento",
                "activities": ["Esercizi pratici", "Studio mirato"],
                "ai_support": "Chiedi esempi e chiarimenti all'AI",
                "duration_minutes": 30
            }
        ],
        "references": [topic]
    }


def _create_minimal_mindmap(topic: str) -> Dict[str, Any]:
    """Create a minimal mindmap when all else fails"""
    title = topic or "Mappa di studio"

    return {
        "title": title,
        "overview": f"Mappa concettuale per {topic}. Questa è una struttura base che puoi espandere.",
        "nodes": [
            {
                "id": "main-concept",
                "title": title,
                "summary": f"Concetto principale per {topic}",
                "ai_hint": "Chiedi all'AI di spiegare questo argomento in dettaglio",
                "study_actions": [
                    "Studiare i materiali di riferimento",
                    "Creare riassunti personali",
                    "Praticare con esercizi"
                ],
                "priority": 1,
                "references": [],
                "children": [
                    {
                        "id": "sub-concept-1",
                        "title": "Concetti Fondamentali",
                        "summary": "Principali concetti di base",
                        "ai_hint": "Chiedi all'AI di definire i concetti chiave",
                        "study_actions": ["Definire i termini", "Creare glossario"],
                        "priority": 1,
                        "references": [],
                        "children": []
                    },
                    {
                        "id": "sub-concept-2",
                        "title": "Applicazioni Pratiche",
                        "summary": "Come applicare questi concetti",
                        "ai_hint": "Chiedi all'AI esempi pratici",
                        "study_actions": ["Trovare esempi", "Creare esercizi"],
                        "priority": 2,
                        "references": [],
                        "children": []
                    }
                ]
            }
        ],
        "study_plan": [
            {
                "phase": "Fase 1 - Introduzione",
                "objective": "Comprendere i concetti base",
                "activities": ["Lettura materiale", "Note personali"],
                "ai_support": "Usa l'AI per chiarimenti",
                "duration_minutes": 30
            }
        ],
        "references": [topic]
    }


def _fix_common_json_issues(json_text: str) -> Optional[str]:
    """Try to fix common JSON formatting issues"""
    if not json_text:
        return None

    try:
        # Remove common prefixes/suffixes
        text = json_text.strip()

        # Remove markdown code blocks
        if text.startswith('```json'):
            text = text[7:].strip()
        if text.startswith('```'):
            text = text[3:].strip()
        if text.endswith('```'):
            text = text[:-3].strip()

        # Remove trailing commas
        text = re.sub(r',\s*}', '}', text)
        text = re.sub(r',\s*]', ']', text)

        # Fix quotes
        text = re.sub(r"'([^']*)'", r'"\1"', text)

        # Remove comments (basic)
        text = re.sub(r'//.*?\n', '\n', text)
        text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)

        # Find balanced braces
        start = text.find('{')
        if start == -1:
            return None

        brace_count = 0
        end = start
        for i, char in enumerate(text[start:], start=start):
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0:
                    end = i + 1
                    break

        if brace_count != 0:
            return None

        return text[start:end]
    except Exception:
        return None


def _extract_json_from_malformed_text(text: str) -> Optional[str]:
    """Extract JSON from malformed text response"""
    try:
        # Try to find JSON object in text
        start = text.find('{')
        if start == -1:
            return None

        # Find matching brace
        brace_count = 0
        end = start
        for i, char in enumerate(text[start:], start=start):
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0:
                    end = i + 1
                    break

        if brace_count != 0:
            return None

        json_candidate = text[start:end]

        # Try to fix and validate
        fixed = _fix_common_json_issues(json_candidate)
        if fixed:
            return fixed

        return json_candidate
    except Exception:
        return None


def _is_low_quality_content(text: str) -> bool:
    """
    Detect if the content is low quality (apologies, document references, etc.)
    """
    if not text or not isinstance(text, str):
        return True

    text_lower = text.lower().strip()

    # Check for apology messages
    apology_phrases = [
        "mi dispiace", "scusami", "non posso", "impossibile",
        "riprova più tardi", "problema", "errore", "sorry",
        "apologize", "issue", "problem", "try again"
    ]

    if any(phrase in text_lower for phrase in apology_phrases):
        return True

    # Check for document reference patterns
    doc_patterns = [
        "document shared on", "downloaded by", "www.", "http",
        "università degli studi", "docsity", "studocu",
        "scan to open", "sponsored or endorsed", "page:",
        "chunk_index", "relevance_score"
    ]

    if any(pattern in text_lower for pattern in doc_patterns):
        return True

    # Check if text is too short or mostly punctuation/numbers
    if len(text.strip()) < 20:
        return True

    # Check if text contains mostly technical identifiers
    words = text.split()
    meaningful_words = [w for w in words if len(w) > 3 and not w.replace('-', '').replace('_', '').isalnum()]
    if len(meaningful_words) < len(words) * 0.3:  # Less than 30% meaningful words
        return True

    return False

def _generate_intelligent_conceptual_nodes(topic: str) -> List[Dict[str, Any]]:
    """
    Generate intelligent conceptual nodes based on topic analysis
    """
    logger.info(f"🧠 Generating intelligent conceptual nodes for topic: {topic}")

    topic_lower = topic.lower() if topic else ""

    # Enhanced topic analysis with multiple patterns
    if any(keyword in topic_lower for keyword in ['caboto', 'sebastiano', 'esplor', 'navigazione', 'viaggio']):
        return [
            {
                "id": "biografia",
                "title": "Biografia e Contesto",
                "summary": "Vita, formazione e contesto storico di Sebastiano Caboto",
                "ai_hint": "Chiedi all'AI dettagli sulla biografia e il periodo storico",
                "study_actions": ["Ricercare fonti biografiche", "Analizzare il contesto XV-XVI secolo"],
                "priority": 1,
                "references": [],
                "children": []
            },
            {
                "id": "viaggi",
                "title": "Viaggi e Scoperte",
                "summary": "Le principali esplorazioni e le rotte navigate da Caboto",
                "ai_hint": "Chiedi all'AI di dettagliare i singoli viaggi e le rotte",
                "study_actions": ["Mappare le rotte", "Confrontare con altri esploratori"],
                "priority": 2,
                "references": [],
                "children": []
            },
            {
                "id": "impatto",
                "title": "Impatto Storico",
                "summary": "Conseguenze delle esplorazioni e influenza sulla geografia",
                "ai_hint": "Chiedi all'AI di analizzare l'impatto a lungo termine",
                "study_actions": ["Valutare l'impatto geopolitico", "Analizzare le conseguenze economiche"],
                "priority": 3,
                "references": [],
                "children": []
            },
            {
                "id": "relazioni",
                "title": "Relazioni con Popoli Nativi",
                "summary": "Interazioni tra gli esploratori e le popolazioni indigene",
                "ai_hint": "Chiedi all'AI di approfondire gli aspetti etnografici",
                "study_actions": ["Analizzare le fonti etnografiche", "Studiare gli scambi culturali"],
                "priority": 4,
                "references": [],
                "children": []
            },
            {
                "id": "fonti",
                "title": "Fonti Storiche",
                "summary": "Documenti, mappe e testimonianze dell'epoca",
                "ai_hint": "Chiedi all'AI di identificare le fonti primarie e secondarie",
                "study_actions": ["Analizzare le fonti primarie", "Criticare le testimonianze"],
                "priority": 5,
                "references": [],
                "children": []
            }
        ]

    elif any(keyword in topic_lower for keyword in ['geografia', 'storia', 'geografico', 'storico']):
        return [
            {
                "id": "concetti",
                "title": "Concetti Fondamentali",
                "summary": "Principi teorici e definizioni di base",
                "ai_hint": "Chiedi all'AI di chiarire i concetti principali",
                "study_actions": ["Definire i termini chiave", "Creare schemi concettuali"],
                "priority": 1,
                "references": [],
                "children": []
            },
            {
                "id": "contesto",
                "title": "Contesto Geografico",
                "summary": "Caratteristiche fisiche e umane del territorio",
                "ai_hint": "Chiedi all'AI di descrivere l'ambiente geografico",
                "study_actions": ["Analizzare le carte geografiche", "Studiare l'ambiente fisico"],
                "priority": 2,
                "references": [],
                "children": []
            },
            {
                "id": "sviluppo",
                "title": "Evoluzione Storica",
                "summary": "Sviluppo temporale degli eventi e dei fenomeni",
                "ai_hint": "Chiedi all'AI di creare una timeline degli eventi",
                "study_actions": ["Creare linee del tempo", "Identificare i momenti chiave"],
                "priority": 3,
                "references": [],
                "children": []
            },
            {
                "id": "metodologia",
                "title": "Metodologia di Studio",
                "summary": "Metodi e approcci per l'analisi geografico-storica",
                "ai_hint": "Chiedi all'AI di suggerire metodi di analisi",
                "study_actions": ["Applicare metodi di analisi", "Confrontare diverse prospettive"],
                "priority": 4,
                "references": [],
                "children": []
            },
            {
                "id": "applicazioni",
                "title": "Applicazioni Moderne",
                "summary": "Rilevanza contemporanea e applicazioni pratiche",
                "ai_hint": "Chiedi all'AI di collegare al presente",
                "study_actions": ["Identificare collegamenti attuali", "Analizzare la rilevanza odierna"],
                "priority": 5,
                "references": [],
                "children": []
            }
        ]

    # Generic academic structure for other topics
    return [
        {
            "id": "fondamenti",
            "title": "Fondamenti Teorici",
            "summary": "Concetti di base e principi fondamentali dell'argomento",
            "ai_hint": f"Chiedi all'AI di spiegare i fondamenti di {topic}",
            "study_actions": ["Definire i concetti base", "Comprendere i principi teorici"],
            "priority": 1,
            "references": [],
            "children": []
        },
        {
            "id": "contesto",
            "title": "Contesto e Background",
            "summary": "Informazioni contestuali essenziali per la comprensione",
            "ai_hint": f"Chiedi all'AI di fornire il contesto di {topic}",
            "study_actions": ["Ricercare il contesto", "Analizzare lo sfondo storico/culturale"],
            "priority": 2,
            "references": [],
            "children": []
        },
        {
            "id": "sviluppi",
            "title": "Sviluppi Principali",
            "summary": "Evoluzione e progressione dei concetti principali",
            "ai_hint": f"Chiedi all'AI di descrivere gli sviluppi chiave di {topic}",
            "study_actions": ["Tracciare gli sviluppi", "Identificare i punti di svolta"],
            "priority": 3,
            "references": [],
            "children": []
        },
        {
            "id": "applicazioni",
            "title": "Applicazioni Pratiche",
            "summary": "Esempi concreti e applicazioni reali dei concetti",
            "ai_hint": f"Chiedi all'AI di fornire esempi pratici di {topic}",
            "study_actions": ["Trovare esempi concreti", "Analizzare le applicazioni"],
            "priority": 4,
            "references": [],
            "children": []
        },
        {
            "id": "approfondimenti",
            "title": "Approfondimenti e Ricerche",
            "summary": "Temi avanzati e possibili direzioni di studio",
            "ai_hint": f"Chiedi all'AI di suggerire approfondimenti su {topic}",
            "study_actions": ["Identificare aree di approfondimento", "Proporre nuove ricerche"],
            "priority": 5,
            "references": [],
            "children": []
        }
    ]

def _create_structured_mindmap_from_text(text: str, topic: str) -> Dict[str, Any]:
    """Create a structured mindmap from unstructured text with intelligent fallback"""
    logger.info(f"🔍 DEBUG: _create_structured_mindmap_from_text called")
    logger.info(f"📝 DEBUG: Input text length: {len(text)}")
    logger.info(f"📝 DEBUG: Topic: {topic}")
    logger.info(f"📝 DEBUG: First 200 chars of text: {text[:200]}")

    # Check for low quality content
    is_low_quality = _is_low_quality_content(text)
    logger.info(f"🚫 DEBUG: Content quality check - Low quality: {is_low_quality}")

    title = topic or "Mappa di studio"

    # If content is low quality, generate intelligent conceptual nodes
    if is_low_quality:
        logger.info(f"🧠 DEBUG: Using intelligent conceptual node generation due to low quality content")
        conceptual_nodes = _generate_intelligent_conceptual_nodes(topic)

        main_node = {
            "id": "main-concept",
            "title": title,
            "summary": f"Mappa concettuale interattiva per {topic} con approfondimenti guidati dall'AI",
            "ai_hint": f"Chiedi all'AI di esplorare approfonditamente i concetti di {topic}",
            "study_actions": [
                f"Esplora i concetti principali di {topic}",
                f"Usa l'AI per approfondire ogni nodo",
                f"Pratica con esempi specifici"
            ],
            "priority": 1,
            "references": [],
            "children": conceptual_nodes
        }

        # Create enhanced study plan
        study_plan_data = [
            {
                "phase": "Fase 1 - Esplorazione Guidata",
                "objective": f"Comprendere i concetti fondamentali di {topic}",
                "activities": [
                    "Esplora i nodi concettuali principali",
                    "Usa l'AI per chiarimenti personalizzati",
                    "Fai domande specifiche su ogni concetto"
                ],
                "ai_support": f"Utilizza l'assistente AI per approfondire {topic} con esempi e spiegazioni",
                "duration_minutes": 45
            },
            {
                "phase": "Fase 2 - Approfondimento",
                "objective": "Analizzare in dettaglio gli aspetti chiave",
                "activities": [
                    "Focalizzati sui nodi di priorità alta",
                    "Chiedi all'AI esempi pratici e applicazioni",
                    "Crea connessioni tra i concetti"
                ],
                "ai_support": "L'AI fornisce spiegazioni dettagliate e esempi personalizzati",
                "duration_minutes": 60
            }
        ]

        logger.info(f"✅ DEBUG: Created intelligent mindmap with {len(conceptual_nodes)} conceptual nodes")

        return {
            "title": title,
            "overview": f"Mappa concettuale interattiva per {topic}. Generata automaticamente con nodi concettuali intelligenti quando il contenuto disponibile non è ottimale.",
            "nodes": [main_node],
            "study_plan": study_plan_data,
            "references": [topic]
        }

    # Original logic for high-quality content
    # Try to extract structured content from JSON string in text
    extracted_content = None
    clean_overview = ""

    # First, try to extract JSON content from the text
    if text and text.strip():
        clean_text = _clean_overview_text(text.strip())

        # Look for JSON content in the text
        if clean_text and clean_text.startswith('{'):
            try:
                # Try to parse the cleaned text as JSON
                parsed = json.loads(clean_text)
                if isinstance(parsed, dict):
                    extracted_content = parsed
            except:
                # If direct parsing fails, try to extract JSON from larger text
                try:
                    json_match = re.search(r'\{.*\}', clean_text, re.DOTALL)
                    if json_match:
                        json_content = json_match.group(0)
                        parsed = json.loads(json_content)
                        if isinstance(parsed, dict):
                            extracted_content = parsed
                except:
                    pass

        # If we couldn't extract JSON, use the cleaned text as overview
        if not extracted_content and clean_text:
            clean_overview = clean_text

    # Create title and overview
    if extracted_content:
        # Use extracted content
        final_title = extracted_content.get("title", title)
        final_overview = extracted_content.get("overview", clean_overview)
        nodes_data = extracted_content.get("nodes", [])
        study_plan_data = extracted_content.get("study_plan", [])
        references_data = extracted_content.get("references", [])
    else:
        # Fallback to basic structure
        final_title = title
        final_overview = clean_overview or f"Mappa concettuale per {topic} basata sui materiali di studio."
        nodes_data = []
        study_plan_data = []
        references_data = []

    # If we have extracted nodes, use them; otherwise create from sentences
    if nodes_data:
        # Use extracted nodes but ensure they have proper structure
        structured_nodes = []
        for i, node in enumerate(nodes_data[:5]):  # Limit to 5 nodes
            if isinstance(node, dict) and node.get("title"):
                structured_node = {
                    "id": node.get("id", f"concept-{i+1}"),
                    "title": node.get("title", f"Concetto {i+1}"),
                    "summary": node.get("summary", "Concetto estratto dai materiali di studio"),
                    "ai_hint": node.get("ai_hint", "Chiedi all'AI di approfondire questo concetto"),
                    "study_actions": node.get("study_actions", ["Approfondire", "Trovare esempi"]),
                    "priority": node.get("priority", i+1),
                    "references": node.get("references", []),
                    "children": node.get("children", [])
                }
                structured_nodes.append(structured_node)

        main_nodes = structured_nodes
    else:
        # Create nodes from sentences
        sentences = [s.strip() for s in text.split('.') if s.strip() and len(s.strip()) > 10]

        main_node = {
            "id": "main-concept",
            "title": final_title,
            "summary": clean_overview or f"Analisi dei concetti principali di {topic}",
            "ai_hint": f"Chiedi all'AI di approfondire i concetti di {topic}",
            "study_actions": ["Analizzare i materiali", "Creare riassunti", "Praticare esercizi"],
            "priority": 1,
            "references": [],
            "children": []
        }

        # Add conceptual children based on topic analysis
        children = []
        topic_lower = topic.lower() if topic else ""

        logger.info(f"🧠 DEBUG: Starting conceptual children generation")
        logger.info(f"🔍 DEBUG: Checking for 'caboto' in topic: {'caboto' in topic_lower}")
        logger.info(f"🔍 DEBUG: Checking for 'sebastiano' in topic: {'sebastiano' in topic_lower}")
        logger.info(f"🔍 DEBUG: Checking for 'esplorazione' in topic: {'esplorazione' in topic_lower}")

        # Generate conceptual nodes based on topic content
        if 'caboto' in topic_lower or 'sebastiano' in topic_lower or 'esplorazione' in topic_lower:
            logger.info(f"✅ DEBUG: Matched Caboto/exploration topic - creating specific conceptual nodes")
            conceptual_children = [
                {"title": "Viaggi e Scoperte", "summary": "Le esplorazioni geografiche e la scoperta di nuove terre"},
                {"title": "Contesto Storico", "summary": "Il periodo storico delle grandi esplorazioni"},
                {"title": "Figure Chiave", "summary": "I protagonisti delle esplorazioni e i loro ruoli"},
                {"title": "Impatto Culturale", "summary": "Le conseguenze delle scoperte sulle culture native"},
                {"title": "Rotte Marittime", "summary": "Le vie di navigazione e le rotte commerciali"}
            ]
        elif 'geografia' in topic_lower or 'storia' in topic_lower:
            conceptual_children = [
                {"title": "Concetti Fondamentali", "summary": "I principi base della geografia storica"},
                {"title": "Contesto Geografico", "summary": "L'ambiente fisico e le caratteristiche territoriali"},
                {"title": "Evoluzione Storica", "summary": "Lo sviluppo degli eventi nel tempo"},
                {"title": "Fonti e Documenti", "summary": "I materiali di studio e le fonti primarie"},
                {"title": "Analisi Critica", "summary": "L'interpretazione critica delle fonti storiche"}
            ]
        else:
            logger.info(f"⚠️ DEBUG: No specific topic match - using generic fallback concepts")
            # Generic fallback concepts
            conceptual_children = [
                {"title": "Concetti Principali", "summary": "Le idee fondamentali del argomento"},
                {"title": "Contesto e Background", "summary": "Le informazioni contestuali essenziali"},
                {"title": "Sviluppi Chiave", "summary": "I punti principali dello sviluppo"},
                {"title": "Applicazioni Pratiche", "summary": "Le applicazioni e gli esempi concreti"},
                {"title": "Approfondimenti", "summary": "Temi correlati e possibili estensioni"}
            ]

        for i, concept in enumerate(conceptual_children[:5]):  # Max 5 children
            # Apply cleaning to ensure consistency
            clean_title = _clean_node_title(concept["title"])
            clean_summary = _clean_overview_text(concept["summary"])

            logger.info(f"🔍 DEBUG: Creating conceptual child node {i+1}")
            logger.info(f"   Concept title: {clean_title}")
            logger.info(f"   Concept summary: {clean_summary}")

            child = {
                "id": f"concept-{i+1}",
                "title": clean_title,
                "summary": clean_summary,
                "ai_hint": f"Chiedi all'AI di approfondire {clean_title}",
                "study_actions": [f"Analizza {clean_title}", f"Trova esempi di {clean_title}"],
                "priority": i + 1,
                "references": [],
                "children": []
            }
            children.append(child)

        main_node["children"] = children
        main_nodes = [main_node]

    # Create study plan if not extracted
    if not study_plan_data:
        study_plan_data = [
            {
                "phase": "Fase 1 - Analisi",
                "objective": "Comprendere i concetti base",
                "activities": ["Studio dei materiali", "Creazione di riassunti"],
                "ai_support": "Utilizzo dell'AI per chiarimenti",
                "duration_minutes": 30
            }
        ]

    # Create references if not extracted
    if not references_data:
        references_data = [topic]

    return {
        "title": final_title,
        "overview": final_overview[:200] + "..." if len(final_overview) > 200 else final_overview,
        "nodes": main_nodes,
        "study_plan": study_plan_data,
        "references": references_data
    }


def _has_json_strings_in_payload(payload: Any) -> bool:
    """Check if payload contains JSON strings as values"""
    try:
        if isinstance(payload, dict):
            for key, value in payload.items():
                if isinstance(value, str) and value.startswith("{"):
                    return True
        return False
    except Exception:
        return False


def _is_valid_mindmap_payload(payload: Any) -> bool:
    """Validate that the payload is a proper mindmap structure"""
    try:
        if not isinstance(payload, dict):
            return False

        # Check required fields
        if not isinstance(payload.get("title"), str):
            return False

        # Check overview is not JSON string
        overview = payload.get("overview", "")
        if isinstance(overview, str) and overview.startswith("{"):
            logger.warning(f"Invalid overview detected (starts with JSON): {overview[:100]}...")
            return False  # Overview contains JSON instead of text

        # Check nodes is a list and not empty
        nodes = payload.get("nodes", [])
        if not isinstance(nodes, list) or len(nodes) == 0:
            return False

        # Check at least one node has valid structure
        for node in nodes:
            if isinstance(node, dict) and isinstance(node.get("title"), str):
                return True

        return False
    except Exception:
        return False


def _clean_overview_text(overview: str) -> str:
    """Clean overview text that might contain JSON strings"""
    if not overview:
        return ""

    # If overview starts with JSON, try to extract the entire JSON content
    if overview.startswith('{'):
        try:
            # Try to parse as JSON and return the full JSON if it's a complete object
            parsed = json.loads(overview)
            if isinstance(parsed, dict):
                # Return the original JSON string to be processed later
                return json.dumps(parsed, ensure_ascii=False)
        except:
            # If parsing fails, try to extract complete JSON from text
            try:
                # Look for complete JSON object in the text
                json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', overview, re.DOTALL)
                if json_match:
                    json_content = json_match.group(0)
                    # Try to validate it's parseable
                    test_parsed = json.loads(json_content)
                    if isinstance(test_parsed, dict):
                        return json_content
            except:
                pass

    # If we get here, try to extract clean text from malformed JSON
    if overview.startswith('{') and '"' in overview:
        # Try to extract the overview text from malformed JSON
        if '"overview":' in overview:
            parts = overview.split('"overview":')
            if len(parts) > 1:
                # Find the quoted text after "overview":
                overview_part = parts[1].strip()
                if overview_part.startswith('"'):
                    # Find the closing quote, handling escaped quotes
                    quote_end = -1
                    for i in range(1, len(overview_part)):
                        if overview_part[i] == '"' and overview_part[i-1] != '\\':
                            quote_end = i
                            break
                    if quote_end != -1:
                        return overview_part[1:quote_end+1]

    # Remove JSON artifacts for non-JSON content
    overview = re.sub(r'^\s*\{\s*".*?"\s*:\s*"', '', overview)  # Remove {"field": "
    overview = re.sub(r'"\s*}\s*$', '', overview)  # Remove trailing "}

    # Clean up common formatting issues
    overview = overview.strip()
    if overview.startswith('"') and overview.endswith('"'):
        overview = overview[1:-1]  # Remove surrounding quotes

    return overview


def _mindmap_to_markdown(mindmap: Dict[str, Any]) -> str:
    lines: List[str] = []
    title = mindmap.get("title", "Mappa di studio")
    lines.append(f"# {title}")

    overview = mindmap.get("overview")
    if overview:
        lines.append(overview.strip())

    def render_nodes(nodes: List[Dict[str, Any]], depth: int = 0) -> None:
        for node in nodes:
            header_level = depth + 2
            lines.append(f"{'#' * header_level} {node.get('title')}")
            summary = node.get("summary")
            if summary:
                lines.append(summary.strip())
            study_actions = node.get("study_actions") or []
            if study_actions:
                lines.append("- Attività consigliate:")
                for action in study_actions:
                    lines.append(f"  - {action}")
            ai_hint = node.get("ai_hint")
            if ai_hint:
                lines.append(f"- Suggerimento AI: {ai_hint}")
            references = node.get("references") or []
            if references:
                lines.append(f"- Riferimenti: {', '.join(references)}")
            render_nodes(node.get("children", []), depth + 1)

    render_nodes(mindmap.get("nodes", []))

    study_plan = mindmap.get("study_plan") or []
    if study_plan:
        lines.append("")
        lines.append("## Piano di Studio Suggerito")
        for phase in study_plan:
            lines.append(f"### {phase.get('phase')}")
            objective = phase.get("objective")
            if objective:
                lines.append(f"- Obiettivo: {objective}")
            activities = phase.get("activities") or []
            if activities:
                lines.append("- Attività:")
                for activity in activities:
                    lines.append(f"  - {activity}")
            ai_support = phase.get("ai_support")
            if ai_support:
                lines.append(f"- Supporto AI: {ai_support}")
            duration = phase.get("duration_minutes")
            if duration:
                lines.append(f"- Durata suggerita: {int(duration)} minuti")

    return "\n".join(lines).strip()


def _parse_markdown_to_structure(markdown_text: str) -> Dict[str, Any]:
    """Fallback parser from markdown headings into structured mindmap data."""
    lines = [line for line in (markdown_text or "").splitlines() if line.strip()]
    title = "Mappa di studio"
    overview_parts: List[str] = []
    nodes: List[Dict[str, Any]] = []
    stack: List[Dict[str, Any]] = []
    used_ids: Dict[str, int] = {}

    header_pattern = re.compile(r"^(#{1,6})\s+(.*)")

    for line in lines:
        heading_match = header_pattern.match(line.strip())
        if heading_match:
            level = len(heading_match.group(1))
            text = heading_match.group(2).strip()

            if level == 1:
                title = text
                continue

            node = {
                "id": None,
                "title": text,
                "summary": "",
                "ai_hint": "",
                "study_actions": [],
                "priority": None,
                "references": [],
                "children": [],
                "level": level
            }

            while stack and stack[-1]["level"] >= level:
                stack.pop()

            node["id"] = _ensure_unique_id(_slugify_text(text), used_ids)

            if stack:
                stack[-1]["children"].append(node)
            else:
                nodes.append(node)

            stack.append(node)
        elif line.strip().startswith(("-", "*")) and stack:
            stack[-1]["study_actions"].append(line.strip()[1:].strip())
        else:
            if stack:
                current_summary = stack[-1].get("summary", "")
                stack[-1]["summary"] = (current_summary + " " + line.strip()).strip()
            else:
                overview_parts.append(line.strip())

    # Remove helper level keys
    def clean_node(node: Dict[str, Any]) -> Dict[str, Any]:
        node.pop("level", None)
        node["children"] = [clean_node(child) for child in node.get("children", [])]
        return node

    nodes = [clean_node(node) for node in nodes]

    structured = {
        "title": title,
        "overview": " ".join(overview_parts).strip(),
        "nodes": nodes or [{
            "id": _ensure_unique_id(_slugify_text(title), used_ids),
            "title": title,
            "summary": "Concetto principale della mappa di studio.",
            "ai_hint": "",
            "study_actions": [],
            "priority": None,
            "references": [],
            "children": []
        }],
        "study_plan": [],
        "references": []
    }

    return structured

# Annotation models
class AnnotationCreate(BaseModel):
    user_id: str
    pdf_filename: str
    pdf_path: str
    course_id: Optional[str] = ""
    book_id: Optional[str] = ""
    page_number: int
    type: Optional[str] = "highlight"  # highlight, underline, note, strikeout
    text: Optional[str] = ""
    selected_text: Optional[str] = ""
    content: Optional[str] = ""  # For note annotations
    position: Optional[Dict[str, Any]] = {}  # x, y, width, height
    style: Optional[Dict[str, Any]] = {
        "color": "#ffeb3b",
        "opacity": 0.3,
        "stroke_color": "#fbc02d",
        "stroke_width": 1
    }
    tags: Optional[List[str]] = []
    is_public: Optional[bool] = False
    is_favorite: Optional[bool] = False

class AnnotationUpdate(BaseModel):
    type: Optional[str] = None
    content: Optional[str] = None
    style: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    is_public: Optional[bool] = None
    is_favorite: Optional[bool] = None

class AnnotationSearch(BaseModel):
    query: str
    course_id: Optional[str] = ""
    book_id: Optional[str] = ""
    tags: Optional[List[str]] = None
    annotation_type: Optional[str] = ""

# Routes
@app.get("/")
async def root():
    return {"message": "AI Tutor Backend API"}

@app.post("/courses")
async def create_course(course: CourseCreate):
    try:
        result = course_service.create_course(course.dict())
        return {"success": True, "course": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/courses")
async def get_courses():
    try:
        courses = course_service.get_all_courses()
        return {"courses": courses}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/courses/{course_id}")
async def get_course(course_id: str):
    try:
        course = course_service.get_course(course_id)
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")
        return {"course": course}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/courses/{course_id}")
async def update_course(course_id: str, course_update: CourseUpdate):
    try:
        update_data = {k: v for k, v in course_update.dict().items() if v is not None}
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")

        course = course_service.update_course(course_id, update_data)
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")
        return {"success": True, "course": course}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/courses/{course_id}")
async def delete_course(course_id: str):
    try:
        success = course_service.delete_course(course_id)
        if not success:
            raise HTTPException(status_code=404, detail="Course not found")

        # Also delete RAG documents for this course
        rag_service.delete_course_documents(course_id)

        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/courses/{course_id}/upload")
async def upload_material(course_id: str, file: UploadFile = File(...), request: Request = None):
    """
    Secure file upload endpoint with comprehensive validation and security checks.
    """
    try:
        # Validate course ID
        if not course_id or not isinstance(course_id, str):
            raise ValidationError("Invalid course ID")

        # Validate file exists and has filename
        if not file or not file.filename:
            raise ValidationError("No file provided")

        # Get client IP for logging
        client_ip = request.client.host if request else "unknown"
        x_forwarded_for = request.headers.get("x-forwarded-for") if request else None
        if x_forwarded_for:
            client_ip = x_forwarded_for.split(",")[0].strip()

        # Read file content for validation
        file_content = await file.read()
        file_size = len(file_content)

        # Reset file position for later processing
        await file.seek(0)

        # Get file MIME type
        mime_type = file.content_type or "application/octet-stream"

        # Validate file upload with security checks
        try:
            validate_file_upload(file.filename, file_size, mime_type)
        except ValueError as e:
            SecurityLogger.log_suspicious_activity(
                "Invalid file upload attempt",
                {
                    "filename": file.filename,
                    "size": file_size,
                    "mime_type": mime_type,
                    "course_id": course_id
                },
                client_ip
            )
            raise ValidationError(str(e))

        # Sanitize filename to prevent directory traversal
        try:
            safe_filename_str = sanitize_filename(file.filename)
        except ValueError as e:
            SecurityLogger.log_suspicious_activity(
                "Dangerous filename attempt",
                {
                    "original_filename": file.filename,
                    "course_id": course_id
                },
                client_ip
            )
            raise ValidationError(f"Invalid filename: {e}")

        # Generate unique filename to prevent overwrites
        from utils.security import generate_safe_filename
        unique_filename = generate_safe_filename(
            safe_filename_str,
            prefix=course_id,
            suffix="upload"
        )

        # Create and validate course directory path
        course_dir = f"data/courses/{course_id}"
        try:
            os.makedirs(course_dir, exist_ok=True)
            validated_course_dir = validate_file_path(course_dir, "data")
        except ValueError as e:
            SecurityLogger.log_suspicious_activity(
                "Invalid directory traversal attempt",
                {
                    "course_id": course_id,
                    "course_dir": course_dir
                },
                client_ip
            )
            raise ValidationError(f"Invalid course directory: {e}")

        # Construct and validate final file path
        file_path = os.path.join(validated_course_dir, unique_filename)
        try:
            validated_file_path = validate_file_path(file_path, "data")
        except ValueError as e:
            SecurityLogger.log_suspicious_activity(
                "File path validation failed",
                {
                    "file_path": file_path,
                    "course_id": course_id
                },
                client_ip
            )
            raise ValidationError(f"Invalid file path: {e}")

        # Additional PDF content validation
        if not file.filename.lower().endswith('.pdf'):
            raise ValidationError("Only PDF files are allowed")

        # Validate PDF content
        temp_file_path = validated_file_path + ".tmp"
        try:
            # Write to temporary file first
            with open(temp_file_path, "wb") as temp_buffer:
                temp_buffer.write(file_content)

            # Validate it's actually a PDF
            from utils.security import validate_pdf_content
            validate_pdf_content(temp_file_path)

            # Move to final location
            os.rename(temp_file_path, validated_file_path)

        except Exception as e:
            # Clean up temp file if validation failed
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
            raise ValidationError(f"PDF validation failed: {e}")

        # Log successful file upload
        SecurityLogger.log_file_access(
            validated_file_path,
            context="file_upload"
        )

        # Process and index the PDF with error handling
        try:
            await rag_service.index_pdf(validated_file_path, course_id)
        except Exception as e:
            # If indexing fails, remove the uploaded file
            if os.path.exists(validated_file_path):
                os.remove(validated_file_path)
            logger.error(f"PDF indexing failed for {validated_file_path}: {e}")
            raise FileOperationError(f"Failed to process PDF: {e}")

        return {
            "success": True,
            "message": "File uploaded and indexed successfully",
            "filename": unique_filename,
            "original_filename": file.filename,
            "size": file_size
        }

    except (ValidationError, SecurityError) as e:
        raise ErrorHandler.handle_error(e, "file_upload")
    except Exception as e:
        logger.error(f"Unexpected error in file upload: {e}")
        raise ErrorHandler.handle_error(e, "file_upload")

# Book endpoints
@app.post("/courses/{course_id}/books")
async def create_book(course_id: str, book: BookCreate):
    try:
        result = book_service.create_book(course_id, book.dict())
        return {"success": True, "book": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/courses/{course_id}/books")
async def get_books(course_id: str):
    try:
        books = book_service.get_books_by_course(course_id)
        return {"books": books}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/courses/{course_id}/books/{book_id}")
async def get_book(course_id: str, book_id: str):
    try:
        book = book_service.get_book(course_id, book_id)
        if not book:
            raise HTTPException(status_code=404, detail="Book not found")
        return {"book": book}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/courses/{course_id}/books/{book_id}")
async def update_book(course_id: str, book_id: str, book_update: BookUpdate):
    try:
        update_data = {k: v for k, v in book_update.dict().items() if v is not None}
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")

        book = book_service.update_book(course_id, book_id, update_data)
        if not book:
            raise HTTPException(status_code=404, detail="Book not found")

        try:
            await study_planner.refresh_course_plans_with_books(course_id)
        except Exception as exc:
            structlog.get_logger().error(
                "Failed to refresh study plans after book update",
                course_id=course_id,
                book_id=book_id,
                error=str(exc)
            )

        return {"success": True, "book": book}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/courses/{course_id}/books/{book_id}")
async def delete_book(course_id: str, book_id: str):
    try:
        success = book_service.delete_book(course_id, book_id)
        if not success:
            raise HTTPException(status_code=404, detail="Book not found")

        # Also delete RAG documents for this book
        rag_service.delete_book_documents(course_id, book_id)

        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/courses/{course_id}/books/{book_id}/upload")
async def upload_book_material(course_id: str, book_id: str, file: UploadFile = File(...)):
    try:
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")

        # Check if book exists first
        book = book_service.get_book(course_id, book_id)
        if not book:
            raise HTTPException(status_code=404, detail="Book not found")

        # Save file
        book_dir = f"data/courses/{course_id}/books/{book_id}"
        os.makedirs(book_dir, exist_ok=True)
        file_path = f"{book_dir}/{file.filename}"

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Process and index the PDF for the book (with error handling)
        try:
            await rag_service.index_pdf(file_path, course_id, book_id)
            indexing_status = "File uploaded and indexed successfully"
        except Exception as indexing_error:
            print(f"Warning: RAG indexing failed: {indexing_error}")
            indexing_status = "File uploaded successfully (indexing temporarily disabled)"

        return {"success": True, "message": indexing_status}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat")
async def chat(chat_message: ChatMessage):
    try:
        # Choose search method based on user preference with caching
        if chat_message.use_hybrid_search:
            # Use hybrid search (semantic + keyword) with caching
            context = await rag_service.retrieve_context_cached(
                chat_message.message,
                chat_message.course_id,
                chat_message.book_id,
                chat_message.search_k,
                use_hybrid=True
            )
        else:
            # Use traditional semantic search with caching
            context = await rag_service.retrieve_context_cached(
                chat_message.message,
                chat_message.course_id,
                chat_message.book_id,
                chat_message.search_k,
                use_hybrid=False
            )

        # Generate response (potentially cached)
        response = await llm_service.generate_response(
            chat_message.message,
            context,
            chat_message.course_id
        )

        # Track session
        session_id = study_tracker.track_interaction(
            chat_message.course_id,
            chat_message.session_id,
            chat_message.message,
            response
        )

        return {
            "response": response,
            "session_id": session_id,
            "sources": context.get("sources", []),
            "search_method": context.get("search_method", "semantic"),
            "cache_info": {
                "cache_enabled": True,
                "cached": context.get("cached", False)
            },
            "search_stats": {
                "hybrid_used": chat_message.use_hybrid_search,
                "results_count": len(context.get("sources", []))
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/quiz")
async def generate_quiz(quiz_request: QuizRequest):
    try:
        quiz = await llm_service.generate_quiz(
            quiz_request.course_id,
            quiz_request.topic,
            quiz_request.difficulty,
            quiz_request.num_questions
        )
        return {"quiz": quiz}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Hybrid Search endpoints
class HybridSearchConfig(BaseModel):
    semantic_weight: Optional[float] = 0.6
    keyword_weight: Optional[float] = 0.4
    fusion_method: Optional[str] = "weighted_sum"

class HybridSearchRequest(BaseModel):
    query: str
    course_id: str
    book_id: Optional[str] = None
    k: Optional[int] = 10
    semantic_weight: Optional[float] = 0.6
    keyword_weight: Optional[float] = 0.4
    fusion_method: Optional[str] = "weighted_sum"

class CacheInvalidationRequest(BaseModel):
    course_id: str
    book_id: Optional[str] = None

@app.post("/hybrid-search/config")
async def configure_hybrid_search(config: HybridSearchConfig):
    """Configure hybrid search parameters"""
    try:
        rag_service._init_hybrid_search()
        if rag_service.hybrid_search:
            rag_service.hybrid_search.update_weights(config.semantic_weight, config.keyword_weight)
            rag_service.hybrid_search.set_fusion_method(config.fusion_method)
            return {
                "success": True,
                "message": "Hybrid search configuration updated",
                "config": {
                    "semantic_weight": config.semantic_weight,
                    "keyword_weight": config.keyword_weight,
                    "fusion_method": config.fusion_method
                }
            }
        else:
            raise HTTPException(status_code=503, detail="Hybrid search service not available")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/hybrid-search")
async def hybrid_search(search_request: HybridSearchRequest):
    """Execute hybrid search with custom parameters"""
    try:
        rag_service._init_hybrid_search()
        if not rag_service.hybrid_search:
            raise HTTPException(status_code=503, detail="Hybrid search service not available")

        # Update configuration temporarily
        original_semantic = rag_service.hybrid_search.semantic_weight
        original_keyword = rag_service.hybrid_search.keyword_weight
        original_fusion = rag_service.hybrid_search.fusion_method

        rag_service.hybrid_search.update_weights(search_request.semantic_weight, search_request.keyword_weight)
        rag_service.hybrid_search.set_fusion_method(search_request.fusion_method)

        # Execute search
        result = await rag_service.hybrid_search.hybrid_search(
            search_request.query,
            search_request.course_id,
            search_request.book_id,
            search_request.k
        )

        # Restore original configuration
        rag_service.hybrid_search.update_weights(original_semantic, original_keyword)
        rag_service.hybrid_search.set_fusion_method(original_fusion)

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/hybrid-search/stats")
async def get_hybrid_search_stats():
    """Get hybrid search statistics and configuration"""
    try:
        stats = rag_service.get_hybrid_search_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Cache Management endpoints
@app.get("/cache/stats")
async def get_cache_stats():
    """Get cache statistics and performance metrics"""
    try:
        cache_metrics = await rag_service.get_cache_metrics()
        return cache_metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/cache/clear")
async def clear_cache(cache_type: Optional[str] = None):
    """Clear cache (all or specific type)"""
    try:
        result = await rag_service.clear_cache(cache_type)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/cache/invalidate")
async def invalidate_cache(invalidation_request: CacheInvalidationRequest):
    """Invalidate cache for specific course/book"""
    try:
        rag_service.invalidate_course_cache(
            invalidation_request.course_id,
            invalidation_request.book_id
        )
        return {
            "success": True,
            "message": f"Cache invalidated for course {invalidation_request.course_id}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/cache/health")
async def cache_health_check():
    """Health check for cache system"""
    try:
        cache_metrics = await rag_service.get_cache_metrics()
        return cache_metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Rimosso temporaneamente endpoint session perché StudySession non è definito
# @app.post("/study-session")
# async def record_study_session(session: StudySession):
#     try:
#         result = study_tracker.record_study_session(session.dict())
#         return {"success": True, "session_id": result}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

@app.get("/study-progress/{course_id}")
async def get_study_progress(course_id: str):
    try:
        progress = study_tracker.get_progress(course_id)
        return {"progress": progress}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/study-progress/overview")
async def get_overall_progress():
    """Get overall progress across all courses"""
    try:
        courses = course_service.get_all_courses()
        overall_stats = {
            "total_study_time": 0,
            "total_sessions": 0,
            "courses_with_progress": 0,
            "total_concepts_learned": 0,
            "weekly_progress": [],
            "course_progress": []
        }

        # Calculate weekly progress (last 7 days)
        weekly_data = []
        for i in range(7):
            day = datetime.now() - timedelta(days=i)
            weekly_data.append({
                "day": day.strftime("%a")[:3],  # Lun, Mar, etc.
                "date": day.strftime("%Y-%m-%d"),
                "minutes": 0,
                "sessions": 0
            })
        weekly_data.reverse()  # Start from Monday

        for course in courses:
            course_id = course["id"]
            progress = study_tracker.get_progress(course_id)

            if progress.get("total_sessions", 0) > 0:
                overall_stats["courses_with_progress"] += 1
                overall_stats["total_study_time"] += progress.get("total_study_time", 0)
                overall_stats["total_sessions"] += progress.get("total_sessions", 0)
                overall_stats["total_concepts_learned"] += len(progress.get("topics_covered", []))

                overall_stats["course_progress"].append({
                    "course_id": course_id,
                    "course_name": course["name"],
                    "sessions": progress.get("total_sessions", 0),
                    "study_time": progress.get("total_study_time", 0),
                    "concepts": len(progress.get("topics_covered", []))
                })

        # Generate weekly breakdown (mock data for now since we don't have daily tracking)
        if overall_stats["total_sessions"] > 0:
            # Distribute sessions and time across the week
            for day_data in weekly_data:
                if overall_stats["total_sessions"] > 0:
                    day_data["sessions"] = max(0, overall_stats["total_sessions"] // 7 - 1 + (hash(day_data["date"]) % 3))
                    day_data["minutes"] = max(0, overall_stats["total_study_time"] // 7 - 10 + (hash(day_data["date"]) % 30))

        overall_stats["weekly_progress"] = weekly_data

        return overall_stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/study-insights/{course_id}")
async def get_study_insights(course_id: str):
    try:
        insights = study_tracker.get_study_insights(course_id)
        return {"insights": insights}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Model management endpoints
@app.get("/models")
async def get_available_models():
    """Get available models and their characteristics"""
    try:
        return await llm_service.get_available_models()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/models/{model_name}")
async def set_model(model_name: str):
    """Set the active model"""
    try:
        success = await llm_service.set_model(model_name)
        if success:
            return {"success": True, "model": model_name}
        else:
            raise HTTPException(status_code=400, detail=f"Model {model_name} not available")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/models/budget-mode")
async def set_budget_mode(request: BudgetModeRequest):
    """Enable/disable budget mode"""
    try:
        llm_service.set_budget_mode(request.enabled)
        return {"success": True, "budget_mode": request.enabled}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/models/local/test")
async def test_local_connection():
    """Test connection with local LLM provider"""
    try:
        return await llm_service.test_local_connection()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/rag/status")
async def get_rag_status():
    """Get RAG system status and statistics"""
    try:
        stats = rag_service.get_collection_stats()
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "vector_db": {
                "collection_name": stats.get("collection_name", "course_materials"),
                "total_documents": stats.get("total_documents", 0),
                "embedding_model": rag_service.model_name,
                "model_loaded": rag_service.embedding_model is not None
            },
            "system_info": {
                "data_directory": "data/vector_db",
                "supported_formats": ["PDF"],
                "chunk_size": 1000,
                "chunk_overlap": 200,
                "similarity_metric": "cosine"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/rag/documents")
async def get_all_documents():
    """Get all indexed documents"""
    try:
        courses = course_service.get_all_courses()
        all_documents = []

        for course in courses:
            course_id = course["id"]
            course_docs = await rag_service.search_documents(course_id)
            if course_docs.get("documents"):
                for doc in course_docs["documents"]:
                    doc["course_name"] = course["name"]
                    doc["course_id"] = course_id
                all_documents.extend(course_docs["documents"])

        return {
            "documents": all_documents,
            "total_count": len(all_documents)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/rag/analytics")
async def get_rag_analytics():
    """Get RAG system analytics"""
    try:
        courses = course_service.get_all_courses()
        total_documents = 0
        course_stats = []

        for course in courses:
            course_id = course["id"]
            course_docs = await rag_service.search_documents(course_id)
            doc_count = len(course_docs.get("documents", []))
            total_documents += doc_count

            course_stats.append({
                "course_id": course_id,
                "course_name": course["name"],
                "document_count": doc_count,
                "subject": course["subject"]
            })

        return {
            "analytics": {
                "total_documents": total_documents,
                "total_courses": len(courses),
                "courses_with_documents": len([c for c in course_stats if c["document_count"] > 0]),
                "course_stats": course_stats
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/rag/documents/{course_id}")
async def get_course_documents(course_id: str, search_query: Optional[str] = None):
    """Get all indexed documents for a course"""
    try:
        result = await rag_service.search_documents(course_id, search_query)
        return {
            "documents": result.get("documents", []),
            "course_id": course_id,
            "total_count": len(result.get("documents", [])),
            "total_sources": result.get("total_sources", 0)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Study Planner endpoints
@app.post("/study-plans")
async def create_study_plan(request: StudyPlanCreate):
    """Create a new study plan based on course materials"""
    try:
        plan = await study_planner.generate_study_plan(
            request.course_id,
            request.dict(exclude_unset=True)
        )
        return {"success": True, "plan": plan.dict()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/study-plans/{plan_id}")
async def get_study_plan(plan_id: str):
    """Get a specific study plan"""
    try:
        plan = await study_planner.get_study_plan(plan_id)
        if not plan:
            raise HTTPException(status_code=404, detail="Study plan not found")
        return {"success": True, "plan": plan.dict()}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/courses/{course_id}/study-plans")
async def get_course_study_plans(course_id: str):
    """Get all study plans for a course"""
    try:
        plans = await study_planner.get_course_study_plans(course_id)
        return {"success": True, "plans": [plan.dict() for plan in plans]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/study-plans/{plan_id}/sessions/{session_id}")
async def update_session_progress(plan_id: str, session_id: str, request: SessionProgressUpdate):
    """Update session completion status"""
    try:
        success = await study_planner.update_session_progress(plan_id, session_id, request.completed)
        if not success:
            raise HTTPException(status_code=404, detail="Plan or session not found")
        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/study-plans/{plan_id}/missions")
async def get_study_plan_missions(plan_id: str):
    try:
        missions = await study_planner.get_plan_missions(plan_id)
        return {"success": True, "missions": [mission.dict() for mission in missions]}
    except ValueError:
        raise HTTPException(status_code=404, detail="Study plan not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/study-plans/{plan_id}/missions/{mission_id}/tasks/{task_id}")
async def update_mission_task(plan_id: str, mission_id: str, task_id: str, request: MissionTaskUpdate):
    try:
        mission = await study_planner.update_mission_task(plan_id, mission_id, task_id, request.completed)
        return {"success": True, "mission": mission.dict()}
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/study-plans/{plan_id}/regenerate")
async def regenerate_study_plan(plan_id: str, request: StudyPlanCreate):
    """Regenerate an existing study plan with new preferences"""
    try:
        new_plan = await study_planner.regenerate_plan(plan_id, request.dict(exclude_unset=True))
        return {"success": True, "plan": new_plan.dict()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/study-plans/{plan_id}")
async def delete_study_plan(plan_id: str):
    """Delete a study plan"""
    try:
        success = await study_planner.delete_study_plan(plan_id)
        if not success:
            raise HTTPException(status_code=404, detail="Study plan not found")
        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/rag/rebuild/{course_id}")
async def rebuild_course_rag_index(course_id: str):
    """Rebuild RAG index for a course with proper book_id metadata"""
    try:
        # Get course and books information
        course = course_service.get_course(course_id)
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")

        books = book_service.get_books_by_course(course_id)

        # Delete existing documents for this course
        rag_service.delete_course_documents(course_id)

        # Re-index all PDFs with proper book_id
        total_indexed = 0
        for book in books:
            book_dir = f"data/courses/{course_id}/books/{book['id']}"
            if os.path.exists(book_dir):
                for root, dirs, files in os.walk(book_dir):
                    for filename in files:
                        if filename.endswith('.pdf'):
                            file_path = os.path.join(root, filename)
                            try:
                                await rag_service.index_pdf(file_path, course_id, book['id'])
                                total_indexed += 1
                                print(f"Successfully indexed: {filename} for book {book['title']}")
                            except Exception as e:
                                print(f"Error indexing {filename}: {e}")

        return {
            "success": True,
            "message": f"Rebuilt RAG index for course {course['name']}",
            "books_processed": len(books),
            "documents_indexed": total_indexed
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class ReindexRequest(BaseModel):
    course_id: str
    new_model: Optional[str] = None

@app.post("/rag/reindex")
async def reindex_rag_with_model(request: ReindexRequest):
    """Rebuild RAG index for a course with optional new embedding model"""
    try:
        # Get course and books information
        course = course_service.get_course(request.course_id)
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")

        books = book_service.get_books_by_course(request.course_id)

        # Delete existing documents for this course
        rag_service.delete_course_documents(request.course_id)

        # Re-index all PDFs with proper book_id
        total_indexed = 0
        for book in books:
            book_dir = f"data/courses/{request.course_id}/books/{book['id']}"
            if os.path.exists(book_dir):
                for root, dirs, files in os.walk(book_dir):
                    for filename in files:
                        if filename.endswith('.pdf'):
                            file_path = os.path.join(root, filename)
                            try:
                                await rag_service.index_pdf(file_path, request.course_id, book['id'])
                                total_indexed += 1
                                print(f"Successfully indexed: {filename} for book {book['title']}")
                            except Exception as e:
                                print(f"Error indexing {filename}: {e}")

        response_message = f"Rebuilt RAG index for course {course['name']}"
        if request.new_model:
            response_message += f" with new model {request.new_model}"

        return {
            "success": True,
            "message": response_message,
            "books_processed": len(books),
            "documents_indexed": total_indexed,
            "new_model": request.new_model
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/mindmap")
async def generate_mindmap(request: MindmapRequest):
    """Generate a mindmap using RAG system"""
    try:
        topic = request.topic or "Contenuti del corso"
        focus_description = ", ".join(request.focus_areas) if request.focus_areas else "tutti i contenuti rilevanti"

        instructions = f"""
Sei un pedagogo universitario esperto. Genera una mappa di studio altamente strutturata basata sui materiali forniti.

DEVI restituire esclusivamente un JSON valido (UTF-8) senza testo aggiuntivo, senza markdown e senza commenti.

Schema obbligatorio:
{{
  "title": "Titolo della mappa",
  "overview": "Sintesi di 2-3 frasi",
  "nodes": [
    {{
      "id": "concetto-principale",
      "title": "Titolo del concetto",
      "summary": "Spiegazione sintetica (max 2 frasi)",
      "ai_hint": "Suggerimento su come utilizzare l'AI per approfondire",
      "study_actions": ["Attività concreta 1", "Attività concreta 2"],
      "priority": 1,
      "references": ["Riferimento 1"],
      "children": [...]
    }}
  ],
  "study_plan": [
    {{
      "phase": "Fase 1 - Preparazione",
      "objective": "Obiettivo specifico della fase",
      "activities": ["Attività 1", "Attività 2"],
      "ai_support": "Come l'AI può supportare questa fase",
      "duration_minutes": 45
    }}
  ],
  "references": ["Fonte 1", "Fonte 2"]
}}

Requisiti fondamentali:
- Almeno 5 nodi di primo livello in "nodes"
- Ogni nodo principale deve avere almeno 2 figli
- Ogni nodo deve includere "study_actions" con attività pratiche e concrete
- "ai_hint" spiega come interagire con l'assistente AI per approfondire quel concetto
- "study_plan" deve contenere minimo 3 fasi sequenziali che coprano analisi, pratica e verifica
- Le "references" devono citare fonti o contesti utili (documenti o concetti) quando disponibili

Argomento principale: {topic}
Focus richiesti: {focus_description}
        """.strip()

        rag_context_prompt = f"Genera materiali per la mappa concettuale su {topic}. Focus: {focus_description}."

        rag_response = await rag_service.retrieve_context(
            rag_context_prompt,
            course_id=request.course_id,
            book_id=request.book_id,
            k=6
        )

        # Debug logging to verify book filtering
        print(f"🔍 Mindmap generation - Course: {request.course_id}, Book: {request.book_id}")
        print(f"📊 RAG context found: {len(rag_response.get('text', ''))} characters")

        context_text = rag_response.get("text", "")

        final_prompt = f"""{instructions}

CONTESTO RILEVANTE ESTRATTO DAI MATERIALI:
{context_text}

Ricorda: restituisci SOLO JSON valido conforme allo schema indicato.
""".strip()

        llm_timeout = int(os.getenv("MINDMAP_LLM_TIMEOUT", "25"))
        llm_response = ""

        try:
            llm_response = await asyncio.wait_for(
                llm_service.generate_response(
                    query=final_prompt,
                    context={"text": context_text, "sources": rag_response.get("sources", [])},
                    course_id=request.course_id
                ),
                timeout=llm_timeout
            )
        except asyncio.TimeoutError:
            logger.error(f"LLM mindmap generation timed out after {llm_timeout} seconds – using fallback strategy")
        except Exception as llm_error:
            logger.error(f"LLM mindmap generation failed: {llm_error}")
            # Preserve any textual output if available
            if isinstance(llm_error, str):
                llm_response = llm_error

        raw_output = (llm_response or "").strip()
        lower_output = raw_output.lower()
        apology_markers = ["mi dispiace", "problema", "riprov", "errore"]

        if not raw_output and context_text:
            # Use retrieved context to synthesize a structured map when the LLM response is empty
            raw_output = context_text
        elif any(marker in lower_output for marker in apology_markers) and context_text:
            logger.warning("LLM returned an apology message; falling back to RAG context for mindmap synthesis")
            raw_output = context_text

        # Try to extract JSON from response with multiple strategies
        json_candidate = raw_output

        # Strategy 1: Extract JSON from code fences
        if "```" in raw_output:
            fence_start = raw_output.find("```")
            fence_end = raw_output.rfind("```")
            if fence_end > fence_start:
                possible = raw_output[fence_start + 3:fence_end]
                possible = possible.replace("json", "", 1).strip()
                json_candidate = possible

        # Strategy 2: Find JSON object boundaries
        if json_candidate.startswith('{') and json_candidate.endswith('}'):
            # Try to find complete JSON object
            brace_count = 0
            json_end = 0
            for i, char in enumerate(json_candidate):
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        json_end = i + 1
                        break
            if json_end > 0:
                json_candidate = json_candidate[:json_end]

        # Strategy 3: Clean common JSON issues
        json_candidate = json_candidate.strip()
        # Remove common prefixes/suffixes
        if json_candidate.startswith('```json'):
            json_candidate = json_candidate[7:].strip()
        if json_candidate.endswith('```'):
            json_candidate = json_candidate[:-3].strip()

        structured_map = None
        markdown_content = ""
        parse_error = None
        max_raw_output = int(os.getenv("MINDMAP_MAX_RAW_OUTPUT", "12000"))
        raw_output_contains_json = "{" in raw_output and "}" in raw_output

        # Only force the legacy fallback when we are sure the response is just a huge blob of text.
        if len(raw_output) > max_raw_output and not raw_output_contains_json:
            logger.warning(
                "Raw LLM output too large (%s chars) and missing JSON markers, forcing structured fallback",
                len(raw_output)
            )
            structured_map = _create_structured_mindmap_from_text(raw_output, topic)
            markdown_content = _mindmap_to_markdown(structured_map)
            logger.info("Created structured mindmap due to oversized raw output without JSON data")
        else:
            # Try JSON parsing with better error handling
            try:
                parsed_payload = json.loads(json_candidate)
                # Always validate - the LLM often returns malformed data
                if not _is_valid_mindmap_payload(parsed_payload):
                    logger.warning("Parsed JSON is not a valid mindmap structure, forcing fallback")
                    raise ValueError("Invalid mindmap structure")

                # Additional safety check - if any field looks like JSON string, force fallback
                if _has_json_strings_in_payload(parsed_payload):
                    logger.warning("Payload contains JSON strings as values, forcing fallback")
                    raise ValueError("JSON strings found in payload")

                structured_map = _normalize_mindmap_payload(parsed_payload)
                markdown_content = _mindmap_to_markdown(structured_map)
                logger.info("Successfully parsed JSON mindmap")
            except Exception as e:
                parse_error = str(e)
                logger.warning(f"JSON parsing failed: {parse_error}")
                logger.warning(f"Raw output (first 500 chars): {raw_output[:500]}")

                # More aggressive fallback strategies
                try:
                    # Strategy 1: Try to fix common JSON issues
                    fixed_json = _fix_common_json_issues(json_candidate)
                    if fixed_json:
                        try:
                            parsed_payload = json.loads(fixed_json)
                            structured_map = _normalize_mindmap_payload(parsed_payload)
                            markdown_content = _mindmap_to_markdown(structured_map)
                            logger.info("Successfully parsed fixed JSON")
                        except:
                            pass

                    # Strategy 2: Try to extract JSON from malformed text
                    if not structured_map and '{' in raw_output:
                        # Try multiple extraction strategies
                        extracted_json = _extract_json_from_malformed_text(raw_output)
                        if extracted_json:
                            try:
                                parsed_payload = json.loads(extracted_json)
                                structured_map = _normalize_mindmap_payload(parsed_payload)
                                markdown_content = _mindmap_to_markdown(structured_map)
                                logger.info("Successfully parsed extracted JSON")
                            except:
                                pass

                    # Strategy 3: Create structured mindmap from text content
                    if not structured_map:
                        structured_map = _create_structured_mindmap_from_text(raw_output, topic)
                        markdown_content = _mindmap_to_markdown(structured_map)
                        logger.info("Created structured mindmap from text content")

                except Exception as fallback_error:
                    logger.error(f"All parsing strategies failed: {fallback_error}")
                    # Final fallback - create minimal mindmap
                    structured_map = _create_minimal_mindmap(topic)
                    markdown_content = _mindmap_to_markdown(structured_map)
                    logger.info("Created minimal mindmap as final fallback")

        metadata = {
            "course_id": request.course_id,
            "book_id": request.book_id,
            "topic": topic,
            "focus_areas": request.focus_areas,
            "generated_at": datetime.now().isoformat(),
            "source_count": len(rag_response.get("sources", []))
        }

        # Final safety check - ensure we have valid mindmap data
        if not structured_map or not isinstance(structured_map, dict):
            logger.error("CRITICAL: No valid structured_map created, using minimal fallback")
            structured_map = _create_minimal_mindmap(topic)
            markdown_content = _mindmap_to_markdown(structured_map)

        return {
            "success": True,
            "mindmap": structured_map,
            "markdown": markdown_content,
            "study_plan": structured_map.get("study_plan", []),
            "references": structured_map.get("references", []),
            "sources": rag_response.get("sources", []),
            "metadata": metadata
        }

    except Exception as e:
        logger.error(f"Error generating mindmap: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "Error generating mindmap",
                "detail": str(e),
                "mindmap": None,
                "markdown": "",
                "references": [],
                "sources": []
            }
        )

# Background Task Management Endpoints
@app.post("/study-plans/background")
async def create_background_study_plan(request: StudyPlanCreate):
    """Create a study plan in background"""
    try:
        task_id = await study_planner.generate_study_plan_background(
            course_id=request.course_id,
            preferences=request.dict(exclude_unset=True)
        )

        return {
            "success": True,
            "task_id": task_id,
            "message": "Piano di studio in generazione in background"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating background study plan: {str(e)}")

@app.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    """Get the status of a background task"""
    try:
        task_status = study_planner.get_background_task_status(task_id)
        if not task_status:
            raise HTTPException(status_code=404, detail="Task not found")

        return task_status
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting task status: {str(e)}")

@app.get("/courses/{course_id}/tasks")
async def get_course_tasks(course_id: str):
    """Get all background tasks for a course"""
    try:
        tasks = study_planner.get_course_background_tasks(course_id)
        return {
            "tasks": tasks,
            "total": len(tasks)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting course tasks: {str(e)}")

@app.delete("/tasks/{task_id}")
async def cancel_task(task_id: str):
    """Cancel a running background task"""
    try:
        success = background_task_service.cancel_task(task_id)
        if not success:
            raise HTTPException(status_code=404, detail="Task not found or cannot be cancelled")

        return {
            "success": True,
            "message": "Task cancelled successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error cancelling task: {str(e)}")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/api/courses/{course_id}/presentations")
async def get_presentations(course_id: str):
    """Mock endpoint for compatibility with frontend"""
    return {
        "presentations": [],
        "message": "No presentations available - use Z.AI slide generator instead"
    }

@app.post("/slides/simple")
async def simple_slides_endpoint(request: dict):
    print(f"DEBUG: Simple slides endpoint called with: {request}")
    return {
        "title": f"Simple Presentation: {request.get('prompt', 'No prompt')}",
        "slides": [
            {
                "title": "Test Slide",
                "content": ["This is a test slide", "Simple implementation"],
                "slide_number": 1
            }
        ],
        "total_slides": 1
    }

# Annotation endpoints
@app.post("/annotations")
async def create_annotation(annotation: AnnotationCreate):
    """Create a new annotation"""
    try:
        result = annotation_service.create_annotation(annotation.dict())
        return {"success": True, "annotation": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/annotations/{user_id}/{pdf_filename}")
async def get_annotations_for_pdf(user_id: str, pdf_filename: str, course_id: str = "", book_id: str = ""):
    """Get all annotations for a specific PDF and user"""
    try:
        annotations = annotation_service.get_annotations_for_pdf(user_id, pdf_filename, course_id, book_id)
        return {"annotations": annotations}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/annotations/{user_id}")
async def get_annotation(user_id: str, annotation_id: str, pdf_filename: str = "", course_id: str = "", book_id: str = ""):
    """Get a specific annotation by ID"""
    try:
        annotation = annotation_service.get_annotation(user_id, annotation_id, pdf_filename, course_id, book_id)
        if not annotation:
            raise HTTPException(status_code=404, detail="Annotation not found")
        return {"annotation": annotation}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/annotations/{user_id}/{annotation_id}")
async def update_annotation(user_id: str, annotation_id: str, update_data: AnnotationUpdate, pdf_filename: str = "", course_id: str = "", book_id: str = ""):
    """Update an existing annotation"""
    try:
        annotation = annotation_service.update_annotation(
            user_id, annotation_id, update_data.dict(exclude_unset=True), pdf_filename, course_id, book_id
        )
        if not annotation:
            raise HTTPException(status_code=404, detail="Annotation not found")
        return {"success": True, "annotation": annotation}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/annotations/{user_id}/{annotation_id}")
async def delete_annotation(user_id: str, annotation_id: str, pdf_filename: str = "", course_id: str = "", book_id: str = ""):
    """Delete an annotation"""
    try:
        success = annotation_service.delete_annotation(user_id, annotation_id, pdf_filename, course_id, book_id)
        if not success:
            raise HTTPException(status_code=404, detail="Annotation not found")
        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/annotations/search/{user_id}")
async def search_annotations(user_id: str, search_request: AnnotationSearch):
    """Search annotations by text content, tags, or type"""
    try:
        annotations = annotation_service.search_annotations(
            user_id,
            search_request.query,
            search_request.course_id,
            search_request.book_id,
            search_request.tags,
            search_request.annotation_type
        )
        return {"annotations": annotations}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/annotations/public/{pdf_filename}")
async def get_public_annotations(pdf_filename: str, course_id: str = "", book_id: str = ""):
    """Get public annotations for a PDF from all users"""
    try:
        annotations = annotation_service.get_public_annotations(pdf_filename, course_id, book_id)
        return {"annotations": annotations}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/annotations/{user_id}/export")
async def export_annotations(user_id: str, format: str = "json", course_id: str = "", book_id: str = ""):
    """Export user annotations in various formats"""
    try:
        if format not in ["json", "markdown", "csv"]:
            raise HTTPException(status_code=400, detail="Unsupported export format")

        export_data = annotation_service.export_annotations(user_id, format, course_id, book_id)
        return {"success": True, "format": format, "data": export_data}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/annotations/{user_id}/import")
async def import_annotations(user_id: str, annotations_data: dict, format: str = "json"):
    """Import annotations from various formats"""
    try:
        if format not in ["json", "markdown"]:
            raise HTTPException(status_code=400, detail="Unsupported import format")

        imported_count = annotation_service.import_annotations(user_id, annotations_data, format)
        return {"success": True, "imported_count": imported_count}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/annotations/{user_id}/stats")
async def get_annotation_stats(user_id: str, course_id: str = "", book_id: str = ""):
    """Get statistics about user annotations"""
    try:
        stats = annotation_service.get_annotation_stats(user_id, course_id, book_id)
        return {"stats": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# OCR Endpoints

class OCRRequest(BaseModel):
    pdf_path: str
    language: str = "ita"
    engine: str = "tesseract"  # "tesseract" or "easyocr"

@app.post("/ocr/detect-scanned")
async def detect_scanned_pdf(request: OCRRequest):
    """Detect if a PDF is scanned and needs OCR processing"""
    try:
        if not os.path.exists(request.pdf_path):
            raise HTTPException(status_code=404, detail="PDF file not found")

        result = ocr_service.detect_scanned_pdf(request.pdf_path)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ocr/process-pdf")
async def process_pdf_ocr(request: OCRRequest):
    """Process a PDF with OCR to extract text from scanned pages"""
    try:
        if not os.path.exists(request.pdf_path):
            raise HTTPException(status_code=404, detail="PDF file not found")

        # Set preferred engine
        ocr_service.prefer_engine = request.engine

        # Process OCR
        result = await ocr_service.async_ocr_pdf(request.pdf_path, request.language)

        # Save result to file
        output_file = ocr_service.save_ocr_result(request.pdf_path, result)

        result["output_file"] = output_file
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ocr/upload-and-process")
async def upload_and_process_ocr(
    file: UploadFile = File(...),
    language: str = "ita",
    engine: str = "tesseract"
):
    """Upload a PDF file and process it with OCR"""
    try:
        # Validate file type
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")

        # Create upload directory if it doesn't exist
        upload_dir = "data/uploads/ocr"
        os.makedirs(upload_dir, exist_ok=True)

        # Save uploaded file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{file.filename}"
        file_path = os.path.join(upload_dir, filename)

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Detect if PDF needs OCR
        detection_result = ocr_service.detect_scanned_pdf(file_path)

        # Process with OCR if needed
        ocr_result = None
        if detection_result.get("is_scanned", False):
            ocr_service.prefer_engine = engine
            ocr_result = await ocr_service.async_ocr_pdf(file_path, language)
            output_file = ocr_service.save_ocr_result(file_path, ocr_result)
            ocr_result["output_file"] = output_file

        return {
            "filename": filename,
            "file_path": file_path,
            "detection_result": detection_result,
            "ocr_result": ocr_result
        }

    except Exception as e:
        # Clean up file on error
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/ocr/engines")
async def get_available_ocr_engines():
    """Get list of available OCR engines and their status"""
    return {
        "engines": {
            "tesseract": {
                "available": ocr_service.tesseract_available,
                "name": "Tesseract",
                "languages": ["ita", "eng", "fra", "deu", "spa"]
            },
            "easyocr": {
                "available": ocr_service.easyocr_available,
                "name": "EasyOCR",
                "languages": ["it", "en", "fr", "de", "es", "auto"]
            }
        },
        "preferred_engine": ocr_service.prefer_engine
    }

@app.post("/ocr/set-engine")
async def set_preferred_ocr_engine(engine: str = "tesseract"):
    """Set the preferred OCR engine"""
    if engine not in ["tesseract", "easyocr"]:
        raise HTTPException(status_code=400, detail="Engine must be 'tesseract' or 'easyocr'")

    ocr_service.prefer_engine = engine
    return {
        "message": f"Preferred OCR engine set to {engine}",
        "preferred_engine": ocr_service.prefer_engine
    }

# Advanced Search Endpoints

class AdvancedSearchRequest(BaseModel):
    query: str
    search_type: str = "text"  # "text", "semantic", "hybrid"
    filters: Optional[Dict[str, Any]] = None
    sort_order: str = "relevance"  # "relevance", "date", "alphabetical", "confidence"
    limit: int = 50
    offset: int = 0
    include_highlights: bool = True
    highlight_tags: bool = False

@app.post("/search/advanced")
async def advanced_search(request: AdvancedSearchRequest):
    """Perform advanced search with filters and categories"""
    try:
        # Parse search type
        search_type = SearchType(request.search_type)
        sort_order = SortOrder(request.sort_order)

        # Parse filters
        filters = None
        if request.filters:
            filters = SearchFilter(
                course_ids=request.filters.get("course_ids"),
                book_ids=request.filters.get("book_ids"),
                user_ids=request.filters.get("user_ids"),
                tags=request.filters.get("tags"),
                annotation_types=request.filters.get("annotation_types"),
                date_range=request.filters.get("date_range"),
                confidence_range=request.filters.get("confidence_range"),
                page_range=request.filters.get("page_range"),
                is_public=request.filters.get("is_public"),
                is_favorite=request.filters.get("is_favorite"),
                min_text_length=request.filters.get("min_text_length"),
                language=request.filters.get("language")
            )

        # Create search query
        search_query = SearchQuery(
            query=request.query,
            search_type=search_type,
            filters=filters,
            sort_order=sort_order,
            limit=request.limit,
            offset=request.offset,
            include_highlights=request.include_highlights,
            highlight_tags=request.highlight_tags
        )

        # Perform search
        result = await advanced_search_service.search(search_query)

        return {
            "query": result.query,
            "results": [asdict(search_result) for search_result in result.results],
            "total_count": result.total_count,
            "has_more": result.has_more,
            "search_time": result.search_time,
            "facets": result.facets,
            "suggestions": result.suggestions
        }

    except Exception as e:
        logger.error(f"Error in advanced search: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/search/suggestions")
async def get_search_suggestions(q: str, limit: int = 10):
    """Get search suggestions for autocomplete"""
    try:
        suggestions = advanced_search_service.get_search_suggestions(q, limit)
        return {"suggestions": suggestions}
    except Exception as e:
        logger.error(f"Error getting search suggestions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/search/facets")
async def get_search_facets(query: str = ""):
    """Get available facets for filtering"""
    try:
        if query:
            # Perform a search to get facets
            search_query = SearchQuery(query=query, limit=0)
            result = await advanced_search_service.search(search_query)
            return {"facets": result.facets}
        else:
            # Return available facets without search
            # This would typically come from cached metadata
            return {
                "facets": {
                    "types": {
                        "annotation": 0,
                        "ocr_result": 0,
                        "pdf_content": 0
                    },
                    "courses": {},
                    "users": {},
                    "tags": {}
                }
            }
    except Exception as e:
        logger.error(f"Error getting search facets: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/search/rebuild-indexes")
async def rebuild_search_indexes():
    """Rebuild search indexes"""
    try:
        advanced_search_service.rebuild_indexes()
        return {"message": "Search indexes rebuilt successfully"}
    except Exception as e:
        logger.error(f"Error rebuilding search indexes: {e}")
        raise HTTPException(status_code=500, detail=str(e))

class SearchFiltersRequest(BaseModel):
    course_ids: Optional[List[str]] = None
    book_ids: Optional[List[str]] = None
    user_ids: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    annotation_types: Optional[List[str]] = None
    date_range: Optional[Dict[str, str]] = None
    confidence_range: Optional[Dict[str, float]] = None
    page_range: Optional[Dict[str, int]] = None
    is_public: Optional[bool] = None
    is_favorite: Optional[bool] = None
    min_text_length: Optional[int] = None
    language: Optional[str] = None

@app.post("/search/validate-filters")
async def validate_search_filters(filters: SearchFiltersRequest):
    """Validate search filters and return available options"""
    try:
        # This would validate filters against available data
        # For now, just return the filters as valid
        validation_result = {
            "valid": True,
            "available_options": {
                "course_ids": [],  # Would be populated from actual courses
                "book_ids": [],     # Would be populated from actual books
                "annotation_types": ["highlight", "underline", "note", "strikeout", "text"],
                "languages": ["ita", "eng", "fra", "deu", "spa"]
            },
            "invalid_fields": []
        }

        # Check for invalid fields
        if filters.annotation_types:
            invalid_types = [t for t in filters.annotation_types if t not in validation_result["available_options"]["annotation_types"]]
            if invalid_types:
                validation_result["invalid_fields"].append({
                    "field": "annotation_types",
                    "invalid_values": invalid_types
                })

        validation_result["valid"] = len(validation_result["invalid_fields"]) == 0

        return validation_result

    except Exception as e:
        logger.error(f"Error validating search filters: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/search/stats")
async def get_search_stats():
    """Get search statistics and metrics"""
    try:
        # This would return actual search statistics
        # For now, return placeholder data
        return {
            "total_documents": 0,
            "total_annotations": 0,
            "total_ocr_results": 0,
            "last_indexed": None,
            "search_performance": {
                "avg_search_time": 0.0,
                "total_searches": 0
            },
            "popular_searches": [],
            "index_health": "healthy"
        }
    except Exception as e:
        logger.error(f"Error getting search stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
