"""
Unified Learning API Endpoints for Tutor-AI
Integrates concepts, quizzes, and mindmaps with persistent storage and cross-referencing
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional
from datetime import datetime

from services.unified_learning_service import unified_learning_service

router = APIRouter(prefix="/api/unified-learning", tags=["unified-learning"])

# ==================== REQUEST MODELS ====================

class CreateQuizRequest(BaseModel):
    course_id: str
    topic: str
    difficulty: str = "medium"
    num_questions: int = 5
    linked_concept_ids: Optional[List[str]] = None
    book_id: Optional[str] = None
    title: Optional[str] = None
    user_id: Optional[str] = None

class SubmitQuizRequest(BaseModel):
    course_id: str
    quiz_id: str
    user_id: str
    answers: List[Any]
    time_seconds: float
    book_id: Optional[str] = None

class CreateConceptRequest(BaseModel):
    course_id: str
    name: str
    summary: str = ""
    chapter: Optional[Dict[str, Any]] = None
    related_topics: List[str] = []
    recommended_minutes: int = 30
    auto_generate_quiz: bool = True
    book_id: Optional[str] = None

class LinkMindmapRequest(BaseModel):
    course_id: str
    mindmap_id: str
    concept_links: List[Dict[str, str]]  # [{"node_label": "Concept Name", "concept_id": "concept_id"}]
    book_id: Optional[str] = None

# ==================== QUIZ ENDPOINTS ====================

@router.post("/quiz/create")
async def create_persistent_quiz(request: CreateQuizRequest):
    """
    Create a persistent quiz that's linked to concepts and stored for future use
    """
    try:
        result = await unified_learning_service.create_persistent_quiz(
            course_id=request.course_id,
            topic=request.topic,
            difficulty=request.difficulty,
            num_questions=request.num_questions,
            linked_concept_ids=request.linked_concept_ids,
            book_id=request.book_id,
            title=request.title,
            user_id=request.user_id
        )
        return {
            "success": True,
            "message": "Quiz creato e salvato con successo",
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/quiz/course/{course_id}")
async def get_course_quizzes(
    course_id: str,
    book_id: Optional[str] = Query(None),
    concept_id: Optional[str] = Query(None),
    difficulty: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None)
):
    """
    Get all quizzes for a course with optional filtering
    """
    try:
        result = await unified_learning_service.get_course_quizzes(
            course_id=course_id,
            book_id=book_id,
            concept_id=concept_id,
            difficulty=difficulty,
            user_id=user_id
        )
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/quiz/submit")
async def submit_quiz_results(request: SubmitQuizRequest):
    """
    Submit quiz results and update progress across concepts and mindmaps
    """
    try:
        result = await unified_learning_service.submit_quiz_results(
            course_id=request.course_id,
            quiz_id=request.quiz_id,
            user_id=request.user_id,
            answers=request.answers,
            time_seconds=request.time_seconds,
            book_id=request.book_id
        )
        return {
            "success": True,
            "message": "Risultati del quiz salvati con successo",
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== CONCEPT INTEGRATION ENDPOINTS ====================

@router.post("/concept/create")
async def create_concept_with_quiz(request: CreateConceptRequest):
    """
    Create a concept and automatically generate associated quizzes
    """
    try:
        result = await unified_learning_service.create_concept_with_quiz(
            course_id=request.course_id,
            concept_data={
                "name": request.name,
                "summary": request.summary,
                "chapter": request.chapter,
                "related_topics": request.related_topics,
                "recommended_minutes": request.recommended_minutes
            },
            auto_generate_quiz=request.auto_generate_quiz,
            book_id=request.book_id
        )
        return {
            "success": True,
            "message": "Concetto e quiz creati con successo",
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/mindmap/link-concepts")
async def link_mindmap_to_concepts(request: LinkMindmapRequest):
    """
    Link mindmap nodes to concepts and create missing concepts if needed
    """
    try:
        result = await unified_learning_service.link_mindmap_to_concepts(
            course_id=request.course_id,
            mindmap_id=request.mindmap_id,
            concept_links=request.concept_links,
            book_id=request.book_id
        )
        return {
            "success": True,
            "message": "Mappa mentale collegata ai concetti con successo",
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== UNIFIED VIEW ENDPOINTS ====================

@router.get("/view/course/{course_id}")
async def get_unified_learning_view(
    course_id: str,
    user_id: Optional[str] = Query(None),
    book_id: Optional[str] = Query(None),
    include_content: bool = Query(True)
):
    """
    Get comprehensive view of all learning content with cross-references
    """
    try:
        result = await unified_learning_service.get_unified_learning_view(
            course_id=course_id,
            user_id=user_id,
            book_id=book_id,
            include_content=include_content
        )
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/pathway/{course_id}/user/{user_id}")
async def get_learning_pathway(
    course_id: str,
    user_id: str,
    target_concept_id: Optional[str] = Query(None),
    book_id: Optional[str] = Query(None)
):
    """
    Get personalized learning pathway based on user progress and prerequisites
    """
    try:
        result = await unified_learning_service.get_learning_pathway(
            course_id=course_id,
            user_id=user_id,
            target_concept_id=target_concept_id,
            book_id=book_id
        )
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== INTEGRATION STATUS ENDPOINTS ====================

@router.get("/status/course/{course_id}")
async def get_course_integration_status(
    course_id: str,
    book_id: Optional[str] = Query(None)
):
    """
    Get integration status of concepts, quizzes, and mindmaps for a course
    """
    try:
        from models.unified_learning import unified_manager

        space = unified_manager.load_or_create_learning_space(course_id, book_id)

        # Calculate integration metrics
        total_concepts = len(space.concepts)
        concepts_with_quizzes = len([
            cid for cid, concept in space.concepts.items()
            if concept.available_quizzes
        ])
        concepts_with_mindmaps = len([
            cid for cid, concept in space.concepts.items()
            if concept.mindmap_node_ids
        ])

        total_quizzes = len(space.quizzes)
        total_mindmaps = len(space.mindmaps)

        integration_score = 0
        if total_concepts > 0:
            integration_score = (
                (concepts_with_quizzes / total_concepts) * 0.5 +
                (concepts_with_mindmaps / total_concepts) * 0.5
            ) * 100

        return {
            "success": True,
            "data": {
                "course_id": course_id,
                "book_id": book_id,
                "integration_score": round(integration_score, 1),
                "components": {
                    "concepts": {
                        "total": total_concepts,
                        "with_quizzes": concepts_with_quizzes,
                        "with_mindmaps": concepts_with_mindmaps,
                        "fully_integrated": len([
                            cid for cid, concept in space.concepts.items()
                            if concept.available_quizzes and concept.mindmap_node_ids
                        ])
                    },
                    "quizzes": {
                        "total": total_quizzes,
                        "linked_to_concepts": len(space.quiz_to_concepts),
                        "average_difficulty": "medium"  # Could calculate from actual data
                    },
                    "mindmaps": {
                        "total": total_mindmaps,
                        "linked_to_concepts": len(space.mindmap_to_concepts),
                        "total_nodes": sum(len(mindmap.all_nodes) for mindmap in space.mindmaps.values())
                    }
                },
                "cross_references": {
                    "concept_to_quizzes": len(space.concept_to_quizzes),
                    "concept_to_mindmaps": len(space.concept_to_mindmaps),
                    "quiz_to_concepts": len(space.quiz_to_concepts),
                    "mindmap_to_concepts": len(space.mindmap_to_concepts)
                },
                "recommendations": self._generate_integration_recommendations(space)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/migrate/course/{course_id}")
async def migrate_course_data(
    course_id: str,
    book_ids: Optional[List[str]] = None
):
    """
    Migrate existing course data to unified model
    """
    try:
        result = await unified_learning_service.migrate_course_data(course_id, book_ids)
        return {
            "success": True,
            "message": "Migrazione dei dati completata",
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== ANALYTICS ENDPOINTS ====================

@router.get("/analytics/course/{course_id}/user/{user_id}")
async def get_user_learning_analytics(
    course_id: str,
    user_id: str,
    book_id: Optional[str] = Query(None),
    days_back: int = Query(30)
):
    """
    Get detailed learning analytics for a user in a course
    """
    try:
        from models.unified_learning import unified_manager

        # Load user progress and learning space
        user_progress = unified_manager.load_user_progress(user_id, course_id)
        space = unified_manager.load_or_create_learning_space(course_id, book_id)

        # Calculate analytics
        total_concepts = len(space.concepts)
        mastered_concepts = len([
            cid for cid, mastery in user_progress.concept_mastery.items()
            if mastery >= 0.8
        ])
        in_progress_concepts = len([
            cid for cid, mastery in user_progress.concept_mastery.items()
            if 0.3 <= mastery < 0.8
        ])

        # Quiz analytics
        total_quiz_attempts = sum(len(scores) for scores in user_progress.quiz_scores.values())
        average_quiz_score = 0
        if user_progress.quiz_scores:
            all_scores = []
            for scores in user_progress.quiz_scores.values():
                all_scores.extend(scores)
            average_quiz_score = sum(all_scores) / len(all_scores) if all_scores else 0

        # Time analytics
        total_study_time = user_progress.total_study_time / 60  # Convert to minutes
        average_session_time = total_study_time / max(1, user_progress.study_sessions)

        # Concept performance breakdown
        concept_performance = []
        for concept_id, concept in space.concepts.items():
            mastery = user_progress.concept_mastery.get(concept_id, 0)
            attempts = user_progress.concept_attempts.get(concept_id, 0)

            concept_performance.append({
                "concept_id": concept_id,
                "concept_name": concept.name,
                "mastery_level": mastery,
                "attempts": attempts,
                "available_quizzes": len(concept.available_quizzes),
                "has_mindmap_links": len(concept.mindmap_node_ids) > 0,
                "recommended_action": self._get_recommended_action(mastery, attempts)
            })

        # Sort by mastery level (ascending to focus on weak areas)
        concept_performance.sort(key=lambda x: x["mastery_level"])

        return {
            "success": True,
            "data": {
                "user_id": user_id,
                "course_id": course_id,
                "period_days": days_back,
                "overall_performance": {
                    "total_concepts": total_concepts,
                    "mastered_concepts": mastered_concepts,
                    "in_progress_concepts": in_progress_concepts,
                    "completion_percentage": round((mastered_concepts / max(1, total_concepts)) * 100, 1),
                    "total_quiz_attempts": total_quiz_attempts,
                    "average_quiz_score": round(average_quiz_score, 2),
                    "total_study_time_minutes": round(total_study_time, 1),
                    "average_session_time_minutes": round(average_session_time, 1),
                    "study_sessions": user_progress.study_sessions
                },
                "concept_breakdown": concept_performance[:10],  # Top 10 concepts needing attention
                "strength_areas": [
                    space.concepts[cid].name for cid in user_progress.strength_areas
                    if cid in space.concepts
                ],
                "improvement_areas": [
                    space.concepts[cid].name for cid in user_progress.improvement_areas
                    if cid in space.concepts
                ],
                "recommendations": await unified_learning_service._get_personalized_recommendations(
                    course_id, user_id, book_id
                )
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== PRIVATE HELPER METHODS ====================

def _generate_integration_recommendations(space) -> List[str]:
    """Generate recommendations for improving integration"""
    recommendations = []

    total_concepts = len(space.concepts)
    if total_concepts == 0:
        return ["Nessun concetto trovato - Creare concetti prima di integrare"]

    concepts_with_quizzes = len([
        cid for cid, concept in space.concepts.items()
        if concept.available_quizzes
    ])
    concepts_with_mindmaps = len([
        cid for cid, concept in space.concepts.items()
        if concept.mindmap_node_ids
    ])

    if concepts_with_quizzes < total_concepts:
        recommendations.append(
            f"Genera quiz per {total_concepts - concepts_with_quizzes} concetti senza quiz"
        )

    if concepts_with_mindmaps < total_concepts:
        recommendations.append(
            f"Collega {total_concepts - concepts_with_mindmaps} concetti alle mappe mentali"
        )

    if len(space.quizzes) > 0 and len(space.quiz_to_concepts) < len(space.quizzes):
        recommendations.append(
            f"Collega {len(space.quizzes) - len(space.quiz_to_concepts)} quiz ai concetti"
        )

    if len(space.mindmaps) > 0 and len(space.mindmap_to_concepts) < len(space.mindmaps):
        recommendations.append(
            f"Collega {len(space.mindmaps) - len(space.mindmap_to_concepts)} mappe mentali ai concetti"
        )

    if not recommendations:
        recommendations.append("Ottima integrazione! Tutti i componenti sono ben collegati.")

    return recommendations

def _get_recommended_action(mastery_level: float, attempts: int) -> str:
    """Get recommended action based on mastery and attempts"""
    if mastery_level >= 0.8:
        return "revisione_periodica"
    elif mastery_level >= 0.6:
        return "pratica_aggiuntiva"
    elif attempts == 0:
        return "inizia_apprendimento"
    elif mastery_level < 0.3 and attempts > 3:
        return "rivedi_materiali"
    else:
        return "continua_pratica"