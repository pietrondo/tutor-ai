"""
Comprehensive API Logging Middleware for Tutor-AI Backend.

This middleware provides detailed logging of all HTTP requests and responses
including performance metrics, correlation IDs, security events, and error tracking.

Features:
- Request/response logging with correlation IDs
- Performance monitoring and timing
- Request body logging with sensitive data filtering
- Response size and status tracking
- Security event detection
- Error rate monitoring
- Client IP and User-Agent tracking
- API endpoint analytics
"""

import time
import json
import hashlib
from typing import Callable, Dict, Any, Optional, Set
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import logging
from datetime import datetime
import re
import uuid

try:
    from logging_config import get_logger, RequestLogger, SecurityLogger, PerformanceLogger, SensitiveDataFilter
except ImportError:
    try:
        # Try importing from backend directory for production mode
        from backend.logging_config import get_logger, RequestLogger, SecurityLogger, PerformanceLogger, SensitiveDataFilter
    except ImportError:
        # Fallback if logging_config is not available
        import logging
        get_logger = lambda name: logging.getLogger(name)
        RequestLogger = lambda: None
    SecurityLogger = lambda: None
    PerformanceLogger = lambda: None
    SensitiveDataFilter = lambda: None


class APILoggingMiddleware(BaseHTTPMiddleware):
    """
    Comprehensive API logging middleware with performance monitoring and security tracking.
    """

    def __init__(
        self,
        app: ASGIApp,
        *,
        log_request_body: bool = True,
        log_response_body: bool = False,  # Disabled by default for performance
        max_body_size: int = 10000,  # Max body size to log (bytes)
        excluded_paths: Optional[Set[str]] = None,
        excluded_health_checks: bool = True,
        performance_threshold_ms: float = 1000.0,  # Log slow requests
        rate_limit_tracking: bool = True
    ):
        super().__init__(app)
        self.log_request_body = log_request_body
        self.log_response_body = log_response_body
        self.max_body_size = max_body_size
        self.excluded_paths = excluded_paths or {
            "/health", "/metrics", "/docs", "/openapi.json", "/favicon.ico"
        }
        self.excluded_health_checks = excluded_health_checks
        self.performance_threshold_ms = performance_threshold_ms
        self.rate_limit_tracking = rate_limit_tracking

        # Initialize loggers
        self.logger = get_logger("api_middleware")
        self.request_logger = RequestLogger()
        self.security_logger = SecurityLogger()
        self.performance_logger = PerformanceLogger()
        self.sensitive_filter = SensitiveDataFilter()

        # Rate limiting tracking
        self.request_counts: Dict[str, Dict[str, Any]] = {}

        # Security patterns
        self.security_patterns = {
            "sql_injection": [
                r"union\s+select", r"drop\s+table", r"insert\s+into",
                r"delete\s+from", r"update\s+set", r"exec\s*\(",
                r"script\s*>", r"javascript:", r"vbscript:"
            ],
            "xss": [
                r"<script", r"</script>", r"javascript:", r"onerror=",
                r"onload=", r"onclick=", r"alert\s*\("
            ],
            "path_traversal": [
                r"\.\./", r"\.\.\\", r"%2e%2e%2f", r"%2e%2e%5c",
                r"/etc/passwd", r"/etc/shadow", r"\\windows\\system32"
            ]
        }

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and log comprehensive information."""

        # Skip logging for excluded paths
        if self._should_skip_logging(request):
            return await call_next(request)

        # Generate correlation ID
        correlation_id = self._generate_correlation_id(request)

        # Store correlation ID in request state for other middleware/handlers
        request.state.correlation_id = correlation_id

        # Get client information
        client_info = self._get_client_info(request)

        # Log request start
        start_time = time.time()
        request_size = await self._log_request(request, correlation_id, client_info)

        try:
            # Process request
            response = await call_next(request)

            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000

            # Get response size
            response_size = self._get_response_size(response)

            # Log response
            self._log_response(
                request, response, correlation_id, client_info,
                duration_ms, response_size, request_size
            )

            # Add correlation ID to response headers
            response.headers["X-Correlation-ID"] = correlation_id

            return response

        except Exception as exc:
            # Calculate duration for failed requests
            duration_ms = (time.time() - start_time) * 1000

            # Log error
            await self._log_error(
                request, exc, correlation_id, client_info,
                duration_ms, request_size
            )

            # Re-raise the exception
            raise

    def _should_skip_logging(self, request: Request) -> bool:
        """Determine if request should be excluded from logging."""
        path = request.url.path

        # Skip health checks
        if self.excluded_health_checks and (
            path.startswith("/health") or
            path.startswith("/metrics") or
            path == "/ping"
        ):
            return True

        # Skip excluded paths
        if path in self.excluded_paths:
            return True

        # Skip static files
        if path.startswith("/static/") or path.startswith("/favicon"):
            return True

        return False

    def _generate_correlation_id(self, request: Request) -> str:
        """Generate or retrieve correlation ID for request tracing."""
        # Check if correlation ID is already present in headers
        correlation_id = request.headers.get("X-Correlation-ID") or request.headers.get("X-Request-ID")

        if correlation_id:
            return correlation_id[:8]  # Truncate for readability

        # Generate new correlation ID
        return str(uuid.uuid4())[:8]

    def _get_client_info(self, request: Request) -> Dict[str, Any]:
        """Extract client information from request."""
        # Get client IP (considering proxies)
        client_ip = self._get_client_ip(request)

        # Get user agent
        user_agent = request.headers.get("User-Agent", "Unknown")

        # Extract browser/OS info
        browser_info = self._parse_user_agent(user_agent)

        return {
            "ip_address": client_ip,
            "user_agent": user_agent,
            "browser": browser_info.get("browser"),
            "os": browser_info.get("os"),
            "device": browser_info.get("device"),
            "is_bot": browser_info.get("is_bot", False)
        }

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address considering forwarded headers."""
        # Check for forwarded headers
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()

        # Fall back to client IP
        return getattr(request.client, "host", "unknown") if request.client else "unknown"

    def _parse_user_agent(self, user_agent: str) -> Dict[str, str]:
        """Parse user agent string to extract browser/OS information."""
        user_agent_lower = user_agent.lower()

        browser = "Unknown"
        os = "Unknown"
        device = "Desktop"
        is_bot = False

        # Browser detection
        if "chrome" in user_agent_lower and "edg" not in user_agent_lower:
            browser = "Chrome"
        elif "firefox" in user_agent_lower:
            browser = "Firefox"
        elif "safari" in user_agent_lower and "chrome" not in user_agent_lower:
            browser = "Safari"
        elif "edg" in user_agent_lower:
            browser = "Edge"
        elif "opera" in user_agent_lower or "opr" in user_agent_lower:
            browser = "Opera"
        elif "postman" in user_agent_lower:
            browser = "Postman"
            is_bot = True
        elif "curl" in user_agent_lower:
            browser = "cURL"
            is_bot = True
        elif "wget" in user_agent_lower:
            browser = "Wget"
            is_bot = True

        # OS detection
        if "windows" in user_agent_lower:
            os = "Windows"
        elif "mac os" in user_agent_lower or "macos" in user_agent_lower:
            os = "macOS"
        elif "linux" in user_agent_lower:
            os = "Linux"
        elif "android" in user_agent_lower:
            os = "Android"
            device = "Mobile"
        elif "ios" in user_agent_lower or "iphone" in user_agent_lower or "ipad" in user_agent_lower:
            os = "iOS"
            device = "Mobile" if "iphone" in user_agent_lower else "Tablet"

        # Bot detection
        bot_patterns = ["bot", "crawler", "spider", "scraper", "curl", "wget", "postman"]
        if any(pattern in user_agent_lower for pattern in bot_patterns):
            is_bot = True

        return {
            "browser": browser,
            "os": os,
            "device": device,
            "is_bot": is_bot
        }

    async def _log_request(
        self,
        request: Request,
        correlation_id: str,
        client_info: Dict[str, Any]
    ) -> int:
        """Log incoming request details."""

        # Get request headers (filter sensitive ones)
        headers = dict(request.headers)
        sensitive_headers = {"authorization", "cookie", "x-api-key"}
        filtered_headers = {
            k: v for k, v in headers.items()
            if k.lower() not in sensitive_headers
        }

        # Get request body if enabled
        body_info = {}
        request_size = 0

        if self.log_request_body and request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                request_size = len(body)

                if body and request_size <= self.max_body_size:
                    try:
                        # Try to parse as JSON
                        body_data = json.loads(body.decode())
                        # Filter sensitive data
                        body_info = {"body": self.sensitive_filter.filter_dict(body_data)}
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        # If not JSON, log as text (truncated)
                        body_text = body.decode(errors="ignore")
                        body_info = {"body": body_text[:self.max_body_size]}

            except Exception as e:
                self.logger.warning(f"Failed to log request body: {e}", extra={
                    "correlation_id": correlation_id
                })

        # Check for security patterns in request
        security_events = self._check_security_patterns(request, filtered_headers, body_info)

        # Log security events if any detected
        for event_type, details in security_events:
            self.security_logger.log_security_event(
                event_type=event_type,
                description=f"Security pattern detected in {request.method} {request.url.path}",
                severity="WARNING",
                correlation_id=correlation_id,
                client_ip=client_info["ip_address"],
                **details
            )

        # Rate limiting check
        if self.rate_limit_tracking:
            self._track_request_rate(client_info["ip_address"], request)

        # Use RequestLogger for consistent format
        self.request_logger.log_request(
            method=request.method,
            path=request.url.path,
            headers=filtered_headers,
            body=json.dumps(body_info) if body_info else None,
            correlation_id=correlation_id
        )

        # Additional detailed logging
        self.logger.info(
            f"Incoming request: {request.method} {request.url.path}",
            extra={
                "event_type": "api_request",
                "method": request.method,
                "path": request.url.path,
                "query_params": dict(request.query_params),
                "headers": filtered_headers,
                "client_info": client_info,
                "request_size": request_size,
                "correlation_id": correlation_id,
                "security_events": security_events,
                **body_info
            }
        )

        return request_size

    def _log_response(
        self,
        request: Request,
        response: Response,
        correlation_id: str,
        client_info: Dict[str, Any],
        duration_ms: float,
        response_size: int,
        request_size: int
    ) -> None:
        """Log response details."""

        # Log slow requests
        if duration_ms > self.performance_threshold_ms:
            self.performance_logger.log_operation_time(
                operation=f"slow_request_{request.method}_{request.url.path}",
                duration_ms=duration_ms,
                success=True,
                threshold_ms=self.performance_threshold_ms,
                path=request.url.path,
                method=request.method
            )

        # Use RequestLogger for consistent format
        self.request_logger.log_response(
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            response_size=response_size,
            duration_ms=duration_ms,
            correlation_id=correlation_id
        )

        # Determine log level based on status code
        if response.status_code >= 500:
            level = logging.ERROR
        elif response.status_code >= 400:
            level = logging.WARNING
        else:
            level = logging.INFO

        # Log response details
        self.logger.log(
            level,
            f"Response: {request.method} {request.url.path} - {response.status_code} - {duration_ms:.2f}ms",
            extra={
                "event_type": "api_response",
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
                "response_size": response_size,
                "request_size": request_size,
                "correlation_id": correlation_id,
                "client_info": client_info,
                "response_headers": dict(response.headers),
                "performance_category": self._categorize_performance(duration_ms)
            }
        )

    async def _log_error(
        self,
        request: Request,
        exc: Exception,
        correlation_id: str,
        client_info: Dict[str, Any],
        duration_ms: float,
        request_size: int
    ) -> None:
        """Log error details."""

        # Determine error type and status code
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        error_type = type(exc).__name__

        if isinstance(exc, HTTPException):
            status_code = exc.status_code

        # Log error
        self.logger.error(
            f"Request failed: {request.method} {request.url.path} - {error_type}: {str(exc)}",
            extra={
                "event_type": "api_error",
                "method": request.method,
                "path": request.url.path,
                "error_type": error_type,
                "error_message": str(exc),
                "status_code": status_code,
                "duration_ms": duration_ms,
                "request_size": request_size,
                "correlation_id": correlation_id,
                "client_info": client_info,
                "exception_details": {
                    "type": error_type,
                    "message": str(exc),
                    "args": getattr(exc, 'args', None)
                }
            }
        )

    def _check_security_patterns(
        self,
        request: Request,
        headers: Dict[str, str],
        body_info: Dict[str, Any]
    ) -> list:
        """Check request for potential security threats."""

        security_events = []

        # Combine all text to check
        text_to_check = " ".join([
            request.url.path,
            str(request.query_params),
            " ".join(headers.values()),
            json.dumps(body_info)
        ]).lower()

        # Check for SQL injection
        for pattern in self.security_patterns["sql_injection"]:
            if re.search(pattern, text_to_check, re.IGNORECASE):
                security_events.append(("sql_injection_attempt", {"pattern": pattern}))
                break

        # Check for XSS
        for pattern in self.security_patterns["xss"]:
            if re.search(pattern, text_to_check, re.IGNORECASE):
                security_events.append(("xss_attempt", {"pattern": pattern}))
                break

        # Check for path traversal
        for pattern in self.security_patterns["path_traversal"]:
            if re.search(pattern, text_to_check, re.IGNORECASE):
                security_events.append(("path_traversal_attempt", {"pattern": pattern}))
                break

        return security_events

    def _track_request_rate(self, client_ip: str, request: Request) -> None:
        """Track request rate for potential rate limiting abuse."""
        current_time = time.time()
        minute_key = int(current_time // 60)

        if client_ip not in self.request_counts:
            self.request_counts[client_ip] = {}

        if minute_key not in self.request_counts[client_ip]:
            self.request_counts[client_ip][minute_key] = 0

        self.request_counts[client_ip][minute_key] += 1

        # Check for suspicious patterns
        requests_per_minute = self.request_counts[client_ip][minute_key]
        if requests_per_minute > 100:  # Threshold for suspicious activity
            self.security_logger.log_security_event(
                event_type="high_request_rate",
                description=f"High request rate detected: {requests_per_minute} requests/minute",
                severity="WARNING",
                client_ip=client_ip,
                requests_per_minute=requests_per_minute,
                endpoint=request.url.path
            )

        # Clean old entries (keep only last hour)
        cutoff_time = current_time - 3600
        self.request_counts[client_ip] = {
            k: v for k, v in self.request_counts[client_ip].items()
            if k > cutoff_time // 60
        }

    def _get_response_size(self, response: Response) -> int:
        """Calculate response size."""
        try:
            if hasattr(response, 'body'):
                return len(response.body) if response.body else 0
            elif hasattr(response, 'content'):
                return len(response.content) if response.content else 0
            else:
                # Estimate from content-length header
                return int(response.headers.get("content-length", 0))
        except Exception:
            return 0

    def _categorize_performance(self, duration_ms: float) -> str:
        """Categorize request performance."""
        if duration_ms < 100:
            return "fast"
        elif duration_ms < 500:
            return "normal"
        elif duration_ms < 1000:
            return "slow"
        else:
            return "very_slow"


# Utility function to create and configure the middleware
def create_api_logging_middleware(
    app,
    log_level: str = "INFO",
    **kwargs
) -> APILoggingMiddleware:
    """
    Factory function to create API logging middleware with configuration.

    Args:
        app: FastAPI application
        log_level: Logging level override
        **kwargs: Additional configuration for APILoggingMiddleware

    Returns:
        Configured APILoggingMiddleware instance
    """

    # Set log level if provided
    if log_level:
        logging.getLogger("api_middleware").setLevel(getattr(logging, log_level.upper()))

    return APILoggingMiddleware(app, **kwargs)