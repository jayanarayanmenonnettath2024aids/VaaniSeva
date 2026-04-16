from threading import Lock
from typing import Any, Dict, Optional


sessions: Dict[str, Dict[str, Any]] = {}
_lock = Lock()


def create(call_id: str, mobile: str) -> Dict[str, Any]:
    session = {"mobile": mobile, "language": "", "turn_count": 0}
    with _lock:
        sessions[call_id] = session
    return session


def update_mobile(call_id: str, mobile: str) -> Optional[Dict[str, Any]]:
    """Update or add mobile number to existing session."""
    with _lock:
        if call_id not in sessions:
            return None
        sessions[call_id]["mobile"] = mobile
        return sessions[call_id]


def update_language(call_id: str, language: str) -> Optional[Dict[str, Any]]:
    with _lock:
        if call_id not in sessions:
            return None
        sessions[call_id]["language"] = language
        return sessions[call_id]


def get(call_id: str) -> Optional[Dict[str, Any]]:
    with _lock:
        return sessions.get(call_id)


def increment_turn(call_id: str) -> int:
    with _lock:
        if call_id not in sessions:
            return 0
        current = int(sessions[call_id].get("turn_count", 0) or 0)
        current += 1
        sessions[call_id]["turn_count"] = current
        return current


def get_turn_count(call_id: str) -> int:
    with _lock:
        if call_id not in sessions:
            return 0
        return int(sessions[call_id].get("turn_count", 0) or 0)
