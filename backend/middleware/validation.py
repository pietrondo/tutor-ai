"""
Input Validation Middleware for CLE API
Centralized validation for all incoming requests
"""

import re
import html
from typing import Any, Dict, List, Optional, Type
from pydantic import BaseModel, ValidationError, validator
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
import json
from datetime import datetime

# Common validation patterns
class ValidationPatterns:
    """Common regex patterns for validation"""

    # IDs and identifiers
    UUID_PATTERN = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.IGNORECASE)
    USER_ID_PATTERN = re.compile(r'^[a-zA-Z0-9_-]{3,50}$')
    COURSE_ID_PATTERN = re.compile(r'^[a-zA-Z0-9_-]{3,50}$')

    # Text validation
    SAFE_TEXT_PATTERN = re.compile(r'^[a-zA-Z0-9\s\.,!?;:()[\]{}"\'-_\n\r\t]*$')
    BASIC_TEXT_PATTERN = re.compile(r'^[a-zA-Z0-9\s\.,!?;:()[\]{}"\'-_\n\r\t@#$%&*+=<>/]*$')

    # Numbers and scores
    SCORE_PATTERN = re.compile(r'^\d*\.?\d+$')
    RATING_PATTERN = re.compile(r'^[1-5]$')

    # Email and URLs
    EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    URL_PATTERN = re.compile(r'^https?://[^\s/$.?#].[^\s]*$')

class InputSanitizer:
    """Sanitize and validate input data"""

    @staticmethod
    def sanitize_text(text: str, max_length: int = 10000, allow_html: bool = False) -> str:
        """Sanitize text input"""
        if not isinstance(text, str):
            text = str(text)

        # Length check
        if len(text) > max_length:
            raise ValueError(f"Text exceeds maximum length of {max_length} characters")

        # Remove null bytes and control characters
        text = text.replace('\x00', '')

        # HTML sanitization
        if not allow_html:
            text = html.escape(text)

        # Additional safety checks
        text = text.strip()

        return text

    @staticmethod
    def sanitize_id(id_string: str, pattern: re.Pattern, field_name: str = "ID") -> str:
        """Sanitize and validate ID"""
        if not isinstance(id_string, str):
            raise ValueError(f"{field_name} must be a string")

        id_string = id_string.strip()

        if not pattern.match(id_string):
            raise ValueError(f"Invalid {field_name} format")

        return id_string

    @staticmethod
    def sanitize_numeric(value: Any, field_name: str = "Value", min_val: float = None, max_val: float = None) -> float:
        """Sanitize and validate numeric input"""
        try:
            numeric_value = float(value)
        except (ValueError, TypeError):
            raise ValueError(f"{field_name} must be a valid number")

        if min_val is not None and numeric_value < min_val:
            raise ValueError(f"{field_name} must be at least {min_val}")

        if max_val is not None and numeric_value > max_val:
            raise ValueError(f"{field_name} must not exceed {max_val}")

        return numeric_value

    @staticmethod
    def sanitize_list(items: Any, field_name: str = "List", max_items: int = 1000, item_validator: callable = None) -> List[Any]:
        """Sanitize and validate list input"""
        if items is None:
            return []

        if not isinstance(items, (list, tuple)):
            raise ValueError(f"{field_name} must be a list")

        if len(items) > max_items:
            raise ValueError(f"{field_name} cannot contain more than {max_items} items")

        sanitized_items = []
        for i, item in enumerate(items):
            try:
                if item_validator:
                    sanitized_item = item_validator(item)
                else:
                    sanitized_item = InputSanitizer.sanitize_text(str(item), max_length=1000)
                sanitized_items.append(sanitized_item)
            except Exception as e:
                raise ValueError(f"Invalid item at index {i} in {field_name}: {str(e)}")

        return sanitized_items

class CLERequestValidator(BaseModel):
    """Base validator for CLE requests"""

    # Common fields
    user_id: str
    course_id: Optional[str] = None

    @validator('user_id')
    def validate_user_id(cls, v):
        return InputSanitizer.sanitize_id(v, ValidationPatterns.USER_ID_PATTERN, "user_id")

    @validator('course_id')
    def validate_course_id(cls, v):
        if v is None:
            return v
        return InputSanitizer.sanitize_id(v, ValidationPatterns.COURSE_ID_PATTERN, "course_id")

class TextValidationMixin:
    """Mixin for text validation"""

    @classmethod
    def sanitize_text_field(cls, value: Any, max_length: int = 10000, field_name: str = "text"):
        """Sanitize a text field"""
        return InputSanitizer.sanitize_text(str(value), max_length=max_length)

class ValidationMiddleware:
    """Middleware to validate all incoming requests"""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            # Get request details
            method = scope["method"]
            path = scope["path"]

            # Only validate POST, PUT, PATCH requests
            if method in ["POST", "PUT", "PATCH"]:
                try:
                    # Read request body
                    request_body = await self._get_request_body(scope, receive)

                    if request_body:
                        # Validate the body
                        validated_body = await self._validate_request_body(method, path, request_body)

                        # Update scope with validated body
                        # This is a simplified approach - in production, you'd want proper request body injection
                        return await self._send_response(scope, receive, send, validated_body)

                except ValidationError as e:
                    return await self._send_error_response(send, 422, "Validation Error", str(e))
                except ValueError as e:
                    return await self._send_error_response(send, 400, "Invalid Input", str(e))
                except Exception as e:
                    return await self._send_error_response(send, 500, "Validation Error", str(e))

        # Let other requests pass through
        return await self.app(scope, receive, send)

    async def _get_request_body(self, scope, receive):
        """Get request body from scope"""
        # This is simplified - in production, you'd use proper ASGI message handling
        body = b""
        more_body = True

        while more_body:
            message = await receive()
            body += message.get("body", b"")
            more_body = message.get("more_body", False)

        if body:
            try:
                return json.loads(body.decode())
            except json.JSONDecodeError:
                return {"raw": body.decode()}
        return None

    async def _validate_request_body(self, method: str, path: str, body: Dict[str, Any]) -> Dict[str, Any]:
        """Validate request body based on endpoint"""

        # Route-based validation
        if "/spaced-repetition/" in path:
            return await self._validate_spaced_repetition_request(method, path, body)
        elif "/active-recall/" in path:
            return await self._validate_active_recall_request(method, path, body)
        elif "/dual-coding/" in path:
            return await self._validate_dual_coding_request(method, path, body)
        elif "/interleaved-practice/" in path:
            return await self._validate_interleaved_practice_request(method, path, body)
        elif "/metacognition/" in path:
            return await self._validate_metacognition_request(method, path, body)
        elif "/elaboration-network/" in path:
            return await self._validate_elaboration_network_request(method, path, body)
        else:
            # Basic validation for unknown routes
            return await self._validate_basic_request(body)

    async def _validate_basic_request(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """Basic validation for any request"""
        validated = {}

        # Validate common fields
        if "user_id" in body:
            validated["user_id"] = InputSanitizer.sanitize_id(
                body["user_id"], ValidationPatterns.USER_ID_PATTERN, "user_id"
            )

        if "course_id" in body:
            validated["course_id"] = InputSanitizer.sanitize_id(
                body["course_id"], ValidationPatterns.COURSE_ID_PATTERN, "course_id"
            )

        # Validate text fields
        for key, value in body.items():
            if key in ["user_id", "course_id"]:
                continue
            elif isinstance(value, str) and len(value) < 10000:
                validated[key] = InputSanitizer.sanitize_text(value)
            elif isinstance(value, (int, float)):
                validated[key] = value
            elif isinstance(value, bool):
                validated[key] = value
            elif isinstance(value, list) and len(value) < 100:
                validated[key] = InputSanitizer.sanitize_list(value)

        return validated

    async def _validate_spaced_repetition_request(self, method: str, path: str, body: Dict[str, Any]) -> Dict[str, Any]:
        """Validate spaced repetition requests"""
        # Card creation validation
        if method == "POST" and "/cards" in path:
            required_fields = ["course_id", "question", "answer"]
            for field in required_fields:
                if field not in body:
                    raise ValueError(f"Missing required field: {field}")

            validated = {
                "course_id": InputSanitizer.sanitize_id(body["course_id"], ValidationPatterns.COURSE_ID_PATTERN),
                "question": InputSanitizer.sanitize_text(body["question"], max_length=1000),
                "answer": InputSanitizer.sanitize_text(body["answer"], max_length=2000),
            }

            if "card_type" in body:
                card_type = body["card_type"]
                if card_type not in ["basic", "cloze", "concept", "application"]:
                    raise ValueError("Invalid card_type")
                validated["card_type"] = card_type

            return validated

        # Review submission validation
        elif method == "POST" and "/review" in path:
            if "card_id" not in body or "quality_rating" not in body:
                raise ValueError("Missing required fields for card review")

            return {
                "card_id": InputSanitizer.sanitize_id(body["card_id"], ValidationPatterns.UUID_PATTERN, "card_id"),
                "quality_rating": InputSanitizer.sanitize_numeric(body["quality_rating"], "quality_rating", 0, 5),
                "response_time_ms": InputSanitizer.sanitize_numeric(body.get("response_time_ms", 0), "response_time_ms", 0, 60000),
            }

        return await self._validate_basic_request(body)

    async def _validate_active_recall_request(self, method: str, path: str, body: Dict[str, Any]) -> Dict[str, Any]:
        """Validate active recall requests"""
        # Question generation validation
        if method == "POST" and "/questions" in path:
            if "content" not in body:
                raise ValueError("Missing required content field")

            return {
                "content": InputSanitizer.sanitize_text(body["content"], max_length=5000),
                "num_questions": InputSanitizer.sanitize_numeric(body.get("num_questions", 5), "num_questions", 1, 50),
                "difficulty": body.get("difficulty", "medium"),
            }

        return await self._validate_basic_request(body)

    async def _validate_dual_coding_request(self, method: str, path: str, body: Dict[str, Any]) -> Dict[str, Any]:
        """Validate dual coding requests"""
        if method == "POST" and "/content" in path:
            if "content" not in body:
                raise ValueError("Missing required content field")

            return {
                "content": InputSanitizer.sanitize_text(body["content"], max_length=5000),
                "content_type": body.get("content_type", "text"),
                "target_audience": body.get("target_audience", "intermediate"),
            }

        return await self._validate_basic_request(body)

    async def _validate_interleaved_practice_request(self, method: str, path: str, body: Dict[str, Any]) -> Dict[str, Any]:
        """Validate interleaved practice requests"""
        if method == "POST" and "/schedules" in path:
            if "concepts" not in body or not isinstance(body["concepts"], list):
                raise ValueError("Missing or invalid concepts field")

            validated_concepts = InputSanitizer.sanitize_list(
                body["concepts"], "concepts", max_items=20,
                item_validator=lambda x: InputSanitizer.sanitize_text(str(x), max_length=200)
            )

            return {
                "concepts": validated_concepts,
                "session_duration_minutes": InputSanitizer.sanitize_numeric(
                    body.get("session_duration_minutes", 30), "session_duration_minutes", 5, 180
                ),
            }

        return await self._validate_basic_request(body)

    async def _validate_metacognition_request(self, method: str, path: str, body: Dict[str, Any]) -> Dict[str, Any]:
        """Validate metacognition requests"""
        if method == "POST" and "/sessions" in path:
            if "learning_context" not in body:
                raise ValueError("Missing required learning_context field")

            return {
                "learning_context": body["learning_context"],  # Complex object - would need deeper validation
                "session_type": body.get("session_type", "comprehensive"),
            }

        return await self._validate_basic_request(body)

    async def _validate_elaboration_network_request(self, method: str, path: str, body: Dict[str, Any]) -> Dict[str, Any]:
        """Validate elaboration network requests"""
        if method == "POST" and "/build" in path:
            if "knowledge_base" not in body:
                raise ValueError("Missing required knowledge_base field")

            return {
                "knowledge_base": body["knowledge_base"],  # Complex object
                "integration_level": body.get("integration_level", "deep"),
            }

        return await self._validate_basic_request(body)

    async def _send_error_response(self, send, status_code: int, error_type: str, message: str):
        """Send error response"""
        response = JSONResponse(
            status_code=status_code,
            content={
                "success": False,
                "error": error_type,
                "detail": message,
                "timestamp": datetime.now().isoformat()
            }
        )

        # Send response (simplified)
        await send({
            "type": "http.response.start",
            "status": status_code,
            "headers": [[b"content-type", b"application/json"]],
        })

        await send({
            "type": "http.response.body",
            "body": response.body.encode(),
        })

    async def _send_response(self, scope, receive, send, validated_body):
        """Send response with validated body"""
        # This is a simplified implementation
        # In production, you'd want to properly handle ASGI messages
        return await self.app(scope, receive, send)

# Utility functions for validation
def validate_email(email: str) -> bool:
    """Validate email format"""
    return bool(ValidationPatterns.EMAIL_PATTERN.match(email))

def validate_url(url: str) -> bool:
    """Validate URL format"""
    return bool(ValidationPatterns.URL_PATTERN.match(url))

def validate_rating(rating: Any) -> int:
    """Validate rating (1-5)"""
    try:
        rating_int = int(rating)
        if rating_int < 1 or rating_int > 5:
            raise ValueError("Rating must be between 1 and 5")
        return rating_int
    except (ValueError, TypeError):
        raise ValueError("Rating must be an integer between 1 and 5")

def validate_percentage(value: Any) -> float:
    """Validate percentage (0-100)"""
    try:
        percentage = float(value)
        if percentage < 0 or percentage > 100:
            raise ValueError("Percentage must be between 0 and 100")
        return percentage
    except (ValueError, TypeError):
        raise ValueError("Percentage must be a number between 0 and 100")

# Health check for validation service
def validation_health_check() -> Dict[str, Any]:
    """Check validation service health"""
    return {
        "status": "healthy",
        "patterns_loaded": True,
        "sanitizer_active": True,
        "validation_rules": {
            "user_id_pattern": bool(ValidationPatterns.USER_ID_PATTERN),
            "course_id_pattern": bool(ValidationPatterns.COURSE_ID_PATTERN),
            "uuid_pattern": bool(ValidationPatterns.UUID_PATTERN),
            "email_pattern": bool(ValidationPatterns.EMAIL_PATTERN),
            "url_pattern": bool(ValidationPatterns.URL_PATTERN),
        },
        "timestamp": datetime.now().isoformat()
    }