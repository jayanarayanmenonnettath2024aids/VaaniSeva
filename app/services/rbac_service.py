"""RBAC (Role-Based Access Control) middleware and utilities."""
import logging
from typing import Any, Dict, Optional

from fastapi import Header, HTTPException, status

from app.routes.auth_routes import verify_jwt

logger = logging.getLogger(__name__)


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
