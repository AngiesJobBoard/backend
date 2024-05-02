import os
import asyncio
import requests


async def status():
    heartbeat_url = os.getenv("HEARTBEAL_URL")
    if not heartbeat_url:
        return
    while True:
        # Call out to a heartbeat URL to let them know I'm still cookin
        requests.head(heartbeat_url, timeout=5)

        # Wait for 30 seconds before running the status report again
        await asyncio.sleep(30)
