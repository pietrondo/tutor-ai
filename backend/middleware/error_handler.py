"""
Centralized Error Handling System for CLE API
Standardized error responses with proper HTTP status codes
"""

from typing import Dict, Any, Optional, Union
from datetime import datetime
from enum import Enum
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from pydantic import ValidationError
import traceback
import logging

# Set up logging
logger = logging.getLogger(__name__)

class ErrorCategory(str, Enum):
    """Categories of errors for better client handling"""
    VALIDATION = "validation"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    NOT_FOUND = "not_found"
    BUSINESS_LOGIC = "business_logic"
    EXTERNAL_SERVICE = "external_service"
    SYSTEM = "system"
    RATE_LIMIT = "rate_limit"

class CLEError(Exception):
    """Base error class for CLE application"""

    def __init__(
        self,
        message: str,
        category: ErrorCategory = ErrorCategory.SYSTEM,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None,
        error_code: Optional[str] = None,
        request_id: Optional[str] = None
    ):
        self.message = message
        self.category = category
        self.status_code = status_code
        self.details = details or {}
        self.error_code = error_code
        self.request_id = request_id
        super().__init__(self.message)

class ValidationError(CLEError):
    """Validation related errors"""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        error_code: Optional[str] = None
    ):
        super().__init__(
            message=message,
            category=ErrorCategory.VALIDATION,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details,
            error_code=error_code or "VALIDATION_ERROR"
        )

class AuthenticationError(CLEError):
    """Authentication related errors"""

    def __init__(
        self,
        message: str = "Authentication failed",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            category=ErrorCategory.AUTHENTICATION,
            status_code=status.HTTP_401_UNAUTHORIZED,
            details=details,
            error_code="AUTHENTICATION_ERROR"
        )

class AuthorizationError(CLEError):
    """Authorization related errors"""

    def __init__(
        self,
        message: str = "Access forbidden",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            category=ErrorCategory.AUTHORIZATION,
            status_code=status.HTTP_403_FORBIDDEN,
            details=details,
            error_code="AUTHORIZATION_ERROR"
        )

class NotFoundError(CLEError):
    """Resource not found errors"""

    def __init__(
        self,
        resource: str,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        message = f"{resource} not found"
        if resource_id:
            message += f" with ID: {resource_id}"

        super().__init__(
            message=message,
            category=ErrorCategory.NOT_FOUND,
            status_code=status.HTTP_404_NOT_FOUND,
            details=details,
            error_code="NOT_FOUND_ERROR"
        )

class BusinessLogicError(CLEError):
    """Business logic validation errors"""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        error_code: Optional[str] = None
    ):
        super().__init__(
            message=message,
            category=ErrorCategory.BUSINESS_LOGIC,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details,
            error_code=error_code or "BUSINESS_LOGIC_ERROR"
        )

class ExternalServiceError(CLEError):
    "External service integration errors"""

    def __init__(
        self,
        service_name: str,
        message: str = "External service error",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=f"{service_name}: {message}",
            category=ErrorCategory.EXTERNAL_SERVICE,
            status_code=status.HTTP_502_BAD_GATEWAY,
            details={**{"service": service_name}, **(details or {})},
            error_code="EXTERNAL_SERVICE_ERROR"
        )

class RateLimitError(CLEError):
    """Rate limiting errors"""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            category=ErrorCategory.RATE_LIMIT,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            details={**{"retry_after": retry_after}, **(details or {})},
            error_code="RATE_LIMIT_ERROR"
        )

class ErrorResponse:
    """Standardized error response structure"""

    @staticmethod
    def create(
        error: Union[CLEError, Exception],
        request_id: Optional[str] = None,
        include_traceback: bool = False
    ) -> Dict[str, Any]:
        """Create standardized error response"""

        # Handle different error types
        if isinstance(error, CLEError):
            return ErrorResponse._create_cle_error_response(error, request_id, include_traceback)
        elif isinstance(error, (HTTPException, StarletteHTTPException)):
            return ErrorResponse._create_http_error_response(error, request_id)
        elif isinstance(error, (ValidationError, RequestValidationError)):
            return ErrorResponse._create_validation_error_response(error, request_id)
        else:
            return ErrorResponse._create_generic_error_response(error, request_id, include_traceback)

    @staticmethod
    def _create_cle_error_response(
        error: CLEError,
        request_id: Optional[str],
        include_traceback: bool
    ) -> Dict[str, Any]:
        """Create response for CLE errors"""
        response = {
            "success": False,
            "error": {
                "category": error.category.value,
                "code": error.error_code,
                "message": error.message,
                "status_code": error.status_code
            },
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": request_id
        }

        if error.details:
            response["error"]["details"] = error.details

        if include_traceback:
            response["error"]["traceback"] = traceback.format_exc()

        return response

    @staticmethod
    def _create_http_error_response(
        error: Union[HTTPException, StarletteHTTPException],
        request_id: Optional[str]
    ) -> Dict[str, Any]:
        """Create response for HTTP exceptions"""
        return {
            "success": False,
            "error": {
                "category": "http",
                "code": f"HTTP_{error.status_code}",
                "message": error.detail,
                "status_code": error.status_code
            },
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": request_id
        }

    @staticmethod
    def _create_validation_error_response(
        error: Union[ValidationError, RequestValidationError],
        request_id: Optional[str]
    ) -> Dict[str, Any]:
        """Create response for validation errors"""
        details = {}

        if hasattr(error, 'errors'):
            # Pydantic/RequestValidationError
            details = {
                "validation_errors": error.errors(),
                "field_count": len(error.errors())
            }
        else:
            # Generic ValidationError
            details = {"validation_errors": [str(error)]}

        return {
            "success": False,
            "error": {
                "category": ErrorCategory.VALIDATION.value,
                "code": "VALIDATION_ERROR",
                "message": "Input validation failed",
                "status_code": status.HTTP_400_BAD_REQUEST,
                "details": details
            },
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": request_id
        }

    @staticmethod
    def _create_generic_error_response(
        error: Exception,
        request_id: Optional[str],
        include_traceback: bool
    ) -> Dict[str, Any]:
        """Create response for generic exceptions"""
        return {
            "success": False,
            "error": {
                "category": ErrorCategory.SYSTEM.value,
                "code": "INTERNAL_ERROR",
                "message": "An internal error occurred",
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR
            },
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": request_id,
            "include_traceback": include_traceback
        }

        if include_traceback:
            response["error"]["traceback"] = traceback.format_exc()

        return response

async def cle_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Global exception handler for CLE API"""

    # Get request ID for tracing
    request_id = getattr(request.state, "request_id", None)

    # Determine if we should include traceback (development only)
    include_traceback = False  # Set to True in development environment

    # Create standardized error response
    error_response = ErrorResponse.create(
        error=exc,
        request_id=request_id,
        include_traceback=include_traceback
    )

    # Determine status code
    if isinstance(exc, CLEError):
        status_code = exc.status_code
    elif isinstance(exc, (HTTPException, StarletteHTTPException)):
        status_code = exc.status_code
    elif isinstance(exc, (ValidationError, RequestValidationError)):
        status_code = status.HTTP_400_BAD_REQUEST
    else:
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    # Log the error
    logger.error(
        f"Request failed: {request.method} {request.url.path} - "
        f"{type(exc).__name__}: {str(exc)} - "
        f"Request ID: {request_id}"
    )

    return JSONResponse(
        status_code=status_code,
        content=error_response
    )

# Utility functions for common error scenarios
def raise_not_found(resource: str, resource_id: Optional[str] = None, details: Optional[Dict] = None):
    """Convenience function to raise not found error"""
    raise NotFoundError(resource=resource, resource_id=resource_id, details=details)

def raise_validation_error(message: str, details: Optional[Dict] = None):
    """Convenience function to raise validation error"""
    raise ValidationError(message=message, details=details)

def raise_business_logic_error(message: str, details: Optional[Dict] = None, error_code: Optional[str] = None):
    """Convenience function to raise business logic error"""
    raise BusinessLogicError(message=message, details=details, error_code=error_code)

def raise_external_service_error(service_name: str, message: str, details: Optional[Dict] = None):
    """Convenience function to raise external service error"""
    raise ExternalServiceError(service_name=service_name, message=message, details=details)

# Error response helpers for consistent responses
def create_error_response(
    category: ErrorCategory,
    message: str,
    status_code: int,
    error_code: Optional[str] = None,
    details: Optional[Dict] = None,
    request_id: Optional[str] = None
) -> Dict[str, Any]:
    """Helper to create error response without raising exception"""
    return ErrorResponse.create(
        error=CLEError(
            message=message,
            category=category,
            status_code=status_code,
            details=details,
            error_code=error_code
        ),
        request_id=request_id
    )

def create_success_response(
    data: Any = None,
    message: Optional[str] = None,
    request_id: Optional[str] = None
) -> Dict[str, Any]:
    """Helper to create standardized success response"""
    response = {
        "success": True,
        "timestamp": datetime.utcnow().isoformat(),
        "request_id": request_id
    }

    if data is not None:
        response["data"] = data

    if message:
        response["message"] = message

    return response