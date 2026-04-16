from datetime import datetime
from typing import Any, Dict

from app.config import settings
from app.models.ticket_model import build_ticket_model
from app.services.db_service import get_connection
from app.services.geocoding_service import geocode_location
from app.services.routing_service import get_department
from app.utils.id_generator import generate_ticket_id
from app.utils.time_utils import add_hours, get_current_time


def _get_priority(issue_type: str) -> str:
    normalized = (issue_type or "").lower().strip()
    if "electricity" in normalized or "electric" in normalized:
        return "high"
    if "road" in normalized:
        return "medium"
    return "low"


def _row_to_ticket(row: Any) -> Dict[str, Any]:
    if row is None:
        return {}

    return {
        "ticket_id": str(row["ticket_id"] or ""),
        "city_id": str(row.get("city_id", "coimbatore") or "coimbatore"),
        "call_id": str(row["call_id"] or ""),
        "customer_name": str(row["customer_name"] or ""),
        "mobile": str(row["mobile"] or ""),
        "issue": str(row["issue"] or ""),
        "location": str(row["location"] or ""),
        "normalized_location": str(row["normalized_location"] or ""),
        "geocode_provider": str(row["geocode_provider"] or ""),
        "issue_type": str(row["issue_type"] or ""),
        "department": str(row["department"] or ""),
        "status": str(row["status"] or ""),
        "priority": str(row["priority"] or ""),
        "sla_hours": int(row["sla_hours"] or 0),
        "created_at": str(row["created_at"] or ""),
        "sla_deadline": str(row["sla_deadline"] or ""),
        "coordinates": {
            "lat": float(row["coordinates_lat"] or 0.0),
            "lng": float(row["coordinates_lng"] or 0.0),
        },
        "resolved_at": row["resolved_at"],
        "closed_at": row.get("closed_at"),
        "sla_breached": bool(row.get("sla_breached", False)),
        # E2E timing checkpoints
        "stt_completed_at": row.get("stt_completed_at"),
        "extraction_completed_at": row.get("extraction_completed_at"),
        "routing_completed_at": row.get("routing_completed_at"),
        "assigned_at": row.get("assigned_at"),
        "in_progress_at": row.get("in_progress_at"),
    }


def create_ticket(data: Dict[str, Any], routing_info: Dict[str, Any], city_id: str = None) -> Dict[str, Any]:
    if city_id is None:
        city_id = settings.CITY_ID
    
    ticket_id = generate_ticket_id()
    sla_hours = int(routing_info.get("sla_hours", 24))
    created_at = get_current_time()
    sla_deadline = add_hours(sla_hours)
    geocode = geocode_location(str(data.get("location", "")))
    coordinates = geocode["coordinates"]

    ticket = build_ticket_model(
        ticket_id=ticket_id,
        call_id=str(data.get("call_id", "")),
        customer_name=str(data.get("customer_name", "")),
        mobile=str(data.get("mobile", "")),
        issue=str(data.get("issue", "")),
        location=str(data.get("location", "")),
        issue_type=str(data.get("issue_type", "")),
        department=str(routing_info.get("department", "General Department")),
        priority=_get_priority(str(data.get("issue_type", ""))),
        sla_hours=sla_hours,
        created_at=created_at.isoformat(),
        sla_deadline=sla_deadline.isoformat(),
        coordinates=coordinates,
        city_id=city_id,
    )

    ticket["status"] = "assigned"
    ticket["normalized_location"] = str(geocode.get("normalized_location", ""))
    ticket["geocode_provider"] = str(geocode.get("provider", ""))

    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO tickets(
                ticket_id, city_id, call_id, customer_name, mobile, issue, location,
                issue_type, department, status, priority, sla_hours,
                created_at, sla_deadline, coordinates_lat, coordinates_lng,
                normalized_location, geocode_provider, resolved_at, closed_at,
                sla_breached, stt_completed_at, extraction_completed_at, routing_completed_at,
                assigned_at, in_progress_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                ticket["ticket_id"],
                ticket["city_id"],
                ticket["call_id"],
                ticket["customer_name"],
                ticket["mobile"],
                ticket["issue"],
                ticket["location"],
                ticket["issue_type"],
                ticket["department"],
                ticket["status"],
                ticket["priority"],
                ticket["sla_hours"],
                ticket["created_at"],
                ticket["sla_deadline"],
                coordinates["lat"],
                coordinates["lng"],
                ticket["normalized_location"],
                ticket["geocode_provider"],
                ticket["resolved_at"],
                ticket.get("closed_at"),
                ticket.get("sla_breached", False),
                ticket.get("stt_completed_at"),
                ticket.get("extraction_completed_at"),
                ticket.get("routing_completed_at"),
                ticket.get("assigned_at"),
                ticket.get("in_progress_at"),
            ),
        )

    return ticket


def update_status(ticket_id: str, status: str) -> Dict[str, Any] | None:
    resolved_at = datetime.utcnow().isoformat() if status == "resolved" else None

    with get_connection() as conn:
        updated = conn.execute(
            """
            UPDATE tickets
            SET status = ?, resolved_at = COALESCE(?, resolved_at)
            WHERE ticket_id = ?
            """,
            (status, resolved_at, ticket_id),
        )
        if updated.rowcount == 0:
            return None

        row = conn.execute("SELECT * FROM tickets WHERE ticket_id = ?", (ticket_id,)).fetchone()

    ticket = _row_to_ticket(row)
    return ticket or None


def transition_to_in_progress(ticket_id: str) -> Dict[str, Any] | None:
    """Transition ticket from assigned → in_progress."""
    now = datetime.utcnow().isoformat()
    
    with get_connection() as conn:
        updated = conn.execute(
            """
            UPDATE tickets
            SET status = 'in_progress', in_progress_at = ?
            WHERE ticket_id = ? AND status = 'assigned'
            """,
            (now, ticket_id),
        )
        if updated.rowcount == 0:
            return None
        
        row = conn.execute("SELECT * FROM tickets WHERE ticket_id = ?", (ticket_id,)).fetchone()
    
    return _row_to_ticket(row) if row else None


def resolve_ticket(ticket_id: str) -> Dict[str, Any] | None:
    """Transition ticket from in_progress → resolved."""
    now = datetime.utcnow().isoformat()
    
    with get_connection() as conn:
        # Fetch ticket first to check SLA
        ticket = conn.execute("SELECT * FROM tickets WHERE ticket_id = ?", (ticket_id,)).fetchone()
        if not ticket:
            return None
        
        # Check if SLA was breached
        sla_deadline = ticket["sla_deadline"]
        sla_breached = now > sla_deadline if sla_deadline else False
        
        # Update ticket to resolved
        conn.execute(
            """
            UPDATE tickets
            SET status = 'resolved', resolved_at = ?, sla_breached = ?
            WHERE ticket_id = ?
            """,
            (now, sla_breached, ticket_id),
        )
        
        # Fetch updated ticket
        row = conn.execute("SELECT * FROM tickets WHERE ticket_id = ?", (ticket_id,)).fetchone()
    
    return _row_to_ticket(row) if row else None


def close_ticket(ticket_id: str) -> Dict[str, Any] | None:
    """Transition ticket from resolved → closed."""
    now = datetime.utcnow().isoformat()
    
    with get_connection() as conn:
        updated = conn.execute(
            """
            UPDATE tickets
            SET status = 'closed', closed_at = ?
            WHERE ticket_id = ? AND status = 'resolved'
            """,
            (now, ticket_id),
        )
        if updated.rowcount == 0:
            return None
        
        row = conn.execute("SELECT * FROM tickets WHERE ticket_id = ?", (ticket_id,)).fetchone()
    
    return _row_to_ticket(row) if row else None


def backfill_issue_for_call(call_id: str, issue: str, issue_type: str = "General") -> bool:
    """Backfill latest empty ticket for a call with delayed STT/extraction output."""
    clean_call_id = str(call_id or "").strip()
    clean_issue = str(issue or "").strip()
    clean_issue_type = str(issue_type or "General").strip() or "General"

    if not clean_call_id or not clean_issue:
        return False

    with get_connection() as conn:
        target = conn.execute(
            """
            SELECT rowid, issue_type FROM tickets
            WHERE call_id = ? AND COALESCE(issue, '') = ''
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (clean_call_id,),
        ).fetchone()

        if not target:
            return False

        existing_issue_type = str(target["issue_type"] or "").strip()
        should_reclassify = existing_issue_type.lower() in {"", "general"}

        if not should_reclassify:
            updated = conn.execute(
                """
                UPDATE tickets
                SET issue = ?
                WHERE rowid = ?
                """,
                (clean_issue, target["rowid"]),
            )
        else:
            routing = get_department(clean_issue_type)
            updated = conn.execute(
                """
                UPDATE tickets
                SET issue = ?, issue_type = ?, department = ?, sla_hours = ?, priority = ?
                WHERE rowid = ?
                """,
                (
                    clean_issue,
                    clean_issue_type,
                    str(routing.get("department", "General Department")),
                    int(routing.get("sla_hours", 24)),
                    _get_priority(clean_issue_type),
                    target["rowid"],
                ),
            )

    return bool(updated.rowcount)


def get_ticket(ticket_id: str) -> Dict[str, Any] | None:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM tickets WHERE ticket_id = ?", (ticket_id,)).fetchone()

    ticket = _row_to_ticket(row)
    return ticket or None


def list_tickets() -> Dict[str, Dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM tickets ORDER BY created_at ASC").fetchall()

    result: Dict[str, Dict[str, Any]] = {}
    for row in rows:
        ticket = _row_to_ticket(row)
        result[ticket["ticket_id"]] = ticket
    return result
