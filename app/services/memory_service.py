from threading import Lock
from typing import Dict, List

memory: Dict[str, Dict[str, object]] = {}
_lock = Lock()


def init(call_id: str) -> Dict[str, object]:
    with _lock:
        if call_id not in memory:
            memory[call_id] = {
                "language": "",
                "history": [],
                "last_issue": "",
            }
        return memory[call_id]


def update_language(call_id: str, lang: str) -> Dict[str, object]:
    state = init(call_id)
    with _lock:
        state["language"] = lang
    return state


def add_history(call_id: str, text: str) -> Dict[str, object]:
    state = init(call_id)
    with _lock:
        history = state.get("history", [])
        if not isinstance(history, list):
            history = []
        history.append(text)
        state["history"] = history[-20:]
    return state


def update_last_issue(call_id: str, issue: str) -> Dict[str, object]:
    state = init(call_id)
    with _lock:
        state["last_issue"] = issue
    return state


def get(call_id: str) -> Dict[str, object]:
    return init(call_id)
