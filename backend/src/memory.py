import sqlite3
from pathlib import Path
from datetime import datetime


DB_PATH = Path(__file__).resolve().parent.parent / "data" / "edubuddy.db"


def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS students (
                user_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                language_preference TEXT,
                current_level TEXT,
                topics_covered TEXT,
                common_mistakes TEXT,
                last_interaction TEXT
            )
            """
        )
        conn.commit()


def lookup_user(user_id: str):
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row

        row = conn.execute(
            """
            SELECT
                user_id,
                name,
                language_preference,
                current_level,
                topics_covered,
                common_mistakes,
                last_interaction
            FROM students
            WHERE user_id = ?
            """,
            (user_id,),
        ).fetchone()

        if row is None:
            return None

        return dict(row)


def save_user(
    user_id: str,
    name: str,
    language_preference: str = "",
    current_level: str = "",
    topics_covered: str = "",
    common_mistakes: str = "",
):
    timestamp = datetime.now().isoformat(timespec="seconds")

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT INTO students (
                user_id,
                name,
                language_preference,
                current_level,
                topics_covered,
                common_mistakes,
                last_interaction
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                name = excluded.name,
                language_preference = excluded.language_preference,
                current_level = excluded.current_level,
                topics_covered = excluded.topics_covered,
                common_mistakes = excluded.common_mistakes,
                last_interaction = excluded.last_interaction
            """,
            (
                user_id,
                name,
                language_preference,
                current_level,
                topics_covered,
                common_mistakes,
                timestamp,
            ),
        )
        conn.commit()

    return {
        "user_id": user_id,
        "name": name,
        "language_preference": language_preference,
        "current_level": current_level,
        "topics_covered": topics_covered,
        "common_mistakes": common_mistakes,
        "last_interaction": timestamp,
    }