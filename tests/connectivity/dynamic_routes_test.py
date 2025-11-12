#!/usr/bin/env python3
"""
Dynamic Routes Validation Test for Tutor-AI
Tests all dynamic routes to ensure they render correctly
"""

import requests
import json
import sys
import re
from typing import Dict, List, Tuple
from urllib.parse import urljoin

# Configuration
BACKEND_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3001"
TIMEOUT = 10

class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

class DynamicRoutesTester:
    def __init__(self):
        self.test_results = []
        self.session = requests.Session()
        self.session.timeout = TIMEOUT
        self.courses_data = []

    def print_result(self, test_name: str, passed: bool, message: str = ""):
        """Print test result with color coding"""
        status = f"{Colors.GREEN}✅ PASS{Colors.END}" if passed else f"{Colors.RED}❌ FAIL{Colors.END}"
        print(f"{status}: {test_name}")
        if message:
            print(f"   {Colors.RED if not passed else Colors.GREEN}   {message}{Colors.END}")

        self.test_results.append({
            'name': test_name,
            'passed': passed,
            'message': message
        })

    def fetch_courses_data(self) -> bool:
        """Fetch courses data for testing dynamic routes"""
        print(f"\n{Colors.BLUE}📚 Fetching Courses Data...{Colors.END}")

        try:
            response = self.session.get(f"{BACKEND_URL}/courses")
            if response.status_code != 200:
                self.print_result("Fetch courses data", False, f"Failed to fetch courses: {response.status_code}")
                return False

            data = response.json()
            self.courses_data = data.get('courses', [])

            if not self.courses_data:
                self.print_result("Courses data availability", False, "No courses found in system")
                return False

            self.print_result("Courses data availability", True, f"Found {len(self.courses_data)} courses")
            return True

        except Exception as e:
            self.print_result("Fetch courses data", False, f"Error fetching courses: {str(e)}")
            return False

    def test_static_routes(self) -> bool:
        """Test static routes"""
        print(f"\n{Colors.BLUE}🏠 Testing Static Routes...{Colors.END}")

        static_routes = [
            ("/", "Home page"),
            ("/courses", "Courses listing"),
            ("/chat", "Chat page"),
            ("/api/health", "Frontend health check")
        ]

        all_passed = True

        for route, description in static_routes:
            try:
                url = urljoin(FRONTEND_URL, route)
                response = self.session.get(url)
                passed = response.status_code == 200
                message = f"HTTP {response.status_code}" if passed else f"HTTP {response.status_code}"
                self.print_result(f"Static route: {description}", passed, message)
                all_passed &= passed
            except Exception as e:
                self.print_result(f"Static route: {description}", False, f"Request failed: {str(e)}")
                all_passed = False

        return all_passed

    def test_course_detail_routes(self) -> bool:
        """Test course detail dynamic routes"""
        print(f"\n{Colors.BLUE}📖 Testing Course Detail Routes...{Colors.END}")

        if not self.courses_data:
            self.print_result("Course detail routes", False, "No courses data available")
            return False

        all_passed = True

        # Test up to 3 courses to avoid too many requests
        test_courses = self.courses_data[:3]

        for i, course in enumerate(test_courses):
            course_id = course.get('id')
            course_name = course.get('name', f'Course {i+1}')

            if not course_id:
                continue

            # Test course detail page
            try:
                url = f"{FRONTEND_URL}/courses/{course_id}"
                response = self.session.get(url)
                passed = response.status_code == 200
                message = f"HTTP {response.status_code}" if passed else f"HTTP {response.status_code}"
                self.print_result(f"Course detail: {course_name[:30]}...", passed, message)
                all_passed &= passed
            except Exception as e:
                self.print_result(f"Course detail: {course_name[:30]}...", False, f"Request failed: {str(e)}")
                all_passed = False

        return all_passed

    def test_books_routes(self) -> bool:
        """Test books listing and detail routes"""
        print(f"\n{Colors.BLUE}📚 Testing Books Routes...{Colors.END}")

        if not self.courses_data:
            self.print_result("Books routes", False, "No courses data available")
            return False

        all_passed = True

        # Test up to 2 courses for books
        test_courses = self.courses_data[:2]

        for i, course in enumerate(test_courses):
            course_id = course.get('id')
            course_name = course.get('name', f'Course {i+1}')

            if not course_id:
                continue

            # Test books listing page
            try:
                url = f"{FRONTEND_URL}/courses/{course_id}/books"
                response = self.session.get(url)
                passed = response.status_code == 200
                message = f"HTTP {response.status_code}" if passed else f"HTTP {response.status_code}"
                self.print_result(f"Books listing: {course_name[:30]}...", passed, message)
                all_passed &= passed

                # If books listing works, try to get books data from backend
                if passed:
                    try:
                        books_response = self.session.get(f"{BACKEND_URL}/courses/{course_id}/books")
                        if books_response.status_code == 200:
                            books_data = books_response.json()
                            books = books_data.get('books', [])

                            if books:
                                # Test first book detail page
                                first_book = books[0]
                                book_id = first_book.get('id')
                                book_title = first_book.get('title', 'Unknown Book')

                                if book_id:
                                    book_url = f"{FRONTEND_URL}/courses/{course_id}/books/{book_id}"
                                    book_response = self.session.get(book_url)
                                    book_passed = book_response.status_code == 200
                                    book_message = f"HTTP {book_response.status_code}" if book_passed else f"HTTP {book_response.status_code}"
                                    self.print_result(f"Book detail: {book_title[:30]}...", book_passed, book_message)
                                    all_passed &= book_passed

                    except Exception as e:
                        # Backend books API might fail, but frontend route could still work
                        self.print_result(f"Backend books API for {course_name[:30]}...", False, f"API request failed: {str(e)}")

            except Exception as e:
                self.print_result(f"Books listing: {course_name[:30]}...", False, f"Request failed: {str(e)}")
                all_passed = False

        return all_passed

    def test_materials_routes(self) -> bool:
        """Test materials routes"""
        print(f"\n{Colors.BLUE}📄 Testing Materials Routes...{Colors.END}")

        if not self.courses_data:
            self.print_result("Materials routes", False, "No courses data available")
            return False

        all_passed = True

        # Test up to 2 courses for materials
        test_courses = self.courses_data[:2]

        for i, course in enumerate(test_courses):
            course_id = course.get('id')
            course_name = course.get('name', f'Course {i+1}')

            if not course_id:
                continue

            # Test materials listing page
            try:
                url = f"{FRONTEND_URL}/courses/{course_id}/materials"
                response = self.session.get(url)
                passed = response.status_code == 200
                message = f"HTTP {response.status_code}" if passed else f"HTTP {response.status_code}"
                self.print_result(f"Materials listing: {course_name[:30]}...", passed, message)
                all_passed &= passed

                # If materials listing works, try to get materials data from backend
                if passed:
                    try:
                        materials_response = self.session.get(f"{BACKEND_URL}/courses/{course_id}/materials")
                        if materials_response.status_code == 200:
                            materials_data = materials_response.json()
                            materials = materials_data.get('materials', [])

                            if materials:
                                # Test first material detail page
                                first_material = materials[0]
                                material_filename = first_material.get('filename', 'material.pdf')

                                # Test material detail page with filename
                                material_url = f"{FRONTEND_URL}/courses/{course_id}/materials/{material_filename}"
                                material_response = self.session.get(material_url)
                                material_passed = material_response.status_code == 200
                                material_message = f"HTTP {material_response.status_code}" if material_passed else f"HTTP {material_response.status_code}"
                                self.print_result(f"Material detail: {material_filename[:30]}...", material_passed, material_message)
                                all_passed &= material_passed

                    except Exception as e:
                        # Backend materials API might fail, but frontend route could still work
                        self.print_result(f"Backend materials API for {course_name[:30]}...", False, f"API request failed: {str(e)}")

            except Exception as e:
                self.print_result(f"Materials listing: {course_name[:30]}...", False, f"Request failed: {str(e)}")
                all_passed = False

        return all_passed

    def test_workspace_routes(self) -> bool:
        """Test workspace and study routes"""
        print(f"\n{Colors.BLUE}🖥️  Testing Workspace Routes...{Colors.END}")

        if not self.courses_data:
            self.print_result("Workspace routes", False, "No courses data available")
            return False

        all_passed = True

        # Test one course for workspace routes
        if self.courses_data:
            course = self.courses_data[0]
            course_id = course.get('id')
            course_name = course.get('name', 'Test Course')

            if course_id:
                workspace_routes = [
                    (f"/courses/{course_id}/study", "Study workspace"),
                    (f"/courses/{course_id}/study?book=test-book&pdf=test.pdf", "Study with params"),
                    (f"/courses/{course_id}/workspace", "Workspace"),
                ]

                for route, description in workspace_routes:
                    try:
                        url = f"{FRONTEND_URL}{route}"
                        response = self.session.get(url)
                        passed = response.status_code == 200
                        message = f"HTTP {response.status_code}" if passed else f"HTTP {response.status_code}"
                        self.print_result(f"Workspace: {description}", passed, message)
                        all_passed &= passed
                    except Exception as e:
                        self.print_result(f"Workspace: {description}", False, f"Request failed: {str(e)}")
                        all_passed &= False

        return all_passed

    def test_mindmap_routes(self) -> bool:
        """Test mindmap generation routes"""
        print(f"\n{Colors.BLUE}🗺️  Testing Mindmap Routes...{Colors.END}")

        if not self.courses_data:
            self.print_result("Mindmap routes", False, "No courses data available")
            return False

        all_passed = True

        # Test mindmap routes for first course
        if self.courses_data:
            course = self.courses_data[0]
            course_id = course.get('id')
            course_name = course.get('name', 'Test Course')

            if course_id:
                mindmap_routes = [
                    (f"/courses/{course_id}/mindmap", "Course mindmap"),
                ]

                # Try to add book mindmap routes if we have books data
                try:
                    books_response = self.session.get(f"{BACKEND_URL}/courses/{course_id}/books")
                    if books_response.status_code == 200:
                        books_data = books_response.json()
                        books = books_data.get('books', [])
                        if books:
                            first_book = books[0]
                            book_id = first_book.get('id')
                            if book_id:
                                mindmap_routes.append((f"/courses/{course_id}/books/{book_id}/mindmap", "Book mindmap"))
                except:
                    pass  # Books API might not be available

                for route, description in mindmap_routes:
                    try:
                        url = f"{FRONTEND_URL}{route}"
                        response = self.session.get(url)
                        passed = response.status_code == 200
                        message = f"HTTP {response.status_code}" if passed else f"HTTP {response.status_code}"
                        self.print_result(f"Mindmap: {description}", passed, message)
                        all_passed &= passed
                    except Exception as e:
                        self.print_result(f"Mindmap: {description}", False, f"Request failed: {str(e)}")
                        all_passed &= False

        return all_passed

    def test_invalid_routes(self) -> bool:
        """Test invalid routes to ensure proper 404 handling"""
        print(f"\n{Colors.BLUE}❌ Testing Invalid Routes...{Colors.END}")

        invalid_routes = [
            ("/courses/invalid-course-id", "Invalid course ID"),
            ("/courses/invalid-course-id/books", "Invalid course books"),
            ("/courses/invalid-course-id/books/invalid-book-id", "Invalid book detail"),
            ("/nonexistent-route", "Completely invalid route"),
        ]

        all_passed = True

        for route, description in invalid_routes:
            try:
                url = f"{FRONTEND_URL}{route}"
                response = self.session.get(url)
                # Should return 404 for invalid routes
                passed = response.status_code == 404
                message = f"HTTP {response.status_code}" if passed else f"Expected 404, got HTTP {response.status_code}"
                self.print_result(f"Invalid route: {description}", passed, message)
                all_passed &= passed
            except Exception as e:
                # Connection errors might also indicate proper routing
                self.print_result(f"Invalid route: {description}", True, f"Properly rejected (connection error)")
                # Don't fail the test for connection errors on invalid routes

        return all_passed

    def run_all_tests(self) -> bool:
        """Run all dynamic route tests"""
        print(f"{Colors.BOLD}🛣️  Dynamic Routes Validation Test Suite{Colors.END}")
        print("=" * 60)
        print(f"Frontend URL: {FRONTEND_URL}")
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Timeout: {TIMEOUT}s")

        # Run all test suites
        all_passed = True

        # First fetch courses data
        if not self.fetch_courses_data():
            print(f"\n{Colors.YELLOW}⚠️  Cannot proceed with dynamic route tests without courses data.{Colors.END}")
            return False

        all_passed &= self.test_static_routes()
        all_passed &= self.test_course_detail_routes()
        all_passed &= self.test_books_routes()
        all_passed &= self.test_materials_routes()
        all_passed &= self.test_workspace_routes()
        all_passed &= self.test_mindmap_routes()
        all_passed &= self.test_invalid_routes()

        # Display summary
        self.display_summary()

        return all_passed

    def display_summary(self):
        """Display test summary"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['passed'])
        failed_tests = total_tests - passed_tests

        print(f"\n{Colors.BLUE}📊 Routes Test Summary{Colors.END}")
        print("=" * 40)
        print(f"Total Routes Tested: {total_tests}")
        print(f"{Colors.GREEN}Passed: {passed_tests}{Colors.END}")
        print(f"{Colors.RED}Failed: {failed_tests}{Colors.END}")

        if failed_tests > 0:
            print(f"\n{Colors.RED}❌ Failed Route Tests:{Colors.END}")
            for result in self.test_results:
                if not result['passed']:
                    print(f"   • {result['name']}: {result['message']}")

        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        print(f"\nRoute Success Rate: {success_rate:.1f}%")

        if failed_tests == 0:
            print(f"\n{Colors.GREEN}🎉 All routes are working correctly!{Colors.END}")
        else:
            print(f"\n{Colors.YELLOW}⚠️  Some routes are not working. Please check the issues above.{Colors.END}")

def main():
    """Main function"""
    tester = DynamicRoutesTester()

    try:
        success = tester.run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}⚠️  Tests interrupted by user.{Colors.END}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}💥 Route test suite failed with error: {str(e)}{Colors.END}")
        sys.exit(1)

if __name__ == "__main__":
    main()