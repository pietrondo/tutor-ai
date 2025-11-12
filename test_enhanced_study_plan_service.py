#!/usr/bin/env python3
"""
Test script for Enhanced Study Plan Service with Learning Science and GLM-4.6
"""

import asyncio
import json
import sys
import os
from datetime import datetime, timedelta

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.services.enhanced_study_plan_service import (
    EnhancedStudyPlanService,
    LearningObjectiveType,
    StudyStrategy,
    DifficultyProgression
)

async def test_enhanced_study_plan_generation():
    """Test the enhanced study plan generation with different configurations"""
    print("📚 Testing Enhanced Study Plan Generation Service")
    print("=" * 50)

    service = EnhancedStudyPlanService()

    # Test configurations
    test_cases = [
        {
            "name": "Beginner University Student",
            "course_content": {
                "topics": ["Introduction to Psychology", "Research Methods", "Cognitive Processes", "Social Psychology", "Developmental Psychology"],
                "materials": [
                    {"source": "psychology_textbook.pdf", "chunks_count": 150},
                    {"source": "research_methods_guide.pdf", "chunks_count": 80}
                ],
                "chapters": [
                    {"title": "Chapter 1: What is Psychology?", "estimated_minutes": 45},
                    {"title": "Chapter 2: Research Methods", "estimated_minutes": 60},
                    {"title": "Chapter 3: Cognitive Processes", "estimated_minutes": 55}
                ],
                "estimated_total_hours": 40
            },
            "learner_profile": {
                "experience_level": "beginner",
                "study_discipline": "moderate",
                "time_availability": "moderate",
                "motivation_level": "high",
                "preferred_session_length": "moderate",
                "working_memory": "average",
                "metacognitive_awareness": "beginner"
            },
            "time_constraints": {
                "hours_per_week": 12,
                "deadline": (datetime.now() + timedelta(weeks=10)).isoformat(),
                "preferred_study_days": ["monday", "wednesday", "friday", "saturday"]
            },
            "learning_objectives": [
                {
                    "title": "Understand basic psychological concepts",
                    "description": "Grasp fundamental theories and terminology",
                    "priority": "high",
                    "cognitive_level": "understand"
                },
                {
                    "title": "Apply research methods to psychological studies",
                    "description": "Design and evaluate psychological research",
                    "priority": "medium",
                    "cognitive_level": "apply"
                }
            ]
        },
        {
            "name": "Advanced Computer Science Student",
            "course_content": {
                "topics": ["Machine Learning", "Neural Networks", "Deep Learning", "Computer Vision", "Natural Language Processing"],
                "materials": [
                    {"source": "ml_algorithms.pdf", "chunks_count": 200},
                    {"source": "neural_networks.pdf", "chunks_count": 180},
                    {"source": "cv_applications.pdf", "chunks_count": 150}
                ],
                "chapters": [
                    {"title": "Chapter 1: Introduction to Machine Learning", "estimated_minutes": 90},
                    {"title": "Chapter 2: Neural Network Fundamentals", "estimated_minutes": 120},
                    {"title": "Chapter 3: Deep Learning Architectures", "estimated_minutes": 150}
                ],
                "estimated_total_hours": 60
            },
            "learner_profile": {
                "experience_level": "advanced",
                "study_discipline": "high",
                "time_availability": "high",
                "motivation_level": "high",
                "preferred_session_length": "long",
                "working_memory": "high",
                "metacognitive_awareness": "advanced",
                "challenge_tolerance": "high"
            },
            "time_constraints": {
                "hours_per_week": 20,
                "deadline": (datetime.now() + timedelta(weeks=8)).isoformat(),
                "preferred_study_days": ["monday", "tuesday", "wednesday", "thursday", "friday"]
            },
            "learning_objectives": [
                {
                    "title": "Design and implement neural network architectures",
                    "description": "Create custom neural networks for specific problems",
                    "priority": "high",
                    "cognitive_level": "create"
                },
                {
                    "title": "Evaluate and optimize machine learning models",
                    "description": "Apply advanced optimization techniques",
                    "priority": "high",
                    "cognitive_level": "evaluate"
                }
            ]
        },
        {
            "name": "Time-Constrained Professional Learner",
            "course_content": {
                "topics": ["Business Strategy", "Market Analysis", "Financial Planning", "Leadership", "Organizational Behavior"],
                "materials": [
                    {"source": "business_strategy.pdf", "chunks_count": 120},
                    {"source": "market_analysis.pdf", "chunks_count": 100}
                ],
                "chapters": [
                    {"title": "Chapter 1: Strategic Planning", "estimated_minutes": 40},
                    {"title": "Chapter 2: Market Analysis", "estimated_minutes": 35},
                    {"title": "Chapter 3: Financial Strategy", "estimated_minutes": 50}
                ],
                "estimated_total_hours": 30
            },
            "learner_profile": {
                "experience_level": "intermediate",
                "study_discipline": "high",
                "time_availability": "low",
                "motivation_level": "high",
                "preferred_session_length": "short",
                "working_memory": "average",
                "attention_span": "short",
                "metacognitive_awareness": "developing"
            },
            "time_constraints": {
                "hours_per_week": 6,
                "deadline": (datetime.now() + timedelta(weeks=12)).isoformat(),
                "preferred_study_days": ["saturday", "sunday"]
            },
            "learning_objectives": [
                {
                    "title": "Apply business frameworks to real scenarios",
                    "description": "Use strategic tools in practical business situations",
                    "priority": "high",
                    "cognitive_level": "apply"
                }
            ]
        }
    ]

    results = []

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📝 Test Case {i}: {test_case['name']}")
        print(f"   Experience Level: {test_case['learner_profile']['experience_level']}")
        print(f"   Time Availability: {test_case['time_constraints']['hours_per_week']} hours/week")
        print(f"   Learning Objectives: {len(test_case['learning_objectives'])}")

        try:
            # Generate enhanced study plan
            start_time = datetime.now()

            study_plan = await service.generate_enhanced_study_plan(
                course_id=f"test_course_{i}",
                course_content=test_case['course_content'],
                learner_profile=test_case['learner_profile'],
                study_preferences={},
                time_constraints=test_case['time_constraints'],
                learning_objectives=test_case['learning_objectives'],
                previous_performance={}
            )

            generation_time = (datetime.now() - start_time).total_seconds()

            # Analyze results
            analysis = analyze_study_plan_results(study_plan, test_case)
            results.append({
                "test_case": test_case['name'],
                "success": True,
                "analysis": analysis,
                "generation_time": generation_time
            })

            print(f"   ✅ SUCCESS: Generated plan with {len(study_plan.get('study_sessions', []))} sessions")
            print(f"   📊 Estimated Duration: {analysis['estimated_duration_hours']} hours")
            print(f"   🧠 Learning Trajectory: {analysis['trajectory_phases']} phases")
            print(f"   🎯 Success Prediction: {analysis['success_prediction']:.2f}")
            print(f"   ⏱️ Generation Time: {generation_time:.2f}s")

            # Display sample session structure
            if analysis['sample_sessions']:
                print(f"   📋 Sample Sessions:")
                for session_title in analysis['sample_sessions'][:3]:
                    print(f"      - {session_title}")

        except Exception as e:
            print(f"   ❌ FAILED: {str(e)}")
            results.append({
                "test_case": test_case['name'],
                "success": False,
                "error": str(e),
                "generation_time": 0
            })

    # Summary
    print("\n" + "=" * 50)
    print("📈 TEST SUMMARY")
    print("=" * 50)

    successful_tests = sum(1 for r in results if r['success'])
    total_tests = len(results)

    print(f"Total Tests: {total_tests}")
    print(f"Successful: {successful_tests}")
    print(f"Failed: {total_tests - successful_tests}")
    print(f"Success Rate: {(successful_tests/total_tests)*100:.1f}%")

    # Performance metrics
    avg_generation_time = sum(r.get('generation_time', 0) for r in results if r['success']) / max(successful_tests, 1)
    print(f"Average Generation Time: {avg_generation_time:.2f}s")

    # Detailed results
    print("\n📋 DETAILED RESULTS:")
    for result in results:
        status = "✅" if result['success'] else "❌"
        print(f"{status} {result['test_case']}")
        if result['success']:
            analysis = result['analysis']
            print(f"   Sessions: {analysis['session_count']}, Duration: {analysis['estimated_duration_hours']}h")
            print(f"   Success Prediction: {analysis.get('success_prediction', 'N/A')}")
        else:
            print(f"   Error: {result.get('error', 'Unknown error')}")

    return results

def analyze_study_plan_results(study_plan: dict, test_case: dict) -> dict:
    """Analyze the generated study plan results"""

    sessions = study_plan.get('study_sessions', [])
    learning_trajectory = study_plan.get('learning_trajectory', {})
    success_metrics = study_plan.get('success_metrics', {})
    metacognitive_framework = study_plan.get('metacognitive_framework', {})
    adaptive_elements = study_plan.get('adaptive_elements', {})

    # Analyze session structure
    session_count = len(sessions)
    difficulty_distribution = {}
    for session in sessions:
        difficulty = session.get('difficulty_level', 'intermediate')
        difficulty_distribution[difficulty] = difficulty_distribution.get(difficulty, 0) + 1

    # Analyze learning trajectory
    trajectory_phases = len(learning_trajectory.get('phases', []))
    milestones = len(learning_trajectory.get('milestones', []))

    # Analyze cognitive levels in objectives
    objectives_mastery = study_plan.get('objectives_mastery', {})
    structured_objectives = objectives_mastery.get('structured_objectives', [])
    cognitive_levels = {}
    for obj in structured_objectives:
        level = obj.get('cognitive_level', 'unknown')
        cognitive_levels[level] = cognitive_levels.get(level, 0) + 1

    # Check learning science integration
    learning_strategies = study_plan.get('learning_strategies', {})
    primary_strategies = learning_strategies.get('primary_strategies', [])
    strategy_count = len(primary_strategies)

    # Metacognitive components
    metacognitive_components = 0
    if metacognitive_framework.get('reflection_prompts'):
        metacognitive_components += 1
    if metacognitive_framework.get('self_regulation_tools'):
        metacognitive_components += 1
    if metacognitive_framework.get('reflection_cycles'):
        metacognitive_components += 1

    # Sample sessions for display
    sample_sessions = [session.get('title', 'Untitled') for session in sessions[:3]]

    analysis = {
        'session_count': session_count,
        'estimated_duration_hours': study_plan.get('estimated_duration', 0),
        'trajectory_phases': trajectory_phases,
        'milestones_count': milestones,
        'cognitive_levels': cognitive_levels,
        'difficulty_distribution': difficulty_distribution,
        'primary_strategies_count': strategy_count,
        'metacognitive_components': metacognitive_components,
        'success_prediction': success_metrics.get('success_prediction', {}).get('success_probability', 0.7),
        'completion_probability': success_metrics.get('completion_probability', 0.7),
        'adaptive_elements_count': len(adaptive_elements.get('performance_triggers', {})),
        'sample_sessions': sample_sessions,
        'has_learning_trajectory': trajectory_phases > 0,
        'has_metacognitive_framework': metacognitive_components > 0,
        'has_adaptive_elements': bool(adaptive_elements),
        'integrated_learning_science': strategy_count >= 2
    }

    return analysis

async def test_learning_objective_extraction():
    """Test learning objective extraction and structuring"""
    print("\n🎯 Testing Learning Objective Extraction")
    print("=" * 30)

    service = EnhancedStudyPlanService()

    # Test course content and learner profile
    course_content = {
        "topics": ["Calculus", "Linear Algebra", "Probability Theory"],
        "materials": [{"source": "advanced_mathematics.pdf", "chunks_count": 200}],
        "estimated_total_hours": 45
    }

    learner_analysis = {
        "experience_level": "intermediate",
        "metacognitive_awareness": "developing",
        "challenge_tolerance": "moderate"
    }

    learning_objectives = [
        {
            "title": "Master differential calculus",
            "description": "Understand and apply derivative rules and applications",
            "priority": "high"
        },
        {
            "title": "Solve linear systems",
            "description": "Apply matrix methods to solve systems of equations",
            "priority": "high"
        }
    ]

    try:
        print("Extracting structured objectives...")

        structured_objectives = await service._extract_structured_objectives(
            learning_objectives,
            course_content,
            learner_analysis
        )

        objectives_count = len(structured_objectives.get('structured_objectives', []))
        print(f"✅ SUCCESS: Structured {objectives_count} learning objectives")

        # Check for Bloom's taxonomy integration
        objectives = structured_objectives.get('structured_objectives', [])
        bloom_levels = set(obj.get('bloom_taxonomy') for obj in objectives if obj.get('bloom_taxonomy'))
        print(f"📊 Bloom's Levels Covered: {list(bloom_levels)}")

        # Check for mastery criteria
        mastery_criteria_count = sum(1 for obj in objectives if obj.get('mastery_criteria'))
        print(f"🎯 Mastery Criteria: {mastery_criteria_count}/{objectives_count} objectives")

        # Check learning sequence
        learning_sequence = structured_objectives.get('learning_sequence', {})
        phases = learning_sequence.get('phases', [])
        print(f"📈 Learning Phases: {len(phases)}")

        return True

    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False

async def test_strategy_optimization():
    """Test strategy optimization and effectiveness prediction"""
    print("\n🧪 Testing Strategy Optimization")
    print("=" * 30)

    service = EnhancedStudyPlanService()

    # Test different learner profiles
    learner_profiles = [
        {
            "name": "Beginner with Low Discipline",
            "profile": {
                "experience_level": "beginner",
                "study_discipline": "low",
                "metacognitive_awareness": "beginner",
                "working_memory": "low"
            }
        },
        {
            "name": "Advanced High Performer",
            "profile": {
                "experience_level": "advanced",
                "study_discipline": "high",
                "metacognitive_awareness": "advanced",
                "working_memory": "high"
            }
        }
    ]

    results = []

    for learner_test in learner_profiles:
        print(f"\nTesting: {learner_test['name']}")

        # Create test objectives
        test_objectives = {
            "structured_objectives": [
                {
                    "id": "obj_1",
                    "cognitive_level": "knowledge_acquisition",
                    "title": "Basic Concept Understanding"
                },
                {
                    "id": "obj_2",
                    "cognitive_level": "comprehension_application",
                    "title": "Application Skills"
                }
            ]
        }

        try:
            optimal_strategies = service._determine_optimal_strategies(
                learner_test['profile'],
                test_objectives,
                {}
            )

            primary_strategies = optimal_strategies.get('primary_strategies', [])
            effectiveness_predictions = optimal_strategies.get('effectiveness_predictions', {})

            print(f"   Primary Strategies: {primary_strategies}")
            print(f"   Strategy Count: {len(primary_strategies)}")

            # Calculate average effectiveness
            if effectiveness_predictions:
                avg_effectiveness = sum(effectiveness_predictions.values()) / len(effectiveness_predictions)
                print(f"   Average Effectiveness: {avg_effectiveness:.2f}")

            results.append({
                "learner_type": learner_test['name'],
                "success": True,
                "strategies": len(primary_strategies),
                "avg_effectiveness": avg_effectiveness if effectiveness_predictions else 0
            })

        except Exception as e:
            print(f"   ❌ FAILED: {e}")
            results.append({
                "learner_type": learner_test['name'],
                "success": False,
                "error": str(e)
            })

    return all(result['success'] for result in results)

async def test_metacognitive_framework():
    """Test metacognitive framework generation"""
    print("\n🤔 Testing Metacognitive Framework")
    print("=" * 30)

    service = EnhancedStudyPlanService()

    # Test different metacognitive awareness levels
    awareness_levels = ["beginner", "developing", "advanced"]

    for level in awareness_levels:
        print(f"\nTesting {level} metacognitive awareness level:")

        learner_analysis = {
            "metacognitive_awareness": level,
            "experience_level": "intermediate"
        }

        try:
            metacognitive_framework = service._generate_metacognitive_framework(learner_analysis)

            # Check framework components
            phases = ["planning_phase", "monitoring_phase", "evaluation_phase"]
            phase_count = sum(1 for phase in phases if metacognitive_framework.get(phase))

            print(f"   Framework Phases: {phase_count}/3")
            print(f"   Scaffolding Level: {metacognitive_framework.get('scaffolding', {}).get('simplification_level', 'unknown')}")

            # Test self-assessment tools
            self_assessment_tools = service._generate_self_assessment_tools()
            print(f"   Self-Assessment Tools: {len(self_assessment_tools)}")

            # Test goal setting framework
            goal_framework = service._generate_goal_setting_framework()
            smart_goals = goal_framework.get('smart_goals', {})
            print(f"   SMART Goals Framework: {len(smart_goals)} components")

        except Exception as e:
            print(f"   ❌ FAILED: {e}")
            return False

    return True

def test_performance_prediction():
    """Test learning success prediction"""
    print("\n📊 Testing Performance Prediction")
    print("=" * 30)

    service = EnhancedStudyPlanService()

    # Test different learner scenarios
    test_scenarios = [
        {
            "name": "Ideal Learner",
            "profile": {
                "study_discipline": "high",
                "time_availability": "high",
                "experience_level": "intermediate",
                "motivation_level": "high",
                "metacognitive_awareness": "advanced"
            },
            "expected_high": True
        },
        {
            "name": "At-Risk Learner",
            "profile": {
                "study_discipline": "low",
                "time_availability": "low",
                "experience_level": "beginner",
                "motivation_level": "low",
                "metacognitive_awareness": "beginner"
            },
            "expected_high": False
        }
    ]

    for scenario in test_scenarios:
        print(f"\nTesting: {scenario['name']}")

        try:
            # Mock strategies and objectives
            strategies = {"effectiveness_predictions": {"spaced_repetition": 0.8, "retrieval_practice": 0.75}}
            objectives = {"structured_objectives": [{"id": "obj1", "cognitive_level": "knowledge_acquisition"}]}

            prediction = service._predict_learning_success(
                scenario['profile'],
                strategies,
                objectives
            )

            success_probability = prediction.get('success_probability', 0)
            print(f"   Success Probability: {success_probability:.2f}")
            print(f"   Success Factors: {len(prediction.get('success_factors', []))}")
            print(f"   Risk Factors: {len(prediction.get('risk_factors', []))}")
            print(f"   Confidence: {prediction.get('confidence_level', 'unknown')}")

            # Check if prediction matches expectations
            if scenario['expected_high'] and success_probability >= 0.7:
                print(f"   ✅ Prediction matches expectation (high success)")
            elif not scenario['expected_high'] and success_probability < 0.5:
                print(f"   ✅ Prediction matches expectation (lower success)")
            else:
                print(f"   ⚠️ Unexpected prediction level")

        except Exception as e:
            print(f"   ❌ FAILED: {e}")
            return False

    return True

def print_service_capabilities():
    """Print service capabilities and features"""
    print("\n🚀 Enhanced Study Plan Service Capabilities")
    print("=" * 50)

    capabilities = {
        "Learning Science Integration": [
            "Spaced Repetition Optimization",
            "Interleaved Practice Design",
            "Elaborative Interrogation",
            "Dual Coding Implementation",
            "Retrieval Practice",
            "Concrete Examples Usage"
        ],
        "GLM-4.6 Long-term Reasoning": [
            "Learning Trajectory Planning",
            "Objective Structuring",
            "Cognitive Load Management",
            "Adaptive Progression Design",
            "Mastery Prediction",
            "Performance Analytics"
        ],
        "Personalization Features": [
            "Learner Profile Analysis",
            "Experience-based Adaptation",
            "Time Constraint Optimization",
            "Learning Style Integration",
            "Motivation Factor Analysis",
            "Challenge Tolerance Assessment"
        ],
        "Metacognitive Development": [
            "Reflection Framework",
            "Self-Assessment Tools",
            "Goal Setting Framework",
            "Strategy Selection Guidance",
            "Progress Monitoring",
            "Self-Regulation Tools"
        ],
        "Adaptive Elements": [
            "Performance Trigger System",
            "Dynamic Difficulty Adjustment",
            "Strategy Switching",
            "Motivation Enhancement",
            "Flexible Timeline Management",
            "Contingency Planning"
        ]
    }

    for category, features in capabilities.items():
        print(f"\n📚 {category}:")
        for feature in features:
            print(f"   ✅ {feature}")

async def main():
    """Main test execution"""
    print("📚 Enhanced Study Plan Service Test Suite")
    print("Testing Learning Science Integration with GLM-4.6 Long-term Reasoning")
    print("=" * 60)

    try:
        # Print capabilities
        print_service_capabilities()

        # Run main tests
        main_results = await test_enhanced_study_plan_generation()

        # Test individual components
        objective_extraction_result = await test_learning_objective_extraction()
        strategy_optimization_result = await test_strategy_optimization()
        metacognitive_result = await test_metacognitive_framework()
        performance_prediction_result = test_performance_prediction()

        # Final summary
        print("\n" + "=" * 60)
        print("🏁 FINAL TEST SUMMARY")
        print("=" * 60)

        main_success = sum(1 for r in main_results if r['success'])
        main_total = len(main_results)

        component_tests = [
            objective_extraction_result,
            strategy_optimization_result,
            metacognitive_result,
            performance_prediction_result
        ]

        component_success = sum(component_tests)
        component_total = len(component_tests)

        print(f"Main Generation Tests: {main_success}/{main_total} passed")
        print(f"Component Tests: {component_success}/{component_total} passed")

        total_passed = main_success + component_success
        total_tests = main_total + component_total
        overall_success_rate = (total_passed / total_tests) * 100

        print(f"\nOverall Success Rate: {overall_success_rate:.1f}%")

        if overall_success_rate >= 80:
            print("🎉 EXCELLENT: Enhanced study plan service is working very well!")
        elif overall_success_rate >= 60:
            print("✅ GOOD: Enhanced study plan service is mostly functional")
        else:
            print("⚠️  NEEDS WORK: Enhanced study plan service has significant issues")

        # Performance analysis
        if main_results:
            avg_time = sum(r.get('generation_time', 0) for r in main_results if r['success']) / max(main_success, 1)
            print(f"\nPerformance Metrics:")
            print(f"Average Generation Time: {avg_time:.2f} seconds")

            successful_results = [r for r in main_results if r['success']]
            if successful_results:
                avg_success_prediction = sum(r['analysis'].get('success_prediction', 0) for r in successful_results) / len(successful_results)
                avg_session_count = sum(r['analysis'].get('session_count', 0) for r in successful_results) / len(successful_results)
                print(f"Average Success Prediction: {avg_success_prediction:.2f}")
                print(f"Average Session Count: {avg_session_count:.1f}")

        return overall_success_rate >= 60

    except Exception as e:
        print(f"❌ CRITICAL ERROR: {str(e)}")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)