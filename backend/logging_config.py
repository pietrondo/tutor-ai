"""
Centralized logging configuration for Tutor-AI Backend.

This module provides comprehensive logging configuration with structured logging,
multiple output formats, log rotation, and environment-specific settings.

Features:
- Structured JSON logging with structlog
- Console and file output with different formats
- Log rotation and management
- Request correlation ID tracking
- Performance metrics logging
- Environment-specific log levels
- Sensitive data filtering
- Security event logging
"""

import os
import sys
import logging
import logging.handlers
from pathlib import Path
from typing import Any, Dict, Optional
from datetime import datetime
import json
import structlog
from structlog.stdlib import LoggerFactory
import uuid


class SensitiveDataFilter:
    """Filter to mask sensitive information in logs."""

    SENSITIVE_PATTERNS = [
        'api_key', 'password', 'token', 'secret', 'key', 'auth',
        'authorization', 'bearer', 'credential', 'private'
    ]

    def __init__(self, names: Optional[list] = None):
        self.sensitive_patterns = self.SENSITIVE_PATTERNS + (names or [])

    def filter_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively filter sensitive data from dictionaries."""
        if not isinstance(data, dict):
            return data

        filtered = {}
        for key, value in data.items():
            key_lower = key.lower()
            if any(pattern in key_lower for pattern in self.sensitive_patterns):
                filtered[key] = '***REDACTED***'
            elif isinstance(value, dict):
                filtered[key] = self.filter_dict(value)
            elif isinstance(value, list):
                filtered[key] = [
                    self.filter_dict(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                filtered[key] = value
        return filtered


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter with additional context."""

    def __init__(self, service_name: str = "tutor-ai-backend"):
        super().__init__()
        self.service_name = service_name
        self.sensitive_filter = SensitiveDataFilter()

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON with additional context."""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'service': self.service_name,
            'environment': os.getenv('ENVIRONMENT', 'development'),
            'process_id': os.getpid(),
            'thread_id': record.thread,
        }

        # Add exception information if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)

        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in {
                'name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                'filename', 'module', 'lineno', 'funcName', 'created',
                'msecs', 'relativeCreated', 'thread', 'threadName',
                'processName', 'process', 'getMessage', 'exc_info',
                'exc_text', 'stack_info'
            }:
                log_entry[key] = value

        # Filter sensitive data
        log_entry = self.sensitive_filter.filter_dict(log_entry)

        return json.dumps(log_entry, default=str, ensure_ascii=False)


class CorrelationIDFilter(logging.Filter):
    """Filter to add correlation IDs to log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        """Add correlation ID to log record."""
        # Get correlation ID from context or create new one
        correlation_id = getattr(record, 'correlation_id', None)
        if not correlation_id:
            correlation_id = str(uuid.uuid4())[:8]

        record.correlation_id = correlation_id
        return True


def setup_logging(
    log_level: str = None,
    log_dir: str = None,
    service_name: str = "tutor-ai-backend",
    enable_console: bool = True,
    enable_file: bool = True,
    max_file_size: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> None:
    """
    Setup centralized logging configuration.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory for log files
        service_name: Name of the service for log identification
        enable_console: Enable console output
        enable_file: Enable file output
        max_file_size: Maximum file size before rotation
        backup_count: Number of backup files to keep
    """

    # Determine log level
    if log_level is None:
        log_level = os.getenv('LOG_LEVEL', 'DEBUG' if os.getenv('ENVIRONMENT') == 'development' else 'INFO')

    # Create log directory
    if log_dir is None:
        log_dir = os.getenv('LOG_DIR', './logs')

    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))

    # Clear existing handlers
    root_logger.handlers.clear()

    # Create correlation ID filter
    correlation_filter = CorrelationIDFilter()

    # Console handler with readable format
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, log_level.upper()))

        # Console formatter - more readable for development
        console_formatter = logging.Formatter(
            fmt='%(asctime)s | %(levelname)8s | %(correlation_id)s | %(name)s:%(funcName)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        console_handler.addFilter(correlation_filter)
        root_logger.addHandler(console_handler)

    # File handler with JSON format
    if enable_file:
        # Main application log
        app_log_file = log_path / f"{service_name}.log"
        file_handler = logging.handlers.RotatingFileHandler(
            filename=app_log_file,
            maxBytes=max_file_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(getattr(logging, log_level.upper()))
        file_handler.setFormatter(JSONFormatter(service_name))
        file_handler.addFilter(correlation_filter)
        root_logger.addHandler(file_handler)

        # Error log file
        error_log_file = log_path / f"{service_name}-errors.log"
        error_handler = logging.handlers.RotatingFileHandler(
            filename=error_log_file,
            maxBytes=max_file_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(JSONFormatter(service_name))
        error_handler.addFilter(correlation_filter)
        root_logger.addHandler(error_handler)

        # Security events log
        security_log_file = log_path / f"{service_name}-security.log"
        security_handler = logging.handlers.RotatingFileHandler(
            filename=security_log_file,
            maxBytes=max_file_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        security_handler.setLevel(logging.INFO)
        security_handler.setFormatter(JSONFormatter(service_name))
        security_handler.addFilter(correlation_filter)

        # Create security logger
        security_logger = logging.getLogger('security')
        security_logger.addHandler(security_handler)
        security_logger.setLevel(logging.INFO)
        security_logger.propagate = False  # Don't propagate to root logger

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        context_class=dict,
        logger_factory=LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Log startup message
    logger = logging.getLogger(__name__)
    logger.info(
        "Logging system initialized",
        extra={
            'log_level': log_level,
            'log_directory': str(log_path),
            'service_name': service_name,
            'environment': os.getenv('ENVIRONMENT', 'development'),
            'console_output': enable_console,
            'file_output': enable_file
        }
    )


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)


def get_structlog_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    Get a structlog logger instance with the specified name.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Structlog logger instance
    """
    return structlog.get_logger(name)


class RequestLogger:
    """Utility class for logging HTTP requests and responses."""

    def __init__(self, logger_name: str = "http"):
        self.logger = logging.getLogger(logger_name)

    def log_request(
        self,
        method: str,
        path: str,
        headers: Dict[str, str],
        body: Optional[str] = None,
        correlation_id: Optional[str] = None
    ) -> None:
        """Log incoming HTTP request."""
        self.logger.info(
            f"HTTP {method} {path}",
            extra={
                'event_type': 'http_request',
                'method': method,
                'path': path,
                'headers': {k: v for k, v in headers.items() if k.lower() not in ['authorization']},
                'body_size': len(body) if body else 0,
                'correlation_id': correlation_id
            }
        )

    def log_response(
        self,
        method: str,
        path: str,
        status_code: int,
        response_size: int,
        duration_ms: float,
        correlation_id: Optional[str] = None
    ) -> None:
        """Log HTTP response."""
        level = logging.ERROR if status_code >= 500 else logging.WARNING if status_code >= 400 else logging.INFO

        self.logger.log(
            level,
            f"HTTP {method} {path} - {status_code} - {duration_ms:.2f}ms",
            extra={
                'event_type': 'http_response',
                'method': method,
                'path': path,
                'status_code': status_code,
                'response_size': response_size,
                'duration_ms': duration_ms,
                'correlation_id': correlation_id
            }
        )


class SecurityLogger:
    """Utility class for logging security events."""

    def __init__(self):
        self.logger = logging.getLogger('security')

    def log_authentication_attempt(
        self,
        username: Optional[str],
        success: bool,
        ip_address: str,
        user_agent: Optional[str] = None
    ) -> None:
        """Log authentication attempt."""
        self.logger.info(
            f"Authentication attempt: {'SUCCESS' if success else 'FAILED'}",
            extra={
                'event_type': 'authentication',
                'username': username,
                'success': success,
                'ip_address': ip_address,
                'user_agent': user_agent
            }
        )

    def log_authorization_failure(
        self,
        user_id: Optional[str],
        resource: str,
        action: str,
        ip_address: str
    ) -> None:
        """Log authorization failure."""
        self.logger.warning(
            f"Authorization failure: {action} on {resource}",
            extra={
                'event_type': 'authorization_failure',
                'user_id': user_id,
                'resource': resource,
                'action': action,
                'ip_address': ip_address
            }
        )

    def log_security_event(
        self,
        event_type: str,
        description: str,
        severity: str = 'INFO',
        **kwargs
    ) -> None:
        """Log generic security event."""
        self.logger.info(
            f"Security event: {event_type} - {description}",
            extra={
                'event_type': f"security_{event_type}",
                'severity': severity,
                **kwargs
            }
        )


# Performance monitoring utility
class PerformanceLogger:
    """Utility class for logging performance metrics."""

    def __init__(self, logger_name: str = "performance"):
        self.logger = logging.getLogger(logger_name)

    def log_operation_time(
        self,
        operation: str,
        duration_ms: float,
        success: bool = True,
        **metadata
    ) -> None:
        """Log operation execution time."""
        level = logging.INFO if success else logging.WARNING

        self.logger.log(
            level,
            f"Operation '{operation}' completed in {duration_ms:.2f}ms",
            extra={
                'event_type': 'performance',
                'operation': operation,
                'duration_ms': duration_ms,
                'success': success,
                **metadata
            }
        )

    def log_database_query(
        self,
        query_type: str,
        table: str,
        duration_ms: float,
        row_count: Optional[int] = None
    ) -> None:
        """Log database query performance."""
        self.logger.debug(
            f"DB Query: {query_type} on {table} - {duration_ms:.2f}ms",
            extra={
                'event_type': 'database_query',
                'query_type': query_type,
                'table': table,
                'duration_ms': duration_ms,
                'row_count': row_count
            }
        )


# Context manager for timing operations
class LoggedTimer:
    """Context manager for timing operations with automatic logging."""

    def __init__(
        self,
        operation: str,
        logger: Optional[logging.Logger] = None,
        log_level: int = logging.INFO,
        **metadata
    ):
        self.operation = operation
        self.logger = logger or logging.getLogger('performance')
        self.log_level = log_level
        self.metadata = metadata
        self.start_time = None

    def __enter__(self):
        import time
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        import time
        if self.start_time:
            duration_ms = (time.time() - self.start_time) * 1000
            success = exc_type is None

            self.logger.log(
                self.log_level if success else logging.WARNING,
                f"Operation '{self.operation}' {'completed' if success else 'failed'} in {duration_ms:.2f}ms",
                extra={
                    'event_type': 'performance',
                    'operation': self.operation,
                    'duration_ms': duration_ms,
                    'success': success,
                    **self.metadata
                }
            )


# Initialize logging when module is imported
if not logging.getLogger().handlers:
    setup_logging()