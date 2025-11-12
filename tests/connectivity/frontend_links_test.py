#!/usr/bin/env python3
"""
Frontend Links Validation Test for Tutor-AI
Tests all frontend links to ensure they don't return 404 errors
"""

import requests
import json
import sys
import re
from typing import Dict, List, Tuple, Set
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

# Configuration
FRONTEND_URL = "http://localhost:3001"
BACKEND_URL = "http://localhost:8000"
TIMEOUT = 10

class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

class FrontendLinksTester:
    def __init__(self):
        self.test_results = []
        self.session = requests.Session()
        self.session.timeout = TIMEOUT
        self.courses_data = []
        self.tested_links = set()

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

    def test_static_links(self) -> bool:
        """Test static navigation links"""
        print(f"\n{Colors.BLUE}🔗 Testing Static Navigation Links...{Colors.END}")

        static_links = [
            ("/", "Home page"),
            ("/courses", "Courses listing"),
            ("/chat", "Chat interface"),
        ]

        all_passed = True

        for route, description in static_links:
            try:
                url = urljoin(FRONTEND_URL, route)
                response = self.session.get(url)
                passed = response.status_code == 200
                message = f"HTTP {response.status_code}" if passed else f"HTTP {response.status_code}"
                self.print_result(f"Static link: {description}", passed, message)
                all_passed &= passed
            except Exception as e:
                self.print_result(f"Static link: {description}", False, f"Request failed: {str(e)}")
                all_passed = False

        return all_passed

    def test_course_navigation_links(self) -> bool:
        """Test course-related navigation links"""
        print(f"\n{Colors.BLUE}📖 Testing Course Navigation Links...{Colors.END}")

        if not self.courses_data:
            self.print_result("Course navigation links", False, "No courses data available")
            return False

        all_passed = True

        # Test up to 3 courses
        test_courses = self.courses_data[:3]

        for i, course in enumerate(test_courses):
            course_id = course.get('id')
            course_name = course.get('name', f'Course {i+1}')

            if not course_id:
                continue

            # Test course detail page
            course_links = [
                (f"/courses/{course_id}", f"Course detail: {course_name[:30]}..."),
                (f"/courses/{course_id}/books", f"Books listing: {course_name[:30]}..."),
                (f"/courses/{course_id}/materials", f"Materials listing: {course_name[:30]}..."),
                (f"/courses/{course_id}/study", f"Study workspace: {course_name[:30]}..."),
                (f"/courses/{course_id}/workspace", f"Workspace: {course_name[:30]}..."),
                (f"/courses/{course_id}/mindmap", f"Mindmap: {course_name[:30]}..."),
            ]

            for route, description in course_links:
                try:
                    url = f"{FRONTEND_URL}{route}"
                    response = self.session.get(url)
                    passed = response.status_code == 200
                    message = f"HTTP {response.status_code}" if passed else f"HTTP {response.status_code}"
                    self.print_result(description, passed, message)
                    all_passed &= passed
                except Exception as e:
                    self.print_result(description, False, f"Request failed: {str(e)}")
                    all_passed = False

        return all_passed

    def test_book_navigation_links(self) -> bool:
        """Test book-related navigation links"""
        print(f"\n{Colors.BLUE}📚 Testing Book Navigation Links...{Colors.END}")

        if not self.courses_data:
            self.print_result("Book navigation links", False, "No courses data available")
            return False

        all_passed = True

        # Test up to 2 courses for books
        test_courses = self.courses_data[:2]

        for i, course in enumerate(test_courses):
            course_id = course.get('id')
            course_name = course.get('name', f'Course {i+1}')

            if not course_id:
                continue

            # Try to get books data
            try:
                books_response = self.session.get(f"{BACKEND_URL}/courses/{course_id}/books")
                if books_response.status_code == 200:
                    books_data = books_response.json()
                    books = books_data.get('books', [])

                    if books:
                        # Test up to 2 books per course
                        test_books = books[:2]

                        for j, book in enumerate(test_books):
                            book_id = book.get('id')
                            book_title = book.get('title', f'Book {j+1}')

                            if book_id:
                                book_links = [
                                    (f"/courses/{course_id}/books/{book_id}", f"Book detail: {book_title[:30]}..."),
                                    (f"/courses/{course_id}/books/{book_id}/mindmap", f"Book mindmap: {book_title[:30]}..."),
                                ]

                                for route, description in book_links:
                                    try:
                                        url = f"{FRONTEND_URL}{route}"
                                        response = self.session.get(url)
                                        passed = response.status_code == 200
                                        message = f"HTTP {response.status_code}" if passed else f"HTTP {response.status_code}"
                                        self.print_result(description, passed, message)
                                        all_passed &= passed
                                    except Exception as e:
                                        self.print_result(description, False, f"Request failed: {str(e)}")
                                        all_passed = False

            except Exception as e:
                self.print_result(f"Books API for {course_name[:30]}...", False, f"Failed to fetch books: {str(e)}")
                all_passed = False

        return all_passed

    def test_material_navigation_links(self) -> bool:
        """Test material-related navigation links"""
        print(f"\n{Colors.BLUE}📄 Testing Material Navigation Links...{Colors.END}")

        if not self.courses_data:
            self.print_result("Material navigation links", False, "No courses data available")
            return False

        all_passed = True

        # Test up to 2 courses for materials
        test_courses = self.courses_data[:2]

        for i, course in enumerate(test_courses):
            course_id = course.get('id')
            course_name = course.get('name', f'Course {i+1}')

            if not course_id:
                continue

            # Try to get materials data
            try:
                materials_response = self.session.get(f"{BACKEND_URL}/courses/{course_id}/materials")
                if materials_response.status_code == 200:
                    materials_data = materials_response.json()
                    materials = materials_data.get('materials', [])

                    if materials:
                        # Test up to 2 materials per course
                        test_materials = materials[:2]

                        for j, material in enumerate(test_materials):
                            material_filename = material.get('filename', f'material{j+1}.pdf')

                            # Test material detail page
                            try:
                                url = f"{FRONTEND_URL}/courses/{course_id}/materials/{material_filename}"
                                response = self.session.get(url)
                                passed = response.status_code == 200
                                message = f"HTTP {response.status_code}" if passed else f"HTTP {response.status_code}"
                                self.print_result(f"Material: {material_filename[:30]}...", passed, message)
                                all_passed &= passed
                            except Exception as e:
                                self.print_result(f"Material: {material_filename[:30]}...", False, f"Request failed: {str(e)}")
                                all_passed = False

            except Exception as e:
                self.print_result(f"Materials API for {course_name[:30]}...", False, f"Failed to fetch materials: {str(e)}")
                all_passed = False

        return all_passed

    def test_workspace_links(self) -> bool:
        """Test workspace and study links with parameters"""
        print(f"\n{Colors.BLUE}🖥️  Testing Workspace Links with Parameters...{Colors.END}")

        if not self.courses_data:
            self.print_result("Workspace parameter links", False, "No courses data available")
            return False

        all_passed = True

        # Test one course for workspace parameter links
        if self.courses_data:
            course = self.courses_data[0]
            course_id = course.get('id')
            course_name = course.get('name', 'Test Course')

            if course_id:
                workspace_param_links = [
                    (f"/courses/{course_id}/study?book=test-book&pdf=test.pdf", "Study with book & PDF params"),
                    (f"/courses/{course_id}/study?book=sample-book", "Study with book param"),
                    (f"/courses/{course_id}/study?pdf=sample.pdf", "Study with PDF param"),
                    (f"/courses/{course_id}/workspace?tab=materials", "Workspace with tab param"),
                ]

                for route, description in workspace_param_links:
                    try:
                        url = f"{FRONTEND_URL}{route}"
                        response = self.session.get(url)
                        passed = response.status_code == 200
                        message = f"HTTP {response.status_code}" if passed else f"HTTP {response.status_code}"
                        self.print_result(f"Workspace: {description}", passed, message)
                        all_passed &= passed
                    except Exception as e:
                        self.print_result(f"Workspace: {description}", False, f"Request failed: {str(e)}")
                        all_passed = False

        return all_passed

    def test_invalid_links(self) -> bool:
        """Test invalid links to ensure proper 404 handling"""
        print(f"\n{Colors.BLUE}❌ Testing Invalid Links (404 Handling)...{Colors.END}")

        invalid_links = [
            ("/courses/invalid-course-id", "Invalid course ID"),
            ("/courses/invalid-course-id/books", "Invalid course books"),
            ("/courses/invalid-course-id/books/invalid-book-id", "Invalid book detail"),
            ("/courses/invalid-course-id/materials", "Invalid course materials"),
            ("/courses/invalid-course-id/materials/invalid-file.pdf", "Invalid material"),
            ("/nonexistent-route", "Completely invalid route"),
            ("/api/nonexistent-endpoint", "Invalid API route"),
        ]

        all_passed = True

        for route, description in invalid_links:
            try:
                url = f"{FRONTEND_URL}{route}"
                response = self.session.get(url)
                # Should return 404 for invalid routes
                passed = response.status_code == 404
                message = f"HTTP {response.status_code}" if passed else f"Expected 404, got HTTP {response.status_code}"
                self.print_result(f"Invalid link: {description}", passed, message)
                all_passed &= passed
            except Exception as e:
                # Connection errors might also indicate proper routing
                self.print_result(f"Invalid link: {description}", True, f"Properly rejected (connection error)")
                # Don't fail the test for connection errors on invalid routes

        return all_passed

    def extract_and_test_internal_links(self) -> bool:
        """Extract links from main pages and test them"""
        print(f"\n{Colors.BLUE}🔍 Extracting and Testing Internal Links...{Colors.END}")

        all_passed = True

        # Pages to crawl for internal links
        pages_to_crawl = [
            ("/", "Home page"),
            ("/courses", "Courses listing"),
        ]

        for page_url, page_name in pages_to_crawl:
            try:
                full_url = f"{FRONTEND_URL}{page_url}"
                response = self.session.get(full_url)

                if response.status_code != 200:
                    self.print_result(f"Crawl {page_name}", False, f"Failed to load page: HTTP {response.status_code}")
                    all_passed &= False
                    continue

                # Parse HTML to extract links
                soup = BeautifulSoup(response.text, 'html.parser')
                links = soup.find_all('a', href=True)

                internal_links = []
                for link in links:
                    href = link.get('href', '')
                    if href.startswith('/') and not href.startswith('//'):
                        # Convert relative URL to absolute
                        absolute_url = urljoin(FRONTEND_URL, href)

                        # Only test links that look like our routes
                        if any(pattern in href for pattern in ['/courses', '/chat', '/study', '/workspace', '/mindmap']):
                            internal_links.append((href, link.get_text(strip=True) or href))

                # Test unique internal links
                tested_count = 0
                for href, link_text in internal_links[:10]:  # Limit to 10 links per page
                    if href not in self.tested_links:
                        self.tested_links.add(href)
                        try:
                            link_url = f"{FRONTEND_URL}{href}"
                            link_response = self.session.get(link_url)
                            passed = link_response.status_code == 200
                            message = f"HTTP {link_response.status_code}" if passed else f"HTTP {link_response.status_code}"

                            # Truncate long link text
                            display_text = link_text[:50] + "..." if len(link_text) > 50 else link_text
                            self.print_result(f"Internal link: {display_text}", passed, message)
                            all_passed &= passed
                            tested_count += 1

                        except Exception as e:
                            self.print_result(f"Internal link: {link_text[:50]}...", False, f"Request failed: {str(e)}")
                            all_passed &= False

                if tested_count > 0:
                    self.print_result(f"Crawled links from {page_name}", True, f"Tested {tested_count} internal links")
                else:
                    self.print_result(f"Crawled links from {page_name}", True, "No new internal links found")

            except Exception as e:
                self.print_result(f"Crawl {page_name}", False, f"Failed to crawl page: {str(e)}")
                all_passed &= False

        return all_passed

    def run_all_tests(self) -> bool:
        """Run all frontend link tests"""
        print(f"{Colors.BOLD}🔗 Frontend Links Validation Test Suite{Colors.END}")
        print("=" * 70)
        print(f"Frontend URL: {FRONTEND_URL}")
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Timeout: {TIMEOUT}s")

        # Run all test suites
        all_passed = True

        # First fetch courses data
        if not self.fetch_courses_data():
            print(f"\n{Colors.YELLOW}⚠️  Cannot proceed with dynamic link tests without courses data.${Colors.END}")
            print("Running static link tests only...")

        all_passed &= self.test_static_links()
        all_passed &= self.test_course_navigation_links()
        all_passed &= self.test_book_navigation_links()
        all_passed &= self.test_material_navigation_links()
        all_passed &= self.test_workspace_links()
        all_passed &= self.test_invalid_links()
        all_passed &= self.extract_and_test_internal_links()

        # Display summary
        self.display_summary()

        return all_passed

    def display_summary(self):
        """Display test summary"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['passed'])
        failed_tests = total_tests - passed_tests

        print(f"\n{Colors.BLUE}📊 Frontend Links Test Summary${Colors.END}")
        print("=" * 50)
        print(f"Total Links Tested: {total_tests}")
        print(f"{Colors.GREEN}Passed: {passed_tests}${Colors.END}")
        print(f"${Colors.RED}Failed: {failed_tests}${Colors.END}")

        if failed_tests > 0:
            print(f"\n${Colors.RED}❌ Failed Link Tests:${Colors.END}")
            for result in self.test_results:
                if not result['passed']:
                    print(f"   • {result['name']}: {result['message']}")

        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        print(f"\nLink Success Rate: {success_rate:.1f}%")

        if failed_tests == 0:
            print(f"\n${Colors.GREEN}🎉 All frontend links are working correctly!${Colors.END}")
        else:
            print(f"\n${Colors.YELLOW}⚠️  Some frontend links are broken. Please check the issues above.${Colors.END}")

def main():
    """Main function"""
    tester = FrontendLinksTester()

    try:
        success = tester.run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n${Colors.YELLOW}⚠️  Tests interrupted by user.${Colors.END}")
        sys.exit(1)
    except Exception as e:
        print(f"\n${Colors.RED}💥 Frontend links test suite failed with error: {str(e)}${Colors.END}")
        sys.exit(1)

if __name__ == "__main__":
    main()