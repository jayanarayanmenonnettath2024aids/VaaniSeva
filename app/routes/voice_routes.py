import logging
from typing import Any, Dict
from uuid import uuid4

import requests
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel

from app.config import settings
from app.services import exotel_service, session_service, stt_service

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


@router.post("/incoming-call")
async def incoming_call(request: Request) -> Response:
    form = await request.form()
    call_id = str(form.get("CallSid", ""))
    mobile = str(form.get("From", ""))

    if not call_id:
        return Response(
            content=exotel_service.generate_response_xml("Unable to process call."),
            media_type="application/xml",
            status_code=400,
        )

    session_service.create(call_id=call_id, mobile=mobile)

    xml = exotel_service.generate_response_xml(
        "Welcome to PALLAVI voice system. Please speak after the beep."
    )
    return Response(content=xml, media_type="application/xml")


@router.post("/process-recording")
async def process_recording(request: Request) -> JSONResponse:
    form = await request.form()
    recording_url = str(form.get("RecordingUrl", ""))
    call_id = str(form.get("CallSid", ""))

    if not call_id or not recording_url:
        return JSONResponse(
            status_code=400,
            content={"status": "error", "message": "CallSid and RecordingUrl are required"},
        )

    if not recording_url.startswith("http"):
        return JSONResponse(
            status_code=400,
            content={"status": "error", "message": "RecordingUrl must start with http"},
        )

    session = session_service.get(call_id)
    if not session:
        session = session_service.create(call_id=call_id, mobile="")

    try:
        stt_result = stt_service.process_audio(recording_url)
    except Exception as exc:
        logger.exception("Unexpected STT error: %s", exc)
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": "STT failed", "call_id": call_id},
        )

    text = stt_result.get("text", "")
    language = stt_result.get("language", "unknown")
    if language == "unknown":
        language = "en"

    if not text:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": "STT failed", "call_id": call_id},
        )

    session_service.update_language(call_id, language)

    payload = {
        "call_id": call_id,
        "text": text,
        "language": language,
        "mobile": session.get("mobile", ""),
    }
    ai_forward_status = _forward_to_ai_engine(payload)

    return JSONResponse(
        status_code=200,
        content={
            "status": "ok",
            "call_id": call_id,
            "mobile": session.get("mobile", ""),
            "text": text,
            "language": language,
            "ai_engine": ai_forward_status,
        },
    )


@router.post("/outbound-call")
def outbound_call(body: OutboundCallRequest) -> JSONResponse:
    message_url = f"{settings.BASE_URL}/voice-response"

    try:
        exotel_result = exotel_service.create_call(to=body.mobile, message_url=message_url)
    except Exception as exc:
        logger.exception("Outbound call failed unexpectedly: %s", exc)
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "Failed to create outbound call",
                "details": str(exc),
            },
        )

    if exotel_result.get("status") == "error":
        return JSONResponse(status_code=502, content=exotel_result)

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
