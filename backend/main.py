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

app = FastAPI(title="AI Tutor Backend", version="1.0.0")

# CORS configuration - restricted to specific origins and methods
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:5000", "http://127.0.0.1:5000"],  # Frontend ports
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],  # Specific methods only
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

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for consistent error responses."""
    return ErrorHandler.handle_error(exc, f"{request.method} {request.url.path}")

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
    overview = str(payload.get("overview") or payload.get("summary") or "").strip()

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

    # Provide minimal default if no nodes were generated
    if not normalized["nodes"]:
        normalized["nodes"] = [{
            "id": _ensure_unique_id(_slugify_text(title), used_ids),
            "title": title,
            "summary": overview or "Concetto principale della mappa di studio.",
            "ai_hint": "",
            "study_actions": [],
            "priority": None,
            "references": [],
            "children": []
        }]

    return normalized


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
        # Retrieve relevant context (with optional book filter)
        context = await rag_service.retrieve_context(
            chat_message.message,
            chat_message.course_id,
            chat_message.book_id
        )

        # Generate response
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
            "sources": context.get("sources", [])
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

        context_text = rag_response.get("text", "")

        final_prompt = f"""{instructions}

CONTESTO RILEVANTE ESTRATTO DAI MATERIALI:
{context_text}

Ricorda: restituisci SOLO JSON valido conforme allo schema indicato.
""".strip()

        llm_response = await llm_service.generate_response(
            query=final_prompt,
            context={"text": context_text, "sources": rag_response.get("sources", [])},
            course_id=request.course_id
        )

        raw_output = llm_response.strip()

        # Extract JSON content if wrapped in code fences
        if "```" in raw_output:
            fence_start = raw_output.find("```")
            fence_end = raw_output.rfind("```")
            if fence_end > fence_start:
                possible = raw_output[fence_start + 3:fence_end]
                possible = possible.replace("json", "", 1).strip()
                raw_output = possible or raw_output

        structured_map = None
        markdown_content = ""

        try:
            parsed_payload = json.loads(raw_output)
            structured_map = _normalize_mindmap_payload(parsed_payload)
            markdown_content = _mindmap_to_markdown(structured_map)
        except Exception:
            # Fallback: treat response as markdown and parse
            structured_map = _parse_markdown_to_structure(raw_output)
            markdown_content = raw_output if raw_output.startswith("#") else _mindmap_to_markdown(structured_map)

        metadata = {
            "course_id": request.course_id,
            "book_id": request.book_id,
            "topic": topic,
            "focus_areas": request.focus_areas,
            "generated_at": datetime.now().isoformat(),
            "source_count": len(rag_response.get("sources", []))
        }

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
        raise HTTPException(status_code=500, detail=f"Error generating mindmap: {str(e)}")

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
