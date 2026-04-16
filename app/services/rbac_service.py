"""RBAC (Role-Based Access Control) middleware and utilities."""
import logging
import hashlib
from typing import Any, Dict, Optional, Set
from datetime import datetime

import bcrypt
import jwt
from fastapi import Header, HTTPException, status

from app.config import settings

logger = logging.getLogger(__name__)

# Token blacklist for logout (in-memory for demo, use Redis for production)
_token_blacklist: Set[str] = set()
_blacklist_expires: Dict[str, str] = {}

# JWT configuration
JWT_SECRET = settings.JWT_SECRET if hasattr(settings, "JWT_SECRET") else "vaaniseva-default-secret-change-me"


def verify_jwt(token: str) -> Dict[str, Any]:
    """Verify and decode JWT token, checking blacklist."""
    # Check if token is blacklisted
    if is_token_blacklisted(token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has been revoked")
    
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


def extract_token(authorization: Optional[str] = Header(None)) -> str:
    """Extract JWT token from Authorization header."""
    if not authorization:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Missing Authorization header")

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid Authorization scheme")

    return token


def get_current_user(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    """Dependency: Verify JWT and return user info with RBAC context."""
    token = extract_token(authorization)
    payload = verify_jwt(token)
    return {
        "username": payload.get("sub"),
        "role": payload.get("role"),
        "department": payload.get("department"),
    }


def require_role(*allowed_roles: str):
    """Decorator factory to restrict access by role."""
    async def role_dependency(user: Dict[str, Any] = Header(None)) -> Dict[str, Any]:
        if user.get("role") not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required roles: {', '.join(allowed_roles)}",
            )
        return user

    return role_dependency


def filter_tickets_by_department(tickets: Dict[str, Any], user: Dict[str, Any]) -> Dict[str, Any]:
    """
    Filter ticket list based on user's department (RBAC).
    - Admin sees all tickets
    - Department officers see only their dept's tickets
    """
    if user.get("role") == "admin":
        return tickets

    user_dept = user.get("department")
    if not user_dept:
        return {}

    filtered = {}
    for ticket_id, ticket in tickets.items():
        if ticket.get("department") == user_dept:
            filtered[ticket_id] = ticket

    logger.info(
        "[RBAC] Filtered tickets for user=%s department=%s: %d of %d visible",
        user.get("username"),
        user_dept,
        len(filtered),
        len(tickets),
    )
    return filtered


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash.

    Backward compatibility:
    - bcrypt hashes (preferred)
    - legacy SHA256 hex hashes
    """
    if not hashed_password:
        return False

    if hashed_password.startswith("$2"):
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))

    # Legacy fallback for older demo users.
    return hashlib.sha256(plain_password.encode()).hexdigest() == hashed_password


def blacklist_token(token: str, expiry_time: str):
    """Add token to blacklist (for logout)."""
    _token_blacklist.add(token)
    _blacklist_expires[token] = expiry_time
    logger.info("[AUTH] Token blacklisted (expires: %s)", expiry_time)


def is_token_blacklisted(token: str) -> bool:
    """Check if token is blacklisted."""
    return token in _token_blacklist


def cleanup_expired_blacklist():
    """Remove expired tokens from blacklist."""
    now = datetime.utcnow().isoformat()
    expired_tokens = [tok for tok, exp in _blacklist_expires.items() if exp <= now]
    for tok in expired_tokens:
        _token_blacklist.discard(tok)
        _blacklist_expires.pop(tok, None)
    if expired_tokens:
        logger.info("[AUTH] Cleaned up %d expired blacklisted tokens", len(expired_tokens))
