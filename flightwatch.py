import time
import subprocess
from datetime import datetime


INTERVAL = 60


def run_tracker():

    print(
        f"[{datetime.now()}] Running FlightWatch check..."
    )

    result = subprocess.run(
        ["python", "tracker.py"],
        capture_output=True,
        text=True
    )

    print(result.stdout)

    if result.stderr:
        print("ERROR:")
        print(result.stderr)


while True:

    try:

        run_tracker()

    except Exception as e:

        print(
            f"FlightWatch error: {e}"
        )

    print(
        f"Sleeping {INTERVAL} seconds..."
    )

    time.sleep(INTERVAL)
