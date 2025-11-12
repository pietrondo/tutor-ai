"""
Enhanced Study Plan Service with Learning Science and GLM-4.6 Long-term Reasoning
Integrates evidence-based learning principles with advanced AI planning capabilities
"""

import json
import math
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
import logging

from services.advanced_model_selector import AdvancedModelSelector2
from services.prompt_analytics_service import PromptAnalyticsService
from services.advanced_prompt_templates import AdvancedPromptTemplates
from llm_service import LLMService

logger = logging.getLogger(__name__)

class LearningObjectiveType(Enum):
    """Types of learning objectives for study planning"""
    KNOWLEDGE_ACQUISITION = "knowledge_acquisition"    # Remember, Understand
    COMPREHENSION_APPLICATION = "comprehension_application"  # Apply, Analyze
    SYNTHESIS_EVALUATION = "synthesis_evaluation"      # Evaluate, Create
    METACOGNITIVE_DEVELOPMENT = "metacognitive_development"  # Reflection, Self-regulation

class StudyStrategy(Enum):
    """Evidence-based study strategies"""
    SPACED_REPETITION = "spaced_repetition"
    INTERLEAVED_PRACTICE = "interleaved_practice"
    ELABORATIVE_INTERROGATION = "elaborative_interrogation"
    DUAL_CODING = "dual_coding"
    RETRIEVAL_PRACTICE = "retrieval_practice"
    CONCRETE_EXAMPLES = "concrete_examples"

class DifficultyProgression(Enum):
    """Types of difficulty progression in study plans"""
    LINEAR = "linear"                    # Gradual steady increase
    EXPONENTIAL = "exponential"          # Rapid increase after foundation
    SPIRAL = "spiral"                   # Revisit with increasing complexity
    ADAPTIVE = "adaptive"                # Based on performance
    BLOCKED = "blocked"                 # Master one level before next

class EnhancedStudyPlanService:
    """Enhanced study plan generation with learning science and GLM-4.6 integration"""

    def __init__(self):
        self.model_selector = AdvancedModelSelector2()
        self.analytics = PromptAnalyticsService()
        self.prompt_templates = AdvancedPromptTemplates()
        self.llm_service = LLMService()

        # Learning science parameters
        self.optimal_session_lengths = {
            "focused": 25,      # Pomodoro technique
            "moderate": 45,     # Standard academic session
            "extended": 90,     # Deep work session
            "review": 20        # Quick review session
        }

        self.spacing_intervals = {
            "initial": [1, 3, 7, 14, 30],      # Days for initial learning
            "review": [2, 5, 10, 20, 40],      # Days for review sessions
            "mastery": [7, 14, 30, 60, 120]    # Days for mastery maintenance
        }

    async def generate_enhanced_study_plan(
        self,
        course_id: str,
        course_content: Dict[str, Any],
        learner_profile: Optional[Dict[str, Any]] = None,
        study_preferences: Optional[Dict[str, Any]] = None,
        time_constraints: Optional[Dict[str, Any]] = None,
        learning_objectives: Optional[List[Dict[str, Any]]] = None,
        previous_performance: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate enhanced study plan using learning science principles and GLM-4.6 reasoning

        Args:
            course_id: Course identifier
            course_content: Structured course materials and topics
            learner_profile: Learner characteristics and preferences
            study_preferences: Study timing and format preferences
            time_constraints: Available study time and deadlines
            learning_objectives: Specific learning goals and outcomes
            previous_performance: Historical performance data

        Returns:
            Enhanced study plan with learning science optimizations
        """
        start_time = datetime.now()

        try:
            # Analyze learner profile and determine optimal parameters
            learner_analysis = self._analyze_learner_profile(learner_profile, previous_performance)

            # Extract and structure learning objectives using GLM-4.6
            structured_objectives = await self._extract_structured_objectives(
                learning_objectives, course_content, learner_analysis
            )

            # Determine optimal study strategies
            optimal_strategies = self._determine_optimal_strategies(
                learner_analysis, structured_objectives, course_content
            )

            # Generate long-term learning trajectory using GLM-4.6
            learning_trajectory = await self._generate_learning_trajectory(
                course_content, structured_objectives, learner_analysis, time_constraints
            )

            # Create spaced repetition schedule
            spaced_schedule = self._create_spaced_repetition_schedule(
                learning_trajectory, optimal_strategies, time_constraints
            )

            # Generate interleaved practice sessions
            practice_sessions = await self._generate_interleaved_practice(
                course_content, structured_objectives, learner_analysis
            )

            # Build comprehensive study plan
            enhanced_plan = self._build_enhanced_study_plan(
                learning_trajectory=learning_trajectory,
                spaced_schedule=spaced_schedule,
                practice_sessions=practice_sessions,
                learner_analysis=learner_analysis,
                strategies=optimal_strategies,
                objectives=structured_objectives
            )

            # Add metacognitive components
            enhanced_plan = await self._add_metacognitive_components(
                enhanced_plan, learner_analysis, structured_objectives
            )

            # Generate adaptive modifications
            adaptive_elements = await self._generate_adaptive_elements(
                enhanced_plan, learner_analysis, previous_performance
            )

            # Build final response
            result = {
                "plan_id": f"enhanced_plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "course_id": course_id,
                "learner_profile": learner_analysis,
                "learning_trajectory": learning_trajectory,
                "study_sessions": enhanced_plan["sessions"],
                "practice_schedule": practice_sessions,
                "metacognitive_framework": enhanced_plan["metacognitive"],
                "adaptive_elements": adaptive_elements,
                "learning_strategies": optimal_strategies,
                "objectives_mastery": structured_objectives,
                "performance_tracking": enhanced_plan["tracking"],
                "timeline": enhanced_plan["timeline"],
                "success_metrics": enhanced_plan["metrics"],
                "metadata": {
                    "generated_with": "GLM-4.6",
                    "learning_science_integration": True,
                    "evidence_based": True,
                    "created_at": datetime.now().isoformat(),
                    "total_sessions": len(enhanced_plan["sessions"]),
                    "estimated_duration_hours": enhanced_plan["estimated_duration"],
                    "mastery_prediction": enhanced_plan.get("mastery_prediction")
                }
            }

            # Analytics tracking
            duration = (datetime.now() - start_time).total_seconds()
            await self._track_generation_analytics(
                course_id, learner_analysis, optimal_strategies, result, duration
            )

            return result

        except Exception as e:
            logger.error(f"Enhanced study plan generation failed: {e}")
            # Fallback to basic study plan
            return await self._generate_fallback_plan(course_id, course_content)

    def _analyze_learner_profile(
        self,
        learner_profile: Optional[Dict[str, Any]],
        previous_performance: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Comprehensive learner profile analysis"""

        if not learner_profile:
            learner_profile = {}

        # Extract and analyze characteristics
        analysis = {
            # Basic characteristics
            "experience_level": learner_profile.get("experience_level", "intermediate"),
            "study_discipline": learner_profile.get("study_discipline", "moderate"),
            "time_availability": learner_profile.get("time_availability", "moderate"),
            "motivation_level": learner_profile.get("motivation_level", "moderate"),

            # Learning preferences
            "preferred_session_length": learner_profile.get("preferred_session_length", "moderate"),
            "learning_style_preference": learner_profile.get("learning_style", "mixed"),
            "challenge_tolerance": learner_profile.get("challenge_tolerance", "moderate"),
            "feedback_preference": learner_profile.get("feedback_preference", "regular"),

            # Cognitive characteristics
            "working_memory_capacity": learner_profile.get("working_memory", "average"),
            "attention_span": learner_profile.get("attention_span", "moderate"),
            "processing_speed": learner_profile.get("processing_speed", "average"),
            "metacognitive_awareness": learner_profile.get("metacognitive_awareness", "developing"),

            # Previous performance analysis
            "performance_patterns": self._analyze_performance_patterns(previous_performance),
            "strength_areas": learner_profile.get("strength_areas", []),
            "improvement_areas": learner_profile.get("improvement_areas", []),
            "preferred_difficulty_progression": learner_profile.get("difficulty_progression", "gradual")
        }

        # Calculate derived characteristics
        analysis["cognitive_load_tolerance"] = self._calculate_cognitive_tolerance(analysis)
        analysis["optimal_spacings"] = self._determine_optimal_spacings(analysis)
        analysis["intervention_needs"] = self._identify_intervention_needs(analysis)
        analysis["engagement_factors"] = self._analyze_engagement_factors(analysis)

        return analysis

    def _analyze_performance_patterns(self, previous_performance: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze historical performance to identify patterns"""

        if not previous_performance:
            return {
                "overall_trend": "insufficient_data",
                "consistency_score": 0.5,
                "improvement_rate": 0.0,
                "challenge_response": "unknown"
            }

        # Extract performance metrics
        quiz_scores = previous_performance.get("quiz_scores", [])
        completion_rates = previous_performance.get("completion_rates", [])
        time_spent = previous_performance.get("time_spent_sessions", [])
        difficulty_levels = previous_performance.get("attempted_difficulties", [])

        patterns = {
            "overall_trend": self._calculate_performance_trend(quiz_scores),
            "consistency_score": self._calculate_consistency(quiz_scores, completion_rates),
            "improvement_rate": self._calculate_improvement_rate(quiz_scores),
            "challenge_response": self._analyze_challenge_response(difficulty_levels, quiz_scores),
            "time_management": self._analyze_time_management(time_spent),
            "optimal_difficulty": self._identify_optimal_difficulty(difficulty_levels, quiz_scores)
        }

        return patterns

    def _calculate_cognitive_tolerance(self, analysis: Dict[str, Any]) -> str:
        """Calculate cognitive load tolerance level"""

        factors = {
            "working_memory": analysis["working_memory_capacity"],
            "attention_span": analysis["attention_span"],
            "experience": analysis["experience_level"],
            "discipline": analysis["study_discipline"]
        }

        # Weighted scoring
        score = 0
        if factors["working_memory"] == "high":
            score += 0.3
        elif factors["working_memory"] == "low":
            score -= 0.2

        if factors["attention_span"] == "long":
            score += 0.2
        elif factors["attention_span"] == "short":
            score -= 0.1

        if factors["experience"] == "advanced":
            score += 0.3
        elif factors["experience"] == "beginner":
            score -= 0.2

        if factors["discipline"] == "high":
            score += 0.2
        elif factors["discipline"] == "low":
            score -= 0.1

        if score >= 0.5:
            return "high"
        elif score >= 0:
            return "moderate"
        else:
            return "low"

    def _determine_optimal_spacings(self, analysis: Dict[str, Any]) -> Dict[str, List[int]]:
        """Determine optimal spacing intervals based on learner profile"""

        base_intervals = self.spacing_intervals["initial"].copy()

        # Adjust based on learner characteristics
        if analysis["working_memory_capacity"] == "low":
            # More frequent reviews for lower working memory
            base_intervals = [max(1, interval // 2) for interval in base_intervals]

        if analysis["experience_level"] == "advanced":
            # Longer intervals for advanced learners
            base_intervals = [interval * 1.5 for interval in base_intervals]
        elif analysis["experience_level"] == "beginner":
            # Shorter intervals for beginners
            base_intervals = [interval * 0.8 for interval in base_intervals]

        return {
            "initial": [int(interval) for interval in base_intervals],
            "review": [int(interval * 1.2) for interval in base_intervals],
            "mastery": [int(interval * 2) for interval in base_intervals]
        }

    async def _extract_structured_objectives(
        self,
        learning_objectives: Optional[List[Dict[str, Any]]],
        course_content: Dict[str, Any],
        learner_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Use GLM-4.6 to extract and structure learning objectives"""

        # Select optimal model for objective analysis
        model_decision = await self.model_selector.select_model(
            task_type="learning_objective_analysis",
            complexity="high",
            requires_reasoning=True,
            educational_context=True
        )

        # Create objective extraction prompt
        extraction_prompt = self._create_objective_extraction_prompt(
            learning_objectives, course_content, learner_analysis
        )

        try:
            # Use GLM-4.6 for advanced objective structuring
            if "glm-4.6" in model_decision.model.lower() or model_decision.provider == "z.ai":
                response = await self._call_glm46_model(extraction_prompt)
            else:
                response = await self.llm_service.generate_response(
                    query=extraction_prompt,
                    context={"course_content": course_content, "learner": learner_analysis}
                )

            # Parse and structure objectives
            structured_objectives = self._parse_objectives_response(response)

            # Validate and optimize objectives
            optimized_objectives = self._optimize_learning_objectives(
                structured_objectives, learner_analysis, course_content
            )

            return optimized_objectives

        except Exception as e:
            logger.error(f"GLM-4.6 objective extraction failed: {e}")
            # Fallback to basic objective structuring
            return self._fallback_objective_structuring(learning_objectives, course_content)

    def _create_objective_extraction_prompt(
        self,
        learning_objectives: Optional[List[Dict[str, Any]]],
        course_content: Dict[str, Any],
        learner_analysis: Dict[str, Any]
    ) -> str:
        """Create prompt for GLM-4.6 learning objective extraction and structuring"""

        content_summary = self._summarize_course_content(course_content)
        learner_summary = self._summarize_learner_profile(learner_analysis)

        return f"""
You are GLM-4.6, an advanced AI with exceptional capabilities for educational planning and long-term reasoning.

TASK: Analyze and structure comprehensive learning objectives for optimal study plan generation.

COURSE CONTENT:
{content_summary}

LEARNER PROFILE:
{learner_summary}

EXISTING OBJECTIVES (if any):
{json.dumps(learning_objectives or [], indent=2)}

ANALYSIS REQUIREMENTS:
1. **Objective Classification**: Categorize objectives by cognitive level using Bloom's Taxonomy
2. **Learning Sequence**: Determine optimal learning sequence and dependencies
3. **Mastery Criteria**: Define specific, measurable mastery criteria for each objective
4. **Assessment Methods**: Recommend appropriate assessment methods for each objective
5. **Time Estimation**: Estimate optimal study time for each objective based on learner profile

COGNITIVE LEVELS TO USE:
- Remember/Understand (Knowledge Acquisition)
- Apply/Analyze (Comprehension & Application)
- Evaluate/Create (Synthesis & Evaluation)
- Metacognitive Development

LEARNING SCIENCE INTEGRATION:
- Spaced Repetition: Identify objectives requiring frequent review
- Interleaved Practice: Group objectives that benefit from mixed practice
- Retrieval Practice: Prioritize objectives needing active recall
- Elaborative Learning: Identify objectives needing deep processing

OUTPUT FORMAT (JSON ONLY):
{{
  "structured_objectives": [
    {{
      "id": "objective_id",
      "title": "Objective Title",
      "description": "Clear description of what learner will achieve",
      "cognitive_level": "knowledge_acquisition|comprehension_application|synthesis_evaluation|metacognitive_development",
      "bloom_taxonomy": "remember|understand|apply|analyze|evaluate|create",
      "prerequisites": ["objective_id_1", "objective_id_2"],
      "mastery_criteria": {{
        "minimum_score": 0.8,
        "performance_indicators": ["indicator_1", "indicator_2"],
        "evidence_types": ["quiz", "project", "presentation"]
      }},
      "assessment_methods": ["method_1", "method_2"],
      "estimated_study_hours": 5,
      "difficulty_level": "beginner|intermediate|advanced",
      "practice_frequency": "daily|weekly|biweekly",
      "review_schedule": [1, 3, 7, 14],
      "interleaving_group": "group_id",
      "metacognitive_prompts": ["prompt_1", "prompt_2"]
    }}
  ],
  "learning_sequence": {{
    "phases": [
      {{
        "phase_id": "phase_id",
        "title": "Phase Title",
        "duration_weeks": 2,
        "objectives": ["objective_id_1", "objective_id_2"],
        "focus_areas": ["area_1", "area_2"],
        "weekly_goals": ["goal_1", "goal_2"]
      }}
    ],
    "dependencies": {{
      "objective_id_1": ["objective_id_2"],
      "objective_id_2": ["objective_id_3", "objective_id_4"]
    }}
  }},
  "mastery_progression": {{
    "beginner_objectives": ["obj_1", "obj_2"],
    "intermediate_objectives": ["obj_3", "obj_4"],
    "advanced_objectives": ["obj_5", "obj_6"],
    "mastery_thresholds": {{
      "beginner": 0.7,
      "intermediate": 0.8,
      "advanced": 0.9
    }}
  }}
}}

CRITICAL CONSTRAINTS:
- Align objectives with learner's current level and goals
- Ensure logical progression and prerequisite chains
- Incorporate evidence-based learning principles
- Provide specific, measurable criteria
- Consider time constraints and availability
- Include metacognitive development objectives

Analyze the content and learner profile to create comprehensive, evidence-based learning objectives.
"""

    async def _call_glm46_model(self, prompt: str) -> str:
        """Call GLM-4.6 model through the appropriate service"""
        try:
            response = await self.llm_service.generate_response(
                query=prompt,
                context={"model_preference": "glm-4.6", "task_type": "objective_analysis"}
            )
            return response
        except Exception as e:
            logger.error(f"GLM-4.6 model call failed: {e}")
            raise

    def _parse_objectives_response(self, response: str) -> Dict[str, Any]:
        """Parse GLM-4.6 objectives response"""
        try:
            if isinstance(response, dict):
                return response

            if isinstance(response, str):
                start_idx = response.find('{')
                end_idx = response.rfind('}') + 1

                if start_idx != -1 and end_idx != -1:
                    json_str = response[start_idx:end_idx]
                    return json.loads(json_str)

            logger.warning("Could not parse objectives response as JSON")
            return {"structured_objectives": [], "learning_sequence": {}, "mastery_progression": {}}

        except Exception as e:
            logger.error(f"Failed to parse objectives response: {e}")
            return {"structured_objectives": [], "learning_sequence": {}, "mastery_progression": {}}

    def _summarize_course_content(self, course_content: Dict[str, Any]) -> str:
        """Create summary of course content for analysis"""

        topics = course_content.get("topics", [])
        materials = course_content.get("materials", [])
        chapters = course_content.get("chapters", [])

        summary_parts = []

        if topics:
            summary_parts.append(f"Main Topics: {', '.join(topics[:10])}")

        if chapters:
            chapter_titles = [ch.get("title", "") for ch in chapters[:5] if ch.get("title")]
            if chapter_titles:
                summary_parts.append(f"Key Chapters: {', '.join(chapter_titles)}")

        if materials:
            summary_parts.append(f"Available Materials: {len(materials)} documents")

        return " | ".join(summary_parts) if summary_parts else "Course content details not specified"

    def _summarize_learner_profile(self, learner_analysis: Dict[str, Any]) -> str:
        """Create summary of learner profile for analysis"""

        characteristics = [
            f"Experience Level: {learner_analysis.get('experience_level', 'intermediate')}",
            f"Study Discipline: {learner_analysis.get('study_discipline', 'moderate')}",
            f"Time Availability: {learner_analysis.get('time_availability', 'moderate')}",
            f"Preferred Session Length: {learner_analysis.get('preferred_session_length', 'moderate')}",
            f"Cognitive Load Tolerance: {learner_analysis.get('cognitive_load_tolerance', 'moderate')}",
            f"Metacognitive Awareness: {learner_analysis.get('metacognitive_awareness', 'developing')}"
        ]

        return " | ".join(characteristics)

    def _optimize_learning_objectives(
        self,
        structured_objectives: Dict[str, Any],
        learner_analysis: Dict[str, Any],
        course_content: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Optimize learning objectives based on learner profile and content"""

        objectives = structured_objectives.get("structured_objectives", [])

        # Adjust objectives based on learner profile
        for objective in objectives:
            # Adjust difficulty based on experience level
            if learner_analysis.get("experience_level") == "beginner":
                objective["difficulty_level"] = "beginner"
                objective["estimated_study_hours"] = max(2, objective.get("estimated_study_hours", 5) * 0.8)
            elif learner_analysis.get("experience_level") == "advanced":
                objective["difficulty_level"] = max("intermediate", objective.get("difficulty_level", "intermediate"))
                objective["estimated_study_hours"] = objective.get("estimated_study_hours", 5) * 1.2

            # Adjust session length preference
            session_preference = learner_analysis.get("preferred_session_length", "moderate")
            if session_preference == "short":
                objective["estimated_study_hours"] = min(4, objective.get("estimated_study_hours", 5))
            elif session_preference == "long":
                objective["estimated_study_hours"] = max(6, objective.get("estimated_study_hours", 5))

            # Adjust cognitive load tolerance
            if learner_analysis.get("cognitive_load_tolerance") == "low":
                objective["practice_frequency"] = "daily"
                objective["review_schedule"] = [1, 2, 4, 7, 14]

        # Validate prerequisites and dependencies
        validated_objectives = self._validate_objective_dependencies(objectives)

        return {
            "structured_objectives": validated_objectives,
            "learning_sequence": structured_objectives.get("learning_sequence", {}),
            "mastery_progression": structured_objectives.get("mastery_progression", {}),
            "optimization_applied": {
                "learner_adjustments": True,
                "difficulty_calibration": True,
                "timing_optimization": True,
                "dependency_validation": True
            }
        }

    def _validate_objective_dependencies(self, objectives: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate and clean objective dependencies"""

        objective_ids = {obj.get("id") for obj in objectives}
        validated_objectives = []

        for objective in objectives:
            # Clean prerequisites to only include valid objectives
            prerequisites = objective.get("prerequisites", [])
            valid_prerequisites = [
                prereq for prereq in prerequisites
                if prereq in objective_ids
            ]

            objective["prerequisites"] = valid_prerequisites
            validated_objectives.append(objective)

        return validated_objectives

    def _fallback_objective_structuring(
        self,
        learning_objectives: Optional[List[Dict[str, Any]]],
        course_content: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Fallback objective structuring method"""

        # Extract basic objectives from content
        topics = course_content.get("topics", [])
        chapters = course_content.get("chapters", [])

        basic_objectives = []

        # Create objectives from topics
        for i, topic in enumerate(topics[:8]):  # Limit to prevent overload
            basic_objectives.append({
                "id": f"objective_{i+1}",
                "title": f"Comprendere {topic}",
                "description": f"Padroneggiare i concetti fondamentali di {topic}",
                "cognitive_level": "knowledge_acquisition",
                "bloom_taxonomy": "understand",
                "prerequisites": [],
                "mastery_criteria": {
                    "minimum_score": 0.7,
                    "performance_indicators": ["Spiegazione verbale", "Esempi pratici"],
                    "evidence_types": ["quiz"]
                },
                "assessment_methods": ["quiz", "discussion"],
                "estimated_study_hours": 3,
                "difficulty_level": "intermediate",
                "practice_frequency": "weekly",
                "review_schedule": [1, 3, 7, 14],
                "interleaving_group": f"group_{i%3}",
                "metacognitive_prompts": ["Come posso applicare questo concetto?"]
            })

        return {
            "structured_objectives": basic_objectives,
            "learning_sequence": {
                "phases": [
                    {
                        "phase_id": "phase_1",
                        "title": "Fondamenti",
                        "duration_weeks": 2,
                        "objectives": [obj["id"] for obj in basic_objectives[:4]],
                        "focus_areas": topics[:4],
                        "weekly_goals": ["Completare 2 obiettivi", "Ripasso settimanale"]
                    }
                ]
            },
            "mastery_progression": {
                "beginner_objectives": [obj["id"] for obj in basic_objectives[:2]],
                "intermediate_objectives": [obj["id"] for obj in basic_objectives[2:5]],
                "advanced_objectives": [obj["id"] for obj in basic_objectives[5:]],
                "mastery_thresholds": {"beginner": 0.7, "intermediate": 0.8, "advanced": 0.9}
            }
        }

    def _determine_optimal_strategies(
        self,
        learner_analysis: Dict[str, Any],
        structured_objectives: Dict[str, Any],
        course_content: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Determine optimal evidence-based study strategies"""

        objectives = structured_objectives.get("structured_objectives", [])

        strategy_recommendations = {
            "primary_strategies": [],
            "secondary_strategies": [],
            "strategy_applications": {},
            "effectiveness_predictions": {},
            "implementation_schedule": {}
        }

        # Analyze objectives for strategy matching
        knowledge_objectives = [obj for obj in objectives if obj.get("cognitive_level") == "knowledge_acquisition"]
        application_objectives = [obj for obj in objectives if obj.get("cognitive_level") == "comprehension_application"]
        synthesis_objectives = [obj for obj in objectives if obj.get("cognitive_level") == "synthesis_evaluation"]
        metacognitive_objectives = [obj for obj in objectives if obj.get("cognitive_level") == "metacognitive_development"]

        # Determine primary strategies based on learner profile
        if learner_analysis.get("working_memory_capacity") == "low":
            strategy_recommendations["primary_strategies"].append("spaced_repetition")
            strategy_recommendations["primary_strategies"].append("retrieval_practice")

        if learner_analysis.get("experience_level") == "beginner":
            strategy_recommendations["primary_strategies"].extend(["concrete_examples", "dual_coding"])
        elif learner_analysis.get("experience_level") == "advanced":
            strategy_recommendations["primary_strategies"].extend(["elaborative_interrogation", "interleaved_practice"])

        # Strategy applications by objective type
        if knowledge_objectives:
            strategy_recommendations["strategy_applications"]["knowledge_acquisition"] = [
                "spaced_repetition",
                "retrieval_practice",
                "concrete_examples"
            ]

        if application_objectives:
            strategy_recommendations["strategy_applications"]["comprehension_application"] = [
                "interleaved_practice",
                "dual_coding",
                "elaborative_interrogation"
            ]

        if synthesis_objectives:
            strategy_recommendations["strategy_applications"]["synthesis_evaluation"] = [
                "elaborative_interrogation",
                "interleaved_practice",
                "metacognitive_reflection"
            ]

        if metacognitive_objectives:
            strategy_recommendations["strategy_applications"]["metacognitive_development"] = [
                "metacognitive_reflection",
                "self_explanation",
                "goal_setting"
            ]

        # Predict effectiveness based on learner profile
        for strategy in strategy_recommendations["primary_strategies"]:
            effectiveness = self._predict_strategy_effectiveness(strategy, learner_analysis)
            strategy_recommendations["effectiveness_predictions"][strategy] = effectiveness

        # Implementation schedule
        strategy_recommendations["implementation_schedule"] = self._create_strategy_schedule(
            strategy_recommendations["primary_strategies"],
            objectives,
            learner_analysis
        )

        return strategy_recommendations

    def _predict_strategy_effectiveness(self, strategy: str, learner_analysis: Dict[str, Any]) -> float:
        """Predict effectiveness of a strategy for specific learner"""

        base_effectiveness = {
            "spaced_repetition": 0.8,
            "interleaved_practice": 0.75,
            "elaborative_interrogation": 0.85,
            "dual_coding": 0.7,
            "retrieval_practice": 0.82,
            "concrete_examples": 0.76
        }

        effectiveness = base_effectiveness.get(strategy, 0.7)

        # Adjust based on learner characteristics
        if strategy == "spaced_repetition" and learner_analysis.get("study_discipline") == "high":
            effectiveness += 0.1
        elif strategy == "spaced_repetition" and learner_analysis.get("study_discipline") == "low":
            effectiveness -= 0.2

        if strategy == "interleaved_practice" and learner_analysis.get("experience_level") == "advanced":
            effectiveness += 0.1
        elif strategy == "interleaved_practice" and learner_analysis.get("experience_level") == "beginner":
            effectiveness -= 0.1

        if strategy == "elaborative_interrogation" and learner_analysis.get("metacognitive_awareness") == "high":
            effectiveness += 0.15
        elif strategy == "elaborative_interrogation" and learner_analysis.get("metacognitive_awareness") == "low":
            effectiveness -= 0.1

        return min(1.0, max(0.0, effectiveness))

    def _create_strategy_schedule(
        self,
        strategies: List[str],
        objectives: List[Dict[str, Any]],
        learner_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create implementation schedule for strategies"""

        schedule = {
            "immediate_implementation": [],
            "gradual_introduction": [],
            "maintenance_phase": [],
            "strategy_rotations": []
        }

        # Immediate implementation (high-effectiveness, low-effort strategies)
        high_impact_strategies = [
            strategy for strategy in strategies
            if self._predict_strategy_effectiveness(strategy, learner_analysis) > 0.8
        ]
        schedule["immediate_implementation"] = high_impact_strategies

        # Gradual introduction (moderate effectiveness, higher effort)
        moderate_impact_strategies = [
            strategy for strategy in strategies
            if 0.6 < self._predict_strategy_effectiveness(strategy, learner_analysis) <= 0.8
        ]
        schedule["gradual_introduction"] = moderate_impact_strategies

        # Strategy rotations for maintaining engagement
        schedule["strategy_rotations"] = [
            {
                "week_range": [1, 2],
                "focus_strategies": ["retrieval_practice", "spaced_repetition"],
                "objectives_focus": ["knowledge_acquisition"]
            },
            {
                "week_range": [3, 4],
                "focus_strategies": ["interleaved_practice", "dual_coding"],
                "objectives_focus": ["comprehension_application"]
            },
            {
                "week_range": [5, 6],
                "focus_strategies": ["elaborative_interrogation", "concrete_examples"],
                "objectives_focus": ["synthesis_evaluation"]
            }
        ]

        return schedule

    async def _generate_learning_trajectory(
        self,
        course_content: Dict[str, Any],
        structured_objectives: Dict[str, Any],
        learner_analysis: Dict[str, Any],
        time_constraints: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate long-term learning trajectory using GLM-4.6 reasoning"""

        # Select optimal model for trajectory planning
        model_decision = await self.model_selector.select_model(
            task_type="learning_trajectory_planning",
            complexity="high",
            requires_reasoning=True,
            requires_long_term_planning=True,
            educational_context=True
        )

        # Create trajectory planning prompt
        trajectory_prompt = self._create_trajectory_planning_prompt(
            course_content, structured_objectives, learner_analysis, time_constraints
        )

        try:
            # Use GLM-4.6 for advanced trajectory planning
            if "glm-4.6" in model_decision.model.lower() or model_decision.provider == "z.ai":
                response = await self._call_glm46_model(trajectory_prompt)
            else:
                response = await self.llm_service.generate_response(
                    query=trajectory_prompt,
                    context={
                        "course_content": course_content,
                        "objectives": structured_objectives,
                        "learner": learner_analysis,
                        "constraints": time_constraints
                    }
                )

            # Parse and structure trajectory
            trajectory = self._parse_trajectory_response(response)

            # Optimize trajectory based on constraints
            optimized_trajectory = self._optimize_learning_trajectory(
                trajectory, time_constraints, learner_analysis
            )

            return optimized_trajectory

        except Exception as e:
            logger.error(f"GLM-4.6 trajectory planning failed: {e}")
            # Fallback to basic trajectory
            return self._fallback_trajectory_planning(structured_objectives, time_constraints)

    def _create_trajectory_planning_prompt(
        self,
        course_content: Dict[str, Any],
        structured_objectives: Dict[str, Any],
        learner_analysis: Dict[str, Any],
        time_constraints: Optional[Dict[str, Any]]
    ) -> str:
        """Create prompt for GLM-4.6 learning trajectory planning"""

        objectives_summary = self._summarize_objectives_for_planning(structured_objectives)
        constraints_summary = self._summarize_time_constraints(time_constraints)

        return f"""
You are GLM-4.6, an advanced AI specializing in educational planning and long-term learning trajectory design.

TASK: Design an optimal long-term learning trajectory that maximizes learning effectiveness and achievement.

COURSE CONTENT ANALYSIS:
{self._summarize_course_content(course_content)}

STRUCTURED LEARNING OBJECTIVES:
{objectives_summary}

LEARNER PROFILE:
{self._summarize_learner_profile(learner_analysis)}

TIME CONSTRAINTS:
{constraints_summary}

TRAJECTORY DESIGN REQUIREMENTS:
1. **Optimal Sequencing**: Determine the most effective order of learning objectives
2. **Pacing Strategy**: Balance challenge with skill development
3. **Adaptive Progression**: Build in flexibility for performance-based adjustments
4. **Milestones**: Define key progress checkpoints and achievement markers
5. **Recovery Mechanisms**: Plan for setbacks and recovery strategies

LEARNING SCIENCE INTEGRATION:
- **Cognitive Load Management**: Sequence to optimize mental effort
- **Spaced Repetition Optimization**: Time reviews for maximum retention
- **Interleaving Strategy**: Mix related but distinct concepts
- **Desirable Difficulties**: Introduce appropriate challenges
- **Metacognitive Development**: Build self-regulation skills

TRAJECTORY STRUCTURE:
- **Foundation Phase**: Core concepts and skills
- **Development Phase**: Application and deeper understanding
- **Integration Phase**: Connection and synthesis
- **Mastery Phase**: Advanced application and innovation

OUTPUT FORMAT (JSON ONLY):
{{
  "learning_trajectory": {{
    "total_duration_weeks": 12,
    "phases": [
      {{
        "phase_id": "phase_id",
        "title": "Phase Title",
        "duration_weeks": 3,
        "start_week": 1,
        "end_week": 3,
        "phase_type": "foundation|development|integration|mastery",
        "primary_focus": ["focus_area_1", "focus_area_2"],
        "objectives": ["objective_id_1", "objective_id_2"],
        "weekly_structure": [
          {{
            "week": 1,
            "goals": ["goal_1", "goal_2"],
            "new_objectives": ["obj_1"],
            "review_objectives": ["obj_2"],
            "practice_activities": ["activity_1", "activity_2"],
            "estimated_hours": 8,
            "difficulty_level": "beginner",
            "key_challenges": ["challenge_1"],
            "success_criteria": ["criteria_1"]
          }}
        ],
        "assessment_points": [
          {{
            "week": 2,
            "type": "formative",
            "objectives_assessed": ["obj_1", "obj_2"],
            "mastery_threshold": 0.75
          }}
        ],
        "adaptive_triggers": [
          {{
            "condition": "score < 0.7",
            "action": "additional_practice",
            "adjustments": ["increase_repetition", "add_examples"]
          }}
        ]
      }}
    ],
    "milestones": [
      {{
        "milestone_id": "milestone_id",
        "title": "Milestone Title",
        "week": 4,
        "objectives_required": ["obj_1", "obj_2"],
        "mastery_threshold": 0.8,
        "reward_type": "progress_badge",
        "next_phase_prerequisites": true
      }}
    ],
    "progression_metrics": {{
      "weekly_completion_target": 0.8,
      "mastery_acceleration_threshold": 0.85,
      "remediation_trigger_threshold": 0.6,
      "challenge_advancement_threshold": 0.9
    }},
    "contingency_planning": {{
      "behind_schedule": ["intensify_practice", "extend_timeline"],
      "ahead_of_schedule": ["enrichment_activities", "advanced_topics"],
      "struggling_with_concept": ["alternative_explanations", "peer_learning"],
      "losing_motivation": ["variety_introduction", "success_experiences"]
    }}
  }}
}}

CRITICAL CONSTRAINTS:
- Respect time constraints and availability
- Align with learner's current capabilities
- Incorporate regular assessment and feedback
- Build in flexibility for adaptation
- Maintain motivation through appropriate challenge
- Ensure progression is achievable but challenging

Design a comprehensive learning trajectory that optimizes for both learning effectiveness and learner success.
"""

    def _summarize_objectives_for_planning(self, structured_objectives: Dict[str, Any]) -> str:
        """Summarize objectives for trajectory planning"""

        objectives = structured_objectives.get("structured_objectives", [])
        if not objectives:
            return "No specific objectives defined"

        summary_parts = [
            f"Total Objectives: {len(objectives)}",
            f"Knowledge Acquisition: {len([o for o in objectives if o.get('cognitive_level') == 'knowledge_acquisition'])}",
            f"Application Objectives: {len([o for o in objectives if o.get('cognitive_level') == 'comprehension_application'])}",
            f"Synthesis Objectives: {len([o for o in objectives if o.get('cognitive_level') == 'synthesis_evaluation'])}"
        ]

        return " | ".join(summary_parts)

    def _summarize_time_constraints(self, time_constraints: Optional[Dict[str, Any]]) -> str:
        """Summarize time constraints for planning"""

        if not time_constraints:
            return "No specific time constraints defined"

        constraints_parts = []

        if time_constraints.get("hours_per_week"):
            constraints_parts.append(f"Study Time: {time_constraints['hours_per_week']} hours/week")

        if time_constraints.get("deadline"):
            constraints_parts.append(f"Deadline: {time_constraints['deadline']}")

        if time_constraints.get("preferred_study_days"):
            constraints_parts.append(f"Preferred Days: {', '.join(time_constraints['preferred_study_days'])}")

        if time_constraints.get("session_preferences"):
            constraints_parts.append(f"Session Length: {time_constraints['session_preferences']}")

        return " | ".join(constraints_parts) if constraints_parts else "Flexible scheduling"

    def _parse_trajectory_response(self, response: str) -> Dict[str, Any]:
        """Parse GLM-4.6 trajectory response"""
        try:
            if isinstance(response, dict):
                return response

            if isinstance(response, str):
                start_idx = response.find('{')
                end_idx = response.rfind('}') + 1

                if start_idx != -1 and end_idx != -1:
                    json_str = response[start_idx:end_idx]
                    return json.loads(json_str)

            logger.warning("Could not parse trajectory response as JSON")
            return {"learning_trajectory": {}}

        except Exception as e:
            logger.error(f"Failed to parse trajectory response: {e}")
            return {"learning_trajectory": {}}

    def _optimize_learning_trajectory(
        self,
        trajectory: Dict[str, Any],
        time_constraints: Optional[Dict[str, Any]],
        learner_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Optimize trajectory based on constraints and learner profile"""

        learning_trajectory = trajectory.get("learning_trajectory", {})

        # Adjust duration based on time constraints
        if time_constraints:
            hours_per_week = time_constraints.get("hours_per_week", 10)
            if hours_per_week < 6:
                # Reduce intensity for limited time availability
                phases = learning_trajectory.get("phases", [])
                for phase in phases:
                    if "duration_weeks" in phase:
                        phase["duration_weeks"] = max(2, phase["duration_weeks"] * 1.5)

        # Adjust challenge level based on learner experience
        experience_level = learner_analysis.get("experience_level", "intermediate")
        phases = learning_trajectory.get("phases", [])
        for phase in phases:
            weekly_structure = phase.get("weekly_structure", [])
            for week in weekly_structure:
                if experience_level == "beginner":
                    week["difficulty_level"] = "beginner"
                    week["estimated_hours"] = max(4, week.get("estimated_hours", 8) * 0.8)
                elif experience_level == "advanced":
                    if week.get("difficulty_level") == "beginner":
                        week["difficulty_level"] = "intermediate"
                    week["estimated_hours"] = min(12, week.get("estimated_hours", 8) * 1.2)

        # Add adaptive triggers based on learner characteristics
        if learner_analysis.get("metacognitive_awareness") == "low":
            for phase in phases:
                adaptive_triggers = phase.get("adaptive_triggers", [])
                adaptive_triggers.append({
                    "condition": "low_engagement",
                    "action": "metacognitive_scaffolding",
                    "adjustments": ["add_reflection_prompts", "reduce_complexity"]
                })

        return {
            "learning_trajectory": learning_trajectory,
            "optimization_applied": {
                "time_constraint_adjustment": bool(time_constraints),
                "experience_level_calibration": True,
                "adaptive_trigger_enhancement": True,
                "difficulty_optimization": True
            }
        }

    def _fallback_trajectory_planning(
        self,
        structured_objectives: Dict[str, Any],
        time_constraints: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Fallback trajectory planning method"""

        objectives = structured_objectives.get("structured_objectives", [])

        # Create basic 4-phase structure
        phases = [
            {
                "phase_id": "foundation",
                "title": "Fase Fondamentale",
                "duration_weeks": 3,
                "start_week": 1,
                "end_week": 3,
                "phase_type": "foundation",
                "primary_focus": ["Concepti di base"],
                "objectives": [obj["id"] for obj in objectives[:3]],
                "weekly_structure": [
                    {
                        "week": 1,
                        "goals": ["Comprendere i concetti fondamentali"],
                        "new_objectives": [objectives[0]["id"]] if objectives else [],
                        "review_objectives": [],
                        "practice_activities": ["Lettura", "Quiz base"],
                        "estimated_hours": 8,
                        "difficulty_level": "beginner",
                        "key_challenges": ["Comprensione iniziale"],
                        "success_criteria": ["Superamento quiz base"]
                    }
                ],
                "assessment_points": [
                    {
                        "week": 3,
                        "type": "formative",
                        "objectives_assessed": [obj["id"] for obj in objectives[:2]],
                        "mastery_threshold": 0.75
                    }
                ]
            }
        ]

        return {
            "learning_trajectory": {
                "total_duration_weeks": 12,
                "phases": phases,
                "milestones": [
                    {
                        "milestone_id": "foundation_mastery",
                        "title": "Dominio dei Fondamenti",
                        "week": 3,
                        "objectives_required": [obj["id"] for obj in objectives[:2]],
                        "mastery_threshold": 0.75,
                        "reward_type": "progress_badge"
                    }
                ],
                "progression_metrics": {
                    "weekly_completion_target": 0.8,
                    "mastery_acceleration_threshold": 0.85,
                    "remediation_trigger_threshold": 0.6
                }
            }
        }

    def _create_spaced_repetition_schedule(
        self,
        learning_trajectory: Dict[str, Any],
        optimal_strategies: Dict[str, Any],
        time_constraints: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Create optimized spaced repetition schedule"""

        trajectory = learning_trajectory.get("learning_trajectory", {})
        phases = trajectory.get("phases", [])
        objectives = []

        # Collect all objectives from phases
        for phase in phases:
            objectives.extend(phase.get("objectives", []))

        # Create repetition schedule
        schedule = {
            "review_sessions": [],
            "optimization_principles": [],
            "adaptive_adjustments": {}
        }

        # Generate review sessions based on spacing intervals
        base_intervals = [1, 3, 7, 14, 30]  # Days

        for i, objective_id in enumerate(objectives):
            for interval in base_intervals:
                review_day = interval + (i * 2)  # Spread out initial reviews
                if review_day <= 90:  # Limit to reasonable timeframe
                    schedule["review_sessions"].append({
                        "session_id": f"review_{objective_id}_{interval}",
                        "objective_id": objective_id,
                        "review_type": "spaced_repetition",
                        "scheduled_day": review_day,
                        "duration_minutes": 15,
                        "focus_areas": ["key_concepts", "common_misconceptions"],
                        "activities": ["quick_quiz", "recall_practice", "concept_mapping"]
                    })

        # Sort sessions by scheduled day
        schedule["review_sessions"].sort(key=lambda x: x["scheduled_day"])

        # Add optimization principles
        schedule["optimization_principles"] = [
            "Expanding intervals for mastered concepts",
            "Shorter intervals for difficult concepts",
            "Mixed practice for related concepts",
            "Context variation for robust learning"
        ]

        return schedule

    async def _generate_interleaved_practice(
        self,
        course_content: Dict[str, Any],
        structured_objectives: Dict[str, Any],
        learner_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate interleaved practice sessions"""

        objectives = structured_objectives.get("structured_objectives", [])

        # Group objectives by cognitive level for optimal interleaving
        knowledge_objectives = [obj for obj in objectives if obj.get("cognitive_level") == "knowledge_acquisition"]
        application_objectives = [obj for obj in objectives if obj.get("cognitive_level") == "comprehension_application"]

        practice_sessions = []

        # Create interleaved practice sessions
        session_id = 0
        for week in range(1, 13):  # 12-week structure
            if week % 2 == 1:  # Every other week
                # Mix knowledge and application objectives
                practice_session = {
                    "session_id": f"interleaved_practice_{session_id}",
                    "week": week,
                    "title": f"Sessione di Pratica Interleaved - Settimana {week}",
                    "duration_minutes": 45,
                    "mixed_objectives": [],
                    "practice_structure": [],
                    "interleaving_benefits": [],
                    "adaptation_suggestions": []
                }

                # Select objectives for mixing (3-4 per session)
                selected_knowledge = knowledge_objectives[week//2 % len(knowledge_objectives):week//2 % len(knowledge_objectives) + 2]
                selected_application = application_objectives[week//2 % len(application_objectives):week//2 % len(application_objectives) + 2]

                mixed_objectives = selected_knowledge + selected_application
                practice_session["mixed_objectives"] = [obj.get("id") for obj in mixed_objectives]

                # Create practice structure
                practice_session["practice_structure"] = [
                    {
                        "segment": "warmup",
                        "duration_minutes": 5,
                        "activity": "quick_recall",
                        "objectives": [mixed_objectives[0].get("id")] if mixed_objectives else []
                    },
                    {
                        "segment": "mixed_practice",
                        "duration_minutes": 25,
                        "activity": "interleaved_problems",
                        "objectives": [obj.get("id") for obj in mixed_objectives[:2]]
                    },
                    {
                        "segment": "application",
                        "duration_minutes": 15,
                        "activity": "concept_connection",
                        "objectives": [obj.get("id") for obj in mixed_objectives[2:4]]
                    }
                ]

                practice_sessions.append(practice_session)
                session_id += 1

        return {
            "practice_sessions": practice_sessions,
            "interleaving_strategy": "mixed_objective_types",
            "schedule_frequency": "biweekly",
            "expected_benefits": [
                "Enhanced discrimination between concepts",
                "Improved flexible knowledge application",
                "Better long-term retention",
                "Increased problem-solving adaptability"
            ]
        }

    def _build_enhanced_study_plan(
        self,
        learning_trajectory: Dict[str, Any],
        spaced_schedule: Dict[str, Any],
        practice_sessions: Dict[str, Any],
        learner_analysis: Dict[str, Any],
        strategies: Dict[str, Any],
        objectives: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build the comprehensive enhanced study plan"""

        trajectory = learning_trajectory.get("learning_trajectory", {})
        phases = trajectory.get("phases", [])

        # Convert trajectory phases to study sessions
        study_sessions = []
        session_count = 0

        for phase in phases:
            weekly_structure = phase.get("weekly_structure", [])
            for week_plan in weekly_structure:
                session_count += 1
                session = {
                    "session_id": f"session_{session_count}",
                    "week": week_plan.get("week"),
                    "phase": phase.get("phase_type"),
                    "title": f"Sessione {session_count}: {phase.get('title', '')}",
                    "duration_minutes": week_plan.get("estimated_hours", 1) * 60,
                    "learning_objectives": week_plan.get("new_objectives", []),
                    "review_objectives": week_plan.get("review_objectives", []),
                    "difficulty_level": week_plan.get("difficulty_level", "intermediate"),
                    "goals": week_plan.get("goals", []),
                    "activities": week_plan.get("practice_activities", []),
                    "success_criteria": week_plan.get("success_criteria", []),
                    "key_challenges": week_plan.get("key_challenges", []),
                    "strategies_applied": strategies.get("primary_strategies", [])[:2],
                    "metacognitive_prompts": self._generate_session_metacognitive_prompts(
                        week_plan, learner_analysis
                    )
                }
                study_sessions.append(session)

        # Calculate estimated duration
        total_hours = sum(session["duration_minutes"] / 60 for session in study_sessions)

        return {
            "sessions": study_sessions,
            "estimated_duration": total_hours,
            "metacognitive": {
                "reflection_prompts": self._generate_metacognitive_framework(learner_analysis),
                "self_assessment_tools": self._generate_self_assessment_tools(),
                "goal_setting_framework": self._generate_goal_setting_framework()
            },
            "tracking": {
                "progress_indicators": self._define_progress_indicators(),
                "assessment_schedule": self._create_assessment_schedule(phases),
                "performance_metrics": self._define_performance_metrics()
            },
            "timeline": {
                "total_weeks": trajectory.get("total_duration_weeks", 12),
                "key_milestones": trajectory.get("milestones", []),
                "checkpoint_frequency": "weekly",
                "flexibility_factors": ["performance_based", "time_based", "motivation_based"]
            },
            "metrics": {
                "success_prediction": self._predict_learning_success(
                    learner_analysis, strategies, objectives
                ),
                "completion_probability": self._estimate_completion_probability(
                    study_sessions, learner_analysis
                ),
                "mastery_prediction": self._predict_mastery_achievement(objectives)
            }
        }

    def _generate_session_metacognitive_prompts(
        self,
        week_plan: Dict[str, Any],
        learner_analysis: Dict[str, Any]
    ) -> List[str]:
        """Generate metacognitive prompts for study sessions"""

        base_prompts = [
            "Quali concetti mi risultano più chiari oggi?",
            "Cosa posso fare per consolidare quanto appreso?",
            "Come posso collegare questi concetti a ciò che già so?"
        ]

        # Adjust based on learner characteristics
        if learner_analysis.get("metacognitive_awareness") == "developing":
            base_prompts.extend([
                "Quali strategie ho usato oggi e sono risultate efficaci?",
                "Cosa potrei fare diversamente nella prossima sessione?"
            ])

        difficulty = week_plan.get("difficulty_level", "intermediate")
        if difficulty == "advanced":
            base_prompts.extend([
                "In che modi posso applicare questi concetti in contesti nuovi?",
                "Quali sono le implicazioni più ampie di quanto studiato?"
            ])

        return base_prompts[:4]  # Limit to prevent cognitive overload

    def _generate_metacognitive_framework(self, learner_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive metacognitive framework"""

        framework = {
            "planning_phase": [
                "Quali sono i miei obiettivi specifici per questa sessione?",
                "Quali strategie userò per raggiungere questi obiettivi?",
                "Come misurerò il mio successo?"
            ],
            "monitoring_phase": [
                "Sto capendo il materiale o sto solo leggendo?",
                "Quali parti mi risultano difficili e perché?",
                "Le mie strategie stanno funzionando?"
            ],
            "evaluation_phase": [
                "Ho raggiunto i miei obiettivi? Come lo so?",
                "Cosa ha funzionato bene e cosa no?",
                "Cosa imparo su di me come studente?"
            ]
        }

        # Add level-appropriate prompts
        if learner_analysis.get("metacognitive_awareness") == "beginner":
            framework["scaffolding"] = {
                "guided_reflection": True,
                "prompt_frequency": "frequent",
                "simplification_level": "high"
            }
        elif learner_analysis.get("metacognitive_awareness") == "advanced":
            framework["scaffolding"] = {
                "guided_reflection": False,
                "prompt_frequency": "minimal",
                "simplification_level": "low"
            }

        return framework

    def _generate_self_assessment_tools(self) -> List[Dict[str, Any]]:
        """Generate self-assessment tools and instruments"""

        return [
            {
                "tool_type": "confidence_rating",
                "description": "Valuta la tua confidenza su ogni concetto (1-5)",
                "frequency": "post_session",
                "implementation": "scala numerica"
            },
            {
                "tool_type": "knowledge_audit",
                "description": "Autovalutazione della comprensione senza riferimenti",
                "frequency": "weekly",
                "implementation": "domande aperte"
            },
            {
                "tool_type": "strategy_effectiveness",
                "description": "Valuta l'efficacia delle strategie di studio usate",
                "frequency": "weekly",
                "implementation": "checklist"
            },
            {
                "tool_type": "progress_tracking",
                "description": "Monitoraggio dei progressi verso gli obiettivi",
                "frequency": "biweekly",
                "implementation": "grafici e metriche"
            }
        ]

    def _generate_goal_setting_framework(self) -> Dict[str, Any]:
        """Generate evidence-based goal setting framework"""

        return {
            "smart_goals": {
                "specific": "Obiettivi chiari e precisi",
                "measurable": "Metriche definite per valutare il progresso",
                "achievable": "Obiettivi realistici ma sfidanti",
                "relevant": "Allineati con gli obiettivi generali",
                "time_bound": "Con scadenze definite"
            },
            "goal_hierarchy": {
                "long_term_goals": "Obiettivi del corso completo",
                "medium_term_goals": "Obiettivi mensili/settimanali",
                "short_term_goals": "Obiettivi di sessione",
                "process_goals": "Obiettivi sul processo di apprendimento"
            },
            "implementation": {
                "goal_review_frequency": "settimanale",
                "goal_adjustment_triggers": ["performance", "motivazione", "tempo"],
                "celebration_milestones": ["settimanali", "mensili", "completamento"]
            }
        }

    def _define_progress_indicators(self) -> List[Dict[str, Any]]:
        """Define comprehensive progress indicators"""

        return [
            {
                "indicator": "session_completion_rate",
                "type": "quantitative",
                "target": 0.9,
                "measurement": "sessions_completed / sessions_planned"
            },
            {
                "indicator": "quiz_performance_average",
                "type": "quantitative",
                "target": 0.8,
                "measurement": "sum(quiz_scores) / number_of_quizzes"
            },
            {
                "indicator": "concept_mastery_level",
                "type": "qualitative",
                "target": "advanced",
                "measurement": "teacher_assessment + self_assessment"
            },
            {
                "indicator": "study_time_consistency",
                "type": "quantitative",
                "target": 0.8,
                "measurement": "actual_study_time / planned_study_time"
            },
            {
                "indicator": "strategy_application_frequency",
                "type": "quantitative",
                "target": 0.7,
                "measurement": "strategies_used / strategies_recommended"
            }
        ]

    async def _add_metacognitive_components(
        self,
        enhanced_plan: Dict[str, Any],
        learner_analysis: Dict[str, Any],
        structured_objectives: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Add advanced metacognitive components to the study plan"""

        # Generate reflection prompts based on objectives
        objectives = structured_objectives.get("structured_objectives", [])
        reflection_prompts = []

        for objective in objectives:
            objective_level = objective.get("cognitive_level", "")
            if objective_level == "metacognitive_development":
                reflection_prompts.extend(objective.get("metacognitive_prompts", []))
            else:
                # Generate generic prompts for other objectives
                reflection_prompts.extend([
                    f"Come valuto la mia comprensione di {objective.get('title', 'questo concetto')}?",
                    f"In che modi posso applicare {objective.get('title', 'questo concetto')} in situazioni reali?"
                ])

        # Add self-regulation tools
        self_regulation_tools = {
            "time_management": self._generate_time_management_tools(learner_analysis),
            "attention_control": self._generate_attention_control_strategies(learner_analysis),
            "motivation_maintenance": self._generate_motivation_strategies(),
            "stress_management": self._generate_stress_management_tools()
        }

        # Add reflection cycles
        reflection_cycles = {
            "daily_reflection": {
                "duration_minutes": 5,
                "prompts": [
                    "Cosa ho imparato oggi?",
                    "Cosa mi ha creato difficoltà?",
                    "Cosa farò diversamente domani?"
                ]
            },
            "weekly_reflection": {
                "duration_minutes": 15,
                "prompts": [
                    "Quali sono stati i miei successi questa settimana?",
                    "Dove ho bisogno di migliorare?",
                    "Le mie strategie sono state efficaci?"
                ]
            },
            "monthly_reflection": {
                "duration_minutes": 30,
                "prompts": [
                    "Come è progredita la mia comprensione complessiva?",
                    "Quali cambiamenti devo fare al mio piano di studio?",
                    "Sto sviluppando nuove abilità metacognitive?"
                ]
            }
        }

        enhanced_plan["metacognitive"].update({
            "reflection_prompts": reflection_prompts[:10],  # Limit to prevent overload
            "self_regulation_tools": self_regulation_tools,
            "reflection_cycles": reflection_cycles
        })

        return enhanced_plan

    def _generate_time_management_tools(self, learner_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate time management tools based on learner profile"""

        tools = {
            "pomodoro_technique": {
                "recommended": learner_analysis.get("attention_span") in ["short", "moderate"],
                "session_length": 25,
                "break_length": 5,
                "long_break_interval": 4
            },
            "time_blocking": {
                "recommended": learner_analysis.get("study_discipline") == "high",
                "implementation": "assign_specific_blocks",
                "flexibility_factor": 0.2
            },
            "energy_management": {
                "recommended": learner_analysis.get("motivation_level") == "high",
                "peak_time_identification": True,
                "energy_based_scheduling": True
            }
        }

        return tools

    def _generate_attention_control_strategies(self, learner_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate attention control strategies"""

        strategies = [
            {
                "strategy": "environment_optimization",
                "description": "Creare un ambiente di studio minimizzando le distrazioni",
                "effectiveness": 0.8
            },
            {
                "strategy": "mindfulness_techniques",
                "description": "Tecniche di mindfulness per migliorare la concentrazione",
                "effectiveness": 0.7
            },
            {
                "strategy": "task_segmentation",
                "description": "Suddividere i compiti complessi in segmenti gestibili",
                "effectiveness": 0.9
            }
        ]

        # Adjust based on attention span
        if learner_analysis.get("attention_span") == "short":
            strategies.insert(0, {
                "strategy": "micro_sessions",
                "description": "Sessioni molto brevi con pause frequenti",
                "effectiveness": 0.85
            })

        return strategies

    def _generate_motivation_strategies(self) -> List[Dict[str, Any]]:
        """Generate motivation maintenance strategies"""

        return [
            {
                "strategy": "goal_visualization",
                "description": "Visualizzare gli obiettivi e i progressi raggiunti",
                "application": "daily"
            },
            {
                "strategy": "progress_celebration",
                "description": "Celebrare i piccoli successi e i traguardi raggiunti",
                "application": "weekly"
            },
            {
                "strategy": "social_accountability",
                "description": "Condividere i progressi con qualcuno per mantenere l'impegno",
                "application": "biweekly"
            },
            {
                "strategy": "variety_introduction",
                "description": "Introdurre varietà nelle attività di studio",
                "application": "as_needed"
            }
        ]

    def _generate_stress_management_tools(self) -> List[Dict[str, Any]]:
        """Generate stress management tools"""

        return [
            {
                "tool": "breathing_exercises",
                "description": "Esercizi di respirazione per ridurre l'ansia pre-esame",
                "duration_minutes": 5,
                "frequency": "as_needed"
            },
            {
                "tool": "progressive_relaxation",
                "description": "Tecniche di rilassamento muscolare progressivo",
                "duration_minutes": 10,
                "frequency": "daily"
            },
            {
                "tool": "cognitive_restructuring",
                "description": "Tecniche per ristrutturare pensieri negativi",
                "duration_minutes": 15,
                "frequency": "weekly"
            }
        ]

    async def _generate_adaptive_elements(
        self,
        enhanced_plan: Dict[str, Any],
        learner_analysis: Dict[str, Any],
        previous_performance: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate adaptive elements for dynamic plan adjustment"""

        adaptive_elements = {
            "performance_triggers": self._define_performance_triggers(),
            "adaptation_strategies": self._generate_adaptation_strategies(),
            "flexibility_mechanisms": self._create_flexibility_mechanisms(),
            "personalization_factors": self._identify_personalization_factors(learner_analysis)
        }

        # Add performance-based adaptations
        if previous_performance:
            performance_patterns = previous_performance.get("performance_patterns", {})
            if performance_patterns.get("overall_trend") == "declining":
                adaptive_elements["intervention_needed"] = True
                adaptive_elements["recommended_interventions"] = [
                    "reduce_difficulty",
                    "increase_scaffolding",
                    "add_practice_sessions"
                ]
            elif performance_patterns.get("overall_trend") == "improving":
                adaptive_elements["acceleration_available"] = True
                adaptive_elements["enhancement_options"] = [
                    "increase_difficulty",
                    "add_advanced_topics",
                    "reduce_guidance"
                ]

        return adaptive_elements

    def _define_performance_triggers(self) -> Dict[str, Any]:
        """Define performance triggers for adaptive adjustments"""

        return {
            "low_performance_triggers": {
                "quiz_score_below": 0.6,
                "session_completion_below": 0.7,
                "consecutive_struggles": 3
            },
            "high_performance_triggers": {
                "quiz_score_above": 0.9,
                "session_completion_above": 0.95,
                "consistently_ahead": 2
            },
            "engagement_triggers": {
                "time_on_task_decline": 0.8,
                "participation_decrease": 0.7,
                "motivation_indicators": ["procrastination", "avoidance"]
            }
        }

    def _generate_adaptation_strategies(self) -> Dict[str, List[str]]:
        """Generate adaptation strategies for different scenarios"""

        return {
            "difficulty_adjustment": [
                "reduce_concept_load_per_session",
                "increase_scaffolding_and_examples",
                "provide_additional_practice_opportunities",
                "break_complex_tasks_into_smaller_steps"
            ],
            "pace_modification": [
                "extend_timeline_for_difficult_concepts",
                "introduce_review_sessions",
                "adjust_session_frequency",
                "modify_practice_intensity"
            ],
            "strategy_switching": [
                "try_alternative_learning_approaches",
                "integrate_new_study_techniques",
                "modify_content_presentation_format",
                "adjust_interaction_patterns"
            ],
            "motivation_enhancement": [
                "introduce_variety_in_activities",
                "set_intermediate_goals",
                "increase_positive_feedback",
                "connect_content_to_personal_interests"
            ]
        }

    def _create_flexibility_mechanisms(self) -> List[Dict[str, Any]]:
        """Create flexibility mechanisms for plan adjustments"""

        return [
            {
                "mechanism": "buffer_time",
                "description": "Include tempo extra per ritardi imprevisti",
                "implementation": "allocate_20_percent_extra_time",
                "trigger": "projections_based_on_history"
            },
            {
                "mechanism": "modular_structure",
                "description": "Struttura modulare per facile riorganizzazione",
                "implementation": "independent_learning_units",
                "trigger": "content_reordering_needed"
            },
            {
                "mechanism": "multiple_pathways",
                "description": "Percorsi alternativi per raggiungere gli obiettivi",
                "implementation": "parallel_learning_tracks",
                "trigger": "different_learning_preferences"
            },
            {
                "mechanism": "just_in_time_adjustments",
                "description": "Aggiustamenti basati su performance in tempo reale",
                "implementation": "dynamic_content_adaptation",
                "trigger": "real_time_performance_data"
            }
        ]

    def _identify_personalization_factors(self, learner_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Identify key personalization factors for the learner"""

        return {
            "learning_style_preference": learner_analysis.get("learning_style_preference", "mixed"),
            "optimal_session_length": learner_analysis.get("preferred_session_length", "moderate"),
            "feedback_frequency": learner_analysis.get("feedback_preference", "regular"),
            "challenge_tolerance": learner_analysis.get("challenge_tolerance", "moderate"),
            "social_learning_preference": learner_analysis.get("social_learning", "neutral"),
            "technology_comfort": learner_analysis.get("technology_comfort", "moderate"),
            "goal_orientation": learner_analysis.get("goal_orientation", "mastery")
        }

    def _predict_learning_success(
        self,
        learner_analysis: Dict[str, Any],
        strategies: Dict[str, Any],
        objectives: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Predict learning success probability and factors"""

        # Base factors
        factors = {
            "learner_discipline": learner_analysis.get("study_discipline", "moderate"),
            "time_availability": learner_analysis.get("time_availability", "moderate"),
            "experience_level": learner_analysis.get("experience_level", "intermediate"),
            "motivation_level": learner_analysis.get("motivation_level", "moderate"),
            "metacognitive_awareness": learner_analysis.get("metacognitive_awareness", "developing")
        }

        # Calculate base probability
        base_probability = 0.7  # 70% base success rate

        # Adjustments based on factors
        if factors["learner_discipline"] == "high":
            base_probability += 0.15
        elif factors["learner_discipline"] == "low":
            base_probability -= 0.2

        if factors["time_availability"] == "high":
            base_probability += 0.1
        elif factors["time_availability"] == "low":
            base_probability -= 0.15

        if factors["experience_level"] == "advanced":
            base_probability += 0.1
        elif factors["experience_level"] == "beginner":
            base_probability -= 0.05

        if factors["motivation_level"] == "high":
            base_probability += 0.15
        elif factors["motivation_level"] == "low":
            base_probability -= 0.25

        # Strategy effectiveness boost
        strategy_predictions = strategies.get("effectiveness_predictions", {})
        avg_strategy_effectiveness = sum(strategy_predictions.values()) / len(strategy_predictions) if strategy_predictions else 0.7
        base_probability += (avg_strategy_effectiveness - 0.7) * 0.5

        return {
            "success_probability": min(1.0, max(0.0, base_probability)),
            "success_factors": [
                factor for factor, value in factors.items()
                if value in ["high", "advanced"]
            ],
            "risk_factors": [
                factor for factor, value in factors.items()
                if value in ["low", "beginner"]
            ],
            "key_leverages": [
                "motivation_maintenance" if factors["motivation_level"] != "high" else None,
                "discipline_building" if factors["learner_discipline"] != "high" else None,
                "time_management" if factors["time_availability"] != "high" else None
            ],
            "confidence_level": "high" if base_probability > 0.8 else "medium" if base_probability > 0.6 else "low"
        }

    def _estimate_completion_probability(
        self,
        study_sessions: List[Dict[str, Any]],
        learner_analysis: Dict[str, Any]
    ) -> float:
        """Estimate probability of plan completion"""

        if not study_sessions:
            return 0.5

        # Historical completion factors
        discipline_factor = {
            "high": 0.9,
            "moderate": 0.75,
            "low": 0.5
        }.get(learner_analysis.get("study_discipline", "moderate"), 0.75)

        # Time availability factor
        time_factor = {
            "high": 0.95,
            "moderate": 0.8,
            "low": 0.6
        }.get(learner_analysis.get("time_availability", "moderate"), 0.8)

        # Motivation factor
        motivation_factor = {
            "high": 0.9,
            "moderate": 0.7,
            "low": 0.4
        }.get(learner_analysis.get("motivation_level", "moderate"), 0.7)

        # Session complexity factor
        avg_difficulty = sum(1 for session in study_sessions if session.get("difficulty_level") == "advanced") / len(study_sessions)
        complexity_factor = max(0.6, 1.0 - (avg_difficulty * 0.3))

        # Combined probability
        completion_probability = discipline_factor * time_factor * motivation_factor * complexity_factor

        return min(1.0, max(0.0, completion_probability))

    def _predict_mastery_achievement(self, objectives: Dict[str, Any]) -> Dict[str, Any]:
        """Predict mastery achievement levels for different objective types"""

        structured_objectives = objectives.get("structured_objectives", [])

        mastery_predictions = {
            "knowledge_acquisition": {"target_mastery": 0.85, "confidence": 0.8},
            "comprehension_application": {"target_mastery": 0.75, "confidence": 0.7},
            "synthesis_evaluation": {"target_mastery": 0.65, "confidence": 0.6},
            "metacognitive_development": {"target_mastery": 0.7, "confidence": 0.7}
        }

        # Adjust based on number of objectives
        for objective_type in mastery_predictions:
            count = len([obj for obj in structured_objectives if obj.get("cognitive_level") == objective_type])
            if count > 8:
                mastery_predictions[objective_type]["target_mastery"] -= 0.1
                mastery_predictions[objective_type]["confidence"] -= 0.1
            elif count < 3:
                mastery_predictions[objective_type]["target_mastery"] += 0.05

        return mastery_predictions

    async def _track_generation_analytics(
        self,
        course_id: str,
        learner_analysis: Dict[str, Any],
        strategies: Dict[str, Any],
        result: Dict[str, Any],
        duration: float
    ) -> None:
        """Track analytics for enhanced study plan generation"""

        try:
            analytics_data = {
                "prompt_type": "enhanced_study_plan_generation",
                "model_used": "GLM-4.6",
                "strategy": "learning_science_integration",
                "context": {
                    "course_id": course_id,
                    "learner_experience": learner_analysis.get("experience_level"),
                    "learner_discipline": learner_analysis.get("study_discipline"),
                    "primary_strategies": strategies.get("primary_strategies"),
                    "total_sessions": len(result.get("study_sessions", [])),
                    "estimated_duration": result.get("estimated_duration"),
                    "generation_time_seconds": duration,
                    "success_prediction": result.get("success_metrics", {}).get("success_prediction"),
                    "completion_probability": result.get("success_metrics", {}).get("completion_probability")
                }
            }

            await self.analytics.track_performance(analytics_data)

        except Exception as e:
            logger.error(f"Failed to track enhanced study plan analytics: {e}")

    async def _generate_fallback_plan(
        self,
        course_id: str,
        course_content: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate fallback study plan if enhanced generation fails"""

        return {
            "plan_id": f"fallback_plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "course_id": course_id,
            "study_sessions": [
                {
                    "session_id": "fallback_session_1",
                    "title": "Sessione di Studio Base",
                    "duration_minutes": 45,
                    "learning_objectives": ["comprensione_concetti"],
                    "difficulty_level": "intermediate",
                    "goals": ["Studiare i materiali", "Completare esercizi"],
                    "activities": ["Lettura", "Practice", "Review"]
                }
            ],
            "estimated_duration": 0.75,
            "metadata": {
                "generation_method": "fallback",
                "created_at": datetime.now().isoformat()
            }
        }