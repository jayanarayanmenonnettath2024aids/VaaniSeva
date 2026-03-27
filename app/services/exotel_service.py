from typing import Any, Dict
from xml.sax.saxutils import escape

import requests

from app.config import settings


def get_account(account_type: str) -> Dict[str, str]:
    if account_type == "inbound":
        return {
            "sid": settings.EXOTEL_SID_INBOUND,
            "token": settings.EXOTEL_TOKEN_INBOUND,
            "number": settings.EXOTEL_NUMBER_INBOUND,
        }

    if account_type == "outbound":
        return {
            "sid": settings.EXOTEL_SID_OUTBOUND,
            "token": settings.EXOTEL_TOKEN_OUTBOUND,
            "number": settings.EXOTEL_NUMBER_OUTBOUND,
        }

    raise ValueError("account_type must be 'inbound' or 'outbound'")


def create_call(to: str, message_url: str) -> Dict[str, Any]:
    account = get_account("outbound")
    sid = account["sid"]
    token = account["token"]

    if not sid or not token:
        raise RuntimeError("Outbound Exotel credentials are not configured")

    endpoint = f"{settings.EXOTEL_API_BASE_URL}/Accounts/{sid}/Calls/connect.json"

    payload = {
        "From": account["number"],
        "To": to,
        "Url": message_url,
        "CallerId": account["number"],
    }

    try:
        response = requests.post(
            endpoint,
            data=payload,
            auth=(sid, token),
            timeout=5,
        )
        response.raise_for_status()
        return response.json()
    except requests.Timeout:
        return {"status": "error", "error": "exotel_timeout", "message": "Exotel request timed out"}
    except requests.RequestException as exc:
        return {
            "status": "error",
            "error": "exotel_request_failed",
            "message": str(exc),
        }


def generate_response_xml(message: str) -> str:
    """Generate Exotel XML response with voice feedback."""
    safe_message = escape(message)
    action_url = f"{settings.BASE_URL}/process-recording"
    return (
        "<Response>\n"
        f"  <Say voice=\"woman\">{safe_message}</Say>\n"
        f"  <Record maxLength=\"30\" action=\"{action_url}\" />\n"
        "</Response>"
    )


def generate_processing_response_xml() -> str:
    """Generate processing feedback XML (plays while system processes request)."""
    return (
        "<Response>\n"
        "  <Say voice=\"woman\">Thank you. Please wait while we process your request.</Say>\n"
        "  <Pause length=\"2\" />\n"
        "</Response>"
    )
