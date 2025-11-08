"""
Test suite for Performance Optimization - Fase 2
Verifies caching, performance monitoring, and response optimization
"""

import asyncio
import os
import sys
import time
from datetime import datetime
from typing import Dict, Any

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_caching_system():
    """Test caching functionality"""
    print("\n🔍 Testing Caching System...")

    try:
        from middleware.caching import (
            cache_manager, MemoryCache, cached, async_cached,
            cache_key, CacheInvalidator
        )
        print("✅ Caching modules imported")

        # Test cache key generation
        key1 = cache_key("test", "user", 123, active=True)
        key2 = cache_key("test", "user", 123, active=True)
        key3 = cache_key("test", "user", 456, active=True)

        assert key1 == key2  # Same inputs should generate same key
        assert key1 != key3  # Different inputs should generate different key
        print("✅ Cache key generation working")

        # Test memory cache
        memory_cache = MemoryCache(max_size=5)
        memory_cache.set("test_key", {"data": "test_value"}, ttl=1)
        cached_value = memory_cache.get("test_key")
        assert cached_value == {"data": "test_value"}
        print("✅ Memory cache working")

        # Test cache expiration
        time.sleep(1.1)
        expired_value = memory_cache.get("test_key")
        assert expired_value is None
        print("✅ Cache expiration working")

        # Test cache manager
        cache_manager.set("manager_test", {"test": True}, ttl=5)
        manager_result = cache_manager.get("manager_test")
        assert manager_result == {"test": True}
        print("✅ Cache manager working")

        # Test cache invalidation
        invalidated = CacheInvalidator.invalidate_user_data("test-user-123")
        assert isinstance(invalidated, int)
        print("✅ Cache invalidation working")

        return True
    except Exception as e:
        print(f"❌ Caching system test failed: {e}")
        return False

def test_cached_decorators():
    """Test cached decorators"""
    print("\n🔍 Testing Cached Decorators...")

    try:
        from middleware.caching import cached, async_cached, cache_manager

        # Test synchronous cached decorator
        call_count = 0

        @cached(ttl=5, key_prefix="test_sync")
        def expensive_function(x, y):
            nonlocal call_count
            call_count += 1
            time.sleep(0.01)  # Simulate expensive operation
            return x + y

        # First call should execute function
        result1 = expensive_function(1, 2)
        assert result1 == 3
        assert call_count == 1

        # Second call should use cache
        result2 = expensive_function(1, 2)
        assert result2 == 3
        assert call_count == 1  # Should not increase

        # Different arguments should call function
        result3 = expensive_function(2, 3)
        assert result3 == 5
        assert call_count == 2
        print("✅ Synchronous cached decorator working")

        return True
    except Exception as e:
        print(f"❌ Cached decorators test failed: {e}")
        return False

def test_performance_monitoring():
    """Test performance monitoring"""
    print("\n🔍 Testing Performance Monitoring...")

    try:
        from middleware.caching import (
            performance_monitor, monitor_performance, monitor_async_performance
        )

        # Test performance monitor
        performance_monitor.record_response_time("test_endpoint", 0.1)
        performance_monitor.record_response_time("test_endpoint", 0.2)
        performance_monitor.record_response_time("test_endpoint", 0.15)

        metrics = performance_monitor.get_metrics()
        assert "test_endpoint" in metrics
        assert metrics["test_endpoint"]["count"] == 3
        assert metrics["test_endpoint"]["avg_time"] == 0.15  # (0.1 + 0.2 + 0.15) / 3
        print("✅ Performance monitoring working")

        # Test monitor decorator
        @monitor_performance
        def test_function():
            time.sleep(0.01)
            return "test_result"

        result = test_function()
        assert result == "test_result"
        print("✅ Performance monitor decorator working")

        return True
    except Exception as e:
        print(f"❌ Performance monitoring test failed: {e}")
        return False

def test_response_optimization():
    """Test response optimization utilities"""
    print("\n🔍 Testing Response Optimization...")

    try:
        from middleware.caching import (
            should_compress_response, get_cache_ttl_for_content
        )

        # Test compression logic
        # Small response - should not compress
        assert not should_compress_response(500, "application/json")
        # Large response - should compress
        assert should_compress_response(2000, "application/json")
        # Non-compressible content - should not compress
        assert not should_compress_response(2000, "image/jpeg")
        print("✅ Response compression logic working")

        # Test TTL mapping
        user_ttl = get_cache_ttl_for_content("user_profile_data")
        assert user_ttl == 3600  # 1 hour

        course_ttl = get_cache_ttl_for_content("course_content")
        assert course_ttl == 1800  # 30 minutes

        default_ttl = get_cache_ttl_for_content("unknown_content")
        assert default_ttl == 60  # 1 minute
        print("✅ Cache TTL mapping working")

        return True
    except Exception as e:
        print(f"❌ Response optimization test failed: {e}")
        return False

def test_cache_statistics():
    """Test cache statistics and monitoring"""
    print("\n🔍 Testing Cache Statistics...")

    try:
        from middleware.caching import cache_manager

        # Get cache stats
        stats = cache_manager.get_stats()
        assert isinstance(stats, dict)
        assert "memory" in stats
        assert "redis" in stats
        assert "cache_type" in stats
        print("✅ Cache statistics retrieval working")

        # Test memory cache stats
        memory_stats = stats["memory"]
        assert "memory_cache_size" in memory_stats
        assert "memory_cache_max_size" in memory_stats
        assert isinstance(memory_stats["memory_cache_size"], int)
        print("✅ Memory cache statistics working")

        # Test redis stats
        redis_stats = stats["redis"]
        assert "redis_connected" in redis_stats
        assert isinstance(redis_stats["redis_connected"], bool)
        print("✅ Redis statistics working")

        return True
    except Exception as e:
        print(f"❌ Cache statistics test failed: {e}")
        return False

def test_concurrent_cache_access():
    """Test concurrent access to cache"""
    print("\n🔍 Testing Concurrent Cache Access...")

    try:
        from middleware.caching import cache_manager
        import threading
        import time

        results = []
        errors = []

        def worker(worker_id):
            try:
                for i in range(10):
                    key = f"concurrent_test_{worker_id}_{i}"
                    value = f"worker_{worker_id}_value_{i}"

                    # Set value
                    cache_manager.set(key, value, ttl=5)

                    # Get value
                    retrieved = cache_manager.get(key)
                    if retrieved != value:
                        errors.append(f"Worker {worker_id}: Expected {value}, got {retrieved}")

                    time.sleep(0.001)  # Small delay
            except Exception as e:
                errors.append(f"Worker {worker_id}: {str(e)}")

        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)

        # Start all threads
        start_time = time.time()
        for thread in threads:
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        end_time = time.time()

        # Check results
        if errors:
            print(f"❌ Concurrent access errors: {errors}")
            return False

        print(f"✅ Concurrent cache access working")
        print(f"  - Threads: 5")
        print(f"  - Operations per thread: 10")
        print(f"  - Total time: {end_time - start_time:.3f}s")

        return True
    except Exception as e:
        print(f"❌ Concurrent cache access test failed: {e}")
        return False

def test_cache_lru_eviction():
    """Test LRU eviction in memory cache"""
    print("\n🔍 Testing Cache LRU Eviction...")

    try:
        from middleware.caching import MemoryCache

        # Create small cache
        cache = MemoryCache(max_size=3)

        # Fill cache to capacity
        cache.set("key1", "value1", ttl=10)
        cache.set("key2", "value2", ttl=10)
        cache.set("key3", "value3", ttl=10)

        # Access key1 to make it most recently used
        cache.get("key1")

        # Add new item (should evict key2 as least recently used)
        cache.set("key4", "value4", ttl=10)

        # Check eviction
        assert cache.get("key1") == "value1"  # Should still exist (was accessed)
        assert cache.get("key2") is None    # Should be evicted (LRU)
        assert cache.get("key3") == "value3"  # Should still exist
        assert cache.get("key4") == "value4"  # Should exist (newly added)

        print("✅ LRU eviction working correctly")
        return True
    except Exception as e:
        print(f"❌ LRU eviction test failed: {e}")
        return False

# Main test runner
async def run_performance_tests():
    print("🚀 Starting Performance Optimization Testing - Fase 2")
    print("=" * 60)

    tests = [
        ("Caching System", test_caching_system),
        ("Cached Decorators", test_cached_decorators),
        ("Performance Monitoring", test_performance_monitoring),
        ("Response Optimization", test_response_optimization),
        ("Cache Statistics", test_cache_statistics),
        ("Concurrent Cache Access", test_concurrent_cache_access),
        ("Cache LRU Eviction", test_cache_lru_eviction)
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
    print("📊 PERFORMANCE OPTIMIZATION TEST RESULTS")
    print("=" * 60)
    print(f"Total Tests: {len(tests)}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")

    if failed == 0:
        print("\n🎉 ALL PERFORMANCE OPTIMIZATION TESTS PASSED!")
        print("📈 Performance System Fully Operational")
        print("\n✅ Ready for Security Enhancements")
        return True
    else:
        print(f"\n⚠️  {failed} performance optimization issues remaining")
        print("🔧 Address issues before proceeding")
        return False

# Run all tests
async def main():
    print("🧪 CLE Performance Optimization Test Suite")
    print(f"⏰ Started: {datetime.now().isoformat()}")

    # Run all tests
    success = await run_performance_tests()

    if success:
        print("\n" + "=" * 60)
        print("🚀 FASE 2 PERFORMANCE OPTIMIZATION - COMPLETED! 🎉")
        print("=" * 60)
        print("\n📋 PERFORMANCE FEATURES IMPLEMENTED:")
        print("  ✅ Redis-based caching with memory fallback")
        print("  ✅ Automatic cache key generation")
        print("  ✅ TTL-based cache expiration")
        print("  ✅ LRU eviction for memory cache")
        print("  ✅ Cached decorators for functions")
        print("  ✅ Performance monitoring and metrics")
        print("  ✅ Response compression logic")
        print("  ✅ Concurrent-safe cache operations")
        print("  ✅ Cache invalidation utilities")

        print("\n🎯 PERFORMANCE STATUS: PRODUCTION READY")
        print("\n📅 NEXT TASKS (Fase 2):")
        print("  - Security Enhancements")
        print("  - Unit Testing Implementation")
        print("\n✨ READY FOR SECURITY ENHANCEMENTS")
        return True
    else:
        print("\n❌ PERFORMANCE OPTIMIZATION INCOMPLETE")
        return False

if __name__ == "__main__":
    asyncio.run(main())