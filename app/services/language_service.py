from app.services import memory_service

SUPPORTED_LANGUAGES = {"en", "ta", "hi", "ml", "te"}


def detect_language(text: str) -> str:
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


def detect_and_switch(call_id: str, text: str) -> str:
    state = memory_service.get(call_id)
    previous = str(state.get("language", "") or "")

    detected = detect_language(text)
    if detected not in SUPPORTED_LANGUAGES:
        detected = "en"

    if previous != detected:
        memory_service.update_language(call_id, detected)

    if not previous and detected:
        memory_service.update_language(call_id, detected)

    current = memory_service.get(call_id).get("language", "en")
    return str(current or "en")
