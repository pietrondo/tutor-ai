"""
Rate Limiting Middleware for Tutor AI
Protects API endpoints from abuse with configurable rate limits
"""

import time
import asyncio
from typing import Dict, Optional, Callable
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import redis
import json
import os
import hashlib
from collections import defaultdict
from datetime import datetime, timedelta

class RateLimiter:
    """
    Rate limiter using Redis for distributed rate limiting
    Falls back to in-memory rate limiting if Redis is not available
    """

    def __init__(self):
        self.redis_client = None
        self.memory_store: Dict[str, Dict] = defaultdict(dict)
        self.init_redis()

    def init_redis(self):
        """Initialize Redis connection"""
        try:
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            # Test connection
            self.redis_client.ping()
            print("✅ Redis connected for rate limiting")
        except Exception as e:
            print(f"⚠️ Redis not available, using in-memory rate limiting: {e}")
            self.redis_client = None

    def get_client_ip(self, request: Request) -> str:
        """Get client IP address, considering proxies"""
        # Check for forwarded IP headers
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take the first IP in the chain
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # Fall back to direct connection IP
        return request.client.host if request.client else "unknown"

    def get_rate_limit_key(
        self,
        request: Request,
        key_type: str = "general",
        user_id: Optional[str] = None
    ) -> str:
        """Generate rate limit key"""
        client_ip = self.get_client_ip(request)
        path = request.url.path

        # Create a unique key based on IP, path, and type
        key_data = f"{client_ip}:{path}:{key_type}"
        if user_id:
            key_data = f"user:{user_id}:{path}:{key_type}"

        # Hash to create consistent key
        return hashlib.md5(key_data.encode()).hexdigest()[:16]

    async def is_rate_limited(
        self,
        key: str,
        limit: int,
        window: int
    ) -> tuple[bool, Dict[str, int]]:
        """
        Check if request is rate limited
        Returns (is_limited, rate_limit_info)
        """
        now = int(time.time())
        window_start = now - window

        if self.redis_client:
            return await self._redis_rate_limit_check(key, limit, window, now, window_start)
        else:
            return self._memory_rate_limit_check(key, limit, window, now, window_start)

    async def _redis_rate_limit_check(
        self,
        key: str,
        limit: int,
        window: int,
        now: int,
        window_start: int
    ) -> tuple[bool, Dict[str, int]]:
        """Check rate limit using Redis"""
        pipe = self.redis_client.pipeline()

        # Remove old entries
        pipe.zremrangebyscore(f"rate_limit:{key}", 0, window_start)

        # Add current request
        pipe.zadd(f"rate_limit:{key}", {str(now): now})

        # Count requests in window
        pipe.zcard(f"rate_limit:{key}")

        # Set expiry
        pipe.expire(f"rate_limit:{key}", window + 1)

        results = pipe.execute()
        request_count = results[2]

        is_limited = request_count > limit

        return is_limited, {
            "limit": limit,
            "remaining": max(0, limit - request_count),
            "reset_time": now + window,
            "current_count": request_count
        }

    def _memory_rate_limit_check(
        self,
        key: str,
        limit: int,
        window: int,
        now: int,
        window_start: int
    ) -> tuple[bool, Dict[str, int]]:
        """Check rate limit using in-memory storage"""
        # Clean old entries
        if key in self.memory_store:
            self.memory_store[key] = {
                timestamp: count
                for timestamp, count in self.memory_store[key].items()
                if timestamp > window_start
            }

        # Add current request
        if key not in self.memory_store:
            self.memory_store[key] = {}
        self.memory_store[key][now] = self.memory_store[key].get(now, 0) + 1

        # Count requests in window
        request_count = sum(self.memory_store[key].values())

        is_limited = request_count > limit

        return is_limited, {
            "limit": limit,
            "remaining": max(0, limit - request_count),
            "reset_time": now + window,
            "current_count": request_count
        }

    def get_rate_limit_headers(self, rate_info: Dict[str, int]) -> Dict[str, str]:
        """Generate rate limit headers for response"""
        return {
            "X-RateLimit-Limit": str(rate_info["limit"]),
            "X-RateLimit-Remaining": str(rate_info["remaining"]),
            "X-RateLimit-Reset": str(rate_info["reset_time"]),
            "X-RateLimit-Current": str(rate_info["current_count"])
        }

# Global rate limiter instance
rate_limiter = RateLimiter()

# Rate limit configurations - simplified for local setup
RATE_LIMITS = {
    # General API limits - much more permissive for local use
    "general": {"limit": 1000, "window": 3600},  # 1000 requests per hour
    "strict": {"limit": 100, "window": 60},      # 100 requests per minute

    # File upload limits - increased for local use
    "upload": {"limit": 100, "window": 3600},    # 100 uploads per hour

    # AI-powered endpoints - increased for local use
    "ai_chat": {"limit": 500, "window": 3600},   # 500 chat requests per hour
    "ai_generation": {"limit": 200, "window": 3600},  # 200 generation requests per hour

    # Search endpoints - increased for local use
    "search": {"limit": 1000, "window": 3600},   # 1000 searches per hour
}

def get_rate_limit_config(request: Request) -> Dict[str, int]:
    """Get rate limit configuration based on request path"""
    path = request.url.path

    # Auth endpoints removed for local setup

    # File upload endpoints
    if "/upload" in path:
        return RATE_LIMITS["upload"]

    # AI chat endpoints
    if "/chat" in path:
        return RATE_LIMITS["ai_chat"]

    # AI generation endpoints
    if any(x in path for x in ["/mindmap", "/slides", "/quiz"]):
        return RATE_LIMITS["ai_generation"]

    # Search endpoints
    if "/search" in path:
        return RATE_LIMITS["search"]

    # Default rate limit
    return RATE_LIMITS["general"]

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for rate limiting
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip rate limiting for health checks and static files
        if (
            request.url.path in ["/health", "/metrics"] or
            request.url.path.startswith("/static/") or
            request.url.path.startswith("/docs")
        ):
            return await call_next(request)

        # Get rate limit configuration
        rate_config = get_rate_limit_config(request)

        # Get user ID from request if available
        user_id = None
        try:
            # Try to extract user from Authorization header
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                # This is a simplified approach - in production, you'd decode the JWT
                user_id = "authenticated_user"  # Placeholder
        except Exception:
            pass

        # Generate rate limit key
        rate_limit_key = rate_limiter.get_rate_limit_key(
            request,
            key_type="api",
            user_id=user_id
        )

        # Check rate limit
        is_limited, rate_info = await rate_limiter.is_rate_limited(
            rate_limit_key,
            rate_config["limit"],
            rate_config["window"]
        )

        # Add rate limit headers
        headers = rate_limiter.get_rate_limit_headers(rate_info)

        # Return 429 if rate limited
        if is_limited:
            return Response(
                content=json.dumps({
                    "success": False,
                    "error": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": "Too many requests. Please try again later.",
                        "retry_after": rate_info["reset_time"] - int(time.time())
                    }
                }),
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                headers=headers,
                media_type="application/json"
            )

        # Process request
        response = await call_next(request)

        # Add rate limit headers to response
        for header, value in headers.items():
            response.headers[header] = value

        return response

# Rate limit decorator for specific endpoints
def rate_limit(limit: int, window: int, key_type: str = "custom"):
    """
    Decorator for rate limiting specific endpoints
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Extract request from kwargs
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break

            if not request:
                # If no request found, just call the function
                return await func(*args, **kwargs)

            # Check rate limit
            rate_limit_key = rate_limiter.get_rate_limit_key(request, key_type)
            is_limited, rate_info = await rate_limiter.is_rate_limited(
                rate_limit_key, limit, window
            )

            if is_limited:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded"
                )

            return await func(*args, **kwargs)

        return wrapper
    return decorator

# Admin rate limit checker
async def get_rate_limit_stats() -> Dict[str, any]:
    """Get rate limiting statistics"""
    stats = {
        "redis_connected": rate_limiter.redis_client is not None,
        "memory_store_size": len(rate_limiter.memory_store),
        "rate_limit_configs": RATE_LIMITS
    }

    if rate_limiter.redis_client:
        try:
            # Get Redis stats
            info = rate_limiter.redis_client.info()
            stats["redis_memory"] = info.get("used_memory_human", "N/A")
            stats["redis_connected_clients"] = info.get("connected_clients", 0)
        except Exception:
            pass

    return stats

# Clear rate limits for a specific user/IP (admin function)
async def clear_rate_limits(client_ip: str = None, user_id: str = None) -> bool:
    """Clear rate limits for specific IP or user"""
    if rate_limiter.redis_client:
        try:
            # Delete all rate limit keys for the IP/user
            pattern = "*"
            if client_ip:
                pattern = f"*{hashlib.md5(client_ip.encode()).hexdigest()[:16]}*"
            elif user_id:
                pattern = f"*{hashlib.md5(f'user:{user_id}'.encode()).hexdigest()[:16]}*"

            keys = rate_limiter.redis_client.keys(f"rate_limit:{pattern}")
            if keys:
                rate_limiter.redis_client.delete(*keys)
            return True
        except Exception:
            return False
    else:
        # Clear from memory store
        if client_ip:
            keys_to_remove = [k for k in rate_limiter.memory_store.keys() if client_ip in str(k)]
            for key in keys_to_remove:
                del rate_limiter.memory_store[key]
            return len(keys_to_remove) > 0
        elif user_id:
            keys_to_remove = [k for k in rate_limiter.memory_store.keys() if user_id in str(k)]
            for key in keys_to_remove:
                del rate_limiter.memory_store[key]
            return len(keys_to_remove) > 0
        return False