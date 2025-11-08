"""
Enhanced Chat API Endpoints
API endpoints per il sistema chat avanzato con integrazione completa
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime
import asyncio

from ..services.enhanced_chat_tutor_service import EnhancedChatTutorService
from ..services.pdf_annotation_service import PDFAnnotationService, Annotation, AnnotationType, AnnotationColor
from ..services.note_integration_service import NoteIntegrationService, LearningNote, NoteType
from ..services.adaptive_learning_service import AdaptiveLearningService
from ..services.rag_service import RAGService
from ..services.llm_service import LLMService
from ..database.models import get_db

router = APIRouter(prefix="/api/chat", tags=["enhanced-chat"])

# Pydantic models
class ChatInitializeRequest(BaseModel):
    course_id: str
    user_id: str
    book_id: Optional[str] = None

class ChatMessageRequest(BaseModel):
    user_id: str
    course_id: str
    session_id: Optional[str] = None
    message: str
    book_id: Optional[str] = None
    include_user_notes: bool = True
    include_course_context: bool = True
    include_annotations: bool = True

class AnnotationCreateRequest(BaseModel):
    user_id: str
    course_id: str
    book_id: str
    page_number: int
    annotation_type: AnnotationType
    text_content: Optional[str] = None
    note_text: Optional[str] = None
    color: AnnotationColor = AnnotationColor.YELLOW
    position: Dict[str, Any]
    is_shared_with_chat: bool = True

class NoteCreateRequest(BaseModel):
    user_id: str
    course_id: str
    title: str
    content: str
    type: str
    tags: List[str] = []
    priority: str = "medium"

class GenerateTagsRequest(BaseModel):
    text: str
    course_id: str

class LearningProfileRequest(BaseModel):
    user_id: str
    course_id: str
    time_window_days: int = 30

# Dependency injection
async def get_enhanced_chat_service():
    """Inietta il servizio chat avanzato"""
    rag_service = RAGService()
    annotation_service = PDFAnnotationService(get_db(), LLMService())
    note_service = NoteIntegrationService(get_db(), LLMService(), rag_service)
    session_manager = CourseChatSessionManager()  # Importato dal modulo esistente
    ai_service = LLMService()

    return EnhancedChatTutorService(
        rag_service, annotation_service, note_service,
        session_manager, ai_service
    )

async def get_adaptive_learning_service():
    """Inietta il servizio adaptive learning"""
    return AdaptiveLearningService(get_db(), LLMService(), None)

# Endpoints Chat
@router.post("/initialize")
async def initialize_chat(
    request: ChatInitializeRequest,
    chat_service: EnhancedChatTutorService = Depends(get_enhanced_chat_service)
):
    """
    Inizializza una nuova sessione chat
    """
    try:
        # Genera messaggio di benvenuto personalizzato
        welcome_prompt = f"""
        Genera un messaggio di benvenuto personalizzato per un utente che inizia una sessione di studio.
        Il corso è: {request.course_id}
        {f'Sto studiando il libro: {request.book_id}' if request.book_id else ''}

        Il messaggio deve essere:
        - Accogliente e motivazionale
        - Breve (massimo 100 parole)
        - Suggerire come iniziare (fare domande, esplorare materiali)
        - Menzionare che il tutor userà note e annotazioni personali
        """

        ai_service = LLMService()
        welcome_message = await ai_service.generate_response(welcome_prompt, request.course_id)

        # Crea sessione
        session_manager = chat_service.sessions
        session = session_manager.get_or_create_session(request.course_id)

        return {
            "session_id": session.id,
            "welcome_message": welcome_message,
            "course_context": {
                "course_id": request.course_id,
                "book_id": request.book_id
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore inizializzazione chat: {str(e)}")

@router.post("/send")
async def send_message(
    request: ChatMessageRequest,
    background_tasks: BackgroundTasks,
    chat_service: EnhancedChatTutorService = Depends(get_enhanced_chat_service)
):
    """
    Invia messaggio alla chat e ottieni risposta contestuale
    """
    try:
        # Processa messaggio con contesto completo
        response = await chat_service.process_message(
            user_id=request.user_id,
            course_id=request.course_id,
            session_id=request.session_id,
            message=request.message,
            book_id=request.book_id,
            include_user_notes=request.include_user_notes,
            include_course_context=request.include_course_context
        )

        # Background task per aggiornare profilo adaptive learning
        background_tasks.add_task(
            update_adaptive_profile_from_chat,
            request.user_id,
            request.course_id,
            request.message,
            response
        )

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore processamento messaggio: {str(e)}")

@router.get("/session/{session_id}/summary")
async def get_chat_summary(
    session_id: str,
    user_id: str,
    course_id: str,
    chat_service: EnhancedChatTutorService = Depends(get_enhanced_chat_service)
):
    """
    Ottieni riassunto conversazione per adaptive learning
    """
    try:
        summary = await chat_service.get_chat_summary(
            user_id=user_id,
            course_id=course_id,
            session_id=session_id
        )

        return summary

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore generazione riassunto: {str(e)}")

# Endpoints Annotazioni PDF
@router.post("/books/{book_id}/annotations")
async def create_annotation(
    book_id: str,
    request: AnnotationCreateRequest,
    annotation_service: PDFAnnotationService = Depends(get_enhanced_chat_service)
):
    """
    Crea nuova annotazione PDF
    """
    try:
        annotation = Annotation(
            user_id=request.user_id,
            course_id=request.course_id,
            book_id=book_id,
            page_number=request.page_number,
            annotation_type=request.annotation_type,
            text_content=request.text_content,
            note_text=request.note_text,
            color=request.color,
            position=request.position,
            is_shared_with_chat=request.is_shared_with_chat
        )

        created_annotation = await annotation_service.create_annotation(annotation)

        return {
            "annotation": created_annotation.dict(),
            "message": "Annotazione creata con successo"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore creazione annotazione: {str(e)}")

@router.get("/books/{book_id}/annotations")
async def get_annotations(
    book_id: str,
    user_id: str,
    page_number: Optional[int] = None,
    annotation_service: PDFAnnotationService = Depends(get_enhanced_chat_service)
):
    """
    Recupera annotazioni PDF
    """
    try:
        if page_number:
            annotations = await annotation_service.get_annotations_by_page(
                user_id, book_id, page_number
            )
        else:
            annotations = await annotation_service.get_annotations_by_course(
                user_id, book_id.split('_')[0]  # Estrai course_id da book_id
            )

        return {
            "annotations": [ann.dict() for ann in annotations],
            "count": len(annotations)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore recupero annotazioni: {str(e)}")

@router.get("/books/{book_id}/annotations/recent")
async def get_recent_annotations(
    book_id: str,
    user_id: str,
    limit: int = 5,
    annotation_service: PDFAnnotationService = Depends(get_enhanced_chat_service)
):
    """
    Recupera annotazioni recenti per contesto chat
    """
    try:
        course_id = book_id.split('_')[0]
        all_annotations = await annotation_service.get_annotations_by_course(
            user_id, course_id
        )

        # Filtra per libro e ordina per data
        book_annotations = [
            ann for ann in all_annotations
            if ann.book_id == book_id
        ]

        # Ordina per created_at decrescente
        book_annotations.sort(key=lambda x: x.created_at, reverse=True)

        return {
            "annotations": [ann.dict() for ann in book_annotations[:limit]],
            "count": len(book_annotations[:limit])
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore recupero annotazioni recenti: {str(e)}")

@router.delete("/books/{book_id}/annotations/{annotation_id}")
async def delete_annotation(
    book_id: str,
    annotation_id: str,
    annotation_service: PDFAnnotationService = Depends(get_enhanced_chat_service)
):
    """
    Elimina annotazione PDF
    """
    try:
        success = await annotation_service.delete_annotation(annotation_id)

        if success:
            return {"message": "Annotazione eliminata con successo"}
        else:
            raise HTTPException(status_code=404, detail="Annotazione non trovata")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore eliminazione annotazione: {str(e)}")

@router.get("/books/{book_id}/annotations/export")
async def export_annotations(
    book_id: str,
    user_id: str,
    format: str = "json",
    annotation_service: PDFAnnotationService = Depends(get_enhanced_chat_service)
):
    """
    Esporta annotazioni in vari formati
    """
    try:
        course_id = book_id.split('_')[0]
        export_data = await annotation_service.export_annotations(
            user_id, course_id, format
        )

        return export_data

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore esportazione annotazioni: {str(e)}")

# Endpoints Note
@router.post("/notes")
async def create_note(
    request: NoteCreateRequest,
    note_service: NoteIntegrationService = Depends(get_enhanced_chat_service)
):
    """
    Crea nuova nota personale
    """
    try:
        note = await note_service.create_personal_note(request.dict())

        return {
            "note": note.dict(),
            "message": "Nota creata con successo"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore creazione nota: {str(e)}")

@router.post("/notes/from-chat")
async def create_note_from_chat(
    user_id: str,
    course_id: str,
    message_content: str,
    topics: List[str],
    session_id: Optional[str] = None,
    note_service: NoteIntegrationService = Depends(get_enhanced_chat_service)
):
    """
    Crea nota da conversazione chat
    """
    try:
        note_data = {
            "user_id": user_id,
            "course_id": course_id,
            "content": message_content,
            "title": f"Chat: {topics[0] if topics else 'Conversazione'}",
            "type": "chat_note",
            "tags": ["chat"] + topics,
            "priority": "medium"
        }

        note = await note_service.create_note_from_chat({
            **note_data,
            "session_id": session_id,
            "topic": topics[0] if topics else "generale",
            "timestamp": datetime.now().isoformat()
        })

        return {
            "note": note.dict(),
            "message": "Nota creata dalla conversazione"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore creazione nota da chat: {str(e)}")

@router.get("/notes/recent")
async def get_recent_notes(
    user_id: str,
    course_id: str,
    limit: int = 10,
    note_service: NoteIntegrationService = Depends(get_enhanced_chat_service)
):
    """
    Recupera note recenti per contesto
    """
    try:
        notes = await note_service.get_notes_for_chat_context(
            user_id, course_id, limit
        )

        return {
            "notes": [note.dict() for note in notes],
            "count": len(notes)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore recupero note recenti: {str(e)}")

@router.get("/notes/search")
async def search_notes(
    user_id: str,
    course_id: str,
    query: str,
    note_service: NoteIntegrationService = Depends(get_enhanced_chat_service)
):
    """
    Cerca note utente
    """
    try:
        notes = await note_service.search_notes(user_id, course_id, query)

        return {
            "notes": [note.dict() for note in notes],
            "count": len(notes),
            "query": query
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore ricerca note: {str(e)}")

@router.post("/learning/summary")
async def generate_learning_summary(
    user_id: str,
    course_id: str,
    period_days: int = 7,
    note_service: NoteIntegrationService = Depends(get_enhanced_chat_service)
):
    """
    Genera riassunto apprendimento periodico
    """
    try:
        summary = await note_service.generate_learning_summary(
            user_id, course_id, period_days
        )

        return summary

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore generazione riassunto: {str(e)}")

# Endpoints Adaptive Learning
@router.get("/learning/profile")
async def get_learning_profile(
    user_id: str,
    course_id: str,
    adaptive_service: AdaptiveLearningService = Depends(get_adaptive_learning_service)
):
    """
    Recupera profilo apprendimento utente
    """
    try:
        profile = await adaptive_service.analyze_user_behavior(user_id, course_id)

        return {
            "profile": profile.dict() if profile else None,
            "message": "Profilo apprendimento recuperato"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore recupero profilo: {str(e)}")

@router.get("/learning/recommendations")
async def get_learning_recommendations(
    user_id: str,
    course_id: str,
    adaptive_service: AdaptiveLearningService = Depends(get_adaptive_learning_service)
):
    """
    Ottieni raccomandazioni personalizzate
    """
    try:
        recommendations = await adaptive_service.get_personalized_recommendations(
            user_id, course_id
        )

        return recommendations

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore generazione raccomandazioni: {str(e)}")

@router.post("/learning/track")
async def track_learning_progress(
    user_id: str,
    course_id: str,
    event_data: Dict[str, Any],
    adaptive_service: AdaptiveLearningService = Depends(get_adaptive_learning_service)
):
    """
    Traccia evento di apprendimento e aggiorna profilo
    """
    try:
        tracking_result = await adaptive_service.track_learning_progress(
            user_id, course_id, event_data
        )

        return tracking_result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore tracciamento progresso: {str(e)}")

@router.get("/learning/spaced-repetition")
async def get_spaced_repetition_schedule(
    user_id: str,
    course_id: str,
    adaptive_service: AdaptiveLearningService = Depends(get_adaptive_learning_service)
):
    """
    Genera schedule per spaced repetition
    """
    try:
        schedule = await adaptive_service.generate_spaced_repetition_schedule(
            user_id, course_id
        )

        return {
            "schedule": schedule,
            "count": len(schedule)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore generazione schedule: {str(e)}")

# Endpoints AI
@router.post("/ai/generate-tags")
async def generate_tags_for_text(
    request: GenerateTagsRequest,
    ai_service: LLMService = Depends()
):
    """
    Genera tag automatici per testo
    """
    try:
        prompt = f"""
        Analizza questo testo e genera 3-5 tag rilevanti per l'apprendimento.
        I tag dovrebbero rappresentare concetti chiave, argomenti o categorie didattiche.

        Testo: "{request.text}"

        Rispondi solo con i tag separati da virgola, senza altro testo.
        """

        response = await ai_service.generate_response(prompt, request.course_id)

        if response:
            tags = [tag.strip() for tag in response.split(",") if tag.strip()]
            return {"tags": tags[:5]}  # Limita a 5 tag

        return {"tags": []}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore generazione tag: {str(e)}")

# Background tasks
async def update_adaptive_profile_from_chat(
    user_id: str,
    course_id: str,
    message: str,
    response: Dict[str, Any]
):
    """
    Background task per aggiornare profilo adaptive learning
    """
    try:
        adaptive_service = AdaptiveLearningService(get_db(), LLMService(), None)

        # Traccia evento chat
        await adaptive_service.track_learning_progress(
            user_id=user_id,
            course_id=course_id,
            learning_event={
                "type": "chat_session",
                "performance": {
                    "message_length": len(message),
                    "response_length": len(response.get("response", "")),
                    "confidence": response.get("confidence", 0.8)
                },
                "topics": response.get("topics", []),
                "difficulty": "intermediate",  # Da determinare in base al contenuto
                "duration_ms": response.get("response_time", 0)
            }
        )

    except Exception as e:
        print(f"Errore aggiornamento profilo adaptive: {e}")

# Import necessari
from ..services.course_chat_session import CourseChatSessionManager