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
    city_id: str = "coimbatore",
) -> Dict[str, Any]:
    """Build a ticket model with multi-tenancy and E2E timing support.
    
    Status progression: created → assigned → in_progress → resolved → closed
    E2E timing tracks: STT, extraction, routing, assignment, resolution
    """
    return {
        "ticket_id": ticket_id,
        "city_id": city_id,
        "call_id": call_id,
        "customer_name": customer_name,
        "mobile": mobile,
        "issue": issue,
        "location": location,
        "issue_type": issue_type,
        "department": department,
        "status": "created",  # created → assigned → in_progress → resolved → closed
        "priority": priority,
        "sla_hours": sla_hours,
        "created_at": created_at,
        "sla_deadline": sla_deadline,
        "coordinates": coordinates,
        "resolved_at": None,
        "closed_at": None,
        "sla_breached": False,
        # E2E timing checkpoints (for instrumentation)
        "stt_completed_at": None,
        "extraction_completed_at": None,
        "routing_completed_at": None,
        "assigned_at": None,
        "in_progress_at": None,
    }
