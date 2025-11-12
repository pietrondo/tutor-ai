#!/usr/bin/env python3
"""
Comprehensive API Testing Script for Tutor-AI
Tests API endpoints, CORS, and communication between frontend and backend
"""

import requests
import json
import sys
import time
from typing import Dict, List, Tuple, Any

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

class APITester:
    def __init__(self):
        self.test_results = []
        self.session = requests.Session()
        self.session.timeout = TIMEOUT

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

    def test_endpoint(self, method: str, url: str, expected_status: int = 200,
                     headers: Dict = None, data: Any = None, test_name: str = None) -> bool:
        """Test an HTTP endpoint"""
        if test_name is None:
            test_name = f"{method} {url}"

        try:
            response = self.session.request(method, url, headers=headers, json=data)
            passed = response.status_code == expected_status
            message = f"Expected {expected_status}, got {response.status_code}" if not passed else f"HTTP {response.status_code}"
            self.print_result(test_name, passed, message)
            return passed
        except requests.exceptions.RequestException as e:
            self.print_result(test_name, False, f"Request failed: {str(e)}")
            return False

    def test_backend_health(self) -> bool:
        """Test backend health endpoint"""
        print(f"\n{Colors.BLUE}🏥 Testing Backend Health...{Colors.END}")
        try:
            response = self.session.get(f"{BACKEND_URL}/health")
            health_data = response.json()

            # Check if response is valid JSON and contains status
            passed = response.status_code == 200 and health_data.get('status') == 'healthy'
            message = f"Status: {health_data.get('status', 'unknown')}" if passed else "Invalid health response"
            self.print_result("Backend health check", passed, message)
            return passed
        except Exception as e:
            self.print_result("Backend health check", False, f"Health check failed: {str(e)}")
            return False

    def test_api_endpoints(self) -> bool:
        """Test core API endpoints"""
        print(f"\n{Colors.BLUE}🔌 Testing API Endpoints...{Colors.END}")

        all_passed = True

        # Test courses endpoint
        all_passed &= self.test_endpoint("GET", f"{BACKEND_URL}/courses", 200, test_name="Courses API")

        # Test API documentation
        all_passed &= self.test_endpoint("GET", f"{BACKEND_URL}/docs", 200, test_name="API Documentation")

        # Test OpenAPI schema
        all_passed &= self.test_endpoint("GET", f"{BACKEND_URL}/openapi.json", 200, test_name="OpenAPI Schema")

        return all_passed

    def test_cors_configuration(self) -> bool:
        """Test CORS configuration"""
        print(f"\n{Colors.BLUE}🌐 Testing CORS Configuration...{Colors.END}")

        all_passed = True

        # Test preflight request for courses
        headers = {
            'Origin': FRONTEND_URL,
            'Access-Control-Request-Method': 'GET',
            'Access-Control-Request-Headers': 'Content-Type'
        }

        try:
            response = self.session.options(f"{BACKEND_URL}/courses", headers=headers)

            # Check if CORS headers are present
            cors_headers = {
                'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
                'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
                'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers')
            }

            # Check if our origin is allowed
            allowed_origin = cors_headers['Access-Control-Allow-Origin']
            cors_passed = allowed_origin in [FRONTEND_URL, '*']

            message = f"Origin allowed: {allowed_origin}" if cors_passed else f"Origin not allowed: {allowed_origin}"
            self.print_result("CORS preflight for /courses", cors_passed, message)

            # Check if required methods are allowed
            allowed_methods = cors_headers['Access-Control-Allow-Methods'] or ''
            methods_passed = 'GET' in allowed_methods and 'POST' in allowed_methods
            message = f"Methods allowed: {allowed_methods}" if methods_passed else f"Missing required methods: {allowed_methods}"
            self.print_result("CORS methods check", methods_passed, message)

            all_passed &= cors_passed and methods_passed

        except Exception as e:
            self.print_result("CORS configuration test", False, f"CORS test failed: {str(e)}")
            all_passed = False

        return all_passed

    def test_course_data_flow(self) -> bool:
        """Test complete data flow for courses"""
        print(f"\n{Colors.BLUE}📚 Testing Course Data Flow...{Colors.END}")

        all_passed = True

        try:
            # Get courses list
            response = self.session.get(f"{BACKEND_URL}/courses")
            if response.status_code != 200:
                self.print_result("Get courses list", False, f"Failed to get courses: {response.status_code}")
                return False

            courses_data = response.json()
            courses = courses_data.get('courses', [])

            if not courses:
                self.print_result("Course data availability", False, "No courses found in system")
                return False

            self.print_result("Course data availability", True, f"Found {len(courses)} courses")

            # Test first course details
            first_course = courses[0]
            course_id = first_course.get('id')

            if course_id:
                # Test course books endpoint
                all_passed &= self.test_endpoint("GET", f"{BACKEND_URL}/courses/{course_id}/books", 200,
                                                test_name=f"Course books ({course_id[:8]}...)")

                # Test course materials
                all_passed &= self.test_endpoint("GET", f"{BACKEND_URL}/courses/{course_id}/materials", 200,
                                                test_name=f"Course materials ({course_id[:8]}...)")

        except Exception as e:
            self.print_result("Course data flow test", False, f"Data flow test failed: {str(e)}")
            all_passed = False

        return all_passed

    def test_chat_functionality(self) -> bool:
        """Test chat API functionality"""
        print(f"\n{Colors.BLUE}💬 Testing Chat Functionality...{Colors.END}")

        all_passed = True

        # Test basic chat endpoint
        chat_data = {
            "message": "Hello, this is a test message",
            "course_id": "test-course"
        }

        # Note: This might fail due to authentication or missing course data
        # We're mainly testing if the endpoint exists and responds appropriately
        try:
            response = self.session.post(f"{BACKEND_URL}/chat", json=chat_data)

            # Chat might return 401 (unauthorized), 400 (bad request), or 200 (success)
            # All of these indicate the endpoint is working
            passed = response.status_code in [200, 400, 401, 422]
            message = f"Chat endpoint responding (HTTP {response.status_code})"
            self.print_result("Chat endpoint accessibility", passed, message)
            all_passed &= passed

        except Exception as e:
            self.print_result("Chat endpoint test", False, f"Chat test failed: {str(e)}")
            all_passed = False

        return all_passed

    def test_frontend_connectivity(self) -> bool:
        """Test frontend connectivity"""
        print(f"\n{Colors.BLUE}🖥️  Testing Frontend Connectivity...{Colors.END}")

        all_passed = True

        try:
            # Test main page
            response = self.session.get(FRONTEND_URL, timeout=5)
            passed = response.status_code == 200
            message = f"Frontend accessible (HTTP {response.status_code})" if passed else f"Frontend not accessible (HTTP {response.status_code})"
            self.print_result("Frontend main page", passed, message)
            all_passed &= passed

            # Test courses page
            response = self.session.get(f"{FRONTEND_URL}/courses", timeout=5)
            passed = response.status_code == 200
            message = f"Courses page accessible (HTTP {response.status_code})" if passed else f"Courses page not accessible (HTTP {response.status_code})"
            self.print_result("Frontend courses page", passed, message)
            all_passed &= passed

        except requests.exceptions.RequestException as e:
            self.print_result("Frontend connectivity", False, f"Frontend connection failed: {str(e)}")
            all_passed = False

        return all_passed

    def run_all_tests(self) -> bool:
        """Run all test suites"""
        print(f"{Colors.BOLD}🧪 Tutor-AI API Test Suite{Colors.END}")
        print("=" * 50)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Frontend URL: {FRONTEND_URL}")
        print(f"Timeout: {TIMEOUT}s")

        # Run all test suites
        all_passed = True
        all_passed &= self.test_backend_health()
        all_passed &= self.test_frontend_connectivity()
        all_passed &= self.test_api_endpoints()
        all_passed &= self.test_cors_configuration()
        all_passed &= self.test_course_data_flow()
        all_passed &= self.test_chat_functionality()

        # Display summary
        self.display_summary()

        return all_passed

    def display_summary(self):
        """Display test summary"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['passed'])
        failed_tests = total_tests - passed_tests

        print(f"\n{Colors.BLUE}📊 Test Summary{Colors.END}")
        print("=" * 30)
        print(f"Total Tests: {total_tests}")
        print(f"{Colors.GREEN}Passed: {passed_tests}{Colors.END}")
        print(f"{Colors.RED}Failed: {failed_tests}{Colors.END}")

        if failed_tests > 0:
            print(f"\n{Colors.RED}❌ Failed Tests:{Colors.END}")
            for result in self.test_results:
                if not result['passed']:
                    print(f"   • {result['name']}: {result['message']}")

        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        print(f"\nSuccess Rate: {success_rate:.1f}%")

        if failed_tests == 0:
            print(f"\n{Colors.GREEN}🎉 All tests passed! System is fully operational.{Colors.END}")
        else:
            print(f"\n{Colors.YELLOW}⚠️  Some tests failed. Please check the issues above.{Colors.END}")

def main():
    """Main function"""
    tester = APITester()

    try:
        success = tester.run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}⚠️  Tests interrupted by user.{Colors.END}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}💥 Test suite failed with error: {str(e)}{Colors.END}")
        sys.exit(1)

if __name__ == "__main__":
    main()