#!/usr/bin/env python3
"""
Integration Test for Unified Learning System
Tests the integration between concepts, quizzes, and mindmaps
"""

import asyncio
import json
import requests
import time
from typing import Dict, Any, List

class UnifiedLearningIntegrationTest:
    def __init__(self, base_url: str = "http://localhost:8000", frontend_url: str = "http://localhost:3001"):
        self.base_url = base_url
        self.frontend_url = frontend_url
        self.test_results = []
        self.created_resources = []

    def log_result(self, test_name: str, success: bool, message: str = "", data: Any = None):
        """Log a test result"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "timestamp": time.time(),
            "data": data
        }
        self.test_results.append(result)

        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if message:
            print(f"     {message}")

    async def test_backend_health(self):
        """Test if backend is running"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            success = response.status_code == 200
            self.log_result(
                "Backend Health Check",
                success,
                f"Status code: {response.status_code}" if success else "Backend not responding",
                response.json() if success else None
            )
            return success
        except Exception as e:
            self.log_result("Backend Health Check", False, f"Connection error: {str(e)}")
            return False

    async def test_frontend_health(self):
        """Test if frontend is running"""
        try:
            response = requests.get(f"{self.frontend_url}", timeout=5)
            success = response.status_code == 200
            self.log_result(
                "Frontend Health Check",
                success,
                f"Status code: {response.status_code}" if success else "Frontend not responding"
            )
            return success
        except Exception as e:
            self.log_result("Frontend Health Check", False, f"Connection error: {str(e)}")
            return False

    async def test_unified_endpoints_available(self):
        """Test if unified learning endpoints are available"""
        endpoints = [
            "/api/unified-learning/view/course/test",
            "/api/unified-learning/quiz/create",
            "/api/unified-learning/quiz/course/test",
            "/api/unified-learning/pathway/test/user/demo",
            "/api/unified-learning/status/course/test"
        ]

        for endpoint in endpoints:
            try:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=5)
                # We expect 404 or 422 for missing course data, but not 500
                success = response.status_code in [200, 404, 422]
                self.log_result(
                    f"Endpoint {endpoint}",
                    success,
                    f"Status code: {response.status_code}"
                )
            except Exception as e:
                self.log_result(f"Endpoint {endpoint}", False, f"Error: {str(e)}")

    async def test_concept_creation(self):
        """Test concept creation with automatic quiz generation"""
        test_course_id = "test_course_integration"
        test_concept_data = {
            "name": "Test Concept Integration",
            "summary": "This is a test concept for integration testing",
            "recommended_minutes": 25,
            "auto_generate_quiz": True
        }

        try:
            response = requests.post(
                f"{self.base_url}/api/unified-learning/concept/create",
                json={
                    "course_id": test_course_id,
                    **test_concept_data
                },
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    concept_id = data["data"]["concept"]["id"]
                    generated_quizzes = data["data"]["generated_quizzes"]

                    self.created_resources.append({
                        "type": "concept",
                        "id": concept_id,
                        "course_id": test_course_id
                    })

                    for quiz_id in generated_quizzes:
                        self.created_resources.append({
                            "type": "quiz",
                            "id": quiz_id,
                            "course_id": test_course_id
                        })

                    self.log_result(
                        "Concept Creation with Quiz",
                        True,
                        f"Created concept with {len(generated_quizzes)} quizzes",
                        {
                            "concept_id": concept_id,
                            "quizzes_generated": len(generated_quizzes)
                        }
                    )
                    return True
                else:
                    self.log_result("Concept Creation with Quiz", False, data.get("message", "Unknown error"))
                    return False
            else:
                self.log_result(
                    "Concept Creation with Quiz",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return False

        except Exception as e:
            self.log_result("Concept Creation with Quiz", False, f"Exception: {str(e)}")
            return False

    async def test_quiz_creation_and_linking(self):
        """Test persistent quiz creation and concept linking"""
        test_course_id = "test_course_integration"
        test_concept_id = "test_concept_quiz_link"

        try:
            # First create a concept
            concept_response = requests.post(
                f"{self.base_url}/api/unified-learning/concept/create",
                json={
                    "course_id": test_course_id,
                    "name": "Test Concept for Quiz Linking",
                    "summary": "This concept will be linked to quizzes",
                    "auto_generate_quiz": False
                },
                timeout=10
            )

            if not concept_response.ok:
                self.log_result("Quiz Creation and Linking", False, "Failed to create test concept")
                return False

            concept_data = concept_response.json()
            concept_id = concept_data["data"]["concept"]["id"]

            # Now create a quiz linked to this concept
            quiz_response = requests.post(
                f"{self.base_url}/api/unified-learning/quiz/create",
                json={
                    "course_id": test_course_id,
                    "topic": "Test Quiz Topic",
                    "difficulty": "medium",
                    "num_questions": 3,
                    "linked_concept_ids": [concept_id],
                    "title": "Test Integration Quiz"
                },
                timeout=15
            )

            if quiz_response.status_code == 200:
                quiz_data = quiz_response.json()
                quiz_id = quiz_data["data"]["quiz"]["id"]
                linked_concepts = quiz_data["data"]["linked_concepts"]

                self.created_resources.extend([
                    {"type": "concept", "id": concept_id, "course_id": test_course_id},
                    {"type": "quiz", "id": quiz_id, "course_id": test_course_id}
                ])

                success = concept_id in linked_concepts
                self.log_result(
                    "Quiz Creation and Linking",
                    success,
                    f"Quiz linked to {len(linked_concepts)} concepts" if success else "Quiz not properly linked",
                    {
                        "quiz_id": quiz_id,
                        "concept_id": concept_id,
                        "linked_concepts": linked_concepts
                    }
                )
                return success
            else:
                self.log_result(
                    "Quiz Creation and Linking",
                    False,
                    f"Quiz creation failed: HTTP {quiz_response.status_code}"
                )
                return False

        except Exception as e:
            self.log_result("Quiz Creation and Linking", False, f"Exception: {str(e)}")
            return False

    async def test_unified_view_retrieval(self):
        """Test unified learning view retrieval"""
        test_course_id = "test_course_integration"

        try:
            response = requests.get(
                f"{self.base_url}/api/unified-learning/view/course/{test_course_id}?user_id=test_user",
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                view_data = data.get("data", {})

                # Check if the view contains expected fields
                required_fields = ["course_info", "concepts", "quizzes", "mindmaps", "connections"]
                missing_fields = [field for field in required_fields if field not in view_data]

                success = len(missing_fields) == 0
                self.log_result(
                    "Unified View Retrieval",
                    success,
                    f"Retrieved view with {len(view_data.get('concepts', {}))} concepts, {len(view_data.get('quizzes', {}))} quizzes" if success else f"Missing fields: {missing_fields}",
                    {
                        "concepts_count": len(view_data.get("concepts", {})),
                        "quizzes_count": len(view_data.get("quizzes", {})),
                        "mindmaps_count": len(view_data.get("mindmaps", {})),
                        "has_connections": bool(view_data.get("connections"))
                    }
                )
                return success
            else:
                self.log_result(
                    "Unified View Retrieval",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return False

        except Exception as e:
            self.log_result("Unified View Retrieval", False, f"Exception: {str(e)}")
            return False

    async def test_learning_pathway_generation(self):
        """Test personalized learning pathway generation"""
        test_course_id = "test_course_integration"
        test_user_id = "test_user_integration"

        try:
            response = requests.get(
                f"{self.base_url}/api/unified-learning/pathway/{test_course_id}/user/{test_user_id}",
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                pathway = data.get("data", {})

                # Check if pathway contains expected structure
                required_sections = ["current_focus", "next_steps", "review_needed", "ready_for_mastery"]
                missing_sections = [section for section in required_sections if section not in pathway]

                success = len(missing_sections) == 0
                self.log_result(
                    "Learning Pathway Generation",
                    success,
                    f"Generated pathway with {len(pathway.get('current_focus', []))} focus areas" if success else f"Missing sections: {missing_sections}",
                    {
                        "current_focus_count": len(pathway.get("current_focus", [])),
                        "next_steps_count": len(pathway.get("next_steps", [])),
                        "review_needed_count": len(pathway.get("review_needed", []))
                    }
                )
                return success
            else:
                self.log_result(
                    "Learning Pathway Generation",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return False

        except Exception as e:
            self.log_result("Learning Pathway Generation", False, f"Exception: {str(e)}")
            return False

    async def test_cross_referencing_consistency(self):
        """Test cross-referencing consistency between concepts, quizzes, and mindmaps"""
        test_course_id = "test_course_integration"

        try:
            # Get unified view
            view_response = requests.get(
                f"{self.base_url}/api/unified-learning/view/course/{test_course_id}?user_id=test_user",
                timeout=10
            )

            if not view_response.ok:
                self.log_result("Cross-Referencing Consistency", False, "Failed to get unified view")
                return False

            view_data = view_response.json()["data"]
            connections = view_data.get("connections", {})
            concepts = view_data.get("concepts", {})
            quizzes = view_data.get("quizzes", {})

            # Check consistency of cross-references
            inconsistencies = []

            # Check concept_to_quizzes consistency
            for concept_id, quiz_ids in connections.get("concept_to_quizzes", {}).items():
                if concept_id not in concepts:
                    inconsistencies.append(f"concept_to_quizzes references non-existent concept: {concept_id}")
                for quiz_id in quiz_ids:
                    if quiz_id not in quizzes:
                        inconsistencies.append(f"concept_to_quizzes references non-existent quiz: {quiz_id}")

            # Check quiz_to_concepts consistency
            for quiz_id, concept_ids in connections.get("quiz_to_concepts", {}).items():
                if quiz_id not in quizzes:
                    inconsistencies.append(f"quiz_to_concepts references non-existent quiz: {quiz_id}")
                for concept_id in concept_ids:
                    if concept_id not in concepts:
                        inconsistencies.append(f"quiz_to_concepts references non-existent concept: {concept_id}")

            # Check bidirectional consistency
            for concept_id, quiz_ids in connections.get("concept_to_quizzes", {}).items():
                for quiz_id in quiz_ids:
                    reverse_refs = connections.get("quiz_to_concepts", {}).get(quiz_id, [])
                    if concept_id not in reverse_refs:
                        inconsistencies.append(f"Missing reverse reference: quiz {quiz_id} -> concept {concept_id}")

            success = len(inconsistencies) == 0
            self.log_result(
                "Cross-Referencing Consistency",
                success,
                f"Cross-references are consistent" if success else f"Found {len(inconsistencies)} inconsistencies",
                {
                    "inconsistencies": inconsistencies[:5],  # Show first 5
                    "total_inconsistencies": len(inconsistencies)
                }
            )
            return success

        except Exception as e:
            self.log_result("Cross-Referencing Consistency", False, f"Exception: {str(e)}")
            return False

    async def test_data_persistence(self):
        """Test that created data persists across API calls"""
        test_course_id = "test_course_integration"

        try:
            # Create a concept
            create_response = requests.post(
                f"{self.base_url}/api/unified-learning/concept/create",
                json={
                    "course_id": test_course_id,
                    "name": "Persistence Test Concept",
                    "summary": "Testing data persistence",
                    "auto_generate_quiz": True
                },
                timeout=10
            )

            if not create_response.ok:
                self.log_result("Data Persistence", False, "Failed to create test concept")
                return False

            create_data = create_response.json()
            concept_id = create_data["data"]["concept"]["id"]
            generated_quizzes = create_data["data"]["generated_quizzes"]

            # Wait a moment
            await asyncio.sleep(1)

            # Check if data persists in unified view
            view_response = requests.get(
                f"{self.base_url}/api/unified-learning/view/course/{test_course_id}?user_id=test_user",
                timeout=10
            )

            if view_response.ok:
                view_data = view_response.json()["data"]
                persisted_concept = view_data.get("concepts", {}).get(concept_id)
                persisted_quizzes = view_data.get("quizzes", {})

                concept_persisted = persisted_concept is not None
                quizzes_persisted = all(quiz_id in persisted_quizzes for quiz_id in generated_quizzes)

                success = concept_persisted and quizzes_persisted
                self.log_result(
                    "Data Persistence",
                    success,
                    f"Concept persisted: {concept_persisted}, Quizzes persisted: {quizzes_persisted}" if success else "Data persistence failed",
                    {
                        "concept_id": concept_id,
                        "concept_persisted": concept_persisted,
                        "generated_quizzes": len(generated_quizzes),
                        "quizzes_persisted": len([q for q in generated_quizzes if q in persisted_quizzes])
                    }
                )
                return success
            else:
                self.log_result("Data Persistence", False, "Failed to retrieve unified view")
                return False

        except Exception as e:
            self.log_result("Data Persistence", False, f"Exception: {str(e)}")
            return False

    async def cleanup_test_resources(self):
        """Clean up test resources (if cleanup endpoints were available)"""
        # Note: This would require implementing cleanup endpoints
        # For now, we just log what we created
        if self.created_resources:
            print(f"\n📝 Created {len(self.created_resources)} test resources:")
            for resource in self.created_resources:
                print(f"   - {resource['type'].title()}: {resource['id']} (course: {resource['course_id']})")

    async def run_all_tests(self):
        """Run all integration tests"""
        print("🧪 Running Unified Learning Integration Tests")
        print("=" * 50)

        # Basic health checks
        backend_healthy = await self.test_backend_health()
        await self.test_frontend_health()

        if not backend_healthy:
            print("\n❌ Backend is not running. Skipping remaining tests.")
            return False

        # API availability tests
        await self.test_unified_endpoints_available()

        # Core functionality tests
        await self.test_concept_creation()
        await self.test_quiz_creation_and_linking()
        await self.test_unified_view_retrieval()
        await self.test_learning_pathway_generation()
        await self.test_cross_referencing_consistency()
        await self.test_data_persistence()

        # Cleanup
        await self.cleanup_test_resources()

        # Summary
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["success"]])
        failed_tests = total_tests - passed_tests

        print("\n" + "=" * 50)
        print(f"📊 Test Results: {passed_tests}/{total_tests} passed")

        if failed_tests > 0:
            print(f"❌ {failed_tests} tests failed:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   - {result['test']}: {result['message']}")
            return False
        else:
            print("✅ All tests passed!")
            return True

    def save_test_report(self, filename: str = "unified_learning_test_report.json"):
        """Save test results to a JSON file"""
        report = {
            "test_run": {
                "timestamp": time.time(),
                "total_tests": len(self.test_results),
                "passed_tests": len([r for r in self.test_results if r["success"]]),
                "failed_tests": len([r for r in self.test_results if not r["success"]])
            },
            "results": self.test_results,
            "created_resources": self.created_resources
        }

        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"📄 Test report saved to {filename}")


async def main():
    """Main function to run integration tests"""
    import sys

    # Allow custom base URLs
    backend_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    frontend_url = sys.argv[2] if len(sys.argv) > 2 else "http://localhost:3001"

    test_runner = UnifiedLearningIntegrationTest(backend_url, frontend_url)

    success = await test_runner.run_all_tests()
    test_runner.save_test_report()

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())