import os
from datetime import datetime, timezone

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


WEBHOOK = os.getenv("DISCORD_WEBHOOK")


if not WEBHOOK:
    raise RuntimeError(
        "DISCORD_WEBHOOK is missing from the environment."
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
        33.7 < latitude < 34.1
        and -118.7 < longitude < -118.1
    ):
        return "Los Angeles Airport area (LAX)"

    if (
        35 < latitude < 60
        and -10 < longitude < 40
    ):
        return "Europe"

    if (
        0 < latitude < 70
        and -80 < longitude < -10
    ):
        return "North Atlantic"

    if (
        0 < latitude < 70
        and -180 < longitude < -100
    ):
        return "North Pacific"

    return "Unknown area"


def get_map_url(latitude, longitude):

    if latitude is None or longitude is None:
        return None

    return (
        "https://www.google.com/maps/search/"
        f"?api=1&query={latitude},{longitude}"
    )


def get_event_style(event):

    if event == "Takeoff detected":
        return {
            "title": "🛫 Takeoff Detected",
            "color": 0x57F287
        }

    if event == "Landing detected":
        return {
            "title": "🛬 Landing Detected",
            "color": 0x3498DB
        }

    if event == "Aircraft tracking started":
        return {
            "title": "📡 Aircraft Tracking Started",
            "color": 0xFEE75C
        }

    return {
        "title": "✈️ FlightWatch Alert",
        "color": 0x5865F2
    }


def build_alert_embed(
    event,
    registration,
    icao24,
    manufacturer,
    model,
    operator,
    category,
    current_status,
    callsign,
    altitude_ft,
    speed_kts,
    latitude,
    longitude,
    location
):

    style = get_event_style(
        event
    )

    aircraft_name = " ".join(
        part
        for part in (
            manufacturer,
            model
        )
        if part
    )

    embed = {
        "title": style["title"],
        "description": (
            f"## {registration}\n"
            f"{aircraft_name or 'Aircraft type unknown'}"
        ),
        "color": style["color"],
        "timestamp": datetime.now(
            timezone.utc
        ).isoformat(),
        "fields": [
            {
                "name": "Flight",
                "value": callsign or "Unknown",
                "inline": True
            },
            {
                "name": "Current Status",
                "value": current_status,
                "inline": True
            },
            {
                "name": "ICAO24",
                "value": f"`{icao24}`",
                "inline": True
            },
            {
                "name": "Operator",
                "value": operator or "Unknown",
                "inline": True
            },
            {
                "name": "Category",
                "value": category or "Unknown",
                "inline": True
            },
            {
                "name": "Event",
                "value": event,
                "inline": True
            },
            {
                "name": "Altitude",
                "value": f"{altitude_ft:,} ft",
                "inline": True
            },
            {
                "name": "Speed",
                "value": f"{speed_kts:,} knots",
                "inline": True
            },
            {
                "name": "Location",
                "value": location,
                "inline": True
            }
        ],
        "footer": {
            "text": "FlightWatch aircraft monitoring"
        }
    }

    map_url = get_map_url(
        latitude,
        longitude
    )

    if map_url:
        embed["fields"].append(
            {
                "name": "Position",
                "value": (
                    f"[{latitude}, {longitude}]"
                    f"({map_url})"
                ),
                "inline": False
            }
        )

    return embed


def send_webhook_embeds(embeds):

    if not embeds:
        return

    maximum_embeds_per_message = 10

    for start in range(
        0,
        len(embeds),
        maximum_embeds_per_message
    ):

        batch = embeds[
            start:start + maximum_embeds_per_message
        ]

        payload = {
            "content": (
                f"✈️ **FlightWatch detected "
                f"{len(batch)} aircraft event"
                f"{'' if len(batch) == 1 else 's'}.**"
            ),
            "embeds": batch,
            "allowed_mentions": {
                "parse": []
            }
        }

        try:
            response = requests.post(
                WEBHOOK,
                json=payload,
                timeout=20
            )

            print(
                "Discord webhook response: "
                f"{response.status_code}"
            )

            if not response.ok:
                print(
                    "Discord webhook error: "
                    f"{response.text[:500]}"
                )

            response.raise_for_status()

        except requests.RequestException as error:
            print(
                f"Discord webhook request failed: {error}"
            )


def main():

    print(
        "Running FlightWatch check..."
    )

    positions = get_aircraft_positions()

    print(
        f"OpenSky returned {len(positions)} aircraft states."
    )

    tracked = get_tracked_aircraft()

    alert_embeds = []

    for aircraft in tracked:

        icao24 = aircraft[0]

        registration = (
            aircraft[1]
            or icao24.upper()
        )

        manufacturer = (
            aircraft[2]
            or ""
        )

        model = (
            aircraft[3]
            or "Unknown"
        )

        operator = (
            aircraft[4]
            or "Unknown"
        )

        category = (
            aircraft[5]
            or "Unknown"
        )

        previous = get_previous_state(
            icao24
        )

        if icao24 not in positions:
            continue

        data = positions[icao24]

        altitude_ft = (
            round(
                data["altitude"] * 3.28084
            )
            if isinstance(
                data["altitude"],
                (int, float)
            )
            else 0
        )

        speed_kts = (
            round(
                data["velocity"] * 1.94384
            )
            if isinstance(
                data["velocity"],
                (int, float)
            )
            else 0
        )

        callsign = (
            data["callsign"]
            or "Unknown"
        )

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

            alert_embeds.append(
                build_alert_embed(
                    event=event,
                    registration=registration,
                    icao24=icao24,
                    manufacturer=manufacturer,
                    model=model,
                    operator=operator,
                    category=category,
                    current_status=current_status,
                    callsign=callsign,
                    altitude_ft=altitude_ft,
                    speed_kts=speed_kts,
                    latitude=latitude,
                    longitude=longitude,
                    location=location
                )
            )

    if alert_embeds:
        print(
            f"Sending {len(alert_embeds)} "
            "aircraft event alert(s)."
        )

        send_webhook_embeds(
            alert_embeds
        )

    else:
        print(
            "No aircraft events detected."
        )


if __name__ == "__main__":
    main()
