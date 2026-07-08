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

            last_seen TEXT

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

    cursor.execute(
        """
        INSERT OR REPLACE INTO aircraft_state
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            datetime.utcnow().isoformat()
        )
    )

    conn.commit()
    conn.close()
