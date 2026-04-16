"""Department management routes: CRUD for departments and their configurations."""
import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.services.db_service import get_connection
from app.services.rbac_service import get_current_user
from app.utils.id_generator import generate_ticket_id
from app.utils.time_utils import get_current_time

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/departments", tags=["departments"])


class DepartmentCreate(BaseModel):
    name: str
    city_id: str = "coimbatore"
    issue_type: str  # Road, Water, Electricity, Garbage, Street Light, General
    sla_hours: int = 24
    contact_email: str = ""


class DepartmentUpdate(BaseModel):
    name: str = None
    sla_hours: int = None
    contact_email: str = None


def _require_admin(user: Dict[str, Any]) -> Dict[str, Any]:
    """Dependency: Require admin role."""
    if user.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return user


@router.get("")
def list_departments(city_id: str = "coimbatore", user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """List all departments for a city."""
    if user.get("role") == "department":
        # Department staff only see their own department
        dept = user.get("department")
        if not dept:
            return {"departments": []}
        return {"departments": [{"name": dept, "city_id": city_id, "status": "active"}]}

    # Admins see all departments for the city
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM departments WHERE city_id = ? AND active = 1 ORDER BY name",
            (city_id,),
        ).fetchall()

    departments = [
        {
            "department_id": row["department_id"],
            "name": row["name"],
            "city_id": row["city_id"],
            "issue_type": row["issue_type"],
            "sla_hours": row["sla_hours"],
            "contact_email": row["contact_email"],
            "created_at": row["created_at"],
        }
        for row in rows
    ]
    return {"departments": departments}


@router.post("")
def create_department(body: DepartmentCreate, user: Dict[str, Any] = Depends(_require_admin)) -> Dict[str, Any]:
    """Create a new department (admin only)."""
    department_id = generate_ticket_id()  # Reuse ID generator
    created_at = get_current_time().isoformat()

    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO departments(department_id, name, city_id, issue_type, sla_hours, contact_email, active, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?)
            """,
            (
                department_id,
                body.name,
                body.city_id,
                body.issue_type,
                body.sla_hours,
                body.contact_email,
                created_at,
                created_at,
            ),
        )

    logger.info(
        "[DEPT] Created department: id=%s name=%s issue_type=%s city_id=%s sla_hours=%d",
        department_id,
        body.name,
        body.issue_type,
        body.city_id,
        body.sla_hours,
    )

    return {
        "status": "created",
        "department_id": department_id,
        "name": body.name,
        "issue_type": body.issue_type,
        "sla_hours": body.sla_hours,
    }


@router.get("/{department_id}")
def get_department(department_id: str, user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """Get department details."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM departments WHERE department_id = ? AND active = 1",
            (department_id,),
        ).fetchone()

    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")

    # Department staff can only see their own department
    if user.get("role") == "department" and row["name"] != user.get("department"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")

    return {
        "department_id": row["department_id"],
        "name": row["name"],
        "city_id": row["city_id"],
        "issue_type": row["issue_type"],
        "sla_hours": row["sla_hours"],
        "contact_email": row["contact_email"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


@router.put("/{department_id}")
def update_department(
    department_id: str, body: DepartmentUpdate, user: Dict[str, Any] = Depends(_require_admin)
) -> Dict[str, Any]:
    """Update department details (admin only)."""
    updated_at = get_current_time().isoformat()

    updates = []
    params = []
    if body.name is not None:
        updates.append("name = ?")
        params.append(body.name)
    if body.sla_hours is not None:
        updates.append("sla_hours = ?")
        params.append(body.sla_hours)
    if body.contact_email is not None:
        updates.append("contact_email = ?")
        params.append(body.contact_email)

    if not updates:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update")

    updates.append("updated_at = ?")
    params.append(updated_at)
    params.append(department_id)

    with get_connection() as conn:
        result = conn.execute(
            f"UPDATE departments SET {', '.join(updates)} WHERE department_id = ? AND active = 1",
            params,
        )

        if result.rowcount == 0:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")

        updated_row = conn.execute(
            "SELECT * FROM departments WHERE department_id = ?",
            (department_id,),
        ).fetchone()

    logger.info("[DEPT] Updated department: id=%s", department_id)
    return {
        "status": "updated",
        "department_id": updated_row["department_id"],
        "name": updated_row["name"],
        "sla_hours": updated_row["sla_hours"],
        "contact_email": updated_row["contact_email"],
    }


@router.delete("/{department_id}")
def delete_department(department_id: str, user: Dict[str, Any] = Depends(_require_admin)) -> Dict[str, str]:
    """Soft-delete a department (admin only)."""
    updated_at = get_current_time().isoformat()

    with get_connection() as conn:
        result = conn.execute(
            "UPDATE departments SET active = 0, updated_at = ? WHERE department_id = ?",
            (updated_at, department_id),
        )

        if result.rowcount == 0:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")

    logger.info("[DEPT] Deleted department: id=%s", department_id)
    return {"status": "deleted", "department_id": department_id}


@router.get("/{department_id}/sla-policy")
def get_sla_policy(department_id: str, user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """Get SLA policy for a department."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT sla_hours, issue_type FROM departments WHERE department_id = ? AND active = 1",
            (department_id,),
        ).fetchone()

    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")

    return {
        "department_id": department_id,
        "issue_type": row["issue_type"],
        "sla_hours": row["sla_hours"],
        "escalation_enabled": True,
        "escalation_interval_hours": row["sla_hours"] // 2,  # Escalate at half SLA time
    }
