from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect
from fastapi.websockets import WebSocketState

from ajb.contexts.websockets.event_handler import WebSocketEventHandler


router = APIRouter(tags=["Websockets"], prefix="/websockets")


@router.websocket("/{event_type}")
async def websocket_endpoint(websocket: WebSocket, event_type_filter: str | None = None):
    # Accept WebSocket connection
    await websocket.accept()

    # Prepare event handling
    handler = WebSocketEventHandler()

    # Connection handler
    try:
        while True:
            # Wait for event
            event_data = await handler.wait_for_event()
            event_class_type = type(event_data).__name__

            # Check event filters
            if event_type_filter is None or event_type_filter == event_class_type:
                # Respond with result
                event_data_json = event_data.model_dump(mode="json"),
                print(f"Sent message: {event_data}")
                await websocket.send_text(event_data_json)

    except WebSocketDisconnect:
        print("WebSocket disconnected")
        pass
    except Exception as e:
        print(f"Error occurred: {e}")
    finally:
        # Unregister the connection
        if websocket.client_state is not WebSocketState.DISCONNECTED:
            await websocket.close()
        print("Connection closed")