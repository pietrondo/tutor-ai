"""
Course-Specific RAG Service
Enhanced RAG system with course-aware retrieval and personalization
"""

import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timezone
import json
import re
from collections import Counter
import numpy as np

from services.rag_service import RAGService
from services.course_chat_session import course_chat_session_manager, SessionContextType
from services.llm_service import LLMService
from services.spaced_repetition_service import spaced_repetition_service
from services.active_recall_service import active_recall_engine

class CourseRAGService:
    """Enhanced RAG service specifically designed for course-specific chatbot"""

    def __init__(self, rag_service: RAGService, llm_service: LLMService):
        self.rag_service = rag_service
        self.llm_service = llm_service
        self.session_manager = course_chat_session_manager

        # Configuration
        self.default_retrieval_k = 5
        self.max_context_sources = 3
        self.personalization_weight = 0.3
        self.session_context_weight = 0.2

    async def retrieve_context_enhanced(
        self,
        course_id: str,
        session_id: str,
        query: str,
        book_id: Optional[str] = None,
        retrieval_k: int = None
    ) -> Dict[str, Any]:
        """
        Enhanced context retrieval with personalization and session awareness
        """
        try:
            retrieval_k = retrieval_k or self.default_retrieval_k

            # Phase 1: Base RAG retrieval
            base_context = await self.rag_service.retrieve_context(
                query=query,
                course_id=course_id,
                book_id=book_id,
                k=retrieval_k
            )

            # Phase 2: Session-aware retrieval
            session_context_sources = await self._retrieve_session_context(
                course_id, session_id, query, book_id
            )

            # Phase 3: Personalized retrieval based on learning patterns
            personalized_sources = await self._retrieve_personalized_content(
                course_id, session_id, query, book_id
            )

            # Phase 4: Combine and rank sources
            all_sources = (
                base_context.get("sources", []) +
                session_context_sources +
                personalized_sources
            )

            # Remove duplicates and rank
            unique_sources = self._deduplicate_sources(all_sources)
            ranked_sources = self._rank_sources_with_context(
                unique_sources, course_id, session_id, query
            )

            # Phase 5: Build final context
            final_context = self._build_enhanced_context(
                ranked_sources,
                course_id,
                session_id,
                query,
                base_context
            )

            return final_context

        except Exception as e:
            print(f"Error in enhanced context retrieval: {e}")
            # Fallback to basic RAG
            return await self.rag_service.retrieve_context(
                query=query,
                course_id=course_id,
                book_id=book_id,
                k=retrieval_k
            )

    async def _retrieve_session_context(
        self,
        course_id: str,
        session_id: str,
        query: str,
        book_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant context from session history"""
        try:
            # Get conversation history
            conversation_history = self.session_manager.get_conversation_history(session_id, limit=20)

            # Get session context
            topic_history = self.session_manager.get_session_context(
                session_id, SessionContextType.TOPIC_HISTORY
            )

            concept_map = self.session_manager.get_session_context(
                session_id, SessionContextType.CONCEPT_MAP
            )

            study_progress = self.session_manager.get_session_context(
                session_id, SessionContextType.STUDY_PROGRESS
            )

            # Extract key concepts from query
            query_concepts = self._extract_concepts_from_query(query)

            # Find related topics from history
            related_topics = set()
            if topic_history:
                for topic in topic_history.get("topic_frequency", {}):
                    if any(concept.lower() in topic.lower() for concept in query_concepts):
                        related_topics.add(topic)

            # Create context sources from session information
            context_sources = []

            # Add recently discussed topics
            for topic in related_topics:
                last_discussed = topic_history.get("last_discussed", {}).get(topic, "")
                if last_discussed:
                    context_sources.append({
                        "type": "session_topic",
                        "content": f"Argomento discusso precedentemente: {topic}",
                        "timestamp": last_discussed,
                        "relevance_score": 0.8,
                        "source_type": "conversation_history"
                    })

            # Add concept relationships
            if concept_map and query_concepts:
                relationships = concept_map.get("relationships", {})
                for relationship_key, strength in relationships.items():
                    source_concept, target_concept = relationship_key.split("->", 1)
                    if source_concept in query_concepts or target_concept in query_concepts:
                        context_sources.append({
                            "type": "concept_relationship",
                            "content": f"Relazione concettuale: {relationship_key} (forza: {strength})",
                            "relevance_score": min(0.9, strength / 10),
                            "source_type": "concept_map"
                        })

            # Add study progress context
            if study_progress:
                mastery_levels = study_progress.get("mastery_levels", {})
                for concept in query_concepts:
                    if concept in mastery_levels:
                        level = mastery_levels[concept]
                        context_sources.append({
                            "type": "mastery_level",
                            "content": f"Livello di padronanza per '{concept}': {level}",
                            "relevance_score": 0.7,
                            "source_type": "study_progress"
                        })

            return context_sources[:3]  # Limit session context sources

        except Exception as e:
            print(f"Error retrieving session context: {e}")
            return []

    async def _retrieve_personalized_content(
        self,
        course_id: str,
        session_id: str,
        query: str,
        book_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve content personalized to user's learning patterns"""
        try:
            # Get user learning preferences
            learning_style = self.session_manager.get_session_context(
                session_id, SessionContextType.LEARNING_STYLE
            )

            difficulty_level = self.session_manager.get_session_context(
                session_id, SessionContextType.DIFFICULTY_LEVEL
            )

            preferred_examples = self.session_manager.get_session_context(
                session_id, SessionContextType.PREFERRED_EXAMPLES
            )

            # Get base RAG results for personalization
            base_results = await self.rag_service.retrieve_context(
                query=query,
                course_id=course_id,
                book_id=book_id,
                k=10  # Get more for personalization
            )

            personalized_sources = []

            for source in base_results.get("sources", []):
                # Score based on learning preferences
                personalized_score = self._calculate_personalization_score(
                    source, learning_style, difficulty_level, preferred_examples, query
                )

                if personalized_score > 0.5:  # Only keep highly relevant personalized content
                    personalized_source = source.copy()
                    personalized_source["personalization_score"] = personalized_score
                    personalized_source["personalization_factors"] = self._get_personalization_factors(
                        source, learning_style, difficulty_level, preferred_examples
                    )
                    personalized_sources.append(personalized_source)

            return personalized_sources

        except Exception as e:
            print(f"Error retrieving personalized content: {e}")
            return []

    def _extract_concepts_from_query(self, query: str) -> List[str]:
        """Extract key concepts from user query"""
        # Simple concept extraction - can be enhanced with NLP
        concepts = []

        # Remove common words and extract potential concepts
        stop_words = {"il", "lo", "la", "i", "gli", "le", "un", "una", "di", "in", "con", "per", "che", "è", "come", "quando", "dove", "perché"}

        words = re.findall(r'\b\w+\b', query.lower())

        # Filter out stop words and keep meaningful words
        for word in words:
            if word not in stop_words and len(word) > 2:
                concepts.append(word)

        return list(set(concepts))  # Remove duplicates

    def _deduplicate_sources(self, sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate sources while preserving highest scores"""
        seen_sources = {}
        unique_sources = []

        for source in sources:
            # Create a unique key based on content or document
            source_key = source.get("content", "")[:100]  # First 100 chars as key

            if source_key not in seen_sources:
                seen_sources[source_key] = source
                unique_sources.append(source)
            else:
                # Keep the one with higher relevance score
                existing_score = seen_sources[source_key].get("relevance_score", 0)
                new_score = source.get("relevance_score", 0)
                if new_score > existing_score:
                    seen_sources[source_key] = source
                    # Replace in unique_sources
                    for i, s in enumerate(unique_sources):
                        if s.get("content", "")[:100] == source_key:
                            unique_sources[i] = source
                            break

        return unique_sources

    def _rank_sources_with_context(
        self,
        sources: List[Dict[str, Any]],
        course_id: str,
        session_id: str,
        query: str
    ) -> List[Dict[str, Any]]:
        """Rank sources considering session context and query relevance"""
        ranked_sources = []

        for source in sources:
            base_score = source.get("relevance_score", 0.5)
            personalization_score = source.get("personalization_score", 0)
            session_score = source.get("session_relevance_score", 0)

            # Calculate final weighted score
            final_score = (
                base_score * 0.5 +
                personalization_score * 0.3 +
                session_score * 0.2
            )

            source["final_rank_score"] = final_score
            ranked_sources.append(source)

        # Sort by final score
        ranked_sources.sort(key=lambda x: x["final_rank_score"], reverse=True)

        return ranked_sources

    def _build_enhanced_context(
        self,
        sources: List[Dict[str, Any]],
        course_id: str,
        session_id: str,
        query: str,
        base_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build enhanced context with multiple layers"""

        # Limit sources for context window
        limited_sources = sources[:self.max_context_sources]

        # Separate different types of sources
        document_sources = [s for s in limited_sources if s.get("source_type") == "document"]
        session_sources = [s for s in limited_sources if s.get("source_type") in ["conversation_history", "concept_map", "study_progress"]]
        personalized_sources = [s for s in limited_sources if s.get("personalization_score", 0) > 0.5]

        # Build context layers
        context_layers = {
            "primary": {
                "description": "Contenido principale dai documenti del corso",
                "sources": document_sources[:2],
                "weight": 0.6
            },
            "secondary": {
                "description": "Contesto personalizzato e della sessione",
                "sources": session_sources[:2] + personalized_sources[:1],
                "weight": 0.3
            },
            "supporting": {
                "description": "Informazioni di supporto aggiuntive",
                "sources": limited_sources[2:5],
                "weight": 0.1
            }
        }

        # Build final context
        context_text_parts = []
        all_sources = []

        for layer_name, layer_info in context_layers.items():
            layer_sources = layer_info["sources"]
            if layer_sources:
                for source in layer_sources:
                    all_sources.append(source)
                    if source.get("type") == "session_topic":
                        context_text_parts.append(f"**Contesto Sessione**: {source['content']}")
                    elif source.get("type") == "concept_relationship":
                        context_text_parts.append(f"**Relazione Concettuale**: {source['content']}")
                    elif source.get("type") == "mastery_level":
                        context_text_parts.append(f"**Progresso Apprendimento**: {source['content']}")
                    else:
                        context_text_parts.append(source.get("content", ""))

        context_text = "\n\n".join(context_text_parts)

        return {
            "sources": all_sources,
            "context": context_text,
            "context_layers": context_layers,
            "retrieval_method": "enhanced_course_rag",
            "personalization_applied": len(personalized_sources) > 0,
            "session_context_used": len(session_sources) > 0,
            "total_sources_considered": len(sources),
            "context_metadata": {
                "course_id": course_id,
                "session_id": session_id,
                "query": query,
                "generation_timestamp": datetime.now(timezone.utc).isoformat()
            }
        }

    def _calculate_personalization_score(
        self,
        source: Dict[str, Any],
        learning_style: Dict[str, Any],
        difficulty_level: Dict[str, Any],
        preferred_examples: Dict[str, Any],
        query: str
    ) -> float:
        """Calculate how well a source matches user's personalization preferences"""
        score = 0.5  # Base score

        # Learning style matching
        if learning_style:
            preferred_format = learning_style.get("preferred_format", "explanations")
            if "spiegazione" in source.get("content", "").lower():
                score += 0.2 if preferred_format == "explanations" else 0.1
            elif "esempio" in source.get("content", "").lower():
                score += 0.2 if preferred_format == "examples" else 0.1

        # Difficulty level matching
        if difficulty_level:
            current_level = difficulty_level.get("current_level", "intermediate")
            if "avanzato" in source.get("content", "").lower() and current_level == "advanced":
                score += 0.2
            elif "base" in source.get("content", "").lower() and current_level == "beginner":
                score += 0.2

        # Preferred examples matching
        if preferred_examples:
            example_types = preferred_examples.get("types", [])
            if "reale" in example_types and "reale" in source.get("content", "").lower():
                score += 0.1
            elif "accademico" in example_types and "teoria" in source.get("content", "").lower():
                score += 0.1

        return min(1.0, score)

    def _get_personalization_factors(
        self,
        source: Dict[str, Any],
        learning_style: Dict[str, Any],
        difficulty_level: Dict[str, Any],
        preferred_examples: Dict[str, Any]
    ) -> List[str]:
        """Get list of personalization factors that matched"""
        factors = []

        if "spiegazione" in source.get("content", "").lower():
            factors.append("explanation_format_match")

        if learning_style and learning_style.get("preferred_format") == "explanations":
            factors.append("learning_style_match")

        return factors

    async def auto_generate_cards_from_conversation(
        self,
        course_id: str,
        session_id: str,
        max_cards: int = 5
    ) -> List[str]:
        """
        Auto-generate learning cards from conversation history
        """
        try:
            # Get conversation history
            conversation_history = self.session_manager.get_conversation_history(
                session_id, limit=10
            )

            # Extract Q&A pairs from conversation
            qa_pairs = []
            for i, message in enumerate(conversation_history):
                if message["role"] == "user" and i + 1 < len(conversation_history):
                    next_message = conversation_history[i + 1]
                    if next_message["role"] == "assistant":
                        qa_pairs.append({
                            "question": message["content"],
                            "answer": next_message["content"]
                        })

            # Generate cards from Q&A pairs
            card_ids = []
            for qa_pair in qa_pairs[:max_cards]:
                # Clean and format the content
                question = self._format_card_content(qa_pair["question"], is_question=True)
                answer = self._format_card_content(qa_pair["answer"], is_question=False)

                if len(question) > 20 and len(answer) > 20:  # Only create cards with meaningful content
                    try:
                        card_id = spaced_repetition_service.create_card(
                            course_id=course_id,
                            question=question,
                            answer=answer,
                            card_type="conversation",
                            context_tags=["auto_generated", "chat_derived"],
                            source_material=f"Chat Session: {session_id}"
                        )
                        card_ids.append(card_id)
                    except Exception as e:
                        print(f"Error creating card from conversation: {e}")
                        continue

            return card_ids

        except Exception as e:
            print(f"Error auto-generating cards from conversation: {e}")
            return []

    def _format_card_content(self, content: str, is_question: bool = True) -> str:
        """
        Format content for learning cards
        """
        # Remove citations and references
        content = re.sub(r'\[\d+\]', '', content)
        content = re.sub(r'\([^)]*\)', '', content)

        # Clean up whitespace
        content = re.sub(r'\s+', ' ', content).strip()

        # Truncate if too long
        max_length = 800 if is_question else 1200
        if len(content) > max_length:
            content = content[:max_length] + "..."

        return content

    async def generate_cards_from_sources(
        self,
        course_id: str,
        sources: List[Dict[str, Any]],
        max_cards: int = 10
    ) -> List[str]:
        """
        Generate learning cards from RAG sources
        """
        try:
            card_ids = []

            for source in sources[:max_cards]:
                if source.get("content") and len(source["content"]) > 50:
                    # Generate question from content
                    content = source["content"]

                    # Extract key concepts for question generation
                    question = self._generate_question_from_content(content)

                    if question and len(question) > 10:
                        card_id = spaced_repetition_service.create_card(
                            course_id=course_id,
                            question=question,
                            answer=content[:800] + ("..." if len(content) > 800 else ""),
                            card_type="material_based",
                            context_tags=["auto_generated", "rag_derived"],
                            source_material=source.get("source", "Unknown")
                        )
                        card_ids.append(card_id)

            return card_ids

        except Exception as e:
            print(f"Error generating cards from sources: {e}")
            return []

    def _generate_question_from_content(self, content: str) -> str:
        """
        Generate a question from content using simple heuristics
        """
        sentences = content.split('.')

        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 20:
                continue

            # Look for definitional or explanatory content
            sentence_lower = sentence.lower()

            if any(indicator in sentence_lower for indicator in [
                'definisce', 'significa', 'rappresent', 'è', 'sono', 'descrive'
            ]):
                # Extract the main subject
                words = sentence.split()
                if len(words) > 3:
                    subject = words[0]
                    return f"Cos'è {subject}?"

            if any(indicator in sentence_lower for indicator in [
                'perché', 'come', 'quando', 'dove', 'chi'
            ]):
                return sentence + "?"

        # Fallback: create generic question
        if len(content) > 100:
            return "Spiega i concetti principali di questo passaggio."

        return ""

    async def auto_generate_questions_from_conversation(
        self,
        course_id: str,
        session_id: str,
        max_questions: int = 5
    ) -> List[str]:
        """
        Auto-generate Active Recall questions from conversation history
        """
        try:
            from models.active_recall import QuestionGenerationRequest

            # Get conversation history
            conversation_history = self.session_manager.get_conversation_history(
                session_id, limit=8
            )

            # Extract content from conversation
            content_segments = []
            for message in conversation_history:
                if message["role"] == "assistant":
                    content_segments.append(message["content"])
                elif message["role"] == "user" and len(message["content"]) > 50:
                    content_segments.append(f"Domanda studente: {message['content']}")

            # Combine relevant content
            combined_content = "\n\n".join(content_segments)

            if len(combined_content) < 200:  # Need sufficient content
                return []

            # Generate Active Recall questions
            question_request = QuestionGenerationRequest(
                course_id=course_id,
                content=combined_content,
                content_type="conversation",
                question_count=max_questions,
                session_id=session_id,
                context_tags=["auto_generated", "conversation_derived"]
            )

            response = await active_recall_engine.generate_questions(question_request)

            if response.success:
                # Return question IDs for tracking
                question_ids = []
                for question in response.questions:
                    question_ids.append(question.id)
                return question_ids
            else:
                print(f"Failed to generate questions: {response.message}")
                return []

        except Exception as e:
            print(f"Error generating Active Recall questions from conversation: {e}")
            return []

    async def generate_contextual_questions(
        self,
        course_id: str,
        session_id: str,
        topic: str,
        difficulty: str = "medium",
        question_count: int = 3
    ) -> List[str]:
        """
        Generate contextual Active Recall questions based on current chat topic
        """
        try:
            from models.active_recall import QuestionGenerationRequest, DifficultyLevel

            # Get enhanced context for the topic
            context_data = await self.retrieve_context_enhanced(
                course_id=course_id,
                session_id=session_id,
                query=topic,
                retrieval_k=5
            )

            # Extract relevant content from context
            relevant_content = []
            for source in context_data.get("sources", []):
                content = source.get("content", "")
                if content and len(content) > 100:
                    relevant_content.append(content)

            if not relevant_content:
                # Fallback to general knowledge about the topic
                relevant_content = [f"Discussione su: {topic}"]

            combined_content = "\n\n".join(relevant_content[:5])  # Limit content

            # Generate targeted questions
            question_request = QuestionGenerationRequest(
                course_id=course_id,
                content=combined_content,
                content_type="contextual",
                question_count=question_count,
                difficulty=DifficultyLevel(difficulty),
                focus_concepts=[topic],
                session_id=session_id,
                context_tags=["contextual", "topic_focused", topic.lower().replace(" ", "_")]
            )

            response = await active_recall_engine.generate_questions(question_request)

            if response.success:
                question_ids = []
                for question in response.questions:
                    question_ids.append(question.id)
                return question_ids
            else:
                print(f"Failed to generate contextual questions: {response.message}")
                return []

        except Exception as e:
            print(f"Error generating contextual questions: {e}")
            return []

    async def get_adaptive_practice_session(
        self,
        course_id: str,
        session_id: str,
        user_id: str,
        question_count: int = 5,
        focus_weak_areas: bool = True
    ) -> List[str]:
        """
        Get adaptive practice questions based on user performance and current context
        """
        try:
            from models.active_recall import AdaptiveQuestionRequest

            # Get recent conversation topics for context
            conversation_history = self.session_manager.get_conversation_history(
                session_id, limit=5
            )

            recent_topics = []
            for message in conversation_history:
                if message["role"] == "user":
                    # Extract key topics from user messages (simple heuristic)
                    words = message["content"].split()
                    for word in words:
                        if len(word) > 6:  # Likely substantive content
                            recent_topics.append(word.lower())

            adaptive_request = AdaptiveQuestionRequest(
                course_id=course_id,
                user_id=user_id,
                session_id=session_id,
                question_count=question_count,
                focus_weak_areas=focus_weak_areas,
                time_limit_minutes=30
            )

            response = await active_recall_engine.get_adaptive_questions(adaptive_request)

            if response.success:
                question_ids = []
                for question in response.questions:
                    question_ids.append(question.id)
                return question_ids
            else:
                print(f"Failed to get adaptive questions: {response}")
                return []

        except Exception as e:
            print(f"Error getting adaptive practice session: {e}")
            return []

# Initialize enhanced RAG service
def init_course_rag_service(rag_service, llm_service):
    """Initialize the course-specific RAG service"""
    return CourseRAGService(rag_service, llm_service)