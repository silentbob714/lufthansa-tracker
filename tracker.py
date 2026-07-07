import os
import yaml
import requests


WEBHOOK = os.environ["DISCORD_WEBHOOK"]

username = os.environ["OPENSKY_USERNAME"]
password = os.environ["OPENSKY_PASSWORD"]


with open("fleet.yaml", "r") as file:
    fleet_data = yaml.safe_load(file)


tracked_aircraft = {}

for aircraft in fleet_data["aircraft"]:
    tracked_aircraft[aircraft["icao24"].lower()] = {
        "registration": aircraft["registration"],
        "type": aircraft["type"]
    }


status = []


try:

    response = requests.get(
        "https://opensky-network.org/api/states/all",
        auth=(username, password),
        timeout=120
    )

    response.raise_for_status()

    data = response.json()


    detected = {}

    for state in data.get("states", []):

        icao = state[0].lower()

        if icao in tracked_aircraft:
            detected[icao] = state


    for icao, info in tracked_aircraft.items():

        registration = info["registration"]
        aircraft_type = info["type"]


        if icao not in detected:

            status.append(
                f"⚪ **{registration}**\n"
                f"{aircraft_type}\n"
                f"Status: Not currently airborne"
            )

            continue


        state = detected[icao]


        callsign = (
            state[1].strip()
            if state[1]
            else "Unknown"
        )


        altitude_ft = (
            round(state[7] * 3.28084)
            if isinstance(state[7], (int, float))
            else None
        )

        speed_kts = (
            round(state[9] * 1.94384)
            if isinstance(state[9], (int, float))
            else None
        )


        latitude = state[6]
        longitude = state[5]


        altitude_text = (
            f"{altitude_ft:,} ft"
            if altitude_ft
            else "Unknown"
        )

        speed_text = (
            f"{speed_kts} kts"
            if speed_kts
            else "Unknown"
        )

        position_text = (
            f"{latitude:.3f}, {longitude:.3f}"
            if latitude and longitude
            else "Unknown"
        )


        status.append(
            f"🟢 **{registration}**\n"
            f"{aircraft_type}\n"
            f"Flight: `{callsign}`\n"
            f"Altitude: `{altitude_text}`\n"
            f"Speed: `{speed_text}`\n"
            f"Position: `{position_text}`"
        )


except Exception as e:

    status.append(
        f"❌ OpenSky Error:\n`{e}`"
    )


message = (
    "✈ **Lufthansa 100th Anniversary Fleet Status**\n\n"
    +
    "\n\n".join(status)
)


requests.post(
    WEBHOOK,
    json={
        "content": message
    }
)
