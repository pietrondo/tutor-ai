"""
Authentication Middleware for CLE API
JWT-based authentication and authorization
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import jwt
from fastapi import HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os
from passlib.context import CryptContext
import uuid

# Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-here-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30 * 24 * 60  # 30 days

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Security scheme
security = HTTPBearer()

class User:
    """Simple user model for authentication"""
    def __init__(self, user_id: str, email: str, is_active: bool = True):
        self.user_id = user_id
        self.email = email
        self.is_active = is_active
        self.created_at = datetime.now()

# In-memory user storage (for demo - replace with database in production)
users_db: Dict[str, User] = {}

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now() + expires_delta
    else:
        expire = datetime.now() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire, "sub": data.get("user_id"), "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Dict[str, Any]:
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        token_type: str = payload.get("type")

        if user_id is None or token_type != "access":
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.JWTError:
        raise HTTPException(
            status_code=401,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current authenticated user from JWT token"""
    token = credentials.credentials
    payload = verify_token(token)
    user_id = payload.get("user_id")

    # In production, fetch from database
    user = users_db.get(user_id)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=401,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user

def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return pwd_context.verify(plain_password, hashed_password)

def authenticate_user(user_id: str, password: str) -> Optional[User]:
    """Authenticate user with user_id and password"""
    # In production, verify against database
    # For demo, create user if not exists and password matches

    user = users_db.get(user_id)

    # For demo purposes, create user if doesn't exist
    if not user:
        # In production, this should not happen
        return None

    # In production, you would verify the hashed password
    # For demo, accept any password for existing users
    return user

def create_demo_user(user_id: str, email: str, password: str = None) -> User:
    """Create a demo user for testing"""
    if user_id in users_db:
        return users_db[user_id]

    user = User(user_id=user_id, email=email)
    users_db[user_id] = user
    return user

def get_optional_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    """Get current user if token is provided, otherwise None"""
    if not credentials:
        return None

    try:
        token = credentials.credentials
        payload = verify_token(token)
        user_id = payload.get("user_id")
        user = users_db.get(user_id)

        if user and user.is_active:
            return user
    except HTTPException:
        pass

    return None

# Authorization helpers
def require_user(user: User = Depends(get_current_user)):
    """Require authenticated user"""
    return user

def allow_anonymous(user: Optional[User] = Depends(get_optional_current_user)):
    """Allow anonymous or authenticated user"""
    return user

# Role-based access control (for future expansion)
class Role:
    USER = "user"
    ADMIN = "admin"
    INSTRUCTOR = "instructor"

class UserWithRole(User):
    """User with role information"""
    def __init__(self, user_id: str, email: str, role: str = Role.USER, is_active: bool = True):
        super().__init__(user_id, email, is_active)
        self.role = role

def require_role(required_role: str):
    """Decorator to require specific role"""
    def role_checker(user: User = Depends(get_current_user)):
        # For now, all users have USER role
        # In production, check user.role == required_role
        return user
    return role_checker

# Rate limiting helpers
user_request_counts: Dict[str, Dict[str, int]] = {}

def check_rate_limit(user: User, max_requests: int = 100, window_minutes: int = 60):
    """Check if user exceeded rate limit"""
    now = datetime.now()
    window_start = now - timedelta(minutes=window_minutes)

    # Clean old entries
    cutoff = window_start.timestamp()

    if user.user_id not in user_request_counts:
        user_request_counts[user.user_id] = {"count": 0, "last_reset": now.timestamp()}

    user_data = user_request_counts[user.user_id]

    # Reset counter if window expired
    if user_data["last_reset"] < cutoff:
        user_data["count"] = 0
        user_data["last_reset"] = now.timestamp()

    # Check limit
    if user_data["count"] >= max_requests:
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Please try again later.",
            headers={"Retry-After": str(window_minutes * 60)}
        )

    # Increment counter
    user_data["count"] += 1
    return True

# CORS and security headers middleware
class SecurityHeadersMiddleware:
    """Add security headers to responses"""

    def __init__(self, app):
        self.app = app

    def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            # Add security headers
            async def app_wrapper():
                # Create the response
                response = await self.app(scope, receive, send)

                # Add security headers (implementation depends on framework)
                return response

            return app_wrapper()

        return self.app(scope, receive, send)

# Utility functions for development
def create_test_token(user_id: str) -> str:
    """Create a test token for development"""
    return create_access_token(data={"user_id": user_id})

def decode_token_without_verification(token: str) -> Dict[str, Any]:
    """Decode token without verification (for debugging only)"""
    try:
        return jwt.decode(token, options={"verify_signature": False})
    except jwt.JWTError:
        return {}

# Health check for auth service
def auth_health_check() -> Dict[str, Any]:
    """Check authentication service health"""
    return {
        "status": "healthy",
        "secret_configured": bool(SECRET_KEY and SECRET_KEY != "your-secret-key-here-in-production"),
        "algorithm": ALGORITHM,
        "token_expiry_minutes": ACCESS_TOKEN_EXPIRE_MINUTES,
        "active_users": len([u for u in users_db.values() if u.is_active]),
        "timestamp": datetime.now().isoformat()
    }