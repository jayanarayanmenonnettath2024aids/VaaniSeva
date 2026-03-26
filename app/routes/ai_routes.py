from typing import Dict, Optional
from uuid import uuid4

import requests
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.config import settings
from app.services import extraction_service, language_service, memory_service, response_service
from app.utils.validators import empty_structure, validate_json

router = APIRouter()


class ProcessTextRequest(BaseModel):
    call_id: str
    text: str
    language: Optional[str] = None


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
        requests.post(settings.ACTION_ENGINE_URL, json=payload, timeout=5)
    except Exception:
        # Action engine failures should not break AI flow.
        return


@router.post("/process-text")
def process_text(body: ProcessTextRequest) -> JSONResponse:
    if not body.call_id or not body.text:
        return JSONResponse(
            status_code=400,
            content={"status": "error", "message": "call_id and text are required"},
        )

    memory_service.init(body.call_id)

    if not body.text.strip():
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
        language = language_service.detect_and_switch(body.call_id, body.text)
    except Exception:
        language = "en"

    if language == "unknown":
        language = "en"
        memory_service.update_language(body.call_id, language)

    language_changed = bool(previous_language and previous_language != language)

    try:
        structured_data = extraction_service.extract_issue(body.text)
    except Exception:
        structured_data = empty_structure()

    structured_data = validate_json(structured_data)

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

    _send_to_action_engine(body.call_id, structured_data)

    return JSONResponse(
        status_code=200,
        content={
            "call_id": body.call_id,
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
