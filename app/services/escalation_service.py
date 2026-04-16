"""Escalation management service for multi-level ticket escalation."""
import logging
from datetime import datetime
from typing import Any, Dict, List

from app.config import settings
from app.services.db_service import get_connection

logger = logging.getLogger(__name__)


def initialize_escalation_schema():
    """Create escalation tables if they don't exist."""
    with get_connection() as conn:
        # Escalation rules table
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS escalation_rules (
                rule_id TEXT PRIMARY KEY,
                source_dept TEXT NOT NULL,
                dest_dept TEXT NOT NULL,
                escalation_level INTEGER DEFAULT 1,
                sla_minutes_threshold INTEGER DEFAULT 30,
                contact_method TEXT DEFAULT 'sms',  -- sms, call, email, whatsapp
                active BOOLEAN DEFAULT 1,
                created_at TEXT,
                FOREIGN KEY(source_dept) REFERENCES departments(department_id)
            )
            """
        )
        
        # Escalation history table
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS escalation_history (
                escalation_id TEXT PRIMARY KEY,
                ticket_id TEXT NOT NULL,
                from_dept TEXT NOT NULL,
                to_dept TEXT NOT NULL,
                escalation_level INTEGER,
                reason TEXT,
                contact_method TEXT,
                contact_value TEXT,
                escalated_at TEXT,
                FOREIGN KEY(ticket_id) REFERENCES tickets(ticket_id)
            )
            """
        )
        
        # Create indexes
        conn.execute("CREATE INDEX IF NOT EXISTS idx_escalation_rules_source ON escalation_rules(source_dept)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_escalation_history_ticket ON escalation_history(ticket_id)")


def create_escalation_rule(
    source_dept: str,
    dest_dept: str,
    escalation_level: int = 1,
    sla_minutes_threshold: int = 30,
    contact_method: str = "sms",
) -> Dict[str, Any]:
    """Create an escalation rule from one department to another."""
    rule_id = f"rule_{source_dept}_{dest_dept}_{escalation_level}"
    
    with get_connection() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO escalation_rules(
                rule_id, source_dept, dest_dept, escalation_level,
                sla_minutes_threshold, contact_method, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                rule_id,
                source_dept,
                dest_dept,
                escalation_level,
                sla_minutes_threshold,
                contact_method,
                datetime.utcnow().isoformat(),
            ),
        )
    
    logger.info(
        "[ESCALATION] Created rule: %s -> %s (level %d, threshold %d min)",
        source_dept,
        dest_dept,
        escalation_level,
        sla_minutes_threshold,
    )
    
    return {
        "rule_id": rule_id,
        "source_dept": source_dept,
        "dest_dept": dest_dept,
        "escalation_level": escalation_level,
        "sla_minutes_threshold": sla_minutes_threshold,
    }


def get_escalation_chain(source_dept: str) -> List[Dict[str, Any]]:
    """Get the full escalation chain for a department."""
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT * FROM escalation_rules
            WHERE source_dept = ? AND active = 1
            ORDER BY escalation_level ASC
            """,
            (source_dept,),
        ).fetchall()
    
    return [dict(row) for row in rows]


def trigger_escalation(
    ticket_id: str,
    current_dept: str,
    escalation_level: int = 1,
    reason: str = "SLA threshold exceeded",
) -> Dict[str, Any] | None:
    """Trigger escalation for a ticket to the next level."""
    # Get escalation rule for this department at this level
    with get_connection() as conn:
        rule = conn.execute(
            """
            SELECT * FROM escalation_rules
            WHERE source_dept = ? AND escalation_level = ? AND active = 1
            LIMIT 1
            """,
            (current_dept, escalation_level),
        ).fetchone()
    
    if not rule:
        logger.warning("[ESCALATION] No rule found for %s at level %d", current_dept, escalation_level)
        return None
    
    rule = dict(rule)
    escalation_id = f"esc_{ticket_id}_{escalation_level}_{int(datetime.utcnow().timestamp())}"
    
    with get_connection() as conn:
        # Log escalation
        conn.execute(
            """
            INSERT INTO escalation_history(
                escalation_id, ticket_id, from_dept, to_dept, escalation_level,
                reason, contact_method, escalated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                escalation_id,
                ticket_id,
                current_dept,
                rule["dest_dept"],
                escalation_level,
                reason,
                rule["contact_method"],
                datetime.utcnow().isoformat(),
            ),
        )
        
        # Update ticket with escalation level
        conn.execute(
            "UPDATE tickets SET escalation_level = ? WHERE ticket_id = ?",
            (escalation_level, ticket_id),
        )
    
    logger.info(
        "[ESCALATION] Triggered: ticket %s escalated from %s to %s (level %d)",
        ticket_id,
        current_dept,
        rule["dest_dept"],
        escalation_level,
    )
    
    return {
        "escalation_id": escalation_id,
        "ticket_id": ticket_id,
        "from_dept": current_dept,
        "to_dept": rule["dest_dept"],
        "escalation_level": escalation_level,
        "contact_method": rule["contact_method"],
        "reason": reason,
    }


def get_escalation_history(ticket_id: str) -> List[Dict[str, Any]]:
    """Get escalation history for a ticket."""
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT * FROM escalation_history
            WHERE ticket_id = ?
            ORDER BY escalated_at DESC
            """,
            (ticket_id,),
        ).fetchall()
    
    return [dict(row) for row in rows]


# Initialize schema on import
try:
    initialize_escalation_schema()
except Exception as e:
    logger.warning("Escalation schema already exists or initialization error: %s", e)
