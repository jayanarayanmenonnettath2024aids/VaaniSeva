from datetime import datetime
from typing import Dict, List

from app.services.db_service import get_connection


def _utc_now() -> str:
    return datetime.utcnow().isoformat()


def _ensure_call(call_id: str, mobile: str = "") -> None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT call_id, mobile, language, last_issue FROM call_memory WHERE call_id = ?",
            (call_id,),
        ).fetchone()

        if row is None:
            conn.execute(
                """
                INSERT INTO call_memory(call_id, mobile, language, last_issue, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (call_id, mobile, "", "", _utc_now()),
            )
        elif mobile and not row["mobile"]:
            conn.execute(
                "UPDATE call_memory SET mobile = ?, updated_at = ? WHERE call_id = ?",
                (mobile, _utc_now(), call_id),
            )


def init(call_id: str, mobile: str = "") -> Dict[str, object]:
    _ensure_call(call_id, mobile)
    return get(call_id)


def bind_mobile(call_id: str, mobile: str) -> Dict[str, object]:
    _ensure_call(call_id, mobile)
    with get_connection() as conn:
        conn.execute(
            "UPDATE call_memory SET mobile = ?, updated_at = ? WHERE call_id = ?",
            (mobile, _utc_now(), call_id),
        )
    return get(call_id)


def update_language(call_id: str, lang: str) -> Dict[str, object]:
    _ensure_call(call_id)
    with get_connection() as conn:
        conn.execute(
            "UPDATE call_memory SET language = ?, updated_at = ? WHERE call_id = ?",
            (lang, _utc_now(), call_id),
        )
    return get(call_id)


def add_history(call_id: str, text: str) -> Dict[str, object]:
    _ensure_call(call_id)
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO call_history(call_id, text, created_at) VALUES (?, ?, ?)",
            (call_id, text, _utc_now()),
        )
        conn.execute(
            """
            DELETE FROM call_history
            WHERE id IN (
                SELECT id FROM call_history
                WHERE call_id = ?
                ORDER BY created_at DESC
                LIMIT -1 OFFSET 20
            )
            """,
            (call_id,),
        )
    return get(call_id)


def update_last_issue(call_id: str, issue: str) -> Dict[str, object]:
    _ensure_call(call_id)
    with get_connection() as conn:
        conn.execute(
            "UPDATE call_memory SET last_issue = ?, updated_at = ? WHERE call_id = ?",
            (issue, _utc_now(), call_id),
        )
    return get(call_id)


def get_recent_calls_by_mobile(mobile: str, limit: int = 5) -> List[Dict[str, str]]:
    if not mobile:
        return []

    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT call_id, language, last_issue, updated_at
            FROM call_memory
            WHERE mobile = ?
            ORDER BY updated_at DESC
            LIMIT ?
            """,
            (mobile, max(1, limit)),
        ).fetchall()

    return [
        {
            "call_id": str(row["call_id"] or ""),
            "language": str(row["language"] or ""),
            "last_issue": str(row["last_issue"] or ""),
            "updated_at": str(row["updated_at"] or ""),
        }
        for row in rows
    ]


def get(call_id: str) -> Dict[str, object]:
    _ensure_call(call_id)
    with get_connection() as conn:
        memory_row = conn.execute(
            "SELECT call_id, mobile, language, last_issue FROM call_memory WHERE call_id = ?",
            (call_id,),
        ).fetchone()
        history_rows = conn.execute(
            """
            SELECT text FROM call_history
            WHERE call_id = ?
            ORDER BY created_at DESC
            LIMIT 20
            """,
            (call_id,),
        ).fetchall()

    mobile = str(memory_row["mobile"] or "") if memory_row else ""
    recent_calls = [c for c in get_recent_calls_by_mobile(mobile, limit=5) if c["call_id"] != call_id]

    return {
        "call_id": call_id,
        "mobile": mobile,
        "language": str(memory_row["language"] or "") if memory_row else "",
        "last_issue": str(memory_row["last_issue"] or "") if memory_row else "",
        "history": [str(row["text"] or "") for row in history_rows][::-1],
        "recent_calls": recent_calls,
    }
