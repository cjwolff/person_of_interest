import asyncio
from fastapi import WebSocket
from typing import Dict, Set, List
import json
import logging
from .config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

class WebSocketManager:
    """Manages WebSocket connections and message broadcasting"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self._lock = asyncio.Lock()
        
    async def connect(self, websocket: WebSocket, client_id: str):
        """Connect new client"""
        await websocket.accept()
        async with self._lock:
            self.active_connections[client_id] = websocket
        logger.info(f"Client {client_id} connected")
    
    async def disconnect(self, client_id: str):
        """Disconnect client"""
        async with self._lock:
            if client_id in self.active_connections:
                del self.active_connections[client_id]
                logger.info(f"Client {client_id} disconnected")
    
    async def send_message(self, client_id: str, message: dict):
        """Send message to specific client"""
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_json(message)
                logger.debug(f"Sent message to client {client_id}")
            except Exception as e:
                logger.error(f"Error sending message to client {client_id}: {e}")
                await self.disconnect(client_id)

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        client_id = id(websocket)  # Use websocket id as temporary client id
        if client_id not in self.active_connections:
            self.active_connections[client_id] = []
        self.active_connections[client_id].append(websocket)

    def disconnect(self, websocket: WebSocket):
        client_id = id(websocket)
        if client_id in self.active_connections:
            self.active_connections[client_id].remove(websocket)
            if not self.active_connections[client_id]:
                del self.active_connections[client_id]

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        await websocket.send_json(message)

    async def broadcast(self, message: str):
        for connections in self.active_connections.values():
            for connection in connections:
                await connection.send_text(message)

# Global WebSocket manager instance
ws_manager = WebSocketManager() 