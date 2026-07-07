import os
import requests

WEBHOOK = os.environ["DISCORD_WEBHOOK"]

username = os.environ["OPENSKY_USERNAME"]
password = os.environ["OPENSKY_PASSWORD"]

ANNIVERSARY_AIRCRAFT = {
    "3C4A15": "D-ABPU | Boeing 787-9",
    "3C670C": "D-AIXL | Airbus A350-900",
    "3C4B2E": "D-ABYN | Boeing 747-8",
    "3C65A8": "D-AIMH | Airbus A380"
}

found = []

for icao24, description in ANNIVERSARY_AIRCRAFT.items():

    response = requests.get(
        "https://opensky-network.org/api/states/all",
        params={
            "icao24": icao24.lower()
        },
        auth=(username, password),
        timeout=60
    )

    if response.status_code != 200:
        continue

    data = response.json()

    states = data.get("states")

    if states:
        aircraft = states[0]

        callsign = aircraft[1].strip() if aircraft[1] else "Unknown"
        altitude = aircraft[7]

        found.append(
            f"✈ {description}\n"
            f"Flight: {callsign}\n"
            f"Altitude: {altitude} m"
        )


if found:
    message = (
        "🚨 Lufthansa 100th Anniversary Aircraft Detected\n\n"
        + "\n\n".join(found)
    )
else:
    message = "No anniversary aircraft currently airborne."

requests.post(
    WEBHOOK,
    json={"content": message}
)
