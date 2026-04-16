"""Cost tracking service: Calculate and log costs for all system operations."""
import logging
from datetime import datetime
from typing import Any, Dict

from app.config import settings
from app.services.db_service import get_connection

logger = logging.getLogger(__name__)

# Cost per unit (can be configured)
COST_PER_STT_MIN = 0.015  # $0.015 per minute for STT
COST_PER_SMS = 0.0075  # $0.0075 per SMS
COST_PER_TWILIO_MIN = 0.0085  # $0.0085 per call minute
COST_PER_LLM_EXTRACTION = 0.001  # $0.001 per extraction


def log_call_telemetry(
    call_id: str,
    ticket_id: str = "",
    stt_provider: str = "groq",
    stt_latency_ms: int = 0,
    extraction_latency_ms: int = 0,
    routing_latency_ms: int = 0,
    stt_duration_sec: float = 0.0,
    call_duration_sec: float = 0.0,
    sms_sent: bool = False,
    whatsapp_sent: bool = False,
) -> Dict[str, Any]:
    """Log call telemetry with cost calculations."""
    # Calculate costs
    stt_cost = (stt_duration_sec / 60.0) * COST_PER_STT_MIN if stt_duration_sec > 0 else 0
    extraction_cost = COST_PER_LLM_EXTRACTION  # Flat rate per extraction
    sms_cost = (COST_PER_SMS * 2) if (sms_sent and whatsapp_sent) else (COST_PER_SMS if sms_sent else 0)
    call_cost = (call_duration_sec / 60.0) * COST_PER_TWILIO_MIN if call_duration_sec > 0 else 0
    total_cost = stt_cost + extraction_cost + sms_cost + call_cost
    
    total_latency = stt_latency_ms + extraction_latency_ms + routing_latency_ms
    
    # Log to database
    with get_connection() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO call_telemetry(
                call_id, ticket_id, stt_provider, stt_cost, extraction_cost, 
                sms_cost, call_cost, total_cost, stt_latency_ms, extraction_latency_ms, 
                routing_latency_ms, total_latency_ms, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                call_id,
                ticket_id,
                stt_provider,
                round(stt_cost, 6),
                round(extraction_cost, 6),
                round(sms_cost, 6),
                round(call_cost, 6),
                round(total_cost, 6),
                stt_latency_ms,
                extraction_latency_ms,
                routing_latency_ms,
                total_latency,
                datetime.utcnow().isoformat(),
            ),
        )
    
    logger.info(
        "[COST] call_id=%s: STT=$%.4f, LLM=$%.4f, SMS=$%.4f, Call=$%.4f, Total=$%.4f",
        call_id,
        stt_cost,
        extraction_cost,
        sms_cost,
        call_cost,
        total_cost,
    )
    
    return {
        "call_id": call_id,
        "stt_cost": round(stt_cost, 6),
        "extraction_cost": round(extraction_cost, 6),
        "sms_cost": round(sms_cost, 6),
        "call_cost": round(call_cost, 6),
        "total_cost": round(total_cost, 6),
        "total_latency_ms": total_latency,
    }


def get_cost_summary(city_id: str = "", start_date: str = "", end_date: str = "") -> Dict[str, Any]:
    """Get cost summary by time period and city."""
    with get_connection() as conn:
        # Base query
        query = "SELECT * FROM call_telemetry WHERE 1=1"
        params = []
        
        # Filters
        if start_date:
            query += " AND created_at >= ?"
            params.append(start_date)
        if end_date:
            query += " AND created_at <= ?"
            params.append(end_date)
        
        rows = conn.execute(query, params).fetchall()
    
    if not rows:
        return {"total_calls": 0, "total_cost": 0.0, "breakdown": {}}
    
    total_stt = sum(float(row["stt_cost"] or 0) for row in rows)
    total_extraction = sum(float(row["extraction_cost"] or 0) for row in rows)
    total_sms = sum(float(row["sms_cost"] or 0) for row in rows)
    total_call = sum(float(row["call_cost"] or 0) for row in rows)
    grand_total = total_stt + total_extraction + total_sms + total_call
    
    avg_latency = sum(int(row["total_latency_ms"] or 0) for row in rows) / len(rows)
    
    return {
        "period": {
            "start": start_date or "all_time",
            "end": end_date or "now",
        },
        "total_calls": len(rows),
        "total_cost": round(grand_total, 6),
        "breakdown": {
            "stt": round(total_stt, 6),
            "extraction": round(total_extraction, 6),
            "sms": round(total_sms, 6),
            "call": round(total_call, 6),
        },
        "average_latency_ms": round(avg_latency, 1),
        "cost_per_call": round(grand_total / len(rows), 6),
    }


def get_cost_per_ticket(ticket_id: str) -> Dict[str, Any]:
    """Get cost breakdown for a specific ticket."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM call_telemetry WHERE ticket_id = ?",
            (ticket_id,),
        ).fetchall()
    
    if not rows:
        return {"ticket_id": ticket_id, "cost": 0.0, "status": "no_data"}
    
    row = rows[0]
    return {
        "ticket_id": ticket_id,
        "call_id": row["call_id"],
        "stt_cost": float(row["stt_cost"] or 0),
        "extraction_cost": float(row["extraction_cost"] or 0),
        "sms_cost": float(row["sms_cost"] or 0),
        "call_cost": float(row["call_cost"] or 0),
        "total_cost": float(row["total_cost"] or 0),
        "latency_ms": row["total_latency_ms"],
    }
