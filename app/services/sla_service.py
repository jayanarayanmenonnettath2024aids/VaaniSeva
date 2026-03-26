from datetime import datetime
import threading
import time
from typing import Any, Dict, List

import requests

from app.config import settings
from app.services import notification_service, ticket_service


_monitor_started = False


def check_sla(ticket: Dict[str, Any]) -> Dict[str, Any]:
    try:
        deadline = datetime.fromisoformat(str(ticket.get("sla_deadline", "")))
    except Exception:
        return {"breached": False}

    status = str(ticket.get("status", "")).lower()
    breached = datetime.utcnow() > deadline and status != "resolved"
    return {"breached": breached}


def _trigger_escalation_call(ticket: Dict[str, Any]) -> Dict[str, Any]:
    escalation_url = settings.ESCALATION_CALL_URL or f"{settings.BASE_URL}/escalate-call"
    payload = {
        "ticket_id": ticket.get("ticket_id", ""),
        "mobile": notification_service.normalize_phone(str(ticket.get("mobile", ""))),
        "reason": "sla_breached",
    }

    try:
        response = requests.post(escalation_url, json=payload, timeout=5)
        return {
            "status": "ok" if response.ok else "error",
            "status_code": response.status_code,
        }
    except requests.Timeout:
        return {"status": "error", "error": "escalation_timeout"}
    except requests.RequestException as exc:
        return {"status": "error", "error": "escalation_failed", "message": str(exc)}


def run_sla_monitor() -> List[Dict[str, Any]]:
    escalations: List[Dict[str, Any]] = []

    for ticket in ticket_service.list_tickets().values():
        if ticket.get("status") == "resolved":
            continue

        result = check_sla(ticket)
        if not result.get("breached"):
            continue

        sms_message = f"Your complaint {ticket.get('ticket_id', '')} is delayed. We are escalating."
        sms_status = notification_service.send_sms(str(ticket.get("mobile", "")), sms_message)
        escalation_status = _trigger_escalation_call(ticket)

        escalations.append(
            {
                "ticket_id": ticket.get("ticket_id", ""),
                "sms": sms_status,
                "outbound_call": escalation_status,
            }
        )

    return escalations


def sla_background() -> None:
    while True:
        run_sla_monitor()
        time.sleep(60)


def start_sla_background_monitor() -> None:
    global _monitor_started
    if _monitor_started:
        return

    thread = threading.Thread(target=sla_background, daemon=True)
    thread.start()
    _monitor_started = True
