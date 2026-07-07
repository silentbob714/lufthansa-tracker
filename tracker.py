import os
import requests

WEBHOOK = os.environ["DISCORD_WEBHOOK"]

payload = {
    "content": "✈ Lufthansa Tracker test successful."
}

requests.post(WEBHOOK, json=payload)
