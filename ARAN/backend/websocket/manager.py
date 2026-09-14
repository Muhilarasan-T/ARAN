"""
ARAN — WebSocket Connection Manager

Manages all active WebSocket connections and broadcasts real-time events
to the React frontend.
"""
import json
import logging
from typing import Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()
logger = logging.getLogger("aran.websocket")


class WebSocketManager:
    """
    Keeps track of all connected WebSocket clients.
    broadcast() sends a dict as JSON to every connected client.
    """

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"WebSocket connected. Active: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)
        logger.info(f"WebSocket disconnected. Active: {len(self.active_connections)}")

    async def broadcast(self, data: dict):
        """Send JSON message to all connected clients."""
        if not self.active_connections:
            return
        message = json.dumps(data)
        dead = set()
        for ws in self.active_connections:
            try:
                await ws.send_text(message)
            except Exception:
                dead.add(ws)
        for ws in dead:
            self.active_connections.discard(ws)


# Singleton — imported by all services that need to broadcast
ws_manager = WebSocketManager()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    The single WebSocket endpoint for the React frontend.
    The client connects once and receives all real-time events.
    """
    await ws_manager.connect(websocket)
    try:
        # Keep connection alive — client messages are not expected but handled
        while True:
            data = await websocket.receive_text()
            logger.debug(f"WS received: {data}")
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
