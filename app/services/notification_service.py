from typing import Any, Dict
import logging

import requests

from app.config import settings

logger = logging.getLogger(__name__)


def format_sms(ticket: Dict[str, Any]) -> str:
    priority = str(ticket.get("priority", "low")).upper()
    return (
        f"Dear {ticket.get('customer_name', 'Citizen')}, your complaint has been registered. "
        f"Ticket ID: {ticket.get('ticket_id', '')} "
        f"Priority: {priority} "
        f"Department: {ticket.get('department', '')} "
        f"Resolution within: {ticket.get('sla_hours', 24)} hours."
    )


def normalize_phone(mobile: str) -> str:
    digits = "".join(ch for ch in (mobile or "") if ch.isdigit())
    if not digits:
        return ""
    if not str(mobile).startswith("+91"):
        return "+91" + digits[-10:]
    return "+91" + digits[-10:]


def format_whatsapp_message(ticket: Dict[str, Any]) -> str:
    return (
        f"Hello {ticket.get('customer_name', 'Citizen')}! 👋\n\n"
        f"🎫 Ticket ID: {ticket.get('ticket_id', '')}\n"
        f"📋 Issue: {ticket.get('issue', '')}\n"
        f"🏢 Department: {ticket.get('department', '')}\n"
        f"📍 Location: {ticket.get('location', '')}\n"
        f"⏰ SLA: {ticket.get('sla_hours', 24)} hours"
    )


def _twilio_messages_url() -> str:
    return (
        "https://api.twilio.com/2010-04-01/Accounts/"
        f"{settings.TWILIO_ACCOUNT_SID}/Messages.json"
    )


def send_sms(mobile: str, message: str) -> Dict[str, Any]:
    normalized_mobile = normalize_phone(mobile)
    if not normalized_mobile:
        return {"status": "skipped", "reason": "mobile_missing"}

    if not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_AUTH_TOKEN:
        return {"status": "skipped", "reason": "twilio_credentials_missing"}

    payload = {
        "From": settings.TWILIO_PHONE_NUMBER,
        "To": normalized_mobile,
        "Body": message,
    }

    try:
        response = requests.post(
            _twilio_messages_url(),
            data=payload,
            auth=(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN),
            timeout=5,
        )
        response.raise_for_status()
        return {"status": "sent", "provider_response": response.json() if response.content else {}}
    except requests.Timeout:
        logger.exception("Twilio SMS timeout")
        return {"status": "error", "error": "sms_timeout"}
    except requests.RequestException as exc:
        logger.exception("Twilio SMS request failed: %s", exc)
        return {"status": "error", "error": "sms_failed", "message": str(exc)}


def send_whatsapp(mobile: str, message: str) -> Dict[str, Any]:
    normalized_mobile = normalize_phone(mobile)
    if not normalized_mobile:
        return {"status": "skipped", "reason": "mobile_missing"}

    if not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_AUTH_TOKEN:
        return {"status": "skipped", "reason": "twilio_credentials_missing"}

    payload = {
        "From": f"whatsapp:{settings.TWILIO_WHATSAPP_NUMBER}",
        "To": f"whatsapp:{normalized_mobile}",
        "Body": message,
    }

    try:
        response = requests.post(
            _twilio_messages_url(),
            data=payload,
            auth=(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN),
            timeout=5,
        )
        response.raise_for_status()
        return {"status": "sent", "provider_response": response.json() if response.content else {}}
    except requests.Timeout:
        logger.exception("Twilio WhatsApp timeout")
        return {"status": "error", "error": "whatsapp_timeout"}
    except requests.RequestException as exc:
        logger.exception("Twilio WhatsApp request failed: %s", exc)
        return {"status": "error", "error": "whatsapp_failed", "message": str(exc)}
