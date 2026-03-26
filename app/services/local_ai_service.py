import json
from typing import Any, Dict

import requests

from app.config import settings
from app.utils.validators import validate_json


def call_local_model(prompt: str) -> str:
    endpoint = f"{settings.OLLAMA_BASE_URL}/api/generate"
    payload = {
        "model": settings.OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
    }

    response = requests.post(endpoint, json=payload, timeout=10)
    response.raise_for_status()
    data = response.json() if response.content else {}
    return str(data.get("response", "")).strip()


def _extract_json_object(raw_text: str) -> Dict[str, Any]:
    if not raw_text:
        return {}

    try:
        data = json.loads(raw_text)
        return data if isinstance(data, dict) else {}
    except Exception:
        pass

    start = raw_text.find("{")
    end = raw_text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return {}

    try:
        data = json.loads(raw_text[start : end + 1])
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def extract_with_local_ai(text: str) -> Dict[str, str]:
    prompt = (
        "Extract complaint details from input and return strict JSON only with keys: "
        "customer_name, mobile, issue, location, issue_type. "
        "Use empty string for unknown values. Do not include any explanation.\n\n"
        f"Input: {text}"
    )

    try:
        output = call_local_model(prompt)
        parsed = _extract_json_object(output)
        return validate_json(parsed)
    except Exception:
        return validate_json({})


def generate_insight(data: Dict[str, Any]) -> str:
    prompt = (
        "Generate exactly one short analytics insight sentence in plain English from this data: "
        f"{json.dumps(data, ensure_ascii=True)}"
    )
    try:
        response = call_local_model(prompt)
        return response or "No significant insight detected."
    except Exception:
        return "No significant insight detected."
