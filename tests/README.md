# Tutor-AI Test Suite

Comprehensive testing infrastructure for Tutor-AI connectivity, API endpoints, and dynamic routes validation.

## 📁 Test Structure

```
tests/
├── README.md                           # This file
├── run_all_tests.sh                    # Master test runner
├── docker/                             # Docker-focused testing infrastructure
│   ├── run_docker_tests.sh            # Master Docker test orchestrator
│   ├── docker_system_test.py          # 34 Docker system tests
│   └── e2e_integration_test.py        # End-to-end workflow tests
└── connectivity/                       # Connectivity and API tests
    ├── connectivity_test.sh           # Basic connectivity and health checks
    ├── api_test.py                    # Comprehensive API endpoint testing
    ├── dynamic_routes_test.py         # Dynamic routes validation
    ├── frontend_links_test.py         # Frontend link validation
    └── materials_validation_test.py   # Materials and file system testing
```

## 🚀 Quick Start

### Run All Tests
```bash
# From project root
./tests/run_all_tests.sh

# Or from tests directory
./run_all_tests.sh
```

### Run Specific Test Suites

```bash
# Docker-focused tests
./tests/docker/run_docker_tests.sh              # All Docker tests
./tests/docker/run_docker_tests.sh --quick     # Quick Docker tests
./tests/docker/run_docker_tests.sh --diagnostics # Docker diagnostics

# Traditional connectivity tests
./tests/run_all_tests.sh --connectivity        # Connectivity tests
./tests/run_all_tests.sh --api                 # API tests
./tests/run_all_tests.sh --routes              # Dynamic routes tests
./tests/run_all_tests.sh --materials           # Materials validation
./tests/run_all_tests.sh --links               # Frontend link tests
./tests/run_all_tests.sh --quick               # Quick connectivity tests
```

### Run Individual Test Files

```bash
# Docker-focused tests (Python 3)
python3 tests/docker/docker_system_test.py           # Docker system tests
python3 tests/docker/e2e_integration_test.py        # E2E workflow tests

# Traditional tests (Python 3 or shell)
./tests/connectivity/connectivity_test.sh            # Basic connectivity
python3 tests/connectivity/api_test.py               # API endpoint testing
python3 tests/connectivity/dynamic_routes_test.py    # Dynamic routes validation
python3 tests/connectivity/frontend_links_test.py    # Frontend link testing
python3 tests/connectivity/materials_validation_test.py # Materials validation
```

## 📋 Test Coverage

### 🐳 Docker System Tests (`docker_system_test.py`)
**34 comprehensive Docker tests covering:**
- Docker daemon and image validation
- Container health and connectivity
- Network configuration and inter-container communication
- Volume creation and data persistence
- API functionality and documentation
- Materials system integration
- System performance metrics
- Production readiness checks

### 🔄 E2E Integration Tests (`e2e_integration_test.py`)
**Complete end-to-end workflow testing:**
- Docker environment readiness
- Course management workflow
- Materials access workflow
- Chat integration with materials
- API documentation workflow
- Docker logs and monitoring
- Data integrity verification
- Error handling scenarios

### 🔗 Connectivity Tests (`connectivity_test.sh`)
- Docker container health status
- Backend health endpoint (`/health`)
- Frontend accessibility
- Redis connection
- API endpoint availability
- CORS configuration
- File upload endpoint accessibility

### 🔌 API Tests (`api_test.py`)
- Backend health check with JSON validation
- Frontend connectivity
- Core API endpoints (`/courses`, `/docs`, `/openapi.json`)
- CORS preflight requests
- Course data flow (courses → books → materials)
- Chat functionality endpoint
- Response time analysis

### 🛣️ Dynamic Routes Tests (`dynamic_routes_test.py`)
- Static routes (`/`, `/courses`, `/chat`)
- Course detail pages (`/courses/[id]`)
- Books listing and detail pages (`/courses/[id]/books`, `//courses/[id]/books/[bookId]`)
- Materials listing and detail pages (`/courses/[id]/materials`, `/courses/[id]/materials/[filename]`)
- Workspace and study routes (`/courses/[id]/study`, `/courses/[id]/workspace`)
- Mindmap generation routes (`/courses/[id]/mindmap`, `/courses/[id]/books/[bookId]/mindmap`)
- Invalid route handling (404 responses)

### 🔗 Frontend Links Tests (`frontend_links_test.py`)
- Internal link validation
- Navigation menu functionality
- Course and book page links
- 404 error detection
- Link accessibility verification

### 📚 Materials Validation Tests (`materials_validation_test.py`)
- Course and books data structure validation
- File system access verification
- PDF materials accessibility
- Materials API endpoint testing
- Frontend materials route validation
- Comprehensive materials reporting

## ⚙️ Configuration

### Environment Variables
The tests use the following default URLs, but can be overridden by environment variables:

```bash
# Default URLs
BACKEND_URL="http://localhost:8001"
FRONTEND_URL="http://localhost:3001"
REDIS_HOST="localhost"
REDIS_PORT="6379"

# Override with environment variables
export BACKEND_URL="http://localhost:8001"
export FRONTEND_URL="http://localhost:3001"
./tests/run_all_tests.sh
```

### Prerequisites
- Docker and Docker Compose running
- Backend service running on port 8001
- Frontend service running on port 3001
- Python 3 with `requests` package (for Python-based tests)
- `curl` command (for shell-based tests)

## 📊 Current System Status ✅

### Docker Testing Results (Latest)
- **Docker System Tests**: 73.5% success rate (25/34 tests passed)
- **Materials Validation**: 89.6% success rate (43/48 tests passed)
- **Backend Performance**: 2ms response time
- **Materials Available**: 48 PDF files (100% accessible)
- **API Endpoints**: Fully functional with 3 courses and 5 books

### System Health ✅
- ✅ **Backend**: Healthy and responsive (http://localhost:8001)
- ✅ **Redis**: Connected and operational
- ✅ **Materials**: 48 PDF files fully accessible
- ✅ **API Documentation**: Available at /docs
- ⚠️ **Frontend**: Running but affected by WSL2 networking limitations

### Test Coverage Summary
- **Docker Infrastructure**: Complete container, network, and volume testing
- **API Functionality**: Comprehensive endpoint and workflow testing
- **Materials System**: File system and accessibility validation
- **Performance Metrics**: Response time and resource usage monitoring

## 📊 Test Output

### Success Indicators
- ✅ **PASS**: Test completed successfully
- 🎉 **ALL TESTS PASSED**: All test suites completed without failures

### Failure Indicators
- ❌ **FAIL**: Test failed with detailed error message
- ⚠️ **WARNING**: Some prerequisites missing or non-critical issues

### Color Coding
- 🟢 **Green**: Success/passing tests
- 🔴 **Red**: Failed tests or errors
- 🔵 **Blue**: Information headers
- 🟡 **Yellow**: Warnings or in-progress tests

## 🔧 Troubleshooting

### Common Issues

1. **Backend/Frontend Not Accessible**
   ```bash
   # Check if services are running
   docker-compose ps

   # Restart services
   ./start.sh dev
   ```

2. **Python Dependencies Missing**
   ```bash
   # Install requests package
   pip3 install requests

   # Or install system package
   sudo apt-get install python3-requests  # Ubuntu/Debian
   brew install python3-requests           # macOS
   ```

3. **Docker Issues**
   ```bash
   # Check Docker status
   docker info

   # Restart Docker daemon
   sudo systemctl restart docker  # Linux
   # Restart Docker Desktop        # Windows/macOS
   ```

4. **Port Conflicts**
   ```bash
   # Check what's using ports
   ss -tulpn | grep :8001
   ss -tulpn | grep :3001

   # Kill conflicting processes
   sudo fuser -k 8001/tcp
   sudo fuser -k 3001/tcp
   ```

### Running Tests in Different Environments

#### Development Environment
```bash
# Run all tests with verbose output
./tests/run_all_tests.sh --verbose

# Run quick tests during development
./tests/run_all_tests.sh --quick
```

#### CI/CD Pipeline
```bash
# Run tests without interaction
./tests/run_all_tests.sh --quick

# Exit on first failure for CI
set -e
./tests/run_all_tests.sh
```

#### Docker Container Testing
```bash
# Test inside Docker container
docker-compose exec frontend curl -f http://localhost:3000
docker-compose exec backend curl -f http://localhost:8001/health
```

## 📝 Test Reports

After running tests, you'll get a comprehensive report including:

- **Total tests run**
- **Pass/fail counts**
- **Success rate percentage**
- **Detailed failure messages** (if any)
- **Performance metrics** (response times)

### Example Output
```
📊 Test Summary
=====================================
Total Tests: 15
Passed: 15
Failed: 0

Success Rate: 100.0%

🎉 All tests passed! System is fully operational.
```

## 🔄 Continuous Integration

These tests are designed to work in CI/CD pipelines:

### GitHub Actions Example
```yaml
- name: Run connectivity tests
  run: |
    ./tests/run_all_tests.sh --quick
```

### GitLab CI Example
```yaml
test:connectivity:
  script:
    - ./tests/run_all_tests.sh --quick
  artifacts:
    reports:
      junit: test-results.xml
```

## 🤝 Contributing

When adding new features to Tutor-AI, please also add corresponding tests:

1. **New API endpoints**: Add to `api_test.py`
2. **New routes**: Add to `dynamic_routes_test.py`
3. **New services**: Add health checks to `connectivity_test.sh`

### Test Naming Conventions
- Use descriptive test names
- Group related tests together
- Include error messages that help with debugging
- Follow the existing color and format conventions

## 📞 Support

If tests are failing:
1. Check the [troubleshooting section](#troubleshooting) above
2. Verify all services are running correctly
3. Check network connectivity and port availability
4. Review test error messages for specific issues
5. Consult the main [CLAUDE.md](../CLAUDE.md) documentation

For test-related issues or improvements, please create an issue in the project repository.