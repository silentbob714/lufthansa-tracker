import sqlite3
from datetime import datetime, timezone

DB = "alerts.db"


def setup_database():
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            aircraft TEXT,
            flight TEXT,
            alerted_at TEXT
        )
    """)

    conn.commit()
    conn.close()


def already_alerted(aircraft, flight):
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT alerted_at
        FROM alerts
        WHERE aircraft = ?
        AND flight = ?
        ORDER BY alerted_at DESC
        LIMIT 1
    """, (aircraft, flight))

    result = cursor.fetchone()

    conn.close()

    if result:
        return True

    return False


def save_alert(aircraft, flight):
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO alerts
        VALUES (?, ?, ?)
    """, (
        aircraft,
        flight,
        datetime.now(timezone.utc).isoformat()
    ))

    conn.commit()
    conn.close()
