import os
import requests
import time
from dotenv import load_dotenv

load_dotenv()


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

            return aircraft

        except Exception as e:

            print(
                f"OpenSky attempt {attempt + 1}/3 failed: {e}"
            )

            if attempt < 2:
                time.sleep(10)

    print("OpenSky unavailable. Returning empty dataset.")

    return {}
