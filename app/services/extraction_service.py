import json
import re
from typing import Any, Dict

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


def fallback_extract(text: str) -> Dict[str, str]:
    t = (text or "").lower()
    issue_type = "General"

    if any(k in t for k in ["pothole", "road", "street"]):
        issue_type = "Road"
    elif "water" in t:
        issue_type = "Water"
    elif any(k in t for k in ["electric", "power"]):
        issue_type = "Electricity"
    elif any(k in t for k in ["garbage", "waste"]):
        issue_type = "Garbage"

    mobile_match = re.search(r"(?:\+91[- ]?)?[6-9]\d{9}", text)
    mobile = mobile_match.group(0) if mobile_match else ""

    name_match = re.search(r"(?:my name is|i am)\s+([A-Za-z ]{2,40})", text, re.IGNORECASE)
    customer_name = name_match.group(1).strip() if name_match else ""

    return {
        "customer_name": customer_name,
        "mobile": mobile,
        "issue": text,
        "location": "",
        "issue_type": issue_type,
    }


def extract_issue(text: str) -> Dict[str, str]:
    if not text:
        return validate_json({})

    extracted: Dict[str, Any] = {}

    if settings.AI_MODEL_PROVIDER.lower().strip() == "local":
        extracted = local_ai_service.extract_with_local_ai(text)

    validated = validate_json(extracted)
    validated["issue_type"] = normalize_issue(validated.get("issue_type", ""))

    if (
        not validated.get("issue")
        or not validated.get("issue_type")
        or validated.get("issue_type") == "General"
    ):
        validated = validate_json(fallback_extract(text))
        validated["issue_type"] = normalize_issue(validated.get("issue_type", ""))

    return validated
