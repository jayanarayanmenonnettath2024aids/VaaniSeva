import json
from typing import Any, Dict

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.services import analytics_service, notification_service, routing_service, sla_service, ticket_service

router = APIRouter()


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
    try:
        data = _safe_structured_data(body.structured_data, body.call_id)
        routing_info = routing_service.get_department(data.get("issue_type", ""))
        ticket = ticket_service.create_ticket(data, routing_info)

        sms_text = notification_service.format_sms(ticket)
        whatsapp_text = notification_service.format_whatsapp_message(ticket)
        sms_status = notification_service.send_sms(str(ticket.get("mobile", "")), sms_text)
        whatsapp_status = notification_service.send_whatsapp(
            str(ticket.get("mobile", "")),
            whatsapp_text,
        )

        return JSONResponse(
            status_code=200,
            content={
                "ticket_id": ticket.get("ticket_id", ""),
                "department": ticket.get("department", ""),
                "sla_hours": ticket.get("sla_hours", 24),
                "status": ticket.get("status", "created"),
                "sms": sms_status,
                "whatsapp": whatsapp_status,
            },
        )
    except Exception as exc:
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


@router.post("/sla-monitor")
def run_sla_monitor_endpoint() -> JSONResponse:
    return JSONResponse(status_code=200, content={"escalations": sla_service.run_sla_monitor()})


@router.post("/resolve-ticket/{ticket_id}")
def resolve_ticket(ticket_id: str) -> JSONResponse:
    updated = ticket_service.update_status(ticket_id, "resolved")
    if not updated:
        return JSONResponse(status_code=404, content={"status": "error", "message": "Ticket not found"})
    return JSONResponse(status_code=200, content={"status": "resolved", "ticket": updated})
