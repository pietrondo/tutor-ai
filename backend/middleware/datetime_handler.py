"""
DateTime Handler Middleware
Consistent datetime serialization across all CLE endpoints
"""

from datetime import datetime
from typing import Any, Dict, Union
import json
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import pytz
from pytz import UTC

class DateTimeMiddleware(BaseHTTPMiddleware):
    """Middleware to handle consistent datetime serialization"""

    def __init__(self, app, timezone: str = "UTC"):
        super().__init__(app)
        self.timezone = pytz.timezone(timezone)

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Only process JSON responses
        if not isinstance(response, JSONResponse):
            return response

        # Get the original body
        body = response.body

        try:
            # Parse and modify the JSON
            content = json.loads(body.decode())
            processed_content = self._process_datetime(content)

            # Create new response with processed content
            return JSONResponse(
                content=processed_content,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type
            )
        except (json.JSONDecodeError, UnicodeDecodeError):
            # If we can't parse JSON, return original response
            return response

    def _process_datetime(self, obj: Any) -> Any:
        """Recursively process datetime objects in the response"""
        if isinstance(obj, datetime):
            # Convert to specified timezone and format
            if obj.tzinfo is None:
                obj = self.timezone.localize(obj)
            else:
                obj = obj.astimezone(self.timezone)
            return obj.isoformat()

        elif isinstance(obj, dict):
            return {key: self._process_datetime(value) for key, value in obj.items()}

        elif isinstance(obj, list):
            return [self._process_datetime(item) for item in obj]

        elif hasattr(obj, '__dict__'):
            # Handle Pydantic models and other objects
            return self._process_datetime(obj.__dict__)

        return obj

class DateTimeJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for consistent datetime handling"""

    def default(self, obj):
        if isinstance(obj, datetime):
            # Always convert to UTC and ISO format
            if obj.tzinfo is None:
                obj = UTC.localize(obj)
            else:
                obj = obj.astimezone(UTC)
            return obj.isoformat()

        return super().default(obj)

def create_json_response(content: Any, status_code: int = 200) -> JSONResponse:
    """Create JSON response with consistent datetime handling"""
    return JSONResponse(
        content=content,
        status_code=status_code,
        media_type="application/json"
    )

def serialize_datetime(obj: Any) -> Dict[str, Any]:
    """Serialize an object with consistent datetime handling"""
    return json.loads(json.dumps(obj, cls=DateTimeJSONEncoder))

# Common datetime formatting functions
def format_datetime_for_frontend(dt: datetime) -> str:
    """Format datetime for frontend consumption"""
    if dt.tzinfo is None:
        dt = UTC.localize(dt)
    else:
        dt = dt.astimezone(UTC)
    return dt.isoformat()

def parse_datetime_from_frontend(dt_str: str) -> datetime:
    """Parse datetime string from frontend"""
    try:
        dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        if dt.tzinfo is None:
            dt = UTC.localize(dt)
        return dt
    except ValueError as e:
        raise ValueError(f"Invalid datetime format: {dt_str}. Expected ISO format.")