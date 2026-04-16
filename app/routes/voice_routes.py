import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from typing import Any, Dict
from urllib.parse import parse_qs, quote_plus
from uuid import uuid4

import requests
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel

from app.config import settings
from app.services import (
    audit_service,
    extraction_service,
    language_service,
    notification_service,
    routing_service,
    session_service,
    stt_service,
    ticket_service,
    twilio_voice_service,
)
from app.utils.validators import validate_json

logger = logging.getLogger(__name__)

router = APIRouter()


def _run_stt_with_timeout(
    recording_url: str,
    timeout_sec: float = 8.0,
    preferred_language: str = "",
) -> Dict[str, str]:
    # Twilio webhooks have strict response timing. Bound STT time to avoid call-side
    # "application error" when model inference is slow.
    executor = ThreadPoolExecutor(max_workers=1)
    future = executor.submit(stt_service.process_audio, recording_url, preferred_language)
    try:
        return future.result(timeout=timeout_sec)
    finally:
        executor.shutdown(wait=False, cancel_futures=True)


def _backfill_ticket_after_timeout(call_id: str, recording_url: str, preferred_language: str = "") -> None:
    """Best-effort delayed STT backfill for timeout path.

    We acknowledge the caller quickly, then try to enrich the ticket asynchronously
    if STT finishes shortly after timeout.
    """
    try:
        stt_result = stt_service.process_audio(recording_url, preferred_language=preferred_language)
        text = str(stt_result.get("text", "") or "").strip()
        if not text:
            return

        issue_type = "General"
        try:
            structured = validate_json(extraction_service.extract_issue(text))
            issue_type = str(structured.get("issue_type", "General") or "General")
        except Exception:
            issue_type = _infer_issue_type(text)

        if ticket_service.backfill_issue_for_call(call_id=call_id, issue=text, issue_type=issue_type):
            logger.info("[Voice] Backfilled timed-out ticket with STT text for call_id=%s", call_id)
    except Exception as exc:
        logger.warning("[Voice] Timeout backfill failed for call_id=%s: %s", call_id, exc)


class OutboundCallRequest(BaseModel):
    mobile: str
    message: str


class SimulateRecordingRequest(BaseModel):
    text: str


def _build_outbound_prompt(message: str) -> str:
    intro = "Welcome to VaaniSeva civic complaint helpline. I am your AI voice assistant. "
    body = (message or "").strip()
    if not body:
        body = "Please describe your complaint after the beep."
    return f"{intro}{body}"


def _normalize_recording_url(recording_url: str) -> str:
    """Twilio often sends RecordingUrl without extension; many STT providers expect a concrete audio format."""
    url = (recording_url or "").strip()
    if not url:
        return ""

    lower_url = url.lower()
    if any(lower_url.endswith(ext) for ext in (".wav", ".mp3", ".m4a", ".aac", ".ogg")):
        return url

    # Twilio RecordingUrl can be extension-less; .wav is a reliable default export format.
    return f"{url}.wav"


def _forward_to_ai_engine(payload: Dict[str, Any]) -> Dict[str, Any]:
    if not settings.AI_ENGINE_URL:
        logger.warning("AI_ENGINE_URL not configured. Skipping AI ENGINE forwarding.")
        return {"status": "skipped", "reason": "AI_ENGINE_URL not configured"}

    try:
        response = requests.post(settings.AI_ENGINE_URL, json=payload, timeout=5)
        response.raise_for_status()
        return {"status": "ok"}
    except requests.Timeout:
        logger.exception("AI ENGINE request timed out")
        return {
            "status": "error",
            "error": "ai_engine_timeout",
            "message": "AI ENGINE request timed out",
        }
    except Exception as exc:
        # AI engine errors must not break voice pipeline.
        logger.exception("Failed to forward payload to AI ENGINE: %s", exc)
        return {
            "status": "error",
            "error": "ai_engine_request_failed",
            "message": str(exc),
        }


def _forward_to_ai_engine_async(payload: Dict[str, Any]) -> None:
    if not settings.AI_ENGINE_URL:
        return

    try:
        requests.post(settings.AI_ENGINE_URL, json=payload, timeout=3)
    except Exception as exc:
        logger.error("[AI ASYNC ERROR] %s", exc)


def _infer_issue_type(text: str) -> str:
    text_lower = (text or "").lower()
    if "road" in text_lower or "pothole" in text_lower:
        return "Road"
    if "water" in text_lower:
        return "Water"
    if "electric" in text_lower or "power" in text_lower:
        return "Electricity"
    if "garbage" in text_lower or "waste" in text_lower:
        return "Garbage"
    return "General"


def _should_end_conversation(text: str, language: str) -> bool:
    t = (text or "").strip().lower()
    if not t:
        return False

    # Avoid ending on complaint phrases like "no water" by using short utterance guard.
    token_count = len([tok for tok in t.split() if tok])
    if token_count > 4:
        return False

    endings = {
        "en": {"no", "nope", "nothing", "that's all", "thats all", "done", "stop", "bye", "thank you"},
        "ta": {"இல்லை", "வேண்டாம்", "போதும்", "நன்றி", "பை", "முடிந்தது"},
        "hi": {"नहीं", "बस", "धन्यवाद", "बाय", "खत्म"},
        "ml": {"ഇല്ല", "മതി", "നന്ദി", "ബൈ"},
        "te": {"లేదు", "చాలు", "ధన్యవాదాలు", "బై"},
    }
    terms = endings.get(language, endings["en"])
    return any(term in t for term in terms)


def _followup_prompt_for_language(language: str) -> str:
    prompts = {
        "en": "If you have another complaint, please speak after the beep. Or say no to end the call.",
        "ta": "உங்களுக்கு மேலும் புகார் இருந்தால் பீப் ஒலிக்குப் பிறகு சொல்லுங்கள். அழைப்பை முடிக்க வேண்டுமெனில் இல்லை என்று சொல்லுங்கள்.",
        "hi": "अगर आपके पास एक और शिकायत है तो बीप के बाद बोलिए। कॉल समाप्त करने के लिए नहीं बोलिए।",
        "ml": "ഇനിയൊരു പരാതി ഉണ്ടെങ്കിൽ ബീപിന് ശേഷം പറയുക. കോൾ അവസാനിപ്പിക്കാൻ വേണ്ടെന്ന് പറയുക.",
        "te": "మీకు ఇంకో ఫిర్యాదు ఉంటే బీప్ తర్వాత చెప్పండి. కాల్ ముగించాలంటే లేదు అని చెప్పండి.",
    }
    return prompts.get(language, prompts["en"])


def _send_post_call_notifications(call_id: str, mobile: str) -> None:
    clean_call_id = str(call_id or "").strip()
    clean_mobile = str(mobile or "").strip()
    if not clean_call_id or not clean_mobile:
        logger.warning(
            "[Voice] Post-call notification skipped: call_id/mobile missing (call_id=%s)",
            clean_call_id,
        )
        return

    try:
        tickets = [
            t for t in ticket_service.list_tickets().values()
            if str(t.get("call_id", "") or "") == clean_call_id
        ]
        if not tickets:
            logger.warning("[Voice] Post-call notification skipped: no ticket found for call_id=%s", clean_call_id)
            return

        latest_ticket = tickets[-1]
        sms_text = notification_service.format_sms(latest_ticket)
        whatsapp_text = notification_service.format_whatsapp_message(latest_ticket)
        result = notification_service.send_customer_notifications(
            clean_mobile,
            sms_text,
            whatsapp_text,
        )
        logger.info(
            "[Voice] Post-call notifications processed for call_id=%s, ticket_id=%s, mobile=%s, result=%s",
            clean_call_id,
            str(latest_ticket.get("ticket_id", "") or ""),
            clean_mobile,
            result,
        )
    except Exception as exc:
        logger.exception("[Voice] Failed to queue post-call notifications for call_id=%s: %s", clean_call_id, exc)


def _build_voice_ack(issue_type: str, ticket_id: str = "", include_ticket_id: bool = False) -> str:
    return _build_voice_ack_for_language(
        issue_type=issue_type,
        language="en",
        ticket_id=ticket_id,
        include_ticket_id=include_ticket_id,
    )


def _localize_issue_type(issue_type: str, language: str) -> str:
    normalized_issue = (issue_type or "General").strip() or "General"
    issue_labels = {
        "en": {
            "Road": "road",
            "Water": "water",
            "Electricity": "electricity",
            "Garbage": "garbage",
            "Street Light": "street light",
            "General": "general",
        },
        "ta": {
            "Road": "சாலை",
            "Water": "தண்ணீர்",
            "Electricity": "மின்சாரம்",
            "Garbage": "குப்பை",
            "Street Light": "தெரு விளக்கு",
            "General": "பொது",
        },
        "hi": {
            "Road": "सड़क",
            "Water": "पानी",
            "Electricity": "बिजली",
            "Garbage": "कचरा",
            "Street Light": "स्ट्रीट लाइट",
            "General": "सामान्य",
        },
        "ml": {
            "Road": "റോഡ്",
            "Water": "വെള്ളം",
            "Electricity": "വൈദ്യുതി",
            "Garbage": "മാലിന്യം",
            "Street Light": "തെരുവ് വെളിച്ചം",
            "General": "പൊതു",
        },
        "te": {
            "Road": "రోడు",
            "Water": "నీరు",
            "Electricity": "విద్యుత్",
            "Garbage": "చెత్త",
            "Street Light": "వీధి దీపం",
            "General": "సాధారణ",
        },
    }

    lang = language if language in issue_labels else "en"
    return issue_labels[lang].get(normalized_issue, issue_labels[lang]["General"])


def _build_voice_ack_for_language(
    issue_type: str,
    language: str,
    ticket_id: str = "",
    include_ticket_id: bool = False,
) -> str:
    lang = language if language in {"en", "ta", "hi", "ml", "te"} else "en"
    localized_issue = _localize_issue_type(issue_type, lang)

    templates = {
        "en": {
            "base": "Thank you. I understood your issue as {issue}. Your complaint is registered and will be addressed soon.",
            "with_ticket": "Thank you. I understood your issue as {issue}. Your complaint is registered. Your ticket ID is {ticket_id}.",
        },
        "ta": {
            "base": "நன்றி. உங்கள் பிரச்சினை {issue} தொடர்பானது என்று புரிந்துகொண்டேன். உங்கள் புகார் பதிவு செய்யப்பட்டுள்ளது.",
            "with_ticket": "நன்றி. உங்கள் பிரச்சினை {issue} தொடர்பானது என்று புரிந்துகொண்டேன். உங்கள் புகார் பதிவு செய்யப்பட்டுள்ளது. உங்கள் டிக்கெட் எண் {ticket_id}.",
        },
        "hi": {
            "base": "धन्यवाद। मैंने आपकी शिकायत को {issue} समस्या के रूप में समझा है। आपकी शिकायत दर्ज हो गई है।",
            "with_ticket": "धन्यवाद। मैंने आपकी शिकायत को {issue} समस्या के रूप में समझा है। आपकी शिकायत दर्ज हो गई है। आपका टिकट आईडी {ticket_id} है।",
        },
        "ml": {
            "base": "നന്ദി. നിങ്ങളുടെ പരാതി {issue} പ്രശ്നമായി ഞാൻ മനസ്സിലാക്കി. പരാതി രജിസ്റ്റർ ചെയ്തിട്ടുണ്ട്.",
            "with_ticket": "നന്ദി. നിങ്ങളുടെ പരാതി {issue} പ്രശ്നമായി ഞാൻ മനസ്സിലാക്കി. പരാതി രജിസ്റ്റർ ചെയ്തിട്ടുണ്ട്. നിങ്ങളുടെ ടിക്കറ്റ് ഐഡി {ticket_id} ആണ്.",
        },
        "te": {
            "base": "ధన్యవాదాలు. మీ సమస్యను {issue} సమస్యగా గుర్తించాము. మీ ఫిర్యాదు నమోదు అయింది.",
            "with_ticket": "ధన్యవాదాలు. మీ సమస్యను {issue} సమస్యగా గుర్తించాము. మీ ఫిర్యాదు నమోదు అయింది. మీ టికెట్ ఐడి {ticket_id}.",
        },
    }

    variant = "with_ticket" if include_ticket_id and ticket_id else "base"
    return templates[lang][variant].format(issue=localized_issue, ticket_id=ticket_id)


async def _extract_form_data(request: Request) -> Dict[str, Any]:
    try:
        form = await request.form()
        return dict(form)
    except AssertionError:
        # Fall back to urlencoded parsing when python-multipart is not installed.
        raw_body = (await request.body()).decode("utf-8", errors="ignore")
        parsed = parse_qs(raw_body, keep_blank_values=True)
        return {k: (v[0] if isinstance(v, list) and v else "") for k, v in parsed.items()}


@router.post("/incoming-call")
async def incoming_call(request: Request) -> Response:
    started = time.perf_counter()
    form_data = await _extract_form_data(request)
    call_id = str(form_data.get("CallSid", ""))
    mobile = str(form_data.get("From", ""))

    if not call_id:
        audit_service.log_event(
            stage="voice",
            event_name="incoming_call",
            mobile=mobile,
            outcome="error",
            error_code="missing_call_id",
            latency_ms=int((time.perf_counter() - started) * 1000),
        )
        return Response(
            content=twilio_voice_service.generate_response_xml("Unable to process call."),
            media_type="application/xml",
            status_code=400,
        )

    session_service.create(call_id=call_id, mobile=mobile)
    audit_service.log_event(
        stage="voice",
        event_name="incoming_call",
        call_id=call_id,
        mobile=mobile,
        outcome="ok",
        latency_ms=int((time.perf_counter() - started) * 1000),
    )

    xml = twilio_voice_service.generate_response_xml(
        "Welcome to VaaniSeva voice system. Please speak after the beep."
    )
    return Response(content=xml, media_type="application/xml")


@router.post("/process-recording")
async def process_recording(request: Request) -> JSONResponse:
    started = time.perf_counter()
    form_data = await _extract_form_data(request)
    recording_url = str(form_data.get("RecordingUrl", ""))
    call_id = str(form_data.get("CallSid", ""))
    recording_url = _normalize_recording_url(recording_url)

    if not call_id or not recording_url:
        audit_service.log_event(
            stage="voice",
            event_name="process_recording",
            call_id=call_id,
            outcome="error",
            error_code="missing_fields",
            latency_ms=int((time.perf_counter() - started) * 1000),
        )
        return Response(
            content=twilio_voice_service.generate_final_message_xml(
                "We could not capture your recording. Please call again and speak after the beep."
            ),
            media_type="application/xml",
            status_code=200,
        )

    if not recording_url.startswith("http"):
        audit_service.log_event(
            stage="voice",
            event_name="process_recording",
            call_id=call_id,
            outcome="error",
            error_code="invalid_recording_url",
            latency_ms=int((time.perf_counter() - started) * 1000),
        )
        return Response(
            content=twilio_voice_service.generate_final_message_xml(
                "We could not process your recording. Please try again shortly."
            ),
            media_type="application/xml",
            status_code=200,
        )

    session = session_service.get(call_id)
    if not session:
        session = session_service.create(call_id=call_id, mobile="")
    
    # Ensure mobile is in session for all downstream operations
    session_mobile = session.get("mobile", "")
    if not session_mobile and recording_url.startswith("http"):
        logger.warning("[Voice] Session has no mobile for call_id=%s. Recording may not trigger notifications.", call_id)

    try:
        stt_timeout = float(settings.LOCAL_STT_TIMEOUT_SEC)
    except Exception:
        stt_timeout = 8.0

    preferred_language = str(session.get("language", "") or "")

    try:
        stt_result = _run_stt_with_timeout(
            recording_url,
            timeout_sec=stt_timeout,
            preferred_language=preferred_language,
        )
    except FuturesTimeoutError:
        mobile = session.get("mobile", "")
        audit_service.log_event(
            stage="voice",
            event_name="process_recording",
            call_id=call_id,
            mobile=mobile,
            outcome="error",
            error_code="stt_timeout",
            latency_ms=int((time.perf_counter() - started) * 1000),
        )
        # Create minimal ticket so action engine has something to process
        ticket_id = ""
        try:
            minimal_ticket = ticket_service.create_ticket(
                {
                    "call_id": call_id,
                    "mobile": mobile,
                    "issue": "",
                    "issue_type": "General",
                },
                routing_service.get_department("General")
            )
            ticket_id = str(minimal_ticket.get("ticket_id", "") or "")
            logger.info("[Voice] Created minimal ticket on STT timeout: %s", ticket_id)
            
            # Try to enrich minimal ticket in background if STT completes after timeout.
            threading.Thread(
                target=_backfill_ticket_after_timeout,
                args=(call_id, recording_url, preferred_language),
                daemon=True,
            ).start()
        except Exception as ticket_exc:
            logger.warning("[Voice] Failed to create minimal ticket on timeout: %s", ticket_exc)

        ack_message = (
            f"Thank you. A ticket has been raised. Your ticket ID is {ticket_id}. "
            "Our team will process your complaint and update you shortly."
            if ticket_id
            else "Thank you. Your complaint has been recorded. Our team will process it and update you shortly."
        )
        _send_post_call_notifications(call_id=call_id, mobile=str(mobile or ""))
        return Response(
            content=twilio_voice_service.generate_final_message_xml(
                ack_message,
                language=preferred_language or "en",
            ),
            media_type="application/xml",
            status_code=200,
        )
    except Exception as exc:
        mobile = session.get("mobile", "")
        logger.exception("Unexpected STT error: %s", exc)
        audit_service.log_event(
            stage="voice",
            event_name="process_recording",
            call_id=call_id,
            mobile=mobile,
            outcome="error",
            error_code="stt_exception",
            latency_ms=int((time.perf_counter() - started) * 1000),
        )
        # Create minimal ticket on STT crash
        ticket_id = ""
        try:
            minimal_ticket = ticket_service.create_ticket(
                {
                    "call_id": call_id,
                    "mobile": mobile,
                    "issue": f"STT processing error: {str(exc)[:100]}",
                    "issue_type": "General",
                },
                routing_service.get_department("General")
            )
            ticket_id = str(minimal_ticket.get("ticket_id", "") or "")
            logger.info("[Voice] Created minimal ticket on STT error: %s", ticket_id)
            
        except Exception as ticket_exc:
            logger.warning("[Voice] Failed to create minimal ticket on error: %s", ticket_exc)

        ack_message = (
            f"Thank you. A ticket has been raised. Your ticket ID is {ticket_id}. "
            "We had a temporary processing issue, but your complaint is safely registered."
            if ticket_id
            else "We are unable to process your speech right now. Please try again later."
        )
        _send_post_call_notifications(call_id=call_id, mobile=str(mobile or ""))
        return Response(
            content=twilio_voice_service.generate_final_message_xml(
                ack_message,
                language=preferred_language or "en",
            ),
            media_type="application/xml",
            status_code=200,
        )

    text = stt_result.get("text", "")
    language = stt_result.get("language", "unknown")

    logger.info("[Voice] STT result: text_len=%d, language=%s", len(text), language)
    
    if not text:
        mobile = session.get("mobile", "")
        audit_service.log_event(
            stage="voice",
            event_name="process_recording",
            call_id=call_id,
            mobile=mobile,
            outcome="error",
            error_code="stt_empty",
            latency_ms=int((time.perf_counter() - started) * 1000),
            meta={"language": language, "stt_status": "empty"},
        )
        # Create minimal ticket on empty transcription
        ticket_id = ""
        try:
            minimal_ticket = ticket_service.create_ticket(
                {
                    "call_id": call_id,
                    "mobile": mobile,
                    "issue": "Silent or unclear audio - awaiting manual review",
                    "issue_type": "General",
                },
                routing_service.get_department("General")
            )
            ticket_id = str(minimal_ticket.get("ticket_id", "") or "")
            logger.info("[Voice] Created minimal ticket for empty transcription: %s", ticket_id)
            
        except Exception as ticket_exc:
            logger.warning("[Voice] Failed to create minimal ticket for empty text: %s", ticket_exc)

        ack_message = (
            f"Thank you. A ticket has been raised. Your ticket ID is {ticket_id}. "
            "We could not clearly hear your complaint. Please call again and speak clearly."
            if ticket_id
            else "We could not understand your speech. Please call again and speak clearly."
        )
        _send_post_call_notifications(call_id=call_id, mobile=str(mobile or ""))
        return Response(
            content=twilio_voice_service.generate_final_message_xml(
                ack_message,
                language=preferred_language or "en",
            ),
            media_type="application/xml",
            status_code=200,
        )

    # Prefer detector for multilingual flexibility, with STT language as hint.
    language = language_service.detect_and_switch(call_id, text, stt_lang=language)
    if not language:
        language = "en"
    session_service.update_language(call_id, language)

    if _should_end_conversation(text, language):
        bye_messages = {
            "en": "Thank you for calling VaaniSeva. Goodbye.",
            "ta": "VaaniSeva-க்கு அழைத்ததற்கு நன்றி. வணக்கம்.",
            "hi": "VaaniSeva को कॉल करने के लिए धन्यवाद। नमस्ते।",
            "ml": "VaaniSeva-ലേക്ക് വിളിച്ചതിന് നന്ദി. നമസ്കാരം.",
            "te": "VaaniSeva కి కాల్ చేసినందుకు ధన్యవాదాలు. నమస్కారం.",
        }
        _send_post_call_notifications(call_id=call_id, mobile=str(session.get("mobile", "") or ""))
        return Response(
            content=twilio_voice_service.generate_final_message_xml(
                bye_messages.get(language, bye_messages["en"]),
                language=language,
            ),
            media_type="application/xml",
            status_code=200,
        )

    payload = {
        "call_id": call_id,
        "text": text,
        "language": language,
        "mobile": session.get("mobile", ""),
    }

    # Keep the existing AI forwarding in background for compatibility with current pipeline.
    threading.Thread(target=_forward_to_ai_engine_async, args=(payload,), daemon=True).start()

    issue_type = "General"
    ticket_id = ""
    include_ticket_id = False

    try:
        logger.info("[Voice] Starting extraction for text: %s", text[:80])
        extracted = extraction_service.extract_issue(text)
        logger.info("[Voice] Extraction returned: %s", extracted)
        
        structured_data = validate_json(extracted)
        logger.info("[Voice] Validated extraction: %s", structured_data)
        if not structured_data.get("issue_type"):
            structured_data["issue_type"] = _infer_issue_type(text)

        issue_type = structured_data.get("issue_type", "General") or "General"
        structured_data["issue"] = structured_data.get("issue") or text
        structured_data["call_id"] = call_id
        structured_data["mobile"] = structured_data.get("mobile") or session.get("mobile", "")

        logger.info("[Voice] Pre-ticket data: issue_type=%s, issue_len=%d, issue_preview=%s", 
                    issue_type, len(structured_data.get("issue", "")), structured_data.get("issue", "")[:80])

        logger.info("[Voice] Creating ticket with data: issue_type=%s, issue=%s, mobile=%s", 
                    issue_type, structured_data.get("issue", "")[:80], structured_data.get("mobile", ""))
        
        routing_info = routing_service.get_department(issue_type)
        logger.info("[Voice] Got routing, calling create_ticket...")
        
        ticket = ticket_service.create_ticket(structured_data, routing_info)
        ticket_id = str(ticket.get("ticket_id", "") or "")
        logger.info("[Voice] Created ticket %s. DB issue_len=%d. DB issue_preview=%s", ticket_id, len(ticket.get("issue", "")), ticket.get("issue", "")[:80])
        logger.info("[Voice] Created ticket: %s with issue=%s", ticket_id, ticket.get("issue", "")[:80])

        # If processing is quick enough, include ticket ID in spoken acknowledgment.
        include_ticket_id = (time.perf_counter() - started) <= 7.0
    except Exception as exc:
        logger.exception("[Voice] EXCEPTION in ticket creation path: %s | structured_data=%s", exc, structured_data)
        # Create fallback ticket when extraction/creation fails
        mobile = session.get("mobile", "")
        try:
            fallback_ticket = ticket_service.create_ticket(
                {
                    "call_id": call_id,
                    "mobile": mobile,
                    "issue": f"Error during processing: {str(exc)[:100]}",
                    "issue_type": "General",
                },
                routing_service.get_department("General")
            )
            ticket_id = str(fallback_ticket.get("ticket_id", "") or "")
            logger.info("[Voice] Created fallback ticket on exception: %s", ticket_id)
            
        except Exception as exc2:
            logger.exception("[Voice] Failed to create fallback ticket: %s", exc2)

    audit_service.log_event(
        stage="voice",
        event_name="process_recording",
        call_id=call_id,
        mobile=session.get("mobile", ""),
        outcome="ok",
        latency_ms=int((time.perf_counter() - started) * 1000),
        meta={
            "language": language,
            "stt_status": "ok",
            "issue_type": issue_type,
            "ticket_id": ticket_id,
            "ticket_id_spoken": include_ticket_id,
        },
    )

    # Speak acknowledgment in-call; include ticket ID only when processing stayed fast.
    ack_message = _build_voice_ack(
        issue_type=issue_type,
        ticket_id=ticket_id,
        include_ticket_id=include_ticket_id,
    )
    ack_message = _build_voice_ack_for_language(
        issue_type=issue_type,
        language=language,
        ticket_id=ticket_id,
        include_ticket_id=include_ticket_id,
    )
    
    # MULTI-TURN LOGIC WITH DEBUG LOGGING
    turn_count = session_service.increment_turn(call_id)
    max_turns = 3
    logger.info("[Voice] MULTI-TURN DECISION: call_id=%s, turn_count=%s, max_turns=%s, language=%s", 
                call_id, turn_count, max_turns, language)
    logger.info("[Voice] SESSION STATE: %s", session_service.get(call_id))
    
    if turn_count < max_turns:
        followup_msg = _followup_prompt_for_language(language)
        logger.info("[Voice] RETURNING FOLLOWUP (turn %s/%s) for call_id=%s with message: %s", 
                    turn_count, max_turns, call_id, followup_msg[:100])
        xml_response = twilio_voice_service.generate_followup_response_xml(
            ack_message,
            followup_msg,
            language=language,
        )
        logger.info("[Voice] FOLLOWUP TWIML has Record tag: %s", '<Record' in xml_response)
        logger.info("[Voice] FOLLOWUP TWIML has Hangup tag: %s", '<Hangup' in xml_response)
        return Response(
            content=xml_response,
            media_type="application/xml",
            status_code=200,
        )
    
    # MAX TURNS REACHED OR END INTENT DETECTED
    logger.info("[Voice] RETURNING FINAL (turn %s reached max %s) for call_id=%s", turn_count, max_turns, call_id)
    _send_post_call_notifications(call_id=call_id, mobile=str(session.get("mobile", "") or ""))
    return Response(
        content=twilio_voice_service.generate_final_message_xml(ack_message, language=language),
        media_type="application/xml",
        status_code=200,
    )


@router.post("/outbound-call")
def outbound_call(body: OutboundCallRequest) -> JSONResponse:
    started = time.perf_counter()
    prompt = _build_outbound_prompt(body.message)
    message_url = f"{settings.BASE_URL}/voice-response?prompt={quote_plus(prompt)}"

    try:
        twilio_result = twilio_voice_service.create_call(to=body.mobile, message_url=message_url)
    except Exception as exc:
        logger.exception("Outbound call failed unexpectedly: %s", exc)
        audit_service.log_event(
            stage="voice",
            event_name="outbound_call",
            mobile=body.mobile,
            outcome="error",
            error_code="outbound_exception",
            latency_ms=int((time.perf_counter() - started) * 1000),
        )
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "Failed to create outbound call",
                "details": str(exc),
            },
        )

    if twilio_result.get("status") == "error":
        audit_service.log_event(
            stage="voice",
            event_name="outbound_call",
            mobile=body.mobile,
            outcome="error",
            error_code="outbound_provider_error",
            latency_ms=int((time.perf_counter() - started) * 1000),
        )
        return JSONResponse(status_code=502, content=twilio_result)

    audit_service.log_event(
        stage="voice",
        event_name="outbound_call",
        mobile=body.mobile,
        outcome="ok",
        latency_ms=int((time.perf_counter() - started) * 1000),
    )

    return JSONResponse(
        status_code=200,
        content={
            "status": "ok",
            "mobile": body.mobile,
            "message": body.message,
            "twilio": twilio_result,
        },
    )


@router.post("/simulate-recording")
def simulate_recording(body: SimulateRecordingRequest) -> JSONResponse:
    call_id = str(uuid4())
    language = "en"

    session_service.create(call_id=call_id, mobile="simulated")
    session_service.update_language(call_id=call_id, language=language)

    payload = {
        "call_id": call_id,
        "text": body.text,
        "language": language,
        "mobile": "simulated",
    }
    ai_forward_status = _forward_to_ai_engine(payload)

    return JSONResponse(
        status_code=200,
        content={
            "status": "ok",
            "simulated": True,
            "forwarded": payload,
            "ai_engine": ai_forward_status,
        },
    )


def _resolve_voice_prompt(request: Request, fallback: str) -> str:
    prompt = str(request.query_params.get("prompt", "") or "").strip()
    if prompt:
        return prompt
    return fallback


async def _voice_response_impl(request: Request) -> Response:
    call_id = ""
    mobile = ""

    if request.method.upper() == "POST":
        form_data = await _extract_form_data(request)

        call_id = str(form_data.get("CallSid", "") or "")
        # For outbound calls, To is the called party (the recipient)
        mobile = str(form_data.get("To", "") or "")
        
        # Strip +1 or other country code prefixes if present, normalize to E.164
        if not mobile.startswith("+"):
            mobile = f"+{mobile}" if mobile else ""

    if call_id and not session_service.get(call_id):
        session_service.create(call_id=call_id, mobile=mobile)
    elif call_id and mobile:
        # Update mobile in existing session if provided
        session_service.update_mobile(call_id, mobile)

    prompt = _resolve_voice_prompt(
        request,
        "This is PALLAVI. Please describe your complaint after the beep.",
    )
    session_language = "en"
    if call_id:
        state = session_service.get(call_id) or {}
        session_language = str(state.get("language", "") or "en")

    xml = twilio_voice_service.generate_response_xml(prompt, language=session_language)
    return Response(content=xml, media_type="application/xml")


@router.get("/voice-response")
async def voice_response_get(request: Request) -> Response:
    return await _voice_response_impl(request)


@router.post("/voice-response")
async def voice_response_post(request: Request) -> Response:
    return await _voice_response_impl(request)


@router.post("/incoming-message")
async def incoming_message(request: Request) -> Response:
    form_data = await _extract_form_data(request)
    from_number = str(form_data.get("From", "") or "")
    body = str(form_data.get("Body", "") or "")
    message_sid = str(form_data.get("MessageSid", "") or "")
    logger.info(
        "[Twilio] Incoming message webhook received: from=%s sid=%s body_len=%d",
        from_number,
        message_sid,
        len(body),
    )
    return Response(content="<Response></Response>", media_type="application/xml", status_code=200)


@router.post("/message-status")
async def message_status(request: Request) -> JSONResponse:
    form_data = await _extract_form_data(request)
    message_sid = str(form_data.get("MessageSid", "") or "")
    message_status_val = str(form_data.get("MessageStatus", "") or "")
    to_number = str(form_data.get("To", "") or "")
    error_code = str(form_data.get("ErrorCode", "") or "")
    logger.info(
        "[Twilio] Message status callback: sid=%s status=%s to=%s error=%s",
        message_sid,
        message_status_val,
        to_number,
        error_code,
    )
    return JSONResponse(status_code=200, content={"status": "ok"})
