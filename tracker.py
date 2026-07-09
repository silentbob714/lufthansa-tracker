import os
import requests

from dotenv import load_dotenv

from datasource import get_aircraft_positions

from database import (
    get_tracked_aircraft,
    get_previous_state,
    save_state,
    log_event
)


load_dotenv()


WEBHOOK = os.environ["DISCORD_WEBHOOK"]


print("Running FlightWatch check...")


positions = get_aircraft_positions()


print(
    f"OpenSky returned {len(positions)} aircraft states."
)



def get_location_name(latitude, longitude):

    if latitude is None or longitude is None:
        return "Unknown"


    if (
        49.9 < latitude < 50.2
        and 8.3 < longitude < 8.8
    ):
        return "Frankfurt Airport area (FRA)"


    if (
        48.2 < latitude < 48.5
        and 11.4 < longitude < 11.8
    ):
        return "Munich Airport area (MUC)"


    if (
        35 < latitude < 60
        and -10 < longitude < 40
    ):
        return "Europe"


    return "Unknown area"



tracked = get_tracked_aircraft()


events = []



for aircraft in tracked:

    icao24 = aircraft[0]

    registration = aircraft[1] or icao24.upper()

    manufacturer = aircraft[2] or ""

    model = aircraft[3] or "Unknown"

    operator = aircraft[4] or "Unknown"

    category = aircraft[5] or "Unknown"



    previous = get_previous_state(icao24)



    if icao24 not in positions:

        continue



    data = positions[icao24]


    altitude_ft = (

        round(data["altitude"] * 3.28084)

        if isinstance(data["altitude"], (int,float))

        else 0

    )


    speed_kts = (

        round(data["velocity"] * 1.94384)

        if isinstance(data["velocity"], (int,float))

        else 0

    )


    callsign = data["callsign"] or "Unknown"


    latitude = data["latitude"]

    longitude = data["longitude"]


    location = get_location_name(
        latitude,
        longitude
    )



    if altitude_ft > 1000:

        current_status = "Airborne"

    elif speed_kts > 5:

        current_status = "Ground movement"

    else:

        current_status = "On ground"



    event = None



    if previous:

        old_status = previous[1]


        if (
            old_status != "Airborne"
            and current_status == "Airborne"
        ):

            event = "Takeoff detected"



        elif (

            old_status == "Airborne"

            and current_status == "On ground"

        ):

            event = "Landing detected"



    else:

        event = "Aircraft tracking started"



    save_state(

        icao24,

        current_status,

        callsign,

        altitude_ft,

        speed_kts,

        latitude,

        longitude

    )



    if event:


        log_event(

            icao24,

            event,

            callsign,

            latitude,

            longitude

        )


        events.append(

            f"✈ **FlightWatch Alert**\n\n"

            f"🟢 **{registration}**\n"

            f"{manufacturer} {model}\n"

            f"Operator: `{operator}`\n"

            f"Category: `{category}`\n\n"

            f"Event: `{event}`\n"

            f"Flight: `{callsign}`\n"

            f"Altitude: `{altitude_ft:,} ft`\n"

            f"Speed: `{speed_kts} kts`\n"

            f"Location: `{location}`\n"

        )



if events:


    message = "\n\n".join(events)


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
        "No aircraft events detected."
    )


