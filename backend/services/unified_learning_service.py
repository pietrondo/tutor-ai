"""
Unified Learning Service for Tutor-AI
Integrates concepts, quizzes, and mindmaps with persistent storage and cross-referencing
"""

import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from fastapi import HTTPException

import structlog
from models.unified_learning import (
    UnifiedLearningManager, Quiz, QuizQuestion, DifficultyLevel,
    ConceptNode, Mindmap, MindmapNode, UserProgress, migration_helper
)
from services.llm_service import LLMService
from services.concept_map_service import ConceptMapService
from app.api.mindmaps import load_mindmaps, save_mindmaps

logger = structlog.get_logger()

class UnifiedLearningService:
    """Service that integrates all learning components with persistent storage"""

    def __init__(self):
        self.manager = UnifiedLearningManager()
        self.llm_service = LLMService()
        self.concept_service = ConceptMapService()

    # ==================== QUIZ MANAGEMENT ====================

    async def create_persistent_quiz(
        self,
        course_id: str,
        topic: str,
        difficulty: str = "medium",
        num_questions: int = 5,
        linked_concept_ids: Optional[List[str]] = None,
        book_id: Optional[str] = None,
        title: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a persistent quiz linked to concepts and mindmaps"""
        try:
            # Generate quiz using existing LLM service
            quiz_payload = await self.llm_service.generate_quiz(
                course_id=course_id,
                topic=topic,
                difficulty=difficulty,
                num_questions=num_questions
            )

            if not quiz_payload.get("questions"):
                raise ValueError("Quiz generation failed or returned empty questions")

            # Create unified quiz object
            quiz = Quiz(
                title=title or f"Quiz {topic} - {difficulty.title()}",
                description=f"Quiz generato su: {topic}",
                difficulty=DifficultyLevel(difficulty),
                estimated_minutes=num_questions * 2,  # Estimate 2 minutes per question
                topic_tags=[topic],
                linked_concept_ids=linked_concept_ids or [],
                questions=[
                    QuizQuestion(
                        question=q.get("question", ""),
                        options=q.get("options", []),
                        correct_answer=q.get("correct_answer", ""),
                        explanation=q.get("explanation"),
                        question_type=q.get("type", "multiple_choice"),
                        source_material=q.get("source_material")
                    )
                    for q in quiz_payload.get("questions", [])
                ],
                source="ai_generated"
            )

            # Store in unified learning space
            space = self.manager.load_or_create_learning_space(course_id, book_id)
            space.quizzes[quiz.id] = quiz

            # Auto-link to matching concepts
            if not linked_concept_ids:
                linked_concept_ids = await self._find_related_concepts(course_id, topic, book_id)

            for concept_id in linked_concept_ids:
                self.manager.link_concept_to_quiz(course_id, concept_id, quiz.id, book_id)

            self.manager.save_learning_space(space)

            logger.info(
                "Created persistent quiz",
                course_id=course_id,
                book_id=book_id,
                quiz_id=quiz.id,
                topic=topic,
                linked_concepts=len(linked_concept_ids)
            )

            return {
                "quiz": quiz.dict(),
                "linked_concepts": linked_concept_ids,
                "available_actions": [
                    "take_quiz",
                    "view_concepts",
                    "create_mindmap_link"
                ]
            }

        except Exception as e:
            logger.error(f"Failed to create persistent quiz: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to create quiz: {str(e)}")

    async def get_course_quizzes(
        self,
        course_id: str,
        book_id: Optional[str] = None,
        concept_id: Optional[str] = None,
        difficulty: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get all quizzes for a course with filtering options"""
        try:
            space = self.manager.load_or_create_learning_space(course_id, book_id)
            quizzes = list(space.quizzes.values())

            # Apply filters
            if concept_id:
                concept_quizzes = space.concept_to_quizzes.get(concept_id, [])
                quizzes = [q for q in quizzes if q.id in concept_quizzes]

            if difficulty:
                difficulty = DifficultyLevel(difficulty)
                quizzes = [q for q in quizzes if q.difficulty == difficulty]

            # Enrich with user progress if provided
            if user_id:
                user_progress = self.manager.load_user_progress(user_id, course_id)
                for quiz in quizzes:
                    if quiz.id in user_progress.quiz_scores:
                        quiz.user_scores = user_progress.quiz_scores[quiz.id]
                        quiz.average_score = sum(user_progress.quiz_scores[quiz.id]) / len(user_progress.quiz_scores[quiz.id])

            return {
                "quizzes": [quiz.dict() for quiz in quizzes],
                "total_count": len(quizzes),
                "filters_applied": {
                    "concept_id": concept_id,
                    "difficulty": difficulty,
                    "book_id": book_id
                }
            }

        except Exception as e:
            logger.error(f"Failed to get course quizzes: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to retrieve quizzes: {str(e)}")

    async def submit_quiz_results(
        self,
        course_id: str,
        quiz_id: str,
        user_id: str,
        answers: List[Any],
        time_seconds: float,
        book_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Submit quiz results and update progress across all systems"""
        try:
            space = self.manager.load_or_create_learning_space(course_id, book_id)

            if quiz_id not in space.quizzes:
                raise ValueError(f"Quiz {quiz_id} not found")

            quiz = space.quizzes[quiz_id]

            # Calculate score and results
            score_data = self._calculate_quiz_score(quiz, answers)

            # Update user progress
            user_progress = self.manager.load_user_progress(user_id, course_id)

            # Record quiz score
            if quiz_id not in user_progress.quiz_scores:
                user_progress.quiz_scores[quiz_id] = []
            user_progress.quiz_scores[quiz_id].append(score_data["score"])

            if quiz_id not in user_progress.total_time_spent:
                user_progress.total_time_spent[quiz_id] = 0.0
            user_progress.total_time_spent[quiz_id] += time_seconds

            user_progress.study_sessions += 1
            user_progress.total_study_time += time_seconds
            user_progress.last_activity = datetime.now()

            # Update concept mastery for linked concepts
            for concept_id in quiz.linked_concept_ids:
                if concept_id in space.concepts:
                    # Update concept performance in concept map service
                    await self.concept_service.record_quiz_attempt(
                        course_id=course_id,
                        concept_id=concept_id,
                        concept_name=space.concepts[concept_id].name,
                        chapter_title=space.concepts[concept_id].chapter.get("title") if space.concepts[concept_id].chapter else None,
                        score=score_data["score"],
                        time_seconds=time_seconds,
                        correct_answers=score_data["correct_answers"],
                        total_questions=len(quiz.questions)
                    )

                    # Update unified mastery levels
                    current_mastery = user_progress.concept_mastery.get(concept_id, 0.0)
                    attempt_count = user_progress.concept_attempts.get(concept_id, 0) + 1

                    # Weighted average with more weight on recent attempts
                    new_mastery = (current_mastery * 0.7) + (score_data["score"] * 0.3)
                    user_progress.concept_mastery[concept_id] = min(1.0, new_mastery)
                    user_progress.concept_attempts[concept_id] = attempt_count

                    # Update concept node mastery level
                    space.concepts[concept_id].mastery_level = new_mastery
                    space.concepts[concept_id].quiz_performance.append({
                        "quiz_id": quiz_id,
                        "score": score_data["score"],
                        "timestamp": datetime.now().isoformat(),
                        "time_seconds": time_seconds
                    })

                    # Keep only last 10 performances per concept
                    space.concepts[concept_id].quiz_performance = space.concepts[concept_id].quiz_performance[-10:]

            # Update strength and improvement areas
            self._update_learning_areas(user_progress)

            # Save everything
            self.manager.save_user_progress(user_progress)
            self.manager.save_learning_space(space)

            logger.info(
                "Quiz results submitted",
                course_id=course_id,
                quiz_id=quiz_id,
                user_id=user_id,
                score=score_data["score"],
                linked_concepts=len(quiz.linked_concept_ids)
            )

            return {
                "score": score_data["score"],
                "correct_answers": score_data["correct_answers"],
                "total_questions": len(quiz.questions),
                "time_seconds": time_seconds,
                "answers": score_data["answers"],
                "concept_mastery_updates": {
                    concept_id: user_progress.concept_mastery.get(concept_id, 0.0)
                    for concept_id in quiz.linked_concept_ids
                },
                "next_recommendations": await self._get_next_recommendations(
                    course_id, user_id, score_data["score"], book_id
                )
            }

        except Exception as e:
            logger.error(f"Failed to submit quiz results: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to submit quiz results: {str(e)}")

    # ==================== CONCEPT INTEGRATION ====================

    async def create_concept_with_quiz(
        self,
        course_id: str,
        concept_data: Dict[str, Any],
        auto_generate_quiz: bool = True,
        book_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a concept and automatically generate associated quizzes"""
        try:
            space = self.manager.load_or_create_learning_space(course_id, book_id)

            # Create concept node
            concept = ConceptNode(
                name=concept_data.get("name", ""),
                summary=concept_data.get("summary", ""),
                chapter=concept_data.get("chapter"),
                related_topics=concept_data.get("related_topics", []),
                recommended_minutes=concept_data.get("recommended_minutes", 30)
            )

            space.concepts[concept.id] = concept

            generated_quizzes = []

            # Auto-generate quizzes if requested
            if auto_generate_quiz:
                for difficulty in ["easy", "medium"]:
                    quiz_result = await self.create_persistent_quiz(
                        course_id=course_id,
                        topic=concept.name,
                        difficulty=difficulty,
                        num_questions=3,
                        linked_concept_ids=[concept.id],
                        book_id=book_id,
                        title=f"Quiz {difficulty.title()} - {concept.name}"
                    )
                    generated_quizzes.append(quiz_result["quiz"]["id"])

            self.manager.save_learning_space(space)

            return {
                "concept": concept.dict(),
                "generated_quizzes": generated_quizzes,
                "integration_status": {
                    "quizzes_linked": len(generated_quizzes),
                    "mindmap_links": 0
                }
            }

        except Exception as e:
            logger.error(f"Failed to create concept with quiz: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to create concept: {str(e)}")

    async def link_mindmap_to_concepts(
        self,
        course_id: str,
        mindmap_id: str,
        concept_links: List[Dict[str, str]],  # [{"node_label": "Concept Name", "concept_id": "concept_id"}]
        book_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Link mindmap nodes to concepts and create missing concepts if needed"""
        try:
            space = self.manager.load_or_create_learning_space(course_id, book_id)

            if mindmap_id not in space.mindmaps:
                raise ValueError(f"Mindmap {mindmap_id} not found")

            mindmap = space.mindmaps[mindmap_id]
            linked_count = 0
            created_concepts = []

            for link in concept_links:
                node_label = link.get("node_label", "")
                concept_id = link.get("concept_id")

                # Find or create concept
                if concept_id and concept_id in space.concepts:
                    concept = space.concepts[concept_id]
                elif node_label:
                    # Create new concept from node
                    concept = ConceptNode(
                        name=node_label,
                        summary=f"Concepto dalla mappa mentale: {node_label}",
                        related_topics=[],
                        recommended_minutes=20
                    )
                    space.concepts[concept.id] = concept
                    created_concepts.append(concept.id)
                    concept_id = concept.id
                else:
                    continue

                # Create bidirectional link
                self.manager.link_concept_to_mindmap(course_id, concept_id, mindmap_id, book_id)
                linked_count += 1

            # Update mindmap metadata
            mindmap.linked_concept_ids = list(set(mindmap.linked_concept_ids + [
                link.get("concept_id") for link in concept_links if link.get("concept_id")
            ] + created_concepts))

            self.manager.save_learning_space(space)

            return {
                "linked_nodes": linked_count,
                "created_concepts": created_concepts,
                "total_concepts_linked": len(mindmap.linked_concept_ids)
            }

        except Exception as e:
            logger.error(f"Failed to link mindmap to concepts: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to link mindmap: {str(e)}")

    # ==================== UNIFIED VIEW ENDPOINTS ====================

    async def get_unified_learning_view(
        self,
        course_id: str,
        user_id: Optional[str] = None,
        book_id: Optional[str] = None,
        include_content: bool = True
    ) -> Dict[str, Any]:
        """Get comprehensive view of all learning content with cross-references"""
        try:
            unified_view = self.manager.get_unified_view(course_id, user_id, book_id)

            if include_content:
                # Add content from existing systems
                concept_map = self.concept_service.get_concept_map(course_id, book_id)
                if concept_map:
                    unified_view["legacy_concept_map"] = concept_map

                # Add mindmap content
                if book_id:
                    mindmaps = load_mindmaps(course_id, book_id)
                    unified_view["legacy_mindmaps"] = mindmaps

            # Add learning recommendations
            if user_id:
                unified_view["recommendations"] = await self._get_personalized_recommendations(
                    course_id, user_id, book_id
                )

            return unified_view

        except Exception as e:
            logger.error(f"Failed to get unified learning view: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get unified view: {str(e)}")

    async def get_learning_pathway(
        self,
        course_id: str,
        user_id: str,
        target_concept_id: Optional[str] = None,
        book_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get personalized learning pathway based on user progress and prerequisites"""
        try:
            space = self.manager.load_or_create_learning_space(course_id, book_id)
            user_progress = self.manager.load_user_progress(user_id, course_id)

            # Analyze current mastery levels
            mastered_concepts = [
                cid for cid, mastery in user_progress.concept_mastery.items()
                if mastery >= 0.8
            ]
            weak_concepts = [
                cid for cid, mastery in user_progress.concept_mastery.items()
                if 0.3 <= mastery < 0.8
            ]
            not_started = [
                cid for cid in space.concepts.keys()
                if cid not in user_progress.concept_mastery
            ]

            # Build learning pathway
            pathway = {
                "current_focus": [],
                "next_steps": [],
                "review_needed": [],
                "ready_for_mastery": []
            }

            # Priority 1: Weak concepts that block others
            for concept_id in weak_concepts:
                if concept_id in space.concepts:
                    concept = space.concepts[concept_id]
                    # Check if this concept is a prerequisite for others
                    blocks_others = any(
                        concept_id in space.concepts[cid].prerequisite_ids
                        for cid in space.concepts.keys()
                    )
                    if blocks_others:
                        pathway["current_focus"].append({
                            "concept_id": concept_id,
                            "concept_name": concept.name,
                            "current_mastery": user_progress.concept_mastery[concept_id],
                            "recommended_quizzes": space.concept_to_quizzes.get(concept_id, [])
                        })

            # Priority 2: Not started concepts with completed prerequisites
            for concept_id in not_started:
                if concept_id in space.concepts:
                    concept = space.concepts[concept_id]
                    prerequisites_met = all(
                        prereq in mastered_concepts
                        for prereq in concept.prerequisite_ids
                    )
                    if prerequisites_met:
                        pathway["next_steps"].append({
                            "concept_id": concept_id,
                            "concept_name": concept.name,
                            "estimated_time": concept.recommended_minutes,
                            "available_quizzes": space.concept_to_quizzes.get(concept_id, [])
                        })

            # Priority 3: Mastered concepts that need review
            for concept_id in mastered_concepts:
                if concept_id in space.concepts:
                    last_attempt = user_progress.concept_attempts.get(concept_id, 0)
                    if last_attempt > 5:  # Hasn't practiced recently
                        pathway["review_needed"].append({
                            "concept_id": concept_id,
                            "concept_name": space.concepts[concept_id].name,
                            "mastery_level": user_progress.concept_mastery[concept_id],
                            "last_attempts": last_attempt
                        })

            return pathway

        except Exception as e:
            logger.error(f"Failed to get learning pathway: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to generate learning pathway: {str(e)}")

    # ==================== MIGRATION HELPERS ====================

    async def migrate_course_data(self, course_id: str, book_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """Migrate existing course data to unified model"""
        try:
            migration_results = {
                "concepts_migrated": False,
                "mindmaps_migrated": 0,
                "errors": []
            }

            # Migrate concept maps
            if migration_helper.migrate_concept_maps(course_id):
                migration_results["concepts_migrated"] = True

            # Migrate mindmaps for each book
            if book_ids:
                for book_id in book_ids:
                    if migration_helper.migrate_mindmaps(course_id, book_id):
                        migration_results["mindmaps_migrated"] += 1

            logger.info(
                "Course data migration completed",
                course_id=course_id,
                results=migration_results
            )

            return migration_results

        except Exception as e:
            logger.error(f"Failed to migrate course data: {e}")
            raise HTTPException(status_code=500, detail=f"Migration failed: {str(e)}")

    # ==================== PRIVATE HELPER METHODS ====================

    async def _find_related_concepts(
        self, course_id: str, topic: str, book_id: Optional[str] = None
    ) -> List[str]:
        """Find concepts related to a topic using semantic matching"""
        try:
            space = self.manager.load_or_create_learning_space(course_id, book_id)
            related_concepts = []

            topic_lower = topic.lower()
            for concept_id, concept in space.concepts.items():
                # Simple text matching - could be enhanced with embeddings
                if (topic_lower in concept.name.lower() or
                    any(topic_lower in topic.lower() for topic in concept.related_topics) or
                    topic_lower in concept.summary.lower()):
                    related_concepts.append(concept_id)

            return related_concepts[:5]  # Limit to 5 most relevant concepts

        except Exception as e:
            logger.warning(f"Failed to find related concepts for topic {topic}: {e}")
            return []

    def _calculate_quiz_score(self, quiz: Quiz, answers: List[Any]) -> Dict[str, Any]:
        """Calculate quiz score and detailed results"""
        correct_answers = 0
        processed_answers = []

        for i, question in enumerate(quiz.questions):
            user_answer = answers[i] if i < len(answers) else None
            is_correct = self._check_answer(question, user_answer)

            if is_correct:
                correct_answers += 1

            processed_answers.append({
                "question": question.question,
                "user_answer": user_answer,
                "correct_answer": question.correct_answer,
                "is_correct": is_correct,
                "explanation": question.explanation
            })

        score = correct_answers / len(quiz.questions) if quiz.questions else 0.0

        return {
            "score": score,
            "correct_answers": correct_answers,
            "total_questions": len(quiz.questions),
            "percentage": score * 100,
            "answers": processed_answers
        }

    def _check_answer(self, question: QuizQuestion, user_answer: Any) -> bool:
        """Check if user answer is correct"""
        if user_answer is None:
            return False

        if question.question_type == "multiple_choice":
            return str(user_answer).strip().lower() == str(question.correct_answer).strip().lower()
        elif question.question_type == "true_false":
            return bool(user_answer) == bool(question.correct_answer)
        elif question.question_type == "short_answer":
            # Simple string matching for short answers
            return str(user_answer).strip().lower() in str(question.correct_answer).strip().lower().split(",")
        else:
            # For essay questions, we'd need more sophisticated checking
            return False  # Placeholder

    def _update_learning_areas(self, user_progress: UserProgress):
        """Update strength and improvement areas based on current mastery"""
        user_progress.strength_areas = [
            concept_id for concept_id, mastery in user_progress.concept_mastery.items()
            if mastery >= 0.8
        ]
        user_progress.improvement_areas = [
            concept_id for concept_id, mastery in user_progress.concept_mastery.items()
            if mastery < 0.6 and user_progress.concept_attempts.get(concept_id, 0) > 0
        ]

    async def _get_next_recommendations(
        self, course_id: str, user_id: str, score: float, book_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get personalized recommendations based on quiz performance"""
        try:
            recommendations = []

            if score >= 0.8:
                # High score - suggest more challenging content
                recommendations.append({
                    "type": "advanced_quiz",
                    "reason": "Ottimo punteggio! Prova un quiz più difficile.",
                    "difficulty": "hard"
                })
            elif score >= 0.6:
                # Good score - suggest reinforcement
                recommendations.append({
                    "type": "reinforcement_quiz",
                    "reason": "Buon punteggio! Prova un altro quiz simile per rinforzare.",
                    "difficulty": "medium"
                })
            else:
                # Low score - suggest review and easier content
                recommendations.append({
                    "type": "review_material",
                    "reason": "Rivedi i materiali prima di riprovare il quiz.",
                    "difficulty": "easy"
                })

            # Add mindmap exploration recommendation
            recommendations.append({
                "type": "explore_mindmap",
                "reason": "Esplora la mappa concettuale per visualizzare le connessioni.",
                "action": "open_mindmap"
            })

            return recommendations

        except Exception as e:
            logger.warning(f"Failed to generate recommendations: {e}")
            return []

    async def _get_personalized_recommendations(
        self, course_id: str, user_id: str, book_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get personalized learning recommendations"""
        try:
            pathway = await self.get_learning_pathway(course_id, user_id, book_id=book_id)

            return {
                "priority_concepts": pathway["current_focus"],
                "suggested_quizzes": [
                    item["recommended_quizzes"][0]
                    for item in pathway["current_focus"] + pathway["next_steps"]
                    if item["recommended_quizzes"]
                ],
                "study_schedule": self._generate_study_schedule(pathway),
                "estimated_completion": self._estimate_completion_time(pathway)
            }

        except Exception as e:
            logger.warning(f"Failed to get personalized recommendations: {e}")
            return {}

    def _generate_study_schedule(self, pathway: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate a study schedule based on pathway recommendations"""
        schedule = []
        session_count = 0

        # Add current focus items first
        for item in pathway["current_focus"]:
            schedule.append({
                "session": session_count + 1,
                "type": "focus",
                "concept_id": item["concept_id"],
                "concept_name": item["concept_name"],
                "estimated_minutes": item.get("recommended_time", 30),
                "activities": ["study_concept", "take_quiz"]
            })
            session_count += 1

        # Add next steps
        for item in pathway["next_steps"][:3]:  # Limit to next 3 steps
            schedule.append({
                "session": session_count + 1,
                "type": "new_learning",
                "concept_id": item["concept_id"],
                "concept_name": item["concept_name"],
                "estimated_minutes": item.get("estimated_time", 30),
                "activities": ["study_concept", "take_quiz"]
            })
            session_count += 1

        return schedule

    def _estimate_completion_time(self, pathway: Dict[str, Any]) -> Dict[str, Any]:
        """Estimate time to complete current learning pathway"""
        total_minutes = 0
        concepts_remaining = len(pathway["current_focus"]) + len(pathway["next_steps"])

        # Estimate based on average concept study time
        total_minutes = concepts_remaining * 45  # 45 minutes per concept average

        return {
            "total_minutes": total_minutes,
            "total_hours": round(total_minutes / 60, 1),
            "concepts_remaining": concepts_remaining,
            "estimated_sessions": max(1, total_minutes // 30)  # 30-minute sessions
        }

# ==================== GLOBAL INSTANCE ====================

unified_learning_service = UnifiedLearningService()