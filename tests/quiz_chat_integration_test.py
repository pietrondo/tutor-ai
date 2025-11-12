#!/usr/bin/env python3
"""
Test Suite for Quiz Chat Integration
Tests the automatic quiz detection and generation from chat messages
"""

import asyncio
import aiohttp
import json
from typing import Dict, Any, List

# Configuration
API_BASE_URL = "http://localhost:8000"
TEST_COURSE_ID = "test-course-123"

# Quiz intent test cases (Italian)
QUIZ_INTENT_TESTS = [
    # High confidence tests
    {
        "message": "proponimi un quiz sulla fotosintesi",
        "expected": {
            "wants_quiz": True,
            "confidence": 0.9,
            "topic": "fotosintesi",
            "difficulty": "medium",
            "num_questions": 5
        }
    },
    {
        "message": "voglio fare un quiz facile su Darwin",
        "expected": {
            "wants_quiz": True,
            "confidence": 0.9,
            "topic": "Darwin",
            "difficulty": "easy",
            "num_questions": 5
        }
    },
    {
        "message": "facciamo un quiz difficile con 3 domande sulla matematica",
        "expected": {
            "wants_quiz": True,
            "confidence": 0.9,
            "topic": "matematica",
            "difficulty": "hard",
            "num_questions": 3
        }
    },
    # Medium confidence tests
    {
        "message": "un test sulla storia contemporanea?",
        "expected": {
            "wants_quiz": True,
            "confidence": 0.7,
            "topic": "storia contemporanea",
            "difficulty": "medium",
            "num_questions": 5
        }
    },
    {
        "message": "posso avere un quiz su questo argomento?",
        "expected": {
            "wants_quiz": True,
            "confidence": 0.7,
            "difficulty": "medium",
            "num_questions": 5
        }
    },
    # Negative tests (no quiz intent)
    {
        "message": "spiegami la fotosintesi",
        "expected": {
            "wants_quiz": False,
            "confidence": 0.0
        }
    },
    {
        "message": "cos'è l'evoluzione?",
        "expected": {
            "wants_quiz": False,
            "confidence": 0.0
        }
    },
    {
        "message": "aiutami con i compiti di matematica",
        "expected": {
            "wants_quiz": False,
            "confidence": 0.0
        }
    }
]

class QuizChatIntegrationTester:
    def __init__(self):
        self.session = None
        self.results = []

    async def setup_session(self):
        """Setup a test chat session"""
        try:
            async with aiohttp.ClientSession() as session:
                # Create session
                async with session.post(
                    f"{API_BASE_URL}/course-chat/{TEST_COURSE_ID}/sessions",
                    json={}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        self.session = data["session"]
                        print(f"✅ Created test session: {self.session['id']}")
                        return True
                    else:
                        print(f"❌ Failed to create session: {response.status}")
                        return False
        except Exception as e:
            print(f"❌ Error setting up session: {e}")
            return False

    async def test_quiz_intent_detection(self):
        """Test quiz intent detection directly"""
        print("\n🧪 Testing Quiz Intent Detection...")

        try:
            async with aiohttp.ClientSession() as session:
                for i, test_case in enumerate(QUIZ_INTENT_TESTS):
                    print(f"\n  Test {i+1}: \"{test_case['message']}\"")

                    # Send message to course-chat endpoint
                    async with session.post(
                        f"{API_BASE_URL}/course-chat",
                        json={
                            "course_id": TEST_COURSE_ID,
                            "session_id": self.session["id"] if self.session else None,
                            "message": test_case["message"],
                            "use_enhanced_rag": True
                        }
                    ) as response:
                        if response.status == 200:
                            data = await response.json()

                            # Check if quiz suggestion was generated
                            quiz_suggestion = data.get("quiz_suggestion")
                            expected = test_case["expected"]

                            if expected["wants_quiz"]:
                                if quiz_suggestion:
                                    confidence_match = abs(quiz_suggestion["confidence"] - expected["confidence"]) <= 0.1
                                    topic_match = expected["topic"] == "" or expected["topic"].lower() in quiz_suggestion["topic"].lower()
                                    difficulty_match = quiz_suggestion["difficulty"] == expected["difficulty"]
                                    num_questions_match = quiz_suggestion["num_questions"] == expected["num_questions"]

                                    if confidence_match and topic_match and difficulty_match and num_questions_match:
                                        print(f"    ✅ Quiz detected correctly (confidence: {quiz_suggestion['confidence']:.1f})")
                                        self.results.append({
                                            "test": i+1,
                                            "message": test_case["message"],
                                            "status": "PASS",
                                            "detected_confidence": quiz_suggestion["confidence"]
                                        })
                                    else:
                                        print(f"    ⚠️  Quiz detected but parameters mismatch")
                                        print(f"       Expected: confidence={expected['confidence']}, topic='{expected['topic']}'")
                                        print(f"       Got: confidence={quiz_suggestion['confidence']}, topic='{quiz_suggestion['topic']}'")
                                        self.results.append({
                                            "test": i+1,
                                            "message": test_case["message"],
                                            "status": "PARTIAL",
                                            "expected": expected,
                                            "got": quiz_suggestion
                                        })
                                else:
                                    print(f"    ❌ Expected quiz but none detected")
                                    self.results.append({
                                        "test": i+1,
                                        "message": test_case["message"],
                                        "status": "FAIL",
                                        "expected": expected,
                                        "got": None
                                    })
                            else:
                                if quiz_suggestion is None:
                                    print(f"    ✅ Correctly no quiz detected")
                                    self.results.append({
                                        "test": i+1,
                                        "message": test_case["message"],
                                        "status": "PASS",
                                        "expected": False,
                                        "got": None
                                    })
                                else:
                                    print(f"    ❌ Unexpected quiz detected")
                                    self.results.append({
                                        "test": i+1,
                                        "message": test_case["message"],
                                        "status": "FAIL",
                                        "expected": False,
                                        "got": quiz_suggestion
                                    })
                        else:
                            print(f"    ❌ API request failed: {response.status}")
                            self.results.append({
                                "test": i+1,
                                "message": test_case["message"],
                                "status": "ERROR",
                                "http_status": response.status
                            })

                        # Small delay between requests
                        await asyncio.sleep(0.5)

        except Exception as e:
            print(f"❌ Error testing quiz intent: {e}")

    async def test_quiz_generation_flow(self):
        """Test complete quiz generation flow"""
        print("\n🔄 Testing Complete Quiz Generation Flow...")

        try:
            async with aiohttp.ClientSession() as session:
                # Send a clear quiz request
                quiz_message = "proponimi un quiz su italiano con 4 domande facili"

                async with session.post(
                    f"{API_BASE_URL}/course-chat",
                    json={
                        "course_id": TEST_COURSE_ID,
                        "session_id": self.session["id"] if self.session else None,
                        "message": quiz_message,
                        "use_enhanced_rag": True
                    }
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        quiz_suggestion = data.get("quiz_suggestion")

                        if quiz_suggestion:
                            print(f"    ✅ Quiz suggestion generated")
                            print(f"       Topic: {quiz_suggestion['topic']}")
                            print(f"       Questions: {quiz_suggestion['num_questions']}")
                            print(f"       Difficulty: {quiz_suggestion['difficulty']}")
                            print(f"       Confidence: {quiz_suggestion['confidence']:.1f}")

                            # Now test actual quiz generation
                            print("    🎯 Testing actual quiz generation...")

                            async with session.post(
                                f"{API_BASE_URL}/quiz",
                                json={
                                    "course_id": TEST_COURSE_ID,
                                    "topic": quiz_suggestion["topic"],
                                    "difficulty": quiz_suggestion["difficulty"],
                                    "num_questions": quiz_suggestion["num_questions"]
                                }
                            ) as quiz_response:
                                if quiz_response.status == 200:
                                    quiz_data = await quiz_response.json()
                                    quiz = quiz_data.get("quiz")

                                    if quiz and quiz.get("questions"):
                                        print(f"    ✅ Quiz generated with {len(quiz['questions'])} questions")

                                        # Validate quiz structure
                                        for i, question in enumerate(quiz["questions"][:2]):  # Check first 2 questions
                                            if all(key in question for key in ["question", "options", "correct", "explanation"]):
                                                print(f"       Question {i+1}: ✅ Valid structure")
                                            else:
                                                print(f"       Question {i+1}: ❌ Invalid structure")

                                        return True
                                    else:
                                        print(f"    ❌ Quiz generated but no questions found")
                                        return False
                                else:
                                    print(f"    ❌ Quiz generation failed: {quiz_response.status}")
                                    return False
                        else:
                            print(f"    ❌ No quiz suggestion generated")
                            return False
                    else:
                        print(f"    ❌ Chat request failed: {response.status}")
                        return False

        except Exception as e:
            print(f"❌ Error testing quiz flow: {e}")
            return False

    def print_summary(self):
        """Print test results summary"""
        print("\n📊 Test Results Summary")
        print("=" * 50)

        total_tests = len(self.results)
        passed_tests = len([r for r in self.results if r["status"] == "PASS"])
        partial_tests = len([r for r in self.results if r["status"] == "PARTIAL"])
        failed_tests = len([r for r in self.results if r["status"] in ["FAIL", "ERROR"]])

        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"⚠️  Partial: {partial_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests / total_tests * 100):.1f}%")

        if failed_tests > 0:
            print("\n❌ Failed Tests:")
            for result in self.results:
                if result["status"] in ["FAIL", "ERROR"]:
                    print(f"   Test {result['test']}: {result['message']}")

        print("\n🎯 Integration Status:", "✅ WORKING" if passed_tests >= total_tests * 0.8 else "❌ NEEDS FIXES")

async def main():
    """Main test runner"""
    print("🚀 Tutor AI - Quiz Chat Integration Test Suite")
    print("=" * 50)

    tester = QuizChatIntegrationTester()

    # Setup test session
    if not await tester.setup_session():
        print("❌ Cannot proceed without valid session")
        return

    # Run tests
    await tester.test_quiz_intent_detection()
    await tester.test_quiz_generation_flow()

    # Print summary
    tester.print_summary()

if __name__ == "__main__":
    asyncio.run(main())