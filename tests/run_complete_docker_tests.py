#!/usr/bin/env python3
"""
Complete Docker Test Runner for Tutor-AI

Comprehensive test runner that executes all Docker-related tests,
generates reports, and provides detailed analysis of results.

Usage:
    python tests/run_complete_docker_tests.py [options]

Options:
    --quick       Run only quick tests (skip performance tests)
    --verbose     Verbose output
    --report-only Generate reports without running tests
    --category    Run specific category of tests (health, networking, persistence, performance, security, api, ai)
    --parallel    Run tests in parallel (experimental)
"""

import argparse
import subprocess
import sys
import os
import json
import time
import threading
import concurrent.futures
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DockerTestRunner:
    """Comprehensive Docker test runner"""

    def __init__(self, verbose: bool = False, quick_mode: bool = False):
        self.verbose = verbose
        self.quick_mode = quick_mode
        self.test_start_time = datetime.now()
        self.test_results = {}
        self.test_categories = {
            'health': {
                'name': 'Container Health Tests',
                'script': 'tests/docker/container_health_test.py',
                'description': 'Container health, restart policies, resource limits',
                'priority': 1
            },
            'networking': {
                'name': 'Networking Tests',
                'script': 'tests/docker/networking_test.py',
                'description': 'Container communication, DNS, port mapping',
                'priority': 2
            },
            'persistence': {
                'name': 'Volume Persistence Tests',
                'script': 'tests/docker/volume_persistence_test.py',
                'description': 'Data persistence, volume integrity, backup/recovery',
                'priority': 3
            },
            'performance': {
                'name': 'Performance Tests',
                'script': 'tests/docker/performance_test.py',
                'description': 'Resource usage, response times, scalability',
                'priority': 4,
                'skip_in_quick': True
            },
            'security': {
                'name': 'Security Tests',
                'script': 'tests/docker/security_test.py',
                'description': 'Container isolation, security policies, vulnerabilities',
                'priority': 5
            },
            'api_integration': {
                'name': 'API Integration Tests',
                'script': 'tests/docker/api_integration_test.py',
                'description': 'End-to-end API functionality through Docker',
                'priority': 6
            },
            'ai_services': {
                'name': 'AI Services Tests',
                'script': 'tests/docker/ai_services_test.py',
                'description': 'LLM providers, RAG system, AI integration',
                'priority': 7
            }
        }

    def run_all_tests(self, category: Optional[str] = None, parallel: bool = False) -> Dict:
        """Run all Docker tests"""
        print(f"🚀 Starting Complete Docker Test Suite")
        print(f"⏰ Started at: {self.test_start_time}")
        print(f"🐳 Docker Tests Categories: {len(self.test_categories)}")

        if self.quick_mode:
            print("⚡ Quick mode enabled - skipping performance-intensive tests")

        if category:
            if category not in self.test_categories:
                logger.error(f"Unknown test category: {category}")
                return {'error': f'Unknown category: {category}'}
            categories_to_run = {category: self.test_categories[category]}
            print(f"🎯 Running single category: {category}")
        else:
            categories_to_run = self.test_categories

        # Filter out tests skipped in quick mode
        if self.quick_mode:
            categories_to_run = {
                name: config for name, config in categories_to_run.items()
                if not config.get('skip_in_quick', False)
            }

        print(f"📋 Test categories to run: {list(categories_to_run.keys())}")

        # Run tests
        if parallel:
            results = self.run_tests_parallel(categories_to_run)
        else:
            results = self.run_tests_sequential(categories_to_run)

        # Generate comprehensive report
        self.generate_comprehensive_report(results)

        return results

    def run_tests_sequential(self, categories: Dict) -> Dict:
        """Run tests sequentially"""
        results = {}

        # Sort categories by priority
        sorted_categories = sorted(
            categories.items(),
            key=lambda x: x[1]['priority']
        )

        for category_name, category_config in sorted_categories:
            print(f"\n{'='*60}")
            print(f"🧪 Running {category_config['name']}")
            print(f"📝 {category_config['description']}")
            print(f"{'='*60}")

            try:
                start_time = time.time()
                result = self.run_single_test(category_name, category_config)
                duration = time.time() - start_time

                results[category_name] = {
                    'config': category_config,
                    'result': result,
                    'duration_seconds': duration,
                    'duration_formatted': f"{duration:.2f}s",
                    'timestamp': datetime.now().isoformat()
                }

                # Print result summary
                self.print_category_result(category_name, result, duration)

            except Exception as e:
                logger.error(f"Failed to run {category_name} tests: {e}")
                results[category_name] = {
                    'config': category_config,
                    'error': str(e),
                    'duration_seconds': 0,
                    'timestamp': datetime.now().isoformat()
                }

        return results

    def run_tests_parallel(self, categories: Dict) -> Dict:
        """Run tests in parallel (experimental)"""
        print("⚡ Running tests in parallel mode")

        results = {}

        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            # Submit all test categories
            future_to_category = {
                executor.submit(self.run_single_test, name, config): (name, config)
                for name, config in categories.items()
            }

            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_category):
                category_name, category_config = future_to_category[future]

                try:
                    result = future.result()
                    results[category_name] = {
                        'config': category_config,
                        'result': result,
                        'timestamp': datetime.now().isoformat(),
                        'parallel_execution': True
                    }

                    print(f"✅ Completed {category_config['name']} in parallel")

                except Exception as e:
                    logger.error(f"Parallel test failed for {category_name}: {e}")
                    results[category_name] = {
                        'config': category_config,
                        'error': str(e),
                        'timestamp': datetime.now().isoformat(),
                        'parallel_execution': True
                    }

        return results

    def run_single_test(self, category_name: str, category_config: Dict) -> Dict:
        """Run a single test category"""
        script_path = category_config['script']

        if not os.path.exists(script_path):
            return {
                'success': False,
                'error': f'Test script not found: {script_path}',
                'exit_code': -1
            }

        try:
            # Change to project directory
            original_cwd = os.getcwd()
            os.chdir('/mnt/c/Users/pietr/Documents/progetto/tutor-ai')

            # Run the test script
            cmd = [sys.executable, script_path]
            env = os.environ.copy()
            env['PYTHONPATH'] = '/mnt/c/Users/pietr/Documents/progetto/tutor-ai'

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env
            )

            stdout, stderr = process.communicate()
            exit_code = process.returncode

            # Restore original directory
            os.chdir(original_cwd)

            success = exit_code == 0

            result = {
                'success': success,
                'exit_code': exit_code,
                'stdout': stdout if self.verbose else stdout[-1000:] if stdout else '',
                'stderr': stderr if self.verbose else stderr[-1000:] if stderr else '',
                'script_path': script_path,
                'execution_time': datetime.now().isoformat()
            }

            if success:
                logger.info(f"✅ {category_config['name']} completed successfully")
            else:
                logger.error(f"❌ {category_config['name']} failed with exit code {exit_code}")

                # Print error summary if not verbose
                if not self.verbose and stderr:
                    print(f"❌ Error output (last 500 chars):")
                    print(stderr[-500:])

            return result

        except Exception as e:
            logger.error(f"Exception running {category_name} tests: {e}")
            return {
                'success': False,
                'error': str(e),
                'exit_code': -1,
                'script_path': script_path
            }

    def print_category_result(self, category_name: str, result: Dict, duration: float):
        """Print result summary for a test category"""
        success = result.get('success', False)

        if success:
            print(f"✅ {category_name.upper()} - PASSED ({duration:.2f}s)")
        else:
            print(f"❌ {category_name.upper()} - FAILED ({duration:.2f}s)")
            error = result.get('error')
            if error:
                print(f"   Error: {error}")

    def generate_comprehensive_report(self, results: Dict):
        """Generate comprehensive test report"""
        print(f"\n{'='*80}")
        print("📊 COMPREHENSIVE DOCKER TEST REPORT")
        print(f"{'='*80}")

        total_duration = datetime.now() - self.test_start_time
        print(f"⏰ Total Test Duration: {total_duration}")
        print(f"📅 Report Generated: {datetime.now().isoformat()}")

        # Calculate statistics
        total_categories = len(results)
        successful_categories = sum(1 for r in results.values() if r.get('result', {}).get('success', False))
        failed_categories = total_categories - successful_categories

        print(f"\n📈 OVERALL STATISTICS:")
        print(f"   Total Test Categories: {total_categories}")
        print(f"   ✅ Successful: {successful_categories}")
        print(f"   ❌ Failed: {failed_categories}")
        print(f"   📊 Success Rate: {(successful_categories/total_categories*100):.1f}%")

        # Per-category details
        print(f"\n📋 CATEGORY DETAILS:")
        for category_name, category_result in results.items():
            config = category_result.get('config', {})
            result = category_result.get('result', {})
            duration = category_result.get('duration_seconds', 0)

            status_icon = "✅" if result.get('success', False) else "❌"
            status_text = "PASSED" if result.get('success', False) else "FAILED"

            print(f"   {status_icon} {config.get('name', category_name)} - {status_text} ({duration:.2f}s)")

            if not result.get('success', False) and 'error' in result:
                print(f"      Error: {result['error'][:100]}...")

        # Save detailed report
        report_data = {
            'test_suite': 'Complete Docker Test Suite',
            'timestamp': datetime.now().isoformat(),
            'test_duration': str(total_duration),
            'configuration': {
                'verbose': self.verbose,
                'quick_mode': self.quick_mode,
                'categories_tested': list(results.keys())
            },
            'results': results,
            'statistics': {
                'total_categories': total_categories,
                'successful_categories': successful_categories,
                'failed_categories': failed_categories,
                'success_rate': successful_categories/total_categories*100 if total_categories > 0 else 0
            }
        }

        # Save to file
        report_file = f"tests/reports/complete_docker_test_report_{int(time.time())}.json"
        os.makedirs(os.path.dirname(report_file), exist_ok=True)

        try:
            with open(report_file, 'w') as f:
                json.dump(report_data, f, indent=2, default=str)

            print(f"\n📄 Detailed report saved to: {report_file}")

        except Exception as e:
            logger.error(f"Failed to save detailed report: {e}")

        # Generate HTML report
        html_report_file = self.generate_html_report(report_data)
        if html_report_file:
            print(f"🌐 HTML report generated: {html_report_file}")

        print(f"\n{'='*80}")

        # Return success based on overall results
        return successful_categories == total_categories

    def generate_html_report(self, report_data: Dict) -> Optional[str]:
        """Generate HTML report"""
        try:
            html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Tutor-AI Docker Test Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #333; border-bottom: 3px solid #007bff; padding-bottom: 10px; }
        h2 { color: #495057; margin-top: 30px; }
        .stats { display: flex; gap: 20px; margin: 20px 0; }
        .stat-card { flex: 1; padding: 20px; border-radius: 8px; text-align: center; color: white; }
        .stat-card.success { background: #28a745; }
        .stat-card.danger { background: #dc3545; }
        .stat-card.info { background: #17a2b8; }
        .category-result { margin: 10px 0; padding: 15px; border-radius: 5px; border-left: 4px solid #ddd; }
        .category-result.success { border-left-color: #28a745; background: #f8fff9; }
        .category-result.failed { border-left-color: #dc3545; background: #fff8f8; }
        .status { font-weight: bold; }
        .details { margin-top: 10px; font-size: 0.9em; color: #666; }
        .error { color: #dc3545; font-family: monospace; background: #f8f8f8; padding: 10px; border-radius: 4px; margin-top: 10px; }
        .timestamp { color: #6c757d; font-size: 0.9em; }
        .footer { margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; color: #6c757d; text-align: center; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🐳 Tutor-AI Docker Test Report</h1>
        <p class="timestamp">Generated: {timestamp}</p>
        <p><strong>Test Duration:</strong> {test_duration}</p>

        <div class="stats">
            <div class="stat-card info">
                <h3>{total_categories}</h3>
                <p>Total Categories</p>
            </div>
            <div class="stat-card success">
                <h3>{successful_categories}</h3>
                <p>Successful</p>
            </div>
            <div class="stat-card danger">
                <h3>{failed_categories}</h3>
                <p>Failed</p>
            </div>
            <div class="stat-card info">
                <h3>{success_rate:.1f}%</h3>
                <p>Success Rate</p>
            </div>
        </div>

        <h2>📋 Test Category Results</h2>
        {category_results}

        <div class="footer">
            <p>Report generated by Tutor-AI Docker Test Runner</p>
            <p>For more details, check the JSON report file</p>
        </div>
    </div>
</body>
</html>
            """

            # Generate category results HTML
            category_results_html = ""
            for category_name, category_result in report_data['results'].items():
                config = category_result.get('config', {})
                result = category_result.get('result', {})
                duration = category_result.get('duration_seconds', 0)

                success_class = "success" if result.get('success', False) else "failed"
                status_icon = "✅" if result.get('success', False) else "❌"
                status_text = "PASSED" if result.get('success', False) else "FAILED"

                category_results_html += f"""
                <div class="category-result {success_class}">
                    <h4>{status_icon} {config.get('name', category_name)}</h4>
                    <p><strong>Status:</strong> <span class="status">{status_text}</span></p>
                    <p><strong>Duration:</strong> {duration:.2f}s</p>
                    <p><strong>Description:</strong> {config.get('description', 'No description')}</p>
                    <div class="details">
                        <p><strong>Script:</strong> {config.get('script', 'Unknown')}</p>
                        <p><strong>Priority:</strong> {config.get('priority', 'Unknown')}</p>
                        <p><strong>Executed:</strong> {category_result.get('timestamp', 'Unknown')}</p>
                    </div>
                    {f'<div class="error"><strong>Error:</strong> {result.get("error", "Unknown error")}</div>' if not result.get('success', False) else ''}
                </div>
                """

            # Format the HTML
            html_content = html_template.format(
                timestamp=report_data['timestamp'],
                test_duration=report_data['test_duration'],
                total_categories=report_data['statistics']['total_categories'],
                successful_categories=report_data['statistics']['successful_categories'],
                failed_categories=report_data['statistics']['failed_categories'],
                success_rate=report_data['statistics']['success_rate'],
                category_results=category_results_html
            )

            # Save HTML report
            html_file = f"tests/reports/complete_docker_test_report_{int(time.time())}.html"
            with open(html_file, 'w') as f:
                f.write(html_content)

            return html_file

        except Exception as e:
            logger.error(f"Failed to generate HTML report: {e}")
            return None

    def check_docker_environment(self) -> bool:
        """Check if Docker environment is ready"""
        try:
            # Check if Docker is running
            result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
            if result.returncode != 0:
                print("❌ Docker is not installed or not accessible")
                return False

            # Check if Docker daemon is running
            result = subprocess.run(['docker', 'info'], capture_output=True, text=True)
            if result.returncode != 0:
                print("❌ Docker daemon is not running")
                return False

            print("✅ Docker environment is ready")
            return True

        except Exception as e:
            print(f"❌ Error checking Docker environment: {e}")
            return False


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Complete Docker Test Runner for Tutor-AI')
    parser.add_argument('--quick', action='store_true', help='Run only quick tests (skip performance tests)')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    parser.add_argument('--category', choices=['health', 'networking', 'persistence', 'performance', 'security', 'api_integration', 'ai_services'], help='Run specific test category')
    parser.add_argument('--parallel', action='store_true', help='Run tests in parallel (experimental)')
    parser.add_argument('--report-only', action='store_true', help='Generate reports without running tests')
    parser.add_argument('--check-env', action='store_true', help='Only check Docker environment')

    args = parser.parse_args()

    # Create test runner
    runner = DockerTestRunner(verbose=args.verbose, quick_mode=args.quick)

    # Check Docker environment
    if args.check_env:
        success = runner.check_docker_environment()
        sys.exit(0 if success else 1)

    # Only generate reports
    if args.report_only:
        print("📊 Report-only mode - generating reports without running tests")
        # You could implement report generation from existing results here
        return

    # Check environment first
    if not runner.check_docker_environment():
        print("\n💡 Make sure Docker is installed and running:")
        print("   - Install Docker Desktop or Docker Engine")
        print("   - Start Docker service")
        print("   - Ensure your user has Docker permissions")
        sys.exit(1)

    # Change to project directory
    if not os.path.exists('/mnt/c/Users/pietr/Documents/progetto/tutor-ai'):
        print("❌ Tutor-AI project directory not found")
        sys.exit(1)

    os.chdir('/mnt/c/Users/pietr/Documents/progetto/tutor-ai')

    try:
        # Run tests
        results = runner.run_all_tests(category=args.category, parallel=args.parallel)

        # Determine overall success
        successful_tests = sum(1 for r in results.values() if r.get('result', {}).get('success', False))
        total_tests = len(results)
        all_successful = successful_tests == total_tests

        if all_successful:
            print(f"\n🎉 ALL TESTS PASSED! ({successful_tests}/{total_tests})")
            print("✅ Docker environment is healthy and ready for production")
        else:
            print(f"\n⚠️  SOME TESTS FAILED! ({successful_tests}/{total_tests})")
            print("❌ Please review the failed tests and fix issues before deployment")

        sys.exit(0 if all_successful else 1)

    except KeyboardInterrupt:
        print("\n⏹️ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()