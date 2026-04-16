from typing import Any, Dict
from xml.sax.saxutils import escape

import requests

from app.config import settings


def _say_language_code(language: str) -> str:
    lang = (language or "en").strip().lower()
    mapping = {
        "en": "en-IN",
        "ta": "ta-IN",
        "hi": "hi-IN",
        "ml": "ml-IN",
        "te": "te-IN",
    }
    return mapping.get(lang, "en-IN")


def _say_tag(message: str, language: str = "en") -> str:
    safe_message = escape(message)
    say_lang = _say_language_code(language)
    if say_lang == "en-IN":
        return f"  <Say voice=\"alice\" language=\"{say_lang}\">{safe_message}</Say>\n"
    return f"  <Say language=\"{say_lang}\">{safe_message}</Say>\n"


def _voice_account_sid() -> str:
    return settings.TWILIO_VOICE_ACCOUNT_SID


def _voice_auth_token() -> str:
    return settings.TWILIO_VOICE_AUTH_TOKEN


def _twilio_calls_url() -> str:
    account_sid = _voice_account_sid()
    return (
        "https://api.twilio.com/2010-04-01/Accounts/"
        f"{account_sid}/Calls.json"
    )


def _voice_from_number() -> str:
    return settings.TWILIO_VOICE_NUMBER


def create_call(to: str, message_url: str) -> Dict[str, Any]:
    account_sid = _voice_account_sid()
    auth_token = _voice_auth_token()

    if not account_sid or not auth_token:
        raise RuntimeError("Twilio credentials are not configured")

    voice_from = _voice_from_number()
    if not voice_from:
        raise RuntimeError("Twilio voice from number is not configured")

    payload = {
        "From": voice_from,
        "To": to,
        "Url": message_url,
        "Method": "POST",
    }

    try:
        response = requests.post(
            _twilio_calls_url(),
            data=payload,
            auth=(account_sid, auth_token),
            timeout=5,
        )
        response.raise_for_status()
        data = response.json() if response.content else {}
        return {
            "status": "ok",
            "provider": "twilio",
            "call_sid": data.get("sid", ""),
            "provider_response": data,
        }
    except requests.Timeout:
        return {"status": "error", "error": "twilio_timeout", "message": "Twilio request timed out"}
    except requests.RequestException as exc:
        response = getattr(exc, "response", None)
        provider_status = response.status_code if response is not None else None
        provider_body: Dict[str, Any] | str | None = None
        provider_code = None
        provider_message = None

        if response is not None:
            try:
                provider_body = response.json()
                if isinstance(provider_body, dict):
                    provider_code = provider_body.get("code")
                    provider_message = provider_body.get("message")
            except Exception:
                provider_body = response.text

        return {
            "status": "error",
            "error": "twilio_request_failed",
            "message": str(exc),
            "provider_status_code": provider_status,
            "provider_error_code": provider_code,
            "provider_error_message": provider_message,
            "provider_response": provider_body,
        }


def generate_response_xml(message: str, language: str = "en") -> str:
    """Generate TwiML response with voice feedback and recording action callback."""
    action_url = f"{settings.BASE_URL}/process-recording"
    return (
        "<Response>\n"
        f"{_say_tag(message, language)}"
        "  <Pause length=\"1\" />\n"
        f"  <Record maxLength=\"30\" action=\"{action_url}\" method=\"POST\" timeout=\"5\" maxSilence=\"3\" />\n"
        "</Response>"
    )


def generate_processing_response_xml() -> str:
    """Generate TwiML processing feedback while the AI pipeline runs asynchronously."""
    return (
        "<Response>\n"
        "  <Say voice=\"alice\">Thank you. Please wait while we process your request.</Say>\n"
        "  <Pause length=\"2\" />\n"
        "</Response>"
    )


def generate_final_message_xml(message: str, language: str = "en") -> str:
    """Generate one-shot TwiML response and end call (no additional recording loop)."""
    return (
        "<Response>\n"
        f"{_say_tag(message, language)}"
        "  <Pause length=\"1\" />\n"
        "  <Hangup />\n"
        "</Response>"
    )


def generate_followup_response_xml(message: str, followup_prompt: str, language: str = "en") -> str:
    """Speak current acknowledgment and continue call for another complaint turn."""
    action_url = f"{settings.BASE_URL}/process-recording"
    # Hold music URL (royalty-free, public domain hold music)
    hold_music_url = "https://upload.wikimedia.org/wikipedia/commons/d/d5/Zapsplat_retro_80s_style_synthwave_backing_track_007.mp3"
    return (
        "<Response>\n"
        f"{_say_tag(message, language)}"
        "  <Pause length=\"1\" />\n"
        f"{_say_tag(followup_prompt, language)}"
        "  <Pause length=\"1\" />\n"
        f"  <Record maxLength=\"30\" action=\"{action_url}\" method=\"POST\" timeout=\"5\" maxSilence=\"3\" />\n"
        "</Response>"
    )
