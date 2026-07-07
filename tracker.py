import os
import yaml
import requests
from datetime import datetime, timezone

from datasource import get_aircraft_positions


WEBHOOK = os.environ["DISCORD_WEBHOOK"]


with open("fleet.yaml", "r") as file:
    fleet_data = yaml.safe_load(file)


fleet = fleet_data["aircraft"]


positions = get_aircraft_positions()


status = []


for aircraft in fleet:

    icao = aircraft["icao24"].lower()

    registration = aircraft["registration"]
    aircraft_type = aircraft["type"]


    if icao not in positions:

        status.append(
            f"⚪ **{registration}**\n"
            f"{aircraft_type}\n"
            f"Status: No live position available"
        )

        continue


    data = positions[icao]


    altitude_m = data["altitude"]
    speed_ms = data["velocity"]


    altitude_ft = (
        round(altitude_m * 3.28084)
        if isinstance(altitude_m, (int, float))
        else 0
    )


    speed_kts = (
        round(speed_ms * 1.94384)
        if isinstance(speed_ms, (int, float))
        else 0
    )


    # Determine aircraft status

    if altitude_ft > 1000:

        icon = "🟢"
        aircraft_status = "Airborne"


    elif speed_kts > 80:

        icon = "🟢"
        aircraft_status = "Airborne transition"


    elif speed_kts > 5:

        icon = "🟡"
        aircraft_status = "Ground movement"


    else:

        icon = "🔵"
        aircraft_status = "On ground"


    callsign = data["callsign"]

    if not callsign or callsign == "Unknown":

        if aircraft_status == "Ground movement":

            callsign = "Ground operation"

        else:

            callsign = "Not transmitting"


    latitude = data["latitude"]
    longitude = data["longitude"]


    if (
        isinstance(latitude, (int, float))
        and isinstance(longitude, (int, float))
    ):

        position = (
            f"{latitude:.3f}, {longitude:.3f}"
        )

    else:

        position = "Unknown"


    last_contact = data["last_contact"]


    if last_contact:

        age_seconds = (
            datetime.now(timezone.utc).timestamp()
            -
            last_contact
        )


        if age_seconds < 60:

            contact = (
                f"{round(age_seconds)} seconds ago"
            )

        else:

            contact = (
                f"{round(age_seconds / 60)} minutes ago"
            )

    else:

        contact = "Unknown"


    status.append(
        f"{icon} **{registration}**\n"
        f"{aircraft_type}\n"
        f"Status: `{aircraft_status}`\n"
        f"Flight: `{callsign}`\n"
        f"Altitude: `{altitude_ft:,} ft`\n"
        f"Speed: `{speed_kts} kts`\n"
        f"Position: `{position}`\n"
        f"Last contact: `{contact}`"
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
