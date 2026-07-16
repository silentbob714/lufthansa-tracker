import os
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv


load_dotenv()


PROJECT_DIR = Path(__file__).resolve().parent
DATABASE_PATH = PROJECT_DIR / "flightwatch.db"
PROVIDER_NAME = "OpenSky"


def save_provider_status(
    status,
    aircraft_count=0,
    retry_after_seconds=None,
    detail=None
):

    checked_at = datetime.now(
        timezone.utc
    ).isoformat()

    connection = None

    try:
        connection = sqlite3.connect(
            DATABASE_PATH,
            timeout=10
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS provider_status (
                provider TEXT PRIMARY KEY,
                status TEXT NOT NULL,
                checked_at TEXT NOT NULL,
                aircraft_count INTEGER NOT NULL DEFAULT 0,
                retry_after_seconds INTEGER,
                detail TEXT
            )
            """
        )

        connection.execute(
            """
            INSERT INTO provider_status (
                provider,
                status,
                checked_at,
                aircraft_count,
                retry_after_seconds,
                detail
            )
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(provider) DO UPDATE SET
                status = excluded.status,
                checked_at = excluded.checked_at,
                aircraft_count = excluded.aircraft_count,
                retry_after_seconds = excluded.retry_after_seconds,
                detail = excluded.detail
            """,
            (
                PROVIDER_NAME,
                status,
                checked_at,
                aircraft_count,
                retry_after_seconds,
                detail
            )
        )

        connection.commit()

    except sqlite3.Error as error:
        print(
            "Unable to save OpenSky provider status: "
            f"{error}"
        )

    finally:
        if connection is not None:
            connection.close()


def parse_retry_after(response):

    raw_value = response.headers.get(
        "X-Rate-Limit-Retry-After-Seconds"
    )

    if raw_value is None:
        raw_value = response.headers.get(
            "Retry-After"
        )

    if raw_value is None:
        return None

    try:
        return max(
            0,
            int(float(raw_value))
        )

    except (TypeError, ValueError):
        return None


def get_aircraft_positions():

    username = os.getenv("OPENSKY_USERNAME")
    password = os.getenv("OPENSKY_PASSWORD")

    url = "https://opensky-network.org/api/states/all"

    for attempt in range(3):

        try:
            response = requests.get(
                url,
                auth=(username, password),
                timeout=45
            )

            if response.status_code == 429:
                retry_after = parse_retry_after(
                    response
                )

                retry_display = (
                    str(retry_after)
                    if retry_after is not None
                    else "unknown"
                )

                print(
                    "OpenSky rate limited. "
                    f"Retry after {retry_display} seconds."
                )

                save_provider_status(
                    status="rate_limited",
                    aircraft_count=0,
                    retry_after_seconds=retry_after,
                    detail="OpenSky returned HTTP 429."
                )

                return {}

            response.raise_for_status()

            data = response.json()

            aircraft = {}

            for state in data.get("states", []):

                try:
                    icao = state[0].lower()

                    aircraft[icao] = {
                        "callsign": (
                            state[1].strip()
                            if state[1]
                            else "Unknown"
                        ),
                        "longitude": state[5],
                        "latitude": state[6],
                        "altitude": state[7],
                        "velocity": state[9],
                        "heading": state[10],
                        "last_contact": state[4]
                    }

                except Exception:
                    continue

            save_provider_status(
                status="healthy",
                aircraft_count=len(aircraft),
                retry_after_seconds=None,
                detail="OpenSky request completed successfully."
            )

            return aircraft

        except requests.RequestException as error:
            print(
                f"OpenSky attempt {attempt + 1}/3 failed: "
                f"{error}"
            )

            if attempt < 2:
                time.sleep(10)

            else:
                save_provider_status(
                    status="error",
                    aircraft_count=0,
                    retry_after_seconds=None,
                    detail=str(error)[:500]
                )

        except ValueError as error:
            print(
                "OpenSky returned an invalid JSON response: "
                f"{error}"
            )

            save_provider_status(
                status="error",
                aircraft_count=0,
                retry_after_seconds=None,
                detail="OpenSky returned invalid JSON."
            )

            return {}

    print("OpenSky unavailable. Returning empty dataset.")

    return {}
