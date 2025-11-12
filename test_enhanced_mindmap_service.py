#!/usr/bin/env python3
"""
Test script for Enhanced Mindmap Service with GLM-4.6 and Cognitive Load Theory
"""

import asyncio
import json
import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.services.enhanced_mindmap_service import (
    EnhancedMindmapService,
    CognitiveLoadLevel,
    KnowledgeType,
    RelationshipType
)

async def test_enhanced_mindmap_generation():
    """Test the enhanced mindmap generation with different configurations"""
    print("🧠 Testing Enhanced Mindmap Generation Service")
    print("=" * 50)

    service = EnhancedMindmapService()

    # Test configurations
    test_cases = [
        {
            "name": "Beginner Student - Minimal Load",
            "topic": "Introduzione alla Programmazione",
            "context": """
            La programmazione è il processo di scrivere istruzioni che un computer può eseguire.
            Gli algoritmi sono sequenze di passaggi per risolvere problemi.
            Python è un linguaggio di programmazione facile da imparare.
            Le variabili memorizzano dati che possono cambiare durante l'esecuzione.
            I cicli permettono di ripetere azioni più volte.
            """,
            "cognitive_load": "minimal",
            "knowledge_type": "factual",
            "learner_profile": {
                "experience_level": "beginner",
                "complexity_tolerance": "low",
                "attention_span": "short"
            }
        },
        {
            "name": "Advanced Student - Complex Load",
            "topic": "Algoritmi di Ordinamento Complessi",
            "context": """
            Gli algoritmi di ordinamento sono fondamentali in computer science.
            QuickSort utilizza divide et impera con complessità O(n log n) media.
            MergeSort garantisce O(n log log n) nel caso peggiore.
            HeapSort sfrutta la struttura dati heap.
            Gli algoritmi esterni gestiscono dati che non entrano in memoria.
            L'ottimizzazione considera cache locality e parallelismo.
            """,
            "cognitive_load": "complex",
            "knowledge_type": "procedural",
            "learner_profile": {
                "experience_level": "advanced",
                "complexity_tolerance": "high",
                "attention_span": "long"
            }
        },
        {
            "name": "Metacognitive Learning",
            "topic": "Strategie di Studio Efficaci",
            "context": """
            Le tecniche di studio efficace includono ripetizione spaziata.
            La pratica attiva migliora la ritenzione a lungo termine.
            L'elaborazione profonda facilita il trasferimento della conoscenza.
            Il monitoraggio metacognitivo regola l'apprendimento.
            Le strategie di auto-regolazione ottimizzano il tempo di studio.
            La riflessione metacognitiva migliora la consapevolezza.
            """,
            "cognitive_load": "moderate",
            "knowledge_type": "metacognitive",
            "learner_profile": {
                "experience_level": "intermediate",
                "preferred_depth": "deep"
            }
        }
    ]

    results = []

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📝 Test Case {i}: {test_case['name']}")
        print(f"   Topic: {test_case['topic']}")
        print(f"   Cognitive Load: {test_case['cognitive_load']}")
        print(f"   Knowledge Type: {test_case['knowledge_type']}")

        try:
            # Generate enhanced mindmap
            mindmap = await service.generate_enhanced_mindmap(
                topic=test_case['topic'],
                context_text=test_case['context'],
                course_id=f"test_course_{i}",
                book_id=f"test_book_{i}",
                learner_profile=test_case.get('learner_profile'),
                cognitive_load_level=test_case.get('cognitive_load'),
                knowledge_type=test_case.get('knowledge_type'),
                focus_areas=[test_case['topic']]
            )

            # Analyze results
            analysis = analyze_mindmap_results(mindmap, test_case)
            results.append({
                "test_case": test_case['name'],
                "success": True,
                "analysis": analysis
            })

            print(f"   ✅ SUCCESS: Generated mindmap with {len(mindmap.get('nodes', []))} nodes")
            print(f"   📊 Concept Count: {analysis['concept_count']}")
            print(f"   🧠 Cognitive Load Applied: {mindmap.get('cognitive_load_level')}")
            print(f"   🔗 Relationships: {len(mindmap.get('relationships', []))}")

            # Display sample structure
            if analysis['sample_nodes']:
                print(f"   📋 Sample Nodes:")
                for node_title in analysis['sample_nodes'][:3]:
                    print(f"      - {node_title}")

        except Exception as e:
            print(f"   ❌ FAILED: {str(e)}")
            results.append({
                "test_case": test_case['name'],
                "success": False,
                "error": str(e)
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

    # Detailed results
    print("\n📋 DETAILED RESULTS:")
    for result in results:
        status = "✅" if result['success'] else "❌"
        print(f"{status} {result['test_case']}")
        if not result['success']:
            print(f"   Error: {result['error']}")

    return results

def analyze_mindmap_results(mindmap: dict, test_case: dict) -> dict:
    """Analyze the generated mindmap results"""

    nodes = mindmap.get('nodes', [])
    relationships = mindmap.get('relationships', [])
    study_guidance = mindmap.get('study_guidance', {})

    # Count nodes by level
    level_counts = {}
    sample_nodes = []

    for node in nodes:
        level = node.get('level', 0)
        level_counts[level] = level_counts.get(level, 0) + 1
        if len(sample_nodes) < 5:
            sample_nodes.append(node.get('title', 'Unknown'))

    # Check cognitive load optimization
    cognitive_load = mindmap.get('cognitive_load_level', 'moderate')
    expected_limits = {
        'minimal': (4, 8),    # (main, total)
        'moderate': (6, 15),
        'complex': (8, 25),
        'expert': (10, 40)
    }

    expected_main, expected_total = expected_limits.get(cognitive_load, (6, 15))
    actual_main = level_counts.get(1, 0) + level_counts.get(0, 0)  # Primary + root
    actual_total = len(nodes)

    # Check learning features
    optimizations = mindmap.get('learning_optimizations', {})
    study_phases = study_guidance.get('study_phases', [])

    analysis = {
        'concept_count': len(nodes),
        'relationship_count': len(relationships),
        'level_distribution': level_counts,
        'cognitive_load_level': cognitive_load,
        'within_cognitive_limits': actual_total <= expected_total and actual_main <= expected_main,
        'sample_nodes': sample_nodes,
        'has_study_guidance': len(study_phases) > 0,
        'has_learning_optimizations': len(optimizations) > 0,
        'has_ai_hints': any(node.get('ai_hint') for node in nodes),
        'has_study_actions': any(node.get('study_actions') for node in nodes),
        'has_visual_styling': any(node.get('visual_style') for node in nodes)
    }

    return analysis

async def test_cognitive_load_levels():
    """Test different cognitive load levels with same content"""
    print("\n🎯 Testing Cognitive Load Levels")
    print("=" * 30)

    service = EnhancedMindmapService()
    topic = "Photosynthesis Basics"
    context = """
    Photosynthesis is the process plants use to convert light energy into chemical energy.
    Chlorophyll captures sunlight in the leaves.
    Carbon dioxide enters through stomata.
    Water is absorbed through roots.
    Glucose and oxygen are produced as products.
    The process occurs in chloroplasts.
    Light-dependent reactions capture energy.
    Calvin cycle fixes carbon.
    """

    levels = ["minimal", "moderate", "complex"]
    results = {}

    for level in levels:
        print(f"\nTesting {level} cognitive load...")

        try:
            mindmap = await service.generate_enhanced_mindmap(
                topic=topic,
                context_text=context,
                course_id="test_course",
                book_id="test_book",
                cognitive_load_level=level
            )

            results[level] = {
                'success': True,
                'node_count': len(mindmap.get('nodes', [])),
                'relationship_count': len(mindmap.get('relationships', [])),
                'cognitive_load_applied': mindmap.get('cognitive_load_level')
            }

            print(f"  Nodes: {results[level]['node_count']}")
            print(f"  Relationships: {results[level]['relationship_count']}")

        except Exception as e:
            print(f"  Error: {e}")
            results[level] = {'success': False, 'error': str(e)}

    return results

async def test_knowledge_types():
    """Test different knowledge types"""
    print("\n🔬 Testing Knowledge Types")
    print("=" * 30)

    service = EnhancedMindmapService()

    # Test cases for different knowledge types
    knowledge_tests = [
        {
            "type": "factual",
            "topic": "Fatti Storici del XX Secolo",
            "context": "La Seconda Guerra Mondiale è iniziata nel 1939. Il trattato di Versailles è stato firmato nel 1919. La caduta del Muro di Berlino è avvenuta nel 1989."
        },
        {
            "type": "conceptual",
            "topic": "Teorie dell'Apprendimento",
            "context": "Il costruttivismo mette in evidenza il ruolo attivo dello studente. Il cognitivismo si concentra sui processi mentali. Il comportamentismo enfatizza gli stimoli esterni."
        },
        {
            "type": "procedural",
            "topic": "Metodo Scientifico",
            "context": "Si parte da un'osservazione. Si formula un'ipotesi. Si progetta un esperimento. Si raccolgono dati. Si analizzano i risultati. Si traggono conclusioni."
        },
        {
            "type": "metacognitive",
            "topic": "Strategie di Auto-regolazione",
            "context": "Pianifica il tempo di studio. Monitora la comprensione. Valuta i progressi. Adatta le strategie. Rifletti sul processo di apprendimento."
        }
    ]

    results = {}

    for test in knowledge_tests:
        print(f"\nTesting {test['type']} knowledge...")

        try:
            mindmap = await service.generate_enhanced_mindmap(
                topic=test['topic'],
                context_text=test['context'],
                course_id="test_course",
                book_id="test_book",
                knowledge_type=test['type']
            )

            results[test['type']] = {
                'success': True,
                'knowledge_type_applied': mindmap.get('knowledge_type'),
                'node_count': len(mindmap.get('nodes', [])),
                'has_study_guidance': bool(mindmap.get('study_guidance')),
                'has_optimizations': bool(mindmap.get('learning_optimizations'))
            }

            print(f"  Success: {results[test['type']]['knowledge_type_applied']}")
            print(f"  Nodes: {results[test['type']]['node_count']}")

        except Exception as e:
            print(f"  Error: {e}")
            results[test['type']] = {'success': False, 'error': str(e)}

    return results

def print_service_capabilities():
    """Print service capabilities and features"""
    print("\n🚀 Enhanced Mindmap Service Capabilities")
    print("=" * 50)

    capabilities = {
        "Cognitive Load Theory": ["Minimal", "Moderate", "Complex", "Expert"],
        "Knowledge Types": ["Factual", "Conceptual", "Procedural", "Metacognitive"],
        "Relationship Modeling": ["Hierarchical", "Causal", "Comparative", "Temporal", "Associative"],
        "Learning Science Integration": [
            "Dual Coding",
            "Cognitive Scaffolding",
            "Metacognitive Prompts",
            "Retrieval Practice",
            "Spaced Repetition"
        ],
        "GLM-4.6 Features": [
            "Advanced Concept Extraction",
            "Relationship Modeling",
            "Hierarchical Organization",
            "Cognitive Optimization"
        ]
    }

    for category, features in capabilities.items():
        print(f"\n📚 {category}:")
        for feature in features:
            print(f"   ✅ {feature}")

async def main():
    """Main test execution"""
    print("🧠 Enhanced Mindmap Service Test Suite")
    print("Testing GLM-4.6 Integration with Cognitive Load Theory")
    print("=" * 60)

    try:
        # Print capabilities
        print_service_capabilities()

        # Run main tests
        main_results = await test_enhanced_mindmap_generation()

        # Test cognitive load levels
        cognitive_results = await test_cognitive_load_levels()

        # Test knowledge types
        knowledge_results = await test_knowledge_types()

        # Final summary
        print("\n" + "=" * 60)
        print("🏁 FINAL TEST SUMMARY")
        print("=" * 60)

        main_success = sum(1 for r in main_results if r['success'])
        main_total = len(main_results)

        cognitive_success = sum(1 for r in cognitive_results.values() if r.get('success', False))
        cognitive_total = len(cognitive_results)

        knowledge_success = sum(1 for r in knowledge_results.values() if r.get('success', False))
        knowledge_total = len(knowledge_results)

        print(f"Main Generation Tests: {main_success}/{main_total} passed")
        print(f"Cognitive Load Tests: {cognitive_success}/{cognitive_total} passed")
        print(f"Knowledge Type Tests: {knowledge_success}/{knowledge_total} passed")

        total_passed = main_success + cognitive_success + knowledge_success
        total_tests = main_total + cognitive_total + knowledge_total
        overall_success_rate = (total_passed / total_tests) * 100

        print(f"\nOverall Success Rate: {overall_success_rate:.1f}%")

        if overall_success_rate >= 80:
            print("🎉 EXCELLENT: Enhanced mindmap service is working very well!")
        elif overall_success_rate >= 60:
            print("✅ GOOD: Enhanced mindmap service is mostly functional")
        else:
            print("⚠️  NEEDS WORK: Enhanced mindmap service has significant issues")

        return overall_success_rate >= 60

    except Exception as e:
        print(f"❌ CRITICAL ERROR: {str(e)}")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)