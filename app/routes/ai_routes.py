import threading
import time
from typing import Dict, Optional
from uuid import uuid4

import requests
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.config import settings
from app.services import audit_service, extraction_service, language_service, memory_service, response_service
from app.utils.validators import empty_structure, validate_json

router = APIRouter()


class ProcessTextRequest(BaseModel):
    call_id: str
    text: str
    language: Optional[str] = None
    mobile: Optional[str] = None


class SimulateTextRequest(BaseModel):
    text: str


def _send_to_action_engine(call_id: str, structured_data: Dict[str, str]) -> None:
    if not settings.ACTION_ENGINE_URL:
        return

    try:
        payload = {
            "call_id": call_id,
            "structured_data": structured_data,
        }
        requests.post(settings.ACTION_ENGINE_URL, json=payload, timeout=2)
    except Exception:
        # Action engine failures should not break AI flow.
        return


def _send_to_action_engine_async(call_id: str, structured_data: Dict[str, str]) -> None:
    threading.Thread(
        target=_send_to_action_engine,
        args=(call_id, structured_data),
        daemon=True,
    ).start()


@router.post("/process-text")
def process_text(body: ProcessTextRequest) -> JSONResponse:
    started = time.perf_counter()
    if not body.call_id or not body.text:
        audit_service.log_event(
            stage="ai",
            event_name="process_text",
            call_id=body.call_id,
            mobile=(body.mobile or ""),
            outcome="error",
            error_code="missing_fields",
            latency_ms=int((time.perf_counter() - started) * 1000),
        )
        return JSONResponse(
            status_code=400,
            content={"status": "error", "message": "call_id and text are required"},
        )

    memory_service.init(body.call_id, mobile=(body.mobile or ""))
    if body.mobile:
        memory_service.bind_mobile(body.call_id, body.mobile)

    if not body.text.strip():
        audit_service.log_event(
            stage="ai",
            event_name="process_text",
            call_id=body.call_id,
            mobile=(body.mobile or ""),
            outcome="error",
            error_code="empty_text",
            latency_ms=int((time.perf_counter() - started) * 1000),
        )
        return JSONResponse(
            status_code=200,
            content={
                "call_id": body.call_id,
                "language": "en",
                "response": "Sorry, I couldn't understand. Please repeat your issue.",
                "structured_data": empty_structure(),
            },
        )

    if body.language in language_service.SUPPORTED_LANGUAGES:
        memory_service.update_language(body.call_id, body.language)

    previous_language = str(memory_service.get(body.call_id).get("language", "") or "")

    try:
        language = language_service.detect_and_switch(
            body.call_id,
            body.text,
            stt_lang=(body.language or ""),
        )
    except Exception:
        language = "en"

    if language == "unknown":
        language = "en"
        memory_service.update_language(body.call_id, language)

    language_changed = bool(previous_language and previous_language != language)

    # HARD TIMEOUT BUDGET: 2.5s for extraction
    extraction_deadline = started + 2.5
    
    try:
        structured_data = extraction_service.extract_issue(body.text)
    except Exception:
        structured_data = empty_structure()

    # Early return if extraction took too long (avoid cascading delays)
    if time.perf_counter() > extraction_deadline:
        structured_data = empty_structure()
    
    structured_data = validate_json(structured_data)

    if body.mobile and not structured_data.get("mobile"):
        structured_data["mobile"] = body.mobile

    if not structured_data.get("issue_type"):
        text_lower = body.text.lower()

        if "road" in text_lower or "pothole" in text_lower:
            structured_data["issue_type"] = "Road"
        elif "water" in text_lower:
            structured_data["issue_type"] = "Water"
        elif "electric" in text_lower:
            structured_data["issue_type"] = "Electricity"
        elif "garbage" in text_lower:
            structured_data["issue_type"] = "Garbage"
        else:
            structured_data["issue_type"] = "General"

    context = memory_service.get(body.call_id)
    try:
        response_text = response_service.generate_response(body.text, language, context)
    except Exception:
        response_text = response_service.generate_response("", language, context)

    location_text = structured_data.get("location") or "your area"
    ack = (
        "I understood that you are reporting a "
        f"{structured_data['issue_type']} issue in {location_text}."
    )
    response_text = f"{ack} {response_text}"

    prefix = f"[Switched to {language}] " if language_changed else ""
    response_text = f"{prefix}{response_text}"

    memory_service.add_history(body.call_id, body.text)
    if structured_data.get("issue", ""):
        memory_service.update_last_issue(body.call_id, structured_data["issue"])

    _send_to_action_engine_async(body.call_id, structured_data)

    audit_service.log_event(
        stage="ai",
        event_name="process_text",
        call_id=body.call_id,
        mobile=(body.mobile or structured_data.get("mobile", "")),
        issue_type=structured_data.get("issue_type", ""),
        location_norm=structured_data.get("location", ""),
        outcome="ok",
        latency_ms=int((time.perf_counter() - started) * 1000),
        meta={"language": language, "issue_type": structured_data.get("issue_type", "")},
    )

    return JSONResponse(
        status_code=200,
        content={
            "call_id": body.call_id,
            "mobile": body.mobile or "",
            "language": language,
            "response": response_text,
            "structured_data": structured_data,
        },
    )


@router.post("/simulate-text")
def simulate_text(body: SimulateTextRequest) -> JSONResponse:
    simulated_call_id = f"sim-{uuid4()}"

    request_body = ProcessTextRequest(call_id=simulated_call_id, text=body.text)
    return process_text(request_body)
