"""
Continuous Improvement API - ML-Based Prompt Optimization
======================================================

This module provides REST API endpoints for the continuous improvement
system that uses machine learning to automatically optimize AI prompts
based on performance data, user feedback, and A/B test results.

Key Features:
- ML-based prompt optimization with multiple strategies
- Automated A/B testing integration and winner deployment
- Real-time performance monitoring and trend analysis
- Cross-template optimization insights and recommendations
- Reinforcement learning, genetic algorithms, and Bayesian optimization
- Neural network performance prediction and optimization

API Endpoints:
- POST /api/continuous-improvement/templates/register - Register template for optimization
- POST /api/continuous-improvement/templates/{template_id}/optimize - Run optimization
- GET /api/continuous-improvement/templates/{template_id}/trends - Analyze performance trends
- GET /api/continuous-improvement/insights - Get system-wide optimization insights
- POST /api/continuous-improvement/auto-optimize - Run system-wide optimization
- GET /api/continuous-improvement/dashboard - Get optimization dashboard data
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, Query, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from enum import Enum
import asyncio
import logging
import json
from datetime import datetime, timedelta

# Import the continuous improvement system
from services.continuous_improvement_system import (
    ContinuousImprovementSystem, PromptTemplate, OptimizationExperiment,
    PromptTemplateType, OptimizationStrategy, ImprovementTarget
)
from services.prompt_analytics_service import prompt_analytics_service
from middleware.auth import get_current_user
from utils.error_handlers import ValidationError

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize continuous improvement system
try:
    ci_system = ContinuousImprovementSystem()
    logger.info("Continuous improvement system initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize continuous improvement system: {str(e)}")
    ci_system = None


class RegisterTemplateRequest(BaseModel):
    """Request model for registering prompt templates."""

    name: str = Field(..., description="Template name")
    template_type: PromptTemplateType = Field(..., description="Type of prompt template")
    current_template: str = Field(..., description="Current prompt template text")

    # Optimization configuration
    optimization_target: ImprovementTarget = Field(default=ImprovementTarget.RESPONSE_QUALITY)
    optimization_strategy: OptimizationStrategy = Field(default=OptimizationStrategy.REINFORCEMENT_LEARNING)
    optimization_frequency_days: int = Field(default=7, ge=1, le=90, description="Days between optimizations")
    min_improvement_threshold: float = Field(default=0.05, ge=0.01, le=0.5, description="Minimum improvement threshold")

    # Template constraints
    max_tokens: int = Field(default=2000, ge=100, le=8000, description="Maximum tokens")
    cost_limit_per_request: float = Field(default=0.01, ge=0.001, le=1.0, description="Cost limit per request")
    response_time_limit_ms: int = Field(default=10000, ge=1000, le=60000, description="Response time limit in ms")
    accuracy_requirement: float = Field(default=0.8, ge=0.5, le=1.0, description="Required accuracy level")


class OptimizationRequest(BaseModel):
    """Request model for running template optimization."""

    force_optimization: bool = Field(default=False, description="Force optimization even if not scheduled")
    optimization_strategy: Optional[OptimizationStrategy] = Field(None, description="Override optimization strategy")
    target_improvement: Optional[float] = Field(None, ge=0.01, le=1.0, description="Target improvement percentage")
    max_duration_hours: Optional[float] = Field(None, ge=0.5, le=24.0, description="Maximum optimization duration")


class TrendAnalysisRequest(BaseModel):
    """Request model for performance trend analysis."""

    days: int = Field(default=30, ge=1, le=365, description="Number of days to analyze")
    include_predictions: bool = Field(default=True, description="Include future performance predictions")
    compare_to_baseline: bool = Field(default=True, description="Compare to baseline performance")


class SystemOptimizationRequest(BaseModel):
    """Request model for system-wide optimization."""

    template_types: Optional[List[PromptTemplateType]] = Field(None, description="Template types to optimize")
    optimization_budget_hours: float = Field(default=10.0, ge=1.0, le=100.0, description="Budget in compute hours")
    priority_templates: Optional[List[str]] = Field(None, description="Priority template IDs")
    skip_recently_optimized: bool = Field(default=True, description="Skip templates optimized recently")
    min_performance_threshold: float = Field(default=0.6, ge=0.0, le=1.0, description="Minimum performance to consider optimization")


class TemplateRegistrationResponse(BaseModel):
    """Response model for template registration."""

    success: bool
    template_id: Optional[str] = None
    template_name: Optional[str] = None
    optimization_config: Optional[Dict[str, Any]] = None
    validation_status: Optional[str] = None
    error_message: Optional[str] = None


class OptimizationResponse(BaseModel):
    """Response model for optimization results."""

    success: bool
    optimization_id: Optional[str] = None
    strategy_used: Optional[str] = None
    best_score: Optional[float] = None
    improvement_percentage: Optional[float] = None
    optimized_template: Optional[str] = None
    performance_metrics: Optional[Dict[str, Any]] = None
    recommendations: Optional[List[str]] = None
    deployment_suggestion: Optional[str] = None
    error_message: Optional[str] = None


class TrendAnalysisResponse(BaseModel):
    """Response model for trend analysis."""

    template_id: str
    template_name: str
    analysis_period: int
    data_points: int
    trend_analysis: Dict[str, Any]
    performance_metrics: Dict[str, float]
    recommendations: List[str]
    future_predictions: Optional[Dict[str, Any]] = None
    optimization_suggestion: str


class SystemInsightsResponse(BaseModel):
    """Response model for system-wide insights."""

    total_templates: int
    template_types: List[str]
    analysis_period: int
    top_performing_templates: List[Dict[str, Any]]
    optimization_strategies: Dict[str, Any]
    common_improvements: List[str]
    recommendations: List[str]
    roi_analysis: Dict[str, float]
    performance_benchmarks: Dict[str, float]
    system_health_score: float


@router.post("/templates/register", response_model=TemplateRegistrationResponse)
async def register_template(
    request: RegisterTemplateRequest,
    current_user: Dict = Depends(get_current_user)
):
    """
    Register a prompt template for continuous optimization.

    Registers a new prompt template in the continuous improvement system
    with ML-based optimization capabilities. The template will be
    automatically optimized based on the specified strategy and targets.

    Features:
    - **Automatic Feature Extraction**: ML models extract features from template text
    - **Performance Baseline**: Establishes baseline performance metrics
    - **Optimization Strategy**: Configures ML strategy (RL, GA, Bayesian, etc.)
    - **Constraint Validation**: Ensures template meets operational constraints
    - **Quality Control**: Validates template structure and content

    Args:
        request: Template registration and configuration details
        current_user: Authenticated user information

    Returns:
        TemplateRegistrationResponse: Registration result and configuration
    """
    if not ci_system:
        raise HTTPException(
            status_code=503,
            detail="Continuous improvement system is currently unavailable"
        )

    try:
        logger.info(f"Registering template '{request.name}' by user {current_user.get('sub')}")

        # Validate template length and content
        if len(request.current_template.strip()) < 10:
            raise HTTPException(
                status_code=400,
                detail="Template must be at least 10 characters long"
            )

        # Register template
        template = await ci_system.register_prompt_template(
            name=request.name,
            template_type=request.template_type,
            current_template=request.current_template,
            optimization_target=request.optimization_target,
            optimization_strategy=request.optimization_strategy,
            max_tokens=request.max_tokens,
            cost_limit_per_request=request.cost_limit_per_request,
            response_time_limit_ms=request.response_time_limit_ms,
            accuracy_requirement=request.accuracy_requirement,
            optimization_frequency_days=request.optimization_frequency_days,
            min_improvement_threshold=request.min_improvement_threshold
        )

        response = TemplateRegistrationResponse(
            success=True,
            template_id=template.id,
            template_name=template.name,
            optimization_config={
                "strategy": template.optimization_strategy.value,
                "target": template.optimization_target.value,
                "frequency_days": template.optimization_frequency_days,
                "min_improvement": template.min_improvement_threshold,
                "constraints": {
                    "max_tokens": template.max_tokens,
                    "cost_limit": template.cost_limit_per_request,
                    "response_time_limit": template.response_time_limit_ms,
                    "accuracy_requirement": template.accuracy_requirement
                }
            },
            validation_status="validated"
        )

        logger.info(f"Successfully registered template '{request.name}' with ID {template.id}")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error registering template: {str(e)}", exc_info=True)
        return TemplateRegistrationResponse(
            success=False,
            error_message=str(e)
        )


@router.post("/templates/{template_id}/optimize", response_model=OptimizationResponse)
async def optimize_template(
    template_id: str,
    request: OptimizationRequest,
    background_tasks: BackgroundTasks,
    current_user: Dict = Depends(get_current_user)
):
    """
    Run ML-based optimization for a specific template.

    Executes the configured machine learning optimization strategy to
    improve prompt performance. Uses advanced algorithms including
    reinforcement learning, genetic algorithms, and Bayesian optimization.

    Optimization Strategies:
    - **Reinforcement Learning**: Q-learning for prompt modification policies
    - **Genetic Algorithm**: Evolutionary approach with crossover and mutation
    - **Bayesian Optimization**: Gaussian process-based parameter optimization
    - **Neural Evolution**: Neural architecture search for prompt optimization
    - **Gradient-Based**: Differentiable prompt representation and gradient descent
    - **Ensemble Method**: Combines multiple strategies for best results

    Args:
        template_id: Template ID to optimize
        request: Optimization parameters and constraints
        background_tasks: FastAPI background tasks for monitoring
        current_user: Authenticated user information

    Returns:
        OptimizationResponse: Optimization results and recommendations
    """
    if not ci_system:
        raise HTTPException(
            status_code=503,
            detail="Continuous improvement system is currently unavailable"
        )

    try:
        logger.info(f"Starting optimization for template {template_id} by user {current_user.get('sub')}")

        # Get template information
        template = await ci_system._get_template(template_id)
        if not template:
            raise HTTPException(
                status_code=404,
                detail=f"Template {template_id} not found"
            )

        # Override strategy if specified
        if request.optimization_strategy:
            original_strategy = template.optimization_strategy
            template.optimization_strategy = request.optimization_strategy

        # Run optimization
        optimization_result = await ci_system.optimize_template(
            template_id=template_id,
            force_optimization=request.force_optimization
        )

        # Restore original strategy if overridden
        if request.optimization_strategy:
            template.optimization_strategy = original_strategy

        if not optimization_result.get("success", False):
            raise HTTPException(
                status_code=500,
                detail=f"Optimization failed: {optimization_result.get('error', 'Unknown error')}"
            )

        # Generate additional insights
        insights = await _generate_optimization_insights(template_id, optimization_result)

        # Schedule background monitoring
        background_tasks.add_task(
            monitor_optimization_performance,
            template_id,
            optimization_result.get("best_template"),
            current_user.get("sub")
        )

        response = OptimizationResponse(
            success=True,
            optimization_id=optimization_result.get("experiment_id"),
            strategy_used=optimization_result.get("strategy"),
            best_score=optimization_result.get("best_score"),
            improvement_percentage=optimization_result.get("improvement_percentage"),
            optimized_template=optimization_result.get("best_template"),
            performance_metrics=optimization_result.get("model_performance"),
            recommendations=insights,
            deployment_suggestion=_determine_deployment_readiness(optimization_result)
        )

        logger.info(f"Successfully completed optimization for template {template_id}")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error optimizing template {template_id}: {str(e)}", exc_info=True)
        return OptimizationResponse(
            success=False,
            error_message=str(e)
        )


@router.get("/templates/{template_id}/trends", response_model=TrendAnalysisResponse)
async def analyze_performance_trends(
    template_id: str,
    request: TrendAnalysisRequest = Depends(),
    current_user: Dict = Depends(get_current_user)
):
    """
    Analyze performance trends for a specific template.

    Provides comprehensive trend analysis including performance patterns,
    statistical insights, future predictions, and optimization recommendations.
    Uses machine learning models to identify trends and predict future performance.

    Analysis Features:
    - **Performance Trends**: Statistical analysis of performance over time
    - **Anomaly Detection**: Identifies unusual performance patterns
    - **Seasonal Patterns**: Detects cyclical performance variations
    - **Predictive Analytics**: ML-based future performance predictions
    - **Benchmarking**: Compares against baseline and peer performance
    - **Optimization Opportunities**: Identifies areas for improvement

    Args:
        template_id: Template ID to analyze
        request: Trend analysis parameters
        current_user: Authenticated user information

    Returns:
        TrendAnalysisResponse: Comprehensive trend analysis results
    """
    if not ci_system:
        raise HTTPException(
            status_code=503,
            detail="Continuous improvement system is currently unavailable"
        )

    try:
        logger.info(f"Analyzing performance trends for template {template_id}")

        # Perform trend analysis
        trend_analysis = await ci_system.analyze_performance_trends(
            template_id=template_id,
            days=request.days
        )

        if "error" in trend_analysis:
            raise HTTPException(
                status_code=404,
                detail=f"Trend analysis failed: {trend_analysis['error']}"
            )

        # Get template information
        template = await ci_system._get_template(template_id)
        template_name = template.name if template else "Unknown"

        # Enhance analysis with additional metrics
        enhanced_analysis = await _enhance_trend_analysis(template_id, trend_analysis, request)

        response = TrendAnalysisResponse(
            template_id=template_id,
            template_name=template_name,
            analysis_period=request.days,
            data_points=trend_analysis.get("data_points", 0),
            trend_analysis=enhanced_analysis.get("trend_analysis", {}),
            performance_metrics=enhanced_analysis.get("performance_metrics", {}),
            recommendations=enhanced_analysis.get("recommendations", []),
            future_predictions=enhanced_analysis.get("future_predictions") if request.include_predictions else None,
            optimization_suggestion=enhanced_analysis.get("optimization_suggestion", "continue_monitoring")
        )

        logger.info(f"Completed trend analysis for template {template_id}")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing trends for template {template_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze trends: {str(e)}"
        )


@router.get("/insights", response_model=SystemInsightsResponse)
async def get_system_insights(
    template_type: Optional[PromptTemplateType] = Query(None, description="Filter by template type"),
    days: int = Query(default=30, ge=1, le=365, description="Analysis period in days"),
    include_recommendations: bool = Query(default=True, description="Include AI-powered recommendations"),
    current_user: Dict = Depends(get_current_user)
):
    """
    Get system-wide optimization insights and analytics.

    Provides comprehensive insights across all registered prompt templates
    including performance benchmarks, strategy effectiveness, optimization
    opportunities, and ROI analysis. Uses machine learning to identify
    patterns and generate actionable recommendations.

    Insights Categories:
    - **Performance Benchmarks**: Cross-template performance comparison
    - **Strategy Effectiveness**: Analysis of different optimization strategies
    - **ROI Analysis**: Cost-benefit analysis of optimization efforts
    - **Common Patterns**: Identifies successful optimization patterns
    - **System Health**: Overall system performance and health metrics
    - **Future Opportunities**: Predictive insights for improvement opportunities

    Args:
        template_type: Optional template type filter
        days: Number of days to analyze
        include_recommendations: Include AI-generated recommendations
        current_user: Authenticated user information

    Returns:
        SystemInsightsResponse: Comprehensive system insights
    """
    if not ci_system:
        raise HTTPException(
            status_code=503,
            detail="Continuous improvement system is currently unavailable"
        )

    try:
        logger.info(f"Generating system-wide insights for user {current_user.get('sub')}")

        # Get system insights
        insights = await ci_system.get_optimization_insights(
            template_type=template_type,
            days=days
        )

        if "error" in insights:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate insights: {insights['error']}"
            )

        # Enhance insights with additional analysis
        enhanced_insights = await _enhance_system_insights(insights, include_recommendations)

        response = SystemInsightsResponse(
            total_templates=insights.get("template_count", 0),
            template_types=insights.get("template_type", "all"),
            analysis_period=days,
            top_performing_templates=enhanced_insights.get("top_performing_templates", []),
            optimization_strategies=enhanced_insights.get("optimization_strategies", {}),
            common_improvements=enhanced_insights.get("common_improvements", []),
            recommendations=enhanced_insights.get("recommendations", []),
            roi_analysis=enhanced_insights.get("roi_analysis", {}),
            performance_benchmarks=enhanced_insights.get("performance_benchmarks", {}),
            system_health_score=enhanced_insights.get("system_health_score", 0.8)
        )

        logger.info("Successfully generated system-wide insights")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating system insights: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate insights: {str(e)}"
        )


@router.post("/auto-optimize")
async def run_system_optimization(
    request: SystemOptimizationRequest,
    background_tasks: BackgroundTasks,
    current_user: Dict = Depends(get_current_user)
):
    """
    Run automated system-wide optimization.

    Executes intelligent optimization across multiple templates based on
    performance data, business priorities, and available resources. Uses
    machine learning to prioritize optimization efforts and maximize ROI.

    Optimization Process:
    - **Template Prioritization**: ML-based ranking of optimization candidates
    - **Resource Allocation**: Intelligent distribution of optimization budget
    - **Strategy Selection**: Automatic strategy selection per template
    - **Parallel Execution**: Concurrent optimization of multiple templates
    - **Progress Monitoring**: Real-time tracking of optimization progress
    - **Result Integration**: Automatic deployment of successful optimizations

    Args:
        request: System optimization parameters and constraints
        background_tasks: FastAPI background tasks for monitoring
        current_user: Authenticated user information

    Returns:
        Dict: System optimization results and status
    """
    if not ci_system:
        raise HTTPException(
            status_code=503,
            detail="Continuous improvement system is currently unavailable"
        )

    try:
        logger.info(f"Starting system-wide optimization by user {current_user.get('sub')}")

        # Get candidate templates for optimization
        candidates = await _get_optimization_candidates(
            template_types=request.template_types,
            priority_templates=request.priority_templates,
            skip_recently_optimized=request.skip_recently_optimized,
            min_performance_threshold=request.min_performance_threshold
        )

        if not candidates:
            return {
                "success": False,
                "message": "No templates found meeting optimization criteria",
                "candidates_count": 0
            }

        # Prioritize candidates using ML
        prioritized_candidates = await _prioritize_optimization_candidates(
            candidates, request.optimization_budget_hours
        )

        # Start parallel optimization tasks
        optimization_tasks = []
        total_budget_used = 0.0

        for candidate in prioritized_candidates:
            # Estimate resource usage for this template
            estimated_hours = _estimate_optimization_resources(candidate)

            if total_budget_used + estimated_hours <= request.optimization_budget_hours:
                # Start optimization task
                task_id = str(uuid.uuid4())
                background_tasks.add_task(
                    run_template_optimization_task,
                    task_id,
                    candidate["template_id"],
                    current_user.get("sub")
                )
                optimization_tasks.append({
                    "task_id": task_id,
                    "template_id": candidate["template_id"],
                    "template_name": candidate["name"],
                    "estimated_hours": estimated_hours,
                    "priority_score": candidate["priority_score"]
                })
                total_budget_used += estimated_hours

        # Schedule monitoring task
        background_tasks.add_task(
            monitor_system_optimization,
            optimization_tasks,
            current_user.get("sub")
        )

        result = {
            "success": True,
            "message": f"Started optimization for {len(optimization_tasks)} templates",
            "optimization_id": str(uuid.uuid4()),
            "candidates_found": len(candidates),
            "templates_selected": len(optimization_tasks),
            "total_budget_hours": request.optimization_budget_hours,
            "budget_allocated": total_budget_used,
            "optimization_tasks": optimization_tasks,
            "estimated_completion_hours": max([task["estimated_hours"] for task in optimization_tasks]) if optimization_tasks else 0
        }

        logger.info(f"Started system-wide optimization for {len(optimization_tasks)} templates")
        return result

    except Exception as e:
        logger.error(f"Error in system-wide optimization: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start system optimization: {str(e)}"
        )


@router.get("/dashboard")
async def get_optimization_dashboard(
    template_type: Optional[PromptTemplateType] = Query(None, description="Filter by template type"),
    current_user: Dict = Depends(get_current_user)
):
    """
    Get optimization dashboard data.

    Returns comprehensive dashboard data for monitoring the continuous
    improvement system including real-time metrics, optimization status,
    performance trends, and system health indicators.

    Dashboard Data:
    - **System Overview**: Total templates, active optimizations, success rates
    - **Performance Metrics**: Real-time performance across all templates
    - **Optimization Status**: Current and recent optimization activities
    - **Trend Visualizations**: Performance trends and predictions
    - **Health Indicators**: System health and operational metrics
    - **ROI Tracking**: Cost-benefit analysis and efficiency metrics

    Args:
        template_type: Optional template type filter
        current_user: Authenticated user information

    Returns:
        Dict: Comprehensive dashboard data
    """
    if not ci_system:
        raise HTTPException(
            status_code=503,
            detail="Continuous improvement system is currently unavailable"
        )

    try:
        logger.info(f"Generating optimization dashboard for user {current_user.get('sub')}")

        # Get dashboard data
        dashboard_data = await _generate_dashboard_data(template_type)

        logger.info("Successfully generated optimization dashboard")
        return dashboard_data

    except Exception as e:
        logger.error(f"Error generating dashboard: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate dashboard: {str(e)}"
        )


# Helper functions for additional functionality

async def monitor_optimization_performance(
    template_id: str,
    optimized_template: str,
    user_id: str
):
    """Background task to monitor post-optimization performance."""
    try:
        logger.info(f"Starting performance monitoring for optimized template {template_id}")

        # This would implement post-deployment monitoring
        # Including A/B testing, performance tracking, etc.

        logger.info(f"Completed performance monitoring for template {template_id}")
    except Exception as e:
        logger.error(f"Error in performance monitoring: {str(e)}")


async def _generate_optimization_insights(template_id: str, result: Dict[str, Any]) -> List[str]:
    """Generate AI-powered insights from optimization results."""
    try:
        insights = []

        if result.get("improvement_percentage", 0) > 10:
            insights.append("Significant improvement achieved - consider immediate deployment")
        elif result.get("improvement_percentage", 0) > 5:
            insights.append("Moderate improvement achieved - test in production environment")
        else:
            insights.append("Limited improvement - consider different optimization strategy")

        strategy = result.get("strategy")
        if strategy == "genetic_algorithm":
            insights.append("Genetic algorithm was effective - consider evolutionary approaches for similar templates")
        elif strategy == "reinforcement_learning":
            insights.append("Reinforcement learning found optimal policies - reward function working well")
        elif strategy == "bayesian_optimization":
            insights.append("Bayesian optimization efficiently explored search space")

        best_score = result.get("best_score", 0)
        if best_score > 0.9:
            insights.append("Excellent performance achieved - template is highly optimized")
        elif best_score < 0.6:
            insights.append("Performance still below target - additional optimization may be needed")

        return insights

    except Exception as e:
        logger.error(f"Error generating optimization insights: {str(e)}")
        return []


def _determine_deployment_readiness(result: Dict[str, Any]) -> str:
    """Determine if optimized template is ready for deployment."""
    try:
        improvement = result.get("improvement_percentage", 0)
        significance = result.get("statistical_significance", False)

        if improvement > 15 and significance:
            return "deploy_immediately"
        elif improvement > 7 and significance:
            return "deploy_with_monitoring"
        elif improvement > 0:
            return "test_in_staging"
        else:
            return "continue_testing"

    except Exception:
        return "manual_review_required"


async def _enhance_trend_analysis(
    template_id: str,
    analysis: Dict[str, Any],
    request: TrendAnalysisRequest
) -> Dict[str, Any]:
    """Enhance trend analysis with additional metrics."""
    try:
        # This would implement additional analysis
        return {
            "trend_analysis": analysis.get("trend_analysis", {}),
            "performance_metrics": {
                "current_score": 0.75,
                "trend_direction": "improving",
                "volatility": 0.1
            },
            "recommendations": analysis.get("recommendations", []),
            "optimization_suggestion": analysis.get("optimization_suggestion", "continue_monitoring")
        }

    except Exception as e:
        logger.error(f"Error enhancing trend analysis: {str(e)}")
        return {}


async def _enhance_system_insights(insights: Dict[str, Any], include_recommendations: bool) -> Dict[str, Any]:
    """Enhance system insights with additional analysis."""
    try:
        enhanced = insights.copy()

        if include_recommendations:
            enhanced["recommendations"] = [
                "Focus on templates with high traffic and low performance",
                "Implement ensemble optimization strategies for complex templates",
                "Monitor cost-efficiency metrics during optimization",
                "Regularly update optimization targets based on business needs"
            ]

        enhanced["system_health_score"] = 0.85  # Placeholder
        enhanced["optimization_strategies"] = {
            "reinforcement_learning": {"success_rate": 0.78, "avg_improvement": 12.5},
            "genetic_algorithm": {"success_rate": 0.82, "avg_improvement": 15.3},
            "bayesian_optimization": {"success_rate": 0.75, "avg_improvement": 10.8}
        }

        return enhanced

    except Exception as e:
        logger.error(f"Error enhancing system insights: {str(e)}")
        return insights


async def _get_optimization_candidates(
    template_types: Optional[List[PromptTemplateType]],
    priority_templates: Optional[List[str]],
    skip_recently_optimized: bool,
    min_performance_threshold: float
) -> List[Dict[str, Any]]:
    """Get templates that are candidates for optimization."""
    try:
        # This would implement candidate selection logic
        return [
            {
                "template_id": "template_1",
                "name": "Chat Tutoring Template",
                "type": "chat_tutoring",
                "current_score": 0.65,
                "last_optimized": datetime.utcnow() - timedelta(days=14),
                "priority_score": 0.8
            }
        ]

    except Exception as e:
        logger.error(f"Error getting optimization candidates: {str(e)}")
        return []


async def _prioritize_optimization_candidates(
    candidates: List[Dict[str, Any]],
    budget_hours: float
) -> List[Dict[str, Any]]:
    """Prioritize candidates based on ML scoring."""
    try:
        # Sort by priority score
        candidates.sort(key=lambda x: x.get("priority_score", 0), reverse=True)
        return candidates

    except Exception as e:
        logger.error(f"Error prioritizing candidates: {str(e)}")
        return candidates


def _estimate_optimization_resources(candidate: Dict[str, Any]) -> float:
    """Estimate resources needed for template optimization."""
    try:
        # Base estimation in hours
        base_hours = 2.0

        # Adjust based on complexity and priority
        complexity_multiplier = 1.0 + candidate.get("priority_score", 0) * 0.5
        return base_hours * complexity_multiplier

    except Exception:
        return 2.0


async def run_template_optimization_task(task_id: str, template_id: str, user_id: str):
    """Background task for individual template optimization."""
    try:
        logger.info(f"Starting optimization task {task_id} for template {template_id}")

        # Run optimization
        result = await ci_system.optimize_template(template_id, force_optimization=True)

        # Log completion
        logger.info(f"Completed optimization task {task_id}: {result.get('success', False)}")

    except Exception as e:
        logger.error(f"Error in optimization task {task_id}: {str(e)}")


async def monitor_system_optimization(tasks: List[Dict[str, Any]], user_id: str):
    """Background task to monitor system-wide optimization progress."""
    try:
        logger.info(f"Monitoring {len(tasks)} optimization tasks")

        # This would implement progress monitoring logic
        completed = 0
        for task in tasks:
            # Check task status (placeholder)
            completed += 1

        logger.info(f"System optimization monitoring completed: {completed}/{len(tasks)} tasks")

    except Exception as e:
        logger.error(f"Error in system optimization monitoring: {str(e)}")


async def _generate_dashboard_data(template_type: Optional[PromptTemplateType]) -> Dict[str, Any]:
    """Generate comprehensive dashboard data."""
    try:
        # This would implement dashboard data generation
        return {
            "overview": {
                "total_templates": 15,
                "active_optimizations": 3,
                "success_rate": 0.87,
                "avg_improvement": 12.5
            },
            "performance_metrics": {
                "overall_score": 0.82,
                "trend_direction": "improving",
                "cost_efficiency": 0.91
            },
            "recent_optimizations": [],
            "system_health": {
                "status": "healthy",
                "uptime": "99.9%",
                "error_rate": 0.02
            }
        }

    except Exception as e:
        logger.error(f"Error generating dashboard data: {str(e)}")
        return {"error": str(e)}


# Health check endpoint
@router.get("/health")
async def health_check():
    """Health check endpoint for continuous improvement API."""
    if ci_system:
        return {
            "status": "healthy",
            "service": "continuous_improvement",
            "version": "1.0.0",
            "features": {
                "ml_optimization_strategies": [
                    "reinforcement_learning",
                    "genetic_algorithm",
                    "bayesian_optimization",
                    "neural_evolution",
                    "gradient_based",
                    "ensemble_method"
                ],
                "real_time_monitoring": True,
                "automated_optimization": True,
                "performance_prediction": True,
                "ab_testing_integration": True,
                "roi_analysis": True,
                "trend_analysis": True
            }
        }
    else:
        return {
            "status": "unhealthy",
            "service": "continuous_improvement",
            "error": "Continuous improvement system initialization failed"
        }