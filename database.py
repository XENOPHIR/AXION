import sqlite3
import uuid
from datetime import datetime
from typing import Optional

import os
os.makedirs("data", exist_ok=True)
DB_PATH = "data/accessbank_cases.db"


def init_db():
    """Initialize the database and create tables if they don't exist."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cases (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            username TEXT,
            issue_description TEXT NOT NULL,
            department TEXT NOT NULL,
            severity TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'open',
            collected_info TEXT,
            email_sent_to TEXT,
            email_message_id TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS case_timeline (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_id TEXT NOT NULL,
            event TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            FOREIGN KEY (case_id) REFERENCES cases (id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ratings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            case_id TEXT,
            stars INTEGER NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ratings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            username TEXT,
            stars INTEGER NOT NULL,
            case_id TEXT,
            created_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def save_rating(user_id: str, username: str, stars: int, case_id: str = None):
    now = datetime.utcnow().isoformat()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO ratings (user_id, username, stars, case_id, created_at) VALUES (?, ?, ?, ?, ?)",
        (user_id, username, stars, case_id, now),
    )
    conn.commit()
    conn.close()


def get_rating_stats() -> dict:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT AVG(stars), COUNT(*) FROM ratings")
    avg, total = cursor.fetchone()
    conn.close()
    return {"average": round(avg or 0, 1), "total": total or 0}


def create_case(
    user_id: str,
    username: str,
    issue_description: str,
    department: str,
    severity: str,
    collected_info: str,
    email_sent_to: str,
    email_message_id: str = None,
) -> str:
    """Create a new support case and return the case ID."""
    case_id = "AB-" + str(uuid.uuid4())[:8].upper()
    now = datetime.utcnow().isoformat()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO cases (id, user_id, username, issue_description, department,
            severity, status, collected_info, email_sent_to, email_message_id,
            created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, 'open', ?, ?, ?, ?, ?)
    """,
        (
            case_id, user_id, username, issue_description, department,
            severity, collected_info, email_sent_to, email_message_id, now, now,
        ),
    )

    # Add timeline entry
    cursor.execute(
        "INSERT INTO case_timeline (case_id, event, timestamp) VALUES (?, ?, ?)",
        (case_id, "✅ Case created and registered", now),
    )
    cursor.execute(
        "INSERT INTO case_timeline (case_id, event, timestamp) VALUES (?, ?, ?)",
        (case_id, f"📂 Routed to department: {department}", now),
    )
    cursor.execute(
        "INSERT INTO case_timeline (case_id, event, timestamp) VALUES (?, ?, ?)",
        (case_id, f"📧 Escalation email sent to {email_sent_to}", now),
    )

    conn.commit()
    conn.close()
    return case_id


def get_case(case_id: str) -> Optional[dict]:
    """Retrieve a case by its ID."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM cases WHERE id = ?", (case_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None


def get_case_timeline(case_id: str) -> list:
    """Retrieve timeline events for a case."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM case_timeline WHERE case_id = ? ORDER BY timestamp ASC",
        (case_id,),
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def update_case_status(case_id: str, new_status: str):
    """Update the status of a case."""
    now = datetime.utcnow().isoformat()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE cases SET status = ?, updated_at = ? WHERE id = ?",
        (new_status, now, case_id),
    )
    cursor.execute(
        "INSERT INTO case_timeline (case_id, event, timestamp) VALUES (?, ?, ?)",
        (case_id, f"🔄 Status updated to: {new_status}", now),
    )
    conn.commit()
    conn.close()


def get_user_cases(user_id: str) -> list:
    """Get all cases for a specific user."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM cases WHERE user_id = ? ORDER BY created_at DESC",
        (user_id,),
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]





def get_rating_stats() -> dict:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT AVG(stars), COUNT(*) FROM ratings")
    avg, total = cursor.fetchone()
    conn.close()
    return {"average": round(avg or 0, 1), "total": total or 0}