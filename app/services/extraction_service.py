import json
import os
import re
from typing import Any, Dict

import requests

from app.config import settings
from app.services import local_ai_service
from app.utils.validators import validate_json


ISSUE_MAP = {
    "pothole": "Road",
    "road": "Road",
    "water": "Water",
    "electricity": "Electricity",
    "garbage": "Garbage",
    "sanitation": "Garbage",
    "waste": "Garbage",
    "street light": "Street Light",
}


def normalize_issue(issue_type: str) -> str:
    normalized_input = (issue_type or "").lower()
    for key, value in ISSUE_MAP.items():
        if key in normalized_input:
            return value
    return "General"


def _extract_json_object(raw_text: str) -> Dict[str, Any]:
    if not raw_text:
        return {}

    try:
        data = json.loads(raw_text)
        return data if isinstance(data, dict) else {}
    except Exception:
        pass

    match = re.search(r"\{[\s\S]*\}", raw_text)
    if not match:
        return {}

    try:
        data = json.loads(match.group(0))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _call_openai_for_extraction(text: str) -> Dict[str, Any]:
    endpoint = f"{settings.OPENAI_API_BASE_URL}/chat/completions"
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    prompt = (
        "Extract complaint data and return strict JSON only with keys: "
        "customer_name, mobile, issue, location, issue_type. "
        "If unknown, use empty string. No extra keys."
    )

    response = requests.post(
        endpoint,
        headers={
            "Authorization": f"Bearer {settings.AI_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": prompt},
                {"role": "user", "content": text},
            ],
            "temperature": 0,
        },
        timeout=5,
    )
    response.raise_for_status()

    data = response.json()
    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
    return _extract_json_object(content)


def _call_claude_for_extraction(text: str) -> Dict[str, Any]:
    endpoint = f"{settings.CLAUDE_API_BASE_URL}/messages"
    model = os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-latest")
    prompt = (
        "Extract complaint data and return strict JSON only with keys: "
        "customer_name, mobile, issue, location, issue_type. "
        "If unknown, use empty string. No extra keys."
    )

    response = requests.post(
        endpoint,
        headers={
            "x-api-key": settings.AI_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": model,
            "max_tokens": 200,
            "temperature": 0,
            "messages": [
                {"role": "user", "content": f"{prompt}\n\nInput: {text}"},
            ],
        },
        timeout=5,
    )
    response.raise_for_status()

    data = response.json()
    chunks = data.get("content", [])
    content = ""
    if isinstance(chunks, list) and chunks:
        content = str(chunks[0].get("text", ""))
    return _extract_json_object(content)


def _rule_based_extract(text: str) -> Dict[str, str]:
    lowered = text.lower()
    issue_type = ""

    if any(token in lowered for token in ["pothole", "road", "street"]):
        issue_type = "road"
    elif any(token in lowered for token in ["water", "leak", "drain", "sewage"]):
        issue_type = "water"
    elif any(token in lowered for token in ["electric", "power", "street light", "eb"]):
        issue_type = "electricity"
    elif any(token in lowered for token in ["garbage", "waste", "clean"]):
        issue_type = "sanitation"

    mobile_match = re.search(r"(?:\+91[- ]?)?[6-9]\d{9}", text)
    mobile = mobile_match.group(0) if mobile_match else ""

    name_match = re.search(r"(?:my name is|i am)\s+([A-Za-z ]{2,40})", text, re.IGNORECASE)
    customer_name = name_match.group(1).strip() if name_match else ""

    return {
        "customer_name": customer_name,
        "mobile": mobile,
        "issue": text.strip(),
        "location": "",
        "issue_type": issue_type,
    }


def extract_issue(text: str) -> Dict[str, str]:
    if not text:
        return validate_json({})

    extracted: Dict[str, Any] = {}

    provider = settings.AI_MODEL_PROVIDER.lower().strip()

    if provider == "local":
        extracted = local_ai_service.extract_with_local_ai(text)
    elif settings.AI_API_KEY:
        try:
            if provider == "openai":
                extracted = _call_openai_for_extraction(text)
            elif provider == "claude":
                extracted = _call_claude_for_extraction(text)
        except Exception:
            extracted = {}

    if not extracted:
        extracted = _rule_based_extract(text)

    validated = validate_json(extracted)
    validated["issue_type"] = normalize_issue(validated.get("issue_type", ""))
    return validated
