"""
Custom exceptions and centralized error handling for the Tutor AI system.
"""

import logging
import traceback
from typing import Optional, Dict, Any, List
from fastapi import HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class BaseTutorError(Exception):
    """Base exception for all Tutor AI specific errors."""

    def __init__(
        self,
        message: str,
        error_code: str = None,
        details: Dict[str, Any] = None,
        cause: Exception = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        self.cause = cause
        logger.error(f"{self.error_code}: {message} - Details: {details}")

class ValidationError(BaseTutorError):
    """Raised when input validation fails."""
    pass

class FileNotFoundError(BaseTutorError):
    """Raised when a required file is not found."""
    pass

class FileOperationError(BaseTutorError):
    """Raised when file operations fail."""
    pass

class OCRProcessingError(BaseTutorError):
    """Raised when OCR processing fails."""
    pass

class LLMServiceError(BaseTutorError):
    """Raised when LLM service operations fail."""
    pass

class RAGProcessingError(BaseTutorError):
    """Raised when RAG processing fails."""
    pass

class DatabaseError(BaseTutorError):
    """Raised when database operations fail."""
    pass

class AuthenticationError(BaseTutorError):
    """Raised when authentication fails."""
    pass

class AuthorizationError(BaseTutorError):
    """Raised when authorization fails."""
    pass

class RateLimitError(BaseTutorError):
    """Raised when rate limits are exceeded."""
    pass

class SecurityError(BaseTutorError):
    """Raised when security validation fails."""
    pass

class ConfigurationError(BaseTutorError):
    """Raised when configuration is invalid."""
    pass

class NetworkError(BaseTutorError):
    """Raised when network operations fail."""
    pass

class TimeoutError(BaseTutorError):
    """Raised when operations timeout."""
    pass

class ResourceExhaustedError(BaseTutorError):
    """Raised when system resources are exhausted."""
    pass

class ServiceUnavailableError(BaseTutorError):
    """Raised when external services are unavailable."""
    pass

class APIError(BaseModel):
    """Standardized API error response model."""
    error_code: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: Optional[str] = None
    request_id: Optional[str] = None

class ErrorHandler:
    """Centralized error handling utility."""

    @staticmethod
    def handle_error(error: Exception, context: str = None) -> HTTPException:
        """
        Convert any exception to an appropriate HTTPException.

        Args:
            error: The exception to handle
            context: Additional context about where the error occurred

        Returns:
            HTTPException with appropriate status code and details
        """
        error_details = {
            "exception_type": type(error).__name__,
            "context": context
        }

        if isinstance(error, BaseTutorError):
            status_code = ErrorHandler._get_status_code_for_error(error)
            error_details.update(error.details)

            return HTTPException(
                status_code=status_code,
                detail={
                    "error_code": error.error_code,
                    "message": error.message,
                    "details": error_details
                }
            )

        elif isinstance(error, FileNotFoundError):
            return HTTPException(
                status_code=404,
                detail={
                    "error_code": "FILE_NOT_FOUND",
                    "message": "The requested file was not found",
                    "details": error_details
                }
            )

        elif isinstance(error, PermissionError):
            return HTTPException(
                status_code=403,
                detail={
                    "error_code": "PERMISSION_DENIED",
                    "message": "Permission denied to access the requested resource",
                    "details": error_details
                }
            )

        elif isinstance(error, ValueError):
            return HTTPException(
                status_code=400,
                detail={
                    "error_code": "INVALID_INPUT",
                    "message": str(error),
                    "details": error_details
                }
            )

        elif isinstance(error, TimeoutError):
            return HTTPException(
                status_code=408,
                detail={
                    "error_code": "TIMEOUT",
                    "message": "Operation timed out",
                    "details": error_details
                }
            )

        elif isinstance(error, ConnectionError):
            return HTTPException(
                status_code=503,
                detail={
                    "error_code": "CONNECTION_ERROR",
                    "message": "Failed to connect to external service",
                    "details": error_details
                }
            )

        else:
            # Log the full traceback for unexpected errors
            logger.error(f"Unexpected error in {context}: {error}")
            logger.error(f"Traceback: {traceback.format_exc()}")

            return HTTPException(
                status_code=500,
                detail={
                    "error_code": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected error occurred",
                    "details": error_details
                }
            )

    @staticmethod
    def _get_status_code_for_error(error: BaseTutorError) -> int:
        """Map custom errors to HTTP status codes."""
        status_mapping = {
            ValidationError: 400,
            AuthenticationError: 401,
            AuthorizationError: 403,
            FileNotFoundError: 404,
            RateLimitError: 429,
            TimeoutError: 408,
            ServiceUnavailableError: 503,
            NetworkError: 503,
            ResourceExhaustedError: 507,
            DatabaseError: 500,
            FileOperationError: 500,
            OCRProcessingError: 500,
            LLMServiceError: 502,
            RAGProcessingError: 500,
            ConfigurationError: 500
        }

        return status_mapping.get(type(error), 500)

class ErrorCollector:
    """Collects and manages multiple errors during batch operations."""

    def __init__(self):
        self.errors: List[Dict[str, Any]] = []
        self.warnings: List[Dict[str, Any]] = []

    def add_error(self, error: Exception, context: str = None, item_id: str = None):
        """Add an error to the collection."""
        error_data = {
            "error_code": getattr(error, 'error_code', type(error).__name__),
            "message": str(error),
            "context": context,
            "item_id": item_id
        }
        self.errors.append(error_data)
        logger.error(f"Collected error: {error_data}")

    def add_warning(self, message: str, context: str = None, item_id: str = None):
        """Add a warning to the collection."""
        warning_data = {
            "message": message,
            "context": context,
            "item_id": item_id
        }
        self.warnings.append(warning_data)
        logger.warning(f"Collected warning: {warning_data}")

    def has_errors(self) -> bool:
        """Check if any errors have been collected."""
        return len(self.errors) > 0

    def has_warnings(self) -> bool:
        """Check if any warnings have been collected."""
        return len(self.warnings) > 0

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of collected errors and warnings."""
        return {
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "errors": self.errors,
            "warnings": self.warnings
        }

    def raise_if_has_errors(self, context: str = None):
        """Raise an exception if errors exist."""
        if self.has_errors():
            message = f"{len(self.errors)} errors occurred"
            if context:
                message += f" during {context}"
            raise BaseTutorError(
                message=message,
                error_code="BATCH_OPERATION_FAILED",
                details=self.get_summary()
            )

def safe_execute(func, default_value=None, error_context: str = None):
    """
    Safely execute a function and handle any exceptions.

    Args:
        func: Function to execute
        default_value: Value to return if function fails
        error_context: Context for error logging

    Returns:
        Function result or default_value
    """
    try:
        return func()
    except Exception as e:
        logger.error(f"Error in {error_context or 'safe_execute'}: {e}")
        if default_value is not None:
            return default_value
        raise

async def safe_execute_async(func, default_value=None, error_context: str = None):
    """
    Safely execute an async function and handle any exceptions.

    Args:
        func: Async function to execute
        default_value: Value to return if function fails
        error_context: Context for error logging

    Returns:
        Function result or default_value
    """
    try:
        return await func()
    except Exception as e:
        logger.error(f"Error in {error_context or 'safe_execute_async'}: {e}")
        if default_value is not None:
            return default_value
        raise

class RetryHandler:
    """Handles retry logic for transient failures."""

    @staticmethod
    def retry_with_backoff(
        func,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        backoff_factor: float = 2.0,
        exceptions: tuple = (ConnectionError, TimeoutError)
    ):
        """
        Retry a function with exponential backoff.

        Args:
            func: Function to retry
            max_retries: Maximum number of retry attempts
            base_delay: Initial delay between retries
            max_delay: Maximum delay between retries
            backoff_factor: Multiplier for delay after each retry
            exceptions: Exception types that trigger a retry

        Returns:
            Function result if successful

        Raises:
            Last exception if all retries fail
        """
        import time

        last_exception = None
        for attempt in range(max_retries + 1):
            try:
                return func()
            except exceptions as e:
                last_exception = e
                if attempt == max_retries:
                    logger.error(f"Max retries ({max_retries}) exceeded for {func.__name__}")
                    raise

                delay = min(base_delay * (backoff_factor ** attempt), max_delay)
                logger.warning(f"Retry {attempt + 1}/{max_retries} for {func.__name__} after {delay}s delay: {e}")
                time.sleep(delay)
            except Exception as e:
                # Don't retry on non-transient exceptions
                raise

        if last_exception:
            raise last_exception