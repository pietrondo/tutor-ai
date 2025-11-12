"""
Enhanced Study Plan API with Learning Science and GLM-4.6 Integration
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from services.enhanced_study_plan_service import EnhancedStudyPlanService
from rag_service import RAGService
from llm_service import LLMService
from services.study_planner_service import StudyPlannerService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/courses/{course_id}/enhanced-study-plans", tags=["enhanced-study-plans"])

class LearnerProfileRequest(BaseModel):
    """Request model for learner profile analysis"""
    experience_level: Optional[str] = Field(default="intermediate", description="beginner|intermediate|advanced")
    study_discipline: Optional[str] = Field(default="moderate", description="low|moderate|high")
    time_availability: Optional[str] = Field(default="moderate", description="low|moderate|high")
    motivation_level: Optional[str] = Field(default="moderate", description="low|moderate|high")
    preferred_session_length: Optional[str] = Field(default="moderate", description="short|moderate|long")
    learning_style: Optional[str] = Field(default="mixed", description="visual|auditory|kinesthetic|mixed")
    challenge_tolerance: Optional[str] = Field(default="moderate", description="low|moderate|high")
    feedback_preference: Optional[str] = Field(default="regular", description="immediate|regular|minimal")
    working_memory: Optional[str] = Field(default="average", description="low|average|high")
    attention_span: Optional[str] = Field(default="moderate", description="short|moderate|long")
    processing_speed: Optional[str] = Field(default="average", description="slow|average|fast")
    metacognitive_awareness: Optional[str] = Field(default="developing", description="beginner|developing|advanced")
    strength_areas: Optional[List[str]] = Field(default=[], description="Areas where learner excels")
    improvement_areas: Optional[List[str]] = Field(default=[], description="Areas needing improvement")
    difficulty_progression: Optional[str] = Field(default="gradual", description="gradual|steep|adaptive")

class TimeConstraintsRequest(BaseModel):
    """Request model for time constraints"""
    hours_per_week: Optional[float] = Field(default=10.0, description="Study hours available per week")
    deadline: Optional[str] = Field(default=None, description="Target completion date")
    preferred_study_days: Optional[List[str]] = Field(default=[], description="Preferred study days")
    session_preferences: Optional[str] = Field(default="moderate", description="Preferred session length")
    buffer_time_percentage: Optional[float] = Field(default=20.0, description="Extra time buffer percentage")
    intensive_periods: Optional[List[Dict[str, Any]]] = Field(default=[], description="Periods of intensive study")

class LearningObjectiveRequest(BaseModel):
    """Request model for learning objectives"""
    id: Optional[str] = None
    title: str
    description: Optional[str] = None
    priority: Optional[str] = Field(default="medium", description="low|medium|high|critical")
    cognitive_level: Optional[str] = Field(default="application", description="remember|understand|apply|analyze|evaluate|create")
    mastery_criteria: Optional[str] = None

class EnhancedStudyPlanRequest(BaseModel):
    """Request model for enhanced study plan generation"""
    learner_profile: Optional[LearnerProfileRequest] = None
    study_preferences: Optional[Dict[str, Any]] = Field(default={}, description="Study format and timing preferences")
    time_constraints: Optional[TimeConstraintsRequest] = None
    learning_objectives: Optional[List[LearningObjectiveRequest]] = Field(default=[], description="Specific learning goals")
    previous_performance: Optional[Dict[str, Any]] = Field(default={}, description="Historical performance data")
    focus_areas: Optional[List[str]] = Field(default=[], description="Specific areas to focus on")
    custom_strategies: Optional[List[str]] = Field(default=[], description="Preferred learning strategies")

class StudyPlanGenerationResponse(BaseModel):
    """Response model for study plan generation"""
    plan_id: str
    course_id: str
    learner_profile: Dict[str, Any]
    learning_trajectory: Dict[str, Any]
    study_sessions: List[Dict[str, Any]]
    practice_schedule: Dict[str, Any]
    metacognitive_framework: Dict[str, Any]
    adaptive_elements: Dict[str, Any]
    learning_strategies: Dict[str, Any]
    objectives_mastery: Dict[str, Any]
    performance_tracking: Dict[str, Any]
    timeline: Dict[str, Any]
    success_metrics: Dict[str, Any]
    metadata: Dict[str, Any]

class StudyPlanAnalysisResponse(BaseModel):
    """Response model for study plan analysis"""
    current_performance: Dict[str, Any]
    recommendations: List[Dict[str, Any]]
    adjustment_suggestions: Dict[str, Any]
    next_steps: List[str]
    success_probability: float
    risk_factors: List[str]

# Initialize services
enhanced_study_plan_service = EnhancedStudyPlanService()
rag_service = RAGService()
llm_service = LLMService()
study_planner_service = StudyPlannerService()

@router.post("/generate", response_model=StudyPlanGenerationResponse)
async def generate_enhanced_study_plan(
    course_id: str,
    request: EnhancedStudyPlanRequest,
    background_tasks: BackgroundTasks
):
    """
    Generate enhanced study plan using learning science principles and GLM-4.6 long-term reasoning
    """
    try:
        logger.info(f"Generating enhanced study plan for course {course_id}")
        logger.info(f"Learner experience: {request.learner_profile.experience_level if request.learner_profile else 'unknown'}")
        logger.info(f"Time availability: {request.time_constraints.hours_per_week if request.time_constraints else 'unspecified'} hours/week")

        # Retrieve course content using RAG
        documents_result = await rag_service.search_documents(course_id)

        if not documents_result.get('documents'):
            raise HTTPException(status_code=404, detail="No course materials found")

        # Prepare course content structure
        course_content = {
            "topics": [],
            "materials": documents_result.get('documents', []),
            "chapters": [],
            "estimated_total_hours": 0
        }

        # Extract topics and structure from documents
        for doc in documents_result.get('documents', []):
            # Add document as material
            course_content["materials"].append({
                "source": doc.get('source'),
                "chunks_count": doc.get('total_chunks', 0)
            })

            # Extract basic topics from document source
            source_name = doc.get('source', '')
            if source_name:
                # Simple topic extraction from filename
                topic = source_name.split('/')[-1].split('.')[0] if '/' in source_name else source_name.split('.')[0]
                if topic and topic not in course_content["topics"]:
                    course_content["topics"].append(topic)

        # Get existing study planner chapters if available
        try:
            book_chapters = study_planner_service._collect_course_chapters(course_id)
            course_content["chapters"] = book_chapters
        except Exception as e:
            logger.warning(f"Could not retrieve book chapters: {e}")
            course_content["chapters"] = []

        # Estimate total study time
        total_chunks = sum(doc.get('total_chunks', 0) for doc in documents_result.get('documents', []))
        course_content["estimated_total_hours"] = max(20, total_chunks * 0.5)  # Rough estimation

        logger.info(f"Course content prepared: {len(course_content['topics'])} topics, {len(course_content['chapters'])} chapters")

        # Prepare request data
        learner_profile = request.learner_profile.dict() if request.learner_profile else {}
        time_constraints = request.time_constraints.dict() if request.time_constraints else {}
        learning_objectives = [obj.dict() for obj in request.learning_objectives] if request.learning_objectives else []

        # Generate enhanced study plan
        study_plan_result = await enhanced_study_plan_service.generate_enhanced_study_plan(
            course_id=course_id,
            course_content=course_content,
            learner_profile=learner_profile,
            study_preferences=request.study_preferences,
            time_constraints=time_constraints,
            learning_objectives=learning_objectives,
            previous_performance=request.previous_performance
        )

        logger.info(f"Enhanced study plan generated successfully: {study_plan_result.get('plan_id')}")
        logger.info(f"Total sessions: {len(study_plan_result.get('study_sessions', []))}")

        return StudyPlanGenerationResponse(**study_plan_result)

    except Exception as e:
        logger.error(f"Enhanced study plan generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate enhanced study plan: {str(e)}")

@router.post("/analyze-learner-profile")
async def analyze_learner_profile(profile_request: LearnerProfileRequest):
    """
    Analyze learner profile and provide detailed assessment
    """
    try:
        learner_analysis = enhanced_study_plan_service._analyze_learner_profile(
            profile_request.dict(), {}
        )

        # Generate detailed recommendations
        recommendations = _generate_learner_recommendations(learner_analysis)

        return {
            "profile_analysis": learner_analysis,
            "recommendations": recommendations,
            "optimal_study_strategies": _determine_optimal_strategies(learner_analysis),
            "potential_challenges": _identify_potential_challenges(learner_analysis),
            "success_factors": _identify_success_factors(learner_analysis)
        }

    except Exception as e:
        logger.error(f"Learner profile analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to analyze learner profile: {str(e)}")

@router.get("/learning-science-principles")
async def get_learning_science_principles():
    """
    Get comprehensive learning science principles and their applications
    """
    return {
        "learning_science_principles": {
            "spaced_repetition": {
                "description": "Distribute study sessions over increasing intervals",
                "effectiveness": 0.85,
                "optimal_intervals": [1, 3, 7, 14, 30],
                "applications": ["vocabulary_learning", "concept_mastery", "skill_retention"],
                "implementation": "Review material at systematically increasing intervals"
            },
            "interleaved_practice": {
                "description": "Mix different topics or problem types in study sessions",
                "effectiveness": 0.75,
                "benefits": ["better_discrimination", "improved_transfer", "enhanced_retention"],
                "applications": ["mathematics", "science_concepts", "language_learning"],
                "implementation": "Alternate between related but distinct concepts"
            },
            "elaborative_interrogation": {
                "description": "Generate explanations for why stated facts are true",
                "effectiveness": 0.82,
                "benefits": ["deeper_processing", "better_integration", "improved_understanding"],
                "applications": ["conceptual_learning", "cause_effect_relationships"],
                "implementation": "Ask 'why' and 'how' questions about material"
            },
            "dual_coding": {
                "description": "Combine verbal and visual information",
                "effectiveness": 0.70,
                "benefits": ["multiple_representation", "improved_recall", "better_comprehension"],
                "applications": ["diagrams", "mind_maps", "visual_explanations"],
                "implementation": "Create visual representations alongside text"
            },
            "retrieval_practice": {
                "description": "Actively recall information from memory",
                "effectiveness": 0.82,
                "benefits": ["strengthened_memory", "improved_access", "better_retention"],
                "applications": ["self-testing", "flashcards", "practice_problems"],
                "implementation": "Test yourself without looking at materials"
            },
            "concrete_examples": {
                "description": "Use concrete, relatable examples to explain abstract concepts",
                "effectiveness": 0.76,
                "benefits": ["better_understanding", "improved_application", "enhanced_memory"],
                "applications": ["abstract_concepts", "theoretical_principles"],
                "implementation": "Connect new concepts to familiar examples"
            }
        },
        "strategy_combinations": {
            "beginner_learners": ["spaced_repetition", "retrieval_practice", "concrete_examples"],
            "intermediate_learners": ["interleaved_practice", "elaborative_interrogation", "dual_coding"],
            "advanced_learners": ["elaborative_interrogation", "interleaved_practice", "metacognitive_reflection"]
        }
    }

@router.get("/bloom-taxonomy-guide")
async def get_bloom_taxonomy_guide():
    """
    Get Bloom's taxonomy guide for objective classification
    """
    return {
        "bloom_taxonomy": {
            "remember": {
                "level": 1,
                "description": "Recall facts and basic concepts",
                "keywords": ["list", "define", "identify", "name", "recall", "recognize"],
                "assessment_methods": ["multiple_choice", "fill_in_blank", "matching"],
                "study_activities": ["flashcards", "repetition", "summarization"],
                "example_objectives": ["List the main components of X", "Define key terminology"]
            },
            "understand": {
                "level": 2,
                "description": "Explain ideas or concepts",
                "keywords": ["explain", "describe", "summarize", "interpret", "classify"],
                "assessment_methods": ["short_answer", "explanation", "classification"],
                "study_activities": ["paraphrasing", "concept_explanation", "analogy_creation"],
                "example_objectives": ["Explain the process of X", "Summarize the main arguments"]
            },
            "apply": {
                "level": 3,
                "description": "Use information in new situations",
                "keywords": ["apply", "implement", "use", "execute", "carry_out"],
                "assessment_methods": ["problem_solving", "case_studies", "practical_exercises"],
                "study_activities": ["practice_problems", "simulations", "real_world_application"],
                "example_objectives": ["Apply theory to solve X", "Implement Y process"]
            },
            "analyze": {
                "level": 4,
                "description": "Draw connections among ideas",
                "keywords": ["analyze", "compare", "examine", "break_down", "differentiate"],
                "assessment_methods": ["comparative_analysis", "case_study_analysis", "critique"],
                "study_activities": ["concept_mapping", "comparison_tables", "critical_analysis"],
                "example_objectives": ["Analyze the relationship between X and Y", "Compare different approaches"]
            },
            "evaluate": {
                "level": 5,
                "description": "Justify a stand or decision",
                "keywords": ["evaluate", "judge", "critique", "assess", "validate"],
                "assessment_methods": ["evaluation_rubrics", "argument_analysis", "critique"],
                "study_activities": ["peer_review", "critique_analysis", "evaluation_frameworks"],
                "example_objectives": ["Evaluate the effectiveness of X", "Judge the quality of Y"]
            },
            "create": {
                "level": 6,
                "description": "Produce new or original work",
                "keywords": ["create", "design", "develop", "construct", "produce"],
                "assessment_methods": ["project_based", "design_tasks", "creative_outputs"],
                "study_activities": ["design_projects", "creative_synthesis", "innovation_tasks"],
                "example_objectives": ["Create a solution for X", "Design an improved version of Y"]
            }
        },
        "objective_classification_guide": {
            "verbs_by_level": {
                "remember": ["list", "name", "define", "identify", "recall", "recognize", "record"],
                "understand": ["explain", "describe", "summarize", "interpret", "classify", "paraphrase"],
                "apply": ["apply", "use", "implement", "execute", "carry_out", "demonstrate"],
                "analyze": ["analyze", "compare", "examine", "break_down", "differentiate", "investigate"],
                "evaluate": ["evaluate", "judge", "critique", "assess", "validate", "appraise"],
                "create": ["create", "design", "develop", "construct", "produce", "synthesize"]
            },
            "progression_guidelines": {
                "beginner": "Focus on remember and understand levels",
                "intermediate": "Include apply and analyze levels",
                "advanced": "Emphasize evaluate and create levels"
            }
        }
    }

@router.get("/metacognitive-tools")
async def get_metacognitive_tools():
    """
    Get comprehensive metacognitive development tools
    """
    return {
        "metacognitive_tools": {
            "planning_tools": {
                "goal_setting": {
                    "description": "Set specific, measurable, achievable, relevant, time-bound goals",
                    "techniques": ["SMART_goals", "backward_planning", "milestone_setting"],
                    "templates": ["weekly_objectives", "session_goals", "long_term_targets"]
                },
                "strategy_selection": {
                    "description": "Choose appropriate learning strategies for tasks",
                    "techniques": ["strategy_matching", "effectiveness_prediction", "resource_identification"],
                    "considerations": ["task_type", "personal_strengths", "available_resources"]
                },
                "time_allocation": {
                    "description": "Plan how to use available study time effectively",
                    "techniques": ["pomodoro_technique", "time_blocking", "energy_management"],
                    "tools": ["study_calendars", "time_trackers", "priority_matrices"]
                }
            },
            "monitoring_tools": {
                "comprehension_monitoring": {
                    "description": "Check understanding during learning",
                    "techniques": ["self_questioning", "summary_generation", "concept_explanation"],
                    "indicators": ["confusion_detection", "progress_assessment", "gap_identification"]
                },
                "strategy_effectiveness": {
                    "description": "Monitor if chosen strategies are working",
                    "techniques": ["performance_tracking", "strategy_logs", "effectiveness_ratings"],
                    "metrics": ["learning_outcomes", "time_efficiency", "engagement_levels"]
                },
                "attention_control": {
                    "description": "Maintain focus and manage distractions",
                    "techniques": ["mindfulness", "environment_optimization", "break_scheduling"],
                    "tools": ["focus_timers", "distraction_lists", "attention_trackers"]
                }
            },
            "evaluation_tools": {
                "self_assessment": {
                    "description": "Evaluate learning outcomes and processes",
                    "techniques": ["knowledge_audit", "skill_assessment", "progress_review"],
                    "methods": ["self_testing", "peer_feedback", "comparison_with_standards"]
                },
                "reflection": {
                    "description": "Think about learning experiences and extract insights",
                    "techniques": ["journaling", "guided_reflection", "pattern_identification"],
                    "focus_areas": ["what_worked", "what_didn't", "why", "improvements"]
                },
                "adjustment_planning": {
                    "description": "Plan changes to improve future learning",
                    "techniques": ["strategy_modification", "goal_adjustment", "process_improvement"],
                    "considerations": ["lessons_learned", "new_insights", "changing_circumstances"]
                }
            }
        },
        "implementation_schedules": {
            "daily": ["brief_goal_review", "strategy_check", "attention_monitoring"],
            "weekly": ["progress_assessment", "strategy_evaluation", "reflection_session"],
            "monthly": ["comprehensive_review", "goal_adjustment", "strategy_overhaul"]
        }
    }

@router.get("/study-strategies")
async def get_study_strategies():
    """
    Get comprehensive study strategies with effectiveness ratings
    """
    return {
        "study_strategies": {
            "cognitive_strategies": {
                "elaboration": {
                    "description": "Connect new information to existing knowledge",
                    "effectiveness": 0.85,
                    "techniques": ["analogies", "examples", "explanations"],
                    "best_for": ["conceptual_understanding", "long_term_retention"]
                },
                "organization": {
                    "description": "Structure information for better understanding",
                    "effectiveness": 0.78,
                    "techniques": ["outlining", "concept_mapping", "categorization"],
                    "best_for": ["complex_material", "relationship_understanding"]
                },
                "rehearsal": {
                    "description": "Repeat information to strengthen memory",
                    "effectiveness": 0.65,
                    "techniques": ["repetition", "practice", "review"],
                    "best_for": ["factual_information", "basic_concepts"]
                }
            },
            "metacognitive_strategies": {
                "planning": {
                    "description": "Plan learning activities before starting",
                    "effectiveness": 0.72,
                    "techniques": ["goal_setting", "time_management", "strategy_selection"],
                    "best_for": ["complex_tasks", "long_term_projects"]
                },
                "monitoring": {
                    "description": "Monitor understanding during learning",
                    "effectiveness": 0.80,
                    "techniques": ["self_questioning", "comprehension_checks", "progress_tracking"],
                    "best_for": ["all_learning_situations"]
                },
                "evaluating": {
                    "description": "Evaluate learning outcomes and processes",
                    "effectiveness": 0.75,
                    "techniques": ["self_assessment", "reflection", "feedback_analysis"],
                    "best_for": ["learning_improvement", "strategy_optimization"]
                }
            },
            "resource_management_strategies": {
                "time_management": {
                    "description": "Effectively manage study time",
                    "effectiveness": 0.70,
                    "techniques": ["pomodoro", "time_blocking", "prioritization"],
                    "best_for": ["all_students", "time_constraints"]
                },
                "environment_management": {
                    "description": "Create optimal learning environment",
                    "effectiveness": 0.65,
                    "techniques": ["distraction_control", "space_optimization", "tool_preparation"],
                    "best_for": ["attention_management", "focus_improvement"]
                },
                "effort_regulation": {
                    "description": "Maintain appropriate effort and persistence",
                    "effectiveness": 0.78,
                    "techniques": ["motivation_maintenance", "stress_management", "goal_commitment"],
                    "best_for": ["long_term_learning", "challenging_material"]
                }
            }
        },
        "strategy_combinations": {
            "high_effectiveness_combinations": [
                ["elaboration", "monitoring", "planning"],
                ["organization", "rehearsal", "monitoring"],
                ["planning", "monitoring", "evaluating"]
            ],
            "context_specific_recommendations": {
                "beginner": ["rehearsal", "organization", "monitoring"],
                "intermediate": ["elaboration", "planning", "monitoring"],
                "advanced": ["elaboration", "evaluating", "planning"]
            }
        }
    }

@router.post("/adaptive-adjustments")
async def get_adaptive_adjustments(
    course_id: str,
    current_performance: Dict[str, Any],
    plan_id: Optional[str] = None
):
    """
    Get adaptive adjustments for study plan based on current performance
    """
    try:
        # Analyze performance patterns
        performance_analysis = _analyze_current_performance(current_performance)

        # Generate adjustment recommendations
        adjustments = _generate_adjustment_recommendations(performance_analysis)

        # Create specific action plans
        action_plans = _create_adjustment_action_plans(adjustments)

        return {
            "performance_analysis": performance_analysis,
            "recommended_adjustments": adjustments,
            "action_plans": action_plans,
            "implementation_timeline": _create_adjustment_timeline(adjustments),
            "success_indicators": _define_adjustment_success_indicators(adjustments)
        }

    except Exception as e:
        logger.error(f"Adaptive adjustments generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate adaptive adjustments: {str(e)}")

@router.get("/health")
async def enhanced_study_plan_health_check():
    """
    Health check for enhanced study plan service
    """
    return {
        "status": "healthy",
        "features": {
            "learning_science_integration": True,
            "glm46_long_term_reasoning": True,
            "metacognitive_framework": True,
            "adaptive_personalization": True,
            "bloom_taxonomy_integration": True,
            "evidence_based_strategies": True
        },
        "supported_learning_objectives": [
            "knowledge_acquisition", "comprehension_application",
            "synthesis_evaluation", "metacognitive_development"
        ],
        "supported_strategies": [
            "spaced_repetition", "interleaved_practice", "elaborative_interrogation",
            "dual_coding", "retrieval_practice", "concrete_examples"
        ],
        "cognitive_levels": [
            "beginner", "intermediate", "advanced", "expert"
        ],
        "services": {
            "enhanced_study_plan_service": "active",
            "rag_service": "active",
            "llm_service": "active",
            "study_planner_service": "active"
        }
    }

# Helper functions for API endpoints
def _generate_learner_recommendations(learner_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generate detailed recommendations based on learner analysis"""

    recommendations = []

    # Experience-based recommendations
    experience = learner_analysis.get("experience_level", "intermediate")
    if experience == "beginner":
        recommendations.append({
            "category": "experience_level",
            "recommendation": "Start with foundational concepts and build gradually",
            "priority": "high",
            "implementation": "Begin with remember/understand objectives before advancing"
        })
    elif experience == "advanced":
        recommendations.append({
            "category": "experience_level",
            "recommendation": "Focus on application, analysis, and creation tasks",
            "priority": "medium",
            "implementation": "Emphasize higher-order thinking and complex problem-solving"
        })

    # Discipline-based recommendations
    discipline = learner_analysis.get("study_discipline", "moderate")
    if discipline == "low":
        recommendations.append({
            "category": "study_discipline",
            "recommendation": "Implement structure and accountability mechanisms",
            "priority": "high",
            "implementation": "Use external deadlines, study partners, and regular check-ins"
        })

    # Time availability recommendations
    time_availability = learner_analysis.get("time_availability", "moderate")
    if time_availability == "low":
        recommendations.append({
            "category": "time_management",
            "recommendation": "Prioritize essential topics and use efficient study strategies",
            "priority": "high",
            "implementation": "Focus on high-impact strategies like spaced repetition and retrieval practice"
        })

    return recommendations

def _determine_optimal_strategies(learner_analysis: Dict[str, Any]) -> List[str]:
    """Determine optimal learning strategies based on learner profile"""

    strategies = []

    # Base strategies for all learners
    strategies.extend(["spaced_repetition", "retrieval_practice"])

    # Experience-based additions
    experience = learner_analysis.get("experience_level", "intermediate")
    if experience == "beginner":
        strategies.extend(["concrete_examples", "dual_coding"])
    elif experience == "advanced":
        strategies.extend(["elaborative_interrogation", "interleaved_practice"])

    # Cognitive capacity adjustments
    cognitive_tolerance = learner_analysis.get("cognitive_load_tolerance", "moderate")
    if cognitive_tolerance == "low":
        strategies.append("chunking")

    # Metacognitive awareness
    if learner_analysis.get("metacognitive_awareness") in ["developing", "advanced"]:
        strategies.append("metacognitive_reflection")

    return strategies

def _identify_potential_challenges(learner_analysis: Dict[str, Any]) -> List[str]:
    """Identify potential challenges based on learner profile"""

    challenges = []

    if learner_analysis.get("study_discipline") == "low":
        challenges.append("maintaining_consistent_study_schedule")

    if learner_analysis.get("time_availability") == "low":
        challenges.append("covering_all_required_material")

    if learner_analysis.get("motivation_level") == "low":
        challenges.append("staying_engaged_with_difficult_content")

    if learner_analysis.get("cognitive_load_tolerance") == "low":
        challenges.append("managing_cognitive_overload")

    if learner_analysis.get("metacognitive_awareness") == "beginner":
        challenges.append("identifying_effective_study_strategies")

    return challenges

def _identify_success_factors(learner_analysis: Dict[str, Any]) -> List[str]:
    """Identify factors that contribute to learning success"""

    success_factors = []

    if learner_analysis.get("study_discipline") == "high":
        success_factors.append("strong_discipline_and_consistency")

    if learner_analysis.get("motivation_level") == "high":
        success_factors.append("high_intrinsic_motivation")

    if learner_analysis.get("time_availability") == "high":
        success_factors.append("adequate_study_time")

    if learner_analysis.get("experience_level") == "advanced":
        success_factors.append("prior_knowledge_and_experience")

    if learner_analysis.get("metacognitive_awareness") in ["developing", "advanced"]:
        success_factors.append("strong_metacognitive_skills")

    return success_factors

def _analyze_current_performance(current_performance: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze current performance data"""

    analysis = {
        "overall_trend": "stable",
        "strength_areas": [],
        "improvement_areas": [],
        "performance_consistency": 0.7,
        "engagement_level": "moderate"
    }

    # Extract performance metrics
    quiz_scores = current_performance.get("quiz_scores", [])
    session_completion = current_performance.get("session_completion_rates", [])
    time_management = current_performance.get("time_management_metrics", {})

    if quiz_scores:
        avg_score = sum(quiz_scores) / len(quiz_scores)
        if avg_score >= 0.8:
            analysis["overall_trend"] = "strong"
        elif avg_score >= 0.6:
            analysis["overall_trend"] = "adequate"
        else:
            analysis["overall_trend"] = "needs_improvement"

    return analysis

def _generate_adjustment_recommendations(performance_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generate specific adjustment recommendations"""

    adjustments = []

    trend = performance_analysis.get("overall_trend", "stable")

    if trend == "needs_improvement":
        adjustments.append({
            "adjustment_type": "difficulty_reduction",
            "description": "Reduce difficulty level and increase scaffolding",
            "priority": "high",
            "expected_impact": 0.8
        })
        adjustments.append({
            "adjustment_type": "additional_practice",
            "description": "Add more practice sessions and review opportunities",
            "priority": "high",
            "expected_impact": 0.7
        })
    elif trend == "strong":
        adjustments.append({
            "adjustment_type": "acceleration",
            "description": "Increase pace and add enrichment activities",
            "priority": "medium",
            "expected_impact": 0.6
        })

    return adjustments

def _create_adjustment_action_plans(adjustments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Create specific action plans for adjustments"""

    action_plans = []

    for adjustment in adjustments:
        adjustment_type = adjustment.get("adjustment_type")

        if adjustment_type == "difficulty_reduction":
            action_plans.append({
                "adjustment_type": adjustment_type,
                "actions": [
                    "Break complex topics into smaller segments",
                    "Add more examples and explanations",
                    "Provide additional guided practice",
                    "Extend time for difficult concepts"
                ],
                "timeline": "implement_immediately",
                "monitoring_metrics": ["quiz_improvement", "completion_rates"]
            })
        elif adjustment_type == "additional_practice":
            action_plans.append({
                "adjustment_type": adjustment_type,
                "actions": [
                    "Schedule extra review sessions",
                    "Add supplementary exercises",
                    "Create practice quizzes",
                    "Implement spaced repetition reviews"
                ],
                "timeline": "implement_this_week",
                "monitoring_metrics": ["practice_completion", "retention_scores"]
            })
        elif adjustment_type == "acceleration":
            action_plans.append({
                "adjustment_type": adjustment_type,
                "actions": [
                    "Introduce advanced topics early",
                    "Add challenge problems",
                    "Reduce guided instruction time",
                    "Include enrichment activities"
                ],
                "timeline": "implement_next_week",
                "monitoring_metrics": ["challenge_completion", "advanced_scores"]
            })

    return action_plans

def _create_adjustment_timeline(adjustments: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Create timeline for implementing adjustments"""

    immediate_adjustments = [adj for adj in adjustments if adj.get("priority") == "high"]
    medium_adjustments = [adj for adj in adjustments if adj.get("priority") == "medium"]

    return {
        "immediate_actions": [adj.get("adjustment_type") for adj in immediate_adjustments],
        "short_term_actions": [adj.get("adjustment_type") for adj in medium_adjustments],
        "review_points": [1, 2, 4],  # Weeks to review adjustment effectiveness
        "expected_timeline": "see_improvement_within_2_weeks"
    }

def _define_adjustment_success_indicators(adjustments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Define success indicators for adjustments"""

    indicators = []

    for adjustment in adjustments:
        adjustment_type = adjustment.get("adjustment_type")

        if adjustment_type == "difficulty_reduction":
            indicators.append({
                "adjustment_type": adjustment_type,
                "indicators": [
                    {"metric": "quiz_scores", "target_improvement": 0.15, "timeline": "2_weeks"},
                    {"metric": "session_completion", "target_improvement": 0.20, "timeline": "1_week"}
                ]
            })
        elif adjustment_type == "additional_practice":
            indicators.append({
                "adjustment_type": adjustment_type,
                "indicators": [
                    {"metric": "retention_scores", "target_improvement": 0.20, "timeline": "3_weeks"},
                    {"metric": "confidence_levels", "target_improvement": 0.25, "timeline": "2_weeks"}
                ]
            })
        elif adjustment_type == "acceleration":
            indicators.append({
                "adjustment_type": adjustment_type,
                "indicators": [
                    {"metric": "challenge_completion", "target_rate": 0.80, "timeline": "2_weeks"},
                    {"metric": "engagement_level", "target_improvement": 0.15, "timeline": "1_week"}
                ]
            })

    return indicators