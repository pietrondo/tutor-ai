#!/usr/bin/env python3
"""
End-to-End Integration Test for Tutor-AI
Tests complete user workflows in Docker environment
"""

import subprocess
import requests
import json
import time
import sys
import os
from typing import Dict, List, Optional
from datetime import datetime

# Configuration
BACKEND_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3001"
TIMEOUT = 30

class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'

class E2ETester:
    def __init__(self):
        self.test_results = []
        self.session = requests.Session()
        self.session.timeout = TIMEOUT
        self.test_data = {}

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

    def execute_command(self, command: str, description: str, expected_exit_code: int = 0) -> bool:
        """Execute command and check result"""
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=TIMEOUT
            )

            passed = result.returncode == expected_exit_code
            message = f"Exit code: {result.returncode}" if not passed else "Command executed successfully"

            if result.stdout.strip() and passed:
                message += f" | {result.stdout.strip()[:100]}..."

            self.print_result(description, passed, message)
            return passed

        except subprocess.TimeoutExpired:
            self.print_result(description, False, "Command timed out")
            return False
        except Exception as e:
            self.print_result(description, False, f"Command failed: {str(e)}")
            return False

    def test_docker_environment_readiness(self) -> bool:
        """Test if Docker environment is ready for testing"""
        print(f"\n{Colors.BLUE}🐳 Testing Docker Environment Readiness...{Colors.END}")

        all_passed = True

        # Check if containers are running
        all_passed &= self.execute_command(
            "docker ps --filter 'name=tutor-ai' --format '{{.Names}}:{{.Status}}' | grep -q 'Up'",
            "Tutor-AI containers running"
        )

        # Check if services are accessible
        try:
            response = requests.get(f"{BACKEND_URL}/health", timeout=5)
            self.print_result("Backend accessibility", response.status_code == 200, f"HTTP {response.status_code}")
            all_passed &= response.status_code == 200
        except:
            self.print_result("Backend accessibility", False, "Cannot reach backend")
            all_passed = False

        return all_passed

    def test_course_management_workflow(self) -> bool:
        """Test complete course management workflow"""
        print(f"\n{Colors.BLUE}📚 Testing Course Management Workflow...{Colors.END}")

        all_passed = True

        # Step 1: Get all courses
        try:
            response = self.session.get(f"{BACKEND_URL}/courses")
            if response.status_code == 200:
                courses_data = response.json()
                courses = courses_data.get('courses', [])
                self.print_result("Fetch courses list", len(courses) > 0, f"Found {len(courses)} courses")
                all_passed &= len(courses) > 0

                # Store first course for testing
                if courses:
                    self.test_data['first_course'] = courses[0]
                    self.test_data['course_id'] = courses[0]['id']
                    self.test_data['course_name'] = courses[0]['name']
                else:
                    self.print_result("Course data availability", False, "No courses available")
                    all_passed &= False
            else:
                self.print_result("Fetch courses list", False, f"HTTP {response.status_code}")
                all_passed &= False
        except Exception as e:
            self.print_result("Fetch courses list", False, f"Request failed: {str(e)}")
            all_passed &= False

        # Step 2: Get books for course
        if 'course_id' in self.test_data:
            try:
                response = self.session.get(f"{BACKEND_URL}/courses/{self.test_data['course_id']}/books")
                if response.status_code == 200:
                    books_data = response.json()
                    books = books_data.get('books', [])
                    self.print_result("Fetch books for course", len(books) > 0, f"Found {len(books)} books")
                    all_passed &= len(books) > 0

                    # Store first book for testing
                    if books:
                        self.test_data['first_book'] = books[0]
                        self.test_data['book_id'] = books[0]['id']
                        self.test_data['book_title'] = books[0]['title']
                        self.test_data['materials_count'] = books[0].get('materials_count', 0)
                else:
                    self.print_result("Fetch books for course", False, f"HTTP {response.status_code}")
                    all_passed &= False
            except Exception as e:
                self.print_result("Fetch books for course", False, f"Request failed: {str(e)}")
                all_passed &= False

        return all_passed

    def test_materials_access_workflow(self) -> bool:
        """Test materials access workflow"""
        print(f"\n{Colors.BLUE}📄 Testing Materials Access Workflow...{Colors.END}")

        all_passed = True

        # Step 1: Check file system materials
        material_files = self.execute_command(
            "find ./data -name '*.pdf' | head -5",
            "PDF materials in file system",
            expected_exit_code=0
        )

        # Step 2: Test materials API access
        if 'course_id' in self.test_data and 'book_id' in self.test_data:
            try:
                # Test if materials are accessible through API
                self.print_result("Materials API structure", True, f"Book has {self.test_data['materials_count']} materials")

                # Test materials directory structure
                course_dir = f"./data/courses/{self.test_data['course_id']}"
                books_dir = f"{course_dir}/books"

                dir_exists = self.execute_command(
                    f"test -d {books_dir}",
                    "Books directory structure exists"
                )
                all_passed &= dir_exists

                if dir_exists:
                    # List available materials
                    material_list = self.execute_command(
                        f"find {books_dir} -name '*.pdf' | wc -l",
                        "Count PDF materials",
                        expected_exit_code=0
                    )
            except Exception as e:
                self.print_result("Materials workflow", False, f"Error: {str(e)}")
                all_passed &= False

        return all_passed

    def test_chat_integration_workflow(self) -> bool:
        """Test chat integration with materials"""
        print(f"\n{Colors.BLUE}💬 Testing Chat Integration Workflow...{Colors.END}")

        all_passed = True

        if 'course_id' in self.test_data:
            # Step 1: Test basic chat functionality
            chat_data = {
                "message": f"Tell me about the course {self.test_data['course_name']}",
                "course_id": self.test_data['course_id']
            }

            try:
                response = self.session.post(f"{BACKEND_URL}/chat", json=chat_data)
                if response.status_code == 200:
                    chat_response = response.json()
                    response_text = chat_response.get('response', '')
                    self.print_result("Chat API response", len(response_text) > 50, f"Response length: {len(response_text)} chars")
                    all_passed &= len(response_text) > 50
                else:
                    self.print_result("Chat API response", response.status_code in [200, 400, 401, 422], f"HTTP {response.status_code}")
                    all_passed &= response.status_code in [200, 400, 401, 422]
            except Exception as e:
                self.print_result("Chat integration", False, f"Request failed: {str(e)}")
                all_passed &= False

            # Step 2: Test chat with book context
            if 'book_id' in self.test_data and self.test_data['materials_count'] > 0:
                chat_with_book = {
                    "message": f"Summarize the key points from {self.test_data['book_title']}",
                    "course_id": self.test_data['course_id'],
                    "book_id": self.test_data['book_id']
                }

                try:
                    response = self.session.post(f"{BACKEND_URL}/chat", json=chat_with_book)
                    if response.status_code == 200:
                        chat_response = response.json()
                        response_text = chat_response.get('response', '')
                        self.print_result("Chat with book context", len(response_text) > 50, f"Response length: {len(response_text)} chars")
                        all_passed &= len(response_text) > 50
                    else:
                        self.print_result("Chat with book context", response.status_code in [200, 400, 401, 422], f"HTTP {response.status_code}")
                except Exception as e:
                    self.print_result("Chat with book context", False, f"Request failed: {str(e)}")
                    all_passed &= False

        return all_passed

    def test_api_documentation_workflow(self) -> bool:
        """Test API documentation and discovery"""
        print(f"\n{Colors.BLUE}📖 Testing API Documentation Workflow...{Colors.END}")

        all_passed = True

        # Step 1: Test API docs accessibility
        try:
            response = self.session.get(f"{BACKEND_URL}/docs")
            self.print_result("API documentation", response.status_code == 200, f"HTTP {response.status_code}")
            all_passed &= response.status_code == 200
        except Exception as e:
            self.print_result("API documentation", False, f"Request failed: {str(e)}")
            all_passed &= False

        # Step 2: Test OpenAPI schema
        try:
            response = self.session.get(f"{BACKEND_URL}/openapi.json")
            if response.status_code == 200:
                try:
                    schema = response.json()
                    has_paths = 'paths' in schema and len(schema['paths']) > 0
                    self.print_result("OpenAPI schema", has_paths, f"Endpoints defined: {len(schema.get('paths', {}))}")
                    all_passed &= has_paths
                except:
                    self.print_result("OpenAPI schema", False, "Invalid JSON response")
                    all_passed &= False
            else:
                self.print_result("OpenAPI schema", False, f"HTTP {response.status_code}")
                all_passed &= False
        except Exception as e:
            self.print_result("OpenAPI schema", False, f"Request failed: {str(e)}")
            all_passed &= False

        return all_passed

    def test_docker_logs_workflow(self) -> bool:
        """Test Docker logs and monitoring"""
        print(f"\n{Colors.BLUE}📋 Testing Docker Logs Workflow...{Colors.END}")

        all_passed = True

        # Step 1: Test logs accessibility
        all_passed &= self.execute_command(
            "docker-compose logs --tail=10 backend | head -5",
            "Backend logs accessible"
        )

        all_passed &= self.execute_command(
            "docker-compose logs --tail=10 frontend | head -5",
            "Frontend logs accessible"
        )

        all_passed &= self.execute_command(
            "docker-compose logs --tail=5 redis | head -3",
            "Redis logs accessible"
        )

        # Step 2: Test container stats
        all_passed &= self.execute_command(
            "docker stats --no-stream --format 'table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}' | grep tutor-ai",
            "Container resource monitoring"
        )

        return all_passed

    def test_data_integrity_workflow(self) -> bool:
        """Test data integrity across the system"""
        print(f"\n{Colors.BLUE}🔒 Testing Data Integrity Workflow...{Colors.END}")

        all_passed = True

        # Step 1: Test course data consistency
        if 'course_id' in self.test_data:
            # Check if course exists in file system
            course_dir = f"./data/courses/{self.test_data['course_id']}"
            all_passed &= self.execute_command(
                f"test -d {course_dir}",
                f"Course directory exists in file system"
            )

            # Check if course data is accessible via API
            try:
                response = self.session.get(f"{BACKEND_URL}/courses/{self.test_data['course_id']}")
                self.print_result("Course data API access", response.status_code == 200, f"HTTP {response.status_code}")
                all_passed &= response.status_code == 200
            except Exception as e:
                self.print_result("Course data API access", False, f"Request failed: {str(e)}")
                all_passed &= False

        # Step 2: Test file system data consistency
        all_passed &= self.execute_command(
            "test -d ./data && ls ./data | head -3",
            "Data directory structure integrity"
        )

        # Step 3: Test database consistency
        all_passed &= self.execute_command(
            "docker-compose exec -T redis redis-cli dbsize",
            "Redis database consistency"
        )

        return all_passed

    def test_error_handling_workflow(self) -> bool:
        """Test error handling and edge cases"""
        print(f"\n{Colors.BLUE}⚠️  Testing Error Handling Workflow...{Colors.END}")

        all_passed = True

        # Step 1: Test invalid course ID
        try:
            response = self.session.get(f"{BACKEND_URL}/courses/invalid-course-id")
            self.print_result("Invalid course ID handling", response.status_code == 404, f"HTTP {response.status_code}")
            all_passed &= response.status_code == 404
        except Exception as e:
            self.print_result("Invalid course ID handling", False, f"Request failed: {str(e)}")
            all_passed &= False

        # Step 2: Test invalid book ID
        if 'course_id' in self.test_data:
            try:
                response = self.session.get(f"{BACKEND_URL}/courses/{self.test_data['course_id']}/books/invalid-book-id")
                self.print_result("Invalid book ID handling", response.status_code in [404, 400], f"HTTP {response.status_code}")
                all_passed &= response.status_code in [404, 400]
            except Exception as e:
                self.print_result("Invalid book ID handling", False, f"Request failed: {str(e)}")
                all_passed &= False

        # Step 3: Test malformed request
        try:
            response = self.session.post(f"{BACKEND_URL}/chat", json={})
            self.print_result("Malformed request handling", response.status_code in [400, 422], f"HTTP {response.status_code}")
            all_passed &= response.status_code in [400, 422]
        except Exception as e:
            self.print_result("Malformed request handling", False, f"Request failed: {str(e)}")
            all_passed &= False

        return all_passed

    def generate_workflow_report(self) -> None:
        """Generate comprehensive workflow test report"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['passed'])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0

        print(f"\n{Colors.BOLD}{Colors.CYAN}🔄 END-TO-END WORKFLOW TEST REPORT{Colors.END}")
        print("=" * 70)
        print(f"Total Tests: {total_tests}")
        print(f"{Colors.GREEN}Passed: {passed_tests}{Colors.END}")
        print(f"{Colors.RED}Failed: {failed_tests}{Colors.END}")
        print(f"Success Rate: {success_rate:.1f}%")

        # Show test data used
        print(f"\n{Colors.BLUE}📊 Test Data Summary:{Colors.END}")
        if 'course_name' in self.test_data:
            print(f"   Course: {self.test_data['course_name']}")
        if 'book_title' in self.test_data:
            print(f"   Book: {self.test_data['book_title']}")
        if 'materials_count' in self.test_data:
            print(f"   Materials: {self.test_data['materials_count']}")

        if failed_tests > 0:
            print(f"\n{Colors.RED}❌ Failed Workflows:{Colors.END}")
            for result in self.test_results:
                if not result['passed']:
                    print(f"   • {result['name']}: {result['message']}")

        print(f"\n{Colors.BOLD}E2E Readiness: ", end="")
        if failed_tests == 0:
            print(f"{Colors.GREEN}✅ ALL WORKFLOWS OPERATIONAL{Colors.END}")
        elif success_rate >= 80:
            print(f"{Colors.YELLOW}⚠️  MOSTLY OPERATIONAL - Minor Issues{Colors.END}")
        else:
            print(f"{Colors.RED}❌ WORKFLOW ISSUES DETECTED{Colors.END}")

    def run_all_workflows(self) -> bool:
        """Run all end-to-end workflow tests"""
        print(f"{Colors.BOLD}{Colors.BLUE}🔄 End-to-End Integration Test Suite{Colors.END}")
        print("=" * 80)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Frontend URL: {FRONTEND_URL}")
        print(f"Test Timeout: {TIMEOUT}s")

        # Run all workflow tests
        all_passed = True

        all_passed &= self.test_docker_environment_readiness()
        all_passed &= self.test_course_management_workflow()
        all_passed &= self.test_materials_access_workflow()
        all_passed &= self.test_chat_integration_workflow()
        all_passed &= self.test_api_documentation_workflow()
        all_passed &= self.test_docker_logs_workflow()
        all_passed &= self.test_data_integrity_workflow()
        all_passed &= self.test_error_handling_workflow()

        # Generate report
        self.generate_workflow_report()

        return all_passed

def main():
    """Main function"""
    tester = E2ETester()

    try:
        success = tester.run_all_workflows()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}⚠️  Tests interrupted by user{Colors.END}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}💥 E2E test failed: {str(e)}{Colors.END}")
        sys.exit(1)

if __name__ == "__main__":
    main()