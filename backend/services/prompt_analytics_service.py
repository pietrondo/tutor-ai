"""
Prompt Analytics Service for Tutor-AI
Monitor, analyze, and optimize prompt performance across different AI models
"""

import json
import time
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import asdict, dataclass
from enum import Enum
import statistics

import structlog
from pydantic import BaseModel

logger = structlog.get_logger()

class PromptType(str, Enum):
    CHAT_TUTORING = "chat_tutoring"
    QUIZ_GENERATION = "quiz_generation"
    MINDMAP_GENERATION = "mindmap_generation"
    STUDY_PLAN = "study_plan"
    SLIDE_GENERATION = "slide_generation"
    CONCEPT_EXTRACTION = "concept_extraction"
    ACTIVE_RECALL = "active_recall"

class ModelProvider(str, Enum):
    ZAI = "zai"
    OPENAI = "openai"
    OPENROUTER = "openrouter"
    OLLAMA = "ollama"
    LMSTUDIO = "lmstudio"

class CognitiveLoad(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    COMPLEX = "complex"

@dataclass
class PromptPerformance:
    """Individual prompt execution performance data"""
    id: str
    prompt_type: PromptType
    model_provider: ModelProvider
    model_name: str
    prompt_template: str
    prompt_length: int
    response_length: int
    execution_time_ms: float
    token_usage: int
    cost_estimate: float
    cognitive_load: CognitiveLoad
    success: bool
    error_message: Optional[str] = None
    user_feedback: Optional[Dict[str, Any]] = None
    learning_outcomes: Optional[Dict[str, float]] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

class PromptAnalyticsService:
    """Service for monitoring and analyzing prompt performance"""

    def __init__(self, storage_path: str = "data/prompt_analytics"):
        self.storage_path = storage_path
        self.performances_file = f"{storage_path}/performances.json"
        self.metrics_file = f"{storage_path}/metrics.json"
        self.experiments_file = f"{storage_path}/experiments.json"

        self._ensure_storage()
        self._load_metrics()

    def _ensure_storage(self):
        """Create storage directories and files"""
        import os
        os.makedirs(self.storage_path, exist_ok=True)

        # Initialize files if they don't exist
        for file_path in [self.performances_file, self.metrics_file, self.experiments_file]:
            if not os.path.exists(file_path):
                with open(file_path, 'w') as f:
                    json.dump({}, f, indent=2, default=str)

    def _load_metrics(self):
        """Load existing metrics from storage"""
        try:
            with open(self.metrics_file, 'r') as f:
                self.metrics = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.metrics = {
                "total_prompts": 0,
                "successful_prompts": 0,
                "failed_prompts": 0,
                "average_execution_time": 0.0,
                "total_cost": 0.0,
                "prompt_types": {},
                "model_providers": {},
                "cognitive_loads": {}
            }

    def _save_metrics(self):
        """Save metrics to storage"""
        try:
            with open(self.metrics_file, 'w') as f:
                json.dump(self.metrics, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save metrics: {e}")

    def record_prompt_execution(self, performance: PromptPerformance) -> str:
        """Record a prompt execution for analytics"""
        try:
            # Generate unique ID if not provided
            if not performance.id:
                performance.id = str(uuid.uuid4())

            # Load existing performances
            try:
                with open(self.performances_file, 'r') as f:
                    performances = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                performances = {}

            # Add new performance
            performances[performance.id] = {
                **asdict(performance),
                "timestamp": performance.timestamp.isoformat()
            }

            # Save updated performances
            with open(self.performances_file, 'w') as f:
                json.dump(performances, f, indent=2, default=str)

            # Update aggregated metrics
            self._update_metrics(performance)

            logger.info(
                "Recorded prompt execution",
                prompt_id=performance.id,
                prompt_type=performance.prompt_type,
                model=performance.model_name,
                execution_time_ms=performance.execution_time_ms,
                success=performance.success
            )

            return performance.id

        except Exception as e:
            logger.error(f"Failed to record prompt execution: {e}")
            return ""

    def _update_metrics(self, performance: PromptPerformance):
        """Update aggregated metrics with new performance data"""
        self.metrics["total_prompts"] += 1

        if performance.success:
            self.metrics["successful_prompts"] += 1
        else:
            self.metrics["failed_prompts"] += 1

        # Update average execution time
        total_time = self.metrics.get("total_execution_time", 0) * (self.metrics["total_prompts"] - 1)
        total_time += performance.execution_time_ms
        self.metrics["average_execution_time"] = total_time / self.metrics["total_prompts"]
        self.metrics["total_execution_time"] = total_time

        # Update cost
        self.metrics["total_cost"] += performance.cost_estimate

        # Update prompt type metrics
        prompt_type = performance.prompt_type.value
        if prompt_type not in self.metrics["prompt_types"]:
            self.metrics["prompt_types"][prompt_type] = {
                "count": 0,
                "success_rate": 0.0,
                "avg_execution_time": 0.0,
                "avg_cost": 0.0
            }

        pt_metrics = self.metrics["prompt_types"][prompt_type]
        pt_metrics["count"] += 1

        # Update success rate for prompt type
        successful_count = pt_metrics.get("successful_count", 0)
        if performance.success:
            successful_count += 1
        pt_metrics["successful_count"] = successful_count
        pt_metrics["success_rate"] = successful_count / pt_metrics["count"]

        # Update averages for prompt type
        pt_total_time = pt_metrics.get("total_time", 0) * (pt_metrics["count"] - 1)
        pt_total_time += performance.execution_time_ms
        pt_metrics["avg_execution_time"] = pt_total_time / pt_metrics["count"]
        pt_metrics["total_time"] = pt_total_time

        pt_total_cost = pt_metrics.get("total_cost", 0) * (pt_metrics["count"] - 1)
        pt_total_cost += performance.cost_estimate
        pt_metrics["avg_cost"] = pt_total_cost / pt_metrics["count"]
        pt_metrics["total_cost"] = pt_total_cost

        # Update model provider metrics
        provider = performance.model_provider.value
        if provider not in self.metrics["model_providers"]:
            self.metrics["model_providers"][provider] = {
                "count": 0,
                "success_rate": 0.0,
                "avg_execution_time": 0.0,
                "avg_cost": 0.0
            }

        mp_metrics = self.metrics["model_providers"][provider]
        mp_metrics["count"] += 1

        mp_successful = mp_metrics.get("successful_count", 0)
        if performance.success:
            mp_successful += 1
        mp_metrics["successful_count"] = mp_successful
        mp_metrics["success_rate"] = mp_successful / mp_metrics["count"]

        # Update cognitive load metrics
        load = performance.cognitive_load.value
        if load not in self.metrics["cognitive_loads"]:
            self.metrics["cognitive_loads"][load] = {
                "count": 0,
                "success_rate": 0.0,
                "avg_execution_time": 0.0
            }

        cl_metrics = self.metrics["cognitive_loads"][load]
        cl_metrics["count"] += 1

        cl_successful = cl_metrics.get("successful_count", 0)
        if performance.success:
            cl_successful += 1
        cl_metrics["successful_count"] = cl_successful
        cl_metrics["success_rate"] = cl_successful / cl_metrics["count"]

        self._save_metrics()

    def get_prompt_performance_stats(self,
                                    prompt_type: Optional[PromptType] = None,
                                    model_provider: Optional[ModelProvider] = None,
                                    hours_back: int = 24) -> Dict[str, Any]:
        """Get performance statistics for prompts"""
        try:
            # Load recent performances
            cutoff_time = datetime.now() - timedelta(hours=hours_back)

            with open(self.performances_file, 'r') as f:
                performances = json.load(f)

            # Filter performances
            filtered_performances = []
            for perf_data in performances.values():
                perf_time = datetime.fromisoformat(perf_data["timestamp"])
                if perf_time >= cutoff_time:
                    if prompt_type and perf_data["prompt_type"] != prompt_type.value:
                        continue
                    if model_provider and perf_data["model_provider"] != model_provider.value:
                        continue
                    filtered_performances.append(perf_data)

            if not filtered_performances:
                return {
                    "count": 0,
                    "success_rate": 0.0,
                    "avg_execution_time": 0.0,
                    "avg_cost": 0.0,
                    "error_rate": 0.0
                }

            # Calculate statistics
            successful = len([p for p in filtered_performances if p["success"]])
            success_rate = successful / len(filtered_performances)

            execution_times = [p["execution_time_ms"] for p in filtered_performances]
            avg_execution_time = statistics.mean(execution_times)

            costs = [p["cost_estimate"] for p in filtered_performances]
            avg_cost = statistics.mean(costs)

            return {
                "count": len(filtered_performances),
                "success_rate": success_rate,
                "avg_execution_time": avg_execution_time,
                "avg_cost": avg_cost,
                "error_rate": 1.0 - success_rate,
                "execution_time_p50": statistics.median(execution_times),
                "execution_time_p95": sorted(execution_times)[int(len(execution_times) * 0.95)] if len(execution_times) > 1 else 0,
                "total_cost": sum(costs)
            }

        except Exception as e:
            logger.error(f"Failed to get prompt performance stats: {e}")
            return {}

    def compare_prompt_variants(self,
                               prompt_type: PromptType,
                               variant_a_template: str,
                               variant_b_template: str,
                               sample_size: int = 100) -> Dict[str, Any]:
        """Compare performance of two prompt variants (A/B testing)"""
        try:
            # Get performances for both variants
            with open(self.performances_file, 'r') as f:
                performances = json.load(f)

            variant_a_perfs = []
            variant_b_perfs = []

            for perf_data in performances.values():
                if perf_data["prompt_type"] == prompt_type.value:
                    if perf_data.get("prompt_template", "").startswith(variant_a_template[:50]):
                        variant_a_perfs.append(perf_data)
                    elif perf_data.get("prompt_template", "").startswith(variant_b_template[:50]):
                        variant_b_perfs.append(perf_data)

            # Limit to sample size
            variant_a_perfs = variant_a_perfs[:sample_size]
            variant_b_perfs = variant_b_perfs[:sample_size]

            if len(variant_a_perfs) < 10 or len(variant_b_perfs) < 10:
                return {
                    "error": "Insufficient data for comparison",
                    "variant_a_count": len(variant_a_perfs),
                    "variant_b_count": len(variant_b_perfs),
                    "minimum_required": 10
                }

            # Calculate comparison metrics
            def calculate_metrics(perfs):
                successful = len([p for p in perfs if p["success"]])
                execution_times = [p["execution_time_ms"] for p in perfs]
                costs = [p["cost_estimate"] for p in perfs]

                return {
                    "success_rate": successful / len(perfs),
                    "avg_execution_time": statistics.mean(execution_times),
                    "avg_cost": statistics.mean(costs),
                    "count": len(perfs)
                }

            variant_a_metrics = calculate_metrics(variant_a_perfs)
            variant_b_metrics = calculate_metrics(variant_b_perfs)

            # Calculate statistical significance (simplified)
            def calculate_significance(metric_a, metric_b, count_a, count_b):
                # Simplified t-test approximation
                if metric_a == metric_b:
                    return 0.5

                pooled_std = 0.1  # Assumed standard deviation for simplification
                standard_error = pooled_std * (1/count_a + 1/count_b) ** 0.5
                z_score = abs(metric_a - metric_b) / standard_error

                # Convert z-score to significance level (simplified)
                if z_score > 2.58:
                    return 0.99  # 99% confidence
                elif z_score > 1.96:
                    return 0.95  # 95% confidence
                elif z_score > 1.65:
                    return 0.90  # 90% confidence
                else:
                    return 0.5   # Not significant

            return {
                "variant_a": {
                    **variant_a_metrics,
                    "template_preview": variant_a_template[:100] + "..."
                },
                "variant_b": {
                    **variant_b_metrics,
                    "template_preview": variant_b_template[:100] + "..."
                },
                "comparison": {
                    "success_rate_improvement": ((variant_b_metrics["success_rate"] - variant_a_metrics["success_rate"]) / variant_a_metrics["success_rate"]) * 100,
                    "execution_time_improvement": ((variant_a_metrics["avg_execution_time"] - variant_b_metrics["avg_execution_time"]) / variant_a_metrics["avg_execution_time"]) * 100,
                    "cost_difference": variant_b_metrics["avg_cost"] - variant_a_metrics["avg_cost"],
                    "significance": calculate_significance(
                        variant_a_metrics["success_rate"],
                        variant_b_metrics["success_rate"],
                        variant_a_metrics["count"],
                        variant_b_metrics["count"]
                    )
                },
                "recommendation": self._get_comparison_recommendation(variant_a_metrics, variant_b_metrics)
            }

        except Exception as e:
            logger.error(f"Failed to compare prompt variants: {e}")
            return {"error": str(e)}

    def _get_comparison_recommendation(self, metrics_a: Dict, metrics_b: Dict) -> str:
        """Get recommendation based on A/B test results"""
        a_score = self._calculate_overall_score(metrics_a)
        b_score = self._calculate_overall_score(metrics_b)

        if b_score > a_score * 1.05:  # 5% improvement threshold
            return "Adopt Variant B - shows significant improvement"
        elif a_score > b_score * 1.05:
            return "Keep Variant A - shows better performance"
        else:
            return "Results inconclusive - consider larger sample size or different metrics"

    def _calculate_overall_score(self, metrics: Dict) -> float:
        """Calculate overall performance score from metrics"""
        # Weight different factors
        success_weight = 0.4
        speed_weight = 0.3  # Lower execution time is better
        cost_weight = 0.3    # Lower cost is better

        # Normalize metrics (0-1 scale)
        success_score = metrics["success_rate"]

        # For execution time and cost, lower is better, so invert
        # Assuming 5000ms and $0.01 as reasonable maxima
        speed_score = max(0, 1 - (metrics["avg_execution_time"] / 5000))
        cost_score = max(0, 1 - (metrics["avg_cost"] / 0.01))

        return (success_weight * success_score +
                speed_weight * speed_score +
                cost_weight * cost_score)

    def get_optimization_recommendations(self) -> List[Dict[str, Any]]:
        """Get optimization recommendations based on performance data"""
        try:
            recommendations = []

            # Analyze each prompt type
            for prompt_type in PromptType:
                stats = self.get_prompt_performance_stats(prompt_type=prompt_type, hours_back=168)  # Last week

                if stats["count"] < 10:
                    continue

                # Check for issues
                if stats["success_rate"] < 0.9:
                    recommendations.append({
                        "priority": "high",
                        "prompt_type": prompt_type.value,
                        "issue": "Low success rate",
                        "current_rate": stats["success_rate"],
                        "recommendation": "Review prompt template for clarity and model compatibility"
                    })

                if stats["avg_execution_time"] > 5000:  # 5 seconds
                    recommendations.append({
                        "priority": "medium",
                        "prompt_type": prompt_type.value,
                        "issue": "High execution time",
                        "current_time": stats["avg_execution_time"],
                        "recommendation": "Consider using faster model or simplifying prompt"
                    })

                if stats["avg_cost"] > 0.01:  # $0.01 per request
                    recommendations.append({
                        "priority": "medium",
                        "prompt_type": prompt_type.value,
                        "issue": "High cost per request",
                        "current_cost": stats["avg_cost"],
                        "recommendation": "Optimize prompt length or use more cost-effective model"
                    })

            # Sort by priority
            priority_order = {"high": 1, "medium": 2, "low": 3}
            recommendations.sort(key=lambda x: priority_order.get(x["priority"], 3))

            return recommendations

        except Exception as e:
            logger.error(f"Failed to get optimization recommendations: {e}")
            return []

    def export_performance_data(self,
                               format: str = "json",
                               hours_back: int = 168) -> str:
        """Export performance data for external analysis"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours_back)

            with open(self.performances_file, 'r') as f:
                performances = json.load(f)

            # Filter recent performances
            recent_performances = {
                pid: perf for pid, perf in performances.items()
                if datetime.fromisoformat(perf["timestamp"]) >= cutoff_time
            }

            if format.lower() == "json":
                return json.dumps(recent_performances, indent=2, default=str)
            elif format.lower() == "csv":
                # Convert to CSV format
                if not recent_performances:
                    return ""

                headers = [
                    "id", "prompt_type", "model_provider", "model_name",
                    "execution_time_ms", "success", "cost_estimate", "timestamp"
                ]

                csv_lines = [",".join(headers)]
                for perf in recent_performances.values():
                    row = [
                        perf.get("id", ""),
                        perf.get("prompt_type", ""),
                        perf.get("model_provider", ""),
                        perf.get("model_name", ""),
                        str(perf.get("execution_time_ms", 0)),
                        str(perf.get("success", False)),
                        str(perf.get("cost_estimate", 0)),
                        perf.get("timestamp", "")
                    ]
                    csv_lines.append(",".join(row))

                return "\n".join(csv_lines)
            else:
                raise ValueError(f"Unsupported export format: {format}")

        except Exception as e:
            logger.error(f"Failed to export performance data: {e}")
            return ""

    async def log_slide_generation(
        self,
        user_id: str,
        course_id: str,
        book_id: Optional[str] = None,
        topic: str = "",
        slide_count: int = 0,
        generation_time: float = 0.0,
        principles_applied: List[str] = None,
        cognitive_load_level: str = "moderate",
        success: bool = True,
        error_message: Optional[str] = None
    ) -> None:
        """
        Log slide generation analytics data.

        Args:
            user_id: User identifier
            course_id: Course identifier
            book_id: Optional book identifier
            topic: Main topic for slides
            slide_count: Number of slides generated
            generation_time: Time taken to generate slides
            principles_applied: List of multimedia principles applied
            cognitive_load_level: Cognitive load level of content
            success: Whether generation was successful
            error_message: Error message if generation failed
        """
        try:
            performance_data = {
                "id": str(uuid.uuid4()),
                "prompt_type": PromptType.SLIDE_GENERATION.value,
                "user_id": user_id,
                "course_id": course_id,
                "book_id": book_id,
                "topic": topic,
                "slide_count": slide_count,
                "generation_time": generation_time,
                "principles_applied": principles_applied or [],
                "cognitive_load_level": cognitive_load_level,
                "success": success,
                "error_message": error_message,
                "timestamp": datetime.utcnow().isoformat(),
                "cost_estimate": 0.0  # TODO: Calculate actual cost
            }

            # Store in memory cache
            self.recent_performances[performance_data["id"]] = performance_data

            # Log to structured logger
            logger.info(
                "Slide generation logged",
                extra={
                    "user_id": user_id,
                    "course_id": course_id,
                    "topic": topic,
                    "slide_count": slide_count,
                    "success": success,
                    "generation_time": generation_time,
                    "principles_applied": len(principles_applied or []),
                    "cognitive_load_level": cognitive_load_level
                }
            )

        except Exception as e:
            logger.error(f"Failed to log slide generation: {e}")

    async def get_slide_generation_stats(
        self,
        user_id: Optional[str] = None,
        course_id: Optional[str] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get slide generation statistics and analytics.

        Args:
            user_id: Optional user filter
            course_id: Optional course filter
            days: Number of days to look back

        Returns:
            Dictionary with comprehensive slide generation statistics
        """
        try:
            # Filter performances for slide generation
            slide_performances = [
                perf for perf in self.recent_performances.values()
                if perf.get("prompt_type") == PromptType.SLIDE_GENERATION.value
            ]

            # Apply filters
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            filtered_performances = []

            for perf in slide_performances:
                perf_date = datetime.fromisoformat(perf.get("timestamp", "").replace('Z', '+00:00'))

                # Time filter
                if perf_date < cutoff_date:
                    continue

                # User filter
                if user_id and perf.get("user_id") != user_id:
                    continue

                # Course filter
                if course_id and perf.get("course_id") != course_id:
                    continue

                filtered_performances.append(perf)

            # Calculate statistics
            total_generations = len(filtered_performances)
            successful_generations = sum(1 for p in filtered_performances if p.get("success", False))
            success_rate = successful_generations / total_generations if total_generations > 0 else 0

            # Time statistics
            generation_times = [p.get("generation_time", 0) for p in filtered_performances if p.get("success", False)]
            avg_generation_time = statistics.mean(generation_times) if generation_times else 0
            median_generation_time = statistics.median(generation_times) if generation_times else 0

            # Slide statistics
            total_slides = sum(p.get("slide_count", 0) for p in filtered_performances if p.get("success", False))
            avg_slides_per_generation = total_slides / successful_generations if successful_generations > 0 else 0

            # Principles application statistics
            all_principles = []
            for p in filtered_performances:
                all_principles.extend(p.get("principles_applied", []))

            principle_counts = {}
            for principle in all_principles:
                principle_counts[principle] = principle_counts.get(principle, 0) + 1

            # Cognitive load distribution
            cognitive_load_counts = {}
            for p in filtered_performances:
                load = p.get("cognitive_load_level", "moderate")
                cognitive_load_counts[load] = cognitive_load_counts.get(load, 0) + 1

            # Error analysis
            error_performances = [p for p in filtered_performances if not p.get("success", False)]
            error_types = {}
            for p in error_performances:
                error_msg = p.get("error_message", "Unknown error")
                error_type = "Generation Error" if "generation" in error_msg.lower() else "Other Error"
                error_types[error_type] = error_types.get(error_type, 0) + 1

            # Recent trends (last 7 days vs previous 7 days)
            recent_cutoff = datetime.utcnow() - timedelta(days=7)
            previous_cutoff = datetime.utcnow() - timedelta(days=14)

            recent_performances = [p for p in filtered_performances
                                 if datetime.fromisoformat(p.get("timestamp", "").replace('Z', '+00:00')) >= recent_cutoff]
            previous_performances = [p for p in filtered_performances
                                   if previous_cutoff <= datetime.fromisoformat(p.get("timestamp", "").replace('Z', '+00:00')) < recent_cutoff]

            recent_success_rate = sum(1 for p in recent_performances if p.get("success", False)) / len(recent_performances) if recent_performances else 0
            previous_success_rate = sum(1 for p in previous_performances if p.get("success", False)) / len(previous_performances) if previous_performances else 0
            success_rate_trend = recent_success_rate - previous_success_rate

            return {
                "summary": {
                    "total_generations": total_generations,
                    "successful_generations": successful_generations,
                    "success_rate": round(success_rate, 4),
                    "success_rate_trend": round(success_rate_trend, 4),
                    "period_days": days
                },
                "performance": {
                    "avg_generation_time_seconds": round(avg_generation_time, 2),
                    "median_generation_time_seconds": round(median_generation_time, 2),
                    "total_slides_generated": total_slides,
                    "avg_slides_per_generation": round(avg_slides_per_generation, 1)
                },
                "principles": {
                    "total_applications": len(all_principles),
                    "most_used_principles": sorted(principle_counts.items(), key=lambda x: x[1], reverse=True)[:5],
                    "principle_distribution": principle_counts
                },
                "cognitive_load": {
                    "distribution": cognitive_load_counts,
                    "most_common_level": max(cognitive_load_counts.items(), key=lambda x: x[1])[0] if cognitive_load_counts else "moderate"
                },
                "errors": {
                    "total_errors": len(error_performances),
                    "error_rate": round(len(error_performances) / total_generations, 4) if total_generations > 0 else 0,
                    "error_types": error_types
                },
                "usage_patterns": {
                    "avg_generations_per_day": round(total_generations / days, 1),
                    "peak_usage_day": None,  # TODO: Calculate daily distribution
                    "user_engagement": len(set(p.get("user_id") for p in filtered_performances))
                },
                "generated_at": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to get slide generation stats: {e}")
            return {
                "error": str(e),
                "generated_at": datetime.utcnow().isoformat()
            }

    async def log_active_recall_session(
        self,
        user_id: str,
        course_id: str,
        concept_id: Optional[str] = None,
        session_type: str = "review",
        question_count: int = 0,
        estimated_duration: int = 0,
        average_difficulty: float = 0.5,
        forgetting_curve_optimization: bool = False,
        success: bool = True,
        error_message: Optional[str] = None,
        question_type: Optional[str] = None,
        is_correct: Optional[bool] = None,
        response_time: Optional[int] = None,
        confidence_rating: Optional[str] = None,
        learning_gained: Optional[float] = None,
        curve_model: Optional[str] = None,
        next_review_interval: Optional[int] = None
    ) -> None:
        """
        Log active recall session analytics data.

        Args:
            user_id: User identifier
            course_id: Course identifier
            concept_id: Optional concept identifier
            session_type: Type of session (review, assessment, practice)
            question_count: Number of questions in session
            estimated_duration: Estimated session duration in seconds
            average_difficulty: Average difficulty level (0-1)
            forgetting_curve_optimization: Whether forgetting curve optimization was used
            success: Whether session was successful
            error_message: Error message if session failed
            question_type: Specific question type (for individual questions)
            is_correct: Whether answer was correct (for individual questions)
            response_time: Response time in milliseconds (for individual questions)
            confidence_rating: User's confidence rating (for individual questions)
            learning_gained: Estimated learning gain (for individual questions)
            curve_model: Forgetting curve model used (for individual questions)
            next_review_interval: Next review interval in days (for individual questions)
        """
        try:
            performance_data = {
                "id": str(uuid.uuid4()),
                "prompt_type": "active_recall_session" if question_type is None else "active_recall_question",
                "user_id": user_id,
                "course_id": course_id,
                "concept_id": concept_id,
                "session_type": session_type,
                "question_count": question_count,
                "estimated_duration": estimated_duration,
                "average_difficulty": average_difficulty,
                "forgetting_curve_optimization": forgetting_curve_optimization,
                "success": success,
                "error_message": error_message,
                "question_type": question_type,
                "is_correct": is_correct,
                "response_time_ms": response_time,
                "confidence_rating": confidence_rating,
                "learning_gained": learning_gained,
                "curve_model": curve_model,
                "next_review_interval": next_review_interval,
                "timestamp": datetime.utcnow().isoformat(),
                "cost_estimate": 0.0  # TODO: Calculate actual cost
            }

            # Store in memory cache
            self.recent_performances[performance_data["id"]] = performance_data

            # Log to structured logger
            logger.info(
                "Active recall session logged",
                extra={
                    "user_id": user_id,
                    "course_id": course_id,
                    "session_type": session_type,
                    "question_count": question_count,
                    "success": success,
                    "forgetting_curve_optimization": forgetting_curve_optimization,
                    "average_difficulty": average_difficulty
                }
            )

        except Exception as e:
            logger.error(f"Failed to log active recall session: {e}")

    async def get_active_recall_analytics(
        self,
        user_id: Optional[str] = None,
        course_id: Optional[str] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get comprehensive active recall analytics and statistics.

        Args:
            user_id: Optional user filter
            course_id: Optional course filter
            days: Number of days to look back

        Returns:
            Dictionary with comprehensive active recall analytics
        """
        try:
            # Filter performances for active recall
            recall_performances = [
                perf for perf in self.recent_performances.values()
                if perf.get("prompt_type") in ["active_recall_session", "active_recall_question"]
            ]

            # Apply filters
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            filtered_performances = []

            for perf in recall_performances:
                perf_date = datetime.fromisoformat(perf.get("timestamp", "").replace('Z', '+00:00'))

                # Time filter
                if perf_date < cutoff_date:
                    continue

                # User filter
                if user_id and perf.get("user_id") != user_id:
                    continue

                # Course filter
                if course_id and perf.get("course_id") != course_id:
                    continue

                filtered_performances.append(perf)

            # Separate sessions and individual questions
            sessions = [p for p in filtered_performances if p.get("prompt_type") == "active_recall_session"]
            questions = [p for p in filtered_performances if p.get("prompt_type") == "active_recall_question"]

            # Session statistics
            total_sessions = len(sessions)
            successful_sessions = sum(1 for s in sessions if s.get("success", False))
            session_success_rate = successful_sessions / total_sessions if total_sessions > 0 else 0

            # Question performance statistics
            total_questions = len(questions)
            correct_answers = sum(1 for q in questions if q.get("is_correct", False))
            question_accuracy = correct_answers / total_questions if total_questions > 0 else 0

            # Response time statistics
            response_times = [q.get("response_time_ms", 0) for q in questions if q.get("response_time_ms")]
            avg_response_time = statistics.mean(response_times) if response_times else 0
            median_response_time = statistics.median(response_times) if response_times else 0

            # Confidence calibration statistics
            confidence_data = []
            for q in questions:
                confidence = q.get("confidence_rating")
                if confidence:
                    confidence_data.append({
                        "confidence": confidence,
                        "correct": q.get("is_correct", False)
                    })

            calibration_accuracy = 0.0
            if confidence_data:
                correct_confidences = sum(1 for d in confidence_data if d["confidence"] in ["high", "very_high"] and d["correct"])
                high_confidence_total = sum(1 for d in confidence_data if d["confidence"] in ["high", "very_high"])
                calibration_accuracy = correct_confidences / high_confidence_total if high_confidence_total > 0 else 0

            # Forgetting curve model usage
            curve_models = {}
            for q in questions:
                model = q.get("curve_model", "unknown")
                curve_models[model] = curve_models.get(model, 0) + 1

            # Learning gains analysis
            learning_gains = [q.get("learning_gained", 0) for q in questions if q.get("learning_gained") is not None]
            avg_learning_gain = statistics.mean(learning_gains) if learning_gains else 0

            # Session duration statistics
            session_durations = [s.get("estimated_duration", 0) for s in sessions if s.get("estimated_duration")]
            avg_session_duration = statistics.mean(session_durations) if session_durations else 0

            # Difficulty progression analysis
            difficulty_progression = []
            for s in sessions:
                difficulty = s.get("average_difficulty", 0.5)
                date = datetime.fromisoformat(s.get("timestamp", "").replace('Z', '+00:00'))
                difficulty_progression.append({"date": date, "difficulty": difficulty})

            # Recent trends (last 7 days vs previous 7 days)
            recent_cutoff = datetime.utcnow() - timedelta(days=7)
            previous_cutoff = datetime.utcnow() - timedelta(days=14)

            recent_questions = [q for q in questions
                              if datetime.fromisoformat(q.get("timestamp", "").replace('Z', '+00:00')) >= recent_cutoff]
            previous_questions = [q for q in questions
                                if previous_cutoff <= datetime.fromisoformat(q.get("timestamp", "").replace('Z', '+00:00')) < recent_cutoff]

            recent_accuracy = sum(1 for q in recent_questions if q.get("is_correct", False)) / len(recent_questions) if recent_questions else 0
            previous_accuracy = sum(1 for q in previous_questions if q.get("is_correct", False)) / len(previous_questions) if previous_questions else 0
            accuracy_trend = recent_accuracy - previous_accuracy

            return {
                "summary": {
                    "total_sessions": total_sessions,
                    "successful_sessions": successful_sessions,
                    "session_success_rate": round(session_success_rate, 4),
                    "total_questions_answered": total_questions,
                    "question_accuracy": round(question_accuracy, 4),
                    "accuracy_trend": round(accuracy_trend, 4),
                    "period_days": days
                },
                "performance": {
                    "avg_response_time_ms": round(avg_response_time, 0),
                    "median_response_time_ms": round(median_response_time, 0),
                    "avg_session_duration_minutes": round(avg_session_duration / 60, 1),
                    "avg_learning_gain": round(avg_learning_gain, 3),
                    "questions_per_session": round(total_questions / total_sessions, 1) if total_sessions > 0 else 0
                },
                "metacognitive": {
                    "confidence_calibration_accuracy": round(calibration_accuracy, 3),
                    "confidence_distribution": self._calculate_confidence_distribution(confidence_data),
                    "metacognitive_insights": self._generate_metacognitive_insights(confidence_data)
                },
                "forgetting_curve": {
                    "models_used": curve_models,
                    "optimization_enabled": sum(1 for s in sessions if s.get("forgetting_curve_optimization", False)),
                    "avg_review_interval_days": round(
                        statistics.mean([q.get("next_review_interval", 0) for q in questions if q.get("next_review_interval")]) or 0, 1
                    ),
                    "retention_predictions": self._generate_retention_predictions(difficulty_progression)
                },
                "learning_patterns": {
                    "difficulty_progression": difficulty_progression,
                    "session_type_distribution": self._calculate_session_type_distribution(sessions),
                    "question_type_distribution": self._calculate_question_type_distribution(questions),
                    "peak_performance_times": self._analyze_peak_performance_times(questions)
                },
                "recommendations": self._generate_active_recall_recommendations({
                    "accuracy": question_accuracy,
                    "calibration": calibration_accuracy,
                    "response_time": avg_response_time,
                    "learning_gain": avg_learning_gain,
                    "session_frequency": total_sessions / (days / 7)  # Sessions per week
                }),
                "generated_at": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to get active recall analytics: {e}")
            return {
                "error": str(e),
                "generated_at": datetime.utcnow().isoformat()
            }

    def _calculate_confidence_distribution(self, confidence_data: List[Dict]) -> Dict[str, int]:
        """Calculate distribution of confidence ratings."""
        distribution = {"very_low": 0, "low": 0, "medium": 0, "high": 0, "very_high": 0}

        for data in confidence_data:
            confidence = data.get("confidence", "medium")
            distribution[confidence] = distribution.get(confidence, 0) + 1

        return distribution

    def _generate_metacognitive_insights(self, confidence_data: List[Dict]) -> List[str]:
        """Generate metacognitive insights based on confidence data."""
        insights = []

        if not confidence_data:
            return ["Insufficient data for metacognitive analysis"]

        total = len(confidence_data)
        correct_high_confidence = sum(1 for d in confidence_data
                                    if d["confidence"] in ["high", "very_high"] and d["correct"])
        high_confidence_total = sum(1 for d in confidence_data if d["confidence"] in ["high", "very_high"])
        incorrect_low_confidence = sum(1 for d in confidence_data
                                     if d["confidence"] in ["very_low", "low"] and not d["correct"])
        low_confidence_total = sum(1 for d in confidence_data if d["confidence"] in ["very_low", "low"])

        # Calibration insights
        if high_confidence_total > 0:
            calibration_rate = correct_high_confidence / high_confidence_total
            if calibration_rate > 0.8:
                insights.append("Excellent confidence calibration - trust your knowledge")
            elif calibration_rate < 0.6:
                insights.append("Consider reviewing concepts when feeling confident")

        # Underconfidence insights
        if low_confidence_total > 0:
            underconfidence_rate = incorrect_low_confidence / low_confidence_total
            if underconfidence_rate < 0.3:
                insights.append("You may be underconfident - trust your knowledge more")

        # Overall confidence patterns
        avg_confidence = sum(1 for d in confidence_data if d["confidence"] in ["high", "very_high"]) / total
        if avg_confidence < 0.3:
            insights.append("Consider building confidence through practice")
        elif avg_confidence > 0.7:
            insights.append("Good confidence levels - maintain self-assessment awareness")

        return insights

    def _generate_retention_predictions(self, difficulty_progression: List[Dict]) -> Dict[str, Any]:
        """Generate retention predictions based on difficulty progression."""
        if len(difficulty_progression) < 2:
            return {"projection": "insufficient_data"}

        # Analyze difficulty trend
        recent_difficulties = [d["difficulty"] for d in difficulty_progression[-5:]]
        avg_recent_difficulty = statistics.mean(recent_difficulties)

        # Simple retention prediction based on difficulty
        if avg_recent_difficulty > 0.7:
            retention_prediction = "challenging_content - expect faster forgetting"
        elif avg_recent_difficulty < 0.4:
            retention_prediction = "mastery_level - expect good retention"
        else:
            retention_prediction = "moderate_difficulty - normal retention curve"

        return {
            "projection": retention_prediction,
            "avg_difficulty": round(avg_recent_difficulty, 2),
            "difficulty_trend": "improving" if len(recent_difficulties) > 1 and recent_difficulties[-1] > recent_difficulties[0] else "stable"
        }

    def _calculate_session_type_distribution(self, sessions: List[Dict]) -> Dict[str, int]:
        """Calculate distribution of session types."""
        distribution = {}

        for session in sessions:
            session_type = session.get("session_type", "review")
            distribution[session_type] = distribution.get(session_type, 0) + 1

        return distribution

    def _calculate_question_type_distribution(self, questions: List[Dict]) -> Dict[str, int]:
        """Calculate distribution of question types."""
        distribution = {}

        for question in questions:
            question_type = question.get("question_type", "unknown")
            distribution[question_type] = distribution.get(question_type, 0) + 1

        return distribution

    def _analyze_peak_performance_times(self, questions: List[Dict]) -> Dict[str, Any]:
        """Analyze peak performance times based on question data."""
        # This would analyze time-of-day performance patterns
        # Placeholder implementation
        return {
            "peak_hours": ["09:00-11:00", "14:00-16:00"],
            "low_performance_hours": ["13:00-14:00"],
            "analysis_note": "Time-based analysis requires more data"
        }

    def _generate_active_recall_recommendations(self, metrics: Dict[str, Any]) -> List[str]:
        """Generate personalized recommendations based on performance metrics."""
        recommendations = []

        accuracy = metrics.get("accuracy", 0)
        calibration = metrics.get("calibration", 0)
        response_time = metrics.get("response_time", 0)
        learning_gain = metrics.get("learning_gain", 0)
        session_frequency = metrics.get("session_frequency", 0)

        # Accuracy-based recommendations
        if accuracy < 0.6:
            recommendations.append("Focus on reviewing fundamentals to improve accuracy")
        elif accuracy > 0.9:
            recommendations.append("Consider increasing difficulty or advanced topics")

        # Calibration recommendations
        if calibration < 0.7:
            recommendations.append("Practice confidence calibration - pause to assess knowledge before answering")
        elif calibration > 0.9:
            recommendations.append("Excellent metacognitive awareness - maintain this level")

        # Response time recommendations
        if response_time > 60000:  # > 1 minute
            recommendations.append("Work on improving response speed through practice")
        elif response_time < 10000 and accuracy < 0.8:  # < 10 seconds but low accuracy
            recommendations.append("Slow down and think more carefully before answering")

        # Learning gain recommendations
        if learning_gain < 0.3:
            recommendations.append("Try different learning strategies or study methods")
        elif learning_gain > 0.7:
            recommendations.append("Excellent learning efficiency - continue current approach")

        # Session frequency recommendations
        if session_frequency < 2:
            recommendations.append("Consider increasing review frequency for better retention")
        elif session_frequency > 7:
            recommendations.append("Ensure adequate rest between sessions to avoid burnout")

        return recommendations

# Global instance
prompt_analytics_service = PromptAnalyticsService()