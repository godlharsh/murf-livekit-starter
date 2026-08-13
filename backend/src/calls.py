import sqlite3
import uuid
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "edubuddy.db"


def init_calls_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS calls (
                call_id TEXT PRIMARY KEY,
                channel TEXT,
                started_at TEXT,
                ended_at TEXT,
                outcome TEXT,
                reason TEXT
            )
            """
        )
        conn.commit()


def start_call(call_id: str, channel: str = "browser"):
    started_at = datetime.now().isoformat(timespec="seconds")

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO calls (call_id, channel, started_at, outcome)
            VALUES (?, ?, ?, ?)
            """,
            (call_id, channel, started_at, "in_progress"),
        )
        conn.commit()


def end_call(call_id: str, success: bool, reason: str = ""):
    ended_at = datetime.now().isoformat(timespec="seconds")
    outcome = "success" if success else "failed"

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            UPDATE calls
            SET ended_at = ?, outcome = ?, reason = ?
            WHERE call_id = ?
            """,
            (ended_at, outcome, reason, call_id),
        )
        conn.commit()


def get_stats():
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row

        total = conn.execute(
            "SELECT COUNT(*) as c FROM calls WHERE outcome != 'in_progress'"
        ).fetchone()["c"]

        success = conn.execute(
            "SELECT COUNT(*) as c FROM calls WHERE outcome = 'success'"
        ).fetchone()["c"]

        failed = conn.execute(
            "SELECT COUNT(*) as c FROM calls WHERE outcome = 'failed'"
        ).fetchone()["c"]

        return {"total": total, "success": success, "failed": failed}