#!/bin/bash

# PDF Production Test Script
# Tests PDF loading functionality in production mode

set -e

echo "🔍 Tutor-AI PDF Production Test Script"
echo "======================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Test 1: Check if production services are running
test_production_services() {
    log_info "Testing production services..."

    # Check backend health
    if curl -s -f http://localhost:8000/health > /dev/null; then
        log_success "Backend is healthy"
    else
        log_error "Backend is not responding on port 8000"
        return 1
    fi

    # Check frontend
    if curl -s -f http://localhost:3001 > /dev/null; then
        log_success "Frontend is responding"
    else
        log_error "Frontend is not responding on port 3001"
        return 1
    fi

    return 0
}

# Test 2: Check PDF worker accessibility
test_pdf_worker() {
    log_info "Testing PDF.js worker accessibility..."

    # Test local worker
    if curl -s -f http://localhost:3001/pdf.worker.min.js > /dev/null; then
        log_success "Local PDF worker accessible"
    else
        log_warning "Local PDF worker not accessible"
    fi

    # Test backend worker
    if curl -s -f http://localhost:8000/pdf.worker.min.js > /dev/null; then
        log_success "Backend PDF worker accessible"
    else
        log_error "Backend PDF worker not accessible"
        return 1
    fi

    # Test backend PDF worker health check
    if curl -s -f http://localhost:8000/health/pdf-worker > /dev/null; then
        local health_response=$(curl -s http://localhost:8000/health/pdf-worker)
        log_success "PDF worker health check passed"
        echo "Health check response: $health_response" | head -n 1
    else
        log_error "PDF worker health check failed"
        return 1
    fi

    return 0
}

# Test 3: Test PDF functionality through API
test_pdf_api() {
    log_info "Testing PDF functionality through API..."

    # Get available courses
    local courses_response=$(curl -s http://localhost:8000/courses)
    if [ $? -eq 0 ] && [ "$courses_response" != "null" ]; then
        log_success "Courses API working"

        # Extract first course ID (basic parsing)
        local first_course_id=$(echo "$courses_response" | grep -o '"id":"[^"]*"' | head -n 1 | cut -d'"' -f4)

        if [ ! -z "$first_course_id" ]; then
            log_success "Found course ID: $first_course_id"

            # Test course materials endpoint
            if curl -s -f "http://localhost:8000/courses/$first_course_id/materials" > /dev/null; then
                log_success "Course materials API working"
            else
                log_warning "Course materials API not working"
            fi
        else
            log_warning "No courses found"
        fi
    else
        log_error "Courses API not working"
        return 1
    fi

    return 0
}

# Test 4: Test Docker configuration
test_docker_config() {
    log_info "Testing Docker configuration..."

    # Check if running in Docker
    if [ -f /.dockerenv ]; then
        log_success "Running inside Docker container"

        # Check if public directory is accessible
        if [ -d "/app/public" ]; then
            log_success "Public directory accessible in container"
        else
            log_warning "Public directory not accessible in container"
        fi

        # Check if PDF worker exists in expected locations
        if [ -f "/app/public/pdf.worker.min.js" ]; then
            log_success "PDF worker exists in container public directory"
        else
            log_warning "PDF worker not found in container public directory"
        fi
    else
        log_info "Not running in Docker container"
    fi

    return 0
}

# Test 5: Validate build configuration
test_build_validation() {
    log_info "Testing build validation..."

    # Change to frontend directory
    cd frontend

    # Run build validation script
    if npm run validate:build; then
        log_success "Build validation passed"
    else
        log_error "Build validation failed"
        cd ..
        return 1
    fi

    cd ..
    return 0
}

# Test 6: Browser accessibility test
test_browser_accessibility() {
    log_info "Testing browser accessibility..."

    # Test if we can access the main application
    local frontend_response=$(curl -s -I http://localhost:3001)
    if echo "$frontend_response" | grep -q "200 OK"; then
        log_success "Frontend accessible via HTTP"
    else
        log_error "Frontend not accessible via HTTP"
        return 1
    fi

    # Test CORS headers
    local backend_response=$(curl -s -I http://localhost:8000/pdf.worker.min.js)
    if echo "$backend_response" | grep -qi "access-control-allow-origin"; then
        log_success "CORS headers present on PDF worker endpoint"
    else
        log_warning "CORS headers not found on PDF worker endpoint"
    fi

    return 0
}

# Main execution
main() {
    echo "Starting PDF production tests..."
    echo ""

    local test_failed=0

    # Run all tests
    if ! test_production_services; then
        log_error "Production services test failed"
        test_failed=1
    fi
    echo ""

    if ! test_pdf_worker; then
        log_error "PDF worker test failed"
        test_failed=1
    fi
    echo ""

    if ! test_pdf_api; then
        log_error "PDF API test failed"
        test_failed=1
    fi
    echo ""

    if ! test_docker_config; then
        log_error "Docker configuration test failed"
        test_failed=1
    fi
    echo ""

    if ! test_build_validation; then
        log_error "Build validation test failed"
        test_failed=1
    fi
    echo ""

    if ! test_browser_accessibility; then
        log_error "Browser accessibility test failed"
        test_failed=1
    fi
    echo ""

    # Final results
    if [ $test_failed -eq 0 ]; then
        log_success "All tests passed! 🎉"
        echo ""
        echo "PDF loading should now work correctly in production mode."
        echo "Access the application at: http://localhost:3001"
        echo "Backend API at: http://localhost:8000"
        echo "PDF Worker at: http://localhost:8000/pdf.worker.min.js"
        exit 0
    else
        log_error "Some tests failed. Please check the errors above."
        echo ""
        echo "Common issues and solutions:"
        echo "1. Backend not responding: Check if containers are running with './docker.sh status'"
        echo "2. PDF worker not found: Ensure frontend is built with 'npm run build'"
        echo "3. CORS issues: Check backend CORS configuration"
        exit 1
    fi
}

# Check if running with appropriate permissions
if [ "$EUID" -ne 0 ]; then
    echo "Note: This script can be run as regular user."
fi

# Run main function
main "$@"