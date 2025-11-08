"""
Performance Optimization and Caching Middleware
Redis-based caching with fallback to memory cache
"""

import os
import json
import hashlib
import time
from typing import Any, Optional, Dict, Union, Callable
from datetime import datetime, timedelta
from functools import wraps
import asyncio
import logging

logger = logging.getLogger(__name__)

# Try to import Redis, fallback to memory cache
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis not available, using memory cache fallback")

class MemoryCache:
    """Simple in-memory cache as fallback when Redis is not available"""

    def __init__(self, max_size: int = 1000):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.max_size = max_size
        self.access_times: Dict[str, float] = {}

    def get(self, key: str) -> Optional[Any]:
        """Get item from cache"""
        if key in self.cache:
            item = self.cache[key]
            if time.time() < item['expires_at']:
                self.access_times[key] = time.time()
                return item['value']
            else:
                # Item expired, remove it
                del self.cache[key]
                if key in self.access_times:
                    del self.access_times[key]
        return None

    def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """Set item in cache with TTL"""
        try:
            # Remove expired items if cache is full
            if len(self.cache) >= self.max_size:
                self._cleanup_expired()
                if len(self.cache) >= self.max_size:
                    self._evict_lru()

            expires_at = time.time() + ttl
            self.cache[key] = {
                'value': value,
                'expires_at': expires_at,
                'created_at': time.time()
            }
            self.access_times[key] = time.time()
            return True
        except Exception as e:
            logger.error(f"Memory cache set error: {e}")
            return False

    def delete(self, key: str) -> bool:
        """Delete item from cache"""
        if key in self.cache:
            del self.cache[key]
        if key in self.access_times:
            del self.access_times[key]
        return True

    def clear(self) -> bool:
        """Clear all cache items"""
        self.cache.clear()
        self.access_times.clear()
        return True

    def _cleanup_expired(self):
        """Remove expired items"""
        current_time = time.time()
        expired_keys = [
            key for key, item in self.cache.items()
            if current_time >= item['expires_at']
        ]
        for key in expired_keys:
            del self.cache[key]
            if key in self.access_times:
                del self.access_times[key]

    def _evict_lru(self):
        """Evict least recently used item"""
        if not self.access_times:
            return

        lru_key = min(self.access_times.items(), key=lambda x: x[1])[0]
        self.delete(lru_key)

class CacheManager:
    """Unified cache manager with Redis backend and memory fallback"""

    def __init__(self, redis_url: str = None, default_ttl: int = 300):
        self.default_ttl = default_ttl
        self.redis_client = None
        self.memory_cache = MemoryCache()

        # Initialize Redis if available
        if REDIS_AVAILABLE and redis_url:
            try:
                self.redis_client = redis.from_url(
                    redis_url,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                    retry_on_timeout=True
                )
                # Test connection
                self.redis_client.ping()
                logger.info("Redis cache initialized successfully")
            except Exception as e:
                logger.warning(f"Redis connection failed: {e}, using memory cache")
                self.redis_client = None

    def get(self, key: str) -> Optional[Any]:
        """Get item from cache (Redis first, fallback to memory)"""
        try:
            # Try Redis first
            if self.redis_client:
                cached_value = self.redis_client.get(key)
                if cached_value:
                    try:
                        return json.loads(cached_value)
                    except json.JSONDecodeError:
                        return cached_value

            # Fallback to memory cache
            return self.memory_cache.get(key)
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set item in cache (Redis and memory)"""
        ttl = ttl or self.default_ttl
        try:
            success = True

            # Try Redis first
            if self.redis_client:
                try:
                    if isinstance(value, (dict, list)):
                        serialized_value = json.dumps(value, default=str)
                    else:
                        serialized_value = str(value)

                    self.redis_client.setex(key, ttl, serialized_value)
                except Exception as e:
                    logger.warning(f"Redis set error: {e}")
                    success = False

            # Always store in memory cache as backup
            memory_success = self.memory_cache.set(key, value, ttl)

            return success and memory_success
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False

    def delete(self, key: str) -> bool:
        """Delete item from cache"""
        try:
            success = True

            # Try Redis first
            if self.redis_client:
                try:
                    self.redis_client.delete(key)
                except Exception as e:
                    logger.warning(f"Redis delete error: {e}")
                    success = False

            # Always delete from memory cache
            self.memory_cache.delete(key)

            return success
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False

    def clear_pattern(self, pattern: str) -> int:
        """Clear cache items matching pattern"""
        try:
            cleared_count = 0

            # Try Redis pattern deletion
            if self.redis_client:
                try:
                    keys = self.redis_client.keys(pattern)
                    if keys:
                        cleared_count += len(keys)
                        self.redis_client.delete(*keys)
                except Exception as e:
                    logger.warning(f"Redis pattern delete error: {e}")

            # Clear matching keys from memory cache
            memory_keys = list(self.memory_cache.cache.keys())
            for key in memory_keys:
                if pattern.replace('*', '') in key:
                    self.memory_cache.delete(key)
                    cleared_count += 1

            return cleared_count
        except Exception as e:
            logger.error(f"Cache clear pattern error: {e}")
            return 0

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            redis_stats = {}
            if self.redis_client:
                try:
                    info = self.redis_client.info()
                    redis_stats = {
                        'redis_connected': True,
                        'used_memory': info.get('used_memory_human', 'N/A'),
                        'connected_clients': info.get('connected_clients', 0),
                        'keyspace_hits': info.get('keyspace_hits', 0),
                        'keyspace_misses': info.get('keyspace_misses', 0)
                    }
                except Exception:
                    redis_stats = {'redis_connected': False}
            else:
                redis_stats = {'redis_connected': False}

            memory_stats = {
                'memory_cache_size': len(self.memory_cache.cache),
                'memory_cache_max_size': self.memory_cache.max_size
            }

            return {
                'redis': redis_stats,
                'memory': memory_stats,
                'cache_type': 'redis' if self.redis_client else 'memory'
            }
        except Exception as e:
            logger.error(f"Cache stats error: {e}")
            return {}

# Global cache manager instance
cache_manager = CacheManager(
    redis_url=os.getenv('REDIS_URL', None),
    default_ttl=int(os.getenv('CACHE_TTL', 300))
)

def cache_key(prefix: str, *args, **kwargs) -> str:
    """Generate cache key from arguments"""
    try:
        # Create a deterministic key
        key_data = {
            'args': args,
            'kwargs': sorted(kwargs.items())
        }
        key_string = json.dumps(key_data, sort_keys=True, default=str)
        key_hash = hashlib.md5(key_string.encode()).hexdigest()[:16]
        return f"{prefix}:{key_hash}"
    except Exception:
        # Fallback to simple key
        return f"{prefix}:{hash(str(args) + str(sorted(kwargs.items())))}"

def cached(ttl: Optional[int] = None, key_prefix: str = "api"):
    """Decorator to cache function results"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key_str = cache_key(key_prefix, func.__name__, *args, **kwargs)

            # Try to get from cache
            cached_result = cache_manager.get(cache_key_str)
            if cached_result is not None:
                return cached_result

            # Execute function and cache result
            result = func(*args, **kwargs)
            cache_manager.set(cache_key_str, result, ttl)
            return result

        return wrapper
    return decorator

def async_cached(ttl: Optional[int] = None, key_prefix: str = "api"):
    """Decorator to cache async function results"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key_str = cache_key(key_prefix, func.__name__, *args, **kwargs)

            # Try to get from cache
            cached_result = cache_manager.get(cache_key_str)
            if cached_result is not None:
                return cached_result

            # Execute function and cache result
            result = await func(*args, **kwargs)
            cache_manager.set(cache_key_str, result, ttl)
            return result

        return wrapper
    return decorator

# Cache invalidation utilities
class CacheInvalidator:
    """Utilities for cache invalidation"""

    @staticmethod
    def invalidate_user_data(user_id: str):
        """Invalidate all cache data for a user"""
        patterns = [
            f"user:{user_id}:*",
            f"api:*:{user_id}:*",
            f"analytics:{user_id}:*"
        ]
        total_cleared = 0
        for pattern in patterns:
            total_cleared += cache_manager.clear_pattern(pattern)
        logger.info(f"Invalidated {total_cleared} cache entries for user {user_id}")
        return total_cleared

    @staticmethod
    def invalidate_course_data(course_id: str):
        """Invalidate all cache data for a course"""
        patterns = [
            f"course:{course_id}:*",
            f"api:*:{course_id}:*",
            f"cards:{course_id}:*",
            f"questions:{course_id}:*"
        ]
        total_cleared = 0
        for pattern in patterns:
            total_cleared += cache_manager.clear_pattern(pattern)
        logger.info(f"Invalidated {total_cleared} cache entries for course {course_id}")
        return total_cleared

    @staticmethod
    def invalidate_api_response(endpoint: str, params: Dict = None):
        """Invalidate specific API response cache"""
        try:
            if params:
                key_str = cache_key("api", endpoint, **params)
            else:
                key_str = f"api:{endpoint}"
            cache_manager.delete(key_str)
            logger.info(f"Invalidated cache for API endpoint: {endpoint}")
        except Exception as e:
            logger.error(f"Failed to invalidate API cache: {e}")

# Performance monitoring
class PerformanceMonitor:
    """Monitor and log performance metrics"""

    def __init__(self):
        self.metrics: Dict[str, List[float]] = {}

    def record_response_time(self, endpoint: str, response_time: float):
        """Record response time for an endpoint"""
        if endpoint not in self.metrics:
            self.metrics[endpoint] = []
        self.metrics[endpoint].append(response_time)

    def get_metrics(self) -> Dict[str, Dict[str, float]]:
        """Get performance metrics"""
        result = {}
        for endpoint, times in self.metrics.items():
            if times:
                result[endpoint] = {
                    'count': len(times),
                    'avg_time': sum(times) / len(times),
                    'min_time': min(times),
                    'max_time': max(times),
                    'last_time': times[-1]
                }
        return result

    def clear_metrics(self):
        """Clear all metrics"""
        self.metrics.clear()

# Global performance monitor
performance_monitor = PerformanceMonitor()

def monitor_performance(func: Callable) -> Callable:
    """Decorator to monitor function performance"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            response_time = time.time() - start_time
            performance_monitor.record_response_time(func.__name__, response_time)
            return result
        except Exception as e:
            response_time = time.time() - start_time
            performance_monitor.record_response_time(func.__name__, response_time)
            raise
    return wrapper

def monitor_async_performance(func: Callable) -> Callable:
    """Decorator to monitor async function performance"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            response_time = time.time() - start_time
            performance_monitor.record_response_time(func.__name__, response_time)
            return result
        except Exception as e:
            response_time = time.time() - start_time
            performance_monitor.record_response_time(func.__name__, response_time)
            raise
    return wrapper

# Response compression utilities
def should_compress_response(response_size: int, content_type: str) -> bool:
    """Determine if response should be compressed"""
    # Don't compress very small responses
    if response_size < 1024:  # Less than 1KB
        return False

    # Only compress compressible content types
    compressible_types = [
        'application/json',
        'text/html',
        'text/css',
        'text/javascript',
        'application/javascript'
    ]

    return any(ct in content_type for ct in compressible_types)

def get_cache_ttl_for_content(content_type: str) -> int:
    """Get appropriate TTL for different content types"""
    ttl_map = {
        'user_profile': 3600,      # 1 hour
        'course_data': 1800,       # 30 minutes
        'analytics': 300,          # 5 minutes
        'questions': 600,         # 10 minutes
        'static_data': 7200,      # 2 hours
        'api_response': 60         # 1 minute (default)
    }

    for content_key, ttl in ttl_map.items():
        if content_key in content_type:
            return ttl

    return 60  # Default 1 minute