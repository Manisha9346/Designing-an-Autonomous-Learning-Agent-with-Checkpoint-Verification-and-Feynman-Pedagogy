import sqlite3
from datetime import datetime

DB_NAME = "student.db"


# --------------------------------------------------
# Initialize database (auto-creates DB & table)
# --------------------------------------------------
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            concept TEXT,
            score INTEGER,
            attempts INTEGER,
            status TEXT,
            badge TEXT,
            timestamp TEXT
        )
    """)

    conn.commit()
    conn.close()


# --------------------------------------------------
# Badge logic
# --------------------------------------------------
def get_badge(score):
    if score >= 90:
        return "🥇 Gold"
    elif score >= 75:
        return "🥈 Silver"
    elif score >= 60:
        return "🥉 Bronze"
    else:
        return "🔁 Keep Trying"


# --------------------------------------------------
# Save progress
# --------------------------------------------------
def save_progress(username, concept, score, attempts):
    badge = get_badge(score)
    status = "PASS" if score >= 70 else "FAIL"

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO progress
        (username, concept, score, attempts, status, badge, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        username,
        concept,
        score,
        attempts,
        status,
        badge,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))

    conn.commit()
    conn.close()


# --------------------------------------------------
# Load progress by user
# --------------------------------------------------
def load_progress_by_user(username):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT concept, score, attempts, status, badge
        FROM progress
        WHERE username = ?
        ORDER BY id
    """, (username,))

    data = cursor.fetchall()
    conn.close()
    return data
