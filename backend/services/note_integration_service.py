"""
Note Integration Service
Gestisce integrazione tra note utente, annotazioni PDF e chat tutor
con sistema di adaptive learning
"""

from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum
import json
import uuid
import re

class NoteType(str, Enum):
    PDF_ANNOTATION = "pdf_annotation"
    CHAT_NOTE = "chat_note"
    PERSONAL_NOTE = "personal_note"
    SUMMARY = "summary"
    QUESTION = "question"
    INSIGHT = "insight"

class NotePriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class LearningNote(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    course_id: str
    note_type: NoteType
    title: Optional[str] = None
    content: str
    source_reference: Optional[Dict[str, Any]] = None  # riferimento a PDF/chat
    tags: List[str] = []
    priority: NotePriority = NotePriority.MEDIUM
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    ai_generated_summary: Optional[str] = None
    learning_objectives: List[str] = []
    related_concepts: List[str] = []
    difficulty_level: Optional[int] = None  # 1-5
    mastery_level: Optional[int] = None    # 1-5
    is_archived: bool = False
    review_count: int = 0
    last_reviewed: Optional[datetime] = None

class NoteIntegrationService:
    """
    Servizio centrale per integrazione note con chat e adaptive learning
    """

    def __init__(self, db_service, ai_service, rag_service):
        self.db = db_service
        self.ai = ai_service
        self.rag = rag_service

    async def create_note_from_annotation(self, annotation_data: Dict[str, Any]) -> LearningNote:
        """
        Crea nota da annotazione PDF
        """
        note = LearningNote(
            user_id=annotation_data["user_id"],
            course_id=annotation_data["course_id"],
            note_type=NoteType.PDF_ANNOTATION,
            title=f"Nota da pagina {annotation_data['page_number']}",
            content=annotation_data.get("note_text", ""),
            source_reference={
                "type": "pdf_annotation",
                "book_id": annotation_data["book_id"],
                "page": annotation_data["page_number"],
                "highlighted_text": annotation_data.get("text_content", "")
            },
            tags=annotation_data.get("ai_generated_tags", [])
        )

        # Genera AI summary e learning objectives
        await self._enrich_note_with_ai(note)

        await self.db.save_note(note)
        return note

    async def create_note_from_chat(self, chat_data: Dict[str, Any]) -> LearningNote:
        """
        Crea nota da conversazione chat
        """
        note = LearningNote(
            user_id=chat_data["user_id"],
            course_id=chat_data["course_id"],
            note_type=NoteType.CHAT_NOTE,
            title=f"Spiegazione: {chat_data.get('topic', 'Argomento Chat')}",
            content=chat_data["content"],
            source_reference={
                "type": "chat_conversation",
                "chat_session_id": chat_data["session_id"],
                "timestamp": chat_data.get("timestamp"),
                "topic": chat_data.get("topic")
            }
        )

        # Estrae concetti e tag dalla conversazione
        await self._extract_concepts_from_chat(note, chat_data)
        await self._enrich_note_with_ai(note)

        await self.db.save_note(note)
        return note

    async def create_personal_note(self, note_data: Dict[str, Any]) -> LearningNote:
        """
        Crea nota personale manuale
        """
        note = LearningNote(
            user_id=note_data["user_id"],
            course_id=note_data["course_id"],
            note_type=NoteType.PERSONAL_NOTE,
            title=note_data.get("title", "Nota Personale"),
            content=note_data["content"],
            tags=note_data.get("tags", []),
            priority=NotePriority(note_data.get("priority", "medium"))
        )

        await self._enrich_note_with_ai(note)
        await self.db.save_note(note)
        return note

    async def get_notes_for_chat_context(self, user_id: str, course_id: str,
                                       limit: int = 10) -> List[LearningNote]:
        """
        Recupera note rilevanti per contesto chat
        """
        # Priorità: note recenti, priorità alta, non archiviate
        notes = await self.db.get_relevant_notes(user_id, course_id, limit)

        # Ordina per pertinenza usando AI
        if notes and len(notes) > 5:
            notes = await self._rank_notes_by_relevance(notes, course_id)

        return notes[:limit]

    async def search_notes(self, user_id: str, course_id: str, query: str) -> List[LearningNote]:
        """
        Cerca note con ricerca semantica
        """
        # Ricerca semantica usando RAG
        semantic_results = await self.rag.search_notes(query, user_id, course_id)

        # Ricerca testuale tradizionale
        text_results = await self.db.search_notes_textual(user_id, course_id, query)

        # Combina e deduplica risultati
        combined_results = self._combine_search_results(semantic_results, text_results)

        return combined_results

    async def generate_learning_summary(self, user_id: str, course_id: str,
                                      period_days: int = 7) -> Dict[str, Any]:
        """
        Genera riassunto apprendimento periodico
        """
        # Recupera note del periodo
        notes = await self.db.get_notes_by_period(user_id, course_id, period_days)

        # Analisi con AI
        summary_data = await self._analyze_learning_pattern(notes, course_id)

        # Crea nota di riepilogo
        summary_note = LearningNote(
            user_id=user_id,
            course_id=course_id,
            note_type=NoteType.SUMMARY,
            title=f"Riepilogo Settimanale - {datetime.now().strftime('%Y-%m-%d')}",
            content=summary_data["summary_text"],
            tags=["riepilogo", "settimanale", "auto-generato"],
            ai_generated_summary=summary_data["summary_text"]
        )

        await self.db.save_note(summary_note)

        return {
            "summary_note": summary_note,
            "analytics": summary_data["analytics"],
            "recommendations": summary_data["recommendations"]
        }

    async def update_note_mastery(self, note_id: str, mastery_level: int) -> LearningNote:
        """
        Aggiorna livello di padronanza nota
        """
        note = await self.db.get_note(note_id)
        note.mastery_level = mastery_level
        note.review_count += 1
        note.last_reviewed = datetime.now()
        note.updated_at = datetime.now()

        await self.db.update_note(note)

        # Aggiorna sistema adaptive learning
        await self._update_adaptive_learning_profile(note.user_id, note.course_id)

        return note

    async def _enrich_note_with_ai(self, note: LearningNote):
        """
        Arricchisce nota con analisi AI
        """
        prompt = f"""
        Analizza questa nota di apprendimento e fornisci:
        1. Un breve riassunto (massimo 50 parole)
        2. 2-3 obiettivi di apprendimento chiave
        3. Concetti correlati importanti
        4. Livello di difficoltà (1-5)

        Nota: "{note.content}"

        Rispondi in formato JSON:
        {{
            "summary": "...",
            "objectives": ["...", "..."],
            "related_concepts": ["...", "..."],
            "difficulty_level": 3
        }}
        """

        try:
            response = await self.ai.generate_response(prompt, note.course_id)
            if response:
                ai_data = json.loads(response)
                note.ai_generated_summary = ai_data.get("summary", "")
                note.learning_objectives = ai_data.get("objectives", [])
                note.related_concepts = ai_data.get("related_concepts", [])
                note.difficulty_level = ai_data.get("difficulty_level", 3)
        except Exception as e:
            print(f"Error enriching note with AI: {e}")

    async def _extract_concepts_from_chat(self, note: LearningNote, chat_data: Dict[str, Any]):
        """
        Estrae concetti chiave da conversazione chat
        """
        # Usa RAG per estrarre concetti
        concepts = await self.rag.extract_concepts_from_text(
            chat_data["content"],
            note.course_id
        )
        note.related_concepts = concepts

    async def _rank_notes_by_relevance(self, notes: List[LearningNote],
                                     course_id: str) -> List[LearningNote]:
        """
        Ordina note per pertinenza usando AI
        """
        # Implementazione ordinamento basato su pertinenza
        # Considera: recentità, priorità, pertinenza semantica
        return sorted(notes, key=lambda x: (
            x.priority.value,  # Priorità alta prima
            x.updated_at,      # Più recenti prima
            x.review_count     # Meno riviste prima (spaced repetition)
        ), reverse=True)

    def _combine_search_results(self, semantic: List[LearningNote],
                              textual: List[LearningNote]) -> List[LearningNote]:
        """
        Combina risultati ricerca semantica e testuale
        """
        seen_ids = set()
        combined = []

        # Priorità a risultati semantici
        for note in semantic:
            if note.id not in seen_ids:
                combined.append(note)
                seen_ids.add(note.id)

        # Aggiungi risultati testuali non duplicati
        for note in textual:
            if note.id not in seen_ids:
                combined.append(note)
                seen_ids.add(note.id)

        return combined

    async def _analyze_learning_pattern(self, notes: List[LearningNote],
                                      course_id: str) -> Dict[str, Any]:
        """
        Analizza pattern di apprendimento da note
        """
        if not notes:
            return {
                "summary_text": "Nessuna attività di apprendimento registrata questa settimana.",
                "analytics": {},
                "recommendations": []
            }

        # Statistiche base
        total_notes = len(notes)
        avg_difficulty = sum(n.difficulty_level or 3 for n in notes) / total_notes
        note_types = {}
        tags_frequency = {}

        for note in notes:
            # Conteggio tipi
            note_types[note.note_type.value] = note_types.get(note.note_type.value, 0) + 1

            # Frequenza tag
            for tag in note.tags:
                tags_frequency[tag] = tags_frequency.get(tag, 0) + 1

        # Genera riassunto con AI
        prompt = f"""
        Basati su queste statistiche di apprendimento della settimana:
        - Note totali: {total_notes}
        - Difficoltà media: {avg_difficulty:.1f}
        - Tipi di note: {note_types}
        - Tag più comuni: {dict(sorted(tags_frequency.items(), key=lambda x: x[1], reverse=True)[:5])}

        Genera un riassunto personale dei progressi e 2-3 raccomandazioni per migliorare.
        """

        response = await self.ai.generate_response(prompt, course_id)

        return {
            "summary_text": response or "Riepilogo apprendimento settimanale.",
            "analytics": {
                "total_notes": total_notes,
                "avg_difficulty": avg_difficulty,
                "note_types": note_types,
                "top_tags": dict(sorted(tags_frequency.items(), key=lambda x: x[1], reverse=True)[:5])
            },
            "recommendations": []  # Estratte dalla risposta AI
        }

    async def _update_adaptive_learning_profile(self, user_id: str, course_id: str):
        """
        Aggiorna profilo adaptive learning basato sulle note
        """
        # Implementazione aggiornamento profilo utente
        # per sistema adaptive learning
        pass

class NoteDBService:
    """
    Servizio database per persistenza note
    """

    async def save_note(self, note: LearningNote):
        """Salva nota nel database"""
        pass

    async def get_note(self, note_id: str) -> Optional[LearningNote]:
        """Recupera nota specifica"""
        pass

    async def get_relevant_notes(self, user_id: str, course_id: str,
                                limit: int) -> List[LearningNote]:
        """Recupera note rilevanti"""
        pass

    async def search_notes_textual(self, user_id: str, course_id: str,
                                  query: str) -> List[LearningNote]:
        """Ricerca testuale note"""
        pass

    async def get_notes_by_period(self, user_id: str, course_id: str,
                                 days: int) -> List[LearningNote]:
        """Recupera note per periodo"""
        pass

    async def update_note(self, note: LearningNote):
        """Aggiorna nota esistente"""
        pass

    async def delete_note(self, note_id: str) -> bool:
        """Elimina nota"""
        pass