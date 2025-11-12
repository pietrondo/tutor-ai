"""
Enhanced Mindmap API with Cognitive Load Theory and GLM-4.6 Integration
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from services.enhanced_mindmap_service import EnhancedMindmapService
from rag_service import RAGService
from llm_service import LLMService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/courses/{course_id}/books/{book_id}/enhanced-mindmaps", tags=["enhanced-mindmaps"])

class EnhancedMindmapRequest(BaseModel):
    """Request model for enhanced mindmap generation"""
    topic: str = Field(..., description="Main topic for the mindmap")
    focus_areas: Optional[List[str]] = Field(default=None, description="Specific areas to focus on")
    learner_profile: Optional[Dict[str, Any]] = Field(default=None, description="Learner characteristics")
    cognitive_load_level: Optional[str] = Field(default=None, description="minimal|moderate|complex|expert")
    knowledge_type: Optional[str] = Field(default=None, description="factual|conceptual|procedural|metacognitive")
    previous_mindmaps: Optional[List[Dict[str, Any]]] = Field(default=None, description="Previously generated mindmaps")

class EnhancedMindmapResponse(BaseModel):
    """Response model for enhanced mindmap"""
    id: str
    title: str
    overview: str
    cognitive_load_level: str
    knowledge_type: str
    nodes: List[Dict[str, Any]]
    relationships: List[Dict[str, Any]]
    study_guidance: Dict[str, Any]
    learning_optimizations: Dict[str, Any]
    metadata: Dict[str, Any]

class CognitiveProfileRequest(BaseModel):
    """Request for cognitive profile analysis"""
    experience_level: Optional[str] = Field(default="intermediate", description="beginner|intermediate|advanced")
    attention_span: Optional[str] = Field(default="moderate", description="short|moderate|long")
    visual_preference: Optional[str] = Field(default="high", description="low|moderate|high")
    complexity_tolerance: Optional[str] = Field(default="moderate", description="low|moderate|high")
    learning_style: Optional[str] = Field(default="mixed", description="visual|auditory|kinesthetic|mixed")
    previous_exposure: Optional[List[str]] = Field(default=None, description="Previous topics studied")
    preferred_depth: Optional[str] = Field(default="balanced", description="surface|balanced|deep")

class CognitiveProfileResponse(BaseModel):
    """Response with cognitive profile analysis"""
    profile_analysis: Dict[str, Any]
    recommendations: Dict[str, Any]
    optimal_mindmap_settings: Dict[str, str]

# Initialize services
enhanced_mindmap_service = EnhancedMindmapService()
rag_service = RAGService()
llm_service = LLMService()

@router.post("/generate", response_model=EnhancedMindmapResponse)
async def generate_enhanced_mindmap(
    course_id: str,
    book_id: str,
    request: EnhancedMindmapRequest
):
    """
    Generate enhanced mindmap using cognitive load theory and GLM-4.6 relationship modeling
    """
    try:
        logger.info(f"Generating enhanced mindmap for course {course_id}, book {book_id}")
        logger.info(f"Topic: {request.topic}, Cognitive Load: {request.cognitive_load_level}")

        # Retrieve context materials using RAG
        rag_context_prompt = f"Generate enhanced mindmap for {request.topic}"
        if request.focus_areas:
            rag_context_prompt += f" with focus on: {', '.join(request.focus_areas)}"

        rag_response = await rag_service.retrieve_context(
            rag_context_prompt,
            course_id=course_id,
            book_id=book_id,
            k=8  # More context for enhanced generation
        )

        context_text = rag_response.get("text", "")
        logger.info(f"Retrieved {len(context_text)} characters of context")

        if not context_text.strip():
            logger.warning("No context retrieved, using minimal approach")
            context_text = f"Argomento: {request.topic}\nFocus: {', '.join(request.focus_areas) if request.focus_areas else 'Generale'}"

        # Generate enhanced mindmap
        mindmap_result = await enhanced_mindmap_service.generate_enhanced_mindmap(
            topic=request.topic,
            context_text=context_text,
            course_id=course_id,
            book_id=book_id,
            learner_profile=request.learner_profile,
            cognitive_load_level=request.cognitive_load_level,
            knowledge_type=request.knowledge_type,
            focus_areas=request.focus_areas,
            previous_mindmaps=request.previous_mindmaps
        )

        logger.info(f"Enhanced mindmap generated successfully: {mindmap_result.get('id')}")

        return EnhancedMindmapResponse(**mindmap_result)

    except Exception as e:
        logger.error(f"Enhanced mindmap generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate enhanced mindmap: {str(e)}")

@router.post("/analyze-profile", response_model=CognitiveProfileResponse)
async def analyze_cognitive_profile(
    profile_request: CognitiveProfileRequest
):
    """
    Analyze learner profile and provide recommendations for optimal mindmap settings
    """
    try:
        # Use enhanced mindmap service to analyze profile
        profile_analysis = enhanced_mindmap_service._analyze_learner_profile(
            profile_request.dict()
        )

        # Generate recommendations based on profile
        recommendations = _generate_profile_recommendations(profile_analysis)

        # Determine optimal mindmap settings
        optimal_settings = _determine_optimal_settings(profile_analysis)

        return CognitiveProfileResponse(
            profile_analysis=profile_analysis,
            recommendations=recommendations,
            optimal_mindmap_settings=optimal_settings
        )

    except Exception as e:
        logger.error(f"Profile analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to analyze profile: {str(e)}")

@router.get("/cognitive-levels")
async def get_cognitive_load_levels():
    """
    Get available cognitive load levels with descriptions
    """
    return {
        "cognitive_load_levels": {
            "minimal": {
                "description": "Per principianti o concetti molto complessi",
                "max_concepts": "4-8 concetti totali",
                "max_branches": "3 rami per nodo",
                "recommended_for": "Prima esposizione all'argomento, learners ansiosi"
            },
            "moderate": {
                "description": "Livello intermedio bilanciato",
                "max_concepts": "6-15 concetti totali",
                "max_branches": "4 rami per nodo",
                "recommended_for": "La maggior parte degli studenti, revisione standard"
            },
            "complex": {
                "description": "Per studenti esperti o argomenti ricchi",
                "max_concepts": "8-25 concetti totali",
                "max_branches": "5 rami per nodo",
                "recommended_for": "Studenti avanzati, approfondimenti"
            },
            "expert": {
                "description": "Massima complessità per esperti",
                "max_concepts": "10-40+ concetti totali",
                "max_branches": "6 rami per nodo",
                "recommended_for": "Specialisti, revisione completa"
            }
        }
    }

@router.get("/knowledge-types")
async def get_knowledge_types():
    """
    Get available knowledge types with descriptions
    """
    return {
        "knowledge_types": {
            "factual": {
                "description": "Fatti, termini, definizioni, concetti base",
                "focus": "Memorizzazione e richiamo preciso",
                "example": "Definizioni di termini tecnici, date, formule"
            },
            "conceptual": {
                "description": "Relazioni, categorie, principi, teorie",
                "focus": "Comprensione profonda e connessioni",
                "example": "Teorie scientifiche, modelli concettuali, framework"
            },
            "procedural": {
                "description": "Processi, metodi, procedure, come fare",
                "focus": "Esecuzione e applicazione pratica",
                "example": "Procedimenti matematici, protocolli di laboratorio"
            },
            "metacognitive": {
                "description": "Strategie di apprendimento, riflessione",
                "focus": "Auto-regolazione e consapevolezza",
                "example": "Tecniche di studio, strategie di problem solving"
            }
        }
    }

@router.get("/examples")
async def get_mindmap_examples():
    """
    Get examples of enhanced mindmaps for different scenarios
    """
    return {
        "examples": [
            {
                "scenario": "Studente universitario principiante",
                "settings": {
                    "cognitive_load_level": "minimal",
                    "knowledge_type": "conceptual",
                    "learner_profile": {
                        "experience_level": "beginner",
                        "complexity_tolerance": "low"
                    }
                },
                "expected_structure": "4-6 concetti principali con relazioni semplici"
            },
            {
                "scenario": "Studente avanzato revisione",
                "settings": {
                    "cognitive_load_level": "complex",
                    "knowledge_type": "procedural",
                    "learner_profile": {
                        "experience_level": "advanced",
                        "complexity_tolerance": "high"
                    }
                },
                "expected_structure": "10-15 concetti con relazioni complesse e cross-connections"
            },
            {
                "scenario": "Studio per esame pratico",
                "settings": {
                    "cognitive_load_level": "moderate",
                    "knowledge_type": "procedural",
                    "learner_profile": {
                        "preferred_depth": "balanced"
                    }
                },
                "expected_structure": "6-10 concetti focalizzati su processi e passaggi"
            }
        ]
    }

def _generate_profile_recommendations(profile_analysis: Dict[str, Any]) -> Dict[str, Any]:
    """Generate recommendations based on cognitive profile analysis"""

    recommendations = {
        "study_strategies": [],
        "mindmap_preferences": {},
        "learning_tips": []
    }

    experience = profile_analysis.get("experience_level", "intermediate")
    tolerance = profile_analysis.get("complexity_tolerance", "moderate")
    cognitive_capacity = profile_analysis.get("cognitive_capacity", "moderate")

    # Study strategies
    if experience == "beginner":
        recommendations["study_strategies"].extend([
            "Inizia con mappe semplici e gradualmente aumenta la complessità",
            "Usa esempi concreti e analogie",
            "Fai frequenti pause per consolidare le informazioni"
        ])
    elif experience == "advanced":
        recommendations["study_strategies"].extend([
            "Crea mappe complesse con molte interconnessioni",
            "Esplora applicazioni avanzate e contesti diversi",
            "Usa le mappe per integrare conoscenze da diverse fonti"
        ])

    if tolerance == "low":
        recommendations["study_strategies"].append("Concentrati su pochi concetti chiave per volta")

    # Mindmap preferences
    if cognitive_capacity == "lower":
        recommendations["mindmap_preferences"] = {
            "cognitive_load_level": "minimal",
            "max_concepts_per_session": 5,
            "use_visual_aids": True
        }
    elif cognitive_capacity == "higher":
        recommendations["mindmap_preferences"] = {
            "cognitive_load_level": "complex",
            "max_concepts_per_session": 15,
            "include_cross_connections": True
        }

    # Learning tips
    visual_preference = profile_analysis.get("visual_preference", "moderate")
    if visual_preference == "high":
        recommendations["learning_tips"].append("Sfrutta gli elementi visivi e i colori nella mappa")

    attention_span = profile_analysis.get("attention_span", "moderate")
    if attention_span == "short":
        recommendations["learning_tips"].append("Dividi lo studio in sessioni brevi e intensive")

    return recommendations

def _determine_optimal_settings(profile_analysis: Dict[str, Any]) -> Dict[str, str]:
    """Determine optimal mindmap settings based on profile"""

    experience = profile_analysis.get("experience_level", "intermediate")
    tolerance = profile_analysis.get("complexity_tolerance", "moderate")
    cognitive_capacity = profile_analysis.get("cognitive_capacity", "moderate")

    # Determine cognitive load level
    if experience == "beginner" or tolerance == "low":
        cognitive_load = "minimal"
    elif experience == "advanced" and tolerance == "high":
        cognitive_load = "expert"
    elif tolerance == "high":
        cognitive_load = "complex"
    else:
        cognitive_load = "moderate"

    # Determine knowledge type preference based on learning style
    learning_style = profile_analysis.get("learning_style", "mixed")
    if learning_style == "visual":
        knowledge_type = "conceptual"
    elif learning_style == "kinesthetic":
        knowledge_type = "procedural"
    else:
        knowledge_type = "conceptual"  # Default

    return {
        "cognitive_load_level": cognitive_load,
        "knowledge_type": knowledge_type,
        "complexity_tolerance": tolerance,
        "experience_level": experience
    }

@router.get("/health")
async def enhanced_mindmap_health_check():
    """
    Health check for enhanced mindmap service
    """
    return {
        "status": "healthy",
        "features": {
            "cognitive_load_optimization": True,
            "glm46_integration": True,
            "learning_science_integration": True,
            "personalization": True,
            "dual_coding": True,
            "metacognitive_support": True
        },
        "supported_knowledge_types": ["factual", "conceptual", "procedural", "metacognitive"],
        "supported_cognitive_levels": ["minimal", "moderate", "complex", "expert"],
        "services": {
            "enhanced_mindmap_service": "active",
            "rag_service": "active",
            "llm_service": "active"
        }
    }