"""
Enhanced Centralized Error Handling for Tutor AI
Provides consistent error responses, advanced logging, and analytics
"""

import logging
import traceback
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from pydantic import ValidationError
import sqlite3
import os
import json

# Enhanced logging imports
try:
    from logging_config import get_logger, get_structlog_logger, SecurityLogger, PerformanceLogger
except ImportError:
    try:
        # Try importing from backend directory for production mode
        from backend.logging_config import get_logger, get_structlog_logger, SecurityLogger, PerformanceLogger
    except ImportError:
        # Fallback if logging_config is not available
        import logging
        get_logger = lambda name: logging.getLogger(name)
        get_structlog_logger = lambda name: logging.getLogger(name)
        SecurityLogger = lambda: None
        PerformanceLogger = lambda: None

# Setup enhanced logging
logger = get_structlog_logger("error_handlers")
security_logger = SecurityLogger()
performance_logger = PerformanceLogger()

class TutorAIException(Exception):
    """Base exception for Tutor AI application"""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code: str = "INTERNAL_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)

class ValidationException(TutorAIException):
    """Exception for validation errors"""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="VALIDATION_ERROR",
            details=details
        )

# Authentication/Authorization exceptions removed for local setup

class NotFoundException(TutorAIException):
    """Exception for resource not found errors"""

    def __init__(self, resource: str, identifier: str = ""):
        message = f"{resource} not found"
        if identifier:
            message += f" with identifier: {identifier}"
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="NOT_FOUND"
        )

class ConflictException(TutorAIException):
    """Exception for conflict errors"""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            error_code="CONFLICT_ERROR",
            details=details
        )

class RateLimitException(TutorAIException):
    """Exception for rate limiting errors"""

    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(
            message=message,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            error_code="RATE_LIMIT_EXCEEDED"
        )

class DatabaseException(TutorAIException):
    """Exception for database errors"""

    def __init__(self, message: str, operation: str = ""):
        super().__init__(
            message=f"Database error: {message}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="DATABASE_ERROR",
            details={"operation": operation}
        )

class EnhancedSlideGeneratorError(TutorAIException):
    """Exception for enhanced slide generation errors"""

    def __init__(self, message: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"Enhanced slide generation error: {message}",
            status_code=status_code,
            error_code="ENHANCED_SLIDE_GENERATION_ERROR",
            details=details or {}
        )

class ExternalServiceException(TutorAIException):
    """Exception for external service errors"""

    def __init__(self, service: str, message: str):
        super().__init__(
            message=f"{service} service error: {message}",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            error_code="EXTERNAL_SERVICE_ERROR",
            details={"service": service}
        )

class ErrorHandler:
    """Enhanced centralized error handler with analytics and logging"""

    def __init__(self):
        self.error_log_path = os.getenv("ERROR_LOG_PATH", "data/error_logs.db")

        # Enhanced logging setup
        self.logger = get_structlog_logger("ErrorHandler")
        self.security_logger = SecurityLogger()

        # Error tracking for analytics
        self.error_counts: Dict[str, int] = {}
        self.error_rates: Dict[str, float] = {}
        self.last_error_reset = datetime.now()

        # Security tracking
        self.suspicious_activity: Dict[str, int] = {}

        self.logger.info(
            "ErrorHandler initialization started",
            extra={
                "error_log_path": self.error_log_path,
                "enhanced_features": ["analytics", "security_tracking", "performance_monitoring"]
            }
        )

        self.init_error_database()

        self.logger.info(
            "ErrorHandler initialization completed",
            extra={
                "database_ready": True,
                "security_tracking_enabled": True,
                "analytics_enabled": True
            }
        )

    def init_error_database(self):
        """Initialize error logging database"""
        os.makedirs(os.path.dirname(self.error_log_path), exist_ok=True)

        with sqlite3.connect(self.error_log_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS error_logs (
                    id TEXT PRIMARY KEY,
                    error_type TEXT NOT NULL,
                    error_code TEXT NOT NULL,
                    message TEXT NOT NULL,
                    details TEXT,
                    stack_trace TEXT,
                    request_path TEXT,
                    request_method TEXT,
                    user_id TEXT,
                    ip_address TEXT,
                    user_agent TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()

    def log_error(
        self,
        error: Exception,
        request: Optional[Request] = None,
        user_id: Optional[str] = None
    ):
        """Log error to database"""
        error_id = str(uuid.uuid4())

        # Extract error details
        error_type = type(error).__name__
        error_code = getattr(error, 'error_code', 'UNKNOWN_ERROR')
        message = str(error)
        details = getattr(error, 'details', {})
        stack_trace = traceback.format_exc()

        # Extract request information
        request_path = None
        request_method = None
        ip_address = None
        user_agent = None

        if request:
            request_path = request.url.path
            request_method = request.method
            ip_address = request.client.host if request.client else None
            user_agent = request.headers.get("user-agent")

        with sqlite3.connect(self.error_log_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO error_logs (
                    id, error_type, error_code, message, details, stack_trace,
                    request_path, request_method, user_id, ip_address, user_agent
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                error_id, error_type, error_code, message,
                str(details), stack_trace, request_path, request_method,
                user_id, ip_address, user_agent
            ))
            conn.commit()

        # Also log to standard logging
        logger.error(
            f"Error {error_id}: {error_type} - {message}",
            extra={
                "error_id": error_id,
                "error_code": error_code,
                "details": details,
                "request_path": request_path,
                "user_id": user_id
            }
        )

        return error_id

    def create_error_response(
        self,
        error: Exception,
        request: Optional[Request] = None,
        include_details: bool = False
    ) -> JSONResponse:
        """Create standardized error response"""

        # Log the error
        error_id = self.log_error(error, request)

        # Determine status code and error code
        if isinstance(error, HTTPException):
            status_code = error.status_code
            error_code = f"HTTP_{status_code}"
            message = error.detail
        elif isinstance(error, TutorAIException):
            status_code = error.status_code
            error_code = error.error_code
            message = error.message
        else:
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            error_code = "INTERNAL_ERROR"
            message = "An unexpected error occurred"

        # Build response
        response_content = {
            "success": False,
            "error": {
                "code": error_code,
                "message": message,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "error_id": error_id
            }
        }

        # Include details in development or if explicitly requested
        if include_details or os.getenv("DEBUG", "false").lower() == "true":
            response_content["error"]["details"] = getattr(error, 'details', {})

        return JSONResponse(
            status_code=status_code,
            content=response_content
        )

    async def validation_exception_handler(self, request: Request, exc: RequestValidationError):
        """Handle FastAPI validation errors"""
        details = {
            "validation_errors": exc.errors(),
            "field_count": len(exc.errors())
        }

        error = ValidationException(
            message="Request validation failed",
            details=details
        )

        return self.create_error_response(error, request)

    async def http_exception_handler(self, request: Request, exc: HTTPException):
        """Handle HTTP exceptions"""
        return self.create_error_response(exc, request)

    async def general_exception_handler(self, request: Request, exc: Exception):
        """Handle general exceptions"""
        return self.create_error_response(exc, request)

    def get_error_statistics(self, days: int = 7) -> Dict[str, Any]:
        """Get error statistics for the last N days"""
        with sqlite3.connect(self.error_log_path) as conn:
            cursor = conn.cursor()

            # Total errors in period
            cursor.execute('''
                SELECT COUNT(*) FROM error_logs
                WHERE timestamp >= datetime('now', '-{} days')
            '''.format(days))
            total_errors = cursor.fetchone()[0]

            # Errors by type
            cursor.execute('''
                SELECT error_type, COUNT(*)
                FROM error_logs
                WHERE timestamp >= datetime('now', '-{} days')
                GROUP BY error_type
                ORDER BY COUNT(*) DESC
            '''.format(days))
            errors_by_type = dict(cursor.fetchall())

            # Errors by code
            cursor.execute('''
                SELECT error_code, COUNT(*)
                FROM error_logs
                WHERE timestamp >= datetime('now', '-{} days')
                GROUP BY error_code
                ORDER BY COUNT(*) DESC
                LIMIT 10
            '''.format(days))
            top_error_codes = dict(cursor.fetchall())

            # Recent errors
            cursor.execute('''
                SELECT error_type, error_code, message, timestamp
                FROM error_logs
                ORDER BY timestamp DESC
                LIMIT 10
            ''')
            recent_errors = [
                {
                    "type": row[0],
                    "code": row[1],
                    "message": row[2],
                    "timestamp": row[3]
                }
                for row in cursor.fetchall()
            ]

            return {
                "total_errors": total_errors,
                "errors_by_type": errors_by_type,
                "top_error_codes": top_error_codes,
                "recent_errors": recent_errors,
                "period_days": days
            }

# Global error handler instance
error_handler = ErrorHandler()

# Decorator for error handling in services
def handle_errors(service_name: str = "service"):
    """Decorator to handle errors in service methods"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except sqlite3.Error as e:
                raise DatabaseException(
                    message=str(e),
                    operation=f"{service_name}.{func.__name__}"
                )
            except ValidationError as e:
                raise ValidationException(
                    message=f"Validation error in {service_name}",
                    details={"validation_errors": e.errors()}
                )
            except TutorAIException:
                # Re-raise our custom exceptions
                raise
            except Exception as e:
                logger.error(f"Unexpected error in {service_name}.{func.__name__}: {str(e)}")
                raise TutorAIException(
                    message=f"An error occurred in {service_name}",
                    error_code="SERVICE_ERROR",
                    details={"service": service_name, "method": func.__name__}
                )
        return wrapper
    return decorator

# Utility function to create consistent success responses
def create_success_response(
    data: Any = None,
    message: str = "Operation successful",
    meta: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Create standardized success response"""
    response = {
        "success": True,
        "message": message,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    if data is not None:
        response["data"] = data

    if meta:
        response["meta"] = meta

    return response

# Utility function to validate environment configuration
def validate_config() -> List[str]:
    """Validate required environment configuration"""
    errors = []

    required_vars = [
        "JWT_SECRET_KEY",
        "DATABASE_PATH"
    ]

    for var in required_vars:
        if not os.getenv(var):
            errors.append(f"Missing required environment variable: {var}")

    # Validate optional but recommended vars
    recommended_vars = [
        "OPENAI_API_KEY",
        "ENVIRONMENT"
    ]

    for var in recommended_vars:
        if not os.getenv(var):
            logger.warning(f"Recommended environment variable not set: {var}")

    return errors