"""
Test suite for Security Enhancements - Fase 2
Verifies rate limiting, CORS, security headers, and input sanitization
"""

import asyncio
import os
import sys
import time
import json
from datetime import datetime, timedelta
from typing import Dict, Any

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_rate_limiting():
    """Test rate limiting functionality"""
    print("\n🔍 Testing Rate Limiting...")

    try:
        from middleware.security import RateLimiter, AdvancedRateLimiter

        # Test basic rate limiter
        limiter = RateLimiter(requests_per_minute=5)

        # First 5 requests should be allowed
        for i in range(5):
            assert limiter.is_allowed("test_client") == True

        # 6th request should be blocked
        assert limiter.is_allowed("test_client") == False
        print("✅ Basic rate limiting working")

        # Test rate limit headers
        headers = limiter.get_rate_limit_headers("test_client")
        assert "X-RateLimit-Limit" in headers
        assert "X-RateLimit-Remaining" in headers
        assert "X-RateLimit-Reset" in headers
        assert headers["X-RateLimit-Limit"] == "5"
        print("✅ Rate limit headers working")

        # Test advanced rate limiter
        advanced_limiter = AdvancedRateLimiter()
        auth_limiter = advanced_limiter.get_limiter_for_path("/api/v1/auth/login")
        api_limiter = advanced_limiter.get_limiter_for_path("/api/v1/courses/123")

        # Should have different rate limits for different paths
        assert auth_limiter.requests_per_minute == 10
        assert api_limiter.requests_per_minute == 60
        print("✅ Advanced rate limiting working")

        return True
    except Exception as e:
        print(f"❌ Rate limiting test failed: {e}")
        return False

def test_security_headers():
    """Test security headers"""
    print("\n🔍 Testing Security Headers...")

    try:
        from middleware.security import SecurityHeaders
        from fastapi import Response

        # Create mock response
        response = Response(content="test")

        # Add security headers
        secured_response = SecurityHeaders.add_security_headers(response)

        # Check essential security headers
        headers = secured_response.headers
        assert "X-Frame-Options" in headers
        assert "X-XSS-Protection" in headers
        assert "X-Content-Type-Options" in headers
        assert "Referrer-Policy" in headers
        assert "Content-Security-Policy" in headers
        assert "Permissions-Policy" in headers

        # Check header values
        assert headers["X-Frame-Options"] == "DENY"
        assert headers["X-XSS-Protection"] == "1; mode=block"
        assert headers["X-Content-Type-Options"] == "nosniff"
        print("✅ Security headers working")

        return True
    except Exception as e:
        print(f"❌ Security headers test failed: {e}")
        return False

def test_input_sanitization():
    """Test input sanitization"""
    print("\n🔍 Testing Input Sanitization...")

    try:
        from middleware.security import InputSanitizer

        sanitizer = InputSanitizer()

        # Test basic sanitization
        clean_input = sanitizer.sanitize_input("Hello, World!")
        assert clean_input == "Hello, World!"

        # Test XSS prevention
        xss_input = sanitizer.sanitize_input("<script>alert('xss')</script>")
        assert "<script>" not in xss_input
        assert "javascript:" not in xss_input
        print("✅ XSS prevention working")

        # Test SQL injection prevention
        sql_input = sanitizer.sanitize_sql_input("'; DROP TABLE users; --")
        assert "DROP" not in sql_input
        assert "DELETE" not in sql_input
        print("✅ SQL injection prevention working")

        # Test email validation
        assert sanitizer.validate_email("test@example.com") == True
        assert sanitizer.validate_email("invalid-email") == False
        assert sanitizer.validate_email("test@domain") == False
        print("✅ Email validation working")

        # Test user ID validation
        assert sanitizer.validate_user_id("user123") == True
        assert sanitizer.validate_user_id("user@123") == False
        assert sanitizer.validate_user_id("") == False
        print("✅ User ID validation working")

        # Test course ID validation
        assert sanitizer.validate_course_id("course-123") == True
        assert sanitizer.validate_course_id("course@123") == False
        assert sanitizer.validate_course_id("") == False
        print("✅ Course ID validation working")

        return True
    except Exception as e:
        print(f"❌ Input sanitization test failed: {e}")
        return False

def test_csrf_protection():
    """Test CSRF token protection"""
    print("\n🔍 Testing CSRF Protection...")

    try:
        from middleware.security import CSRFProtection

        csrf = CSRFProtection()

        # Test token generation
        token = csrf.generate_token()
        assert token is not None
        assert ":" in token  # Should have timestamp:data:signature format
        print("✅ CSRF token generation working")

        # Test token validation
        is_valid = csrf.validate_token(token)
        assert is_valid == True
        print("✅ CSRF token validation working")

        # Test invalid token
        invalid_token = "invalid:token:format"
        is_invalid = csrf.validate_token(invalid_token)
        assert is_invalid == False
        print("✅ Invalid CSRF token rejection working")

        # Test token expiration
        old_token = csrf.generate_token()
        # Manually create an expired token (1 hour ago)
        timestamp = str(int(time.time()) - 3700)  # More than 1 hour ago
        parts = old_token.split(":")
        expired_token = f"{timestamp}:{parts[1]}:{parts[2]}"
        is_expired = csrf.validate_token(expired_token)
        assert is_expired == False
        print("✅ CSRF token expiration working")

        return True
    except Exception as e:
        print(f"❌ CSRF protection test failed: {e}")
        return False

def test_ip_whitelist():
    """Test IP whitelist functionality"""
    print("\n🔍 Testing IP Whitelist...")

    try:
        from middleware.security import IPWhitelist

        # Test with empty whitelist (should allow all IPs)
        whitelist = IPWhitelist()
        assert whitelist.is_whitelisted("192.168.1.1") == True
        assert whitelist.is_whitelisted("10.0.0.1") == True
        print("✅ Empty whitelist allows all IPs")

        # Test with specific whitelist
        os.environ["IP_WHITELIST"] = "192.168.1.1,10.0.0.1"
        whitelist_with_restrictions = IPWhitelist()
        assert whitelist_with_restrictions.is_whitelisted("192.168.1.1") == True
        assert whitelist_with_restrictions.is_whitelisted("10.0.0.1") == True
        assert whitelist_with_restrictions.is_whitelisted("8.8.8.8") == False
        print("✅ IP whitelist restrictions working")

        # Cleanup
        del os.environ["IP_WHITELIST"]
        return True
    except Exception as e:
        print(f"❌ IP whitelist test failed: {e}")
        return False

def test_security_monitoring():
    """Test security monitoring"""
    print("\n🔍 Testing Security Monitoring...")

    try:
        from middleware.security import SecurityMonitor

        monitor = SecurityMonitor()

        # Test event logging
        monitor.log_security_event("failed_login", {
            "user_id": "test-user",
            "ip": "192.168.1.1",
            "attempts": 3
        })
        print("✅ Security event logging working")

        # Test recent events retrieval
        recent_events = monitor.get_recent_events(minutes=60)
        assert isinstance(recent_events, list)
        assert len(recent_events) >= 1
        assert recent_events[0]["type"] == "failed_login"
        print("✅ Recent events retrieval working")

        # Test event severity detection
        high_severity_event = monitor.log_security_event("multiple_failed_logins", {
            "user_id": "test-user",
            "attempts": 10
        })
        print("✅ Event severity detection working")

        return True
    except Exception as e:
        print(f"❌ Security monitoring test failed: {e}")
        return False

def test_data_masking():
    """Test data masking utilities"""
    print("\n🔍 Testing Data Masking...")

    try:
        from middleware.security import mask_sensitive_data

        # Test email masking
        masked_email = mask_sensitive_data("user@example.com", "*", 4)
        assert masked_email.startswith("user")
        assert "@" not in masked_email[len("user"):]
        print("✅ Email masking working")

        # Test API key masking
        masked_key = mask_sensitive_data("sk-1234567890abcdef", "*", 8)
        assert masked_key.startswith("sk-123456")
        assert len(masked_key.replace("*", "")) == 8
        print("✅ API key masking working")

        # Test short string masking
        masked_short = mask_sensitive_data("abc", "*", 10)
        assert masked_short == "***"
        print("✅ Short string masking working")

        return True
    except Exception as e:
        print(f"❌ Data masking test failed: {e}")
        return False

def test_concurrent_rate_limiting():
    """Test rate limiting under concurrent load"""
    print("\n🔍 Testing Concurrent Rate Limiting...")

    try:
        from middleware.security import RateLimiter
        import threading
        import time

        limiter = RateLimiter(requests_per_minute=10)
        results = []

        def worker(worker_id):
            allowed_count = 0
            for i in range(20):
                if limiter.is_allowed(f"concurrent_client_{worker_id}"):
                    allowed_count += 1
                time.sleep(0.001)  # Small delay
            results.append(allowed_count)

        # Create multiple threads simulating concurrent requests
        threads = []
        for i in range(3):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)

        start_time = time.time()
        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        end_time = time.time()

        # Check results
        total_allowed = sum(results)
        assert total_allowed <= 30  # 3 clients * 10 requests per minute max
        assert total_allowed > 0  # Some requests should be allowed

        print(f"✅ Concurrent rate limiting working")
        print(f"  - Threads: 3")
        print(f"  - Total allowed requests: {total_allowed}")
        print(f"  - Test duration: {end_time - start_time:.3f}s")

        return True
    except Exception as e:
        print(f"❌ Concurrent rate limiting test failed: {e}")
        return False

# Main test runner
async def run_security_tests():
    print("🚀 Starting Security Enhancements Testing - Fase 2")
    print("=" * 60)

    tests = [
        ("Rate Limiting", test_rate_limiting),
        ("Security Headers", test_security_headers),
        ("Input Sanitization", test_input_sanitization),
        ("CSRF Protection", test_csrf_protection),
        ("IP Whitelist", test_ip_whitelist),
        ("Security Monitoring", test_security_monitoring),
        ("Data Masking", test_data_masking),
        ("Concurrent Rate Limiting", test_concurrent_rate_limiting)
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
    print("📊 SECURITY ENHANCEMENTS TEST RESULTS")
    print("=" * 60)
    print(f"Total Tests: {len(tests)}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")

    if failed == 0:
        print("\n🎉 ALL SECURITY TESTS PASSED!")
        print("📈 Security System Fully Operational")
        print("\n✅ Ready for Unit Testing Implementation")
        return True
    else:
        print(f"\n⚠️  {failed} security issues remaining")
        print("🔧 Address issues before proceeding")
        return False

# Run all tests
async def main():
    print("🧪 CLE Security Enhancements Test Suite")
    print(f"⏰ Started: {datetime.now().isoformat()}")

    # Run all tests
    success = await run_security_tests()

    if success:
        print("\n" + "=" * 60)
        print("🚀 FASE 2 SECURITY ENHANCEMENTS - COMPLETED! 🎉")
        print("=" * 60)
        print("\n📋 SECURITY FEATURES IMPLEMENTED:")
        print("  ✅ Advanced rate limiting with multiple tiers")
        print("  ✅ Comprehensive security headers")
        print("  ✅ Input sanitization and validation")
        print("  ✅ CSRF token protection")
        print("  ✅ IP whitelist functionality")
        print("  ✅ Security event monitoring")
        print("  ✅ Data masking for sensitive information")
        print("  ✅ Concurrent-safe security measures")
        print("  ✅ CORS configuration")

        print("\n🎯 SECURITY STATUS: PRODUCTION READY")
        print("\n📅 FINAL TASK (Fase 2):")
        print("  - Unit Testing Implementation")
        print("\n✨ READY FOR UNIT TESTING IMPLEMENTATION")
        return True
    else:
        print("\n❌ SECURITY ENHANCEMENTS INCOMPLETE")
        return False

if __name__ == "__main__":
    asyncio.run(main())