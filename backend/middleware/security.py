"""
Security Middleware for CLE API
Rate limiting, CORS configuration, security headers, and input sanitization
"""

import time
import hashlib
import secrets
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime, timedelta
from collections import defaultdict, deque
from fastapi import Request, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import os
import re

logger = logging.getLogger(__name__)

class RateLimiter:
    """Rate limiting implementation with sliding window"""

    def __init__(self, requests_per_minute: int = 60, cleanup_interval: int = 300):
        self.requests_per_minute = requests_per_minute
        self.window_size = 60  # 1 minute sliding window
        self.cleanup_interval = cleanup_interval
        self.clients: Dict[str, deque] = defaultdict(lambda: deque(maxlen=self.requests_per_minute * 2))
        self.last_cleanup = time.time()

    def _cleanup_old_requests(self):
        """Clean up old request records"""
        current_time = time.time()
        if current_time - self.last_cleanup > self.cleanup_interval:
            cutoff = current_time - self.window_size
            for client_id, requests in list(self.clients.items()):
                # Remove requests older than window
                while requests and requests[0] < cutoff:
                    requests.popleft()

                # Remove empty client records
                if not requests:
                    del self.clients[client_id]

            self.last_cleanup = current_time

    def is_allowed(self, client_id: str) -> bool:
        """Check if client is allowed to make request"""
        self._cleanup_old_requests()

        current_time = time.time()
        client_requests = self.clients[client_id]

        # Remove requests outside the window
        cutoff = current_time - self.window_size
        while client_requests and client_requests[0] < cutoff:
            client_requests.popleft()

        # Check if under rate limit
        if len(client_requests) < self.requests_per_minute:
            client_requests.append(current_time)
            return True

        return False

    def get_rate_limit_headers(self, client_id: str) -> Dict[str, str]:
        """Get rate limit headers for response"""
        self._cleanup_old_requests()
        current_time = time.time()
        cutoff = current_time - self.window_size

        client_requests = self.clients[client_id]
        recent_requests = [r for r in client_requests if r >= cutoff]

        remaining = max(0, self.requests_per_minute - len(recent_requests))
        reset_time = int(max(client_requests) + self.window_size) if client_requests else int(current_time + self.window_size)

        return {
            "X-RateLimit-Limit": str(self.requests_per_minute),
            "X-RateLimit-Remaining": str(remaining),
            "X-RateLimit-Reset": str(reset_time)
        }

class AdvancedRateLimiter:
    """Advanced rate limiting with multiple tiers"""

    def __init__(self):
        self.limiters = {
            'global': RateLimiter(requests_per_minute=1000),  # Global API limit
            'auth': RateLimiter(requests_per_minute=10),        # Authentication endpoints
            'api': RateLimiter(requests_per_minute=60),         # General API endpoints
            'upload': RateLimiter(requests_per_minute=5),        # File upload endpoints
            'admin': RateLimiter(requests_per_minute=30),        # Admin endpoints
        }

    def get_limiter_for_path(self, path: str) -> RateLimiter:
        """Get appropriate rate limiter for API path"""
        if '/auth/' in path:
            return self.limiters['auth']
        elif '/admin/' in path:
            return self.limiters['admin']
        elif '/upload' in path or '/file' in path:
            return self.limiters['upload']
        else:
            return self.limiters['api']

class SecurityHeaders:
    """Security headers middleware"""

    @staticmethod
    def add_security_headers(response: Response) -> Response:
        """Add security headers to response"""
        headers = {
            # Clickjacking protection - disabled for development convenience
            "X-Frame-Options": "ALLOWALL",

            # XSS Protection
            "X-XSS-Protection": "1; mode=block",

            # Content type protection
            "X-Content-Type-Options": "nosniff",

            # Referrer policy
            "Referrer-Policy": "strict-origin-when-cross-origin",

            # Content Security Policy (basic)
            "Content-Security-Policy": (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self'; "
                "connect-src 'self' https:; "
                "frame-ancestors 'none';"
            ),

            # Strict Transport Security (HTTPS only)
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains" if os.getenv("HTTPS_ONLY") else "",

            # Permissions policy
            "Permissions-Policy": (
                "camera=(), microphone=(), geolocation=(), "
                "payment=(), usb=(), magnetometer=(), gyroscope=(), "
                "accelerometer=(), autoplay=(), encrypted-media=()"
            )
        }

        # Add headers to response
        for key, value in headers.items():
            if value:  # Only add non-empty headers
                response.headers[key] = value

        return response

class InputSanitizer:
    """Advanced input sanitization"""

    @staticmethod
    def sanitize_input(input_string: str, max_length: int = 10000) -> str:
        """Sanitize user input string"""
        if not isinstance(input_string, str):
            return str(input_string)

        # Length limit
        if len(input_string) > max_length:
            input_string = input_string[:max_length]

        # Remove null bytes and control characters
        sanitized = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', input_string)

        # Basic XSS prevention
        sanitized = re.sub(r'<script[^>]*>.*?</script>', '', sanitized, flags=re.IGNORECASE | re.DOTALL)
        sanitized = re.sub(r'<iframe[^>]*>.*?</iframe>', '', sanitized, flags=re.IGNORECASE | re.DOTALL)
        sanitized = re.sub(r'javascript:', '', sanitized, flags=re.IGNORECASE)
        sanitized = re.sub(r'vbscript:', '', sanitized, flags=re.IGNORECASE)
        sanitized = re.sub(r'onload=', '', sanitized, flags=re.IGNORECASE)
        sanitized = re.sub(r'onerror=', '', sanitized, flags=re.IGNORECASE)

        return sanitized.strip()

    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

    @staticmethod
    def validate_user_id(user_id: str) -> bool:
        """Validate user ID format"""
        pattern = r'^[a-zA-Z0-9_-]{3,50}$'
        return bool(re.match(pattern, user_id))

    @staticmethod
    def validate_course_id(course_id: str) -> bool:
        """Validate course ID format"""
        pattern = r'^[a-zA-Z0-9_-]{3,50}$'
        return bool(re.match(pattern, course_id))

    @staticmethod
    def sanitize_sql_input(input_string: str) -> str:
        """Prevent SQL injection"""
        # Remove SQL keywords and patterns
        sql_patterns = [
            r'(?i)\b(drop|delete|truncate|insert|update|alter|exec|execute|union|select)\b',
            r'(?i)\b(--|#|\/\*|\*\/)',
            r'(?i)(or\s+1\s*=\s*1|or\s+true|\'+\s*=\s*[''])'
        ]

        sanitized = input_string
        for pattern in sql_patterns:
            sanitized = re.sub(pattern, '', sanitized)

        return sanitized.strip()

class CSRFProtection:
    """CSRF token protection"""

    def __init__(self):
        self.secret_key = os.getenv("CSRF_SECRET_KEY", secrets.token_urlsafe(32))
        self.token_expiry = 3600  # 1 hour

    def generate_token(self) -> str:
        """Generate CSRF token"""
        timestamp = str(int(time.time()))
        random_data = secrets.token_urlsafe(16)

        # Create token: timestamp:random:signature
        message = f"{timestamp}:{random_data}"
        signature = hashlib.sha256(f"{message}:{self.secret_key}".encode()).hexdigest()

        return f"{message}:{signature}"

    def validate_token(self, token: str) -> bool:
        """Validate CSRF token"""
        if not token or ':' not in token:
            return False

        try:
            parts = token.split(':')
            if len(parts) != 3:
                return False

            timestamp, random_data, signature = parts

            # Check token age
            token_time = int(timestamp)
            if time.time() - token_time > self.token_expiry:
                return False

            # Verify signature
            expected_signature = hashlib.sha256(
                f"{timestamp}:{random_data}:{self.secret_key}".encode()
            ).hexdigest()

            return secrets.compare_digest(signature, expected_signature)
        except (ValueError, AttributeError):
            return False

class IPWhitelist:
    """IP whitelist functionality"""

    def __init__(self):
        self.whitelisted_ips = set()
        self.load_whitelist()

    def load_whitelist(self):
        """Load IP whitelist from environment"""
        whitelist = os.getenv("IP_WHITELIST", "")
        if whitelist:
            self.whitelisted_ips = set(ip.strip() for ip in whitelist.split(',') if ip.strip())

    def is_whitelisted(self, ip_address: str) -> bool:
        """Check if IP is whitelisted"""
        if not self.whitelisted_ips:
            return True  # No whitelist means all IPs allowed
        return ip_address in self.whitelisted_ips

class SecurityMiddleware:
    """Main security middleware"""

    def __init__(self, app):
        self.app = app
        self.rate_limiter = AdvancedRateLimiter()
        self.csrf_protection = CSRFProtection()
        self.ip_whitelist = IPWhitelist()
        self.sanitizer = InputSanitizer()

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            request = Request(scope, receive)

            # Get client IP
            client_ip = self._get_client_ip(request)

            # Check IP whitelist
            if not self.ip_whitelist.is_whitelisted(client_ip):
                return await self._send_error_response(send, 403, "IP not whitelisted")

            # Rate limiting
            rate_limiter = self.rate_limiter.get_limiter_for_path(request.url.path)
            client_id = self._get_client_identifier(request)

            if not rate_limiter.is_allowed(client_id):
                headers = rate_limiter.get_rate_limit_headers(client_id)
                return await self._send_rate_limit_response(send, headers)

            # CSRF protection for state-changing requests
            if request.method in ["POST", "PUT", "DELETE", "PATCH"]:
                if not self._validate_csrf_token(request):
                    return await self._send_error_response(send, 403, "Invalid CSRF token")

        # Let request proceed
        return await self.app(scope, receive, send)

    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address"""
        # Check for forwarded headers
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        return request.client.host if request.client else "unknown"

    def _get_client_identifier(self, request: Request) -> str:
        """Get unique client identifier for rate limiting"""
        # Try to get user ID from token or use IP address
        user_id = getattr(request.state, "user_id", None)
        if user_id:
            return f"user:{user_id}"

        client_ip = self._get_client_ip(request)
        return f"ip:{client_ip}"

    def _validate_csrf_token(self, request: Request) -> bool:
        """Validate CSRF token for protected requests"""
        # Skip CSRF for API endpoints that use other authentication
        if request.url.path.startswith("/api/v1/"):
            # For API, we rely on JWT authentication instead of CSRF
            return True

        # Check CSRF token in headers or form data
        csrf_token = (
            request.headers.get("X-CSRF-Token") or
            request.headers.get("X-XSRF-Token") or
            request.headers.get("Authorization")  # JWT tokens bypass CSRF
        )

        if csrf_token:
            return self.csrf_protection.validate_token(csrf_token)

        return False

    async def _send_error_response(self, send, status_code: int, message: str):
        """Send error response"""
        response = JSONResponse(
            status_code=status_code,
            content={
                "success": False,
                "error": "Security Error",
                "detail": message,
                "timestamp": datetime.utcnow().isoformat()
            }
        )

        # Add security headers
        response = SecurityHeaders.add_security_headers(response)

        await send({
            "type": "http.response.start",
            "status": status_code,
            "headers": [
                [key.encode(), value.encode()] for key, value in response.headers.items()
            ],
        })

        await send({
            "type": "http.response.body",
            "body": response.body.encode(),
        })

    async def _send_rate_limit_response(self, send, headers: Dict[str, str]):
        """Send rate limit response"""
        response = JSONResponse(
            status_code=429,
            content={
                "success": False,
                "error": "Rate Limit Exceeded",
                "detail": "Too many requests, please try again later",
                "timestamp": datetime.utcnow().isoformat()
            }
        )

        # Add rate limit headers
        for key, value in headers.items():
            response.headers[key] = value

        # Add security headers
        response = SecurityHeaders.add_security_headers(response)

        await send({
            "type": "http.response.start",
            "status": 429,
            "headers": [
                [key.encode(), value.encode()] for key, value in response.headers.items()
            ],
        })

        await send({
            "type": "http.response.body",
            "body": response.body.encode(),
        })

# Utility functions for security
def setup_cors(app):
    """Setup CORS with security best practices"""
    allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[origin.strip() for origin in allowed_origins],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-RateLimit-*"],
    )

def create_csrf_token():
    """Create CSRF token for forms"""
    csrf = CSRFProtection()
    return csrf.generate_token()

def validate_api_key(api_key: str) -> bool:
    """Validate API key (placeholder implementation)"""
    valid_keys = os.getenv("VALID_API_KEYS", "").split(",") if os.getenv("VALID_API_KEYS") else []
    return api_key in [key.strip() for key in valid_keys if key.strip()]

def encrypt_sensitive_data(data: str) -> str:
    """Encrypt sensitive data (placeholder implementation)"""
    # In production, use proper encryption
    import hashlib
    return hashlib.sha256(f"{data}{os.getenv('ENCRYPTION_KEY', 'default')}".encode()).hexdigest()

def mask_sensitive_data(data: str, mask_char: str = "*", visible_chars: int = 4) -> str:
    """Mask sensitive data for logging"""
    if not data or len(data) <= visible_chars:
        return mask_char * len(data)

    return data[:visible_chars] + mask_char * (len(data) - visible_chars)

# Security monitoring
class SecurityMonitor:
    """Monitor security events"""

    def __init__(self):
        self.events = deque(maxlen=1000)
        self.suspicious_patterns = {
            'multiple_failed_logins': 5,
            'rapid_api_calls': 100,
            'suspicious_user_agents': 10
        }

    def log_security_event(self, event_type: str, details: Dict[str, Any]):
        """Log security event"""
        event = {
            'timestamp': datetime.utcnow().isoformat(),
            'type': event_type,
            'details': details,
            'severity': self._get_event_severity(event_type, details)
        }

        self.events.append(event)

        # Log to file if severe
        if event['severity'] in ['HIGH', 'CRITICAL']:
            logger.warning(f"Security Event: {event_type} - {details}")

    def _get_event_severity(self, event_type: str, details: Dict[str, Any]) -> str:
        """Determine event severity"""
        if 'failed_login' in event_type and details.get('attempts', 0) > 5:
            return 'HIGH'
        elif 'rate_limit' in event_type:
            return 'MEDIUM'
        elif 'csrf' in event_type:
            return 'HIGH'
        else:
            return 'LOW'

    def get_recent_events(self, minutes: int = 60) -> List[Dict[str, Any]]:
        """Get recent security events"""
        cutoff = datetime.utcnow() - timedelta(minutes=minutes)
        return [
            event for event in self.events
            if datetime.fromisoformat(event['timestamp']) >= cutoff
        ]

# Global security monitor
security_monitor = SecurityMonitor()