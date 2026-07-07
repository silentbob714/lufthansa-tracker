import os
import yaml
import requests


WEBHOOK = os.environ["DISCORD_WEBHOOK"]

username = os.environ["OPENSKY_USERNAME"]
password = os.environ["OPENSKY_PASSWORD"]


with open("fleet.yaml", "r") as file:
    fleet_data = yaml.safe_load(file)


tracked_aircraft = fleet_data["aircraft"]


status = []


for aircraft_info in tracked_aircraft:

    icao24 = aircraft_info["icao24"].lower()
    registration = aircraft_info["registration"]
    aircraft_type = aircraft_info["type"]


    try:

        response = requests.get(
            "https://opensky-network.org/api/states/all",
            params={
                "icao24": icao24
            },
            auth=(username, password),
            timeout=60
        )


        if response.status_code != 200:
            continue


        data = response.json()

        states = data.get("states")


        if not states:

            status.append(
                f"⚪ **{registration}**\n"
                f"{aircraft_type}\n"
                f"Status: Not currently airborne"
            )

            continue


        state = states[0]


        callsign = (
            state[1].strip()
            if state[1]
            else "Unknown"
        )


        altitude_ft = (
            round(state[7] * 3.28084)
            if state[7]
            else "N/A"
        )


        speed_kts = (
            round(state[9] * 1.94384)
            if state[9]
            else "N/A"
        )


        latitude = state[6]
        longitude = state[5]


        status.append(
            f"🟢 **{registration}**\n"
            f"{aircraft_type}\n"
            f"Flight: `{callsign}`\n"
            f"Altitude: `{altitude_ft:,} ft`\n"
            f"Speed: `{speed_kts} kts`\n"
            f"Position: `{latitude:.3f}, {longitude:.3f}`"
        )


    except Exception as e:

        status.append(
            f"❌ **{registration}**\n"
            f"Error: {e}"
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
