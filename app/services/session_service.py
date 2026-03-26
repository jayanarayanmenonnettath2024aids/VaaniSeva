from threading import Lock
from typing import Dict, Optional


sessions: Dict[str, Dict[str, str]] = {}
_lock = Lock()


def create(call_id: str, mobile: str) -> Dict[str, str]:
    session = {"mobile": mobile, "language": ""}
    with _lock:
        sessions[call_id] = session
    return session


def update_language(call_id: str, language: str) -> Optional[Dict[str, str]]:
    with _lock:
        if call_id not in sessions:
            return None
        sessions[call_id]["language"] = language
        return sessions[call_id]


def get(call_id: str) -> Optional[Dict[str, str]]:
    with _lock:
        return sessions.get(call_id)
