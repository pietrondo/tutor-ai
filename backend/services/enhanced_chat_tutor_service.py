"""
Enhanced Chat Tutor Service
Estende il sistema chat esistente con integrazione completa di note,
annotazioni PDF e RAG esteso a tutto il corso
"""

from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime, timedelta
import json
import uuid

from .course_chat_session import CourseChatSessionManager, SessionContextType, ChatMessage
from .pdf_annotation_service import PDFAnnotationService, Annotation
from .note_integration_service import NoteIntegrationService, LearningNote
from .rag_service import RAGService

class EnhancedChatTutorService:
    """
    Servizio chat tutor avanzato con integrazione completa
    """

    def __init__(self, rag_service: RAGService,
                 annotation_service: PDFAnnotationService,
                 note_service: NoteIntegrationService,
                 session_manager: CourseChatSessionManager,
                 ai_service):
        self.rag = rag_service
        self.annotations = annotation_service
        self.notes = note_service
        self.sessions = session_manager
        self.ai = ai_service

    async def process_message(self, user_id: str, course_id: str, session_id: Optional[str],
                            message: str, book_id: Optional[str] = None,
                            include_user_notes: bool = True,
                            include_course_context: bool = True) -> Dict[str, Any]:
        """
        Processa messaggio utente con contesto completo
        """
        start_time = datetime.now()

        # Recupera o crea sessione
        session = self.sessions.get_or_create_session(course_id, session_id)

        # Costruisci contesto esteso
        context = await self._build_comprehensive_context(
            user_id, course_id, message, book_id,
            include_user_notes, include_course_context
        )

        # Genera risposta AI
        ai_response = await self._generate_contextual_response(
            message, context, course_id, user_id
        )

        # Analizza risposta per estrarre metadati
        response_metadata = await self._analyze_response_metadata(
            message, ai_response, context
        )

        # Salva messaggio nella sessione
        response_time = (datetime.now() - start_time).total_seconds() * 1000

        chat_message = self.sessions.add_message(
            session.id, "assistant", ai_response["response"],
            sources=ai_response.get("sources", []),
            context_used=list(context.keys()),
            confidence_score=ai_response.get("confidence", 0.8),
            response_time_ms=int(response_time),
            topic_tags=response_metadata["topics"],
            is_followup=response_metadata["is_followup"]
        )

        # Crea automaticamente note se appropriato
        if response_metadata["should_create_note"]:
            await self._auto_create_note_from_conversation(
                user_id, course_id, message, ai_response["response"],
                response_metadata["topic_summary"]
            )

        # Aggiorna contesto sessione
        await self._update_session_context_with_new_info(
            session, message, ai_response["response"], response_metadata
        )

        return {
            "response": ai_response["response"],
            "sources": ai_response.get("sources", []),
            "session_id": session.id,
            "context_used": list(context.keys()),
            "confidence": ai_response.get("confidence", 0.8),
            "topics": response_metadata["topics"],
            "suggested_actions": response_metadata["suggested_actions"],
            "related_annotations": context.get("user_annotations", [])[:3]  # Top 3 annotations
        }

    async def _build_comprehensive_context(self, user_id: str, course_id: str,
                                         message: str, book_id: Optional[str] = None,
                                         include_user_notes: bool = True,
                                         include_course_context: bool = True) -> Dict[str, Any]:
        """
        Costruisce contesto completo per la risposta AI
        """
        context = {}

        # 1. Contesto RAG tradizionale (documenti del corso)
        if include_course_context:
            rag_context = await self.rag.retrieve_context(
                message, course_id, book_id, limit=5
            )
            context["course_materials"] = rag_context

        # 2. Note utente recenti e rilevanti
        if include_user_notes:
            user_notes = await self.notes.get_notes_for_chat_context(
                user_id, course_id, limit=8
            )
            context["user_notes"] = [note.dict() for note in user_notes]

        # 3. Annotazioni PDF recenti
        recent_annotations = await self.annotations.get_annotations_by_course(
            user_id, course_id
        )
        # Filtra annotazioni rilevanti per il messaggio
        relevant_annotations = await self._filter_relevant_annotations(
            recent_annotations, message
        )
        context["user_annotations"] = [ann.dict() for ann in relevant_annotations[:5]]

        # 4. Contesto sessione corrente
        if book_id:
            context["current_book"] = book_id

        # 5. Contesto storico della sessione
        session_context = self.sessions.get_session_context(
            self.sessions.get_or_create_session(course_id).id
        )
        if session_context:
            context["session_history"] = {
                "learning_style": session_context.get("learning_style", {}),
                "difficulty_level": session_context.get("difficulty_level", {}),
                "frequent_concepts": session_context.get("frequent_concepts", {}),
                "preferred_examples": session_context.get("preferred_examples", {})
            }

        return context

    async def _generate_contextual_response(self, message: str,
                                          context: Dict[str, Any],
                                          course_id: str, user_id: str) -> Dict[str, Any]:
        """
        Genera risposta AI usando contesto completo
        """
        # Costruisci prompt contestuale
        contextual_prompt = self._build_contextual_prompt(message, context, user_id)

        # Genera risposta usando servizio AI
        response = await self.ai.generate_response(
            contextual_prompt,
            course_id,
            include_sources=True,
            max_tokens=1000
        )

        # Estrai fonti e metadati
        sources = self._extract_sources_from_context(context)

        return {
            "response": response,
            "sources": sources,
            "confidence": self._calculate_response_confidence(context, response)
        }

    def _build_contextual_prompt(self, message: str, context: Dict[str, Any],
                               user_id: str) -> str:
        """
        Costruisce prompt contestuale per AI
        """
        prompt_parts = [
            f"Sei un tutor AI esperto per questo corso. L'utente {user_id} ti chiede:",
            f"DOMANDA: {message}\n"
        ]

        # Aggiungi contesto materiali del corso
        if context.get("course_materials"):
            prompt_parts.append("MATERIALE DI RIFERIMENTO:")
            for i, material in enumerate(context["course_materials"][:3], 1):
                prompt_parts.append(f"{i}. {material.get('text', '')[:200]}...")
            prompt_parts.append("")

        # Aggiungi note utente pertinenti
        if context.get("user_notes"):
            prompt_parts.append("NOTE PERSONALI DELL'UTENTE:")
            for note in context["user_notes"][:3]:
                prompt_parts.append(f"- {note.get('title', '')}: {note.get('content', '')[:150]}...")
            prompt_parts.append("")

        # Aggiungi annotazioni PDF pertinenti
        if context.get("user_annotations"):
            prompt_parts.append("ANNOTAZIONI PDF DELL'UTENTE:")
            for ann in context["user_annotations"][:3]:
                if ann.get("note_text"):
                    prompt_parts.append(f"- Pagina {ann.get('page_number', '?')}: {ann['note_text'][:100]}...")
            prompt_parts.append("")

        # Aggiungi contesto storico sessione
        if context.get("session_history"):
            history = context["session_history"]
            prompt_parts.append("PROFILO DI APPRENDIMENTO:")
            if history.get("learning_style"):
                style = history["learning_style"]
                prompt_parts.append(f"- Stile preferito: {style.get('preferred_format', 'explanations')}")
            if history.get("difficulty_level"):
                level = history["difficulty_level"]
                prompt_parts.append(f"- Livello corrente: {level.get('current_level', 'intermediate')}")
            prompt_parts.append("")

        # Istruzioni specifiche
        prompt_parts.extend([
            "ISTRUZIONI SPECIFICHE:",
            "1. Usa le informazioni fornite per dare una risposta contestuale e personalizzata",
            "2. Fai riferimento esplicito alle note e annotazioni dell'utente quando pertinenti",
            "3. Adatta il linguaggio e la complessità al profilo di apprendimento",
            "4. Se ci sono collegamenti tra materiali del corso e note personali, evidenziali",
            "5. Fornisci esempi pratici basati sul contenuto dei documenti",
            "\nRISPOSTA:"
        ])

        return "\n".join(prompt_parts)

    async def _filter_relevant_annotations(self, annotations: List[Annotation],
                                         query: str) -> List[Annotation]:
        """
        Filtra annotazioni rilevanti per la query corrente
        """
        if not annotations:
            return []

        # Semplice rilevanza basata su keywords
        query_words = set(query.lower().split())
        relevant = []

        for ann in annotations:
            score = 0

            # Controlla testo evidenziato
            if ann.text_content:
                text_words = set(ann.text_content.lower().split())
                score += len(query_words.intersection(text_words)) * 2

            # Controlla note utente
            if ann.note_text:
                note_words = set(ann.note_text.lower().split())
                score += len(query_words.intersection(note_words)) * 3

            # Controlla tag AI
            if ann.ai_generated_tags:
                tag_words = set(tag.lower() for tag in ann.ai_generated_tags)
                score += len(query_words.intersection(tag_words))

            if score > 0:
                relevant.append((ann, score))

        # Ordina per rilevanza e restituisci top results
        relevant.sort(key=lambda x: x[1], reverse=True)
        return [ann for ann, _ in relevant]

    async def _analyze_response_metadata(self, question: str, response: str,
                                        context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analizza la risposta per estrarre metadati utili
        """
        # Estrai topic principali
        topics = await self._extract_topics_from_response(response)

        # Determina se è un follow-up
        is_followup = await self._is_followup_question(question, context)

        # Valuta se creare nota automatica
        should_create_note = await self._should_auto_create_note(question, response, topics)

        # Genera riassunto topic
        topic_summary = None
        if should_create_note:
            topic_summary = await self._generate_topic_summary(question, response, topics)

        # Suggerisci azioni
        suggested_actions = await self._suggest_learning_actions(question, response, topics, context)

        return {
            "topics": topics,
            "is_followup": is_followup,
            "should_create_note": should_create_note,
            "topic_summary": topic_summary,
            "suggested_actions": suggested_actions
        }

    async def _auto_create_note_from_conversation(self, user_id: str, course_id: str,
                                                question: str, response: str,
                                                topic_summary: str):
        """
        Crea automaticamente nota da conversazione importante
        """
        note_data = {
            "user_id": user_id,
            "course_id": course_id,
            "title": f"Conversazione: {topic_summary[:50]}...",
            "content": f"**Domanda:** {question}\n\n**Risposta:** {response}",
            "tags": ["chat", "auto-generata"],
            "priority": "medium"
        }

        await self.notes.create_personal_note(note_data)

    async def _extract_topics_from_response(self, response: str) -> List[str]:
        """
        Estrae topic principali dalla risposta AI
        """
        prompt = f"Estrai 3-5 topic principali da questa risposta, separati da virgola:\n{response[:500]}"

        try:
            topics_response = await self.ai.generate_response(prompt, "")
            if topics_response:
                return [topic.strip() for topic in topics_response.split(",") if topic.strip()]
        except Exception:
            pass

        return []

    async def _is_followup_question(self, question: str, context: Dict[str, Any]) -> bool:
        """
        Determina se la domanda è un follow-up di conversazioni precedenti
        """
        followup_indicators = ["perché", "come", "spiegami meglio", "cioè", "quindi", "allora"]
        question_lower = question.lower()

        return any(indicator in question_lower for indicator in followup_indicators)

    async def _should_auto_create_note(self, question: str, response: str,
                                     topics: List[str]) -> bool:
        """
        Determina se creare automaticamente una nota dalla conversazione
        """
        # Crea nota se la risposta è lunga e contiene topic importanti
        if len(response) > 300 and len(topics) > 0:
            return True

        # Crea nota se la domanda contiene "spiegami" o simili
        question_indicators = ["spiegami", "come funziona", "perché", "definisci", "cos'è"]
        question_lower = question.lower()

        return any(indicator in question_lower for indicator in question_indicators)

    async def _generate_topic_summary(self, question: str, response: str,
                                    topics: List[str]) -> str:
        """
        Genera riassunto del topic per nota automatica
        """
        if topics:
            return ", ".join(topics[:3])

        # Fallback: usa prime parole della domanda
        return question[:50] + "..." if len(question) > 50 else question

    async def _suggest_learning_actions(self, question: str, response: str,
                                      topics: List[str], context: Dict[str, Any]) -> List[str]:
        """
        Suggerisce azioni di apprendimento basate sulla conversazione
        """
        actions = []

        # Se ci sono materiali correlati, suggerisci di leggerli
        if context.get("course_materials"):
            actions.append("📚 Rivedi i materiali di corso correlati")

        # Se ci sono note personali, suggerisci di rileggerle
        if context.get("user_notes"):
            actions.append("📝 Rileggi le tue note precedenti")

        # Se il topic è complesso, suggerisci esercizi
        if any(topic in ["formula", "calcolo", "problema", "esercizio"] for topic in topics):
            actions.append("🧪 Prova esercizi pratici su questo topic")

        # Se è un concetto importante, suggerisci annotazione
        if len(response) > 400:
            actions.append("📑 Annota i punti chiave nei tuoi materiali")

        return actions[:3]  # Max 3 suggerimenti

    def _extract_sources_from_context(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Estrae fonti dal contesto per citazione
        """
        sources = []

        # Fonti dai materiali del corso
        for material in context.get("course_materials", []):
            sources.append({
                "type": "course_material",
                "title": material.get("book_title", "Materiale del corso"),
                "page": material.get("page_number"),
                "relevance": material.get("relevance_score", 1.0)
            })

        # Fonti dalle annotazioni
        for ann in context.get("user_annotations", []):
            sources.append({
                "type": "user_annotation",
                "title": f"Annotazione pagina {ann.get('page_number', '?')}",
                "content": ann.get("note_text", "")[:100] + "...",
                "relevance": 0.8
            })

        return sources

    def _calculate_response_confidence(self, context: Dict[str, Any], response: str) -> float:
        """
        Calcola punteggio di confidenza della risposta
        """
        confidence = 0.5  # Base confidence

        # Aumenta se ci sono molte fonti
        if context.get("course_materials"):
            confidence += 0.2

        # Aumenta se ci sono note utente pertinenti
        if context.get("user_notes"):
            confidence += 0.15

        # Aumenta se ci sono annotazioni pertinenti
        if context.get("user_annotations"):
            confidence += 0.15

        return min(confidence, 1.0)

    async def _update_session_context_with_new_info(self, session, question: str,
                                                  response: str, metadata: Dict[str, Any]):
        """
        Aggiorna contesto sessione con nuove informazioni
        """
        # Aggiorna topic history
        for topic in metadata["topics"]:
            self.sessions.update_session_context(
                session.id,
                SessionContextType.TOPIC_HISTORY,
                {
                    "last_topic": topic,
                    "timestamp": datetime.now().isoformat()
                }
            )

        # Aggiorna frequent concepts
        if metadata["topics"]:
            self.sessions.update_session_context(
                session.id,
                SessionContextType.FREQUENT_CONCEPTS,
                {
                    "recent_concepts": metadata["topics"][-3:],  # Last 3 topics
                    "last_updated": datetime.now().isoformat()
                }
            )

    async def get_chat_summary(self, user_id: str, course_id: str,
                             session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Genera riassunto conversazione per adaptive learning
        """
        if not session_id:
            # Trova sessione attiva
            session = self.sessions.get_or_create_session(course_id)
            session_id = session.id
        else:
            session = self.sessions.load_session(session_id)
            if not session:
                return {"error": "Session not found"}

        # Estrai messaggi recenti
        recent_messages = session.messages[-10:]  # Last 10 messages

        # Genera riassunto con AI
        conversation_text = "\n".join([
            f"{msg.role}: {msg.content}" for msg in recent_messages
        ])

        summary_prompt = f"""
        Analizza questa conversazione e fornisci:
        1. Topic principali discussi
        2. Livello di comprensione mostrato
        3. Aree che potrebbero necessitare approfondimento
        4. Suggerimenti per il prossimo studio

        Conversazione:
        {conversation_text}
        """

        ai_summary = await self.ai.generate_response(summary_prompt, course_id)

        return {
            "session_id": session_id,
            "summary": ai_summary,
            "message_count": len(recent_messages),
            "session_duration": (session.last_activity - session.created_at).total_seconds(),
            "topics_discussed": list(set().union(*[msg.topic_tags for msg in recent_messages if msg.topic_tags])),
            "average_confidence": sum(msg.confidence_score for msg in recent_messages if msg.role == "assistant") / max(len([msg for msg in recent_messages if msg.role == "assistant"]), 1)
        }