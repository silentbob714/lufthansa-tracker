import os
import requests

username = os.environ["OPENSKY_USERNAME"]
password = os.environ["OPENSKY_PASSWORD"]

url = "https://opensky-network.org/api/states/all"

response = requests.get(
    url,
    auth=(username, password),
    timeout=30
)

print(response.status_code)
