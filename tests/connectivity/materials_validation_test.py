#!/usr/bin/env python3
"""
Materials Validation Test for Tutor-AI
Tests all existing materials and verifies they are accessible
"""

import requests
import json
import sys
import os
from typing import Dict, List, Tuple
from urllib.parse import urljoin

# Configuration
BACKEND_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3001"
TIMEOUT = 15

class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

class MaterialsValidator:
    def __init__(self):
        self.test_results = []
        self.session = requests.Session()
        self.session.timeout = TIMEOUT
        self.courses_data = []
        self.books_data = {}
        self.materials_summary = {
            'total_courses': 0,
            'total_books': 0,
            'total_materials': 0,
            'accessible_materials': 0,
            'inaccessible_materials': 0
        }

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

    def fetch_all_data(self) -> bool:
        """Fetch courses, books, and materials data"""
        print(f"\n{Colors.BLUE}📚 Fetching Course and Materials Data...{Colors.END}")

        try:
            # Fetch courses
            response = self.session.get(f"{BACKEND_URL}/courses")
            if response.status_code != 200:
                self.print_result("Fetch courses data", False, f"Failed to fetch courses: {response.status_code}")
                return False

            data = response.json()
            self.courses_data = data.get('courses', [])
            self.materials_summary['total_courses'] = len(self.courses_data)

            if not self.courses_data:
                self.print_result("Courses data availability", False, "No courses found in system")
                return False

            self.print_result("Courses data availability", True, f"Found {len(self.courses_data)} courses")

            # Fetch books for each course
            for course in self.courses_data:
                course_id = course.get('id')
                course_name = course.get('name', 'Unknown Course')

                if course_id:
                    try:
                        books_response = self.session.get(f"{BACKEND_URL}/courses/{course_id}/books")
                        if books_response.status_code == 200:
                            books_data = books_response.json()
                            books = books_data.get('books', [])
                            self.books_data[course_id] = {
                                'course_name': course_name,
                                'books': books
                            }
                            self.materials_summary['total_books'] += len(books)
                        else:
                            self.print_result(f"Fetch books for {course_name}", False, f"HTTP {books_response.status_code}")
                    except Exception as e:
                        self.print_result(f"Fetch books for {course_name}", False, f"Error: {str(e)}")

            self.print_result("Books data availability", True, f"Found {self.materials_summary['total_books']} total books")
            return True

        except Exception as e:
            self.print_result("Fetch all data", False, f"Error fetching data: {str(e)}")
            return False

    def test_materials_structure(self) -> bool:
        """Test the structure and metadata of materials"""
        print(f"\n{Colors.BLUE}📋 Testing Materials Structure...{Colors.END}")

        all_passed = True

        for course_id, course_data in self.books_data.items():
            course_name = course_data['course_name']
            books = course_data['books']

            print(f"\n{Colors.YELLOW}📖 Course: {course_name}{Colors.END}")

            for book in books:
                book_id = book.get('id')
                book_title = book.get('title', 'Unknown Book')
                materials_count = book.get('materials_count', 0)

                # Test book metadata
                metadata_tests = [
                    (bool(book_id), f"Book ID present: {book_title[:30]}..."),
                    (bool(book_title), f"Book title present: {book_title[:30]}..."),
                    (isinstance(materials_count, int), f"Materials count valid: {book_title[:30]}..."),
                ]

                for test_passed, description in metadata_tests:
                    self.print_result(description, test_passed)
                    all_passed &= test_passed

                # Track total materials
                self.materials_summary['total_materials'] += materials_count

                if materials_count > 0:
                    self.print_result(f"Materials available: {book_title[:30]}...", True, f"Count: {materials_count}")
                else:
                    self.print_result(f"No materials: {book_title[:30]}...", True, "No materials uploaded")

        return all_passed

    def test_file_system_access(self) -> bool:
        """Test file system access to materials"""
        print(f"\n{Colors.BLUE}📁 Testing File System Access...{Colors.END}")

        all_passed = True
        accessible_count = 0

        # Test data directory structure
        data_dir = "./data"
        if os.path.exists(data_dir):
            self.print_result("Data directory exists", True, f"Path: {data_dir}")

            # Test courses directory
            courses_dir = os.path.join(data_dir, "courses")
            if os.path.exists(courses_dir):
                self.print_result("Courses directory exists", True, f"Path: {courses_dir}")

                # List course directories
                try:
                    course_dirs = [d for d in os.listdir(courses_dir) if os.path.isdir(os.path.join(courses_dir, d))]
                    self.print_result("Course directories found", True, f"Count: {len(course_dirs)}")

                    # Test materials in course directories
                    for course in self.courses_data:
                        course_id = course.get('id')
                        course_name = course.get('name', 'Unknown Course')
                        course_dir = os.path.join(courses_dir, course_id)

                        if os.path.exists(course_dir):
                            self.print_result(f"Course directory accessible: {course_name[:30]}...", True)

                            # Test books directory
                            books_dir = os.path.join(course_dir, "books")
                            if os.path.exists(books_dir):
                                try:
                                    book_dirs = [d for d in os.listdir(books_dir) if os.path.isdir(os.path.join(books_dir, d))]

                                    for book_dir in book_dirs:
                                        book_path = os.path.join(books_dir, book_dir)
                                        try:
                                            materials = os.listdir(book_path)
                                            pdf_files = [f for f in materials if f.lower().endswith('.pdf')]
                                            if pdf_files:
                                                accessible_count += len(pdf_files)
                                                self.print_result(f"PDF files in {book_dir[:8]}...", True, f"Count: {len(pdf_files)}")
                                                # List actual PDF files
                                                for pdf_file in pdf_files[:3]:  # Show first 3
                                                    self.print_result(f"  📄 {pdf_file[:40]}...", True, "Accessible")
                                        except Exception as e:
                                            self.print_result(f"Access book dir {book_dir[:8]}...", False, f"Error: {str(e)}")
                                            all_passed &= False
                                except Exception as e:
                                    self.print_result(f"List books directory {course_name[:30]}...", False, f"Error: {str(e)}")
                                    all_passed &= False
                            else:
                                self.print_result(f"Books directory: {course_name[:30]}...", False, "Missing books directory")
                                all_passed &= False
                        else:
                            self.print_result(f"Course directory: {course_name[:30]}...", False, "Missing course directory")
                            all_passed &= False

                except Exception as e:
                    self.print_result("List course directories", False, f"Error: {str(e)}")
                    all_passed &= False
            else:
                self.print_result("Courses directory exists", False, f"Missing: {courses_dir}")
                all_passed &= False
        else:
            self.print_result("Data directory exists", False, f"Missing: {data_dir}")
            all_passed &= False

        # Update summary
        self.materials_summary['accessible_materials'] = accessible_count

        if accessible_count > 0:
            self.print_result("File system accessibility", True, f"Accessible files: {accessible_count}")
        else:
            self.print_result("File system accessibility", False, "No accessible files found")
            all_passed &= False

        return all_passed

    def test_materials_routes(self) -> bool:
        """Test frontend routes for materials access"""
        print(f"\n{Colors.BLUE}🛣️  Testing Materials Routes...{Colors.END}")

        if not self.courses_data:
            self.print_result("Materials routes", False, "No courses data available")
            return False

        all_passed = True
        tested_routes = 0

        # Test materials listing routes
        for course in self.courses_data[:2]:  # Test first 2 courses
            course_id = course.get('id')
            course_name = course.get('name', f'Course {course_id[:8]}...')

            if course_id:
                # Test course materials listing
                try:
                    url = f"{FRONTEND_URL}/courses/{course_id}/materials"
                    response = self.session.get(url)
                    passed = response.status_code == 200
                    message = f"HTTP {response.status_code}" if passed else f"HTTP {response.status_code}"
                    self.print_result(f"Materials listing: {course_name[:30]}...", passed, message)
                    all_passed &= passed
                    tested_routes += 1
                except Exception as e:
                    self.print_result(f"Materials listing: {course_name[:30]}...", False, f"Request failed: {str(e)}")
                    all_passed &= False

        # Test study workspace with books
        if self.books_data:
            for course_id, course_data in list(self.books_data.items())[:1]:  # Test first course with books
                course_name = course_data['course_name']
                books = course_data['books']

                for book in books[:1]:  # Test first book with materials
                    book_id = book.get('id')
                    book_title = book.get('title', 'Unknown Book')
                    materials_count = book.get('materials_count', 0)

                    if book_id and materials_count > 0:
                        # Test study workspace with book
                        try:
                            study_url = f"{FRONTEND_URL}/courses/{course_id}/study?book={book_id}"
                            study_response = self.session.get(study_url)
                            study_passed = study_response.status_code == 200
                            study_message = f"HTTP {study_response.status_code}" if study_passed else f"HTTP {study_response.status_code}"
                            self.print_result(f"Study workspace: {book_title[:30]}...", study_passed, study_message)
                            all_passed &= study_passed
                            tested_routes += 1
                        except Exception as e:
                            self.print_result(f"Study workspace: {book_title[:30]}...", False, f"Request failed: {str(e)}")
                            all_passed &= False

        if tested_routes > 0:
            self.print_result("Materials routes testing", True, f"Tested {tested_routes} routes")
        else:
            self.print_result("Materials routes testing", False, "No routes tested")
            all_passed &= False

        return all_passed

    def display_materials_summary(self):
        """Display comprehensive materials summary"""
        print(f"\n{Colors.BLUE}📊 Materials Summary Report{Colors.END}")
        print("=" * 50)
        print(f"Total Courses: {self.materials_summary['total_courses']}")
        print(f"Total Books: {self.materials_summary['total_books']}")
        print(f"Total Materials (metadata): {self.materials_summary['total_materials']}")
        print(f"{Colors.GREEN}Accessible Files: {self.materials_summary['accessible_materials']}{Colors.END}")

        if self.materials_summary['total_materials'] > 0:
            accessibility_rate = (self.materials_summary['accessible_materials'] / self.materials_summary['total_materials']) * 100
            print(f"Accessibility Rate: {accessibility_rate:.1f}%")

        # Course breakdown
        if self.courses_data:
            print(f"\n{Colors.YELLOW}📚 Course Breakdown:${Colors.END}")
            for course in self.courses_data:
                course_name = course.get('name', 'Unknown Course')
                course_id = course.get('id', 'Unknown ID')

                if course_id in self.books_data:
                    books = self.books_data[course_id]['books']
                    total_materials = sum(book.get('materials_count', 0) for book in books)
                    print(f"  • {course_name}: {len(books)} books, {total_materials} materials")

    def display_test_summary(self):
        """Display test results summary"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['passed'])
        failed_tests = total_tests - passed_tests

        print(f"\n{Colors.BLUE}📊 Test Results Summary${Colors.END}")
        print("=" * 40)
        print(f"Total Tests: {total_tests}")
        print(f"${Colors.GREEN}Passed: {passed_tests}${Colors.END}")
        print(f"${Colors.RED}Failed: {failed_tests}${Colors.END}")

        if failed_tests > 0:
            print(f"\n${Colors.RED}❌ Failed Tests:${Colors.END}")
            for result in self.test_results:
                if not result['passed']:
                    print(f"   • {result['name']}: {result['message']}")

        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        print(f"\nTest Success Rate: {success_rate:.1f}%")

        if failed_tests == 0:
            print(f"\n${Colors.GREEN}🎉 All materials tests passed!${Colors.END}")
        else:
            print(f"\n${Colors.YELLOW}⚠️  Some materials tests failed.${Colors.END}")

    def run_all_tests(self) -> bool:
        """Run all materials validation tests"""
        print(f"{Colors.BOLD}📚 Materials Validation Test Suite{Colors.END}")
        print("=" * 60)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Frontend URL: {FRONTEND_URL}")
        print(f"Data Directory: ./data")

        # Run all test suites
        all_passed = True

        # First fetch all data
        if not self.fetch_all_data():
            print(f"\n${Colors.YELLOW}⚠️  Cannot proceed with materials tests without data.${Colors.END}")
            return False

        all_passed &= self.test_materials_structure()
        all_passed &= self.test_file_system_access()
        all_passed &= self.test_materials_routes()

        # Display comprehensive summary
        self.display_materials_summary()
        self.display_test_summary()

        return all_passed

def main():
    """Main function"""
    validator = MaterialsValidator()

    try:
        success = validator.run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n${Colors.YELLOW}⚠️  Tests interrupted by user.${Colors.END}")
        sys.exit(1)
    except Exception as e:
        print(f"\n${Colors.RED}💥 Materials validation failed: {str(e)}${Colors.END}")
        sys.exit(1)

if __name__ == "__main__":
    main()