"""
Security utilities for the Tutor AI system.
Provides input validation, file sanitization, and security helpers.
"""

import os
import re
import hashlib
import mimetypes
from pathlib import Path
from typing import Optional, List, Set
import logging

logger = logging.getLogger(__name__)

class SecurityConfig:
    """Security configuration constants."""
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    ALLOWED_EXTENSIONS = {'.pdf', '.docx', '.pptx', '.txt', '.md'}
    ALLOWED_MIME_TYPES = {
        'application/pdf',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        'text/plain',
        'text/markdown'
    }
    MAX_FILENAME_LENGTH = 255
    FORBIDDEN_NAMES = {
        'CON', 'PRN', 'AUX', 'NUL',
        'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
        'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
    }
    SAFE_FILENAME_PATTERN = re.compile(r'^[a-zA-Z0-9._-]+$')

def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename to prevent directory traversal and injection attacks.

    Args:
        filename: Original filename

    Returns:
        Sanitized safe filename

    Raises:
        ValueError: If filename is invalid or dangerous
    """
    if not filename or not isinstance(filename, str):
        raise ValueError("Filename must be a non-empty string")

    # Remove path separators and dangerous characters
    filename = os.path.basename(filename)

    # Check for forbidden names (Windows reserved names)
    name_without_ext = os.path.splitext(filename)[0].upper()
    if name_without_ext in SecurityConfig.FORBIDDEN_NAMES:
        raise ValueError(f"Filename '{filename}' uses a reserved name")

    # Check length
    if len(filename) > SecurityConfig.MAX_FILENAME_LENGTH:
        raise ValueError(f"Filename too long (max {SecurityConfig.MAX_FILENAME_LENGTH} characters)")

    # Remove dangerous characters
    # Keep only alphanumeric, dots, hyphens, and underscores
    safe_name = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)

    # Ensure filename doesn't start with a dot or dash
    if safe_name.startswith(('.', '-')):
        safe_name = '_' + safe_name[1:]

    # Ensure it's not empty after sanitization
    if not safe_name or safe_name == '_' * len(safe_name):
        raise ValueError("Filename becomes invalid after sanitization")

    # Limit consecutive dots/dashes/underscores
    safe_name = re.sub(r'[._-]{2,}', '_', safe_name)

    return safe_name

def validate_file_path(file_path: str, base_path: str = "data") -> str:
    """
    Validate that a file path is safe and within allowed directories.

    Args:
        file_path: The file path to validate
        base_path: Base directory that files should be within

    Returns:
        Absolute, safe file path

    Raises:
        ValueError: If path is invalid or outside allowed directories
    """
    if not file_path or not isinstance(file_path, str):
        raise ValueError("File path must be a non-empty string")

    try:
        # Get absolute paths
        base_abs = os.path.abspath(base_path)
        file_abs = os.path.abspath(file_path)

        # Ensure the file path is within the base path
        if not file_abs.startswith(base_abs):
            raise ValueError("File path is outside allowed directory")

        # Check for symlink attacks
        if os.path.islink(file_path):
            target = os.path.realpath(file_path)
            if not target.startswith(base_abs):
                raise ValueError("Symlink target is outside allowed directory")

        return file_abs

    except (OSError, ValueError) as e:
        logger.error(f"Path validation error for {file_path}: {e}")
        raise ValueError(f"Invalid file path: {e}")

def validate_file_upload(filename: str, file_size: int, mime_type: str) -> bool:
    """
    Validate an uploaded file for security constraints.

    Args:
        filename: Original filename
        file_size: File size in bytes
        mime_type: MIME type of the file

    Returns:
        True if file passes all validations

    Raises:
        ValueError: If file fails validation
    """
    # Check file size
    if file_size > SecurityConfig.MAX_FILE_SIZE:
        raise ValueError(f"File too large (max {SecurityConfig.MAX_FILE_SIZE // (1024*1024)}MB)")

    if file_size <= 0:
        raise ValueError("File size must be greater than 0")

    # Check filename
    safe_filename(filename)  # Will raise ValueError if invalid

    # Check file extension
    file_ext = os.path.splitext(filename)[1].lower()
    if file_ext not in SecurityConfig.ALLOWED_EXTENSIONS:
        raise ValueError(f"File extension '{file_ext}' not allowed")

    # Check MIME type
    if mime_type not in SecurityConfig.ALLOWED_MIME_TYPES:
        raise ValueError(f"MIME type '{mime_type}' not allowed")

    # Check consistency between extension and MIME type
    expected_mime = mimetypes.guess_type(filename)[0]
    if expected_mime and expected_mime != mime_type:
        logger.warning(f"MIME type mismatch for {filename}: expected {expected_mime}, got {mime_type}")

    return True

def generate_safe_filename(original_filename: str, prefix: str = "", suffix: str = "") -> str:
    """
    Generate a safe filename with optional prefix and suffix.

    Args:
        original_filename: Original filename
        prefix: Optional prefix to add
        suffix: Optional suffix to add before extension

    Returns:
        Safe generated filename
    """
    # Sanitize original filename
    safe_name = sanitize_filename(original_filename)

    # Split name and extension
    name, ext = os.path.splitext(safe_name)

    # Add timestamp hash for uniqueness
    timestamp_hash = hashlib.md5(
        f"{original_filename}{os.urandom(8)}".encode()
    ).hexdigest()[:8]

    # Build new filename
    parts = []
    if prefix:
        parts.append(prefix.strip('_-'))
    parts.append(name)
    if suffix:
        parts.append(suffix.strip('_-'))
    parts.append(timestamp_hash)

    new_name = '_'.join(parts) + ext
    return new_name

def sanitize_user_input(text: str, max_length: int = 10000) -> str:
    """
    Sanitize user text input to prevent injection attacks.

    Args:
        text: User input text
        max_length: Maximum allowed length

    Returns:
        Sanitized text

    Raises:
        ValueError: If input is invalid
    """
    if not isinstance(text, str):
        raise ValueError("Input must be a string")

    if len(text) > max_length:
        raise ValueError(f"Input too long (max {max_length} characters)")

    # Remove potentially dangerous characters for system commands
    # Keep most characters but remove control chars and dangerous symbols
    sanitized = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)

    # Normalize whitespace
    sanitized = ' '.join(sanitized.split())

    return sanitized.strip()

def validate_pdf_content(file_path: str) -> bool:
    """
    Validate that a file is actually a PDF by checking its content.

    Args:
        file_path: Path to the file

    Returns:
        True if file is a valid PDF

    Raises:
        ValueError: If file is not a valid PDF
    """
    try:
        with open(file_path, 'rb') as f:
            header = f.read(5)

        # PDF files must start with %PDF-
        if not header.startswith(b'%PDF-'):
            raise ValueError("File does not have valid PDF header")

        return True

    except (OSError, IOError) as e:
        logger.error(f"Error reading file {file_path}: {e}")
        raise ValueError(f"Cannot read file: {e}")

class SecurityLogger:
    """Enhanced security logger for monitoring suspicious activities."""

    @staticmethod
    def log_suspicious_activity(activity: str, details: dict, ip_address: str = None):
        """Log suspicious security-related activity."""
        warning_msg = f"SUSPICIOUS ACTIVITY: {activity}"
        if ip_address:
            warning_msg += f" from IP: {ip_address}"
        warning_msg += f" - Details: {details}"
        logger.warning(warning_msg)

    @staticmethod
    def log_file_access(filename: str, user_id: str = None, action: str = "access"):
        """Log file access for audit trail."""
        info_msg = f"FILE {action.upper()}: {filename}"
        if user_id:
            info_msg += f" by user: {user_id}"
        logger.info(info_msg)

def rate_limit_check(identifier: str, limit: int = 100, window: int = 60) -> bool:
    """
    Simple in-memory rate limiting check.

    Args:
        identifier: Unique identifier (IP, user ID, etc.)
        limit: Maximum requests allowed
        window: Time window in seconds

    Returns:
        True if request is allowed
    """
    # Trusted identifiers (local development/IPs) bypass
    TRUSTED_IDENTIFIERS = {"127.0.0.1", "::1", "172.18.0.1"}
    if identifier in TRUSTED_IDENTIFIERS:
        return True

    # This is a simple implementation - in production, use Redis or similar
    from datetime import datetime, timedelta
    import time

    # Store request timestamps (this would be Redis in production)
    if not hasattr(rate_limit_check, '_requests'):
        rate_limit_check._requests = {}

    now = time.time()
    window_start = now - window

    # Clean old requests and add new one
    if identifier not in rate_limit_check._requests:
        rate_limit_check._requests[identifier] = []

    # Remove old requests outside the window
    rate_limit_check._requests[identifier] = [
        req_time for req_time in rate_limit_check._requests[identifier]
        if req_time > window_start
    ]

    # Check if limit exceeded
    if len(rate_limit_check._requests[identifier]) >= limit:
        SecurityLogger.log_suspicious_activity(
            "Rate limit exceeded",
            {"identifier": identifier, "requests": len(rate_limit_check._requests[identifier])}
        )
        return False

    # Add current request
    rate_limit_check._requests[identifier].append(now)
    return True
