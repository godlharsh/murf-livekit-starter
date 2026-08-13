from flask import Flask, render_template_string
import sqlite3
from pathlib import Path

app = Flask(__name__)

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "edubuddy.db"

TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Bharat Buddy - Call Analytics</title>
    <meta http-equiv="refresh" content="10">
    <style>
        body {
            background: #0f0f0f;
            color: #fff;
            font-family: Arial, sans-serif;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding-top: 60px;
        }
        h1 { margin-bottom: 40px; }
        .cards {
            display: flex;
            gap: 30px;
        }
        .card {
            background: #1a1a1a;
            border-radius: 12px;
            padding: 30px 50px;
            text-align: center;
            box-shadow: 0 0 10px rgba(255,255,255,0.05);
        }
        .card h2 {
            font-size: 40px;
            margin: 0;
        }
        .card p {
            color: #aaa;
            margin-top: 8px;
        }
        .success { color: #4ade80; }
        .failed { color: #f87171; }
    </style>
</head>
<body>
    <h1>📊 Bharat Buddy - Call Analytics</h1>
    <div class="cards">
        <div class="card">
            <h2>{{ total }}</h2>
            <p>Total Calls</p>
        </div>
        <div class="card">
            <h2 class="success">{{ success }}</h2>
            <p>Successful Calls</p>
        </div>
        <div class="card">
            <h2 class="failed">{{ failed }}</h2>
            <p>Failed Calls</p>
        </div>
    </div>
</body>
</html>
"""


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

        return total, success, failed


@app.route("/")
def dashboard():
    total, success, failed = get_stats()
    return render_template_string(TEMPLATE, total=total, success=success, failed=failed)


if __name__ == "__main__":
    app.run(port=5050, debug=True)