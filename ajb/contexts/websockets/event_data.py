import asyncio

class EventData:
    def __init__(self):
        self.event = asyncio.Event()
        self.data = None
        self.lock = asyncio.Lock()

    async def wait_for_event(self):
        await self.event.wait()
        async with self.lock:
            return self.data

    async def trigger_event(self, data):
        async with self.lock:
            self.data = data
            self.event.set()
            self.event.clear()  # Reset the event for future use
