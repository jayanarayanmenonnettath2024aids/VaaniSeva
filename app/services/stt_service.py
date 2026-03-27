from typing import Dict

import requests

from app.config import settings
from app.utils.load_balancer import RoundRobinBalancer


_sarvam_balancer = RoundRobinBalancer(settings.SARVAM_API_KEYS)


def whisper_transcribe(audio_url: str) -> Dict[str, str]:
    # Explicit fallback error until a real Whisper endpoint is integrated.
    return {
        "text": "",
        "language": "unknown",
        "error": "whisper_not_configured",
    }


def _sarvam_transcribe(audio_url: str) -> Dict[str, str]:
    api_key = _sarvam_balancer.get_next()
    endpoint = settings.SARVAM_STT_URL

    payload = {"audio_url": audio_url}

    # Header names can vary by plan/provider configuration.
    headers = {
        "Content-Type": "application/json",
        "api-key": api_key,
    }

    response = requests.post(endpoint, json=payload, headers=headers, timeout=3)
    response.raise_for_status()

    data = response.json() if response.content else {}
    text = data.get("text") or data.get("transcript") or ""
    language = data.get("language") or data.get("lang") or "unknown"

    if not text:
        raise RuntimeError("Sarvam STT returned no transcript")

    return {"text": text, "language": language}


def process_audio(audio_url: str) -> Dict[str, str]:
    try:
        return _sarvam_transcribe(audio_url)
    except requests.Timeout:
        # Timeout → fallback to Whisper
        return whisper_transcribe(audio_url)
    except Exception:
        # Any other error → fallback to Whisper
        return whisper_transcribe(audio_url)
