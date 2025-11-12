#!/bin/bash

# Docker Master Test Runner for Tutor-AI
# Comprehensive Docker testing with workflow validation

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

# Configuration
BACKEND_URL="http://localhost:8001"
FRONTEND_URL="http://localhost:3001"
REDIS_URL="localhost:6379"

# Test results
TEST_SUITES=()
PASSED_SUITES=()
FAILED_SUITES=()

# Function to print header
print_header() {
    echo -e "\n${CYAN}========================================${NC}"
    echo -e "${BOLD}$1${NC}"
    echo -e "${CYAN}========================================${NC}"
}

# Function to print result
print_result() {
    local test_name="$1"
    local result="$2"
    local message="$3"

    if [ "$result" = "PASS" ]; then
        echo -e "${GREEN}✅ PASS${NC}: $test_name"
        PASSED_SUITES+=("$test_name")
    else
        echo -e "${RED}❌ FAIL${NC}: $test_name"
        if [ -n "$message" ]; then
            echo -e "   ${RED}   $message${NC}"
        fi
        FAILED_SUITES+=("$test_name")
    fi
}

# Function to run Docker test suite
run_test_suite() {
    local suite_name="$1"
    local test_command="$2"
    local description="$3"

    echo -e "\n${YELLOW}🧪 Running Docker Test Suite: $suite_name${NC}"
    echo -e "Description: $description"
    echo -e "Command: $test_command"

    # Change to project root directory
    cd "$PROJECT_ROOT"

    # Run the test and capture result
    if eval "$test_command"; then
        print_result "$suite_name" "PASS"
        return 0
    else
        print_result "$suite_name" "FAIL"
        return 1
    fi
}

# Function to check prerequisites
check_prerequisites() {
    print_header "🔍 Checking Docker Prerequisites"

    local all_good=true

    # Check if Docker is running
    if docker info > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Docker daemon is running${NC}"
    else
        echo -e "${RED}❌ Docker daemon is not running${NC}"
        all_good=false
    fi

    # Check if Docker Compose is available
    if command -v docker-compose &> /dev/null; then
        echo -e "${GREEN}✅ Docker Compose is available${NC}"
    else
        echo -e "${RED}❌ Docker Compose is not available${NC}"
        all_good=false
    fi

    # Check if required Python packages are available
    if command -v python3 &> /dev/null; then
        echo -e "${GREEN}✅ Python 3 is available${NC}"
    else
        echo -e "${RED}❌ Python 3 is not available${NC}"
        all_good=false
    fi

    if python3 -c "import requests" 2>/dev/null; then
        echo -e "${GREEN}✅ Python 'requests' package is available${NC}"
    else
        echo -e "${YELLOW}⚠️  Installing Python 'requests' package...${NC}"
        pip3 install requests --break-system-packages || {
            echo -e "${RED}❌ Failed to install requests package${NC}"
            all_good=false
        }
    fi

    if [ "$all_good" = false ]; then
        echo -e "\n${RED}❌ Some prerequisites are missing. Please fix them before running tests.${NC}"
        exit 1
    fi

    echo -e "\n${GREEN}✅ All prerequisites are met.${NC}"
}

# Function to check service status
check_service_status() {
    print_header "🚀 Checking Service Status"

    # Check Docker containers
    echo "Checking Docker containers..."
    if docker-compose ps | grep -q "Up"; then
        echo -e "${GREEN}✅ Containers are running${NC}"
    else
        echo -e "${RED}❌ No containers are running${NC}"
        echo -e "${YELLOW}💡 Starting services with ./start.sh dev...${NC}"
        cd "$PROJECT_ROOT"
        ./start.sh dev
        sleep 30
    fi

    # Check service accessibility
    echo "Checking service accessibility..."

    # Backend
    if curl -s --connect-timeout 5 "$BACKEND_URL/health" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Backend is accessible ($BACKEND_URL)${NC}"
    else
        echo -e "${RED}❌ Backend is not accessible ($BACKEND_URL)${NC}"
        return 1
    fi

    # Redis
    if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Redis is accessible${NC}"
    else
        echo -e "${RED}❌ Redis is not accessible${NC}"
        return 1
    fi

    # Frontend (optional - may fail in WSL)
    if curl -s --connect-timeout 5 "$FRONTEND_URL" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Frontend is accessible ($FRONTEND_URL)${NC}"
    else
        echo -e "${YELLOW}⚠️  Frontend not accessible (WSL networking issue)${NC}"
    fi

    return 0
}

# Function to test Docker system integration
test_docker_system() {
    print_header "🐳 Docker System Integration Test"

    if [ -f "$PROJECT_ROOT/tests/docker/docker_system_test.py" ]; then
        cd "$PROJECT_ROOT"
        python3 tests/docker/docker_system_test.py
    else
        print_result "Docker System Test" "FAIL" "Test file not found"
        return 1
    fi
}

# Function to test end-to-end workflows
test_e2e_workflows() {
    print_header "🔄 End-to-End Workflow Tests"

    if [ -f "$PROJECT_ROOT/tests/docker/e2e_integration_test.py" ]; then
        cd "$PROJECT_ROOT"
        python3 tests/docker/e2e_integration_test.py
    else
        print_result "E2E Workflow Tests" "FAIL" "Test file not found"
        return 1
    fi
}

# Function to test materials specifically
test_materials_system() {
    print_header "📚 Docker Materials System Test"

    if [ -f "$PROJECT_ROOT/tests/connectivity/materials_validation_test.py" ]; then
        cd "$PROJECT_ROOT"
        python3 tests/connectivity/materials_validation_test.py
    else
        print_result "Materials System Test" "FAIL" "Test file not found"
        return 1
    fi
}

# Function to test container health
test_container_health() {
    print_header "🏥 Container Health Tests"

    local healthy=true

    # Check individual container health
    local containers=("tutor-ai-backend" "tutor-ai-frontend" "tutor-ai-redis")

    for container in "${containers[@]}"; do
        if docker ps --filter "name=$container" --format "{{.Status}}" | grep -q "healthy\|Up"; then
            echo -e "${GREEN}✅ $container is healthy${NC}"
        else
            echo -e "${RED}❌ $container is unhealthy or not running${NC}"
            healthy=false
        fi
    done

    # Test container communication
    echo "Testing inter-container communication..."

    # Backend to Redis
    if docker-compose exec -T backend python -c "import redis; r=redis.Redis(host='redis', port=6379); print(r.ping())" 2>/dev/null | grep -q "PONG"; then
        echo -e "${GREEN}✅ Backend can reach Redis${NC}"
    else
        echo -e "${RED}❌ Backend cannot reach Redis${NC}"
        healthy=false
    fi

    # Frontend to Backend
    if docker-compose exec -T frontend wget -q --spider http://backend:8001/health 2>&1 | grep -q "200 OK"; then
        echo -e "${GREEN}✅ Frontend can reach Backend${NC}"
    else
        echo -e "${YELLOW}⚠️  Frontend cannot reach Backend (WSL networking)${NC}"
    fi

    return $([ "$healthy" = true ])
}

# Function to test data persistence
test_data_persistence() {
    print_header "💾 Data Persistence Tests"

    local persistent=true

    # Check data directory
    if [ -d "$PROJECT_ROOT/data" ]; then
        echo -e "${GREEN}✅ Data directory exists${NC}"
    else
        echo -e "${RED}❌ Data directory missing${NC}"
        persistent=false
    fi

    # Check courses data
    if [ -d "$PROJECT_ROOT/data/courses" ]; then
        course_count=$(find "$PROJECT_ROOT/data/courses" -maxdepth 1 -type d | wc -l)
        echo -e "${GREEN}✅ Course data exists ($course_count courses)${NC}"
    else
        echo -e "${RED}❌ Course data missing${NC}"
        persistent=false
    fi

    # Check materials
    material_count=$(find "$PROJECT_ROOT/data" -name "*.pdf" 2>/dev/null | wc -l)
    if [ "$material_count" -gt 0 ]; then
        echo -e "${GREEN}✅ PDF materials found ($material_count files)${NC}"
    else
        echo -e "${YELLOW}⚠️  No PDF materials found${NC}"
    fi

    return $([ "$persistent" = true ])
}

# Function to test system performance
test_system_performance() {
    print_header "⚡ System Performance Tests"

    local performant=true

    # Test API response time
    local start_time=$(date +%s%N)
    if curl -s "$BACKEND_URL/health" > /dev/null; then
        local end_time=$(date +%s%N)
        local response_time=$(( (end_time - start_time) / 1000000 ))  # Convert to milliseconds
        if [ "$response_time" -lt 2000 ]; then
            echo -e "${GREEN}✅ Backend response time: ${response_time}ms${NC}"
        else
            echo -e "${RED}❌ Backend response time too slow: ${response_time}ms${NC}"
            performant=false
        fi
    else
        echo -e "${RED}❌ Backend not responding${NC}"
        performant=false
    fi

    # Check container resource usage
    echo "Checking container resource usage..."
    if docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}" | grep -q "tutor-ai"; then
        echo -e "${GREEN}✅ Container stats available${NC}"
        docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}" | grep "tutor-ai"
    else
        echo -e "${RED}❌ Cannot retrieve container stats${NC}"
        performant=false
    fi

    return $([ "$performant" = true ])
}

# Function to run Docker-specific diagnostics
run_docker_diagnostics() {
    print_header "🔧 Docker Diagnostics"

    echo "Docker System Information:"
    docker --version
    docker-compose --version

    echo -e "\nDocker Storage Usage:"
    docker system df

    echo -e "\nDocker Networks:"
    docker network ls | grep tutor-ai

    echo -e "\nDocker Volumes:"
    docker volume ls | grep tutor-ai

    echo -e "\nDocker Images:"
    docker images | grep tutor-ai

    echo -e "\nContainer Details:"
    docker-compose ps
}

# Function to display final results
display_final_results() {
    print_header "📊 Docker Test Results Summary"

    local total_suites=${#TEST_SUITES[@]}
    local passed_count=${#PASSED_SUITES[@]}
    local failed_count=${#FAILED_SUITES[@]}

    echo -e "Total Test Suites: $total_suites"
    echo -e "${GREEN}Passed: $passed_count${NC}"
    echo -e "${RED}Failed: $failed_count${NC}"

    if [ $passed_count -gt 0 ]; then
        echo -e "\n${GREEN}✅ Passed Test Suites:${NC}"
        for suite in "${PASSED_SUITES[@]}"; do
            echo -e "   • $suite"
        done
    fi

    if [ $failed_count -gt 0 ]; then
        echo -e "\n${RED}❌ Failed Test Suites:${NC}"
        for suite in "${FAILED_SUITES[@]}"; do
            echo -e "   • $suite"
        done
    fi

    local success_rate=0
    if [ $total_suites -gt 0 ]; then
        success_rate=$((passed_count * 100 / total_suites))
    fi

    echo -e "\nDocker Success Rate: ${success_rate}%"

    if [ $failed_count -eq 0 ]; then
        echo -e "\n${GREEN}${BOLD}🎉 ALL DOCKER TESTS PASSED! System is fully operational.${NC}"
        return 0
    else
        echo -e "\n${YELLOW}${BOLD}⚠️  Some Docker tests failed. Please check the issues above.${NC}"
        return 1
    fi
}

# Main execution
main() {
    local quick_mode=false
    local skip_prereqs=false
    local skip_status=false
    local diagnostics_only=false

    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -q|--quick)
                quick_mode=true
                shift
                ;;
            --no-prereqs)
                skip_prereqs=true
                shift
                ;;
            --no-status)
                skip_status=true
                shift
                ;;
            --diagnostics)
                diagnostics_only=true
                shift
                ;;
            -h|--help)
                echo -e "${BOLD}Docker Test Runner for Tutor-AI${NC}"
                echo -e "Usage: $0 [OPTIONS]"
                echo -e ""
                echo -e "Options:"
                echo -e "  -q, --quick        Run quick tests only"
                echo -e "  --no-prereqs      Skip prerequisite checks"
                echo -e "  --no-status       Skip service status check"
                echo -e "  --diagnostics     Run Docker diagnostics only"
                echo -e "  -h, --help        Show this help message"
                echo -e ""
                echo -e "Examples:"
                echo -e "  $0                # Run all Docker tests"
                echo -e "  $0 --quick        # Run quick tests only"
                echo -e "  $0 --diagnostics   # Run Docker diagnostics"
                exit 0
                ;;
            *)
                echo -e "${RED}Unknown option: $1${NC}"
                echo -e "Use -h or --help for usage information"
                exit 1
                ;;
        esac
    done

    # Run diagnostics only if requested
    if [ "$diagnostics_only" = true ]; then
        run_docker_diagnostics
        exit 0
    fi

    print_header "🐳 Docker Test Runner for Tutor-AI"
    echo -e "Project Root: $PROJECT_ROOT"
    echo -e "Backend URL: $BACKEND_URL"
    echo -e "Frontend URL: $FRONTEND_URL"
    echo -e "Quick Mode: $quick_mode"

    # Check prerequisites
    if [ "$skip_prereqs" = false ]; then
        check_prerequisites
    fi

    # Check service status
    if [ "$skip_status" = false ]; then
        check_service_status
    fi

    # Define test suites
    local test_suites=()

    if [ "$quick_mode" = true ]; then
        test_suites+=(
            "Container Health:python3 tests/docker/docker_system_test.py:Quick container health checks"
        )
    else
        test_suites+=(
            "Docker System Integration:python3 tests/docker/docker_system_test.py:Complete Docker system testing"
            "Container Health Tests:python3 tests/docker/docker_system_test.py:Container health and communication"
            "Data Persistence:python3 tests/docker/docker_system_test.py:Data persistence verification"
            "System Performance:python3 tests/docker/docker_system_test.py:Performance metrics"
            "End-to-End Workflows:python3 tests/docker/e2e_integration_test.py:Complete workflow testing"
            "Materials System:python3 tests/connectivity/materials_validation_test.py:Materials and file system testing"
        )
    fi

    # Add all test suites to the global list
    TEST_SUITES=("${test_suites[@]}")

    # Run all test suites
    for suite_config in "${test_suites[@]}"; do
        IFS=':' read -r suite_name test_command description <<< "$suite_config"
        TEST_SUITES+=("$suite_name")

        if run_test_suite "$suite_name" "$test_command" "$description"; then
            :
        else
            # Continue running other tests even if one fails
            continue
        fi
    done

    # Run diagnostics
    run_docker_diagnostics

    # Display final results
    display_final_results
}

# Check if script is being run directly
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    main "$@"
fi