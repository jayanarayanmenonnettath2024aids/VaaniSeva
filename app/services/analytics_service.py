from datetime import datetime
from typing import Any, Dict

from app.services import sla_service, ticket_service


def get_summary() -> Dict[str, int]:
    all_tickets = list(ticket_service.list_tickets().values())
    total = len(all_tickets)
    resolved = sum(1 for t in all_tickets if str(t.get("status", "")).lower() == "resolved")
    unresolved = total - resolved
    breaches = sum(1 for t in all_tickets if sla_service.check_sla(t).get("breached"))

    return {
        "total": total,
        "resolved": resolved,
        "unresolved": unresolved,
        "sla_breaches": breaches,
    }


def get_issue_distribution() -> Dict[str, int]:
    distribution: Dict[str, int] = {}
    for ticket in ticket_service.list_tickets().values():
        issue_type = str(ticket.get("issue_type", "") or "General")
        distribution[issue_type] = distribution.get(issue_type, 0) + 1
    return distribution


def get_region_distribution() -> Dict[str, int]:
    distribution: Dict[str, int] = {}
    for ticket in ticket_service.list_tickets().values():
        location = str(
            ticket.get("normalized_location", "")
            or ticket.get("location", "")
            or "Unknown"
        )
        distribution[location] = distribution.get(location, 0) + 1
    return distribution


def get_sla_performance() -> Dict[str, float]:
    all_tickets = list(ticket_service.list_tickets().values())
    if not all_tickets:
        return {"avg_resolution_time_hours": 0.0, "breach_rate": 0.0}

    resolved_tickets = [t for t in all_tickets if t.get("resolved_at")]
    resolution_hours = []

    for ticket in resolved_tickets:
        try:
            created_at = datetime.fromisoformat(str(ticket.get("created_at")))
            resolved_at = datetime.fromisoformat(str(ticket.get("resolved_at")))
            resolution_hours.append((resolved_at - created_at).total_seconds() / 3600)
        except Exception:
            continue

    avg_resolution = sum(resolution_hours) / len(resolution_hours) if resolution_hours else 0.0
    breach_count = sum(1 for t in all_tickets if sla_service.check_sla(t).get("breached"))
    breach_rate = breach_count / len(all_tickets)

    return {
        "avg_resolution_time_hours": round(avg_resolution, 2),
        "breach_rate": round(breach_rate, 4),
    }
