import re
from typing import Dict

import requests

from app.config import settings


def _normalize_text(location: str) -> str:
    text = (location or "").strip()
    text = re.sub(r"\s+", " ", text)
    return text


def geocode_location(location: str) -> Dict[str, object]:
    normalized = _normalize_text(location)
    if not normalized:
        return {
            "normalized_location": "",
            "coordinates": {"lat": 0.0, "lng": 0.0},
            "provider": "none",
            "status": "empty",
        }

    try:
        response = requests.get(
            settings.GEOCODING_URL,
            params={
                "q": normalized,
                "format": "json",
                "limit": 1,
            },
            headers={"User-Agent": settings.GEOCODING_USER_AGENT},
            timeout=4,
        )
        response.raise_for_status()
        payload = response.json()

        if isinstance(payload, list) and payload:
            top = payload[0]
            display_name = str(top.get("display_name", normalized)).strip()
            lat = float(top.get("lat", 0.0))
            lng = float(top.get("lon", 0.0))
            return {
                "normalized_location": display_name,
                "coordinates": {"lat": lat, "lng": lng},
                "provider": "nominatim",
                "status": "ok",
            }
    except Exception:
        pass

    return {
        "normalized_location": normalized,
        "coordinates": {"lat": 0.0, "lng": 0.0},
        "provider": "nominatim",
        "status": "not_found",
    }
