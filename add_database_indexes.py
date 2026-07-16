import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent
DATABASE_PATH = PROJECT_DIR / "flightwatch.db"
BACKUP_DIR = PROJECT_DIR / "backups"


INDEXES = {
    "idx_aircraft_metadata_registration": """
        CREATE INDEX IF NOT EXISTS
            idx_aircraft_metadata_registration
        ON aircraft_metadata (registration)
    """,

    "idx_tracked_aircraft_active": """
        CREATE INDEX IF NOT EXISTS
            idx_tracked_aircraft_active
        ON tracked_aircraft (active)
    """,

    "idx_aircraft_state_last_seen": """
        CREATE INDEX IF NOT EXISTS
            idx_aircraft_state_last_seen
        ON aircraft_state (last_seen)
    """,

    "idx_aircraft_events_icao24_id": """
        CREATE INDEX IF NOT EXISTS
            idx_aircraft_events_icao24_id
        ON aircraft_events (icao24, id DESC)
    """,

    "idx_aircraft_events_event_type": """
        CREATE INDEX IF NOT EXISTS
            idx_aircraft_events_event_type
        ON aircraft_events (event_type)
    """,

    "idx_aircraft_events_timestamp": """
        CREATE INDEX IF NOT EXISTS
            idx_aircraft_events_timestamp
        ON aircraft_events (timestamp)
    """
}


def create_backup():
    BACKUP_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    timestamp = datetime.now().strftime(
        "%Y%m%d-%H%M%S"
    )

    backup_path = BACKUP_DIR / (
        f"flightwatch-before-indexes-{timestamp}.db"
    )

    shutil.copy2(
        DATABASE_PATH,
        backup_path
    )

    return backup_path


def get_existing_tables(connection):
    rows = connection.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        """
    ).fetchall()

    return {
        row[0]
        for row in rows
    }


def get_existing_indexes(connection):
    rows = connection.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'index'
          AND name NOT LIKE 'sqlite_autoindex_%'
        ORDER BY name
        """
    ).fetchall()

    return [
        row[0]
        for row in rows
    ]


def verify_required_tables(connection):
    required_tables = {
        "aircraft_metadata",
        "tracked_aircraft",
        "aircraft_state",
        "aircraft_events"
    }

    existing_tables = get_existing_tables(
        connection
    )

    missing_tables = (
        required_tables - existing_tables
    )

    if missing_tables:
        raise RuntimeError(
            "Missing required database tables: "
            + ", ".join(sorted(missing_tables))
        )


def create_indexes(connection):
    for index_name, statement in INDEXES.items():
        connection.execute(
            statement
        )

        print(
            f"Verified index: {index_name}"
        )


def verify_indexes(connection):
    existing_indexes = set(
        get_existing_indexes(connection)
    )

    missing_indexes = (
        set(INDEXES) - existing_indexes
    )

    if missing_indexes:
        raise RuntimeError(
            "Index verification failed. Missing: "
            + ", ".join(sorted(missing_indexes))
        )

    return sorted(
        set(INDEXES) & existing_indexes
    )


def main():
    if not DATABASE_PATH.exists():
        print(
            f"Database not found: {DATABASE_PATH}",
            file=sys.stderr
        )

        return 1

    backup_path = create_backup()

    print(
        f"Backup created: {backup_path}"
    )

    connection = sqlite3.connect(
        DATABASE_PATH
    )

    try:
        connection.execute(
            "BEGIN IMMEDIATE"
        )

        verify_required_tables(
            connection
        )

        create_indexes(
            connection
        )

        verified_indexes = verify_indexes(
            connection
        )

        connection.commit()

        print(
            "Database indexes completed successfully."
        )

        print(
            f"Verified {len(verified_indexes)} "
            "FlightWatch indexes:"
        )

        for index_name in verified_indexes:
            print(
                f"- {index_name}"
            )

        return 0

    except Exception as error:
        connection.rollback()

        print(
            f"Index migration failed: {error}",
            file=sys.stderr
        )

        print(
            "The transaction was rolled back. "
            f"Backup remains at: {backup_path}",
            file=sys.stderr
        )

        return 1

    finally:
        connection.close()


if __name__ == "__main__":
    raise SystemExit(main())
