import os
import requests
from datetime import datetime, timezone

WEBHOOK = os.environ["DISCORD_WEBHOOK"]

payload = {
    "content": f"✈ Tracker check: {datetime.now(timezone.utc)}"
}

requests.post(WEBHOOK, json=payload)
