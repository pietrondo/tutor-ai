"""
Advanced Model Selector 2.0 for Tutor-AI
Intelligent routing between Z.AI GLM-4.6 and OpenRouter Claude-3.5
Based on task complexity, cognitive load, and pedagogical requirements
"""

import os
import json
from enum import Enum
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass

import structlog

logger = structlog.get_logger()

class TaskType(str, Enum):
    """Types of educational tasks"""
    SIMPLE_QA = "simple_qa"
    COMPLEX_REASONING = "complex_reasoning"
    PEDAGOGICAL_EXPLANATION = "pedagogical_explanation"
    CREATIVE_GENERATION = "creative_generation"
    VISUAL_REASONING = "visual_reasoning"
    MATHEMATICAL_PROBLEM = "mathematical_problem"
    CODE_GENERATION = "code_generation"
    MULTISTEP_PROBLEM = "multistep_problem"
    SUMMARIZATION = "summarization"
    TRANSLATION = "translation"

class CognitiveLoad(str, Enum):
    """Complexity levels of cognitive tasks"""
    LOW = "low"          # Simple recall, basic comprehension
    MEDIUM = "medium"    # Application, analysis
    HIGH = "high"        # Synthesis, evaluation
    COMPLEX = "complex"  # Multi-step, cross-domain reasoning

class PedagogicalFocus(str, Enum):
    """Educational focus areas"""
    CONCEPT_BUILDING = "concept_building"
    SKILL_PRACTICE = "skill_practice"
    PROBLEM_SOLVING = "problem_solving"
    CRITICAL_THINKING = "critical_thinking"
    CREATIVITY = "creativity"
    METACOGNITION = "metacognition"
    SCAFFOLDING = "scaffolding"
    ASSESSMENT = "assessment"

class BudgetMode(str, Enum):
    """Budget optimization modes"""
    OPTIMAL = "optimal"           # Best quality regardless of cost
    BALANCED = "balanced"         # Balance quality and cost
    ECONOMICAL = "economical"     # Minimize cost while maintaining quality

@dataclass
class ModelCapabilities:
    """Model capabilities and characteristics"""
    provider: str
    model_name: str
    max_context_tokens: int
    max_output_tokens: int
    strengths: List[TaskType]
    weaknesses: List[TaskType]
    cost_per_1k_tokens: float
    average_response_time_ms: float
    pedagogical_strength: Optional[PedagogicalFocus] = None
    supports_vision: bool = False
    supports_functions: bool = False
    reasoning_depth: int = 1  # 1-5 scale
    reliability_score: float = 1.0  # 0-1 scale

class AdvancedModelSelector:
    """Advanced model selection with pedagogical optimization"""

    def __init__(self):
        budget_env = os.getenv("BUDGET_MODE", "balanced").lower()
        # Handle legacy boolean values
        if budget_env in ["false", "true"]:
            self.budget_mode = BudgetMode("balanced")
        else:
            self.budget_mode = BudgetMode(budget_env)
        self.zai_manager = None
        self.openrouter_manager = None
        self.openai_manager = None
        self.local_manager = None

        # Initialize model capabilities
        self._initialize_model_capabilities()

        # Load performance data
        self._load_performance_data()

    def _initialize_model_capabilities(self):
        """Initialize model capability profiles"""
        self.models = {
            # Z.AI Models - Excellent for complex reasoning
            "zai_glm_4_6": ModelCapabilities(
                provider="zai",
                model_name="glm-4.6",
                max_context_tokens=128000,
                max_output_tokens=8192,
                strengths=[
                    TaskType.COMPLEX_REASONING,
                    TaskType.MULTISTEP_PROBLEM,
                    TaskType.MATHEMATICAL_PROBLEM,
                    TaskType.COMPLEX_REASONING
                ],
                weaknesses=[TaskType.VISUAL_REASONING],
                cost_per_1k_tokens=0.002,
                average_response_time_ms=1500,
                pedagogical_strength=PedagogicalFocus.PROBLEM_SOLVING,
                reasoning_depth=5,
                reliability_score=0.95
            ),

            "zai_glm_4_5_air": ModelCapabilities(
                provider="zai",
                model_name="glm-4.5-air",
                max_context_tokens=128000,
                max_output_tokens=8192,
                strengths=[
                    TaskType.PEDAGOGICAL_EXPLANATION,
                    TaskType.PEDAGOGICAL_EXPLANATION,
                    TaskType.SUMMARIZATION
                ],
                weaknesses=[TaskType.CODE_GENERATION],
                cost_per_1k_tokens=0.0015,
                average_response_time_ms=1200,
                pedagogical_strength=PedagogicalFocus.CONCEPT_BUILDING,
                reasoning_depth=4,
                reliability_score=0.93
            ),

            # OpenRouter Claude-3.5 - Excellent for pedagogical explanations
            "openrouter_claude_3_5_sonnet": ModelCapabilities(
                provider="openrouter",
                model_name="anthropic/claude-3.5-sonnet",
                max_context_tokens=200000,
                max_output_tokens=8192,
                strengths=[
                    TaskType.PEDAGOGICAL_EXPLANATION,
                    TaskType.COMPLEX_REASONING,
                    TaskType.PEDAGOGICAL_EXPLANATION,
                    TaskType.COMPLEX_REASONING
                ],
                weaknesses=[TaskType.MATHEMATICAL_PROBLEM],
                cost_per_1k_tokens=0.003,
                average_response_time_ms=1800,
                pedagogical_strength=PedagogicalFocus.SCAFFOLDING,
                reasoning_depth=5,
                reliability_score=0.98
            ),

            # OpenRouter GPT-4o - Fast and capable
            "openrouter_gpt_4o": ModelCapabilities(
                provider="openrouter",
                model_name="openai/gpt-4o",
                max_context_tokens=128000,
                max_output_tokens=4096,
                strengths=[
                    TaskType.MULTISTEP_PROBLEM,
                    TaskType.CODE_GENERATION,
                    TaskType.CREATIVE_GENERATION,
                    TaskType.SUMMARIZATION
                ],
                weaknesses=[TaskType.VISUAL_REASONING],
                cost_per_1k_tokens=0.0025,
                average_response_time_ms=800,
                pedagogical_strength=PedagogicalFocus.SKILL_PRACTICE,
                reasoning_depth=4,
                reliability_score=0.97,
                supports_functions=True
            ),

            # OpenAI GPT-4o - Fast with vision capabilities
            "openai_gpt_4o": ModelCapabilities(
                provider="openai",
                model_name="gpt-4o",
                max_context_tokens=128000,
                max_output_tokens=4096,
                strengths=[
                    TaskType.MULTISTEP_PROBLEM,
                    TaskType.CODE_GENERATION,
                    TaskType.VISUAL_REASONING,
                    TaskType.CREATIVE_GENERATION
                ],
                weaknesses=[TaskType.MATHEMATICAL_PROBLEM],
                cost_per_1k_tokens=0.005,
                average_response_time_ms=700,
                reasoning_depth=4,
                reliability_score=0.99,
                supports_vision=True,
                supports_functions=True
            ),

            # Local Models - Cost-effective but less capable
            "local_llama3_1": ModelCapabilities(
                provider="local",
                model_name="llama3.1:8b",
                max_context_tokens=8192,
                max_output_tokens=2048,
                strengths=[
                    TaskType.SIMPLE_QA,
                    TaskType.SUMMARIZATION,
                    TaskType.TRANSLATION
                ],
                weaknesses=[
                    TaskType.COMPLEX_REASONING,
                    TaskType.MULTISTEP_PROBLEM
                ],
                cost_per_1k_tokens=0.0001,
                average_response_time_ms=2000,
                reasoning_depth=2,
                reliability_score=0.85
            )
        }

    def _load_performance_data(self):
        """Load historical performance data for optimization"""
        try:
            with open("data/prompt_analytics/metrics.json", 'r') as f:
                self.performance_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.performance_data = {}

    def select_optimal_model(self,
                           task_type: TaskType,
                           cognitive_load: CognitiveLoad = CognitiveLoad.MEDIUM,
                           pedagogical_focus: Optional[PedagogicalFocus] = None,
                           requires_vision: bool = False,
                           requires_functions: bool = False,
                           context_size: int = 1000,
                           output_size: int = 500,
                           budget_mode: Optional[BudgetMode] = None) -> Dict[str, Any]:
        """
        Select the optimal model for a given educational task

        Args:
            task_type: Type of educational task
            cognitive_load: Complexity of the cognitive task
            pedagogical_focus: Specific educational focus area
            requires_vision: Whether vision capabilities are needed
            requires_functions: Whether function calling is needed
            context_size: Estimated context size in tokens
            output_size: Estimated output size in tokens
            budget_mode: Budget optimization mode

        Returns:
            Dictionary with model selection and reasoning
        """
        budget_mode = budget_mode or self.budget_mode

        # Filter candidates based on hard requirements
        candidates = self._filter_candidates(
            requires_vision, requires_functions, context_size, output_size
        )

        if not candidates:
            logger.warning("No models meet requirements, falling back to basic model")
            return self._get_fallback_model()

        # Score candidates based on task requirements
        scored_candidates = []
        for model_key, model in candidates.items():
            score = self._calculate_model_score(
                model, task_type, cognitive_load, pedagogical_focus, budget_mode
            )
            scored_candidates.append((model_key, model, score))

        # Sort by score (descending)
        scored_candidates.sort(key=lambda x: x[2], reverse=True)

        # Select best candidate
        best_model_key, best_model, best_score = scored_candidates[0]

        # Prepare result with reasoning
        result = {
            "model_key": best_model_key,
            "provider": best_model.provider,
            "model_name": best_model.model_name,
            "score": best_score,
            "reasoning": self._explain_selection(
                best_model, task_type, cognitive_load, pedagogical_focus, budget_mode
            ),
            "estimated_cost": self._estimate_cost(best_model, context_size, output_size),
            "estimated_time": best_model.average_response_time_ms,
            "alternatives": [
                {
                    "model_key": key,
                    "model_name": model.model_name,
                    "score": score,
                    "reason": f"Alternative option with {score:.2f} score"
                }
                for key, model, score in scored_candidates[1:3]  # Top 3 alternatives
            ]
        }

        logger.info(
            "Selected optimal model",
            model=best_model.model_name,
            provider=best_model.provider,
            task_type=task_type,
            score=best_score,
            cognitive_load=cognitive_load
        )

        return result

    def _filter_candidates(self,
                          requires_vision: bool,
                          requires_functions: bool,
                          context_size: int,
                          output_size: int) -> Dict[str, ModelCapabilities]:
        """Filter models based on hard requirements"""
        candidates = {}

        for model_key, model in self.models.items():
            # Check context size
            if context_size > model.max_context_tokens:
                continue

            # Check output size
            if output_size > model.max_output_tokens:
                continue

            # Check vision requirement
            if requires_vision and not model.supports_vision:
                continue

            # Check functions requirement
            if requires_functions and not model.supports_functions:
                continue

            candidates[model_key] = model

        return candidates

    def _calculate_model_score(self,
                             model: ModelCapabilities,
                             task_type: TaskType,
                             cognitive_load: CognitiveLoad,
                             pedagogical_focus: Optional[PedagogicalFocus],
                             budget_mode: BudgetMode) -> float:
        """Calculate score for model based on task requirements"""

        # Base score from task compatibility
        task_score = 1.0 if task_type in model.strengths else 0.5
        if task_type in model.weaknesses:
            task_score *= 0.3

        # Cognitive load matching
        load_scores = {
            CognitiveLoad.LOW: {1: 1.0, 2: 0.8, 3: 0.6, 4: 0.4, 5: 0.2},
            CognitiveLoad.MEDIUM: {1: 0.6, 2: 1.0, 3: 0.9, 4: 0.7, 5: 0.5},
            CognitiveLoad.HIGH: {1: 0.3, 2: 0.6, 3: 1.0, 4: 0.9, 5: 0.8},
            CognitiveLoad.COMPLEX: {1: 0.1, 2: 0.3, 3: 0.7, 4: 1.0, 5: 1.0}
        }
        load_score = load_scores[cognitive_load].get(model.reasoning_depth, 0.5)

        # Pedagogical focus matching
        pedagogy_score = 1.0
        if pedagogical_focus and model.pedagogical_strength == pedagogical_focus:
            pedagogy_score = 1.2  # 20% boost for perfect match
        elif pedagogical_focus and model.pedagogical_strength:
            pedagogy_score = 0.9  # Slight penalty for mismatch
        elif pedagogical_focus:
            pedagogy_score = 0.7  # Penalty for no pedagogical strength

        # Budget optimization
        budget_score = self._calculate_budget_score(model, budget_mode)

        # Reliability factor
        reliability_score = model.reliability_score

        # Performance history (if available)
        performance_score = self._get_performance_score(model)

        # Calculate weighted total score
        weights = {
            "task": 0.30,
            "load": 0.20,
            "pedagogy": 0.15,
            "budget": 0.15,
            "reliability": 0.10,
            "performance": 0.10
        }

        total_score = (
            weights["task"] * task_score +
            weights["load"] * load_score +
            weights["pedagogy"] * pedagogy_score +
            weights["budget"] * budget_score +
            weights["reliability"] * reliability_score +
            weights["performance"] * performance_score
        )

        return total_score

    def _calculate_budget_score(self, model: ModelCapabilities, budget_mode: BudgetMode) -> float:
        """Calculate budget optimization score"""
        if budget_mode == BudgetMode.OPTIMAL:
            # Prefer better models regardless of cost
            cost_scores = {0.005: 0.7, 0.003: 0.8, 0.0025: 0.85, 0.002: 0.9, 0.0015: 0.95, 0.0001: 1.0}
        elif budget_mode == BudgetMode.BALANCED:
            # Balance cost and quality
            cost_scores = {0.005: 0.6, 0.003: 0.75, 0.0025: 0.85, 0.002: 0.9, 0.0015: 0.9, 0.0001: 0.7}
        else:  # ECONOMICAL
            # Prefer cheaper models
            cost_scores = {0.005: 0.4, 0.003: 0.5, 0.0025: 0.6, 0.002: 0.7, 0.0015: 0.8, 0.0001: 1.0}

        return cost_scores.get(model.cost_per_1k_tokens, 0.5)

    def _get_performance_score(self, model: ModelCapabilities) -> float:
        """Get historical performance score for model"""
        # Look up performance data for this model
        provider_metrics = self.performance_data.get("model_providers", {}).get(model.provider, {})

        if provider_metrics:
            success_rate = provider_metrics.get("success_rate", 0.9)
            avg_time = provider_metrics.get("avg_execution_time", 1000)

            # Score based on success rate and speed
            time_score = max(0, 1 - (avg_time - model.average_response_time_ms) / 5000)
            return (success_rate * 0.7 + time_score * 0.3)

        return model.reliability_score

    def _explain_selection(self,
                          model: ModelCapabilities,
                          task_type: TaskType,
                          cognitive_load: CognitiveLoad,
                          pedagogical_focus: Optional[PedagogicalFocus],
                          budget_mode: BudgetMode) -> str:
        """Generate explanation for model selection"""
        reasons = []

        # Task compatibility
        if task_type in model.strengths:
            reasons.append(f"Excellent for {task_type.value} tasks")
        elif task_type in model.weaknesses:
            reasons.append(f"Not ideal for {task_type.value}, but acceptable")

        # Cognitive load
        if model.reasoning_depth >= 4 and cognitive_load in [CognitiveLoad.HIGH, CognitiveLoad.COMPLEX]:
            reasons.append(f"High reasoning capability ({model.reasoning_depth}/5) matches complex cognitive load")
        elif model.reasoning_depth <= 2 and cognitive_load == CognitiveLoad.LOW:
            reasons.append(f"Efficient for simple cognitive tasks")

        # Pedagogical focus
        if pedagogical_focus and model.pedagogical_strength == pedagogical_focus:
            reasons.append(f"Specialized for {pedagogical_focus.value}")
        elif pedagogical_focus:
            reasons.append(f"Capable for {pedagogical_focus.value}")

        # Budget considerations
        if budget_mode == BudgetMode.ECONOMICAL and model.cost_per_1k_tokens < 0.002:
            reasons.append(f"Cost-effective at ${model.cost_per_1k_tokens:.4f}/1k tokens")
        elif budget_mode == BudgetMode.OPTIMAL and model.reasoning_depth >= 4:
            reasons.append("Optimal quality for educational tasks")

        # Special capabilities
        if model.supports_vision:
            reasons.append("Supports visual reasoning")
        if model.supports_functions:
            reasons.append("Supports function calling")

        return "; ".join(reasons)

    def _estimate_cost(self, model: ModelCapabilities, context_size: int, output_size: int) -> float:
        """Estimate cost for this request"""
        total_tokens = context_size + output_size
        return (total_tokens / 1000) * model.cost_per_1k_tokens

    def _get_fallback_model(self) -> Dict[str, Any]:
        """Get fallback model when no suitable model is found"""
        fallback_key = "local_llama3_1"
        fallback_model = self.models.get(fallback_key)

        if not fallback_model:
            fallback_key = "zai_glm_4_5_air"
            fallback_model = self.models.get(fallback_key)

        return {
            "model_key": fallback_key,
            "provider": fallback_model.provider if fallback_model else "unknown",
            "model_name": fallback_model.model_name if fallback_model else "unknown",
            "score": 0.5,
            "reasoning": "Fallback model - no suitable models found for requirements",
            "estimated_cost": 0.001,
            "estimated_time": 2000,
            "alternatives": []
        }

    def get_model_recommendations(self,
                                 task_description: str) -> List[Dict[str, Any]]:
        """Get model recommendations for a described task"""
        # Analyze task description to infer requirements
        task_type = self._infer_task_type(task_description)
        cognitive_load = self._infer_cognitive_load(task_description)
        pedagogical_focus = self._infer_pedagogical_focus(task_description)

        # Get recommendations for different budget modes
        recommendations = []
        for budget_mode in BudgetMode:
            try:
                selection = self.select_optimal_model(
                    task_type=task_type,
                    cognitive_load=cognitive_load,
                    pedagogical_focus=pedagogical_focus,
                    budget_mode=budget_mode
                )
                selection["budget_mode"] = budget_mode.value
                recommendations.append(selection)
            except Exception as e:
                logger.error(f"Failed to get recommendation for {budget_mode}: {e}")

        return recommendations

    def _infer_task_type(self, description: str) -> TaskType:
        """Infer task type from description"""
        description_lower = description.lower()

        if any(word in description_lower for word in ["explain", "teach", "clarify", "describe"]):
            return TaskType.PEDAGOGICAL_EXPLANATION
        elif any(word in description_lower for word in ["solve", "calculate", "compute", "analyze"]):
            return TaskType.MULTISTEP_PROBLEM
        elif any(word in description_lower for word in ["create", "generate", "write", "compose"]):
            return TaskType.CREATIVE_GENERATION
        elif any(word in description_lower for word in ["summarize", "condense", "outline"]):
            return TaskType.SUMMARIZATION
        elif any(word in description_lower for word in ["code", "program", "script"]):
            return TaskType.CODE_GENERATION
        else:
            return TaskType.SIMPLE_QA

    def _infer_cognitive_load(self, description: str) -> CognitiveLoad:
        """Infer cognitive load from description"""
        description_lower = description.lower()

        complex_indicators = ["analyze", "synthesize", "evaluate", "compare", "multiple steps", "complex"]
        high_indicators = ["apply", "explain why", "solve problem", "demonstrate"]
        medium_indicators = ["describe", "identify", "list", "define"]

        if any(indicator in description_lower for indicator in complex_indicators):
            return CognitiveLoad.COMPLEX
        elif any(indicator in description_lower for indicator in high_indicators):
            return CognitiveLoad.HIGH
        elif any(indicator in description_lower for indicator in medium_indicators):
            return CognitiveLoad.MEDIUM
        else:
            return CognitiveLoad.LOW

    def _infer_pedagogical_focus(self, description: str) -> Optional[PedagogicalFocus]:
        """Infer pedagogical focus from description"""
        description_lower = description.lower()

        focus_keywords = {
            PedagogicalFocus.CONCEPT_BUILDING: ["concept", "understand", "define", "explain"],
            PedagogicalFocus.SKILL_PRACTICE: ["practice", "exercise", "drill", "repeat"],
            PedagogicalFocus.PROBLEM_SOLVING: ["solve", "problem", "challenge", "solution"],
            PedagogicalFocus.CRITICAL_THINKING: ["analyze", "evaluate", "critique", "compare"],
            PedagogicalFocus.CREATIVITY: ["create", "design", "imagine", "innovate"],
            PedagogicalFocus.SCAFFOLDING: ["guide", "support", "step by step", "help"],
            PedagogicalFocus.ASSESSMENT: ["test", "quiz", "evaluate", "assess"]
        }

        for focus, keywords in focus_keywords.items():
            if any(keyword in description_lower for keyword in keywords):
                return focus

        return None

# Global instance
advanced_model_selector = AdvancedModelSelector()