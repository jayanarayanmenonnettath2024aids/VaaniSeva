import json
import time
from typing import Any, Dict

from fastapi import APIRouter, Depends, Header, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.services import (
    analytics_service,
    audit_service,
    notification_service,
    rbac_service,
    routing_service,
    sla_service,
    ticket_service,
    cost_service,
    escalation_service,
    language_response_service,
)

router = APIRouter()


@router.get("/analytics/metrics")
def analytics_metrics(user: Dict[str, Any] = Depends(rbac_service.get_current_user)) -> JSONResponse:
    """Get operational metrics filtered by user's role and department."""
    tickets_dict = ticket_service.list_tickets()
    tickets = list(tickets_dict.values()) if tickets_dict else []
    
    # Apply RBAC filter
    if user.get("role") == "department":
        user_dept = user.get("department")
        tickets = [t for t in tickets if t.get("department") == user_dept]
    
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


def _get_filtered_tickets(user: Dict[str, Any]) -> list:
    """Get tickets filtered by user's role and department."""
    tickets_dict = ticket_service.list_tickets()
    tickets = list(tickets_dict.values()) if tickets_dict else []
    
    # Admins see all tickets, department staff see only their department's
    if user.get("role") == "department":
        user_dept = user.get("department")
        tickets = [t for t in tickets if t.get("department") == user_dept]
    
    return tickets


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

        # Best-effort telemetry capture for cost and latency tracking.
        try:
            cost_service.log_call_telemetry(
                call_id=body.call_id or ticket.get("ticket_id", ""),
                ticket_id=ticket.get("ticket_id", ""),
                stt_provider="groq",
                stt_latency_ms=0,
                extraction_latency_ms=0,
                routing_latency_ms=0,
                stt_duration_sec=0.0,
                call_duration_sec=0.0,
                sms_sent=True,
                whatsapp_sent=True,
            )
        except Exception:
            pass

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
def get_ticket(ticket_id: str, user: Dict[str, Any] = Depends(rbac_service.get_current_user)) -> JSONResponse:
    ticket = ticket_service.get_ticket(ticket_id)
    if not ticket:
        return JSONResponse(status_code=404, content={"status": "error", "message": "Ticket not found"})
    
    # RBAC: department staff can only view their own department's tickets
    if user.get("role") == "department" and ticket.get("department") != user.get("department"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    
    return JSONResponse(status_code=200, content=ticket)


@router.get("/tickets")
def list_tickets(user: Dict[str, Any] = Depends(rbac_service.get_current_user)) -> JSONResponse:
    tickets = _get_filtered_tickets(user)
    return JSONResponse(status_code=200, content={"tickets": tickets})


@router.get("/analytics/summary")
def analytics_summary(user: Dict[str, Any] = Depends(rbac_service.get_current_user)) -> JSONResponse:
    tickets = _get_filtered_tickets(user)
    summary = {
        "total_tickets": len(tickets),
        "open_tickets": len([t for t in tickets if t.get("status") in ["created", "assigned", "in_progress"]]),
        "resolved_tickets": len([t for t in tickets if t.get("status") == "resolved"]),
        "sla_breaches": len([t for t in tickets if t.get("sla_breached")]),
    }
    return JSONResponse(status_code=200, content=summary)


@router.get("/analytics/issues")
def analytics_issues(user: Dict[str, Any] = Depends(rbac_service.get_current_user)) -> JSONResponse:
    tickets = _get_filtered_tickets(user)
    issue_counts = {}
    for t in tickets:
        issue_type = t.get("issue_type", "General")
        issue_counts[issue_type] = issue_counts.get(issue_type, 0) + 1
    return JSONResponse(status_code=200, content={"distribution": issue_counts})


@router.get("/analytics/regions")
def analytics_regions(user: Dict[str, Any] = Depends(rbac_service.get_current_user)) -> JSONResponse:
    tickets = _get_filtered_tickets(user)
    region_counts = {}
    for t in tickets:
        location = t.get("normalized_location", "Unknown")
        region_counts[location] = region_counts.get(location, 0) + 1
    return JSONResponse(status_code=200, content={"distribution": region_counts})


@router.get("/analytics/sla")
def analytics_sla(user: Dict[str, Any] = Depends(rbac_service.get_current_user)) -> JSONResponse:
    tickets = _get_filtered_tickets(user)
    sla_data = {
        "total_tickets": len(tickets),
        "breached_count": len([t for t in tickets if t.get("sla_breached")]),
        "on_track_count": len([t for t in tickets if not t.get("sla_breached") and t.get("status") != "resolved"]),
        "resolved_on_time": len([t for t in tickets if t.get("status") == "resolved" and not t.get("sla_breached")]),
    }
    return JSONResponse(status_code=200, content=sla_data)


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
def resolve_ticket(ticket_id: str, user: Dict[str, Any] = Depends(rbac_service.get_current_user)) -> JSONResponse:
    """Resolve a ticket (transition from in_progress → resolved)."""
    # Check authorization
    ticket = ticket_service.get_ticket(ticket_id)
    if not ticket:
        return JSONResponse(status_code=404, content={"status": "error", "message": "Ticket not found"})
    
    if user.get("role") == "department" and ticket.get("department") != user.get("department"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    
    # Update to resolved (with SLA checking)
    updated = ticket_service.resolve_ticket(ticket_id)
    if not updated:
        return JSONResponse(status_code=400, content={"status": "error", "message": "Cannot resolve ticket in current status"})
    
    return JSONResponse(status_code=200, content={"status": "resolved", "ticket": updated})


@router.post("/tickets/{ticket_id}/transition/in-progress")
def mark_in_progress(ticket_id: str, user: Dict[str, Any] = Depends(rbac_service.get_current_user)) -> JSONResponse:
    """Mark ticket as in-progress (assigned → in_progress)."""
    ticket = ticket_service.get_ticket(ticket_id)
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    
    if user.get("role") == "department" and ticket.get("department") != user.get("department"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    
    updated = ticket_service.transition_to_in_progress(ticket_id)
    if not updated:
        return JSONResponse(status_code=400, content={"status": "error", "message": "Cannot transition to in-progress"})
    
    return JSONResponse(status_code=200, content={"status": "in_progress", "ticket": updated})


@router.post("/tickets/{ticket_id}/transition/closed")
def mark_closed(ticket_id: str, user: Dict[str, Any] = Depends(rbac_service.get_current_user)) -> JSONResponse:
    """Close a resolved ticket (resolved → closed)."""
    ticket = ticket_service.get_ticket(ticket_id)
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    
    if user.get("role") == "department" and ticket.get("department") != user.get("department"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    
    updated = ticket_service.close_ticket(ticket_id)
    if not updated:
        return JSONResponse(status_code=400, content={"status": "error", "message": "Ticket is not resolved"})
    
    return JSONResponse(status_code=200, content={"status": "closed", "ticket": updated})


# ============ COST TRACKING ENDPOINTS ============

@router.post("/analytics/log-cost")
def log_call_cost(
    call_id: str,
    ticket_id: str = "",
    stt_duration_sec: float = 0.0,
    call_duration_sec: float = 0.0,
    sms_sent: bool = False,
    whatsapp_sent: bool = False,
    user: Dict[str, Any] = Depends(rbac_service.get_current_user),
) -> JSONResponse:
    """Log cost metrics for a call (STT, extraction, SMS, call charges)."""
    result = cost_service.log_call_telemetry(
        call_id=call_id,
        ticket_id=ticket_id,
        stt_duration_sec=stt_duration_sec,
        call_duration_sec=call_duration_sec,
        sms_sent=sms_sent,
        whatsapp_sent=whatsapp_sent,
    )
    return JSONResponse(status_code=200, content=result)


@router.get("/i18n/response")
def get_localized_response(
    language: str = "en",
    context_key: str = "issue_received",
    issue_type: str = "complaint",
    ticket_id: str = "",
    sla_hours: int = 24,
    user: Dict[str, Any] = Depends(rbac_service.get_current_user),
) -> JSONResponse:
    """Get localized response text for voice/SMS workflows."""
    text = language_response_service.get_response(
        language=language,
        context_key=context_key,
        variables={
            "issue_type": issue_type,
            "ticket_id": ticket_id,
            "sla_hours": sla_hours,
        },
    )
    return JSONResponse(status_code=200, content={"language": language, "context_key": context_key, "text": text})


@router.get("/analytics/cost-summary")
def get_cost_summary(
    start_date: str = "",
    end_date: str = "",
    user: Dict[str, Any] = Depends(rbac_service.get_current_user),
) -> JSONResponse:
    """Get cost summary for a time period (admin only)."""
    if user.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    
    summary = cost_service.get_cost_summary(start_date=start_date, end_date=end_date)
    return JSONResponse(status_code=200, content=summary)


@router.get("/tickets/{ticket_id}/cost")
def get_ticket_cost(ticket_id: str, user: Dict[str, Any] = Depends(rbac_service.get_current_user)) -> JSONResponse:
    """Get cost breakdown for a specific ticket."""
    ticket = ticket_service.get_ticket(ticket_id)
    if not ticket:
        return JSONResponse(status_code=404, content={"status": "error", "message": "Ticket not found"})
    
    if user.get("role") == "department" and ticket.get("department") != user.get("department"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    
    cost_data = cost_service.get_cost_per_ticket(ticket_id)
    return JSONResponse(status_code=200, content=cost_data)


# ============ ESCALATION ENDPOINTS ============

@router.post("/escalation/rules")
def create_escalation_rule(
    source_dept: str,
    dest_dept: str,
    escalation_level: int = 1,
    sla_minutes_threshold: int = 30,
    contact_method: str = "sms",
    user: Dict[str, Any] = Depends(rbac_service.get_current_user),
) -> JSONResponse:
    """Create escalation rule (admin only)."""
    if user.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    
    rule = escalation_service.create_escalation_rule(
        source_dept=source_dept,
        dest_dept=dest_dept,
        escalation_level=escalation_level,
        sla_minutes_threshold=sla_minutes_threshold,
        contact_method=contact_method,
    )
    return JSONResponse(status_code=201, content=rule)


@router.get("/escalation/rules/{dept_id}")
def get_escalation_chain(dept_id: str, user: Dict[str, Any] = Depends(rbac_service.get_current_user)) -> JSONResponse:
    """Get escalation chain for a department."""
    chain = escalation_service.get_escalation_chain(dept_id)
    return JSONResponse(status_code=200, content={"escalation_chain": chain})


@router.post("/escalation/trigger/{ticket_id}")
def trigger_escalation(
    ticket_id: str,
    escalation_level: int = 1,
    reason: str = "SLA threshold exceeded",
    user: Dict[str, Any] = Depends(rbac_service.get_current_user),
) -> JSONResponse:
    """Trigger escalation for a ticket."""
    ticket = ticket_service.get_ticket(ticket_id)
    if not ticket:
        return JSONResponse(status_code=404, content={"status": "error", "message": "Ticket not found"})
    
    current_dept = ticket.get("department")
    result = escalation_service.trigger_escalation(
        ticket_id=ticket_id,
        current_dept=current_dept,
        escalation_level=escalation_level,
        reason=reason,
    )
    
    if not result:
        return JSONResponse(
            status_code=400,
            content={"status": "error", "message": f"No escalation rule found for {current_dept} level {escalation_level}"},
        )
    
    return JSONResponse(status_code=200, content=result)


@router.get("/tickets/{ticket_id}/escalation-history")
def get_escalation_history(
    ticket_id: str,
    user: Dict[str, Any] = Depends(rbac_service.get_current_user),
) -> JSONResponse:
    """Get escalation history for a ticket."""
    ticket = ticket_service.get_ticket(ticket_id)
    if not ticket:
        return JSONResponse(status_code=404, content={"status": "error", "message": "Ticket not found"})
    
    if user.get("role") == "department" and ticket.get("department") != user.get("department"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    
    history = escalation_service.get_escalation_history(ticket_id)
    return JSONResponse(status_code=200, content={"escalation_history": history})


# ============ DATA PRIVACY & DELETION ============

@router.delete("/tickets/{ticket_id}")
def delete_ticket(
    ticket_id: str,
    user: Dict[str, Any] = Depends(rbac_service.get_current_user),
) -> JSONResponse:
    """Soft-delete a ticket (admin only, for GDPR compliance)."""
    if user.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    
    from app.services.db_service import get_connection
    with get_connection() as conn:
        conn.execute("UPDATE tickets SET deleted_at = datetime('now') WHERE ticket_id = ?", (ticket_id,))
    
    return JSONResponse(status_code=200, content={"status": "deleted", "ticket_id": ticket_id})


@router.post("/data-deletion-request/{mobile}")
def request_data_deletion(mobile: str, user: Dict[str, Any] = Depends(rbac_service.get_current_user)) -> JSONResponse:
    """Request data deletion for a mobile number (GDPR right to be forgotten)."""
    from app.services.db_service import get_connection
    from datetime import datetime
    
    # Only admin users can request deletion
    if user.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    
    # Mark all tickets for this mobile as deleted
    deletion_id = f"del_{mobile}_{int(datetime.utcnow().timestamp())}"
    with get_connection() as conn:
        conn.execute(
            "UPDATE tickets SET deleted_at = datetime('now'), deletion_request_id = ? WHERE mobile = ?",
            (deletion_id, mobile),
        )
        stats = conn.execute(
            "SELECT COUNT(*) AS ticket_count FROM tickets WHERE mobile = ?",
            (mobile,),
        ).fetchone()
        ticket_count = int(stats["ticket_count"] if stats else 0)
        conn.execute(
            """
            INSERT OR REPLACE INTO data_deletion_requests(
                deletion_request_id, mobile, requested_at, ticket_count, status, reason
            ) VALUES (?, ?, datetime('now'), ?, 'completed', 'admin_requested')
            """,
            (deletion_id, mobile, ticket_count),
        )
    
    return JSONResponse(
        status_code=200,
        content={
            "status": "deletion_requested",
            "deletion_id": deletion_id,
            "mobile": mobile,
            "message": "Data deletion request submitted. All records for this mobile will be deleted."
        },
    )


@router.get("/analytics/deletion-status/{deletion_id}")
def get_deletion_status(
    deletion_id: str,
    user: Dict[str, Any] = Depends(rbac_service.get_current_user),
) -> JSONResponse:
    """Check status of data deletion request."""
    if user.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    
    from app.services.db_service import get_connection
    with get_connection() as conn:
        request_row = conn.execute(
            """
            SELECT deletion_request_id, mobile, requested_at, completed_at, ticket_count, status, reason
            FROM data_deletion_requests
            WHERE deletion_request_id = ?
            """,
            (deletion_id,),
        ).fetchone()
        ticket_row = conn.execute(
            "SELECT COUNT(*) AS deleted_count, MAX(deleted_at) AS deletion_timestamp FROM tickets WHERE deletion_request_id = ?",
            (deletion_id,),
        ).fetchone()

    req = dict(request_row) if request_row else {}
    tickets = dict(ticket_row) if ticket_row else {"deleted_count": 0, "deletion_timestamp": None}
    return JSONResponse(
        status_code=200,
        content={
            "deletion_id": deletion_id,
            "status": req.get("status", "unknown"),
            "mobile": req.get("mobile"),
            "requested_at": req.get("requested_at"),
            "completed_at": req.get("completed_at"),
            "reason": req.get("reason"),
            "deleted_records": tickets.get("deleted_count", 0),
            "deletion_timestamp": tickets.get("deletion_timestamp"),
        },
    )
