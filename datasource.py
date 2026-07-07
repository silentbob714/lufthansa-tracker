import os
import requests


def get_aircraft_positions():

    username = os.environ["OPENSKY_USERNAME"]
    password = os.environ["OPENSKY_PASSWORD"]


    response = requests.get(
        "https://opensky-network.org/api/states/all",
        auth=(username, password),
        timeout=120
    )


    response.raise_for_status()

    data = response.json()


    aircraft = {}


    for state in data.get("states", []):

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


    return aircraft
