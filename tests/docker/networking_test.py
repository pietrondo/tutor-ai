#!/usr/bin/env python3
"""
Docker Networking Tests for Tutor-AI

Comprehensive tests for Docker networking, container communication,
DNS resolution, port mapping, and network security.

Usage:
    python tests/docker/networking_test.py
"""

import unittest
import docker
import requests
import socket
import subprocess
import time
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import threading
import concurrent.futures
import psutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DockerNetworkingTest(unittest.TestCase):
    """Test suite for Docker networking capabilities"""

    @classmethod
    def setUpClass(cls):
        """Initialize test environment"""
        cls.client = docker.from_env()
        cls.test_start_time = datetime.now()
        cls.network_stats = {}

        # Ensure we're in the correct directory
        import os
        os.chdir('/mnt/c/Users/pietr/Documents/progetto/tutor-ai')

        logger.info("Starting Docker Networking Tests")
        logger.info(f"Test started at: {cls.test_start_time}")

    @classmethod
    def tearDownClass(cls):
        """Cleanup and generate reports"""
        test_duration = datetime.now() - cls.test_start_time
        logger.info(f"Network tests completed in: {test_duration}")
        cls.generate_network_report()

    def setUp(self):
        """Setup for each test"""
        self.test_start_time = time.time()

    def tearDown(self):
        """Cleanup after each test"""
        test_duration = time.time() - self.test_start_time
        logger.info(f"Network test completed in: {test_duration:.2f}s")

    def test_01_docker_networks_exist(self):
        """Test 1: Verify Docker networks exist and are properly configured"""
        logger.info("Testing Docker network configuration...")

        try:
            # List all Docker networks
            networks = self.client.networks.list()

            network_info = {}
            for network in networks:
                network_info[network.name] = {
                    'id': network.id,
                    'driver': network.attrs['Driver'],
                    'scope': network.attrs['Scope'],
                    'internal': network.attrs['Internal'],
                    'containers': len(network.attrs.get('Containers', {}))
                }

            logger.info(f"Found {len(networks)} Docker networks")

            # Check for tutor-ai specific network
            tutor_ai_networks = [name for name in network_info.keys() if 'tutor-ai' in name]
            default_networks = ['bridge', 'host', 'none']

            logger.info(f"Tutor-AI networks: {tutor_ai_networks}")
            logger.info(f"Default networks present: {network for network in default_networks if network in network_info}")

            self.network_stats['network_configuration'] = {
                'total_networks': len(networks),
                'tutor_ai_networks': tutor_ai_networks,
                'default_networks': [n for n in default_networks if n in network_info],
                'network_details': network_info
            }

            # Basic network validation
            self.assertGreater(len(networks), 0, "No Docker networks found")
            self.assertIn('bridge', network_info, "Default bridge network not found")

        except Exception as e:
            logger.error(f"Docker network configuration test failed: {e}")
            self.fail(f"Network configuration test failed: {e}")

    def test_02_container_network_connectivity(self):
        """Test 2: Verify containers can communicate within Docker networks"""
        logger.info("Testing container network connectivity...")

        connectivity_results = {}

        try:
            # Get running containers
            containers = self.client.containers.list()
            tutor_ai_containers = [c for c in containers if 'tutor-ai' in c.name]

            logger.info(f"Found {len(tutor_ai_containers)} tutor-ai containers")

            for container in tutor_ai_containers:
                container_networks = container.attrs.get('NetworkSettings', {}).get('Networks', {})

                connectivity_results[container.name] = {
                    'networks': list(container_networks.keys()),
                    'ip_addresses': {},
                    'connectivity_status': 'unknown'
                }

                # Get IP addresses for each network
                for network_name, network_config in container_networks.items():
                    ip_address = network_config.get('IPAddress')
                    connectivity_results[container.name]['ip_addresses'][network_name] = ip_address
                    logger.info(f"{container.name} - {network_name}: {ip_address}")

            # Test external connectivity from containers
            self.test_container_external_connectivity(tutor_ai_containers, connectivity_results)

            # Test inter-container communication
            self.test_inter_container_communication(tutor_ai_containers, connectivity_results)

        except Exception as e:
            logger.error(f"Container network connectivity test failed: {e}")
            self.fail(f"Network connectivity test failed: {e}")

        self.network_stats['container_connectivity'] = connectivity_results

    def test_container_external_connectivity(self, containers: List, results: Dict):
        """Test external connectivity from containers"""
        try:
            for container in containers:
                if 'backend' in container.name.lower():
                    # Test external connectivity from backend container
                    try:
                        # Execute network test inside container
                        exit_code, output = container.exec_run(
                            "curl -s --connect-timeout 5 http://httpbin.org/ip",
                            workdir="/app"
                        )

                        if exit_code == 0:
                            results[container.name]['external_connectivity'] = {
                                'status': 'success',
                                'response': output.decode('utf-8').strip()
                            }
                            logger.info(f"{container.name} - External connectivity: SUCCESS")
                        else:
                            results[container.name]['external_connectivity'] = {
                                'status': 'failed',
                                'error': output.decode('utf-8').strip()
                            }
                            logger.warning(f"{container.name} - External connectivity: FAILED")

                    except Exception as e:
                        results[container.name]['external_connectivity'] = {
                            'status': 'error',
                            'error': str(e)
                        }
                        logger.warning(f"{container.name} - External connectivity test error: {e}")

        except Exception as e:
            logger.error(f"External connectivity test failed: {e}")

    def test_inter_container_communication(self, containers: List, results: Dict):
        """Test communication between containers"""
        try:
            backend_container = None
            frontend_container = None

            for container in containers:
                if 'backend' in container.name.lower():
                    backend_container = container
                elif 'frontend' in container.name.lower():
                    frontend_container = container

            if backend_container and frontend_container:
                # Get backend container IP
                backend_networks = backend_container.attrs.get('NetworkSettings', {}).get('Networks', {})
                backend_ip = None

                for network_name, network_config in backend_networks.items():
                    if network_config.get('IPAddress'):
                        backend_ip = network_config['IPAddress']
                        break

                if backend_ip:
                    # Test frontend can reach backend
                    try:
                        exit_code, output = frontend_container.exec_run(
                            f"curl -s --connect-timeout 5 http://{backend_ip}:8000/health",
                            workdir="/app"
                        )

                        results['inter_container_communication'] = {
                            'status': 'success' if exit_code == 0 else 'failed',
                            'backend_ip': backend_ip,
                            'response_code': exit_code,
                            'response': output.decode('utf-8').strip() if exit_code == 0 else output.decode('utf-8').strip()
                        }

                        if exit_code == 0:
                            logger.info(f"Frontend -> Backend communication: SUCCESS (IP: {backend_ip})")
                        else:
                            logger.warning(f"Frontend -> Backend communication: FAILED")

                    except Exception as e:
                        results['inter_container_communication'] = {
                            'status': 'error',
                            'backend_ip': backend_ip,
                            'error': str(e)
                        }
                        logger.warning(f"Inter-container communication test error: {e}")
                else:
                    logger.warning("Could not find backend container IP address")

        except Exception as e:
            logger.error(f"Inter-container communication test failed: {e}")

    def test_03_port_mapping_and_accessibility(self):
        """Test 3: Verify port mapping and external accessibility"""
        logger.info("Testing port mapping and accessibility...")

        port_tests = {}

        try:
            # Expected port mappings
            expected_ports = [
                ('Backend API', 'http://localhost:8000', 8000),
                ('Frontend', 'http://localhost:3001', 3001),
            ]

            for service_name, url, port in expected_ports:
                try:
                    logger.info(f"Testing {service_name} at {url}")

                    # Test HTTP connectivity
                    response = requests.get(url, timeout=10)

                    port_tests[service_name] = {
                        'status': 'accessible',
                        'url': url,
                        'port': port,
                        'status_code': response.status_code,
                        'response_time': response.elapsed.total_seconds(),
                        'content_length': len(response.content)
                    }

                    logger.info(f"{service_name} - Status: {response.status_code}, "
                              f"Time: {response.elapsed.total_seconds():.3f}s")

                    # Basic response validation
                    self.assertEqual(response.status_code, 200,
                                   f"{service_name} returned {response.status_code}")
                    self.assertLess(response.elapsed.total_seconds(), 5.0,
                                   f"{service_name} response time too slow")

                except requests.exceptions.ConnectionError:
                    port_tests[service_name] = {
                        'status': 'connection_refused',
                        'url': url,
                        'port': port,
                        'error': 'Connection refused'
                    }
                    logger.error(f"{service_name} - Connection refused on port {port}")
                    self.fail(f"{service_name} not accessible on port {port}")

                except requests.exceptions.Timeout:
                    port_tests[service_name] = {
                        'status': 'timeout',
                        'url': url,
                        'port': port,
                        'error': 'Request timeout'
                    }
                    logger.error(f"{service_name} - Timeout on port {port}")
                    self.fail(f"{service_name} timeout on port {port}")

                except Exception as e:
                    port_tests[service_name] = {
                        'status': 'error',
                        'url': url,
                        'port': port,
                        'error': str(e)
                    }
                    logger.error(f"{service_name} - Error: {e}")
                    self.fail(f"{service_name} error: {e}")

            # Test port availability
            self.test_port_availability()

        except Exception as e:
            logger.error(f"Port mapping test failed: {e}")
            self.fail(f"Port mapping test failed: {e}")

        self.network_stats['port_mapping'] = port_tests

    def test_port_availability(self):
        """Test if ports are properly bound and available"""
        try:
            # Check which ports are listening
            listening_ports = []

            # Get network connections
            for conn in psutil.net_connections():
                if conn.status == 'LISTEN' and conn.laddr:
                    listening_ports.append(conn.laddr.port)

            logger.info(f"Listening ports: {sorted(set(listening_ports))}")

            # Check for expected ports
            expected_ports = [8000, 3001]  # backend, frontend
            missing_ports = [port for port in expected_ports if port not in listening_ports]

            if missing_ports:
                logger.warning(f"Expected ports not listening: {missing_ports}")

            self.network_stats['port_availability'] = {
                'listening_ports': sorted(set(listening_ports)),
                'expected_ports': expected_ports,
                'missing_ports': missing_ports
            }

        except Exception as e:
            logger.error(f"Port availability test failed: {e}")
            self.network_stats['port_availability'] = {'error': str(e)}

    def test_04_dns_resolution_in_containers(self):
        """Test 4: Verify DNS resolution works inside containers"""
        logger.info("Testing DNS resolution in containers...")

        dns_results = {}

        try:
            containers = self.client.containers.list()
            tutor_ai_containers = [c for c in containers if 'tutor-ai' in c.name]

            for container in tutor_ai_containers:
                if 'backend' in container.name.lower():
                    try:
                        # Test DNS resolution for common domains
                        test_domains = [
                            'google.com',
                            'localhost',
                            'host.docker.internal'
                        ]

                        domain_results = {}

                        for domain in test_domains:
                            try:
                                # Test DNS resolution using nslookup
                                exit_code, output = container.exec_run(
                                    f"nslookup {domain}",
                                    workdir="/app"
                                )

                                domain_results[domain] = {
                                    'status': 'success' if exit_code == 0 else 'failed',
                                    'exit_code': exit_code,
                                    'output': output.decode('utf-8').strip()
                                }

                                if exit_code == 0:
                                    logger.info(f"{container.name} - DNS resolution for {domain}: SUCCESS")
                                else:
                                    logger.warning(f"{container.name} - DNS resolution for {domain}: FAILED")

                            except Exception as e:
                                domain_results[domain] = {
                                    'status': 'error',
                                    'error': str(e)
                                }
                                logger.warning(f"{container.name} - DNS test error for {domain}: {e}")

                        dns_results[container.name] = {
                            'domains_tested': list(test_domains),
                            'domain_results': domain_results,
                            'overall_status': 'success' if all(
                                r.get('status') == 'success' for r in domain_results.values()
                            ) else 'partial_failure'
                        }

                    except Exception as e:
                        dns_results[container.name] = {
                            'status': 'error',
                            'error': str(e)
                        }
                        logger.error(f"DNS resolution test failed for {container.name}: {e}")

        except Exception as e:
            logger.error(f"DNS resolution test failed: {e}")
            dns_results['test_error'] = {'error': str(e)}

        self.network_stats['dns_resolution'] = dns_results

    def test_05_network_performance(self):
        """Test 5: Measure network performance between containers"""
        logger.info("Testing network performance...")

        performance_results = {}

        try:
            # Test API response times from different angles
            api_endpoints = [
                ('Health Check', 'http://localhost:8000/health'),
                ('Courses API', 'http://localhost:8000/courses'),
                ('Frontend Root', 'http://localhost:3001'),
            ]

            performance_stats = {}

            for endpoint_name, url in api_endpoints:
                try:
                    # Make multiple requests and measure performance
                    response_times = []
                    status_codes = []

                    for _ in range(10):  # 10 requests for statistical significance
                        response = requests.get(url, timeout=10)
                        response_times.append(response.elapsed.total_seconds() * 1000)  # ms
                        status_codes.append(response.status_code)

                        time.sleep(0.1)  # Small delay between requests

                    # Calculate statistics
                    avg_time = sum(response_times) / len(response_times)
                    min_time = min(response_times)
                    max_time = max(response_times)
                    p95_time = sorted(response_times)[int(len(response_times) * 0.95)]

                    performance_stats[endpoint_name] = {
                        'url': url,
                        'requests_count': len(response_times),
                        'avg_response_time_ms': avg_time,
                        'min_response_time_ms': min_time,
                        'max_response_time_ms': max_time,
                        'p95_response_time_ms': p95_time,
                        'success_rate': sum(1 for code in status_codes if code == 200) / len(status_codes),
                        'status_codes': dict(zip(status_codes, [status_codes.count(code) for code in set(status_codes)]))
                    }

                    logger.info(f"{endpoint_name} - Avg: {avg_time:.1f}ms, "
                              f"P95: {p95_time:.1f}ms, Success: {performance_stats[endpoint_name]['success_rate']*100:.1f}%")

                    # Performance assertions
                    self.assertLess(avg_time, 1000, f"{endpoint_name} average response time too high: {avg_time:.1f}ms")
                    self.assertLess(p95_time, 2000, f"{endpoint_name} P95 response time too high: {p95_time:.1f}ms")
                    self.assertGreater(performance_stats[endpoint_name]['success_rate'], 0.9,
                                     f"{endpoint_name} success rate too low: {performance_stats[endpoint_name]['success_rate']*100:.1f}%")

                except Exception as e:
                    logger.error(f"Performance test failed for {endpoint_name}: {e}")
                    performance_stats[endpoint_name] = {'error': str(e)}
                    self.fail(f"Performance test failed for {endpoint_name}: {e}")

            # Test concurrent requests
            concurrent_results = self.test_concurrent_requests()

            performance_results['endpoint_performance'] = performance_stats
            performance_results['concurrent_requests'] = concurrent_results

        except Exception as e:
            logger.error(f"Network performance test failed: {e}")
            performance_results['test_error'] = {'error': str(e)}

        self.network_stats['network_performance'] = performance_results

    def test_concurrent_requests(self) -> Dict:
        """Test concurrent request handling"""
        try:
            logger.info("Testing concurrent request handling...")

            def make_request(url: str) -> Dict:
                try:
                    start_time = time.time()
                    response = requests.get(url, timeout=15)
                    end_time = time.time()

                    return {
                        'status_code': response.status_code,
                        'response_time': end_time - start_time,
                        'success': response.status_code == 200
                    }
                except Exception as e:
                    return {
                        'status_code': 0,
                        'response_time': 0,
                        'success': False,
                        'error': str(e)
                    }

            # Test with 20 concurrent requests
            urls = [
                'http://localhost:8000/health',
                'http://localhost:8000/courses',
                'http://localhost:3001'
            ]

            concurrent_results = {}

            for url in urls:
                with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
                    # Submit 20 concurrent requests
                    futures = [executor.submit(make_request, url) for _ in range(20)]

                    # Collect results
                    results = [future.result() for future in concurrent.futures.as_completed(futures)]

                    # Analyze results
                    successful_requests = [r for r in results if r['success']]
                    response_times = [r['response_time'] for r in successful_requests]

                    concurrent_results[url] = {
                        'total_requests': len(results),
                        'successful_requests': len(successful_requests),
                        'success_rate': len(successful_requests) / len(results),
                        'avg_response_time': sum(response_times) / len(response_times) if response_times else 0,
                        'max_response_time': max(response_times) if response_times else 0,
                        'min_response_time': min(response_times) if response_times else 0
                    }

                    logger.info(f"Concurrent requests to {url}: "
                              f"{len(successful_requests)}/{len(results)} successful, "
                              f"avg time: {concurrent_results[url]['avg_response_time']:.3f}s")

            return concurrent_results

        except Exception as e:
            logger.error(f"Concurrent requests test failed: {e}")
            return {'error': str(e)}

    def test_06_network_isolation_and_security(self):
        """Test 6: Verify network isolation and security measures"""
        logger.info("Testing network isolation and security...")

        security_results = {}

        try:
            containers = self.client.containers.list()
            tutor_ai_containers = [c for c in containers if 'tutor-ai' in c.name]

            for container in tutor_ai_containers:
                try:
                    container_info = container.attrs

                    # Check network settings
                    network_settings = container_info.get('NetworkSettings', {})
                    networks = network_settings.get('Networks', {})

                    # Check port bindings
                    port_bindings = network_settings.get('Ports', {})

                    security_results[container.name] = {
                        'networks': list(networks.keys()),
                        'port_bindings': port_bindings,
                        'privileged': container_info.get('HostConfig', {}).get('Privileged', False),
                        'host_networking': network_settings.get('NetworkMode') == 'host',
                        'published_ports': len([p for p in port_bindings.keys() if p]),
                    }

                    # Security checks
                    is_privileged = container_info.get('HostConfig', {}).get('Privileged', False)
                    host_networking = network_settings.get('NetworkMode') == 'host'

                    if is_privileged:
                        logger.warning(f"{container.name} is running in privileged mode")

                    if host_networking:
                        logger.warning(f"{container.name} is using host networking")

                    # Check for excessive port exposure
                    exposed_ports = len([p for p in port_bindings.keys() if p])
                    if exposed_ports > 5:
                        logger.warning(f"{container.name} has many exposed ports: {exposed_ports}")

                    logger.info(f"{container.name} - Networks: {list(networks.keys())}, "
                              f"Privileged: {is_privileged}, Host networking: {host_networking}")

                except Exception as e:
                    security_results[container.name] = {'error': str(e)}
                    logger.error(f"Security test failed for {container.name}: {e}")

        except Exception as e:
            logger.error(f"Network isolation and security test failed: {e}")
            security_results['test_error'] = {'error': str(e)}

        self.network_stats['network_security'] = security_results

    @classmethod
    def generate_network_report(cls):
        """Generate comprehensive network test report"""
        report = {
            'test_suite': 'Docker Networking Tests',
            'timestamp': datetime.now().isoformat(),
            'test_duration': str(datetime.now() - cls.test_start_time),
            'network_stats': cls.network_stats,
        }

        # Save report to file
        report_file = f"tests/reports/network_test_report_{int(time.time())}.json"
        import os
        os.makedirs(os.path.dirname(report_file), exist_ok=True)

        try:
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)

            logger.info(f"Network test report saved to: {report_file}")

            # Print summary
            print(f"\n{'='*60}")
            print("DOCKER NETWORKING TEST SUMMARY")
            print(f"{'='*60}")
            print(f"Test Duration: {report['test_duration']}")
            print(f"Report File: {report_file}")

            # Network summary
            if 'network_configuration' in cls.network_stats:
                network_config = cls.network_stats['network_configuration']
                print(f"Total Networks: {network_config.get('total_networks', 0)}")
                print(f"Tutor-AI Networks: {network_config.get('tutor_ai_networks', [])}")

            # Connectivity summary
            if 'container_connectivity' in cls.network_stats:
                connectivity = cls.network_stats['container_connectivity']
                print(f"Container Connectivity: {len(connectivity)} containers tested")

            # Performance summary
            if 'network_performance' in cls.network_stats:
                perf = cls.network_stats['network_performance']
                if 'endpoint_performance' in perf:
                    endpoints = perf['endpoint_performance']
                    print(f"Performance Tests: {len(endpoints)} endpoints tested")

            print(f"{'='*60}")

        except Exception as e:
            logger.error(f"Failed to generate network test report: {e}")


def run_networking_tests():
    """Run the Docker networking test suite"""
    print("🌐 Starting Docker Networking Tests...")

    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(DockerNetworkingTest)

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2, buffer=True)
    result = runner.run(suite)

    # Return results
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_networking_tests()
    import sys
    sys.exit(0 if success else 1)