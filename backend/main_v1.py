"""
CLE API v1 - Standardized Cognitive Learning Engine Endpoints
All endpoints follow /api/v1/ pattern with consistent structure
"""

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
import asyncio
import uuid

# Error Handling
from middleware.error_handler import (
    cle_exception_handler, CLEError, ValidationError, NotFoundError,
    BusinessLogicError, ExternalServiceError, AuthenticationError,
    AuthorizationError, create_success_response, raise_not_found,
    raise_validation_error, raise_business_logic_error
)

# Performance Optimization
from middleware.caching import (
    cache_manager, cached, async_cached, monitor_performance,
    monitor_async_performance, should_compress_response, CacheInvalidator
)

# CLE Services
from services.spaced_repetition_service import spaced_repetition_service
from services.active_recall_service import active_recall_service
from services.dual_coding_service import dual_coding_service
from services.interleaved_practice_service import interleaved_practice_service
from services.metacognition_service import metacognition_service
from services.elaboration_network_service import elaboration_network_service

# CLE Models
from models.spaced_repetition import (
    LearningCardCreate, LearningCardResponse, CardReviewRequest, CardReviewResponse,
    StudySessionRequest, StudySessionResponse, LearningAnalytics,
    StudyRecommendations, AutoGenerateCardsRequest, AutoGenerateCardsResponse
)
from models.active_recall import (
    QuestionGenerationRequest, QuestionGenerationResponse, AdaptiveQuestionRequest,
    AdaptiveQuestionResponse, QuestionSubmission, QuestionSubmissionResponse,
    QuizSessionStart, QuizSessionStartResponse, QuizSessionResponse,
    ActiveRecallAnalytics, ActiveRecallAnalyticsResponse, ConceptExtraction,
    ConceptExtractionResponse
)
from models.dual_coding import (
    DualCodingRequest, DualCodingResponse, DualCodingAnalytics, DualCodingAnalyticsResponse,
    ContentEnhancementRequest, EnhancedContentResponse, LearningPathRequest,
    LearningPathResponse, AssessmentRequest, AssessmentResponse,
    FeedbackSubmissionRequest, FeedbackResponse, PersonalizationUpdate,
    PersonalizationResponse
)
from models.interleaved_practice import (
    InterleavedScheduleRequest, InterleavedScheduleResponse, ScheduleOptimizationRequest,
    ScheduleOptimizationResponse, InterleavedAnalytics, InterleavedAnalyticsResponse,
    SessionFeedback, PatternFeedback, LearningProgress, ProgressUpdate,
    UserPreferences, AdaptiveAdjustment, PerformanceMetrics
)
from models.metacognition import (
    MetacognitiveSessionCreate, MetacognitiveSessionResponse, ReflectionActivityRequest,
    ReflectionActivityResponse, SelfRegulationRequest, SelfRegulationResponse,
    MetacognitiveAnalytics, MetacognitiveAnalyticsResponse, LearningStrategyRequest,
    LearningStrategyResponse, MetacognitiveFeedbackRequest, MetacognitiveFeedbackResponse
)
from models.elaboration_network import (
    ElaborationNetworkRequest, ElaborationNetworkResponse, NetworkOptimizationRequest,
    NetworkOptimizationResponse, ConnectionEnhancementRequest, ConnectionEnhancementResponse,
    PathwayCreationRequest, PathwayCreationResponse, ElaborationAnalytics,
    ElaborationAnalyticsResponse, NetworkVisualizationData, ComparativeRequest,
    ComparativeResponse, UserNetworkProfile, NetworkPersonalization
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Cognitive Learning Engine API",
    description="Evidence-based cognitive learning system with 6 integrated phases",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add exception handlers for standardized error handling
app.add_exception_handler(Exception, cle_exception_handler)
app.add_exception_handler(CLEError, cle_exception_handler)

# Request ID middleware
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Global error handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "detail": str(exc),
            "timestamp": datetime.now().isoformat()
        }
    )

# API Health Check
@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "components": {
            "spaced_repetition": "active",
            "active_recall": "active",
            "dual_coding": "active",
            "interleaved_practice": "active",
            "metacognition": "active",
            "elaboration_network": "active"
        }
    }

# =================== SPACED REPETITION ENDPOINTS ===================

@app.post("/api/v1/spaced-repetition/cards", response_model=LearningCardResponse)
async def create_learning_card(request: LearningCardCreate):
    """Create a new learning card for spaced repetition"""
    try:
        # Validate request data
        if not request.question or len(request.question.strip()) == 0:
            raise_validation_error("Question cannot be empty", {"field": "question"})

        if not request.answer or len(request.answer.strip()) == 0:
            raise_validation_error("Answer cannot be empty", {"field": "answer"})

        card = await spaced_repetition_service.create_card(
            course_id=request.course_id,
            question=request.question,
            answer=request.answer,
            card_type=request.card_type,
            concept_id=request.concept_id,
            context_tags=request.context_tags,
            source_material=request.source_material
        )

        return create_success_response(
            data=card,
            message="Learning card created successfully",
            request_id=getattr(request.state, "request_id", None)
        )
    except CLEError:
        # Re-raise CLE errors to be handled by the exception handler
        raise
    except Exception as e:
        logger.error(f"Error creating learning card: {e}")
        raise ExternalServiceError(
            service_name="spaced_repetition_service",
            message="Failed to create learning card",
            details={"original_error": str(e)}
        )

@app.get("/api/v1/spaced-repetition/courses/{course_id}/cards/due", response_model=List[LearningCardResponse])
async def get_due_cards(course_id: str, user_id: str, limit: int = 20):
    """Get cards due for review"""
    try:
        # Validate input parameters
        if limit < 1 or limit > 100:
            raise_validation_error("Limit must be between 1 and 100", {"field": "limit", "value": limit})

        cards = await spaced_repetition_service.get_due_cards(
            user_id=user_id,
            course_id=course_id,
            limit=limit
        )

        if not cards:
            # This is not an error, just an empty result
            return create_success_response(
                data=[],
                message=f"No due cards found for course {course_id}",
                request_id=getattr(request.state, "request_id", None)
            )

        return create_success_response(
            data=cards,
            message=f"Found {len(cards)} due cards",
            request_id=getattr(request.state, "request_id", None)
        )
    except CLEError:
        raise
    except Exception as e:
        logger.error(f"Error getting due cards: {e}")
        raise ExternalServiceError(
            service_name="spaced_repetition_service",
            message="Failed to retrieve due cards",
            details={"course_id": course_id, "user_id": user_id, "original_error": str(e)}
        )

@app.post("/api/v1/spaced-repetition/cards/review", response_model=CardReviewResponse)
async def review_card(request: CardReviewRequest):
    """Submit a card review"""
    try:
        result = await spaced_repetition_service.review_card(
            card_id=request.card_id,
            quality_rating=request.quality_rating,
            response_time_ms=request.response_time_ms,
            session_id=request.session_id
        )
        return result
    except Exception as e:
        logger.error(f"Error reviewing card: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/spaced-repetition/sessions", response_model=StudySessionResponse)
async def create_study_session(request: StudySessionRequest):
    """Create a new study session"""
    try:
        session = await spaced_repetition_service.create_session(
            user_id=request.user_id,
            course_id=request.course_id,
            session_type=request.session_type,
            max_cards=request.max_cards
        )
        return session
    except Exception as e:
        logger.error(f"Error creating study session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/spaced-repetition/courses/{course_id}/analytics", response_model=LearningAnalytics)
async def get_spaced_repetition_analytics(course_id: str, user_id: str, period_days: int = 30):
    """Get spaced repetition analytics"""
    try:
        analytics = await spaced_repetition_service.get_analytics(
            user_id=user_id,
            course_id=course_id,
            period_days=period_days
        )
        return analytics
    except Exception as e:
        logger.error(f"Error getting spaced repetition analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/spaced-repetition/cards/auto-generate", response_model=AutoGenerateCardsResponse)
async def auto_generate_cards(request: AutoGenerateCardsRequest):
    """Auto-generate learning cards from content"""
    try:
        result = await spaced_repetition_service.auto_generate_cards(
            course_id=request.course_id,
            content=request.content,
            content_type=request.content_type,
            num_cards=request.num_cards
        )
        return result
    except Exception as e:
        logger.error(f"Error auto-generating cards: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# =================== ACTIVE RECALL ENDPOINTS ===================

@app.post("/api/v1/active-recall/questions/generate", response_model=QuestionGenerationResponse)
async def generate_questions(request: QuestionGenerationRequest):
    """Generate questions for active recall"""
    try:
        questions = await active_recall_service.generate_questions(request)
        return questions
    except Exception as e:
        logger.error(f"Error generating questions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/active-recall/questions/adaptive", response_model=AdaptiveQuestionResponse)
async def get_adaptive_questions(request: AdaptiveQuestionRequest):
    """Get adaptive questions based on performance"""
    try:
        response = await active_recall_service.get_adaptive_questions(request)
        return response
    except Exception as e:
        logger.error(f"Error getting adaptive questions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/active-recall/questions/submit", response_model=QuestionSubmissionResponse)
async def submit_question_answer(request: QuestionSubmission):
    """Submit an answer to a question"""
    try:
        result = await active_recall_service.submit_answer(request)
        return result
    except Exception as e:
        logger.error(f"Error submitting answer: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/active-recall/sessions/start", response_model=QuizSessionStartResponse)
async def start_quiz_session(request: QuizSessionStart):
    """Start a new quiz session"""
    try:
        session = await active_recall_service.start_session(request)
        return session
    except Exception as e:
        logger.error(f"Error starting quiz session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/active-recall/sessions/{session_id}/complete", response_model=QuizSessionResponse)
async def complete_quiz_session(session_id: str, user_id: str):
    """Complete a quiz session"""
    try:
        result = await active_recall_service.complete_session(session_id, user_id)
        return result
    except Exception as e:
        logger.error(f"Error completing quiz session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/active-recall/sessions/{session_id}/next-question")
async def get_next_question(session_id: str):
    """Get next question in session"""
    try:
        question = await active_recall_service.get_next_question(session_id)
        return {"success": True, "question": question}
    except Exception as e:
        logger.error(f"Error getting next question: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/active-recall/concepts/extract", response_model=ConceptExtractionResponse)
async def extract_concepts(content: str, course_id: str):
    """Extract concepts from content"""
    try:
        concepts = await active_recall_service.extract_concepts(content, course_id)
        return concepts
    except Exception as e:
        logger.error(f"Error extracting concepts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/active-recall/analytics", response_model=ActiveRecallAnalyticsResponse)
async def get_active_recall_analytics(request: ActiveRecallAnalytics):
    """Get active recall analytics"""
    try:
        analytics = await active_recall_service.get_analytics(request)
        return analytics
    except Exception as e:
        logger.error(f"Error getting active recall analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# =================== DUAL CODING ENDPOINTS ===================

@app.post("/api/v1/dual-coding/content/create", response_model=DualCodingResponse)
async def create_dual_coding_content(request: DualCodingRequest):
    """Create dual coding enhanced content"""
    try:
        content = await dual_coding_service.create_dual_coding_content(
            content=request.content,
            content_type=request.content_type,
            target_audience=request.target_audience,
            learning_style=request.learning_style
        )
        return content
    except Exception as e:
        logger.error(f"Error creating dual coding content: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/dual-coding/content/enhance", response_model=EnhancedContentResponse)
async def enhance_content(request: ContentEnhancementRequest):
    """Enhance existing content with dual coding"""
    try:
        enhanced = await dual_coding_service.enhance_content(
            content_id=request.content_id,
            enhancement_type=request.enhancement_type,
            target_learning_style=request.target_learning_style
        )
        return enhanced
    except Exception as e:
        logger.error(f"Error enhancing content: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/dual-coding/visual-elements")
async def get_visual_elements():
    """Get available visual element types"""
    try:
        elements = await dual_coding_service.get_visual_elements()
        return {"success": True, "elements": elements}
    except Exception as e:
        logger.error(f"Error getting visual elements: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/dual-coding/learning-paths", response_model=LearningPathResponse)
async def create_learning_path(request: LearningPathRequest):
    """Create personalized learning path"""
    try:
        path = await dual_coding_service.create_learning_path(request)
        return path
    except Exception as e:
        logger.error(f"Error creating learning path: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/dual-coding/analytics", response_model=DualCodingAnalyticsResponse)
async def get_dual_coding_analytics(request: DualCodingAnalytics):
    """Get dual coding analytics"""
    try:
        analytics = await dual_coding_service.get_analytics(request)
        return analytics
    except Exception as e:
        logger.error(f"Error getting dual coding analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# =================== INTERLEAVED PRACTICE ENDPOINTS ===================

@app.post("/api/v1/interleaved-practice/schedules", response_model=InterleavedScheduleResponse)
async def create_interleaved_schedule(request: InterleavedScheduleRequest):
    """Create interleaved practice schedule"""
    try:
        schedule = await interleaved_practice_service.create_interleaved_schedule(
            user_id=request.user_id,
            course_id=request.course_id,
            concepts=request.concepts,
            session_duration_minutes=request.session_duration_minutes
        )
        return schedule
    except Exception as e:
        logger.error(f"Error creating interleaved schedule: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/interleaved-practice/patterns")
async def get_practice_patterns():
    """Get available practice patterns"""
    try:
        patterns = await interleaved_practice_service.get_practice_patterns()
        return {"success": True, "patterns": patterns}
    except Exception as e:
        logger.error(f"Error getting practice patterns: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/interleaved-practice/schedules/optimize", response_model=ScheduleOptimizationResponse)
async def optimize_schedule(request: ScheduleOptimizationRequest):
    """Optimize existing practice schedule"""
    try:
        optimized = await interleaved_practice_service.optimize_schedule(
            schedule_id=request.schedule_id,
            optimization_goals=request.optimization_goals,
            user_feedback=request.user_feedback,
            performance_data=request.performance_data
        )
        return optimized
    except Exception as e:
        logger.error(f"Error optimizing schedule: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/interleaved-practice/sessions/{session_id}/feedback")
async def submit_session_feedback(session_id: str, feedback: SessionFeedback):
    """Submit feedback for practice session"""
    try:
        result = await interleaved_practice_service.submit_feedback(session_id, feedback)
        return {"success": True, "result": result}
    except Exception as e:
        logger.error(f"Error submitting session feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/interleaved-practice/analytics", response_model=InterleavedAnalyticsResponse)
async def get_interleaved_analytics(request: InterleavedAnalytics):
    """Get interleaved practice analytics"""
    try:
        analytics = await interleaved_practice_service.get_analytics(request)
        return analytics
    except Exception as e:
        logger.error(f"Error getting interleaved analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/interleaved-practice/user/preferences")
async def update_user_preferences(user_id: str, preferences: UserPreferences):
    """Update user practice preferences"""
    try:
        result = await interleaved_practice_service.update_user_preferences(user_id, preferences)
        return {"success": True, "result": result}
    except Exception as e:
        logger.error(f"Error updating user preferences: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/interleaved-practice/users/{user_id}/preferences")
async def get_user_preferences(user_id: str):
    """Get user practice preferences"""
    try:
        preferences = await interleaved_practice_service.get_user_preferences(user_id)
        return {"success": True, "preferences": preferences}
    except Exception as e:
        logger.error(f"Error getting user preferences: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# =================== METACOGNITION ENDPOINTS ===================

@app.post("/api/v1/metacognition/sessions", response_model=MetacognitiveSessionResponse)
async def create_metacognitive_session(request: MetacognitiveSessionCreate):
    """Create a comprehensive metacognitive session"""
    try:
        session = await metacognition_service.create_metacognitive_session(
            user_id=request.user_id,
            course_id=request.course_id,
            learning_context=request.learning_context,
            session_type=request.session_type
        )
        return session
    except Exception as e:
        logger.error(f"Error creating metacognitive session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/metacognition/reflection-activities", response_model=ReflectionActivityResponse)
async def create_reflection_activity(request: ReflectionActivityRequest):
    """Create a reflection activity for metacognitive development"""
    try:
        activity = await metacognition_service.create_reflection_activity(
            user_id=request.user_id,
            course_id=request.course_id,
            activity_type=request.activity_type,
            reflection_context=request.reflection_context
        )
        return activity
    except Exception as e:
        logger.error(f"Error creating reflection activity: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/metacognition/self-regulation", response_model=SelfRegulationResponse)
async def create_self_regulation_activity(request: SelfRegulationRequest):
    """Create a self-regulation activity"""
    try:
        activity = await metacognition_service.create_self_regulation_activity(
            user_id=request.user_id,
            course_id=request.course_id,
            regulation_phase=request.regulation_phase,
            context=request.context
        )
        return activity
    except Exception as e:
        logger.error(f"Error creating self-regulation activity: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/metacognition/analytics", response_model=MetacognitiveAnalyticsResponse)
async def get_metacognitive_analytics(request: MetacognitiveAnalytics):
    """Get metacognitive analytics for a user"""
    try:
        analytics = await metacognition_service.get_metacognitive_analytics(
            user_id=request.user_id,
            course_id=request.course_id,
            period_days=request.period_days
        )
        return analytics
    except Exception as e:
        logger.error(f"Error getting metacognitive analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/metacognition/learning-strategies", response_model=LearningStrategyResponse)
async def recommend_learning_strategy(request: LearningStrategyRequest):
    """Get personalized learning strategy recommendations"""
    try:
        strategy = await metacognition_service.recommend_learning_strategy(
            user_id=request.user_id,
            learning_context=request.learning_context,
            performance_data=request.performance_data
        )
        return strategy
    except Exception as e:
        logger.error(f"Error recommending learning strategy: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/metacognition/feedback", response_model=MetacognitiveFeedbackResponse)
async def process_metacognitive_feedback(request: MetacognitiveFeedbackRequest):
    """Process metacognitive feedback and generate insights"""
    try:
        feedback = await metacognition_service.process_metacognitive_feedback(
            user_id=request.user_id,
            feedback_type=request.feedback_type,
            feedback_data=request.feedback_data
        )
        return feedback
    except Exception as e:
        logger.error(f"Error processing metacognitive feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# =================== ELABORATION NETWORK ENDPOINTS ===================

@app.post("/api/v1/elaboration-network/build", response_model=ElaborationNetworkResponse)
async def build_elaboration_network(request: ElaborationNetworkRequest):
    """Build a comprehensive elaboration network integrating all CLE phases"""
    try:
        network = await elaboration_network_service.build_elaboration_network(
            user_id=request.user_id,
            course_id=request.course_id,
            knowledge_base=request.knowledge_base,
            learning_objectives=request.learning_objectives,
            integration_level=request.integration_level,
            transfer_goals=request.transfer_goals,
            focus_concepts=request.focus_concepts
        )
        return network
    except Exception as e:
        logger.error(f"Error building elaboration network: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/elaboration-network/optimize", response_model=NetworkOptimizationResponse)
async def optimize_network(request: NetworkOptimizationRequest):
    """Optimize an existing elaboration network"""
    try:
        optimized = await elaboration_network_service.optimize_network(
            network_id=request.network_id,
            optimization_goals=request.optimization_goals,
            user_feedback=request.user_feedback,
            performance_data=request.performance_data
        )
        return optimized
    except Exception as e:
        logger.error(f"Error optimizing network: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/elaboration-network/connections/enhance", response_model=ConnectionEnhancementResponse)
async def enhance_connections(request: ConnectionEnhancementRequest):
    """Enhance specific connections in the elaboration network"""
    try:
        enhanced = await elaboration_network_service.enhance_connections(
            network_id=request.network_id,
            connection_ids=request.connection_ids,
            enhancement_type=request.enhancement_type,
            enhancement_reason=request.enhancement_reason,
            target_outcomes=request.target_outcomes
        )
        return enhanced
    except Exception as e:
        logger.error(f"Error enhancing connections: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/elaboration-network/pathways/create", response_model=PathwayCreationResponse)
async def create_transfer_pathways(request: PathwayCreationRequest):
    """Create transfer pathways between concepts"""
    try:
        pathways = await elaboration_network_service.create_transfer_pathways(
            network_id=request.network_id,
            source_concepts=request.source_concepts,
            target_domains=request.target_domains,
            pathway_type=request.pathway_type,
            constraints=request.constraints,
            preferences=request.preferences
        )
        return pathways
    except Exception as e:
        logger.error(f"Error creating transfer pathways: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/elaboration-network/analytics", response_model=ElaborationAnalyticsResponse)
async def get_elaboration_analytics(request: ElaborationAnalytics):
    """Get comprehensive elaboration network analytics"""
    try:
        analytics = await elaboration_network_service.get_elaboration_analytics(
            user_id=request.user_id,
            course_id=request.course_id,
            period_days=request.period_days,
            analysis_type=request.analysis_type
        )
        return analytics
    except Exception as e:
        logger.error(f"Error getting elaboration analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/elaboration-network/visualize", response_model=NetworkVisualizationData)
async def visualize_network(request: dict):
    """Generate visualization data for the elaboration network"""
    try:
        network_id = request.get("network_id")
        visualization_config = request.get("config", {})

        visualization = await elaboration_network_service.generate_network_visualization(
            network_id=network_id,
            config=visualization_config
        )
        return visualization
    except Exception as e:
        logger.error(f"Error generating network visualization: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/elaboration-network/comparative-analysis", response_model=ComparativeResponse)
async def comparative_analysis(request: ComparativeRequest):
    """Perform comparative analysis of network development"""
    try:
        analysis = await elaboration_network_service.perform_comparative_analysis(
            user_id=request.user_id,
            comparison_type=request.comparison_type,
            time_periods=request.time_periods,
            baseline_period=request.baseline_period,
            metrics_to_compare=request.metrics_to_compare,
            include_visualizations=request.include_visualizations
        )
        return analysis
    except Exception as e:
        logger.error(f"Error performing comparative analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/elaboration-network/user-profile", response_model=UserNetworkProfile)
async def update_user_profile(request: UserNetworkProfile):
    """Update user network profile and preferences"""
    try:
        profile = await elaboration_network_service.update_user_profile(
            user_id=request.user_id,
            profile_data=request.dict()
        )
        return profile
    except Exception as e:
        logger.error(f"Error updating user profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/elaboration-network/personalize", response_model=NetworkPersonalization)
async def personalize_network(request: NetworkPersonalization):
    """Create personalized network adaptations"""
    try:
        personalization = await elaboration_network_service.create_network_personalization(
            user_id=request.user_id,
            network_id=request.network_id,
            customization_preferences=request.customization_preferences,
            learning_objectives=request.learning_objectives,
            challenge_areas=request.challenge_areas,
            strength_areas=request.strength_areas
        )
        return personalization
    except Exception as e:
        logger.error(f"Error creating network personalization: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/elaboration-network/{network_id}/export")
async def export_network(network_id: str, format: str = "json"):
    """Export elaboration network in specified format"""
    try:
        export_data = await elaboration_network_service.export_network(
            network_id=network_id,
            format=format,
            include_analytics=True,
            include_activities=True
        )
        return export_data
    except Exception as e:
        logger.error(f"Error exporting network: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/elaboration-network/{network_id}/activities")
async def get_network_activities(network_id: str, limit: int = 50):
    """Get elaboration activities for a network"""
    try:
        activities = await elaboration_network_service.get_network_activities(
            network_id=network_id,
            limit=limit
        )
        return {"success": True, "activities": activities, "total_count": len(activities)}
    except Exception as e:
        logger.error(f"Error getting network activities: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/elaboration-network/{network_id}/pathways")
async def get_transfer_pathways(network_id: str, domain: Optional[str] = None):
    """Get transfer pathways for a network"""
    try:
        pathways = await elaboration_network_service.get_transfer_pathways(
            network_id=network_id,
            domain_filter=domain
        )
        return {"success": True, "pathways": pathways, "total_count": len(pathways)}
    except Exception as e:
        logger.error(f"Error getting transfer pathways: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/elaboration-network/{network_id}/connections")
async def get_network_connections(network_id: str, connection_type: Optional[str] = None):
    """Get connections in the elaboration network"""
    try:
        connections = await elaboration_network_service.get_network_connections(
            network_id=network_id,
            connection_type_filter=connection_type
        )
        return {"success": True, "connections": connections, "total_count": len(connections)}
    except Exception as e:
        logger.error(f"Error getting network connections: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# =================== UTILITY ENDPOINTS ===================

@app.get("/api/v1/info")
async def get_api_info():
    """Get API information and capabilities"""
    return {
        "name": "Cognitive Learning Engine API",
        "version": "1.0.0",
        "description": "Evidence-based cognitive learning system",
        "phases": [
            {
                "name": "Spaced Repetition",
                "description": "Algorithmic memory retention system",
                "status": "active"
            },
            {
                "name": "Active Recall",
                "description": "Systematic knowledge retrieval practice",
                "status": "active"
            },
            {
                "name": "Dual Coding",
                "description": "Visual-verbal integration learning",
                "status": "active"
            },
            {
                "name": "Interleaved Practice",
                "description": "Mixed concept practice scheduling",
                "status": "active"
            },
            {
                "name": "Metacognition",
                "description": "Self-regulation and reflection framework",
                "status": "active"
            },
            {
                "name": "Elaboration Network",
                "description": "Knowledge integration and transfer system",
                "status": "active"
            }
        ],
        "total_endpoints": 45,
        "status": "production_ready",
        "last_updated": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")