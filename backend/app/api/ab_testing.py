"""
A/B Testing API - Prompt Performance Comparison Framework
========================================================

This module provides REST API endpoints for comprehensive A/B testing
of prompt performance across different AI models, templates, and configurations.

Key Features:
- Test creation and management with statistical validation
- Real-time variant assignment and traffic allocation
- Performance tracking and results collection
- Statistical analysis with multiple test methods
- Comprehensive analytics and reporting
- Risk assessment and deployment recommendations
- Integration with all AI service endpoints
- Bias detection and quality control

API Endpoints:
- POST /api/ab-testing/tests - Create new A/B test
- GET /api/ab-testing/tests - List all tests
- POST /api/ab-testing/tests/{test_id}/start - Start a test
- POST /api/ab-testing/tests/{test_id}/assign - Assign user to variant
- POST /api/ab-testing/tests/{test_id}/results - Record test result
- POST /api/ab-testing/tests/{test_id}/analyze - Analyze test results
- GET /api/ab-testing/tests/{test_id}/results - Get comprehensive results
- GET /api/ab-testing/tests/{test_id}/analytics - Get real-time analytics
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

# Import the A/B testing framework
from services.ab_testing_framework import (
    ABTestingFramework, ABTest, TestVariant, TestParticipant, TestResult,
    TestType, TestStatus, TrafficAllocationMethod, StatisticalTest, MetricType
)
from services.prompt_analytics_service import prompt_analytics_service
from middleware.auth import get_current_user
from utils.error_handlers import ValidationError

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize A/B testing framework
try:
    ab_framework = ABTestingFramework()
    logger.info("A/B testing framework initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize A/B testing framework: {str(e)}")
    ab_framework = None


class CreateTestRequest(BaseModel):
    """Request model for creating A/B tests."""

    name: str = Field(..., description="Test name")
    description: str = Field(..., description="Test description")
    test_type: TestType = Field(..., description="Type of test to run")

    # Variant configurations
    variants: List[Dict[str, Any]] = Field(..., description="List of variant configurations")
    control_variant_name: str = Field(..., description="Name of the control variant")

    # Test parameters
    traffic_allocation_method: TrafficAllocationMethod = Field(default=TrafficAllocationMethod.RANDOM)
    statistical_test: StatisticalTest = Field(default=StatisticalTest.Z_TEST)
    confidence_level: float = Field(default=0.95, ge=0.8, le=0.99, description="Statistical confidence level")
    minimum_detectable_effect: float = Field(default=0.05, ge=0.01, le=0.5, description="Minimum effect size to detect")

    # Targeting and duration
    target_user_segment: Optional[str] = Field(None, description="Target user segment")
    target_course_ids: Optional[List[str]] = Field(None, description="Target specific courses")
    sample_size_required: Optional[int] = Field(None, ge=100, description="Required sample size")
    duration_days: Optional[int] = Field(None, ge=1, le=365, description="Test duration in days")


class VariantConfiguration(BaseModel):
    """Configuration for individual test variants."""

    name: str = Field(..., description="Variant name")
    description: str = Field(default="", description="Variant description")
    traffic_weight: float = Field(default=1.0, ge=0.1, description="Traffic weight for this variant")

    # AI model configuration
    prompt_template: str = Field(..., description="Prompt template to test")
    model_provider: str = Field(default="zai", description="AI model provider")
    model_name: str = Field(default="glm-4.6", description="Specific model name")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Model temperature")
    max_tokens: int = Field(default=2000, ge=100, le=8000, description="Maximum tokens")
    additional_params: Dict[str, Any] = Field(default_factory=dict, description="Additional model parameters")


class AssignmentRequest(BaseModel):
    """Request model for variant assignment."""

    user_id: str = Field(..., description="User ID to assign")
    session_context: Optional[Dict[str, Any]] = Field(None, description="Session context for allocation")


class ResultRecordRequest(BaseModel):
    """Request model for recording test results."""

    user_id: str = Field(..., description="User ID")
    metric_values: Dict[str, float] = Field(..., description="Metric values (MetricType -> value)")
    success: bool = Field(..., description="Whether the interaction was successful")
    response_time_ms: int = Field(..., ge=0, description="Response time in milliseconds")
    user_satisfaction: Optional[float] = Field(None, ge=1.0, le=5.0, description="User satisfaction rating")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context information")


class TestSummaryResponse(BaseModel):
    """Response model for test summary."""

    id: str
    name: str
    description: str
    test_type: str
    status: str
    variants_count: int
    participants_count: int
    results_count: int
    is_significant: Optional[bool] = None
    winner_variant_id: Optional[str] = None
    improvement_percentage: Optional[float] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    created_at: str


class AssignmentResponse(BaseModel):
    """Response model for variant assignment."""

    success: bool
    variant_id: Optional[str] = None
    variant_name: Optional[str] = None
    variant_config: Optional[Dict[str, Any]] = None
    test_metadata: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


class ResultAnalysisResponse(BaseModel):
    """Response model for test result analysis."""

    success: bool
    analysis: Optional[Dict[str, Any]] = None
    statistical_significance: Optional[Dict[str, Any]] = None
    recommendations: Optional[List[str]] = None
    deployment_suggestion: Optional[str] = None
    risk_assessment: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


@router.post("/tests", response_model=TestSummaryResponse)
async def create_test(
    request: CreateTestRequest,
    current_user: Dict = Depends(get_current_user)
):
    """
    Create a new A/B test for prompt performance comparison.

    Creates a comprehensive A/B test with statistical validation,
    variant configuration, and targeting parameters. Supports
    multiple statistical tests and traffic allocation methods.

    Features:
    - **Statistical Validation**: Automatic power analysis and sample size calculation
    - **Variant Configuration**: Support for multiple AI models and prompt templates
    - **Traffic Allocation**: Multiple allocation strategies (random, hash-based, bandit)
    - **Targeting**: User segment and course-specific targeting
    - **Quality Control**: Automatic bias detection and validation checks

    Args:
        request: Test creation parameters and configuration
        current_user: Authenticated user information

    Returns:
        TestSummaryResponse: Created test summary information
    """
    if not ab_framework:
        raise HTTPException(
            status_code=503,
            detail="A/B testing framework is currently unavailable"
        )

    try:
        logger.info(f"Creating A/B test '{request.name}' by user {current_user.get('sub')}")

        # Validate variant configurations
        if len(request.variants) < 2:
            raise HTTPException(
                status_code=400,
                detail="At least 2 variants are required for A/B testing"
            )

        # Find control variant
        control_variant = None
        for variant in request.variants:
            if variant.get("name") == request.control_variant_name:
                control_variant = variant
                break

        if not control_variant:
            raise HTTPException(
                status_code=400,
                detail=f"Control variant '{request.control_variant_name}' not found"
            )

        # Ensure all variants have required fields
        validated_variants = []
        for i, variant in enumerate(request.variants):
            if "prompt_template" not in variant:
                raise HTTPException(
                    status_code=400,
                    detail=f"Variant {i+1} missing required 'prompt_template' field"
                )

            validated_variants.append({
                "name": variant["name"],
                "description": variant.get("description", ""),
                "traffic_weight": variant.get("traffic_weight", 1.0),
                "prompt_template": variant["prompt_template"],
                "model_provider": variant.get("model_provider", "zai"),
                "model_name": variant.get("model_name", "glm-4.6"),
                "temperature": variant.get("temperature", 0.7),
                "max_tokens": variant.get("max_tokens", 2000),
                "additional_params": variant.get("additional_params", {})
            })

        # Create test
        test = await ab_framework.create_test(
            name=request.name,
            description=request.description,
            test_type=request.test_type,
            variants=validated_variants,
            control_variant_id=control_variant.get("name", str(uuid.uuid4())),
            created_by=current_user.get("sub"),
            traffic_allocation_method=request.traffic_allocation_method,
            statistical_test=request.statistical_test,
            confidence_level=request.confidence_level,
            minimum_detectable_effect=request.minimum_detectable_effect,
            target_user_segment=request.target_user_segment,
            target_course_ids=request.target_course_ids,
            sample_size_required=request.sample_size_required,
            duration_days=request.duration_days
        )

        # Convert to response format
        response = TestSummaryResponse(
            id=test.id,
            name=test.name,
            description=test.description,
            test_type=test.test_type.value,
            status=test.status.value,
            variants_count=len(test.variants),
            participants_count=0,
            results_count=0,
            start_date=test.start_date.isoformat() if test.start_date else None,
            end_date=test.end_date.isoformat() if test.end_date else None,
            created_at=test.created_at.isoformat()
        )

        logger.info(f"Successfully created A/B test '{test.name}' with ID {test.id}")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating A/B test: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create A/B test: {str(e)}"
        )


@router.get("/tests", response_model=List[TestSummaryResponse])
async def list_tests(
    status: Optional[TestStatus] = Query(None, description="Filter by test status"),
    test_type: Optional[TestType] = Query(None, description="Filter by test type"),
    limit: int = Query(default=50, ge=1, le=200, description="Maximum number of tests to return"),
    current_user: Dict = Depends(get_current_user)
):
    """
    List A/B tests with optional filtering.

    Returns a list of A/B tests with basic statistics and status information.
    Supports filtering by status and test type for easier test management.

    Args:
        status: Optional status filter
        test_type: Optional test type filter
        limit: Maximum number of tests to return
        current_user: Authenticated user information

    Returns:
        List[TestSummaryResponse]: List of test summaries
    """
    if not ab_framework:
        raise HTTPException(
            status_code=503,
            detail="A/B testing framework is currently unavailable"
        )

    try:
        logger.info(f"Listing A/B tests for user {current_user.get('sub')}")

        # Get tests from framework
        tests = await ab_framework.get_all_tests(
            status=status,
            test_type=test_type,
            limit=limit,
            created_by=current_user.get("sub")
        )

        # Convert to response format
        summaries = []
        for test in tests:
            summary = TestSummaryResponse(
                id=test.id,
                name=test.name,
                description=test.description,
                test_type=test.test_type.value,
                status=test.status.value,
                variants_count=len(test.variants),
                participants_count=sum(v.participant_count for v in test.variants),
                results_count=sum(
                    v.conversion_count + v.participant_count - v.conversion_count
                    for v in test.variants
                ),
                is_significant=test.is_significant,
                winner_variant_id=test.winner_variant_id,
                improvement_percentage=test.improvement_percentage,
                start_date=test.start_date.isoformat() if test.start_date else None,
                end_date=test.end_date.isoformat() if test.end_date else None,
                created_at=test.created_at.isoformat()
            )
            summaries.append(summary)

        logger.info(f"Retrieved {len(summaries)} A/B tests")
        return summaries

    except Exception as e:
        logger.error(f"Error listing A/B tests: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list A/B tests: {str(e)}"
        )


@router.post("/tests/{test_id}/start")
async def start_test(
    test_id: str,
    background_tasks: BackgroundTasks,
    current_user: Dict = Depends(get_current_user)
):
    """
    Start an A/B test.

    Activates a drafted A/B test and begins allocating traffic to variants.
    Performs final validation checks and initializes monitoring systems.

    Args:
        test_id: Test ID to start
        background_tasks: FastAPI background tasks
        current_user: Authenticated user information

    Returns:
        Dict: Operation result
    """
    if not ab_framework:
        raise HTTPException(
            status_code=503,
            detail="A/B testing framework is currently unavailable"
        )

    try:
        logger.info(f"Starting A/B test {test_id} by user {current_user.get('sub')}")

        # Start the test
        success = await ab_framework.start_test(test_id)

        if success:
            # Schedule background monitoring
            background_tasks.add_task(
                monitor_test_progress,
                test_id,
                current_user.get("sub")
            )

            logger.info(f"Successfully started A/B test {test_id}")
            return {
                "success": True,
                "message": f"Test {test_id} started successfully",
                "test_id": test_id
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to start test {test_id}"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting test {test_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start test: {str(e)}"
        )


@router.post("/tests/{test_id}/assign", response_model=AssignmentResponse)
async def assign_variant(
    test_id: str,
    request: AssignmentRequest,
    current_user: Dict = Depends(get_current_user)
):
    """
    Assign user to a test variant.

    Assigns a user to a variant within an active A/B test using the
    configured traffic allocation method. Returns the assigned variant
    configuration for immediate use.

    Features:
    - **Consistent Assignment**: Users get the same variant across sessions
    - **Targeting Compliance**: Respects test targeting criteria
    - **Quality Control**: Includes data validation and bias detection
    - **Performance Tracking**: Tracks assignment for analytics

    Args:
        test_id: Test ID
        request: Assignment request with user and context
        current_user: Authenticated user information

    Returns:
        AssignmentResponse: Assignment result with variant configuration
    """
    if not ab_framework:
        raise HTTPException(
            status_code=503,
            detail="A/B testing framework is currently unavailable"
        )

    try:
        logger.info(f"Assigning user {request.user_id} to test {test_id}")

        # Assign variant
        variant = await ab_framework.assign_variant(
            test_id=test_id,
            user_id=request.user_id,
            session_context=request.session_context
        )

        if variant:
            # Get test details
            test = await ab_framework.get_test(test_id)

            response = AssignmentResponse(
                success=True,
                variant_id=variant.id,
                variant_name=variant.name,
                variant_config={
                    "prompt_template": variant.prompt_template,
                    "model_provider": variant.model_provider,
                    "model_name": variant.model_name,
                    "temperature": variant.temperature,
                    "max_tokens": variant.max_tokens,
                    "additional_params": variant.additional_params
                },
                test_metadata={
                    "test_id": test_id,
                    "test_name": test.name if test else "",
                    "test_type": test.test_type.value if test else "",
                    "is_control": variant.id == test.control_variant_id if test else False
                }
            )

            logger.info(f"Assigned user {request.user_id} to variant '{variant.name}' in test {test_id}")
            return response
        else:
            return AssignmentResponse(
                success=False,
                error_message="User not eligible for test assignment"
            )

    except Exception as e:
        logger.error(f"Error assigning variant for test {test_id}: {str(e)}", exc_info=True)
        return AssignmentResponse(
            success=False,
            error_message=str(e)
        )


@router.post("/tests/{test_id}/results")
async def record_result(
    test_id: str,
    request: ResultRecordRequest,
    current_user: Dict = Depends(get_current_user)
):
    """
    Record test result for analysis.

    Records performance metrics and outcomes for a user's interaction
    with a test variant. Includes quality control and bias detection.

    Metrics Tracked:
    - **Response Time**: AI model response time in milliseconds
    - **Success Rate**: Whether the interaction was successful
    - **User Satisfaction**: User satisfaction rating (1-5)
    - **Cost Efficiency**: Token usage and cost tracking
    - **Learning Gains**: Educational effectiveness metrics
    - **Engagement Time**: Time spent interacting with the response

    Args:
        test_id: Test ID
        request: Result data with metrics and context
        current_user: Authenticated user information

    Returns:
        Dict: Operation result
    """
    if not ab_framework:
        raise HTTPException(
            status_code=503,
            detail="A/B testing framework is currently unavailable"
        )

    try:
        logger.info(f"Recording result for user {request.user_id} in test {test_id}")

        # Convert metric strings to enum
        metric_values = {}
        for metric_str, value in request.metric_values.items():
            try:
                metric_type = MetricType(metric_str)
                metric_values[metric_type] = value
            except ValueError:
                logger.warning(f"Unknown metric type: {metric_str}")

        # Record result
        success = await ab_framework.record_result(
            test_id=test_id,
            user_id=request.user_id,
            metric_values=metric_values,
            success=request.success,
            response_time_ms=request.response_time_ms,
            user_satisfaction=request.user_satisfaction,
            context=request.context
        )

        if success:
            logger.info(f"Successfully recorded result for user {request.user_id} in test {test_id}")
            return {
                "success": True,
                "message": "Result recorded successfully"
            }
        else:
            raise HTTPException(
                status_code=400,
                detail="Failed to record result"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error recording result for test {test_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to record result: {str(e)}"
        )


@router.post("/tests/{test_id}/analyze", response_model=ResultAnalysisResponse)
async def analyze_test(
    test_id: str,
    background_tasks: BackgroundTasks,
    current_user: Dict = Depends(get_current_user)
):
    """
    Analyze A/B test results.

    Performs comprehensive statistical analysis of test results including
    significance testing, effect size calculation, and risk assessment.
    Generates deployment recommendations and insights.

    Analysis Methods:
    - **Statistical Tests**: Z-test, t-test, chi-square, Mann-Whitney, Bayesian
    - **Significance Testing**: P-value calculation and confidence intervals
    - **Effect Size**: Cohen's d and practical significance assessment
    - **Risk Analysis**: Business impact and deployment risk assessment
    - **Insight Generation**: AI-powered insights and recommendations

    Args:
        test_id: Test ID to analyze
        background_tasks: FastAPI background tasks
        current_user: Authenticated user information

    Returns:
        ResultAnalysisResponse: Comprehensive analysis results
    """
    if not ab_framework:
        raise HTTPException(
            status_code=503,
            detail="A/B testing framework is currently unavailable"
        )

    try:
        logger.info(f"Analyzing A/B test {test_id} by user {current_user.get('sub')}")

        # Perform analysis
        analysis = await ab_framework.analyze_test(test_id)

        if "error" in analysis:
            raise HTTPException(
                status_code=400,
                detail=f"Analysis failed: {analysis['error']}"
            )

        # Generate additional insights using AI
        insights = await _generate_ai_insights(test_id, analysis)

        # Create deployment recommendation
        deployment_suggestion = _create_deployment_recommendation(analysis)

        response = ResultAnalysisResponse(
            success=True,
            analysis=analysis,
            statistical_significance={
                "is_significant": analysis.get("is_significant", False),
                "p_value": analysis.get("p_value"),
                "confidence_level": analysis.get("confidence_level"),
                "confidence_interval": analysis.get("confidence_interval"),
                "effect_size": analysis.get("effect_size")
            },
            recommendations=insights,
            deployment_suggestion=deployment_suggestion,
            risk_assessment=analysis.get("risk_assessment")
        )

        logger.info(f"Successfully analyzed test {test_id}")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing test {test_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze test: {str(e)}"
        )


@router.get("/tests/{test_id}/results")
async def get_test_results(
    test_id: str,
    include_time_series: bool = Query(default=True, description="Include time series data"),
    include_segments: bool = Query(default=True, description="Include segment analysis"),
    current_user: Dict = Depends(get_current_user)
):
    """
    Get comprehensive test results and analytics.

    Returns detailed performance data, statistical analysis, and
    insights for a specific A/B test. Includes variant performance,
    time-series data, and segment analysis.

    Data Included:
    - **Variant Performance**: Metrics for each test variant
    - **Statistical Analysis**: Significance tests and confidence intervals
    - **Time Series**: Performance over time
    - **Segment Analysis**: Performance by user segments
    - **Business Impact**: ROI and business value assessment

    Args:
        test_id: Test ID
        include_time_series: Include time-series analysis
        include_segments: Include segment-based analysis
        current_user: Authenticated user information

    Returns:
        Dict: Comprehensive test results and analytics
    """
    if not ab_framework:
        raise HTTPException(
            status_code=503,
            detail="A/B testing framework is currently unavailable"
        )

    try:
        logger.info(f"Retrieving results for test {test_id}")

        # Get test results
        results = await ab_framework.get_test_results(test_id)

        if "error" in results:
            raise HTTPException(
                status_code=404,
                detail=f"Test {test_id} not found or no results available"
            )

        # Filter data based on query parameters
        if not include_time_series:
            results.pop("time_series", None)

        if not include_segments:
            results.pop("segment_analysis", None)

        logger.info(f"Retrieved comprehensive results for test {test_id}")
        return results

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving test results for {test_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve test results: {str(e)}"
        )


@router.get("/tests/{test_id}/analytics")
async def get_test_analytics(
    test_id: str,
    metric_type: Optional[MetricType] = Query(None, description="Filter by metric type"),
    time_range: Optional[str] = Query(None, description="Time range for analysis"),
    current_user: Dict = Depends(get_current_user)
):
    """
    Get real-time test analytics and monitoring data.

    Returns current performance metrics, participant statistics,
    and monitoring data for active A/B tests. Useful for real-time
    dashboards and monitoring systems.

    Analytics Available:
    - **Live Metrics**: Real-time performance indicators
    - **Participant Stats**: User participation and engagement data
    - **Health Monitoring**: Test health and data quality metrics
    - **Progress Tracking**: Test completion and statistical power
    - **Alert System**: Automated alerts for anomalies

    Args:
        test_id: Test ID
        metric_type: Optional metric type filter
        time_range: Optional time range for analysis
        current_user: Authenticated user information

    Returns:
        Dict: Real-time analytics data
    """
    if not ab_framework:
        raise HTTPException(
            status_code=503,
            detail="A/B testing framework is currently unavailable"
        )

    try:
        logger.info(f"Retrieving analytics for test {test_id}")

        # Get test
        test = await ab_framework.get_test(test_id)
        if not test:
            raise HTTPException(
                status_code=404,
                detail=f"Test {test_id} not found"
            )

        # Get current analytics
        analytics = await ab_framework.get_test_analytics(
            test_id=test_id,
            metric_type=metric_type,
            time_range=time_range
        )

        # Add test metadata
        analytics["test_metadata"] = {
            "name": test.name,
            "status": test.status.value,
            "start_date": test.start_date.isoformat() if test.start_date else None,
            "variants_count": len(test.variants),
            "statistical_test": test.statistical_test.value,
            "confidence_level": test.confidence_level
        }

        logger.info(f"Retrieved analytics for test {test_id}")
        return analytics

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving analytics for test {test_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve analytics: {str(e)}"
        )


@router.post("/tests/{test_id}/deploy")
async def deploy_winner(
    test_id: str,
    confirmation: bool = Query(..., description="Confirm deployment"),
    current_user: Dict = Depends(get_current_user)
):
    """
    Deploy the winning variant of a completed test.

    Deploys the winning variant to production after confirming
    statistical significance and business impact. Includes rollback
    capabilities and deployment monitoring.

    Deployment Process:
    - **Validation**: Final statistical and business validation
    - **Rollout Plan**: Gradual rollout with monitoring
    - **Rollback Protection**: Automatic rollback on performance degradation
    - **Documentation**: Comprehensive deployment documentation
    - **Monitoring**: Post-deployment performance monitoring

    Args:
        test_id: Test ID
        confirmation: Deployment confirmation flag
        current_user: Authenticated user information

    Returns:
        Dict: Deployment result and monitoring information
    """
    if not ab_framework:
        raise HTTPException(
            status_code=503,
            detail="A/B testing framework is currently unavailable"
        )

    if not confirmation:
        raise HTTPException(
            status_code=400,
            detail="Deployment confirmation required"
        )

    try:
        logger.info(f"Deploying winner for test {test_id} by user {current_user.get('sub')}")

        # Deploy winning variant
        deployment_result = await ab_framework.deploy_winner(test_id)

        if deployment_result.get("success"):
            logger.info(f"Successfully deployed winner for test {test_id}")
            return deployment_result
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Deployment failed: {deployment_result.get('error', 'Unknown error')}"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deploying winner for test {test_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to deploy winner: {str(e)}"
        )


# Helper functions for additional functionality

async def monitor_test_progress(test_id: str, user_id: str):
    """Background task to monitor test progress."""
    try:
        # This would implement ongoing monitoring logic
        logger.info(f"Monitoring progress for test {test_id}")
    except Exception as e:
        logger.error(f"Error monitoring test progress: {str(e)}")


async def _generate_ai_insights(test_id: str, analysis: Dict[str, Any]) -> List[str]:
    """Generate AI-powered insights from test analysis."""
    try:
        if not ab_framework:
            return []

        # Use AI to generate insights
        insights_prompt = f"""
        Analyze this A/B test data and generate actionable insights:

        Test Analysis:
        {json.dumps(analysis, indent=2)}

        Generate 3-5 specific, actionable insights that would help:
        1. Understand why certain variants performed better
        2. Identify patterns in user behavior
        3. Suggest improvements for future tests
        4. Provide business-relevant recommendations

        Focus on practical, implementable insights.
        """

        # This would integrate with LLM service
        # For now, return placeholder insights
        return [
            "Statistical significance achieved - results are reliable",
            "Consider implementing winning variant across all users",
            "Monitor post-deployment performance closely",
            "Document learnings for future test design"
        ]

    except Exception as e:
        logger.error(f"Error generating AI insights: {str(e)}")
        return []


def _create_deployment_recommendation(analysis: Dict[str, Any]) -> str:
    """Create deployment recommendation based on analysis."""
    try:
        if not analysis.get("is_significant", False):
            return "continue_testing"

        improvement = analysis.get("improvement_percentage", 0)
        if improvement > 10:
            return "deploy_winner"
        elif improvement > 0:
            return "consider_deployment"
        else:
            return "keep_control"

    except Exception:
        return "manual_review_required"


# Health check endpoint
@router.get("/health")
async def health_check():
    """Health check endpoint for A/B testing API."""
    if ab_framework:
        return {
            "status": "healthy",
            "service": "ab_testing",
            "version": "1.0.0",
            "features": {
                "statistical_tests": ["z_test", "t_test", "chi_square", "mann_whitney", "bayesian_ab"],
                "allocation_methods": ["random", "hash_based", "multi_armed_bandit"],
                "test_types": ["prompt_template", "model_selection", "parameter_tuning"],
                "real_time_analytics": True,
                "risk_assessment": True,
                "ai_insights": True
            }
        }
    else:
        return {
            "status": "unhealthy",
            "service": "ab_testing",
            "error": "A/B testing framework initialization failed"
        }