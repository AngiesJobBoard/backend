import asyncio
from ajb.contexts.websockets.event_data import EventData
from ajb.contexts.websockets.singleton import Singleton


class WebSocketEventHandler(Singleton):
    def _initialize(self):
        self.event_data = EventData()

    async def wait_for_event(self):
        print("Waiting for event to be set...")
        data = await self.event_data.wait_for_event()
        print("Event has been set with data:", data)
        return data

    async def trigger_event(self, data):
        print("Triggering the event now with data:", data)
        await self.event_data.trigger_event(data)

    def fire_update_event(self, updated_object):
        """Fires off an update event for this object"""
        try:
            # Try to get the current running event loop
            loop = asyncio.get_running_loop()
            loop.create_task(self.trigger_event(updated_object))
        except RuntimeError:
            # If no event loop is running, use asyncio.run
            asyncio.run(self.trigger_event(updated_object))