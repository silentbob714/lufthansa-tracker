import os
import yaml
import requests
from datetime import datetime, timezone
from dotenv import load_dotenv

from datasource import get_aircraft_positions
from database import (
    initialize_database,
    get_previous_state,
    save_state
)

load_dotenv()

WEBHOOK = os.getenv("DISCORD_WEBHOOK")


initialize_database()


with open("fleet.yaml", "r") as file:
    fleet = yaml.safe_load(file)["aircraft"]


positions = get_aircraft_positions()


alerts = []


def determine_status(altitude_ft, speed_kts):

    if altitude_ft > 1000:
        return "Airborne"

    elif speed_kts > 5:
        return "Ground Movement"

    else:
        return "On Ground"



for aircraft in fleet:

    registration = aircraft["registration"]
    aircraft_type = aircraft["type"]
    icao = aircraft["icao24"].lower()


    if icao not in positions:
        continue


    data = positions[icao]


    altitude_ft = (
        round(data["altitude"] * 3.28084)
        if isinstance(data["altitude"], (int, float))
        else 0
    )


    speed_kts = (
        round(data["velocity"] * 1.94384)
        if isinstance(data["velocity"], (int, float))
        else 0
    )


    callsign = (
        data["callsign"]
        if data["callsign"]
        else "Unknown"
    )


    latitude = data["latitude"]
    longitude = data["longitude"]


    status = determine_status(
        altitude_ft,
        speed_kts
    )


    previous = get_previous_state(
        registration
    )


    if previous:

        previous_status = previous[2]

        if previous_status != status:

            alerts.append(
                f"🚨 **{registration}**\n"
                f"{aircraft_type}\n"
                f"Status change:\n"
                f"`{previous_status}` → `{status}`\n"
                f"Flight: `{callsign}`\n"
                f"Altitude: `{altitude_ft:,} ft`\n"
                f"Speed: `{speed_kts} kts`"
            )

    else:

        alerts.append(
            f"🆕 **Tracking started: {registration}**\n"
            f"{aircraft_type}\n"
            f"Current status: `{status}`"
        )


    save_state(
        registration,
        aircraft_type,
        status,
        callsign,
        altitude_ft,
        speed_kts,
        latitude,
        longitude
    )



if alerts:

    message = (
        "✈ **FlightWatch Alerts**\n\n"
        +
        "\n\n".join(alerts)
    )


    response = requests.post(
        WEBHOOK,
        json={
            "content": message
        }
    )


    print(
        f"Discord response: {response.status_code}"
    )


else:

    print(
        "No aircraft status changes."
    )
