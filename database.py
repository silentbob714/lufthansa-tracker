import sqlite3
from datetime import datetime


DATABASE = "flightwatch.db"


def get_connection():
    return sqlite3.connect(DATABASE)


def initialize_database():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS aircraft_state (

            registration TEXT PRIMARY KEY,

            aircraft_type TEXT,

            status TEXT,

            callsign TEXT,

            altitude INTEGER,

            speed INTEGER,

            latitude REAL,

            longitude REAL,

            first_seen TEXT,

            last_seen TEXT

        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS aircraft_events (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            registration TEXT,

            aircraft_type TEXT,

            event_type TEXT,

            callsign TEXT,

            latitude REAL,

            longitude REAL,

            timestamp TEXT

        )
        """
    )

    conn.commit()
    conn.close()


def get_previous_state(registration):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM aircraft_state
        WHERE registration = ?
        """,
        (registration,)
    )

    result = cursor.fetchone()

    conn.close()

    return result


def save_state(
    registration,
    aircraft_type,
    status,
    callsign,
    altitude,
    speed,
    latitude,
    longitude
):

    conn = get_connection()
    cursor = conn.cursor()

    existing = get_previous_state(
        registration
    )

    now = datetime.utcnow().isoformat()

    if existing:
        first_seen = existing[8]
    else:
        first_seen = now

    cursor.execute(
        """
        INSERT OR REPLACE INTO aircraft_state
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            registration,
            aircraft_type,
            status,
            callsign,
            altitude,
            speed,
            latitude,
            longitude,
            first_seen,
            now
        )
    )

    conn.commit()
    conn.close()


def log_event(
    registration,
    aircraft_type,
    event_type,
    callsign,
    latitude,
    longitude
):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO aircraft_events
        (
            registration,
            aircraft_type,
            event_type,
            callsign,
            latitude,
            longitude,
            timestamp
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            registration,
            aircraft_type,
            event_type,
            callsign,
            latitude,
            longitude,
            datetime.utcnow().isoformat()
        )
    )

    conn.commit()
    conn.close()
