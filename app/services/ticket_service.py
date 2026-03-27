from datetime import datetime
from typing import Any, Dict

from app.models.ticket_model import build_ticket_model
from app.services.db_service import get_connection
from app.services.geocoding_service import geocode_location
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
    }


def create_ticket(data: Dict[str, Any], routing_info: Dict[str, Any]) -> Dict[str, Any]:
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
    )

    ticket["status"] = "assigned"
    ticket["normalized_location"] = str(geocode.get("normalized_location", ""))
    ticket["geocode_provider"] = str(geocode.get("provider", ""))

    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO tickets(
                ticket_id, call_id, customer_name, mobile, issue, location,
                issue_type, department, status, priority, sla_hours,
                created_at, sla_deadline, coordinates_lat, coordinates_lng,
                normalized_location, geocode_provider, resolved_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                ticket["ticket_id"],
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
