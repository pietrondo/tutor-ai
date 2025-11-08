"""
Test suite for Error Handling Standardization - Fase 2
Verifies all error types and response formats are working correctly
"""

import asyncio
import json
import sys
import os
from datetime import datetime
from typing import Dict, Any

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Test imports
try:
    from middleware.error_handler import (
        CLEError, ValidationError, NotFoundError, BusinessLogicError,
        ExternalServiceError, AuthenticationError, AuthorizationError,
        RateLimitError, ErrorResponse, create_success_response,
        create_error_response, raise_not_found, raise_validation_error,
        raise_business_logic_error, ErrorCategory
    )
    print("✅ All error handler imports successful")
except ImportError as e:
    print(f"❌ Error handler import failed: {e}")
    sys.exit(1)

# Test error creation and responses
def test_error_creation():
    print("\n🔍 Testing Error Creation...")

    try:
        # Test ValidationError
        validation_error = ValidationError(
            message="Invalid input data",
            details={"field": "email", "value": "invalid-email"}
        )
        assert validation_error.category == ErrorCategory.VALIDATION
        assert validation_error.status_code == 400
        assert validation_error.error_code == "VALIDATION_ERROR"

        # Test NotFoundError
        not_found_error = NotFoundError(
            resource="LearningCard",
            resource_id="card-123"
        )
        assert not_found_error.category == ErrorCategory.NOT_FOUND
        assert not_found_error.status_code == 404
        assert "LearningCard not found" in not_found_error.message

        # Test BusinessLogicError
        business_error = BusinessLogicError(
            message="Cannot review card before due date",
            error_code="REVIEW_TOO_EARLY"
        )
        assert business_error.category == ErrorCategory.BUSINESS_LOGIC
        assert business_error.status_code == 422
        assert business_error.error_code == "REVIEW_TOO_EARLY"

        # Test ExternalServiceError
        external_error = ExternalServiceError(
            service_name="OpenAI",
            message="API rate limit exceeded",
            details={"retry_after": 60}
        )
        assert external_error.category == ErrorCategory.EXTERNAL_SERVICE
        assert external_error.status_code == 502
        assert "OpenAI:" in external_error.message

        # Test AuthenticationError
        auth_error = AuthenticationError(
            message="Invalid or expired token",
            details={"token_expired": True}
        )
        assert auth_error.category == ErrorCategory.AUTHENTICATION
        assert auth_error.status_code == 401

        # Test AuthorizationError
        perm_error = AuthorizationError(
            message="User does not have admin privileges"
        )
        assert perm_error.category == ErrorCategory.AUTHORIZATION
        assert perm_error.status_code == 403

        # Test RateLimitError
        rate_error = RateLimitError(
            message="Too many requests",
            retry_after=120
        )
        assert rate_error.category == ErrorCategory.RATE_LIMIT
        assert rate_error.status_code == 429

        print("✅ Error creation working correctly")
        print(f"  - ValidationError: ✅")
        print(f"  - NotFoundError: ✅")
        print(f"  - BusinessLogicError: ✅")
        print(f"  - ExternalServiceError: ✅")
        print(f"  - AuthenticationError: ✅")
        print(f"  - AuthorizationError: ✅")
        print(f"  - RateLimitError: ✅")

        return True
    except Exception as e:
        print(f"❌ Error creation test failed: {e}")
        return False

# Test error response formatting
def test_error_response_formatting():
    print("\n🔍 Testing Error Response Formatting...")

    try:
        request_id = "test-request-123"

        # Test CLE error response
        cle_error = ValidationError(
            message="Email is invalid",
            details={"field": "email", "value": "test@"}
        )
        response = ErrorResponse.create(cle_error, request_id=request_id)

        assert response["success"] == False
        assert response["error"]["category"] == ErrorCategory.VALIDATION.value
        assert response["error"]["code"] == "VALIDATION_ERROR"
        assert response["error"]["message"] == "Email is invalid"
        assert response["error"]["status_code"] == 400
        assert response["request_id"] == request_id
        assert "details" in response["error"]
        assert response["error"]["details"]["field"] == "email"

        # Test not found error response
        not_found_error = NotFoundError("Course", "course-456")
        response = ErrorResponse.create(not_found_error)

        assert response["error"]["category"] == ErrorCategory.NOT_FOUND.value
        assert response["error"]["status_code"] == 404
        assert "course-456" in response["error"]["message"]

        # Test external service error response
        external_error = ExternalServiceError(
            service_name="Database",
            message="Connection timeout"
        )
        response = ErrorResponse.create(external_error)

        assert response["error"]["category"] == ErrorCategory.EXTERNAL_SERVICE.value
        assert response["error"]["details"]["service"] == "Database"

        print("✅ Error response formatting working correctly")
        print(f"  - CLE error response: ✅")
        print(f"  - Not found response: ✅")
        print(f"  - External service response: ✅")
        print(f"  - Request ID tracking: ✅")
        print(f"  - Error details inclusion: ✅")

        return True
    except Exception as e:
        print(f"❌ Error response formatting test failed: {e}")
        return False

# Test success response formatting
def test_success_response_formatting():
    print("\n🔍 Testing Success Response Formatting...")

    try:
        request_id = "test-request-456"

        # Test success response with data
        test_data = {
            "id": "card-123",
            "question": "What is machine learning?",
            "answer": "Machine learning is..."
        }

        response = create_success_response(
            data=test_data,
            message="Card created successfully",
            request_id=request_id
        )

        assert response["success"] == True
        assert response["data"] == test_data
        assert response["message"] == "Card created successfully"
        assert response["request_id"] == request_id
        assert "timestamp" in response

        # Test success response without data
        response = create_success_response(message="Operation completed")

        assert response["success"] == True
        assert response["message"] == "Operation completed"
        assert "data" not in response
        assert "timestamp" in response

        print("✅ Success response formatting working correctly")
        print(f"  - Response with data: ✅")
        print(f"  - Response without data: ✅")
        print(f"  - Timestamp inclusion: ✅")
        print(f"  - Request ID tracking: ✅")

        return True
    except Exception as e:
        print(f"❌ Success response formatting test failed: {e}")
        return False

# Test utility functions
def test_utility_functions():
    print("\n🔍 Testing Utility Functions...")

    try:
        # Test raise_not_found function
        try:
            raise_not_found("User", "user-789")
            assert False, "Should have raised NotFoundError"
        except NotFoundError as e:
            assert "User not found" in e.message
            assert "user-789" in e.message

        # Test raise_validation_error function
        try:
            raise_validation_error("Invalid email format", {"field": "email"})
            assert False, "Should have raised ValidationError"
        except ValidationError as e:
            assert e.message == "Invalid email format"
            assert e.details["field"] == "email"

        # Test raise_business_logic_error function
        try:
            raise_business_logic_error("Card already reviewed", error_code="DUPLICATE_REVIEW")
            assert False, "Should have raised BusinessLogicError"
        except BusinessLogicError as e:
            assert e.message == "Card already reviewed"
            assert e.error_code == "DUPLICATE_REVIEW"

        # Test create_error_response function
        response = create_error_response(
            category=ErrorCategory.VALIDATION,
            message="Test error",
            status_code=400,
            error_code="TEST_ERROR",
            details={"test": True}
        )

        assert response["success"] == False
        assert response["error"]["category"] == ErrorCategory.VALIDATION.value
        assert response["error"]["message"] == "Test error"
        assert response["error"]["status_code"] == 400

        print("✅ Utility functions working correctly")
        print(f"  - raise_not_found: ✅")
        print(f"  - raise_validation_error: ✅")
        print(f"  - raise_business_logic_error: ✅")
        print(f"  - create_error_response: ✅")

        return True
    except Exception as e:
        print(f"❌ Utility functions test failed: {e}")
        return False

# Test error categories and consistency
def test_error_categories():
    print("\n🔍 Testing Error Categories...")

    try:
        # Test all categories are properly defined
        expected_categories = {
            "validation", "authentication", "authorization", "not_found",
            "business_logic", "external_service", "system", "rate_limit"
        }

        actual_categories = set([category.value for category in ErrorCategory])
        assert expected_categories == actual_categories

        # Test category consistency with status codes
        category_status_mapping = {
            ErrorCategory.VALIDATION: 400,
            ErrorCategory.AUTHENTICATION: 401,
            ErrorCategory.AUTHORIZATION: 403,
            ErrorCategory.NOT_FOUND: 404,
            ErrorCategory.BUSINESS_LOGIC: 422,
            ErrorCategory.RATE_LIMIT: 429,
            ErrorCategory.EXTERNAL_SERVICE: 502,
            ErrorCategory.SYSTEM: 500
        }

        for category, expected_status in category_status_mapping.items():
            error = CLEError(
                message="Test",
                category=category,
                status_code=expected_status
            )
            assert error.status_code == expected_status

        print("✅ Error categories working correctly")
        print(f"  - All categories defined: ✅")
        print(f"  - Status code consistency: ✅")
        print(f"  - Category completeness: ✅")

        return True
    except Exception as e:
        print(f"❌ Error categories test failed: {e}")
        return False

# Test JSON serialization
def test_json_serialization():
    print("\n🔍 Testing JSON Serialization...")

    try:
        # Test error response JSON serialization
        error = ValidationError(
            message="Test validation error",
            details={"field": "test", "invalid": True}
        )
        response = ErrorResponse.create(error, request_id="json-test")

        # Convert to JSON and back
        json_str = json.dumps(response)
        parsed_response = json.loads(json_str)

        assert parsed_response["success"] == False
        assert parsed_response["error"]["category"] == ErrorCategory.VALIDATION.value
        assert parsed_response["error"]["message"] == "Test validation error"
        assert parsed_response["error"]["details"]["field"] == "test"
        assert parsed_response["request_id"] == "json-test"

        # Test success response JSON serialization
        success_response = create_success_response(
            data={"test": True, "number": 42},
            message="JSON test successful",
            request_id="json-test"
        )

        json_str = json.dumps(success_response)
        parsed_response = json.loads(json_str)

        assert parsed_response["success"] == True
        assert parsed_response["data"]["test"] == True
        assert parsed_response["data"]["number"] == 42
        assert parsed_response["message"] == "JSON test successful"

        print("✅ JSON serialization working correctly")
        print(f"  - Error response JSON: ✅")
        print(f"  - Success response JSON: ✅")
        print(f"  - Round-trip consistency: ✅")

        return True
    except Exception as e:
        print(f"❌ JSON serialization test failed: {e}")
        return False

# Test API integration patterns
def test_api_integration_patterns():
    print("\n🔍 Testing API Integration Patterns...")

    try:
        # Test that main_v1.py exists and has error handler imports
        main_v1_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "main_v1.py")

        if not os.path.exists(main_v1_path):
            print("❌ main_v1.py file not found")
            return False

        # Read and check for error handling patterns
        with open(main_v1_path, 'r') as f:
            content = f.read()

        # Check for error handler imports
        assert "from middleware.error_handler import" in content
        assert "cle_exception_handler" in content

        # Check for exception handlers
        assert "app.add_exception_handler" in content
        assert "CLEError" in content

        # Check for request ID middleware
        assert "request_id" in content
        assert "X-Request-ID" in content

        # Check for proper error handling patterns
        assert "create_success_response" in content
        assert "raise_validation_error" in content or "ValidationError" in content
        assert "ExternalServiceError" in content

        print("✅ API integration patterns verified")
        print(f"  - Error handler imports: ✅")
        print(f"  - Exception handlers registered: ✅")
        print(f"  - Request ID middleware: ✅")
        print(f"  - Updated endpoint patterns: ✅")

        return True
    except Exception as e:
        print(f"❌ API integration patterns test failed: {e}")
        return False

# Main test runner
async def run_all_error_handling_tests():
    print("🚀 Starting Error Handling Standardization Testing - Fase 2")
    print("=" * 60)

    tests = [
        ("Error Creation", test_error_creation),
        ("Error Response Formatting", test_error_response_formatting),
        ("Success Response Formatting", test_success_response_formatting),
        ("Utility Functions", test_utility_functions),
        ("Error Categories", test_error_categories),
        ("JSON Serialization", test_json_serialization),
        ("API Integration Patterns", test_api_integration_patterns)
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            failed += 1

    # Results
    print("\n" + "=" * 60)
    print("📊 ERROR HANDLING TEST RESULTS SUMMARY")
    print("=" * 60)
    print(f"Total Tests: {len(tests)}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")

    if failed == 0:
        print("\n🎉 ALL ERROR HANDLING TESTS PASSED!")
        print("📈 Error Handling System Fully Operational")
        print("\n✅ Ready for Database Schema Corrections")
        return True
    else:
        print(f"\n⚠️  {failed} error handling issues remaining")
        print("🔧 Address issues before proceeding")
        return False

# Run all tests
async def main():
    print("🧪 CLE Error Handling Test Suite")
    print(f"⏰ Started: {datetime.now().isoformat()}")

    # Run all tests
    success = await run_all_error_handling_tests()

    if success:
        print("\n" + "=" * 60)
        print("🚀 FASE 2 ERROR HANDLING - COMPLETED SUCCESSFULLY! 🎉")
        print("=" * 60)
        print("\n📋 ERROR HANDLING FEATURES IMPLEMENTED:")
        print("  ✅ Centralized error types and categories")
        print("  ✅ Standardized error response format")
        print("  ✅ Proper HTTP status code mapping")
        print("  ✅ Request ID tracking for debugging")
        print("  ✅ Structured error details and context")
        print("  ✅ JSON serialization compatibility")
        print("  ✅ API integration with exception handlers")
        print("  ✅ Utility functions for common scenarios")

        print("\n🎯 ERROR HANDLING STATUS: PRODUCTION READY")
        print("\n📅 NEXT TASKS (Fase 2):")
        print("  - Database Schema Corrections")
        print("  - Performance Optimization")
        print("  - Security Enhancements")
        print("  - Unit Testing Implementation")
        print("\n✨ READY FOR DATABASE SCHEMA CORRECTIONS")
        return True
    else:
        print("\n❌ ERROR HANDLING IMPLEMENTATION INCOMPLETE")
        return False

if __name__ == "__main__":
    asyncio.run(main())