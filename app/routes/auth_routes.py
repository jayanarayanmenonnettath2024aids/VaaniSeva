"""Authentication routes: login, logout, token validation."""
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import jwt
from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel

from app.config import settings
from app.services.rbac_service import (
    hash_password,
    verify_password,
    blacklist_token,
    cleanup_expired_blacklist,
    verify_jwt,
    JWT_SECRET,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

# JWT configuration
JWT_EXPIRY_HOURS = settings.JWT_EXPIRY_HOURS if hasattr(settings, "JWT_EXPIRY_HOURS") else 24

# Demo users with hashed passwords
DEMO_USERS = {
    "admin": {
        "password_hash": hash_password("admin123"),
        "role": "admin",
        "department": None,
        "name": "National Admin",
    },
    "pwd_officer": {
        "password_hash": hash_password("pwd123"),
        "role": "department",
        "department": "PWD",
        "name": "PWD Officer",
    },
    "water_officer": {
        "password_hash": hash_password("water123"),
        "role": "department",
        "department": "Municipality",
        "name": "Water Officer",
    },
    "sanitation": {
        "password_hash": hash_password("sanit123"),
        "role": "department",
        "department": "Sanitation",
        "name": "Sanitation Officer",
    },
}


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    token: str
    user: Dict[str, Any]


class TokenPayload(BaseModel):
    sub: str
    role: str
    department: Optional[str]
    exp: datetime


def generate_jwt(username: str, role: str, department: Optional[str] = None) -> str:
    """Generate JWT token with user info."""
    payload = {
        "sub": username,
        "role": role,
        "department": department,
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRY_HOURS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def extract_token(authorization: Optional[str] = Header(None)) -> str:
    """Extract bearer token from Authorization header."""
    if not authorization:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Missing Authorization header")
    
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid Authorization scheme")
    
    return token


async def get_current_user(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    """Dependency: extract and validate JWT from Authorization header."""
    token = extract_token(authorization)
    return verify_jwt(token)


@router.post("/login", response_model=LoginResponse)
def login(body: LoginRequest) -> LoginResponse:
    """
    Authenticate user with username/password.
    Returns JWT token + user info.
    """
    username = body.username.lower().strip()
    password = body.password.strip()

    # Demo authentication with password hashing verification
    if username not in DEMO_USERS:
        logger.warning("[AUTH] Failed login attempt: username=%s (not found)", username)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    
    user_data = DEMO_USERS[username]
    if not verify_password(password, user_data["password_hash"]):
        logger.warning("[AUTH] Failed login attempt: username=%s (wrong password)", username)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = generate_jwt(username, user_data["role"], user_data.get("department"))

    user_response = {
        "username": username,
        "role": user_data["role"],
        "department": user_data.get("department"),
        "name": user_data.get("name", username),
    }

    logger.info("[AUTH] Successful login: username=%s role=%s", username, user_data["role"])
    return LoginResponse(token=token, user=user_response)


@router.post("/logout")
async def logout(authorization: Optional[str] = Header(None)) -> Dict[str, str]:
    """
    Logout endpoint: Blacklist the token.
    Token is added to revocation list and future use is rejected.
    """
    token = extract_token(authorization)
    user = await get_current_user(authorization)
    
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        expiry_time = datetime.fromtimestamp(payload["exp"]).isoformat()
        blacklist_token(token, expiry_time)
    except jwt.InvalidTokenError:
        pass
    
    logger.info("[AUTH] User logged out: username=%s", user.get("sub"))
    cleanup_expired_blacklist()
    return {"status": "ok", "message": "Logged out successfully, token revoked"}


@router.get("/me")
async def get_user(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """Get currently authenticated user info."""
    return {
        "username": user.get("sub"),
        "role": user.get("role"),
        "department": user.get("department"),
        "exp": user.get("exp"),
    }


@router.post("/validate")
async def validate_token(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """Validate JWT token and return decoded payload."""
    return {"valid": True, "user": user}
