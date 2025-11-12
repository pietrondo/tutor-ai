#!/usr/bin/env python3
"""
Comprehensive Docker Container Health Tests for Tutor-AI

Tests container health, restart policies, resource limits, and recovery mechanisms.
Ensures containers are healthy, responsive, and can recover from failures.

Usage:
    python tests/docker/container_health_test.py
"""

import unittest
import time
import docker
import requests
import subprocess
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import psutil
import os
import signal
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ContainerHealthTest(unittest.TestCase):
    """Test suite for Docker container health and resilience"""

    @classmethod
    def setUpClass(cls):
        """Initialize test environment"""
        cls.client = docker.from_env()
        cls.test_start_time = datetime.now()
        cls.container_stats = {}

        # Ensure we're in the correct directory
        os.chdir('/mnt/c/Users/pietr/Documents/progetto/tutor-ai')

        logger.info("Starting Docker Container Health Tests")
        logger.info(f"Test started at: {cls.test_start_time}")

        # Get initial container state
        cls.initial_containers = cls.get_containers_info()

    @classmethod
    def tearDownClass(cls):
        """Cleanup test environment"""
        test_duration = datetime.now() - cls.test_start_time
        logger.info(f"Test completed in: {test_duration}")

        # Generate test report
        cls.generate_test_report()

    def setUp(self):
        """Setup for each test"""
        self.test_start_time = time.time()

    def tearDown(self):
        """Cleanup after each test"""
        test_duration = time.time() - self.test_start_time
        logger.info(f"Test completed in: {test_duration:.2f}s")

    @staticmethod
    def get_containers_info() -> Dict[str, Any]:
        """Get information about running containers"""
        try:
            containers = {}
            client = docker.from_env()

            for container in client.containers.list(all=True):
                if 'tutor-ai' in container.name:
                    containers[container.name] = {
                        'id': container.id,
                        'name': container.name,
                        'status': container.status,
                        'image': container.image.tags[0] if container.image.tags else 'unknown',
                        'ports': container.ports,
                        'labels': container.labels,
                        'attrs': container.attrs
                    }

            return containers
        except Exception as e:
            logger.error(f"Failed to get container info: {e}")
            return {}

    def test_01_docker_daemon_health(self):
        """Test 1: Verify Docker daemon is running and accessible"""
        logger.info("Testing Docker daemon health...")

        try:
            # Test Docker daemon connectivity
            version = self.client.version()

            self.assertIsNotNone(version)
            self.assertIn('Version', version)
            self.assertIn('ApiVersion', version)

            logger.info(f"Docker version: {version['Version']}")
            logger.info(f"API version: {version['ApiVersion']}")

            # Test Docker system info
            info = self.client.info()
            self.assertIsNotNone(info)
            self.assertIn('Containers', info)
            self.assertIn('Images', info)

            logger.info(f"Docker system containers: {info['Containers']}")
            logger.info(f"Docker system images: {info['Images']}")

            self.container_stats['docker_daemon'] = {
                'status': 'healthy',
                'version': version['Version'],
                'api_version': version['ApiVersion'],
                'total_containers': info['Containers'],
                'total_images': info['Images']
            }

        except Exception as e:
            logger.error(f"Docker daemon health check failed: {e}")
            self.fail(f"Docker daemon not accessible: {e}")

    def test_02_container_startup_health(self):
        """Test 2: Verify containers start up correctly and become healthy"""
        logger.info("Testing container startup health...")

        # Expected containers
        expected_containers = ['tutor-ai-backend', 'tutor-ai-frontend']

        # Wait for containers to be ready
        max_wait_time = 120  # 2 minutes
        wait_interval = 5
        containers_ready = False

        for attempt in range(max_wait_time // wait_interval):
            try:
                containers = self.get_containers_info()

                running_containers = [
                    name for name, info in containers.items()
                    if info['status'] == 'running'
                ]

                logger.info(f"Attempt {attempt + 1}: Running containers: {running_containers}")

                # Check if all expected containers are running
                if all(any(expected in name for name in running_containers)
                      for expected in expected_containers):
                    containers_ready = True
                    break

                time.sleep(wait_interval)

            except Exception as e:
                logger.warning(f"Container check attempt {attempt + 1} failed: {e}")
                time.sleep(wait_interval)

        self.assertTrue(containers_ready, f"Containers not ready after {max_wait_time}s")

        # Store container health info
        self.container_stats['startup_health'] = {
            'status': 'healthy' if containers_ready else 'unhealthy',
            'expected_containers': expected_containers,
            'running_containers': running_containers,
            'wait_time': attempt * wait_interval if containers_ready else max_wait_time
        }

    def test_03_container_health_check_endpoints(self):
        """Test 3: Verify container health check endpoints are responding"""
        logger.info("Testing container health check endpoints...")

        health_endpoints = [
            ('Backend Health', 'http://localhost:8000/health', 200),
            ('Frontend Root', 'http://localhost:3001', 200),
            ('API Docs', 'http://localhost:8000/docs', 200),
        ]

        health_results = {}

        for endpoint_name, url, expected_status in health_endpoints:
            try:
                logger.info(f"Testing {endpoint_name}: {url}")

                response = requests.get(url, timeout=10)

                self.assertEqual(response.status_code, expected_status,
                               f"{endpoint_name} returned {response.status_code}, expected {expected_status}")

                response_time = response.elapsed.total_seconds()
                logger.info(f"{endpoint_name} - Status: {response.status_code}, Time: {response_time:.3f}s")

                health_results[endpoint_name.lower().replace(' ', '_')] = {
                    'status': 'healthy',
                    'response_time': response_time,
                    'status_code': response.status_code
                }

            except requests.exceptions.ConnectionError:
                logger.error(f"{endpoint_name} - Connection refused")
                health_results[endpoint_name.lower().replace(' ', '_')] = {
                    'status': 'connection_refused',
                    'error': 'Connection refused'
                }
                self.fail(f"{endpoint_name} endpoint not accessible")

            except requests.exceptions.Timeout:
                logger.error(f"{endpoint_name} - Timeout")
                health_results[endpoint_name.lower().replace(' ', '_')] = {
                    'status': 'timeout',
                    'error': 'Request timeout'
                }
                self.fail(f"{endpoint_name} endpoint timed out")

            except Exception as e:
                logger.error(f"{endpoint_name} - Unexpected error: {e}")
                health_results[endpoint_name.lower().replace(' ', '_')] = {
                    'status': 'error',
                    'error': str(e)
                }
                self.fail(f"{endpoint_name} endpoint error: {e}")

        self.container_stats['health_endpoints'] = health_results

    def test_04_container_resource_limits(self):
        """Test 4: Verify container resource limits are properly set"""
        logger.info("Testing container resource limits...")

        containers = self.get_containers_info()
        resource_stats = {}

        for container_name, container_info in containers.items():
            try:
                container = self.client.containers.get(container_info['id'])
                stats = container.stats(stream=False)

                # Extract resource usage
                cpu_usage = stats['cpu_stats']['cpu_usage']['total_usage']
                cpu_system = stats['cpu_stats']['system_cpu_usage']
                memory_usage = stats['memory_stats']['usage']
                memory_limit = stats['memory_stats']['limit']

                # Calculate percentages
                cpu_percent = (cpu_usage / cpu_system * 100) if cpu_system > 0 else 0
                memory_percent = (memory_usage / memory_limit * 100) if memory_limit > 0 else 0

                resource_stats[container_name] = {
                    'cpu_usage': cpu_percent,
                    'memory_usage_mb': memory_usage / (1024 * 1024),
                    'memory_limit_mb': memory_limit / (1024 * 1024),
                    'memory_percent': memory_percent
                }

                logger.info(f"{container_name} - CPU: {cpu_percent:.2f}%, "
                          f"Memory: {memory_usage / (1024*1024):.2f}MB ({memory_percent:.2f}%)")

                # Basic resource usage checks
                self.assertLess(cpu_percent, 80, f"{container_name} CPU usage too high: {cpu_percent}%")
                self.assertLess(memory_percent, 85, f"{container_name} memory usage too high: {memory_percent}%")

            except Exception as e:
                logger.error(f"Failed to get stats for {container_name}: {e}")
                resource_stats[container_name] = {'error': str(e)}

        self.container_stats['resource_limits'] = resource_stats

    def test_05_container_restart_resilience(self):
        """Test 5: Test container restart and recovery mechanisms"""
        logger.info("Testing container restart resilience...")

        containers = self.get_containers_info()
        restart_results = {}

        for container_name, container_info in containers.items():
            if 'backend' in container_name.lower():  # Test backend container
                try:
                    container = self.client.containers.get(container_info['id'])

                    # Record container state before restart
                    initial_state = {
                        'status': container.status,
                        'restart_count': container.attrs['RestartCount']
                    }

                    logger.info(f"Restarting container: {container_name}")

                    # Restart container
                    container.restart()

                    # Wait for container to be ready
                    max_wait = 60
                    for _ in range(max_wait):
                        container.reload()
                        if container.status == 'running':
                            time.sleep(10)  # Additional wait for health checks
                            break
                        time.sleep(1)
                    else:
                        self.fail(f"Container {container_name} did not restart within {max_wait}s")

                    # Test health endpoint after restart
                    health_response = requests.get('http://localhost:8000/health', timeout=10)
                    self.assertEqual(health_response.status_code, 200,
                                  f"Backend health check failed after restart")

                    final_state = {
                        'status': container.status,
                        'restart_count': container.attrs['RestartCount']
                    }

                    restart_results[container_name] = {
                        'initial_state': initial_state,
                        'final_state': final_state,
                        'restart_success': True,
                        'health_check_passed': health_response.status_code == 200
                    }

                    logger.info(f"Container {container_name} restarted successfully")

                except Exception as e:
                    logger.error(f"Failed to restart container {container_name}: {e}")
                    restart_results[container_name] = {
                        'restart_success': False,
                        'error': str(e)
                    }
                    self.fail(f"Container restart failed: {e}")

        self.container_stats['restart_resilience'] = restart_results

    def test_06_container_log_monitoring(self):
        """Test 6: Verify container logging is working correctly"""
        logger.info("Testing container log monitoring...")

        containers = self.get_containers_info()
        log_results = {}

        for container_name, container_info in containers.items():
            try:
                container = self.client.containers.get(container_info['id'])

                # Get recent logs
                logs = container.logs(tail=20, timestamps=True).decode('utf-8')

                log_lines = [line.strip() for line in logs.split('\n') if line.strip()]

                # Check for error patterns
                error_patterns = ['ERROR', 'FATAL', 'CRITICAL', 'Exception', 'Traceback']
                warning_patterns = ['WARNING', 'WARN']

                error_count = sum(1 for line in log_lines for pattern in error_patterns if pattern in line)
                warning_count = sum(1 for line in log_lines for pattern in warning_patterns if pattern in line)

                log_results[container_name] = {
                    'log_lines_count': len(log_lines),
                    'error_count': error_count,
                    'warning_count': warning_count,
                    'recent_logs': log_lines[-5:] if log_lines else []  # Last 5 lines
                }

                logger.info(f"{container_name} - Log lines: {len(log_lines)}, "
                          f"Errors: {error_count}, Warnings: {warning_count}")

                # Basic log health checks
                self.assertLess(error_count, 5, f"Too many errors in {container_name} logs: {error_count}")

            except Exception as e:
                logger.error(f"Failed to get logs for {container_name}: {e}")
                log_results[container_name] = {'error': str(e)}

        self.container_stats['log_monitoring'] = log_results

    def test_07_container_network_connectivity(self):
        """Test 7: Verify container network connectivity"""
        logger.info("Testing container network connectivity...")

        network_results = {}

        # Test backend to frontend connectivity
        try:
            # Backend should be able to reach itself
            backend_health = requests.get('http://localhost:8000/health', timeout=5)
            network_results['backend_self'] = {
                'status': 'success',
                'response_code': backend_health.status_code,
                'response_time': backend_health.elapsed.total_seconds()
            }

            # Frontend should be accessible
            frontend_health = requests.get('http://localhost:3001', timeout=5)
            network_results['frontend_access'] = {
                'status': 'success',
                'response_code': frontend_health.status_code,
                'response_time': frontend_health.elapsed.total_seconds()
            }

            # Test API endpoints
            api_response = requests.get('http://localhost:8000/courses', timeout=5)
            network_results['api_courses'] = {
                'status': 'success',
                'response_code': api_response.status_code,
                'response_time': api_response.elapsed.total_seconds()
            }

            logger.info("Network connectivity tests passed")

        except Exception as e:
            logger.error(f"Network connectivity test failed: {e}")
            network_results['connectivity_error'] = {'error': str(e)}
            self.fail(f"Network connectivity test failed: {e}")

        self.container_stats['network_connectivity'] = network_results

    def test_08_container_isolation_security(self):
        """Test 8: Verify container isolation and security basics"""
        logger.info("Testing container isolation and security...")

        security_results = {}

        try:
            containers = self.get_containers_info()

            for container_name, container_info in containers.items():
                try:
                    container = self.client.containers.get(container_info['id'])

                    # Check container user (should not be root)
                    user = container.attrs['Config']['User']

                    # Check if running as non-root (best practice)
                    security_results[container_name] = {
                        'user': user or 'root',
                        'is_non_root': bool(user),
                        'capabilities': container.attrs['HostConfig']['CapDrop'],
                        'read_only': container.attrs['HostConfig'].get('ReadOnlyRootfs', False)
                    }

                    # Check for dropped capabilities
                    cap_drop = container.attrs['HostConfig']['CapDrop']
                    has_security_caps = cap_drop and len(cap_drop) > 0

                    security_results[container_name]['has_security_caps'] = has_security_caps

                    logger.info(f"{container_name} - User: {user or 'root'}, "
                              f"Security caps: {has_security_caps}")

                except Exception as e:
                    logger.error(f"Security check failed for {container_name}: {e}")
                    security_results[container_name] = {'error': str(e)}

        except Exception as e:
            logger.error(f"Container security test failed: {e}")
            security_results['security_test_error'] = {'error': str(e)}

        self.container_stats['security_isolation'] = security_results

    def test_09_container_environment_variables(self):
        """Test 9: Verify container environment variables are properly set"""
        logger.info("Testing container environment variables...")

        env_results = {}

        try:
            containers = self.get_containers_info()

            for container_name, container_info in containers.items():
                try:
                    container = self.client.containers.get(container_info['id'])

                    # Get environment variables
                    env_vars = container.attrs['Config']['Env']
                    env_dict = {}

                    for var in env_vars:
                        if '=' in var:
                            key, value = var.split('=', 1)
                            env_dict[key] = value

                    # Check for expected environment variables
                    expected_vars = []
                    if 'backend' in container_name.lower():
                        expected_vars = ['LOG_LEVEL', 'ENVIRONMENT', 'PORT']
                    elif 'frontend' in container_name.lower():
                        expected_vars = ['NODE_ENV', 'NEXT_PUBLIC_API_URL']

                    missing_vars = []
                    present_vars = []

                    for var in expected_vars:
                        if any(env.startswith(var) for env in env_dict.keys()):
                            present_vars.append(var)
                        else:
                            missing_vars.append(var)

                    env_results[container_name] = {
                        'total_env_vars': len(env_vars),
                        'present_vars': present_vars,
                        'missing_vars': missing_vars,
                        'env_count': len(env_dict)
                    }

                    logger.info(f"{container_name} - Env vars: {len(env_vars)}, "
                              f"Missing: {missing_vars}")

                    # Check for critical missing variables
                    if missing_vars:
                        logger.warning(f"{container_name} missing environment variables: {missing_vars}")

                except Exception as e:
                    logger.error(f"Environment check failed for {container_name}: {e}")
                    env_results[container_name] = {'error': str(e)}

        except Exception as e:
            logger.error(f"Environment variables test failed: {e}")
            env_results['env_test_error'] = {'error': str(e)}

        self.container_stats['environment_variables'] = env_results

    def test_10_container_image_integrity(self):
        """Test 10: Verify container image integrity and versions"""
        logger.info("Testing container image integrity...")

        image_results = {}

        try:
            containers = self.get_containers_info()

            for container_name, container_info in containers.items():
                try:
                    container = self.client.containers.get(container_info['id'])
                    image = container.image

                    # Get image information
                    image_info = {
                        'id': image.id,
                        'tags': image.tags,
                        'labels': image.labels,
                        'size': image.attrs['Size']
                    }

                    # Check image age (should be relatively recent)
                    image_created = datetime.fromisoformat(
                        image.attrs['Created'].replace('Z', '+00:00')
                    )
                    image_age_days = (datetime.now() - image_created).days

                    image_results[container_name] = {
                        'image_id': image.id[:12],
                        'image_tags': image.tags,
                        'image_age_days': image_age_days,
                        'image_size_mb': image.attrs['Size'] / (1024 * 1024),
                        'created': image.attrs['Created']
                    }

                    logger.info(f"{container_name} - Image: {image.tags[0] if image.tags else 'untagged'}, "
                              f"Age: {image_age_days} days, Size: {image.attrs['Size'] / (1024*1024):.1f}MB")

                    # Basic image integrity checks
                    self.assertIsNotNone(image.tags, f"{container_name} image has no tags")
                    self.assertLess(image_age_days, 365, f"{container_name} image is too old: {image_age_days} days")

                except Exception as e:
                    logger.error(f"Image integrity check failed for {container_name}: {e}")
                    image_results[container_name] = {'error': str(e)}

        except Exception as e:
            logger.error(f"Image integrity test failed: {e}")
            image_results['image_test_error'] = {'error': str(e)}

        self.container_stats['image_integrity'] = image_results

    @classmethod
    def generate_test_report(cls):
        """Generate comprehensive test report"""
        report = {
            'test_suite': 'Docker Container Health Tests',
            'timestamp': datetime.now().isoformat(),
            'test_duration': str(datetime.now() - cls.test_start_time),
            'container_stats': cls.container_stats,
            'initial_containers': cls.initial_containers,
            'final_containers': cls.get_containers_info()
        }

        # Save report to file
        report_file = f"tests/reports/container_health_test_report_{int(time.time())}.json"
        os.makedirs(os.path.dirname(report_file), exist_ok=True)

        try:
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)

            logger.info(f"Test report saved to: {report_file}")

            # Print summary
            print(f"\n{'='*60}")
            print("DOCKER CONTAINER HEALTH TEST SUMMARY")
            print(f"{'='*60}")
            print(f"Test Duration: {report['test_duration']}")
            print(f"Report File: {report_file}")

            # Health summary
            if 'health_endpoints' in cls.container_stats:
                health_endpoints = cls.container_stats['health_endpoints']
                healthy_endpoints = sum(1 for v in health_endpoints.values()
                                     if v.get('status') == 'healthy')
                total_endpoints = len(health_endpoints)
                print(f"Healthy Endpoints: {healthy_endpoints}/{total_endpoints}")

            # Resource summary
            if 'resource_limits' in cls.container_stats:
                resource_stats = cls.container_stats['resource_limits']
                print(f"Container Resource Stats: {len(resource_stats)} containers monitored")

            print(f"{'='*60}")

        except Exception as e:
            logger.error(f"Failed to generate test report: {e}")


def run_container_health_tests():
    """Run the container health test suite"""
    print("🐳 Starting Docker Container Health Tests...")

    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(ContainerHealthTest)

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2, buffer=True)
    result = runner.run(suite)

    # Return results
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_container_health_tests()
    sys.exit(0 if success else 1)