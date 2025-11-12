#!/bin/bash

# Comprehensive Connectivity Test Script for Tutor-AI
# Tests all critical endpoints and port configurations

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BACKEND_URL="http://localhost:8000"
FRONTEND_URL="http://localhost:3001"
REDIS_HOST="localhost"
REDIS_PORT="6379"

# Test counters
TESTS_TOTAL=0
TESTS_PASSED=0
TESTS_FAILED=0

# Function to print test results
print_test() {
    local test_name="$1"
    local result="$2"
    local message="$3"

    TESTS_TOTAL=$((TESTS_TOTAL + 1))

    if [ "$result" = "PASS" ]; then
        echo -e "${GREEN}✅ PASS${NC}: $test_name"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}❌ FAIL${NC}: $test_name"
        if [ -n "$message" ]; then
            echo -e "   ${RED}   $message${NC}"
        fi
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
}

# Function to check if port is open
check_port() {
    local host="$1"
    local port="$2"
    local service="$3"

    if curl -s --connect-timeout 5 "http://$host:$port" > /dev/null 2>&1; then
        print_test "Port $port ($service)" "PASS"
        return 0
    else
        print_test "Port $port ($service)" "FAIL" "Connection refused or timeout"
        return 1
    fi
}

# Function to test HTTP endpoint
test_endpoint() {
    local url="$1"
    local expected_status="$2"
    local test_name="$3"

    local response
    response=$(curl -s -w "%{http_code}" "$url" 2>/dev/null)
    local status_code="${response: -3}"
    local body="${response%???}"

    if [ "$status_code" = "$expected_status" ]; then
        print_test "$test_name" "PASS" "HTTP $status_code"
        return 0
    else
        print_test "$test_name" "FAIL" "Expected HTTP $expected_status, got HTTP $status_code"
        return 1
    fi
}

# Function to test Docker containers
test_docker_containers() {
    echo -e "\n${BLUE}📦 Testing Docker Containers...${NC}"

    # Check if Docker is running
    if ! docker info > /dev/null 2>&1; then
        print_test "Docker daemon" "FAIL" "Docker daemon is not running"
        return 1
    fi

    print_test "Docker daemon" "PASS"

    # Check individual containers
    local containers=("tutor-ai-backend" "tutor-ai-frontend" "tutor-ai-redis")

    for container in "${containers[@]}"; do
        if docker ps --filter "name=$container" --format "{{.Status}}" | grep -q "healthy\|Up"; then
            print_test "Container $container" "PASS"
        else
            print_test "Container $container" "FAIL" "Container not running or unhealthy"
        fi
    done
}

# Function to test basic connectivity
test_basic_connectivity() {
    echo -e "\n${BLUE}🔗 Testing Basic Connectivity...${NC}"

    # Test backend health
    test_endpoint "$BACKEND_URL/health" "200" "Backend health endpoint"

    # Test frontend accessibility
    test_endpoint "$FRONTEND_URL" "200" "Frontend home page"

    # Test Redis connection (if redis-cli is available)
    if command -v redis-cli &> /dev/null; then
        if redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" ping | grep -q "PONG"; then
            print_test "Redis connection" "PASS"
        else
            print_test "Redis connection" "FAIL" "Cannot connect to Redis"
        fi
    else
        print_test "Redis connection" "SKIP" "redis-cli not available"
    fi
}

# Function to test API endpoints
test_api_endpoints() {
    echo -e "\n${BLUE}🔌 Testing API Endpoints...${NC}"

    # Test courses endpoint
    test_endpoint "$BACKEND_URL/courses" "200" "Courses API endpoint"

    # Test backend API docs
    test_endpoint "$BACKEND_URL/docs" "200" "API documentation"

    # Test OpenAPI schema
    test_endpoint "$BACKEND_URL/openapi.json" "200" "OpenAPI schema"
}

# Function to test CORS configuration
test_cors() {
    echo -e "\n${BLUE}🌐 Testing CORS Configuration...${NC}"

    # Test CORS preflight request
    local cors_response
    cors_response=$(curl -s -X OPTIONS "$BACKEND_URL/courses" \
        -H "Origin: $FRONTEND_URL" \
        -H "Access-Control-Request-Method: GET" \
        -H "Access-Control-Request-Headers: Content-Type" \
        -w "%{http_code}" 2>/dev/null)

    local status_code="${cors_response: -3}"

    if [ "$status_code" = "200" ] || [ "$status_code" = "204" ]; then
        print_test "CORS preflight (GET /courses)" "PASS"
    else
        print_test "CORS preflight (GET /courses)" "FAIL" "CORS not properly configured"
    fi
}

# Function to test dynamic routes
test_dynamic_routes() {
    echo -e "\n${BLUE}🛣️  Testing Dynamic Routes...${NC}"

    # Note: These tests assume there's data available
    # Test courses listing page
    test_endpoint "$FRONTEND_URL/courses" "200" "Courses listing page"

    # Test if courses exist first
    local courses_response
    courses_response=$(curl -s "$BACKEND_URL/courses" 2>/dev/null)

    if echo "$courses_response" | grep -q '"id"'; then
        # Extract first course ID for testing
        local course_id
        course_id=$(echo "$courses_response" | grep -o '"id":"[^"]*' | head -1 | cut -d'"' -f4)

        if [ -n "$course_id" ]; then
            # Test course detail page
            test_endpoint "$FRONTEND_URL/courses/$course_id" "200" "Course detail page"

            # Test books listing
            test_endpoint "$FRONTEND_URL/courses/$course_id/books" "200" "Books listing page"

            # Test course books API
            test_endpoint "$BACKEND_URL/courses/$course_id/books" "200" "Course books API"
        fi
    fi
}

# Function to test file uploads
test_file_upload() {
    echo -e "\n${BLUE}📁 Testing File Upload Endpoint...${NC}"

    # Create a test file
    local test_file="/tmp/test_upload.txt"
    echo "This is a test file for upload testing." > "$test_file"

    # Test upload endpoint accessibility (not actual upload)
    local upload_response
    upload_response=$(curl -s -w "%{http_code}" -X OPTIONS "$BACKEND_URL/courses/test-course/upload" 2>/dev/null)

    if [ "$upload_response" = "200" ] || [ "$upload_response" = "204" ] || [ "$upload_response" = "405" ]; then
        print_test "Upload endpoint accessibility" "PASS" "Endpoint responds (may require auth)"
    else
        print_test "Upload endpoint accessibility" "FAIL" "Upload endpoint not accessible"
    fi

    # Clean up
    rm -f "$test_file"
}

# Function to display final results
display_results() {
    echo -e "\n${BLUE}📊 Test Results Summary${NC}"
    echo -e "================================"
    echo -e "Total Tests: $TESTS_TOTAL"
    echo -e "${GREEN}Passed: $TESTS_PASSED${NC}"
    echo -e "${RED}Failed: $TESTS_FAILED${NC}"

    if [ $TESTS_FAILED -eq 0 ]; then
        echo -e "\n${GREEN}🎉 All tests passed! System is fully operational.${NC}"
        return 0
    else
        echo -e "\n${RED}⚠️  Some tests failed. Please check the issues above.${NC}"
        return 1
    fi
}

# Main execution
main() {
    echo -e "${BLUE}🧪 Tutor-AI Connectivity Test Suite${NC}"
    echo -e "====================================="
    echo -e "Testing system connectivity and functionality..."
    echo -e "Backend URL: $BACKEND_URL"
    echo -e "Frontend URL: $FRONTEND_URL"
    echo -e "Redis: $REDIS_HOST:$REDIS_PORT"

    # Run all test suites
    test_docker_containers
    test_basic_connectivity
    test_api_endpoints
    test_cors
    test_dynamic_routes
    test_file_upload

    # Display final results
    display_results
}

# Check if script is being run directly
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    main "$@"
fi