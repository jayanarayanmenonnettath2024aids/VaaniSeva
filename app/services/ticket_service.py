from datetime import datetime
import random
from typing import Any, Dict

from app.models.ticket_model import build_ticket_model
from app.utils.id_generator import generate_ticket_id
from app.utils.time_utils import add_hours, get_current_time


tickets: Dict[str, Dict[str, Any]] = {}


def mock_geocode(location: str) -> Dict[str, float]:
    return {
        "lat": round(random.uniform(8.0, 37.0), 6),
        "lng": round(random.uniform(68.0, 97.0), 6),
    }


def _get_priority(issue_type: str) -> str:
    normalized = (issue_type or "").lower().strip()
    if "electricity" in normalized or "electric" in normalized:
        return "high"
    if "road" in normalized:
        return "medium"
    return "low"


def create_ticket(data: Dict[str, Any], routing_info: Dict[str, Any]) -> Dict[str, Any]:
    ticket_id = generate_ticket_id()
    sla_hours = int(routing_info.get("sla_hours", 24))
    created_at = get_current_time()
    sla_deadline = add_hours(sla_hours)
    coordinates = mock_geocode(str(data.get("location", "")))

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

    # Auto-progression for demo lifecycle: created -> assigned
    ticket["status"] = "assigned"

    tickets[ticket_id] = ticket
    return ticket


def update_status(ticket_id: str, status: str) -> Dict[str, Any] | None:
    ticket = tickets.get(ticket_id)
    if not ticket:
        return None

    ticket["status"] = status
    if status == "resolved":
        ticket["resolved_at"] = datetime.utcnow().isoformat()

    return ticket


def get_ticket(ticket_id: str) -> Dict[str, Any] | None:
    return tickets.get(ticket_id)


def list_tickets() -> Dict[str, Dict[str, Any]]:
    return tickets
