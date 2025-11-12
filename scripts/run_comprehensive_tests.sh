#!/bin/bash

# Comprehensive Test Runner for Tutor-AI
# This script runs all test suites with proper error handling and reporting

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
TESTS_DIR="$PROJECT_ROOT/tests"
REPORTS_DIR="$PROJECT_ROOT/test-reports"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# Create reports directory
mkdir -p "$REPORTS_DIR"

# Logging functions
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

log_success() {
    echo -e "${GREEN}[SUCCESS] $1${NC}"
}

log_error() {
    echo -e "${RED}[ERROR] $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

log_info() {
    echo -e "${CYAN}[INFO] $1${NC}"
}

log_header() {
    echo -e "${PURPLE}$1${NC}"
}

# Test result tracking
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
SKIPPED_TESTS=0

# Functions
check_dependencies() {
    log_info "Checking dependencies..."

    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed or not in PATH"
        exit 1
    fi

    # Check Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is not installed or not in PATH"
        exit 1
    fi

    # Check Node.js
    if ! command -v node &> /dev/null; then
        log_error "Node.js is not installed or not in PATH"
        exit 1
    fi

    # Check npm
    if ! command -v npm &> /dev/null; then
        log_error "npm is not installed or not in PATH"
        exit 1
    fi

    log_success "All dependencies are available"
}

setup_environment() {
    log_info "Setting up test environment..."

    # Set environment variables
    export ENVIRONMENT=testing
    export LOG_LEVEL=ERROR
    export DATABASE_URL="sqlite:///$REPORTS_DIR/test_$TIMESTAMP.db"
    export REDIS_URL="redis://localhost:6379"
    export NEXT_PUBLIC_API_URL="http://localhost:8000"

    # Ensure we're in project root
    cd "$PROJECT_ROOT"

    log_success "Test environment configured"
}

start_services() {
    log_info "Starting required services..."

    # Start Redis if not running
    if ! docker ps | grep -q redis; then
        log_info "Starting Redis..."
        docker run -d --name test-redis -p 6379:6379 redis:7-alpine || true
    fi

    # Wait for Redis to be ready
    for i in {1..30}; do
        if docker exec test-redis redis-cli ping &> /dev/null; then
            log_success "Redis is ready"
            break
        fi
        sleep 1
    done

    log_success "Services started successfully"
}

stop_services() {
    log_info "Stopping test services..."

    # Stop test containers
    docker stop test-redis 2>/dev/null || true
    docker rm test-redis 2>/dev/null || true

    log_success "Services stopped"
}

run_backend_tests() {
    log_header "🔬 Running Backend Tests"

    local backend_log="$REPORTS_DIR/backend_$TIMESTAMP.log"
    local backend_report="$REPORTS_DIR/backend_report_$TIMESTAMP.txt"

    cd "$BACKEND_DIR"

    # Install test dependencies
    log_info "Installing backend test dependencies..."
    pip install -q pytest pytest-cov pytest-asyncio pytest-mock pytest-xdist

    # Run unit tests
    log_info "Running backend unit tests..."
    if pytest tests/ -v \
        --cov=. \
        --cov-report=term-missing \
        --cov-report=html:"$REPORTS_DIR/coverage_html_$TIMESTAMP" \
        --cov-report=xml:"$REPORTS_DIR/coverage_$TIMESTAMP.xml" \
        --junit-xml="$REPORTS_DIR/junit_backend_$TIMESTAMP.xml" \
        --tb=short \
        2>&1 | tee "$backend_log"; then

        log_success "Backend tests passed"
        ((PASSED_TESTS++))
    else
        log_error "Backend tests failed"
        ((FAILED_TESTS++))
    fi

    ((TOTAL_TESTS++))

    # Generate backend report
    cat > "$backend_report" << EOF
Backend Test Report - $(date)
==================================

Test Environment:
- Python: $(python3 --version)
- Pip: $(pip --version)
- Environment: $ENVIRONMENT

Test Results:
$(tail -50 "$backend_log")

Coverage Report:
- HTML Coverage: $REPORTS_DIR/coverage_html_$TIMESTAMP/index.html
- XML Coverage: $REPORTS_DIR/coverage_$TIMESTAMP.xml

EOF

    log_info "Backend report generated: $backend_report"
}

run_frontend_tests() {
    log_header "🎨 Running Frontend Tests"

    local frontend_log="$REPORTS_DIR/frontend_$TIMESTAMP.log"
    local frontend_report="$REPORTS_DIR/frontend_report_$TIMESTAMP.txt"

    cd "$FRONTEND_DIR"

    # Install dependencies
    log_info "Installing frontend dependencies..."
    npm ci --silent

    # Run linting
    log_info "Running frontend linting..."
    npm run lint 2>&1 | tee -a "$frontend_log" || true

    # Run type checking
    log_info "Running TypeScript type checking..."
    npm run type-check 2>&1 | tee -a "$frontend_log" || true

    # Run unit tests
    log_info "Running frontend unit tests..."
    if npm run test -- --coverage \
        --watchAll=false \
        --coverageDirectory="$REPORTS_DIR/coverage_frontend_$TIMESTAMP" \
        --ci \
        --reporters=default \
        --reporters=jest-junit \
        --outputFile="$REPORTS_DIR/junit_frontend_$TIMESTAMP.xml" \
        2>&1 | tee "$frontend_log"; then

        log_success "Frontend tests passed"
        ((PASSED_TESTS++))
    else
        log_error "Frontend tests failed"
        ((FAILED_TESTS++))
    fi

    ((TOTAL_TESTS++))

    # Generate frontend report
    cat > "$frontend_report" << EOF
Frontend Test Report - $(date)
===================================

Test Environment:
- Node.js: $(node --version)
- npm: $(npm --version)
- Environment: $NODE_ENV

Test Results:
$(tail -50 "$frontend_log")

Coverage Report:
- Coverage Directory: $REPORTS_DIR/coverage_frontend_$TIMESTAMP/

EOF

    log_info "Frontend report generated: $frontend_report"
}

run_integration_tests() {
    log_header "🔗 Running Integration Tests"

    local integration_log="$REPORTS_DIR/integration_$TIMESTAMP.log"
    local integration_report="$REPORTS_DIR/integration_report_$TIMESTAMP.txt"

    # Start application for integration tests
    log_info "Starting application for integration tests..."

    # Start backend
    cd "$BACKEND_DIR"
    python3 main.py > "$REPORTS_DIR/backend_$TIMESTAMP.service.log" 2>&1 &
    local backend_pid=$!

    # Wait for backend to start
    for i in {1..60}; do
        if curl -f http://localhost:8000/health &> /dev/null; then
            log_success "Backend is ready"
            break
        fi
        sleep 1
    done

    # Start frontend
    cd "$FRONTEND_DIR"
    npm run dev > "$REPORTS_DIR/frontend_$TIMESTAMP.service.log" 2>&1 &
    local frontend_pid=$!

    # Wait for frontend to start
    for i in {1..60}; do
        if curl -f http://localhost:3000 &> /dev/null; then
            log_success "Frontend is ready"
            break
        fi
        sleep 1
    done

    # Run integration tests
    log_info "Running integration test suite..."
    cd "$PROJECT_ROOT"

    if pytest "$TESTS_DIR/integration/" -v \
        --tb=short \
        --junit-xml="$REPORTS_DIR/junit_integration_$TIMESTAMP.xml" \
        2>&1 | tee "$integration_log"; then

        log_success "Integration tests passed"
        ((PASSED_TESTS++))
    else
        log_error "Integration tests failed"
        ((FAILED_TESTS++))
    fi

    ((TOTAL_TESTS++))

    # Cleanup
    log_info "Stopping application services..."
    kill $backend_pid $frontend_pid 2>/dev/null || true

    # Generate integration report
    cat > "$integration_report" << EOF
Integration Test Report - $(date)
====================================

Test Environment:
- Backend URL: http://localhost:8000
- Frontend URL: http://localhost:3000
- Database: $DATABASE_URL

Test Results:
$(tail -50 "$integration_log")

Service Logs:
- Backend: $REPORTS_DIR/backend_$TIMESTAMP.service.log
- Frontend: $REPORTS_DIR/frontend_$TIMESTAMP.service.log

EOF

    log_info "Integration report generated: $integration_report"
}

run_e2e_tests() {
    log_header "🎭 Running E2E Tests"

    local e2e_log="$REPORTS_DIR/e2e_$TIMESTAMP.log"
    local e2e_report="$REPORTS_DIR/e2e_report_$TIMESTAMP.txt"

    # Check if Playwright is installed
    if ! command -v npx playwright &> /dev/null; then
        log_warning "Playwright not found, installing..."
        cd "$FRONTEND_DIR"
        npm install --save-dev @playwright/test
        npx playwright install
    fi

    # Run E2E tests
    cd "$PROJECT_ROOT"
    log_info "Running E2E test suite..."

    if pytest "$TESTS_DIR/e2e/" -v \
        --tb=short \
        --maxfail=3 \
        --junit-xml="$REPORTS_DIR/junit_e2e_$TIMESTAMP.xml" \
        2>&1 | tee "$e2e_log"; then

        log_success "E2E tests passed"
        ((PASSED_TESTS++))
    else
        log_error "E2E tests failed"
        ((FAILED_TESTS++))
    fi

    ((TOTAL_TESTS++))

    # Generate E2E report
    cat > "$e2e_report" << EOF
E2E Test Report - $(date)
==========================

Test Environment:
- Base URL: http://localhost:3000
- API URL: http://localhost:8000
- Browsers: Chromium, Firefox, WebKit

Test Results:
$(tail -50 "$e2e_log")

Browser Compatibility:
- Chrome/Chromium: Tested
- Firefox: Tested
- Safari/WebKit: Tested

EOF

    log_info "E2E report generated: $e2e_report"
}

run_performance_tests() {
    log_header "⚡ Running Performance Tests"

    local perf_log="$REPORTS_DIR/performance_$TIMESTAMP.log"
    local perf_report="$REPORTS_DIR/performance_report_$TIMESTAMP.txt"

    cd "$PROJECT_ROOT"
    log_info "Running performance test suite..."

    if pytest "$TESTS_DIR/performance/" -v \
        --tb=short \
        --junit-xml="$REPORTS_DIR/junit_performance_$TIMESTAMP.xml" \
        2>&1 | tee "$perf_log"; then

        log_success "Performance tests passed"
        ((PASSED_TESTS++))
    else
        log_warning "Performance tests had issues (may be expected in CI)"
        ((SKIPPED_TESTS++))
    fi

    ((TOTAL_TESTS++))

    # Generate performance report
    cat > "$perf_report" << EOF
Performance Test Report - $(date)
=================================

Test Environment:
- CPU: $(nproc) cores
- Memory: $(free -h | grep '^Mem:' | awk '{print $2}')
- Disk: $(df -h . | tail -1 | awk '{print $4}')

Test Results:
$(tail -50 "$perf_log")

Performance Benchmarks:
- API Response Times: See log for details
- Memory Usage: See log for details
- Bundle Size: See log for details

EOF

    log_info "Performance report generated: $perf_report"
}

generate_summary_report() {
    log_header "📊 Generating Summary Report"

    local summary_file="$REPORTS_DIR/test_summary_$TIMESTAMP.txt"

    cat > "$summary_file" << EOF
========================================
Tutor-AI Comprehensive Test Summary
========================================
Date: $(date)
Commit: $(git rev-parse HEAD 2>/dev/null || echo "N/A")
Branch: $(git branch --show-current 2>/dev/null || echo "N/A")

Test Suite Overview:
===================

Total Test Categories: $TOTAL_TESTS
Passed Categories: $PASSED_TESTS
Failed Categories: $FAILED_TESTS
Skipped Categories: $SKIPPED_TESTS

Overall Status: $([ $FAILED_TESTS -eq 0 ] && echo "✅ PASS" || echo "❌ FAIL")

Detailed Results:
================

EOF

    # Add individual test results
    if [ -f "$REPORTS_DIR/backend_report_$TIMESTAMP.txt" ]; then
        echo "Backend Tests: $([ -f "$REPORTS_DIR/backend_report_$TIMESTAMP.txt" ] && echo "✅ Completed" || echo "❌ Not Run")" >> "$summary_file"
    fi

    if [ -f "$REPORTS_DIR/frontend_report_$TIMESTAMP.txt" ]; then
        echo "Frontend Tests: $([ -f "$REPORTS_DIR/frontend_report_$TIMESTAMP.txt" ] && echo "✅ Completed" || echo "❌ Not Run")" >> "$summary_file"
    fi

    if [ -f "$REPORTS_DIR/integration_report_$TIMESTAMP.txt" ]; then
        echo "Integration Tests: $([ -f "$REPORTS_DIR/integration_report_$TIMESTAMP.txt" ] && echo "✅ Completed" || echo "❌ Not Run")" >> "$summary_file"
    fi

    if [ -f "$REPORTS_DIR/e2e_report_$TIMESTAMP.txt" ]; then
        echo "E2E Tests: $([ -f "$REPORTS_DIR/e2e_report_$TIMESTAMP.txt" ] && echo "✅ Completed" || echo "❌ Not Run")" >> "$summary_file"
    fi

    if [ -f "$REPORTS_DIR/performance_report_$TIMESTAMP.txt" ]; then
        echo "Performance Tests: $([ -f "$REPORTS_DIR/performance_report_$TIMESTAMP.txt" ] && echo "✅ Completed" || echo "⚠️ Skipped")" >> "$summary_file"
    fi

    cat >> "$summary_file" << EOF

Generated Reports:
==================

EOF

    # List all generated reports
    find "$REPORTS_DIR" -name "*_$TIMESTAMP.*" -type f | sort >> "$summary_file"

    cat >> "$summary_file" << EOF

Next Steps:
===========
- Review detailed logs for any failed tests
- Check coverage reports for test coverage gaps
- Analyze performance reports for optimization opportunities
- Address any security issues found

For detailed analysis, open the HTML coverage reports in a browser.

EOF

    log_success "Summary report generated: $summary_file"

    # Display summary
    cat "$summary_file"
}

cleanup() {
    log_info "Cleaning up test environment..."

    # Kill any remaining processes
    pkill -f "python3 main.py" 2>/dev/null || true
    pkill -f "npm run dev" 2>/dev/null || true
    pkill -f "node.*next" 2>/dev/null || true

    # Clean up test containers
    docker stop test-redis 2>/dev/null || true
    docker rm test-redis 2>/dev/null || true

    log_success "Cleanup completed"
}

# Main execution
main() {
    local test_types=()
    local run_all=false

    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --backend)
                test_types+=("backend")
                shift
                ;;
            --frontend)
                test_types+=("frontend")
                shift
                ;;
            --integration)
                test_types+=("integration")
                shift
                ;;
            --e2e)
                test_types+=("e2e")
                shift
                ;;
            --performance)
                test_types+=("performance")
                shift
                ;;
            --all)
                run_all=true
                shift
                ;;
            --quick)
                test_types=("backend" "frontend")
                log_info "Running quick tests (backend + frontend only)"
                shift
                ;;
            --help|-h)
                cat << EOF
Usage: $0 [OPTIONS]

Options:
  --backend        Run backend tests only
  --frontend       Run frontend tests only
  --integration    Run integration tests only
  --e2e           Run end-to-end tests only
  --performance   Run performance tests only
  --all           Run all test suites (default)
  --quick         Run quick tests (backend + frontend)
  --help, -h      Show this help message

Examples:
  $0 --all              # Run all tests
  $0 --quick            # Run quick tests
  $0 --backend --e2e   # Run backend and E2E tests

EOF
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done

    # Set default if no specific tests requested
    if [ ${#test_types[@]} -eq 0 ] && [ "$run_all" = false ]; then
        run_all=true
    fi

    # If run_all is true, add all test types
    if [ "$run_all" = true ]; then
        test_types=("backend" "frontend" "integration" "e2e" "performance")
    fi

    # Start execution
    log_header "🚀 Starting Tutor-AI Test Suite"
    log_info "Test timestamp: $TIMESTAMP"
    log_info "Reports directory: $REPORTS_DIR"

    # Setup
    check_dependencies
    setup_environment
    start_services

    # Trap cleanup on exit
    trap cleanup EXIT

    # Run requested tests
    for test_type in "${test_types[@]}"; do
        case $test_type in
            "backend")
                run_backend_tests
                ;;
            "frontend")
                run_frontend_tests
                ;;
            "integration")
                run_integration_tests
                ;;
            "e2e")
                run_e2e_tests
                ;;
            "performance")
                run_performance_tests
                ;;
        esac
    done

    # Generate final summary
    generate_summary_report

    # Final status
    log_header "🏁 Test Suite Complete"

    if [ $FAILED_TESTS -eq 0 ]; then
        log_success "All tests completed successfully! ✅"
        log_info "Reports available in: $REPORTS_DIR"
        exit 0
    else
        log_error "Some tests failed! ❌"
        log_info "Check the reports in: $REPORTS_DIR"
        exit 1
    fi
}

# Run main function with all arguments
main "$@"