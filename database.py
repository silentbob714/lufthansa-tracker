import sqlite3
from datetime import datetime


DATABASE = "flightwatch.db"


def get_connection():
    return sqlite3.connect(DATABASE)



def initialize_database():

    conn = get_connection()
    cursor = conn.cursor()


    # Aircraft identity / metadata

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS aircraft_metadata (

            icao24 TEXT PRIMARY KEY,

            registration TEXT,

            manufacturer TEXT,

            model TEXT,

            type_designator TEXT,

            operator TEXT,

            owner TEXT,

            country TEXT,

            category TEXT,

            last_updated TEXT

        )
    """)



    # Aircraft selected for tracking

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tracked_aircraft (

            icao24 TEXT PRIMARY KEY,

            nickname TEXT,

            added_by TEXT,

            active INTEGER DEFAULT 1,

            added_date TEXT

        )
    """)



    # Live aircraft state

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS aircraft_state (

            icao24 TEXT PRIMARY KEY,

            status TEXT,

            callsign TEXT,

            altitude INTEGER,

            speed INTEGER,

            latitude REAL,

            longitude REAL,

            first_seen TEXT,

            last_seen TEXT

        )
    """)



    # Historical events

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS aircraft_events (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            icao24 TEXT,

            event_type TEXT,

            callsign TEXT,

            latitude REAL,

            longitude REAL,

            timestamp TEXT

        )
    """)



    # Migration:
    # Preserve old tracked_aircraft entries if they exist

    try:

        cursor.execute(
            """
            INSERT OR IGNORE INTO tracked_aircraft
            (
                icao24,
                nickname,
                added_by,
                active,
                added_date
            )

            SELECT
                icao24,
                registration,
                'migration',
                active,
                added_date

            FROM old_tracked_aircraft
            """
        )

    except sqlite3.OperationalError:

        pass



    conn.commit()
    conn.close()



def get_tracked_aircraft():

    conn = get_connection()

    cursor = conn.cursor()


    cursor.execute(
        """
        SELECT
            t.icao24,
            m.registration,
            m.manufacturer,
            m.model,
            m.operator,
            m.category

        FROM tracked_aircraft t

        LEFT JOIN aircraft_metadata m

        ON t.icao24 = m.icao24

        WHERE t.active = 1

        ORDER BY m.registration
        """
    )


    rows = cursor.fetchall()


    conn.close()


    return rows



def add_tracked_aircraft(

    icao24,

    nickname=None,

    added_by="system"

):

    conn = get_connection()

    cursor = conn.cursor()


    cursor.execute(
        """
        INSERT OR REPLACE INTO tracked_aircraft

        (
            icao24,
            nickname,
            added_by,
            active,
            added_date
        )

        VALUES (?, ?, ?, 1, ?)

        """,

        (

            icao24.lower(),

            nickname,

            added_by,

            datetime.utcnow().isoformat()

        )

    )


    conn.commit()

    conn.close()



def get_previous_state(icao24):

    conn = get_connection()

    cursor = conn.cursor()


    cursor.execute(
        """
        SELECT *

        FROM aircraft_state

        WHERE icao24 = ?

        """,

        (icao24.lower(),)

    )


    result = cursor.fetchone()


    conn.close()


    return result



def save_state(

    icao24,

    status,

    callsign,

    altitude,

    speed,

    latitude,

    longitude

):

    conn = get_connection()

    cursor = conn.cursor()


    existing = get_previous_state(icao24)


    now = datetime.utcnow().isoformat()


    if existing:

        first_seen = existing[7]

    else:

        first_seen = now



    cursor.execute(
        """
        INSERT OR REPLACE INTO aircraft_state

        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)

        """,

        (

            icao24.lower(),

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

    icao24,

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

            icao24,

            event_type,

            callsign,

            latitude,

            longitude,

            timestamp

        )

        VALUES (?, ?, ?, ?, ?, ?)

        """,

        (

            icao24.lower(),

            event_type,

            callsign,

            latitude,

            longitude,

            datetime.utcnow().isoformat()

        )

    )


    conn.commit()

    conn.close()
