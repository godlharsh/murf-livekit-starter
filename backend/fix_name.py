from src.memory import DB_PATH
import sqlite3

with sqlite3.connect(DB_PATH) as conn:
    conn.execute(
        "UPDATE students SET name = ? WHERE user_id = ?",
        ("Harsh", "student-001"),
    )
    conn.commit()

print("DONE")