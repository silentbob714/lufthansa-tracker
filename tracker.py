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

lufthansa = []

for aircraft in data.get("states", []):
    callsign = aircraft[1]

    if callsign and callsign.strip().startswith("DLH"):
        lufthansa.append(
            f"{callsign.strip()} | ICAO24: {aircraft[0]}"
        )

if lufthansa:
    message = "✈ Lufthansa detected:\n\n"
    message += "\n".join(lufthansa[:20])
else:
    message = "No Lufthansa aircraft detected right now."

requests.post(
    WEBHOOK,
    json={"content": message}
)
