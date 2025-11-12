#!/bin/bash

# Master Test Runner for Tutor-AI
# Runs all connectivity and functionality tests

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Configuration
BACKEND_URL="http://localhost:8001"
FRONTEND_URL="http://localhost:3001"

# Test results
TEST_SUITES=()
PASSED_SUITES=()
FAILED_SUITES=()

# Function to print header
print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BOLD}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

# Function to run test suite
run_test_suite() {
    local suite_name="$1"
    local test_command="$2"
    local description="$3"

    echo -e "\n${YELLOW}🧪 Running $suite_name...${NC}"
    echo -e "Description: $description"
    echo -e "Command: $test_command"

    # Change to project root directory
    cd "$PROJECT_ROOT"

    # Run the test and capture result
    if eval "$test_command"; then
        echo -e "${GREEN}✅ $suite_name PASSED${NC}"
        PASSED_SUITES+=("$suite_name")
        return 0
    else
        echo -e "${RED}❌ $suite_name FAILED${NC}"
        FAILED_SUITES+=("$suite_name")
        return 1
    fi
}

# Function to check prerequisites
check_prerequisites() {
    print_header "🔍 Checking Prerequisites"

    local all_good=true

    # Check if Docker is running
    if docker info > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Docker daemon is running${NC}"
    else
        echo -e "${RED}❌ Docker daemon is not running${NC}"
        all_good=false
    fi

    # Check if required ports are accessible
    if curl -s --connect-timeout 5 "$BACKEND_URL/health" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Backend is accessible ($BACKEND_URL)${NC}"
    else
        echo -e "${RED}❌ Backend is not accessible ($BACKEND_URL)${NC}"
        all_good=false
    fi

    if curl -s --connect-timeout 5 "$FRONTEND_URL" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Frontend is accessible ($FRONTEND_URL)${NC}"
    else
        echo -e "${RED}❌ Frontend is not accessible ($FRONTEND_URL)${NC}"
        all_good=false
    fi

    # Check if Python 3 is available
    if command -v python3 &> /dev/null; then
        echo -e "${GREEN}✅ Python 3 is available${NC}"
    else
        echo -e "${RED}❌ Python 3 is not available${NC}"
        all_good=false
    fi

    # Check if required Python packages are available
    if python3 -c "import requests" 2>/dev/null; then
        echo -e "${GREEN}✅ Python 'requests' package is available${NC}"
    else
        echo -e "${YELLOW}⚠️  Python 'requests' package is not available, installing...${NC}"
        pip3 install requests || {
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

# Function to display final results
display_final_results() {
    print_header "📊 Final Test Results"

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

    echo -e "\nSuccess Rate: ${success_rate}%"

    if [ $failed_count -eq 0 ]; then
        echo -e "\n${GREEN}${BOLD}🎉 ALL TESTS PASSED! System is fully operational.${NC}"
        return 0
    else
        echo -e "\n${RED}${BOLD}⚠️  SOME TESTS FAILED! Please check the issues above.${NC}"
        return 1
    fi
}

# Function to show usage
show_usage() {
    echo -e "${BOLD}Tutor-AI Test Runner${NC}"
    echo -e "Usage: $0 [OPTIONS]"
    echo -e ""
    echo -e "Options:"
    echo -e "  -h, --help     Show this help message"
    echo -e "  -q, --quick    Run only quick tests (basic connectivity)"
    echo -e "  -v, --verbose  Enable verbose output"
    echo -e "  --connectivity Run only connectivity tests"
    echo -e "  --api          Run only API tests"
    echo -e "  --routes       Run only dynamic routes tests"
    echo -e "  --links        Run only frontend links tests"
    echo -e "  --materials    Run only materials validation tests"
    echo -e ""
    echo -e "Examples:"
    echo -e "  $0                # Run all tests"
    echo -e "  $0 --quick        # Run quick tests only"
    echo -e "  $0 --connectivity # Run connectivity tests only"
}

# Main execution
main() {
    local quick_mode=false
    local verbose=false
    local connectivity_only=false
    local api_only=false
    local routes_only=false

    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_usage
                exit 0
                ;;
            -q|--quick)
                quick_mode=true
                shift
                ;;
            -v|--verbose)
                verbose=true
                shift
                ;;
            --connectivity)
                connectivity_only=true
                shift
                ;;
            --api)
                api_only=true
                shift
                ;;
            --routes)
                routes_only=true
                shift
                ;;
            --links)
                links_only=true
                shift
                ;;
            --materials)
                materials_only=true
                shift
                ;;
            *)
                echo -e "${RED}Unknown option: $1${NC}"
                show_usage
                exit 1
                ;;
        esac
    done

    # Check for conflicting options
    if [ "$connectivity_only" = true ] && [ "$api_only" = true ]; then
        echo -e "${RED}Error: Cannot specify both --connectivity and --api${NC}"
        exit 1
    fi

    if [ "$connectivity_only" = true ] && [ "$routes_only" = true ]; then
        echo -e "${RED}Error: Cannot specify both --connectivity and --routes${NC}"
        exit 1
    fi

    if [ "$api_only" = true ] && [ "$routes_only" = true ]; then
        echo -e "${RED}Error: Cannot specify both --api and --routes${NC}"
        exit 1
    fi

    if [ "$connectivity_only" = true ] && [ "$links_only" = true ]; then
        echo -e "${RED}Error: Cannot specify both --connectivity and --links${NC}"
        exit 1
    fi

    if [ "$api_only" = true ] && [ "$links_only" = true ]; then
        echo -e "${RED}Error: Cannot specify both --api and --links${NC}"
        exit 1
    fi

    if [ "$routes_only" = true ] && [ "$links_only" = true ]; then
        echo -e "${RED}Error: Cannot specify both --routes and --links${NC}"
        exit 1
    fi

    if [ "$connectivity_only" = true ] && [ "$materials_only" = true ]; then
        echo -e "${RED}Error: Cannot specify both --connectivity and --materials${NC}"
        exit 1
    fi

    if [ "$api_only" = true ] && [ "$materials_only" = true ]; then
        echo -e "${RED}Error: Cannot specify both --api and --materials${NC}"
        exit 1
    fi

    if [ "$routes_only" = true ] && [ "$materials_only" = true ]; then
        echo -e "${RED}Error: Cannot specify both --routes and --materials${NC}"
        exit 1
    fi

    if [ "$links_only" = true ] && [ "$materials_only" = true ]; then
        echo -e "${RED}Error: Cannot specify both --links and --materials${NC}"
        exit 1
    fi

    print_header "🧪 Tutor-AI Comprehensive Test Suite"
    echo -e "Project Root: $PROJECT_ROOT"
    echo -e "Backend URL: $BACKEND_URL"
    echo -e "Frontend URL: $FRONTEND_URL"
    echo -e "Quick Mode: $quick_mode"
    echo -e "Verbose Mode: $verbose"

    # Check prerequisites
    check_prerequisites

    # Define test suites
    local test_suites=()

    if [ "$quick_mode" = true ]; then
        test_suites+=(
            "Basic Connectivity:./tests/connectivity/connectivity_test.sh --quick:Quick health and connectivity checks"
        )
    elif [ "$connectivity_only" = true ]; then
        test_suites+=(
            "Connectivity Tests:./tests/connectivity/connectivity_test.sh:Comprehensive connectivity and health checks"
        )
    elif [ "$api_only" = true ]; then
        test_suites+=(
            "API Tests:python3 tests/connectivity/api_test.py:API endpoints and CORS testing"
        )
    elif [ "$routes_only" = true ]; then
        test_suites+=(
            "Dynamic Routes Tests:python3 tests/connectivity/dynamic_routes_test.py:Dynamic routes validation"
            "Frontend Links Tests:python3 tests/connectivity/frontend_links_test.py:Frontend links validation"
        )
    elif [ "$links_only" = true ]; then
        test_suites+=(
            "Frontend Links Tests:python3 tests/connectivity/frontend_links_test.py:Frontend links validation"
        )
    elif [ "$materials_only" = true ]; then
        test_suites+=(
            "Materials Validation Tests:python3 tests/connectivity/materials_validation_test.py:Materials validation and accessibility"
        )
    else
        test_suites+=(
            "Connectivity Tests:./tests/connectivity/connectivity_test.sh:Comprehensive connectivity and health checks"
            "API Tests:python3 tests/connectivity/api_test.py:API endpoints and CORS testing"
            "Dynamic Routes Tests:python3 tests/connectivity/dynamic_routes_test.py:Dynamic routes validation"
            "Frontend Links Tests:python3 tests/connectivity/frontend_links_test.py:Frontend links validation"
            "Materials Validation Tests:python3 tests/connectivity/materials_validation_test.py:Materials validation and accessibility"
        )
    fi

    # Run test suites
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

    # Display final results
    display_final_results
}

# Check if script is being run directly
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    main "$@"
fi