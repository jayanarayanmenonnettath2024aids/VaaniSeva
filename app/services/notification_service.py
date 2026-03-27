from typing import Any, Dict
import logging
import threading

import requests

from app.config import settings

logger = logging.getLogger(__name__)


def _send_async(fn, *args, **kwargs) -> None:
    def runner() -> None:
        try:
            fn(*args, **kwargs)
        except Exception as exc:
            logger.error("[MSG ASYNC ERROR] %s", exc)

    threading.Thread(target=runner, daemon=True).start()


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
    """Normalize to E.164 format: +91XXXXXXXXXX (strict 10-digit Indian validation)."""
    normalized = str(mobile or "").strip().replace(" ", "")
    if not normalized:
        return ""
    digits = "".join(ch for ch in normalized if ch.isdigit())
    if not digits:
        return ""
    
    # Use last 10 digits for India
    last_10 = digits[-10:]
    
    # Validate: should start with 6-9 for India mobile (strict validation)
    if not last_10 or last_10[0] not in "6789":
        return ""  # Invalid mobile prefix
    
    return f"+91{last_10}"


def _normalize_whatsapp_sender(value: str) -> str:
    sender = (value or "").strip()
    if sender.startswith("whatsapp:"):
        sender = sender.split("whatsapp:", 1)[1]
    return f"whatsapp:{sender}"


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
    """Send SMS via Twilio with E.164 format validation and strict timeouts."""
    normalized_mobile = normalize_phone(mobile)
    if not normalized_mobile:
        return {"status": "skipped", "reason": "mobile_invalid_format"}

    if not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_AUTH_TOKEN:
        return {"status": "skipped", "reason": "twilio_credentials_missing"}

    if not settings.TWILIO_PHONE_NUMBER:
        return {"status": "skipped", "reason": "twilio_from_number_missing"}

    payload = {
        "From": settings.TWILIO_PHONE_NUMBER,  # E.164 format: +1234567890 or short code
        "To": normalized_mobile,               # E.164 format: +919876543210
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
    """Send WhatsApp message via Twilio with E.164 format."""
    normalized_mobile = normalize_phone(mobile)
    if not normalized_mobile:
        return {"status": "skipped", "reason": "mobile_invalid_format"}

    if not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_AUTH_TOKEN:
        return {"status": "skipped", "reason": "twilio_credentials_missing"}
    if not settings.TWILIO_WHATSAPP_NUMBER:
        return {"status": "skipped", "reason": "whatsapp_number_missing"}

    # WhatsApp format requires E.164 with whatsapp: prefix
    # From: Twilio sandbox (+14155238886) or your verified business number
    payload = {
        "From": _normalize_whatsapp_sender(settings.TWILIO_WHATSAPP_NUMBER),
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
