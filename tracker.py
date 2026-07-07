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


def get_location_name(latitude, longitude):

    if latitude is None or longitude is None:
        return "Unknown"


    # Frankfurt Airport
    if (
        49.9 < latitude < 50.2
        and 8.3 < longitude < 8.8
    ):
        return "Frankfurt Airport area (FRA)"


    # Los Angeles Airport
    if (
        33.8 < latitude < 34.1
        and -118.5 < longitude < -118.2
    ):
        return "Los Angeles Airport area (LAX)"


    # Munich Airport
    if (
        48.2 < latitude < 48.5
        and 11.4 < longitude < 11.8
    ):
        return "Munich Airport area (MUC)"


    # Europe general
    if (
        35 < latitude < 60
        and -10 < longitude < 40
    ):
        return "Europe"


    # Atlantic
    if (
        -60 < longitude < -10
        and 20 < latitude < 70
    ):
        return "Atlantic Ocean"


    # Pacific
    if (
        longitude < -100
        and latitude > -50
    ):
        return "Pacific region"


    return "Unknown area"



status = []


for aircraft in fleet:

    icao = aircraft["icao24"].lower()

    registration = aircraft["registration"]
    aircraft_type = aircraft["type"]


    if icao not in positions:

        status.append(
            f"⚪ **{registration}**\n"
            f"{aircraft_type}\n"
            f"Status: `No live position available`"
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

        map_link = (
            f"https://www.google.com/maps?q="
            f"{latitude},{longitude}"
        )

        location = get_location_name(
            latitude,
            longitude
        )

    else:

        position = "Unknown"
        map_link = "Unavailable"
        location = "Unknown"



    last_contact = data["last_contact"]


    if last_contact:

        age_seconds = (
            datetime.now(timezone.utc).timestamp()
            -
            last_contact
        )


        if age_seconds < 60:
            contact = f"{round(age_seconds)} seconds ago"

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
        f"Location: `{location}`\n"
        f"Position: `{position}`\n"
        f"Map: {map_link}\n"
        f"Last contact: `{contact}`"
    )



message = (
    "✈ **Lufthansa 100th Anniversary Fleet Tracker**\n\n"
    +
    "\n\n".join(status)
)



requests.post(
    WEBHOOK,
    json={
        "content": message
    }
)
