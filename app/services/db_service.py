import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Callable, Iterator, List, Tuple

from app.config import settings


MigrationFn = Callable[[sqlite3.Connection], None]


def _db_path() -> Path:
    return Path(settings.SQLITE_DB_PATH)


def _utc_now() -> str:
    return datetime.utcnow().isoformat()


def _column_exists(conn: sqlite3.Connection, table: str, column: str) -> bool:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return any(str(row[1]) == column for row in rows)


def _bootstrap_schema_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            applied_at TEXT NOT NULL
        )
        """
    )

    # Backward compatibility: upgrade older table variants in-place.
    if not _column_exists(conn, "schema_migrations", "name"):
        conn.execute("ALTER TABLE schema_migrations ADD COLUMN name TEXT")
    if not _column_exists(conn, "schema_migrations", "applied_at"):
        conn.execute("ALTER TABLE schema_migrations ADD COLUMN applied_at TEXT")


def _migration_1_base_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS tickets (
            ticket_id TEXT PRIMARY KEY,
            call_id TEXT,
            customer_name TEXT,
            mobile TEXT,
            issue TEXT,
            location TEXT,
            issue_type TEXT,
            department TEXT,
            status TEXT,
            priority TEXT,
            sla_hours INTEGER,
            created_at TEXT,
            sla_deadline TEXT,
            coordinates_lat REAL,
            coordinates_lng REAL,
            resolved_at TEXT
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS call_memory (
            call_id TEXT PRIMARY KEY,
            mobile TEXT,
            language TEXT,
            last_issue TEXT,
            updated_at TEXT
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS call_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            call_id TEXT,
            text TEXT,
            created_at TEXT
        )
        """
    )


def _migration_2_indexes(conn: sqlite3.Connection) -> None:
    conn.execute("CREATE INDEX IF NOT EXISTS idx_call_memory_mobile ON call_memory(mobile)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_call_history_call_id ON call_history(call_id)")


def _migration_3_ticket_location_normalization(conn: sqlite3.Connection) -> None:
    if not _column_exists(conn, "tickets", "normalized_location"):
        conn.execute("ALTER TABLE tickets ADD COLUMN normalized_location TEXT")
    if not _column_exists(conn, "tickets", "geocode_provider"):
        conn.execute("ALTER TABLE tickets ADD COLUMN geocode_provider TEXT")


def _migration_4_audit_timeline(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS audit_timeline (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_time TEXT NOT NULL,
            stage TEXT NOT NULL,
            event_name TEXT NOT NULL,
            call_ref TEXT,
            mobile_ref TEXT,
            issue_type TEXT,
            location_norm TEXT,
            department TEXT,
            outcome TEXT,
            latency_ms INTEGER,
            error_code TEXT,
            meta_json TEXT
        )
        """
    )

    # Backward compatibility with earlier audit table variants.
    required_columns = {
        "event_type": "TEXT",
        "event_time": "TEXT",
        "stage": "TEXT",
        "event_name": "TEXT",
        "call_ref": "TEXT",
        "mobile_ref": "TEXT",
        "issue_type": "TEXT",
        "location_norm": "TEXT",
        "department": "TEXT",
        "outcome": "TEXT",
        "latency_ms": "INTEGER",
        "error_code": "TEXT",
        "meta_json": "TEXT",
    }
    for col, col_type in required_columns.items():
        if not _column_exists(conn, "audit_timeline", col):
            conn.execute(f"ALTER TABLE audit_timeline ADD COLUMN {col} {col_type}")

    conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_event_time ON audit_timeline(event_time)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_stage ON audit_timeline(stage)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_call_ref ON audit_timeline(call_ref)")


MIGRATIONS: List[Tuple[int, str, MigrationFn]] = [
    (1, "base_schema", _migration_1_base_schema),
    (2, "indexes", _migration_2_indexes),
    (3, "ticket_location_normalization", _migration_3_ticket_location_normalization),
    (4, "audit_timeline", _migration_4_audit_timeline),
]


def init_db() -> None:
    path = _db_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(path) as conn:
        _bootstrap_schema_table(conn)

        applied = {
            int(row[0])
            for row in conn.execute("SELECT version FROM schema_migrations").fetchall()
        }

        for version, name, fn in MIGRATIONS:
            if version in applied:
                continue
            fn(conn)
            conn.execute(
                "INSERT INTO schema_migrations(version, name, applied_at) VALUES (?, ?, ?)",
                (version, name, _utc_now()),
            )

        conn.commit()


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(_db_path())
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()
