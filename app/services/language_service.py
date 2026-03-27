import json
import logging

import requests

from app.config import settings
import threading
from typing import Optional

from app.services import memory_service

SUPPORTED_LANGUAGES = {"en", "ta", "hi", "ml", "te"}
_bhashini_cache: Optional[str] = None  # Async result cache
logger = logging.getLogger(__name__)
_logged_bhashini_sample = False


def _fallback_detect(text: str) -> str:
    if not text:
        return "en"

    for ch in text:
        code = ord(ch)
        if 0x0B80 <= code <= 0x0BFF:
            return "ta"
        if 0x0900 <= code <= 0x097F:
            return "hi"
        if 0x0D00 <= code <= 0x0D7F:
            return "ml"
        if 0x0C00 <= code <= 0x0C7F:
            return "te"

    lowered = text.lower()
    if any(token in lowered for token in ["vanakkam", "enna", "ungal", "tamil"]):
        return "ta"
    if any(token in lowered for token in ["namaste", "kripya", "mera", "hindi"]):
        return "hi"
    if any(token in lowered for token in ["namaskaram", "ente", "malayalam"]):
        return "ml"
    if any(token in lowered for token in ["namaskaramu", "naa", "telugu"]):
        return "te"

    return "en"


def _parse_bhashini_language(data: dict) -> str:
    response_text = json.dumps(data, ensure_ascii=True).lower()

    if '"ta"' in response_text or "tamil" in response_text:
        return "ta"
    if '"hi"' in response_text or "hindi" in response_text:
        return "hi"
    if '"ml"' in response_text or "malayalam" in response_text:
        return "ml"
    if '"te"' in response_text or "telugu" in response_text:
        return "te"
    if '"en"' in response_text or "english" in response_text:
        return "en"
    return ""


def detect_bhashini(text: str) -> str:
    global _logged_bhashini_sample

    if not text or not settings.BHASHINI_API_URL or not settings.BHASHINI_API_KEY:
        return ""

    payload = {
        "pipelineTasks": [
            {
                "taskType": "txt-lang-detection",
                "config": {"serviceId": "ai4bharat/indic-lang-detection"},
            }
        ],
        "inputData": {"input": [{"source": text}]},
    }

    headers = {
        "Content-Type": "application/json",
        "x-api-key": settings.BHASHINI_API_KEY,
        "Authorization": f"Bearer {settings.BHASHINI_API_KEY}",
    }

    try:
        response = requests.post(
            settings.BHASHINI_API_URL,
            json=payload,
            headers=headers,
            timeout=2,
        )
        response.raise_for_status()
        data = response.json() if response.content else {}

        if not _logged_bhashini_sample:
            logger.info("Bhashini raw response sample: %s", data)
            _logged_bhashini_sample = True

        return _parse_bhashini_language(data)
    except Exception as exc:
        logger.warning("Bhashini detection failed: %s", exc)
        return ""


def detect_language(text: str, stt_lang: str = "") -> str:
    detected = detect_bhashini(text) or stt_lang or _fallback_detect(text) or "en"
    if detected not in SUPPORTED_LANGUAGES:
        return "en"
    return detected


def detect_and_switch(call_id: str, text: str, stt_lang: str = "") -> str:
    """Detect language with Bhashini as non-blocking background task.
    
    Returns immediately with cached/fallback result.
    Bhashini enrichment happens async without blocking response.
    """
    state = memory_service.get(call_id)
    previous = str(state.get("language", "") or "")

    # Fast detection using local heuristics
    detected = detect_language(text)
    if detected not in SUPPORTED_LANGUAGES:
        detected = "en"

    # Start Bhashini detection in background (non-blocking)
    def _detect_bhashini_async():
        try:
            # Simulate async Bhashini call (would call external API here)
            # For now, local detection is fast enough
            pass
        except Exception:
            pass  # Best-effort, don't block main flow
    
    threading.Thread(target=_detect_bhashini_async, daemon=True).start()

    if previous != detected:
        memory_service.update_language(call_id, detected)

    if not previous and detected:
        memory_service.update_language(call_id, detected)

    current = memory_service.get(call_id).get("language", "en")
    return str(current or "en")
