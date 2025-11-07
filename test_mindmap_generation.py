#!/usr/bin/env python3
"""
Test script for mindmap generation functionality
Tests with random local books to verify the system works correctly
"""

import asyncio
import json
import random
import sys
import httpx
from datetime import datetime
from typing import Dict, Any, List

# Configuration
BACKEND_URL = "http://localhost:8000"

class MindmapTester:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=300.0)  # 5 minutes timeout

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    async def get_courses(self) -> List[Dict[str, Any]]:
        """Get all available courses"""
        try:
            response = await self.client.get(f"{BACKEND_URL}/courses")
            if response.status_code == 200:
                data = response.json()
                return data.get("courses", [])
            else:
                print(f"❌ Error getting courses: {response.status_code}")
                return []
        except Exception as e:
            print(f"❌ Exception getting courses: {e}")
            return []

    async def get_books(self, course_id: str) -> List[Dict[str, Any]]:
        """Get all books for a course"""
        try:
            response = await self.client.get(f"{BACKEND_URL}/courses/{course_id}/books")
            if response.status_code == 200:
                data = response.json()
                return data.get("books", [])
            else:
                print(f"❌ Error getting books for course {course_id}: {response.status_code}")
                return []
        except Exception as e:
            print(f"❌ Exception getting books: {e}")
            return []

    async def test_mindmap_generation(self, course_id: str, book_id: str, book_title: str) -> Dict[str, Any]:
        """Test mindmap generation for a specific book"""
        print(f"\n🧠 Testing mindmap generation for: {book_title}")
        print(f"   Course ID: {course_id}")
        print(f"   Book ID: {book_id}")

        test_data = {
            "course_id": course_id,
            "book_id": book_id,
            "topic": f"Mappa concettuale di {book_title}",
            "focus_areas": ["capitoli principali", "concetti chiave", "temi centrali"]
        }

        try:
            print("   📤 Sending request...")
            start_time = datetime.now()

            response = await self.client.post(
                f"{BACKEND_URL}/mindmap",
                json=test_data
            )

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            print(f"   ⏱️  Request completed in {duration:.2f} seconds")
            print(f"   📊 Status code: {response.status_code}")

            if response.status_code == 200:
                try:
                    result = response.json()

                    # Validate response structure
                    success = result.get("success", False)
                    mindmap = result.get("mindmap")
                    markdown = result.get("markdown", "")
                    references = result.get("references", [])
                    sources = result.get("sources", [])

                    print(f"   ✅ Success: {success}")

                    if success and mindmap:
                        # Validate mindmap structure
                        title = mindmap.get("title", "No title")
                        overview = mindmap.get("overview", "")
                        nodes = mindmap.get("nodes", [])
                        study_plan = mindmap.get("study_plan", [])

                        print(f"   📋 Mindmap title: {title}")
                        print(f"   📝 Overview length: {len(overview)} chars")
                        print(f"   🌊 Number of nodes: {len(nodes)}")
                        print(f"   📚 Study plan phases: {len(study_plan)}")
                        print(f"   📖 References: {len(references)}")
                        print(f"   🔍 Sources used: {len(sources)}")

                        # Validate nodes structure
                        valid_nodes = 0
                        for node in nodes:
                            if "title" in node and "id" in node:
                                valid_nodes += 1

                        print(f"   ✅ Valid nodes structure: {valid_nodes}/{len(nodes)}")

                        if len(markdown) > 0:
                            print(f"   📄 Markdown generated: {len(markdown)} chars")

                        return {
                            "success": True,
                            "book_title": book_title,
                            "duration": duration,
                            "nodes_count": len(nodes),
                            "has_markdown": len(markdown) > 0,
                            "references_count": len(references),
                            "sources_count": len(sources)
                        }
                    else:
                        print("   ❌ Response indicated failure or missing mindmap data")
                        print(f"   📄 Response preview: {str(result)[:200]}...")
                        return {
                            "success": False,
                            "book_title": book_title,
                            "error": "Invalid response structure",
                            "response_preview": str(result)[:200]
                        }

                except json.JSONDecodeError as e:
                    print(f"   ❌ JSON decode error: {e}")
                    print(f"   📄 Raw response: {response.text[:200]}...")
                    return {
                        "success": False,
                        "book_title": book_title,
                        "error": f"JSON decode error: {e}",
                        "raw_response": response.text[:500]
                    }
            else:
                print(f"   ❌ HTTP error: {response.status_code}")
                print(f"   📄 Error response: {response.text[:200]}...")

                # Try to parse error details
                try:
                    error_data = response.json()
                    error_detail = error_data.get("detail", "Unknown error")
                    print(f"   🔍 Error detail: {error_detail}")
                except:
                    pass

                return {
                    "success": False,
                    "book_title": book_title,
                    "error": f"HTTP {response.status_code}",
                    "error_response": response.text[:200]
                }

        except httpx.TimeoutException:
            print(f"   ❌ Request timeout after 5 minutes - backend is too slow")
            return {
                "success": False,
                "book_title": book_title,
                "error": "Request timeout - backend taking too long to process"
            }
        except Exception as e:
            print(f"   ❌ Exception during request: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "book_title": book_title,
                "error": f"Exception {type(e).__name__}: {e}"
            }

    async def run_random_test(self, num_tests: int = 3):
        """Run mindmap generation tests on random books"""
        print("🚀 Starting Mindmap Generation Test Suite")
        print("=" * 50)

        # Get available courses
        print("📚 Fetching available courses...")
        courses = await self.get_courses()

        if not courses:
            print("❌ No courses found. Make sure the backend is running and has data.")
            return False

        print(f"✅ Found {len(courses)} courses")

        # Get all books from all courses
        all_books = []
        for course in courses:
            print(f"   📖 Getting books for course: {course.get('name', 'Unknown')}")
            books = await self.get_books(course["id"])
            for book in books:
                all_books.append({
                    "course_id": course["id"],
                    "course_name": course.get("name", "Unknown"),
                    "book_id": book["id"],
                    "book_title": book.get("title", "Unknown"),
                    "author": book.get("author", "Unknown")
                })

        if not all_books:
            print("❌ No books found in any course.")
            return False

        print(f"✅ Found {len(all_books)} total books")

        # Select random books for testing
        test_count = min(num_tests, len(all_books))
        test_books = random.sample(all_books, test_count)

        print(f"\n🎯 Testing {test_count} random books:")
        for i, book in enumerate(test_books, 1):
            print(f"   {i}. {book['book_title']} ({book['course_name']})")

        # Run tests
        results = []
        for i, book in enumerate(test_books, 1):
            print(f"\n{'='*20} Test {i}/{test_count} {'='*20}")
            result = await self.test_mindmap_generation(
                book["course_id"],
                book["book_id"],
                book["book_title"]
            )
            results.append(result)

        # Summary
        print(f"\n{'='*20} TEST SUMMARY {'='*20}")
        successful_tests = sum(1 for r in results if r.get("success", False))
        total_tests = len(results)

        print(f"📊 Total tests: {total_tests}")
        print(f"✅ Successful: {successful_tests}")
        print(f"❌ Failed: {total_tests - successful_tests}")
        print(f"📈 Success rate: {(successful_tests/total_tests)*100:.1f}%")

        if successful_tests > 0:
            print(f"\n📈 Successful test details:")
            for result in results:
                if result.get("success"):
                    print(f"   ✅ {result['book_title']}")
                    print(f"      ⏱️  {result['duration']:.2f}s")
                    print(f"      🌊 {result['nodes_count']} nodes")
                    print(f"      📄 {'✅' if result['has_markdown'] else '❌'} markdown")

        if total_tests - successful_tests > 0:
            print(f"\n❌ Failed test details:")
            for result in results:
                if not result.get("success"):
                    print(f"   ❌ {result['book_title']}")
                    print(f"      🚫 {result['error']}")

        return successful_tests == total_tests

async def main():
    """Main test execution"""
    print("🧠 Mindmap Generation Test Script")
    print("This script tests the mindmap generation functionality with specific book")
    print()

    # Check if backend is running
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BACKEND_URL}/health", timeout=5.0)
            if response.status_code != 200:
                print(f"❌ Backend is not responding correctly at {BACKEND_URL}")
                print("Please make sure the backend server is running on port 8000")
                return False
    except Exception as e:
        print(f"❌ Cannot connect to backend at {BACKEND_URL}: {e}")
        print("Please start the backend server first")
        return False

    print(f"✅ Backend is running at {BACKEND_URL}")

    # Run specific test for Caboto book
    async with MindmapTester() as tester:
        print("\n🎯 Testing specific book: Sebastiano Caboto")
        result = await tester.test_mindmap_generation(
            "e9195d61-9bd2-4e30-a183-cee2ab80f1b9",  # course_id
            "582d5f87-89bb-45da-8df5-28e33d7dc009",  # book_id
            "Sebastiano Caboto libro Geografia Storica"
        )

        print(f"\n📊 Test result: {'✅ SUCCESS' if result.get('success') else '❌ FAILED'}")
        if result.get('success'):
            print(f"   Duration: {result.get('duration', 0):.2f}s")
            print(f"   Nodes: {result.get('nodes_count', 0)}")
        else:
            print(f"   Error: {result.get('error', 'Unknown error')}")

    return result.get('success', False)

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n💥 Unexpected error: {e}")
        sys.exit(1)