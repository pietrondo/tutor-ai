#!/bin/bash

# Script per eseguire tutti i test dell'applicazione
# Verifica chat, PDF reader, e integrazione completa

echo "🚀 Tutor-AI Test Suite"
echo "======================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to run a test
run_test() {
    local test_name=$1
    local test_file=$2

    echo -e "\n${BLUE}🧪 Running: ${test_name}${NC}"
    echo "----------------------------------------"

    if node $test_file; then
        echo -e "${GREEN}✅ ${test_name} PASSED${NC}"
        return 0
    else
        echo -e "${RED}❌ ${test_name} FAILED${NC}"
        return 1
    fi
}

# Function to check if services are running
check_services() {
    echo -e "${BLUE}🔍 Checking services...${NC}"

    # Check backend
    if curl -s http://localhost:8001/health > /dev/null; then
        echo -e "${GREEN}✅ Backend is running (port 8001)${NC}"
    else
        echo -e "${RED}❌ Backend is not running on port 8001${NC}"
        echo "Please start the application with: ./start.sh dev"
        exit 1
    fi

    # Check frontend
    if curl -s http://localhost:3000 > /dev/null; then
        echo -e "${GREEN}✅ Frontend is running (port 3000)${NC}"
    else
        echo -e "${RED}❌ Frontend is not running on port 3000${NC}"
        echo "Please start the application with: ./start.sh dev"
        exit 1
    fi

    echo ""
}

# Main execution
main() {
    echo -e "${BLUE}📍 Testing environment:${NC}"
    echo "   Frontend: http://localhost:3000"
    echo "   Backend:  http://localhost:8001"
    echo ""

    # Check if services are running
    check_services

    # Track results
    local passed=0
    local total=0

    # Run ChatWrapper test
    ((total++))
    if run_test "ChatWrapper Test" "tests/chat_wrapper_test.js"; then
        ((passed++))
    fi

    # Run Full Functionality test
    ((total++))
    if run_test "Full Functionality Test" "tests/full_functionality_test.js"; then
        ((passed++))
    fi

    # Summary
    echo ""
    echo "========================================"
    echo -e "${BLUE}📊 TEST SUMMARY${NC}"
    echo "========================================"
    echo -e "Tests passed: ${GREEN}${passed}${NC}/${total}"
    echo -e "Tests failed: ${RED}$((total - passed))${NC}/${total}"

    if [ $passed -eq $total ]; then
        echo -e "\n${GREEN}🎉 ALL TESTS PASSED!${NC}"
        echo -e "${GREEN}✅ ChatWrapper error has been fixed${NC}"
        echo -e "${GREEN}✅ PDF reader is accessible${NC}"
        echo -e "${GREEN}✅ All navigation flows work correctly${NC}"
        exit 0
    else
        echo -e "\n${RED}❌ SOME TESTS FAILED${NC}"
        echo -e "${YELLOW}Please check the logs above for details${NC}"
        exit 1
    fi
}

# Check if we're in the right directory
if [ ! -f "package.json" ]; then
    echo -e "${RED}❌ Error: Please run this script from the project root directory${NC}"
    exit 1
fi

# Run main function
main "$@"