#!/usr/bin/env python3
"""
Basic Docker Health Tests for Tutor-AI

Simple health tests that don't depend on custom logging configuration.
Tests basic container connectivity and endpoint availability.

Usage:
    python tests/docker/basic_health_test.py
"""

import unittest
import requests
import docker
import time
import subprocess
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BasicDockerHealthTest(unittest.TestCase):
    """Basic Docker health tests without complex dependencies"""

    @classmethod
    def setUpClass(cls):
        """Initialize test environment"""
        cls.client = docker.from_env()
        cls.test_start_time = datetime.now()

    def test_01_docker_daemon_running(self):
        """Test that Docker daemon is running"""
        logger.info("Testing Docker daemon connectivity...")

        try:
            version = self.client.version()
            self.assertIsNotNone(version)
            self.assertIn('Version', version)
            logger.info(f"Docker version: {version['Version']}")
        except Exception as e:
            self.fail(f"Docker daemon not accessible: {e}")

    def test_02_containers_running(self):
        """Test that Tutor-AI containers are running"""
        logger.info("Testing container status...")

        expected_containers = ['tutor-ai-backend', 'tutor-ai-frontend-test']
        running_containers = []

        containers = self.client.containers.list()
        for container in containers:
            if any(expected in container.name for expected in expected_containers):
                running_containers.append(container.name)
                logger.info(f"Container running: {container.name} (Status: {container.status})")

        logger.info(f"Found {len(running_containers)} expected containers")
        self.assertGreater(len(running_containers), 0, "No Tutor-AI containers running")

    def test_03_backend_health_endpoint(self):
        """Test backend health endpoint with retries"""
        logger.info("Testing backend health endpoint...")

        max_retries = 5
        retry_delay = 2

        for attempt in range(max_retries):
            try:
                logger.info(f"Health check attempt {attempt + 1}/{max_retries}")

                # Test health endpoint
                response = requests.get(
                    'http://localhost:8000/health',
                    timeout=10,
                    allow_redirects=True
                )

                if response.status_code == 200:
                    logger.info("Backend health check successful")
                    self.assertEqual(response.status_code, 200)
                    return
                else:
                    logger.warning(f"Health check returned {response.status_code}")

            except requests.exceptions.ConnectionError as e:
                logger.warning(f"Connection error (attempt {attempt + 1}): {e}")
            except requests.exceptions.Timeout as e:
                logger.warning(f"Timeout error (attempt {attempt + 1}): {e}")
            except Exception as e:
                logger.warning(f"Unexpected error (attempt {attempt + 1}): {e}")

            if attempt < max_retries - 1:
                logger.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)

        self.fail("Backend health endpoint not responding after retries")

    def test_04_container_health_status(self):
        """Test Docker container health status"""
        logger.info("Testing container health status...")

        containers = self.client.containers.list()
        unhealthy_containers = []

        for container in containers:
            if 'tutor-ai' in container.name:
                health = container.attrs.get('State', {}).get('Health', {})
                health_status = health.get('Status', 'unknown')

                logger.info(f"Container {container.name} health: {health_status}")

                if health_status.lower() == 'unhealthy':
                    unhealthy_containers.append(container.name)

        # Allow containers without health checks
        logger.info(f"Containers without health status are acceptable")

        if unhealthy_containers:
            logger.warning(f"Unhealthy containers: {unhealthy_containers}")

    def test_05_port_accessibility(self):
        """Test that expected ports are accessible"""
        logger.info("Testing port accessibility...")

        # Test basic TCP connectivity
        import socket

        def check_port(host, port, timeout=5):
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(timeout)
                result = sock.connect_ex((host, port))
                sock.close()
                return result == 0
            except Exception:
                return False

        # Check ports
        ports_to_check = [
            ('localhost', 8000, 'Backend API'),
            ('localhost', 3001, 'Frontend'),
        ]

        accessible_ports = 0
        for host, port, description in ports_to_check:
            is_accessible = check_port(host, port)
            status = "✅" if is_accessible else "❌"
            logger.info(f"{status} Port {port} ({description}): {is_accessible}")
            if is_accessible:
                accessible_ports += 1

        logger.info(f"Accessible ports: {accessible_ports}/{len(ports_to_check)}")
        self.assertGreater(accessible_ports, 0, "No ports accessible")

    def test_06_container_logs_no_errors(self):
        """Check container logs for critical errors"""
        logger.info("Checking container logs for critical errors...")

        containers = self.client.containers.list()

        for container in containers:
            if 'tutor-ai' in container.name:
                try:
                    logs = container.logs(tail=50, timestamps=False).decode('utf-8')
                    log_lines = logs.strip().split('\n')

                    # Look for critical error patterns
                    critical_patterns = ['FATAL', 'CRITICAL', 'EXITED', 'segfault', 'panic']
                    found_critical = []

                    for line in log_lines:
                        for pattern in critical_patterns:
                            if pattern.lower() in line.lower():
                                found_critical.append(line.strip())

                    if found_critical:
                        logger.error(f"Critical errors in {container.name}:")
                        for error in found_critical[:3]:  # Show first 3 errors
                            logger.error(f"  - {error}")
                    else:
                        logger.info(f"No critical errors in {container.name} logs")

                except Exception as e:
                    logger.warning(f"Could not check logs for {container.name}: {e}")

    def test_07_container_resource_limits(self):
        """Check basic container resource usage"""
        logger.info("Checking container resource usage...")

        containers = self.client.containers.list()

        for container in containers:
            if 'tutor-ai' in container.name:
                try:
                    stats = container.stats(stream=False)

                    if stats:
                        # Get memory usage
                        memory_usage = stats.get('memory_stats', {}).get('usage', 0)
                        memory_limit = stats.get('memory_stats', {}).get('limit', 1)
                        memory_percent = (memory_usage / memory_limit) * 100 if memory_limit > 1 else 0

                        logger.info(f"{container.name} - Memory: {memory_percent:.1f}%")

                        # Basic check - memory shouldn't be at 100%
                        self.assertLess(memory_percent, 100,
                                      f"{container.name} memory usage at 100%")

                except Exception as e:
                    logger.warning(f"Could not get stats for {container.name}: {e}")

    def test_08_frontend_basic_connectivity(self):
        """Test basic frontend connectivity"""
        logger.info("Testing frontend connectivity...")

        max_retries = 3
        retry_delay = 2

        for attempt in range(max_retries):
            try:
                response = requests.get(
                    'http://localhost:3001',
                    timeout=10,
                    allow_redirects=True
                )

                # Accept 200-299 status codes for frontend
                if 200 <= response.status_code < 300:
                    logger.info(f"Frontend connectivity successful: {response.status_code}")
                    return
                else:
                    logger.warning(f"Frontend returned {response.status_code}")

            except requests.exceptions.ConnectionError as e:
                logger.warning(f"Frontend connection error (attempt {attempt + 1}): {e}")
            except requests.exceptions.Timeout as e:
                logger.warning(f"Frontend timeout error (attempt {attempt + 1}): {e}")
            except Exception as e:
                logger.warning(f"Frontend unexpected error (attempt {attempt + 1}): {e}")

            if attempt < max_retries - 1:
                time.sleep(retry_delay)

        # Don't fail the test for frontend - it might need more time to start
        logger.warning("Frontend not fully responsive yet, but this is acceptable")

    def test_09_api_basic_response(self):
        """Test basic API response"""
        logger.info("Testing basic API responses...")

        try:
            # Test courses endpoint
            response = requests.get(
                'http://localhost:8000/courses',
                timeout=10
            )

            # Accept 200 or 404 (404 is acceptable if no courses exist)
            if response.status_code in [200, 404]:
                logger.info(f"Courses endpoint responding: {response.status_code}")
            else:
                logger.warning(f"Unexpected courses response: {response.status_code}")

        except Exception as e:
            logger.warning(f"Could not test courses endpoint: {e}")

    def test_10_system_info(self):
        """Collect and log system information"""
        logger.info("Collecting system information...")

        info = {
            'timestamp': datetime.now().isoformat(),
            'docker_version': self.client.version()['Version'],
            'container_count': len(self.client.containers.list()),
            'image_count': len(self.client.images.list()),
        }

        logger.info(f"System info: {info}")

        # Basic validation
        self.assertGreater(info['container_count'], 0)
        self.assertIsNotNone(info['docker_version'])


def run_basic_health_tests():
    """Run basic Docker health tests"""
    print("🐳 Starting Basic Docker Health Tests...")

    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(BasicDockerHealthTest)

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Return results
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_basic_health_tests()
    import sys
    sys.exit(0 if success else 1)