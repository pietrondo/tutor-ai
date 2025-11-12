#!/usr/bin/env python3
"""
PDF Functionality Test Suite for Tutor-AI

Tests PDF loading, accessibility, and file system access across the system.
"""

import requests
import json
import time
import os
from typing import Dict, List, Any
import sys

class PDFTestSuite:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.frontend_url = "http://localhost:3001"
        self.results = []

    def log_result(self, test_name: str, passed: bool, message: str = ""):
        """Log test result"""
        status = "PASS" if passed else "FAIL"
        self.results.append({
            "test": test_name,
            "status": status,
            "message": message
        })
        print(f"[{status}] {test_name}: {message}")

    def test_backend_health(self):
        """Test if backend is accessible"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            passed = response.status_code == 200
            self.log_result(
                "Backend Health Check",
                passed,
                f"Status: {response.status_code}" if passed else f"Failed: {response.status_code}"
            )
            return passed
        except Exception as e:
            self.log_result("Backend Health Check", False, f"Connection error: {str(e)}")
            return False

    def test_frontend_health(self):
        """Test if frontend is accessible"""
        try:
            response = requests.get(self.frontend_url, timeout=5)
            passed = response.status_code == 200
            self.log_result(
                "Frontend Health Check",
                passed,
                f"Status: {response.status_code}" if passed else f"Failed: {response.status_code}"
            )
            return passed
        except Exception as e:
            self.log_result("Frontend Health Check", False, f"Connection error: {str(e)}")
            return False

    def test_courses_api(self):
        """Test courses API endpoint"""
        try:
            response = requests.get(f"{self.base_url}/courses", timeout=10)
            if response.status_code == 200:
                data = response.json()
                course_count = len(data.get("courses", []))
                self.log_result("Courses API", True, f"Found {course_count} courses")
                return data.get("courses", [])
            else:
                self.log_result("Courses API", False, f"Status: {response.status_code}")
                return []
        except Exception as e:
            self.log_result("Courses API", False, f"Error: {str(e)}")
            return []

    def test_course_detail_api(self, course_id: str):
        """Test course detail API with books and materials"""
        try:
            response = requests.get(f"{self.base_url}/courses/{course_id}", timeout=10)
            if response.status_code == 200:
                data = response.json()
                book_count = len(data.get("books", []))
                material_count = sum(len(book.get("materials", [])) for book in data.get("books", []))
                self.log_result(
                    "Course Detail API",
                    True,
                    f"Found {book_count} books, {material_count} materials"
                )
                return data
            else:
                self.log_result("Course Detail API", False, f"Status: {response.status_code}")
                return None
        except Exception as e:
            self.log_result("Course Detail API", False, f"Error: {str(e)}")
            return None

    def test_pdf_file_access(self, course_id: str, book_id: str, pdf_filename: str):
        """Test direct PDF file access through course-files endpoint"""
        try:
            url = f"{self.base_url}/course-files/{course_id}/books/{book_id}/{pdf_filename}"
            response = requests.head(url, timeout=10)
            passed = response.status_code == 200

            if passed:
                content_type = response.headers.get('content-type', '')
                content_length = response.headers.get('content-length', '0')
                self.log_result(
                    f"PDF File Access ({pdf_filename})",
                    True,
                    f"Content-Type: {content_type}, Size: {content_length} bytes"
                )
            else:
                self.log_result(
                    f"PDF File Access ({pdf_filename})",
                    False,
                    f"Status: {response.status_code}"
                )

            return passed
        except Exception as e:
            self.log_result(
                f"PDF File Access ({pdf_filename})",
                False,
                f"Error: {str(e)}"
            )
            return False

    def test_course_files_proxy(self, course_id: str, book_id: str, pdf_filename: str):
        """Test course-files proxy route through frontend"""
        try:
            url = f"{self.frontend_url}/course-files/{course_id}/books/{book_id}/{pdf_filename}"
            response = requests.head(url, timeout=10)
            passed = response.status_code == 200

            if passed:
                content_type = response.headers.get('content-type', '')
                self.log_result(
                    f"Frontend PDF Proxy ({pdf_filename})",
                    True,
                    f"Content-Type: {content_type}"
                )
            else:
                self.log_result(
                    f"Frontend PDF Proxy ({pdf_filename})",
                    False,
                    f"Status: {response.status_code}"
                )

            return passed
        except Exception as e:
            self.log_result(
                f"Frontend PDF Proxy ({pdf_filename})",
                False,
                f"Error: {str(e)}"
            )
            return False

    def test_workspace_urls(self, course_id: str, books: List[Dict]):
        """Test workspace URLs for each book/material"""
        for book in books[:2]:  # Test first 2 books
            book_id = book.get("id")
            materials = book.get("materials", [])

            if materials:
                # Test first material of each book
                material = materials[0]
                filename = material.get("filename")

                # Test workspace URL
                workspace_url = f"{self.frontend_url}/courses/{course_id}/materials/{filename}/workspace"
                try:
                    response = requests.get(workspace_url, timeout=10)
                    # We expect 200 for the page itself, even if the PDF loading fails
                    if response.status_code == 200:
                        self.log_result(
                            f"Workspace Page ({filename})",
                            True,
                            "Page loads successfully"
                        )
                    else:
                        self.log_result(
                            f"Workspace Page ({filename})",
                            False,
                            f"Status: {response.status_code}"
                        )
                except Exception as e:
                    self.log_result(
                        f"Workspace Page ({filename})",
                        False,
                        f"Error: {str(e)}"
                    )

    def test_book_detail_pages(self, course_id: str, books: List[Dict]):
        """Test book detail pages"""
        for book in books[:2]:  # Test first 2 books
            book_id = book.get("id")
            book_title = book.get("title", "Unknown")

            book_url = f"{self.frontend_url}/courses/{course_id}/books/{book_id}"
            try:
                response = requests.get(book_url, timeout=10)
                if response.status_code == 200:
                    self.log_result(
                        f"Book Detail Page ({book_title[:30]}...)",
                        True,
                        "Page loads successfully"
                    )
                else:
                    self.log_result(
                        f"Book Detail Page ({book_title[:30]}...)",
                        False,
                        f"Status: {response.status_code}"
                    )
            except Exception as e:
                self.log_result(
                    f"Book Detail Page ({book_title[:30]}...)",
                    False,
                    f"Error: {str(e)}"
                )

    def test_url_consistency(self, course_data: Dict):
        """Test that URLs in API responses use correct port"""
        books = course_data.get("books", [])
        port_inconsistencies = 0

        for book in books:
            materials = book.get("materials", [])
            for material in materials:
                pdf_url = material.get("pdf_url", "")
                if "localhost:8001" in pdf_url:
                    port_inconsistencies += 1

        if port_inconsistencies > 0:
            self.log_result(
                "URL Port Consistency",
                False,
                f"Found {port_inconsistencies} URLs still using port 8001"
            )
        else:
            self.log_result(
                "URL Port Consistency",
                True,
                "All URLs use correct port 8000"
            )

    def run_all_tests(self):
        """Run complete test suite"""
        print("🚀 Starting PDF Functionality Test Suite")
        print("=" * 50)

        # Basic health checks
        backend_ok = self.test_backend_health()
        frontend_ok = self.test_frontend_health()

        if not backend_ok or not frontend_ok:
            print("\n❌ Basic health checks failed. Skipping remaining tests.")
            return

        # Get courses
        courses = self.test_courses_api()
        if not courses:
            print("\n❌ No courses found. Skipping detailed tests.")
            return

        # Test first course in detail
        first_course = courses[0]
        course_id = first_course.get("id")
        course_name = first_course.get("name", "Unknown Course")

        print(f"\n📚 Testing course: {course_name} (ID: {course_id})")

        course_data = self.test_course_detail_api(course_id)
        if not course_data:
            return

        books = course_data.get("books", [])
        if not books:
            print("⚠️  No books found in course.")
            return

        # Test URL consistency
        self.test_url_consistency(course_data)

        # Test book detail pages
        self.test_book_detail_pages(course_id, books)

        # Test workspace functionality
        self.test_workspace_urls(course_id, books)

        # Test PDF file access
        total_pdf_tests = 0
        passed_pdf_tests = 0

        for book in books[:3]:  # Test first 3 books
            book_id = book.get("id")
            materials = book.get("materials", [])

            for material in materials[:2]:  # Test first 2 materials per book
                filename = material.get("filename")
                if filename and filename.endswith('.pdf'):
                    total_pdf_tests += 1

                    # Test direct backend access
                    if self.test_pdf_file_access(course_id, book_id, filename):
                        passed_pdf_tests += 1

                    # Test frontend proxy
                    self.test_course_files_proxy(course_id, book_id, filename)

        # Summary
        print("\n" + "=" * 50)
        print("📊 TEST SUMMARY")
        print("=" * 50)

        passed_tests = sum(1 for r in self.results if r["status"] == "PASS")
        total_tests = len(self.results)

        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")

        if total_pdf_tests > 0:
            print(f"\nPDF Tests: {passed_pdf_tests}/{total_pdf_tests} passed")

        # Show failed tests
        failed_tests = [r for r in self.results if r["status"] == "FAIL"]
        if failed_tests:
            print("\n❌ FAILED TESTS:")
            for test in failed_tests:
                print(f"  • {test['test']}: {test['message']}")

        return passed_tests == total_tests

if __name__ == "__main__":
    tester = PDFTestSuite()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)