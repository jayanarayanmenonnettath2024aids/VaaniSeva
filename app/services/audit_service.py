import hashlib
import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.config import settings
from app.services.db_service import get_connection

_ALLOWED_META_KEYS = {
    "language",
    "issue_type",
    "department",
    "stt_status",
    "action_status",
    "ticket_id",
}


def _utc_now() -> str:
    return datetime.utcnow().isoformat()


def _safe_hash(value: str) -> str:
    raw = (value or "").strip()
    if not raw:
        return ""
    digest = hashlib.sha256(f"{settings.AUDIT_HASH_SALT}:{raw}".encode("utf-8")).hexdigest()
    return digest[:16]


def _sanitize_meta(meta: Optional[Dict[str, Any]]) -> str:
    if not meta:
        return "{}"
    safe_meta = {k: meta[k] for k in meta.keys() if k in _ALLOWED_META_KEYS}
    return json.dumps(safe_meta, ensure_ascii=True, sort_keys=True)


def log_event(
    *,
    stage: str,
    event_name: str,
    call_id: str = "",
    mobile: str = "",
    issue_type: str = "",
    location_norm: str = "",
    department: str = "",
    outcome: str = "",
    latency_ms: int = 0,
    error_code: str = "",
    meta: Optional[Dict[str, Any]] = None,
) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO audit_timeline(
                event_type, event_time, stage, event_name, call_ref, mobile_ref,
                issue_type, location_norm, department, outcome,
                latency_ms, error_code, meta_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                f"{stage}:{event_name}" if stage or event_name else "unknown",
                _utc_now(),
                stage,
                event_name,
                _safe_hash(call_id),
                _safe_hash(mobile),
                issue_type,
                location_norm,
                department,
                outcome,
                max(0, int(latency_ms or 0)),
                error_code,
                _sanitize_meta(meta),
            ),
        )


def list_events(limit: int = 100, stage: str = "") -> List[Dict[str, Any]]:
    with get_connection() as conn:
        if stage:
            rows = conn.execute(
                """
                SELECT event_time, stage, event_name, call_ref, mobile_ref,
                       issue_type, location_norm, department, outcome, latency_ms, error_code, meta_json
                FROM audit_timeline
                WHERE stage = ?
                ORDER BY event_time DESC
                LIMIT ?
                """,
                (stage, max(1, limit)),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT event_time, stage, event_name, call_ref, mobile_ref,
                       issue_type, location_norm, department, outcome, latency_ms, error_code, meta_json
                FROM audit_timeline
                ORDER BY event_time DESC
                LIMIT ?
                """,
                (max(1, limit),),
            ).fetchall()

    return [
        {
            "event_time": str(row["event_time"] or ""),
            "stage": str(row["stage"] or ""),
            "event_name": str(row["event_name"] or ""),
            "call_ref": str(row["call_ref"] or ""),
            "mobile_ref": str(row["mobile_ref"] or ""),
            "issue_type": str(row["issue_type"] or ""),
            "location_norm": str(row["location_norm"] or ""),
            "department": str(row["department"] or ""),
            "outcome": str(row["outcome"] or ""),
            "latency_ms": int(row["latency_ms"] or 0),
            "error_code": str(row["error_code"] or ""),
            "meta": json.loads(str(row["meta_json"] or "{}")),
        }
        for row in rows
    ]


def get_summary() -> Dict[str, Any]:
    with get_connection() as conn:
        total = int(conn.execute("SELECT COUNT(1) FROM audit_timeline").fetchone()[0])
        by_stage_rows = conn.execute(
            "SELECT stage, COUNT(1) AS c FROM audit_timeline GROUP BY stage"
        ).fetchall()
        by_outcome_rows = conn.execute(
            "SELECT outcome, COUNT(1) AS c FROM audit_timeline GROUP BY outcome"
        ).fetchall()

    by_stage = {str(r["stage"] or ""): int(r["c"] or 0) for r in by_stage_rows}
    by_outcome = {str(r["outcome"] or ""): int(r["c"] or 0) for r in by_outcome_rows}

    return {
        "total_events": total,
        "by_stage": by_stage,
        "by_outcome": by_outcome,
    }
