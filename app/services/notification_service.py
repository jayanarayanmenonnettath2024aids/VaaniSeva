from datetime import datetime, timedelta
from typing import Any, Dict, Optional
import logging
import threading

import requests

from app.config import settings

logger = logging.getLogger(__name__)

_sms_blocked_until: Optional[datetime] = None
_wa_blocked_until: Optional[datetime] = None


def _remaining_block_seconds(until: Optional[datetime]) -> int:
    if not until:
        return 0
    remaining = int((until - datetime.utcnow()).total_seconds())
    return remaining if remaining > 0 else 0


def _retry_after_seconds(response: requests.Response) -> int:
    raw = response.headers.get("Retry-After", "").strip()
    if raw.isdigit():
        return max(1, int(raw))
    # Twilio may omit Retry-After; use conservative default.
    return 300


def _msg_account_sid() -> str:
    return settings.TWILIO_MSG_ACCOUNT_SID


def _msg_auth_token() -> str:
    return settings.TWILIO_MSG_AUTH_TOKEN


def _sms_from_number() -> str:
    return settings.TWILIO_SMS_NUMBER


def _send_async(fn, *args, **kwargs) -> None:
    def runner() -> None:
        try:
            result = fn(*args, **kwargs)
            if isinstance(result, dict):
                logger.info("[MSG ASYNC RESULT] %s", result)
        except Exception as exc:
            logger.error("[MSG ASYNC ERROR] %s", exc)

    threading.Thread(target=runner, daemon=True).start()


def format_sms(ticket: Dict[str, Any]) -> str:
    customer_name = str(ticket.get("customer_name", "") or "Customer")
    ticket_id = str(ticket.get("ticket_id", "") or "")
    issue = str(ticket.get("issue", "") or "General complaint")
    department = str(ticket.get("department", "") or "General Department")
    location = str(
        ticket.get("normalized_location", "")
        or ticket.get("location", "")
        or "Unknown"
    )
    sla_hours = int(ticket.get("sla_hours", 24) or 24)
    return (
        f"Hello {customer_name}!\n\n"
        "Your complaint has been registered successfully.\n\n"
        f"Ticket ID  : {ticket_id}\n"
        f"Issue      : {issue}\n"
        f"Department : {department}\n"
        f"Location   : {location}\n"
        f"SLA        : {sla_hours} hours\n\n"
        "We will resolve your issue shortly.\n"
        "Thank you for reaching out!"
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
    customer_name = str(ticket.get("customer_name", "") or "Customer")
    ticket_id = str(ticket.get("ticket_id", "") or "")
    issue = str(ticket.get("issue", "") or "General complaint")
    department = str(ticket.get("department", "") or "General Department")
    location = str(
        ticket.get("normalized_location", "")
        or ticket.get("location", "")
        or "Unknown"
    )
    sla_hours = int(ticket.get("sla_hours", 24) or 24)
    return (
        f"Hello {customer_name}! 👋\n\n"
        "Your complaint has been registered successfully.\n\n"
        f"🎫 Ticket ID  : {ticket_id}\n"
        f"📋 Issue      : {issue}\n"
        f"🏢 Department : {department}\n"
        f"📍 Location   : {location}\n"
        f"⏰ SLA        : {sla_hours} hours\n\n"
        "We will resolve your issue shortly.\n"
        "Thank you for reaching out!"
    )


def send_customer_notifications(mobile: str, sms_message: str, whatsapp_message: str) -> Dict[str, Any]:
    """Send SMS and WhatsApp with one retry on Twilio rate-limit.

    This keeps call flow non-blocking while making delivery more resilient.
    """
    normalized_mobile = normalize_phone(mobile)
    if not normalized_mobile:
        return {"status": "skipped", "reason": "mobile_invalid_format"}

    sms_result = send_sms(normalized_mobile, sms_message)
    wa_result = send_whatsapp(normalized_mobile, whatsapp_message)

    # If Twilio asks us to back off, perform a single delayed retry in background.
    retry_after = 0
    if isinstance(sms_result, dict) and sms_result.get("error") == "sms_rate_limited":
        retry_after = max(retry_after, int(sms_result.get("retry_after_seconds", 0) or 0))
    if isinstance(wa_result, dict) and wa_result.get("error") == "whatsapp_rate_limited":
        retry_after = max(retry_after, int(wa_result.get("retry_after_seconds", 0) or 0))

    if retry_after > 0:
        def delayed_retry() -> None:
            try:
                logger.info("[MSG RETRY] Rate-limited. Retrying SMS/WhatsApp after %ss for %s", retry_after, normalized_mobile)
                threading.Event().wait(retry_after)
                retry_sms = send_sms(normalized_mobile, sms_message)
                retry_wa = send_whatsapp(normalized_mobile, whatsapp_message)
                logger.info("[MSG RETRY RESULT] SMS=%s WHATSAPP=%s", retry_sms, retry_wa)
            except Exception as exc:
                logger.error("[MSG RETRY ERROR] %s", exc)

        threading.Thread(target=delayed_retry, daemon=True).start()

    return {
        "status": "ok",
        "sms": sms_result,
        "whatsapp": wa_result,
        "retry_scheduled": retry_after > 0,
        "retry_after_seconds": retry_after,
    }


def _twilio_messages_url() -> str:
    account_sid = _msg_account_sid()
    return (
        "https://api.twilio.com/2010-04-01/Accounts/"
        f"{account_sid}/Messages.json"
    )


def _message_status_callback_url() -> str:
    base = str(settings.BASE_URL or "").strip().rstrip("/")
    if not base:
        return ""
    return f"{base}/message-status"


def send_sms(mobile: str, message: str) -> Dict[str, Any]:
    """Send SMS via Twilio with E.164 format validation and strict timeouts."""
    global _sms_blocked_until

    blocked_seconds = _remaining_block_seconds(_sms_blocked_until)
    if blocked_seconds > 0:
        return {
            "status": "skipped",
            "reason": "sms_rate_limited",
            "retry_after_seconds": blocked_seconds,
        }

    normalized_mobile = normalize_phone(mobile)
    if not normalized_mobile:
        return {"status": "skipped", "reason": "mobile_invalid_format"}

    account_sid = _msg_account_sid()
    auth_token = _msg_auth_token()
    sms_from = _sms_from_number()

    if not account_sid or not auth_token:
        return {"status": "skipped", "reason": "twilio_credentials_missing"}

    if not sms_from:
        return {"status": "skipped", "reason": "twilio_from_number_missing"}

    payload = {
        "From": sms_from,                      # E.164 format: +1234567890 or short code
        "To": normalized_mobile,               # E.164 format: +919876543210
        "Body": message,
    }
    callback_url = _message_status_callback_url()
    if callback_url:
        payload["StatusCallback"] = callback_url

    try:
        response = requests.post(
            _twilio_messages_url(),
            data=payload,
            auth=(account_sid, auth_token),
            timeout=5,
        )
        response.raise_for_status()
        return {"status": "sent", "provider_response": response.json() if response.content else {}}
    except requests.Timeout:
        logger.exception("Twilio SMS timeout")
        return {"status": "error", "error": "sms_timeout"}
    except requests.RequestException as exc:
        response = getattr(exc, "response", None)
        if response is not None and response.status_code == 429:
            retry_after = _retry_after_seconds(response)
            _sms_blocked_until = datetime.utcnow() + timedelta(seconds=retry_after)
            logger.warning(
                "Twilio SMS rate-limited (429). Pausing SMS sends for %ss.",
                retry_after,
            )
            return {
                "status": "error",
                "error": "sms_rate_limited",
                "message": "Twilio SMS rate-limited",
                "retry_after_seconds": retry_after,
            }
        logger.exception("Twilio SMS request failed: %s", exc)
        return {"status": "error", "error": "sms_failed", "message": str(exc)}


def send_whatsapp(mobile: str, message: str) -> Dict[str, Any]:
    """Send WhatsApp message via Twilio with E.164 format."""
    global _wa_blocked_until

    blocked_seconds = _remaining_block_seconds(_wa_blocked_until)
    if blocked_seconds > 0:
        return {
            "status": "skipped",
            "reason": "whatsapp_rate_limited",
            "retry_after_seconds": blocked_seconds,
        }

    normalized_mobile = normalize_phone(mobile)
    if not normalized_mobile:
        return {"status": "skipped", "reason": "mobile_invalid_format"}

    account_sid = _msg_account_sid()
    auth_token = _msg_auth_token()

    if not account_sid or not auth_token:
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
    callback_url = _message_status_callback_url()
    if callback_url:
        payload["StatusCallback"] = callback_url

    try:
        response = requests.post(
            _twilio_messages_url(),
            data=payload,
            auth=(account_sid, auth_token),
            timeout=5,
        )
        response.raise_for_status()
        return {"status": "sent", "provider_response": response.json() if response.content else {}}
    except requests.Timeout:
        logger.exception("Twilio WhatsApp timeout")
        return {"status": "error", "error": "whatsapp_timeout"}
    except requests.RequestException as exc:
        response = getattr(exc, "response", None)
        if response is not None and response.status_code == 429:
            retry_after = _retry_after_seconds(response)
            _wa_blocked_until = datetime.utcnow() + timedelta(seconds=retry_after)
            logger.warning(
                "Twilio WhatsApp rate-limited (429). Pausing WhatsApp sends for %ss.",
                retry_after,
            )
            return {
                "status": "error",
                "error": "whatsapp_rate_limited",
                "message": "Twilio WhatsApp rate-limited",
                "retry_after_seconds": retry_after,
            }
        logger.exception("Twilio WhatsApp request failed: %s", exc)
        return {"status": "error", "error": "whatsapp_failed", "message": str(exc)}
