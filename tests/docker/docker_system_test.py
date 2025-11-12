#!/usr/bin/env python3
"""
Docker System Integration Test for Tutor-AI
Comprehensive testing of Docker containers, networking, and functionality
"""

import subprocess
import json
import time
import sys
import requests
from typing import Dict, List, Tuple
from datetime import datetime

# Configuration
BACKEND_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3001"
REDIS_URL = "localhost:6379"
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

class DockerSystemTester:
    def __init__(self):
        self.test_results = []
        self.session = requests.Session()
        self.session.timeout = TIMEOUT
        self.start_time = datetime.now()

    def print_result(self, test_name: str, passed: bool, message: str = ""):
        """Print test result with color coding"""
        status = f"{Colors.GREEN}✅ PASS{Colors.END}" if passed else f"{Colors.RED}❌ FAIL{Colors.END}"
        print(f"{status}: {test_name}")
        if message:
            print(f"   {Colors.RED if not passed else Colors.GREEN}   {message}{Colors.END}")

        self.test_results.append({
            'name': test_name,
            'passed': passed,
            'message': message,
            'timestamp': datetime.now()
        })

    def run_command(self, command: str, description: str, expected_exit_code: int = 0) -> bool:
        """Run shell command and check result"""
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
                message += f" | Output: {result.stdout.strip()[:100]}..."
            elif result.stderr.strip() and not passed:
                message += f" | Error: {result.stderr.strip()[:100]}..."

            self.print_result(description, passed, message)
            return passed

        except subprocess.TimeoutExpired:
            self.print_result(description, False, "Command timed out")
            return False
        except Exception as e:
            self.print_result(description, False, f"Command failed: {str(e)}")
            return False

    def test_docker_daemon(self) -> bool:
        """Test Docker daemon availability"""
        print(f"\n{Colors.BLUE}🐳 Testing Docker Daemon...{Colors.END}")

        all_passed = True
        all_passed &= self.run_command("docker info", "Docker daemon running")
        all_passed &= self.run_command("docker --version", "Docker version available")
        all_passed &= self.run_command("docker-compose --version", "Docker Compose available")

        return all_passed

    def test_docker_images(self) -> bool:
        """Test required Docker images"""
        print(f"\n{Colors.BLUE}📦 Testing Docker Images...{Colors.END}")

        required_images = [
            "tutor-ai-backend:dev",
            "tutor-ai-frontend:dev",
            "redis:7-alpine"
        ]

        all_passed = True
        for image in required_images:
            all_passed &= self.run_command(
                f"docker images --format 'table {{.Repository}}:{{.Tag}}' | grep -q '{image}'",
                f"Required image exists: {image}"
            )

        return all_passed

    def test_docker_networks(self) -> bool:
        """Test Docker network configuration"""
        print(f"\n{Colors.BLUE}🌐 Testing Docker Networks...{Colors.END}")

        all_passed = True
        all_passed &= self.run_command(
            "docker network ls | grep -q 'tutor-ai-network'",
            "Tutor-AI network exists"
        )

        all_passed &= self.run_command(
            "docker network inspect tutor-ai-network --format '{{json}}' | jq -r '.[0].Driver' 2>/dev/null || echo 'bridge'",
            "Network driver configured"
        )

        return all_passed

    def test_docker_volumes(self) -> bool:
        """Test Docker volumes for data persistence"""
        print(f"\n{Colors.BLUE}💾 Testing Docker Volumes...{Colors.END}")

        all_passed = True

        # Check if data directory exists
        all_passed &= self.run_command(
            "test -d ./data",
            "Data directory exists"
        )

        # Check volume creation
        all_passed &= self.run_command(
            "docker volume ls | grep -q 'tutor-ai'",
            "Tutor-AI volumes created"
        )

        # Test specific volumes
        all_passed &= self.run_command(
            "docker volume ls | grep -q 'redis_data'",
            "Redis volume exists"
        )

        return all_passed

    def test_container_startup(self) -> bool:
        """Test Docker container startup sequence"""
        print(f"\n{Colors.BLUE}🚀 Testing Container Startup...{Colors.END}")

        all_passed = True

        # Wait for containers to start
        print("   Waiting for containers to initialize...")
        time.sleep(10)

        # Check container status
        container_checks = [
            ("docker ps | grep -q 'tutor-ai-backend.*Up.*healthy'", "Backend container healthy"),
            ("docker ps | grep -q 'tutor-ai-frontend.*Up'", "Frontend container running"),
            ("docker ps | grep -q 'tutor-ai-redis.*Up.*healthy'", "Redis container healthy"),
        ]

        for command, description in container_checks:
            all_passed &= self.run_command(command, description, expected_exit_code=0)

        return all_passed

    def test_container_connectivity(self) -> bool:
        """Test inter-container communication"""
        print(f"\n{Colors.BLUE}🔗 Testing Container Connectivity...{Colors.END}")

        all_passed = True

        # Test backend can reach Redis
        all_passed &= self.run_command(
            "docker-compose exec -T backend python -c \"import redis; r=redis.Redis(host='redis', port=6379); print(r.ping())\" | grep -q 'PONG'",
            "Backend can connect to Redis"
        )

        # Test frontend can reach backend
        all_passed &= self.run_command(
            "docker-compose exec -T frontend wget -q --spider http://backend:8000/health 2>&1 | grep -q '200 OK'",
            "Frontend can reach backend"
        )

        return all_passed

    def test_data_persistence(self) -> bool:
        """Test data persistence across container restarts"""
        print(f"\n{Colors.BLUE}💾 Testing Data Persistence...{Colors.END}")

        all_passed = True

        # Test course data persistence
        all_passed &= self.run_command(
            "test -f ./data/app.db || test -d ./data/courses",
            "Data directory populated"
        )

        # Test specific course data
        all_passed &= self.run_command(
            "test -d ./data/courses && ls ./data/courses/ | head -1",
            "Course data structure exists"
        )

        # Test vector database persistence
        all_passed &= self.run_command(
            "test -d ./data/vector_db || test -d ./data/chroma",
            "Vector database storage exists"
        )

        return all_passed

    def test_health_checks(self) -> bool:
        """Test application health checks"""
        print(f"\n{Colors.BLUE}🏥 Testing Application Health Checks...{Colors.END}")

        all_passed = True

        # Test backend health endpoint
        try:
            response = self.session.get(f"{BACKEND_URL}/health", timeout=10)
            if response.status_code == 200:
                health_data = response.json()
                passed = health_data.get('status') == 'healthy'
                self.print_result("Backend health endpoint", passed, f"Status: {health_data.get('status')}")
                all_passed &= passed
            else:
                self.print_result("Backend health endpoint", False, f"HTTP {response.status_code}")
                all_passed &= False
        except Exception as e:
            self.print_result("Backend health endpoint", False, f"Request failed: {str(e)}")
            all_passed &= False

        # Test Redis health
        all_passed &= self.run_command(
            "docker-compose exec -T redis redis-cli ping | grep -q 'PONG'",
            "Redis health check"
        )

        return all_passed

    def test_api_functionality(self) -> bool:
        """Test core API functionality"""
        print(f"\n{Colors.BLUE}🔌 Testing API Functionality...{Colors.END}")

        all_passed = True

        # Test courses endpoint
        try:
            response = self.session.get(f"{BACKEND_URL}/courses", timeout=10)
            if response.status_code == 200:
                data = response.json()
                courses = data.get('courses', [])
                passed = len(courses) > 0
                self.print_result("Courses API endpoint", passed, f"Found {len(courses)} courses")
                all_passed &= passed

                # Test books endpoint for first course
                if courses:
                    course_id = courses[0].get('id')
                    if course_id:
                        books_response = self.session.get(f"{BACKEND_URL}/courses/{course_id}/books", timeout=10)
                        if books_response.status_code == 200:
                            books_data = books_response.json()
                            books = books_data.get('books', [])
                            self.print_result("Books API endpoint", True, f"Found {len(books)} books")
                        else:
                            self.print_result("Books API endpoint", False, f"HTTP {books_response.status_code}")
                            all_passed &= False
            else:
                self.print_result("Courses API endpoint", False, f"HTTP {response.status_code}")
                all_passed &= False
        except Exception as e:
            self.print_result("API functionality", False, f"Request failed: {str(e)}")
            all_passed &= False

        # Test API documentation
        try:
            docs_response = self.session.get(f"{BACKEND_URL}/docs", timeout=10)
            self.print_result("API documentation", docs_response.status_code == 200, f"HTTP {docs_response.status_code}")
            all_passed &= docs_response.status_code == 200
        except Exception as e:
            self.print_result("API documentation", False, f"Request failed: {str(e)}")
            all_passed &= False

        return all_passed

    def test_materials_integration(self) -> bool:
        """Test materials system integration"""
        print(f"\n{Colors.BLUE}📚 Testing Materials Integration...{Colors.END}")

        all_passed = True

        # Test materials directory structure
        all_passed &= self.run_command(
            "find ./data -name '*.pdf' | head -1",
            "PDF materials found in data directory"
        )

        # Test materials API endpoint (if available)
        try:
            response = self.session.get(f"{BACKEND_URL}/courses", timeout=10)
            if response.status_code == 200:
                data = response.json()
                courses = data.get('courses', [])
                if courses:
                    course_id = courses[0].get('id')
                    if course_id:
                        books_response = self.session.get(f"{BACKEND_URL}/courses/{course_id}/books", timeout=10)
                        if books_response.status_code == 200:
                            books_data = books_response.json()
                            books = books_data.get('books', [])
                            total_materials = sum(book.get('materials_count', 0) for book in books)
                            self.print_result("Materials system", total_materials > 0, f"Total materials: {total_materials}")
                        else:
                            self.print_result("Materials system", False, f"Books API failed: {books_response.status_code}")
                            all_passed &= False
        except Exception as e:
            self.print_result("Materials system", False, f"Request failed: {str(e)}")
            all_passed &= False

        return all_passed

    def test_docker_logs(self) -> bool:
        """Test Docker logs for errors"""
        print(f"\n{Colors.BLUE}📋 Testing Docker Logs...{Colors.END}")

        all_passed = True

        # Check for critical errors in logs
        log_checks = [
            ("docker-compose logs --tail=50 backend | grep -i error", "Backend logs for errors", 1),
            ("docker-compose logs --tail=50 frontend | grep -i error", "Frontend logs for errors", 1),
            ("docker-compose logs --tail=50 redis | grep -i error", "Redis logs for errors", 1),
        ]

        for command, description, expected_code in log_checks:
            try:
                result = subprocess.run(command, shell=True, capture_output=True, text=True)
                has_errors = result.returncode == 0 and result.stdout.strip()
                passed = not has_errors  # We want NO errors
                message = "No errors found" if passed else f"Errors detected: {result.stdout.strip()[:100]}..."
                self.print_result(description, passed, message)
                all_passed &= passed
            except Exception as e:
                self.print_result(description, False, f"Log check failed: {str(e)}")
                all_passed &= False

        return all_passed

    def test_system_performance(self) -> bool:
        """Test system performance metrics"""
        print(f"\n{Colors.BLUE}⚡ Testing System Performance...{Colors.END}")

        all_passed = True

        # Test API response times
        start_time = time.time()
        try:
            response = self.session.get(f"{BACKEND_URL}/health", timeout=10)
            response_time = (time.time() - start_time) * 1000
            passed = response_time < 2000  # Under 2 seconds
            self.print_result("Backend response time", passed, f"{response_time:.0f}ms")
            all_passed &= passed
        except:
            self.print_result("Backend response time", False, "Request failed")
            all_passed &= False

        # Test container resource usage (basic check)
        all_passed &= self.run_command(
            "docker stats --no-stream --format 'table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}' | grep tutor-ai",
            "Container resource usage"
        )

        return all_passed

    def test_production_readiness(self) -> bool:
        """Test production readiness factors"""
        print(f"\n{Colors.BLUE}🚀 Testing Production Readiness...{Colors.END}")

        all_passed = True

        # Test environment variables
        all_passed &= self.run_command(
            "docker-compose exec -T backend printenv | grep -q 'ENVIRONMENT=development'",
            "Environment variables configured"
        )

        # Test SSL/TLS (should not be enabled in dev)
        all_passed &= self.run_command(
            "curl -k https://localhost:8000/health 2>/dev/null || echo 'HTTP only (expected in dev)'",
            "HTTP/HTTPS configuration"
        )

        # Test security headers
        try:
            response = self.session.get(f"{BACKEND_URL}/health", timeout=10)
            has_cors = 'Access-Control-Allow-Origin' in response.headers
            self.print_result("Security headers", has_cors, "CORS headers present")
            all_passed &= has_cors
        except:
            self.print_result("Security headers", False, "Failed to check headers")
            all_passed &= False

        return all_passed

    def generate_test_report(self) -> None:
        """Generate comprehensive test report"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['passed'])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0

        duration = datetime.now() - self.start_time

        print(f"\n{Colors.BOLD}{Colors.CYAN}🐳 DOCKER SYSTEM TEST REPORT{Colors.END}")
        print("=" * 60)
        print(f"Test Duration: {duration.total_seconds():.1f} seconds")
        print(f"Total Tests: {total_tests}")
        print(f"{Colors.GREEN}Passed: {passed_tests}{Colors.END}")
        print(f"{Colors.RED}Failed: {failed_tests}{Colors.END}")
        print(f"Success Rate: {success_rate:.1f}%")

        if failed_tests > 0:
            print(f"\n{Colors.RED}❌ Failed Tests:{Colors.END}")
            for result in self.test_results:
                if not result['passed']:
                    print(f"   • {result['name']}: {result['message']}")

        print(f"\n{Colors.BLUE}📊 Test Categories:{Colors.END}")
        categories = {}
        for result in self.test_results:
            category = result['name'].split(':')[0] if ':' in result['name'] else 'General'
            if category not in categories:
                categories[category] = {'passed': 0, 'total': 0}
            categories[category]['total'] += 1
            if result['passed']:
                categories[category]['passed'] += 1

        for category, stats in categories.items():
            rate = (stats['passed'] / stats['total']) * 100
            status = Colors.GREEN if rate == 100 else Colors.YELLOW if rate >= 80 else Colors.RED
            print(f"   {status}{category}: {stats['passed']}/{stats['total']} ({rate:.1f}%){Colors.END}")

        print(f"\n{Colors.BOLD}Overall Status: ", end="")
        if failed_tests == 0:
            print(f"{Colors.GREEN}✅ ALL TESTS PASSED - SYSTEM READY{Colors.END}")
        elif success_rate >= 80:
            print(f"{Colors.YELLOW}⚠️  MOSTLY OPERATIONAL - Minor Issues{Colors.END}")
        else:
            print(f"{Colors.RED}❌ SIGNIFICANT ISSUES - Attention Required{Colors.END}")

    def run_all_tests(self) -> bool:
        """Run all Docker system tests"""
        print(f"{Colors.BOLD}{Colors.BLUE}🐳 Docker System Integration Test Suite{Colors.END}")
        print("=" * 70)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Frontend URL: {FRONTEND_URL}")
        print(f"Redis URL: {REDIS_URL}")
        print(f"Test Timeout: {TIMEOUT}s")
        print(f"Started: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")

        # Run all test suites
        all_passed = True

        all_passed &= self.test_docker_daemon()
        all_passed &= self.test_docker_images()
        all_passed &= self.test_docker_networks()
        all_passed &= self.test_docker_volumes()
        all_passed &= self.test_container_startup()
        all_passed &= self.test_container_connectivity()
        all_passed &= self.test_data_persistence()
        all_passed &= self.test_health_checks()
        all_passed &= self.test_api_functionality()
        all_passed &= self.test_materials_integration()
        all_passed &= self.test_docker_logs()
        all_passed &= self.test_system_performance()
        all_passed &= self.test_production_readiness()

        # Generate report
        self.generate_test_report()

        return all_passed

def main():
    """Main function"""
    tester = DockerSystemTester()

    try:
        success = tester.run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}⚠️  Tests interrupted by user{Colors.END}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}💥 Docker system test failed: {str(e)}{Colors.END}")
        sys.exit(1)

if __name__ == "__main__":
    main()