import logging
import threading
import time
from typing import Any, Dict
from uuid import uuid4

import requests
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel

from app.config import settings
from app.services import audit_service, exotel_service, session_service, stt_service

logger = logging.getLogger(__name__)

router = APIRouter()


class OutboundCallRequest(BaseModel):
    mobile: str
    message: str


class SimulateRecordingRequest(BaseModel):
    text: str


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


@router.post("/incoming-call")
async def incoming_call(request: Request) -> Response:
    started = time.perf_counter()
    form = await request.form()
    call_id = str(form.get("CallSid", ""))
    mobile = str(form.get("From", ""))

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
            content=exotel_service.generate_response_xml("Unable to process call."),
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

    xml = exotel_service.generate_response_xml(
        "Welcome to PALLAVI voice system. Please speak after the beep."
    )
    return Response(content=xml, media_type="application/xml")


@router.post("/process-recording")
async def process_recording(request: Request) -> JSONResponse:
    started = time.perf_counter()
    form = await request.form()
    recording_url = str(form.get("RecordingUrl", ""))
    call_id = str(form.get("CallSid", ""))

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
            content=exotel_service.generate_response_xml("Error: Missing recording information."),
            media_type="application/xml",
            status_code=400,
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
            content=exotel_service.generate_response_xml("Error: Invalid recording URL."),
            media_type="application/xml",
            status_code=400,
        )

    session = session_service.get(call_id)
    if not session:
        session = session_service.create(call_id=call_id, mobile="")

    try:
        stt_result = stt_service.process_audio(recording_url)
    except Exception as exc:
        logger.exception("Unexpected STT error: %s", exc)
        audit_service.log_event(
            stage="voice",
            event_name="process_recording",
            call_id=call_id,
            mobile=session.get("mobile", ""),
            outcome="error",
            error_code="stt_exception",
            latency_ms=int((time.perf_counter() - started) * 1000),
        )
        return Response(
            content=exotel_service.generate_response_xml("Error: Could not process your speech. Please try again."),
            media_type="application/xml",
            status_code=500,
        )

    text = stt_result.get("text", "")
    language = stt_result.get("language", "unknown")
    if language == "unknown":
        language = "en"

    if not text:
        audit_service.log_event(
            stage="voice",
            event_name="process_recording",
            call_id=call_id,
            mobile=session.get("mobile", ""),
            outcome="error",
            error_code="stt_empty",
            latency_ms=int((time.perf_counter() - started) * 1000),
            meta={"language": language, "stt_status": "empty"},
        )
        return Response(
            content=exotel_service.generate_response_xml("We didn't catch that. Please try again."),
            media_type="application/xml",
            status_code=400,
        )

    session_service.update_language(call_id, language)

    payload = {
        "call_id": call_id,
        "text": text,
        "language": language,
        "mobile": session.get("mobile", ""),
    }
    threading.Thread(target=_forward_to_ai_engine_async, args=(payload,), daemon=True).start()

    audit_service.log_event(
        stage="voice",
        event_name="process_recording",
        call_id=call_id,
        mobile=session.get("mobile", ""),
        outcome="ok",
        latency_ms=int((time.perf_counter() - started) * 1000),
        meta={"language": language, "stt_status": "ok"},
    )

    # Return processing feedback XML to caller while AI processes in background
    return Response(
        content=exotel_service.generate_processing_response_xml(),
        media_type="application/xml",
        status_code=200,
    )


@router.post("/outbound-call")
def outbound_call(body: OutboundCallRequest) -> JSONResponse:
    started = time.perf_counter()
    message_url = f"{settings.BASE_URL}/voice-response"

    try:
        exotel_result = exotel_service.create_call(to=body.mobile, message_url=message_url)
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

    if exotel_result.get("status") == "error":
        audit_service.log_event(
            stage="voice",
            event_name="outbound_call",
            mobile=body.mobile,
            outcome="error",
            error_code="outbound_provider_error",
            latency_ms=int((time.perf_counter() - started) * 1000),
        )
        return JSONResponse(status_code=502, content=exotel_result)

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
            "exotel": exotel_result,
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


@router.get("/voice-response")
def voice_response() -> Response:
    xml = (
        "<Response>"
        "<Say voice=\"woman\">Your complaint has been registered successfully.</Say>"
        "</Response>"
    )
    return Response(content=xml, media_type="application/xml")
