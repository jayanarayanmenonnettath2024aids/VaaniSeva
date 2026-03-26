from typing import Any, Dict


def build_ticket_model(
    ticket_id: str,
    call_id: str,
    customer_name: str,
    mobile: str,
    issue: str,
    location: str,
    issue_type: str,
    department: str,
    priority: str,
    sla_hours: int,
    created_at: str,
    sla_deadline: str,
    coordinates: Dict[str, float],
) -> Dict[str, Any]:
    return {
        "ticket_id": ticket_id,
        "call_id": call_id,
        "customer_name": customer_name,
        "mobile": mobile,
        "issue": issue,
        "location": location,
        "issue_type": issue_type,
        "department": department,
        "status": "created",
        "priority": priority,
        "sla_hours": sla_hours,
        "created_at": created_at,
        "sla_deadline": sla_deadline,
        "coordinates": coordinates,
        "resolved_at": None,
    }
