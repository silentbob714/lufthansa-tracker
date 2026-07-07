import os
import requests

WEBHOOK = os.environ["DISCORD_WEBHOOK"]

username = os.environ["OPENSKY_USERNAME"]
password = os.environ["OPENSKY_PASSWORD"]

response = requests.get(
    "https://opensky-network.org/api/states/all",
    auth=(username, password),
    timeout=30
)

payload = {
    "content": f"OpenSky Status: {response.status_code}"
}

requests.post(WEBHOOK, json=payload)
