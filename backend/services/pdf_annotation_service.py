"""
PDF Annotation Service
Gestisce annotazioni, sottolineature e note sui documenti PDF
con sincronizzazione con chat e sistema adaptive learning
"""

from typing import List, Dict, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum
import json
import uuid

class AnnotationType(str, Enum):
    HIGHLIGHT = "highlight"
    UNDERLINE = "underline"
    NOTE = "note"
    BOOKMARK = "bookmark"
    COMMENT = "comment"

class AnnotationColor(str, Enum):
    YELLOW = "#FFEB3B"
    GREEN = "#4CAF50"
    BLUE = "#2196F3"
    RED = "#F44336"
    PURPLE = "#9C27B0"
    ORANGE = "#FF9800"

class Annotation(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    course_id: str
    book_id: str
    page_number: int
    annotation_type: AnnotationType
    text_content: Optional[str] = None  # testo selezionato
    note_text: Optional[str] = None    # nota utente
    color: AnnotationColor = AnnotationColor.YELLOW
    position: Dict[str, Any]           # coords, dimensions
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    is_shared_with_chat: bool = False  # se condivisa con chat tutor
    ai_generated_tags: List[str] = []  # tag generati da AI
    learning_context: Optional[str] = None  # contesto apprendimento

class PDFAnnotationService:
    """
    Servizio per gestire annotazioni PDF con integrazione AI
    """

    def __init__(self, db_service, ai_service):
        self.db = db_service
        self.ai = ai_service

    async def create_annotation(self, annotation: Annotation) -> Annotation:
        """
        Crea nuova annotazione con tagging AI automatico
        """
        # Genera tag automatici con AI
        if annotation.text_content:
            annotation.ai_generated_tags = await self._generate_ai_tags(
                annotation.text_content,
                annotation.course_id
            )

        # Salva nel database
        await self.db.save_annotation(annotation)

        # Se condivisa con chat, aggiorna contesto sessione
        if annotation.is_shared_with_chat:
            await self._update_chat_context(annotation)

        return annotation

    async def get_annotations_by_page(self, user_id: str, book_id: str, page_number: int) -> List[Annotation]:
        """
        Recupera annotazioni per pagina specifica
        """
        return await self.db.get_annotations(user_id, book_id, page_number)

    async def get_annotations_by_course(self, user_id: str, course_id: str) -> List[Annotation]:
        """
        Recupera tutte le annotazioni utente per un corso
        """
        return await self.db.get_annotations_by_course(user_id, course_id)

    async def update_annotation(self, annotation_id: str, updates: Dict[str, Any]) -> Annotation:
        """
        Aggiorna annotazione esistente
        """
        annotation = await self.db.get_annotation(annotation_id)
        for key, value in updates.items():
            setattr(annotation, key, value)

        annotation.updated_at = datetime.now()
        await self.db.update_annotation(annotation)

        # Aggiorna contesto chat se necessario
        if annotation.is_shared_with_chat:
            await self._update_chat_context(annotation)

        return annotation

    async def delete_annotation(self, annotation_id: str) -> bool:
        """
        Elimina annotazione
        """
        return await self.db.delete_annotation(annotation_id)

    async def search_annotations(self, user_id: str, course_id: str, query: str) -> List[Annotation]:
        """
        Cerca annotazioni per contenuto testo o note
        """
        return await self.db.search_annotations(user_id, course_id, query)

    async def export_annotations(self, user_id: str, course_id: str, format: str = "json") -> Dict[str, Any]:
        """
        Esporta annotazioni in vari formati
        """
        annotations = await self.get_annotations_by_course(user_id, course_id)

        if format == "json":
            return {"annotations": [ann.dict() for ann in annotations]}
        elif format == "markdown":
            return self._export_to_markdown(annotations)

        return {"annotations": []}

    async def _generate_ai_tags(self, text: str, course_id: str) -> List[str]:
        """
        Genera tag automatici usando AI basata sul contenuto
        """
        prompt = f"""
        Analizza questo testo estratto da un documento di studio e genera 3-5 tag rilevanti.
        I tag dovrebbero rappresentare concetti chiave, argomenti o categorie didattiche.

        Testo: "{text}"

        Rispondi solo con i tag separati da virgola, senza altro testo.
        """

        response = await self.ai.generate_response(prompt, course_id)
        if response:
            tags = [tag.strip() for tag in response.split(",") if tag.strip()]
            return tags[:5]  # Limita a 5 tag

        return []

    async def _update_chat_context(self, annotation: Annotation):
        """
        Aggiorna contesto chat con nuova annotazione
        """
        from .course_chat_session import CourseChatSession

        # Recupera sessione attiva per il corso
        session = await CourseChatSession.get_active_session(
            annotation.user_id,
            annotation.course_id
        )

        if session:
            # Aggiunge annotazione al contesto della sessione
            context_note = {
                "type": "pdf_annotation",
                "book_id": annotation.book_id,
                "page": annotation.page_number,
                "text": annotation.text_content,
                "note": annotation.note_text,
                "tags": annotation.ai_generated_tags,
                "created_at": annotation.created_at.isoformat()
            }

            session.context["user_annotations"].append(context_note)
            await session.save()

    def _export_to_markdown(self, annotations: List[Annotation]) -> Dict[str, str]:
        """
        Converte annotazioni in formato markdown
        """
        markdown_content = "# 📝 Note ed Annotazioni\n\n"

        # Raggruppa per libro
        by_book = {}
        for ann in annotations:
            if ann.book_id not in by_book:
                by_book[ann.book_id] = []
            by_book[ann.book_id].append(ann)

        for book_id, book_anns in by_book.items():
            markdown_content += f"## 📖 Libro: {book_id}\n\n"

            # Raggruppa per pagina
            by_page = {}
            for ann in book_anns:
                if ann.page_number not in by_page:
                    by_page[ann.page_number] = []
                by_page[ann.page_number].append(ann)

            for page, page_anns in sorted(by_page.items()):
                markdown_content += f"### Pagina {page}\n\n"

                for ann in page_anns:
                    if ann.text_content:
                        markdown_content += f"**Testo:** {ann.text_content}\n\n"

                    if ann.note_text:
                        markdown_content += f"**Nota:** {ann.note_text}\n\n"

                    if ann.ai_generated_tags:
                        markdown_content += f"**Tag:** {', '.join(ann.ai_generated_tags)}\n\n"

                    markdown_content += f"**Data:** {ann.created_at.strftime('%Y-%m-%d %H:%M')}\n\n"
                    markdown_content += "---\n\n"

        return {"markdown": markdown_content}

# Database integration
class AnnotationDBService:
    """
    Servizio database per persistenza annotazioni
    """

    async def save_annotation(self, annotation: Annotation):
        """
        Salva annotazione nel database
        """
        # Implementazione con SQLite/PostgreSQL
        pass

    async def get_annotations(self, user_id: str, book_id: str, page_number: int) -> List[Annotation]:
        """
        Recupera annotazioni per pagina
        """
        # Implementazione query database
        pass

    async def get_annotations_by_course(self, user_id: str, course_id: str) -> List[Annotation]:
        """
        Recupera annotazioni per corso
        """
        # Implementazione query database
        pass

    async def update_annotation(self, annotation: Annotation):
        """
        Aggiorna annotazione esistente
        """
        # Implementazione update database
        pass

    async def delete_annotation(self, annotation_id: str) -> bool:
        """
        Elimina annotazione
        """
        # Implementazione delete database
        pass

    async def search_annotations(self, user_id: str, course_id: str, query: str) -> List[Annotation]:
        """
        Cerca annotazioni
        """
        # Implementazione ricerca full-text
        pass

    async def get_annotation(self, annotation_id: str) -> Optional[Annotation]:
        """
        Recupera annotazione specifica
        """
        # Implementazione get by ID
        pass