from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services.concept_map_service import concept_map_service

router = APIRouter(prefix="/courses/{course_id}/concepts", tags=["concepts"])


class ConceptMapGenerateRequest(BaseModel):
    book_id: Optional[str] = None
    force: bool = False


class ConceptQuizResultRequest(BaseModel):
    concept_name: str = Field(..., description="Nome umano del concetto")
    chapter_title: Optional[str] = None
    score: float = Field(..., ge=0.0, le=1.0)
    time_seconds: float = Field(..., ge=0.0)
    correct_answers: int = Field(..., ge=0)
    total_questions: int = Field(..., ge=1)


@router.post("/generate")
async def generate_concept_map(course_id: str, payload: ConceptMapGenerateRequest):
    try:
        concept_map = await concept_map_service.generate_concept_map(
            course_id,
            book_id=payload.book_id,
            force=payload.force
        )
        return {"success": True, "concept_map": concept_map}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Errore generazione concept map: {exc}") from exc


@router.get("")
async def get_concept_map(course_id: str, book_id: Optional[str] = None):
    concept_map = concept_map_service.get_concept_map(course_id, book_id=book_id)
    if not concept_map:
        raise HTTPException(status_code=404, detail="Concept map non disponibile per questo corso/libro")
    return {"concept_map": concept_map}


@router.get("/metrics")
async def get_concept_metrics(course_id: str):
    metrics = concept_map_service.get_concept_metrics(course_id)
    return {"metrics": metrics}


@router.post("/{concept_id}/quiz-results")
async def record_concept_quiz_result(
    course_id: str,
    concept_id: str,
    payload: ConceptQuizResultRequest
):
    try:
        metrics = concept_map_service.record_quiz_attempt(
            course_id=course_id,
            concept_id=concept_id,
            concept_name=payload.concept_name,
            chapter_title=payload.chapter_title,
            score=payload.score,
            time_seconds=payload.time_seconds,
            correct_answers=payload.correct_answers,
            total_questions=payload.total_questions
        )
        return {"success": True, "metrics": metrics}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Errore nel salvataggio del quiz: {exc}") from exc
