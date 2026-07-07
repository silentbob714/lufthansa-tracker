import os
import requests

WEBHOOK = os.environ["DISCORD_WEBHOOK"]

username = os.environ["OPENSKY_USERNAME"]
password = os.environ["OPENSKY_PASSWORD"]

response = requests.get(
    "https://opensky-network.org/api/states/all",
    auth=(username, password),
    timeout=120
)

data = response.json()

messages = []

for aircraft in data.get("states", []):

    callsign = aircraft[1]

    if callsign and callsign.startswith("DLH"):

        icao24 = aircraft[0]

        lookup = requests.get(
            f"https://opensky-network.org/api/metadata/aircraft/icao24/{icao24}",
            auth=(username, password),
            timeout=30
        )

        if lookup.status_code == 200:

            info = lookup.json()

            registration = info.get("registration")

            messages.append(
                f"{callsign.strip()} | {registration} | {icao24}"
            )

message = "✈ Lufthansa Aircraft\n\n"

if messages:
    message += "\n".join(messages[:20])
else:
    message += "None detected."

requests.post(
    WEBHOOK,
    json={"content": message}
)
