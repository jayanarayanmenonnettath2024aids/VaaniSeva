import json
import time
from typing import Any, Dict

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.services import (
    analytics_service,
    audit_service,
    notification_service,
    routing_service,
    sla_service,
    ticket_service,
)

router = APIRouter()


@router.get("/analytics/metrics")
def analytics_metrics() -> JSONResponse:
    """Get impressive operational metrics for dashboard display."""
    tickets_dict = ticket_service.list_tickets()
    tickets = list(tickets_dict.values()) if tickets_dict else []
    
    resolved_tickets = [t for t in tickets if t.get("status") == "resolved"]
    active_tickets = [t for t in tickets if t.get("status") != "resolved"]
    
    # Calculate average resolution time in hours
    avg_resolution_hours = 0
    if resolved_tickets:
        total_hours = 0
        for ticket in resolved_tickets:
            created_at = ticket.get("created_at")
            resolved_at = ticket.get("resolved_at")
            if created_at and resolved_at:
                try:
                    from datetime import datetime
                    created_dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    resolved_dt = datetime.fromisoformat(resolved_at.replace('Z', '+00:00'))
                    hours = (resolved_dt - created_dt).total_seconds() / 3600
                    total_hours += hours
                except (ValueError, TypeError):
                    pass
        if resolved_tickets:
            avg_resolution_hours = round(total_hours / len(resolved_tickets), 1)
    
    # Count resolved tickets created today
    from datetime import date, datetime
    today = date.today()
    resolved_today = 0
    for ticket in resolved_tickets:
        resolved_at = ticket.get("resolved_at")
        if resolved_at:
            try:
                resolved_dt = datetime.fromisoformat(resolved_at.replace('Z', '+00:00')).date()
                if resolved_dt == today:
                    resolved_today += 1
            except (ValueError, TypeError):
                pass
    
    metrics = {
        "avg_resolution_hours": avg_resolution_hours if avg_resolution_hours > 0 else "N/A",
        "resolved_today": resolved_today,
        "active_tickets": len(active_tickets),
        "total_resolved": len(resolved_tickets),
        "total_tickets": len(tickets),
        "resolution_rate": f"{(len(resolved_tickets) / len(tickets) * 100):.1f}%" if tickets else "0%",
    }
    
    return JSONResponse(status_code=200, content=metrics)

class StructuredData(BaseModel):
    customer_name: str = ""
    mobile: str = ""
    issue: str = ""
    location: str = ""
    issue_type: str = ""


class ProcessActionRequest(BaseModel):
    call_id: str = ""
    structured_data: StructuredData


class SimulateActionRequest(BaseModel):
    issue_type: str = "Road"


class UpdateStatusRequest(BaseModel):
    status: str


def _safe_structured_data(data: StructuredData, call_id: str) -> Dict[str, Any]:
    return {
        "call_id": call_id or "",
        "customer_name": data.customer_name or "",
        "mobile": data.mobile or "",
        "issue": data.issue or "",
        "location": data.location or "",
        "issue_type": data.issue_type or "",
    }


@router.post("/process-action")
def process_action(body: ProcessActionRequest) -> JSONResponse:
    started = time.perf_counter()
    try:
        data = _safe_structured_data(body.structured_data, body.call_id)
        routing_info = routing_service.get_department(data.get("issue_type", ""))
        ticket = ticket_service.create_ticket(data, routing_info)

        sms_text = notification_service.format_sms(ticket)
        whatsapp_text = notification_service.format_whatsapp_message(ticket)
        mobile = str(ticket.get("mobile", ""))
        notification_service._send_async(notification_service.send_sms, mobile, sms_text)
        notification_service._send_async(notification_service.send_whatsapp, mobile, whatsapp_text)

        audit_service.log_event(
            stage="action",
            event_name="process_action",
            call_id=body.call_id,
            mobile=mobile,
            issue_type=ticket.get("issue_type", ""),
            location_norm=ticket.get("normalized_location", ""),
            department=ticket.get("department", ""),
            outcome="ok",
            latency_ms=int((time.perf_counter() - started) * 1000),
            meta={
                "ticket_id": ticket.get("ticket_id", ""),
                "department": ticket.get("department", ""),
                "issue_type": ticket.get("issue_type", ""),
                "action_status": "assigned",
            },
        )

        return JSONResponse(
            status_code=200,
            content={
                "ticket_id": ticket.get("ticket_id", ""),
                "department": ticket.get("department", ""),
                "sla_hours": ticket.get("sla_hours", 24),
                "status": ticket.get("status", "created"),
                "notifications": "queued",
            },
        )
    except Exception as exc:
        audit_service.log_event(
            stage="action",
            event_name="process_action",
            call_id=body.call_id,
            mobile=body.structured_data.mobile,
            issue_type=body.structured_data.issue_type,
            outcome="error",
            error_code="process_action_exception",
            latency_ms=int((time.perf_counter() - started) * 1000),
            meta={"issue_type": body.structured_data.issue_type, "action_status": "failed"},
        )
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": "Failed to process action", "details": str(exc)},
        )


@router.post("/simulate-action")
def simulate_action(body: SimulateActionRequest) -> JSONResponse:
    simulated_payload = ProcessActionRequest(
        call_id="simulated-call",
        structured_data=StructuredData(
            customer_name="Demo User",
            mobile="",
            issue=f"Simulated {body.issue_type} complaint",
            location="Demo Location",
            issue_type=body.issue_type,
        ),
    )

    result = process_action(simulated_payload)
    output = dict(result.body and json.loads(result.body) or {})

    if output.get("ticket_id"):
        ticket = ticket_service.get_ticket(output["ticket_id"])
        return JSONResponse(status_code=200, content={"result": output, "ticket": ticket})

    return result


@router.patch("/tickets/{ticket_id}/status")
def update_ticket_status(ticket_id: str, body: UpdateStatusRequest) -> JSONResponse:
    updated = ticket_service.update_status(ticket_id, body.status)
    if not updated:
        return JSONResponse(status_code=404, content={"status": "error", "message": "Ticket not found"})
    return JSONResponse(status_code=200, content=updated)


@router.get("/tickets/{ticket_id}")
def get_ticket(ticket_id: str) -> JSONResponse:
    ticket = ticket_service.get_ticket(ticket_id)
    if not ticket:
        return JSONResponse(status_code=404, content={"status": "error", "message": "Ticket not found"})
    return JSONResponse(status_code=200, content=ticket)


@router.get("/tickets")
def list_tickets() -> JSONResponse:
    return JSONResponse(status_code=200, content={"tickets": list(ticket_service.list_tickets().values())})


@router.get("/analytics/summary")
def analytics_summary() -> JSONResponse:
    return JSONResponse(status_code=200, content=analytics_service.get_summary())


@router.get("/analytics/issues")
def analytics_issues() -> JSONResponse:
    return JSONResponse(status_code=200, content=analytics_service.get_issue_distribution())


@router.get("/analytics/regions")
def analytics_regions() -> JSONResponse:
    return JSONResponse(status_code=200, content=analytics_service.get_region_distribution())


@router.get("/analytics/sla")
def analytics_sla() -> JSONResponse:
    return JSONResponse(status_code=200, content=analytics_service.get_sla_performance())


@router.get("/analytics/audit-summary")
def analytics_audit_summary() -> JSONResponse:
    return JSONResponse(status_code=200, content=audit_service.get_summary())


@router.get("/analytics/audit-timeline")
def analytics_audit_timeline(limit: int = 100, stage: str = "") -> JSONResponse:
    return JSONResponse(status_code=200, content={"events": audit_service.list_events(limit=limit, stage=stage)})


@router.post("/sla-monitor")
def run_sla_monitor_endpoint() -> JSONResponse:
    return JSONResponse(status_code=200, content={"escalations": sla_service.run_sla_monitor()})


@router.post("/resolve-ticket/{ticket_id}")
def resolve_ticket(ticket_id: str) -> JSONResponse:
    updated = ticket_service.update_status(ticket_id, "resolved")
    if not updated:
        return JSONResponse(status_code=404, content={"status": "error", "message": "Ticket not found"})
    return JSONResponse(status_code=200, content={"status": "resolved", "ticket": updated})
