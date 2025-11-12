"""
Enhanced Slides API - Mayer's Multimedia Learning Principles
=========================================

This module implements enhanced slide generation using Mayer's 12 multimedia
learning principles with GLM-4.6 long-term reasoning and cognitive load management.

Key Features:
- Mayer's 12 multimedia learning principles application
- Cognitive load management and optimization
- Dual verbal-visual presentation integration
- GLM-4.6 advanced reasoning capabilities
- Accessibility compliance (WCAG 2.1 AA)
- Learner profile analysis and personalization
- Evidence-based educational psychology
- Comprehensive analytics and performance tracking

API Endpoints:
- POST /api/enhanced-slides/generate - Generate enhanced slides
- GET /api/enhanced-slides/templates - Available slide templates
- GET /api/enhanced-slides/progress - Generation progress tracking
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum
import asyncio
import logging
import json
from datetime import datetime

# Import the enhanced slide service
from services.enhanced_slide_service import EnhancedSlideService, SlideGenerationRequest
from services.prompt_analytics_service import analytics_service
from models.enhanced_content import (
    EnhancedSlideResponse,
    SlideTemplate,
    SlideGenerationProgress,
    CognitiveLoadLevel,
    LearningObjectiveType,
    MultimediaPrinciple
)
from middleware.auth import get_current_user
from utils.error_handlers import EnhancedSlideGeneratorError, ValidationError

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize enhanced slide service
try:
    enhanced_slide_service = EnhancedSlideService()
    logger.info("Enhanced slide service initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize enhanced slide service: {str(e)}")
    enhanced_slide_service = None


class SlideGenerationRequestModel(BaseModel):
    """Request model for enhanced slide generation."""

    course_id: str = Field(..., description="Course identifier")
    book_id: Optional[str] = Field(None, description="Specific book ID for focused content")
    topic: str = Field(..., description="Main topic or concept for slides")
    learning_objectives: List[str] = Field(default_factory=list, description="Learning objectives for the presentation")

    # Content and structure parameters
    slide_count: int = Field(default=10, ge=3, le=50, description="Number of slides to generate")
    target_audience: str = Field(default="university_students", description="Target audience for the slides")
    difficulty_level: CognitiveLoadLevel = Field(default=CognitiveLoadLevel.MODERATE, description="Cognitive complexity level")
    presentation_type: str = Field(default="educational", description="Type of presentation")

    # Multimedia learning preferences
    include_visual_elements: bool = Field(default=True, description="Include diagrams, charts, and visual aids")
    include_interactive_elements: bool = Field(default=False, description="Include interactive components")
    include_examples: bool = Field(default=True, description="Include real-world examples and case studies")
    include_assessments: bool = Field(default=False, description="Include knowledge check questions")

    # Accessibility and personalization
    accessibility_mode: bool = Field(default=False, description="Generate with accessibility enhancements")
    language_preference: str = Field(default="it", description="Preferred language for content")
    learning_style_preference: Optional[str] = Field(None, description="Preferred learning style (visual, verbal, etc.)")

    class Config:
        use_enum_values = True


class SlideTemplateResponse(BaseModel):
    """Response model for slide templates."""

    templates: List[SlideTemplate]
    total_count: int
    categories: List[str]


class SlideProgressResponse(BaseModel):
    """Response model for generation progress."""

    task_id: str
    status: str
    progress: float  # 0.0 to 1.0
    current_step: str
    estimated_remaining_time: Optional[int] = None  # seconds
    generated_slides: Optional[int] = None
    total_slides: Optional[int] = None
    error_message: Optional[str] = None


@router.post("/generate", response_model=EnhancedSlideResponse)
async def generate_enhanced_slides(
    request: SlideGenerationRequestModel,
    background_tasks: BackgroundTasks,
    current_user: Dict = Depends(get_current_user)
):
    """
    Generate enhanced slides using Mayer's multimedia learning principles.

    This endpoint creates pedagogically-effective slide presentations that apply
    Mayer's 12 multimedia learning principles with GLM-4.6 advanced reasoning
    capabilities for optimal learning outcomes.

    Features Applied:
    - **Coherence Principle**: Remove unnecessary multimedia elements
    - **Signaling Principle**: Highlight essential information visually
    - **Redundancy Principle**: Avoid redundant graphics/text/ narration
    - **Spatial Contiguity**: Place related words and pictures near each other
    - **Temporal Contiguity**: Present corresponding narration and animation simultaneously
    - **Segmenting Principle**: Break lessons into bite-sized segments
    - **Pre-training Principle**: Pre-teach key concepts and terminology
    - **Modality Principle**: Use graphics + narration rather than graphics + text
    - **Multimedia Principle**: Use words + graphics rather than words alone
    - **Personalization Principle**: Use conversational style and polite language
    - **Voice Principle**: Use human-like voice rather than machine voice
    - **Image Principle**: Use speaker's image with pedagogical purpose

    Args:
        request: Slide generation request with content and structure parameters
        background_tasks: FastAPI background tasks for async processing
        current_user: Authenticated user information

    Returns:
        EnhancedSlideResponse: Generated slides with comprehensive metadata
    """
    if not enhanced_slide_service:
        raise HTTPException(
            status_code=503,
            detail="Enhanced slide service is currently unavailable"
        )

    try:
        logger.info(f"Starting enhanced slide generation for user {current_user.get('sub')}")
        logger.info(f"Topic: {request.topic}, Slides: {request.slide_count}, Level: {request.difficulty_level}")

        # Create the internal request
        slide_request = SlideGenerationRequest(
            course_id=request.course_id,
            book_id=request.book_id,
            topic=request.topic,
            learning_objectives=request.learning_objectives,
            slide_count=request.slide_count,
            target_audience=request.target_audience,
            difficulty_level=request.difficulty_level,
            presentation_type=request.presentation_type,
            include_visual_elements=request.include_visual_elements,
            include_interactive_elements=request.include_interactive_elements,
            include_examples=request.include_examples,
            include_assessments=request.include_assessments,
            accessibility_mode=request.accessibility_mode,
            language_preference=request.language_preference,
            learning_style_preference=request.learning_style_preference
        )

        # Generate enhanced slides
        slides_data = await enhanced_slide_service.generate_enhanced_slides(slide_request)

        # Log generation event
        await analytics_service.log_slide_generation(
            user_id=current_user.get('sub'),
            course_id=request.course_id,
            book_id=request.book_id,
            topic=request.topic,
            slide_count=request.slide_count,
            generation_time=slides_data.metadata.generation_time,
            principles_applied=slides_data.metadata.principles_applied,
            cognitive_load_level=request.difficulty_level.value,
            success=True
        )

        logger.info(f"Successfully generated {slides_data.slide_count} enhanced slides")
        logger.info(f"Applied principles: {', '.join([p.value for p in slides_data.metadata.principles_applied])}")

        return slides_data

    except EnhancedSlideGeneratorError as e:
        logger.error(f"Enhanced slide generation error: {str(e)}")

        # Log error event
        await analytics_service.log_slide_generation(
            user_id=current_user.get('sub'),
            course_id=request.course_id,
            topic=request.topic,
            slide_count=request.slide_count,
            cognitive_load_level=request.difficulty_level.value,
            success=False,
            error_message=str(e)
        )

        raise HTTPException(status_code=e.status_code, detail=str(e))

    except Exception as e:
        logger.error(f"Unexpected error in enhanced slide generation: {str(e)}", exc_info=True)

        # Log error event
        await analytics_service.log_slide_generation(
            user_id=current_user.get('sub'),
            course_id=request.course_id,
            topic=request.topic,
            slide_count=request.slide_count,
            cognitive_load_level=request.difficulty_level.value,
            success=False,
            error_message=f"Unexpected error: {str(e)}"
        )

        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred during enhanced slide generation"
        )


@router.get("/templates", response_model=SlideTemplateResponse)
async def get_slide_templates(
    category: Optional[str] = Query(None, description="Filter templates by category"),
    cognitive_load_level: Optional[CognitiveLoadLevel] = Query(None, description="Filter by cognitive load level"),
    presentation_type: Optional[str] = Query(None, description="Filter by presentation type"),
    current_user: Dict = Depends(get_current_user)
):
    """
    Get available slide templates with filtering options.

    Returns a comprehensive list of slide templates designed according to
    Mayer's multimedia learning principles, categorized by cognitive load
    level and presentation type.

    Args:
        category: Optional category filter (educational, business, technical, creative)
        cognitive_load_level: Optional cognitive load level filter
        presentation_type: Optional presentation type filter
        current_user: Authenticated user information

    Returns:
        SlideTemplateResponse: Available templates and categories
    """
    if not enhanced_slide_service:
        raise HTTPException(
            status_code=503,
            detail="Enhanced slide service is currently unavailable"
        )

    try:
        templates = await enhanced_slide_service.get_slide_templates(
            category=category,
            cognitive_load_level=cognitive_load_level,
            presentation_type=presentation_type
        )

        # Extract unique categories
        categories = list(set(template.category for template in templates))

        logger.info(f"Retrieved {len(templates)} slide templates for user {current_user.get('sub')}")

        return SlideTemplateResponse(
            templates=templates,
            total_count=len(templates),
            categories=categories
        )

    except Exception as e:
        logger.error(f"Error retrieving slide templates: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve slide templates"
        )


@router.get("/progress/{task_id}", response_model=SlideProgressResponse)
async def get_generation_progress(
    task_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """
    Get the progress of an ongoing slide generation task.

    Provides real-time updates on slide generation progress including
    current step, estimated remaining time, and generated slide count.

    Args:
        task_id: Unique identifier for the generation task
        current_user: Authenticated user information

    Returns:
        SlideProgressResponse: Current progress information
    """
    if not enhanced_slide_service:
        raise HTTPException(
            status_code=503,
            detail="Enhanced slide service is currently unavailable"
        )

    try:
        progress = await enhanced_slide_service.get_generation_progress(task_id)

        if not progress:
            raise HTTPException(
                status_code=404,
                detail="Generation task not found"
            )

        # Verify task ownership
        if hasattr(progress, 'user_id') and progress.user_id != current_user.get('sub'):
            raise HTTPException(
                status_code=403,
                detail="Access denied to this generation task"
            )

        return SlideProgressResponse(
            task_id=progress.task_id,
            status=progress.status,
            progress=progress.progress,
            current_step=progress.current_step,
            estimated_remaining_time=getattr(progress, 'estimated_remaining_time', None),
            generated_slides=getattr(progress, 'generated_slides', None),
            total_slides=getattr(progress, 'total_slides', None),
            error_message=getattr(progress, 'error_message', None)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving generation progress: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve generation progress"
        )


@router.get("/principles")
async def get_multimedia_principles(
    current_user: Dict = Depends(get_current_user)
):
    """
    Get detailed information about Mayer's multimedia learning principles.

    Returns educational information about the 12 multimedia learning
    principles applied in enhanced slide generation, useful for
    understanding the pedagogical foundation.

    Args:
        current_user: Authenticated user information

    Returns:
        Dict: Detailed information about multimedia learning principles
    """
    principles_info = {
        "mayer_multimedia_principles": {
            "coherence_principle": {
                "name": "Coherence Principle",
                "description": "Remove unnecessary multimedia elements to avoid cognitive overload",
                "application": "Exclude extraneous graphics, sounds, and words that don't support learning"
            },
            "signaling_principle": {
                "name": "Signaling Principle",
                "description": "Highlight essential information to guide attention",
                "application": "Use visual cues, headings, and emphasis to point out key concepts"
            },
            "redundancy_principle": {
                "name": "Redundancy Principle",
                "description": "Avoid redundant graphics, text, and narration",
                "application": "Don't present identical information in multiple formats simultaneously"
            },
            "spatial_contiguity_principle": {
                "name": "Spatial Contiguity Principle",
                "description": "Place related words and pictures near each other",
                "application": "Integrate text and graphics rather than separating them"
            },
            "temporal_contiguity_principle": {
                "name": "Temporal Contiguity Principle",
                "description": "Present corresponding narration and animation simultaneously",
                "application": "Synchronize verbal explanations with visual animations"
            },
            "segmenting_principle": {
                "name": "Segmenting Principle",
                "description": "Break lessons into bite-sized segments",
                "application": "Chunk content into manageable pieces for learner control"
            },
            "pre_training_principle": {
                "name": "Pre-training Principle",
                "description": "Pre-teach key concepts and terminology",
                "application": "Introduce vocabulary and basic concepts before main content"
            },
            "modality_principle": {
                "name": "Modality Principle",
                "description": "Use graphics + narration rather than graphics + text",
                "application": "Present visual information with spoken explanations"
            },
            "multimedia_principle": {
                "name": "Multimedia Principle",
                "description": "Use words + graphics rather than words alone",
                "application": "Combine verbal and visual representations for better learning"
            },
            "personalization_principle": {
                "name": "Personalization Principle",
                "description": "Use conversational style and polite language",
                "application": "Write in first-person, friendly, and encouraging tone"
            },
            "voice_principle": {
                "name": "Voice Principle",
                "description": "Use human-like voice rather than machine voice",
                "application": "If using narration, use natural human speech patterns"
            },
            "image_principle": {
                "name": "Image Principle",
                "description": "Use speaker's image with pedagogical purpose",
                "application": "Include instructor image only when it adds educational value"
            }
        },
        "cognitive_load_theory": {
            "description": "Manages intrinsic, extraneous, and germane cognitive load",
            "levels": [
                "minimal: Basic concepts, low complexity",
                "moderate: Standard educational complexity",
                "complex: Advanced concepts with multiple elements",
                "expert: High-level synthesis and analysis"
            ]
        },
        "dual_coding_theory": {
            "description": "Combines verbal and visual processing for enhanced memory",
            "application": "Integrate text explanations with relevant graphics and diagrams"
        }
    }

    return principles_info


@router.get("/analytics/generation-stats")
async def get_generation_stats(
    course_id: Optional[str] = Query(None, description="Filter by course ID"),
    days: int = Query(default=30, ge=1, le=365, description="Number of days to analyze"),
    current_user: Dict = Depends(get_current_user)
):
    """
    Get slide generation analytics and statistics.

    Returns comprehensive analytics about slide generation including
    success rates, average generation times, principle application
    frequency, and user engagement metrics.

    Args:
        course_id: Optional course ID filter
        days: Number of days to look back for analytics
        current_user: Authenticated user information

    Returns:
        Dict: Generation analytics and statistics
    """
    try:
        stats = await analytics_service.get_slide_generation_stats(
            user_id=current_user.get('sub'),
            course_id=course_id,
            days=days
        )

        return {
            "period_days": days,
            "course_filter": course_id,
            "statistics": stats,
            "generated_at": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Error retrieving generation stats: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve generation statistics"
        )


@router.delete("/cancel/{task_id}")
async def cancel_generation(
    task_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """
    Cancel an ongoing slide generation task.

    Allows users to cancel long-running slide generation tasks.
    Successfully cancelled tasks will stop processing and clean up
    any temporary resources.

    Args:
        task_id: Unique identifier for the generation task
        current_user: Authenticated user information

    Returns:
        Dict: Cancellation result
    """
    if not enhanced_slide_service:
        raise HTTPException(
            status_code=503,
            detail="Enhanced slide service is currently unavailable"
        )

    try:
        success = await enhanced_slide_service.cancel_generation(task_id, current_user.get('sub'))

        if success:
            logger.info(f"Successfully cancelled generation task {task_id}")
            return {"message": "Slide generation cancelled successfully", "task_id": task_id}
        else:
            raise HTTPException(
                status_code=404,
                detail="Generation task not found or cannot be cancelled"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling generation: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to cancel slide generation"
        )


# Health check endpoint
@router.get("/health")
async def health_check():
    """Health check endpoint for enhanced slides API."""
    if enhanced_slide_service:
        return {
            "status": "healthy",
            "service": "enhanced_slides",
            "version": "1.0.0",
            "features": {
                "mayer_principles": True,
                "glm_integration": True,
                "cognitive_load_management": True,
                "accessibility_support": True,
                "analytics_tracking": True
            }
        }
    else:
        return {
            "status": "unhealthy",
            "service": "enhanced_slides",
            "error": "Enhanced slide service initialization failed"
        }