from fastapi import WebSocket
from typing import Dict, Set
import json
import asyncio
from .config import settings

class WebSocketManager:
    def __init__(self):
        self.active_connections: Dict[int, Set[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        async with self._lock:
            if user_id not in self.active_connections:
                self.active_connections[user_id] = set()
            self.active_connections[user_id].add(websocket)

    async def disconnect(self, websocket: WebSocket, user_id: int):
        async with self._lock:
            if user_id in self.active_connections:
                self.active_connections[user_id].discard(websocket)
                if not self.active_connections[user_id]:
                    del self.active_connections[user_id]

    async def broadcast_to_user(self, user_id: int, message: dict):
        if user_id in self.active_connections:
            disconnected = set()
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except:
                    disconnected.add(connection)
            
            # Clean up disconnected sessions
            if disconnected:
                async with self._lock:
                    self.active_connections[user_id] -= disconnected

    async def broadcast_proximity_alert(self, alert: dict, radius_meters: float = 200):
        """Broadcast proximity alert to nearby users"""
        target_location = (alert["latitude"], alert["longitude"])
        
        for user_id, connections in self.active_connections.items():
            # Check if user is within radius
            user_location = await self.get_user_location(user_id)
            if user_location and self.calculate_distance(
                target_location, user_location
            ) <= radius_meters:
                await self.broadcast_to_user(user_id, {
                    "type": "proximity_alert",
                    "data": alert
                })

    def calculate_distance(self, point1: tuple, point2: tuple) -> float:
        """Calculate distance between two points in meters"""
        from geopy.distance import geodesic
        return geodesic(point1, point2).meters

    async def get_user_location(self, user_id: int) -> tuple:
        """Get user's last known location"""
        # TODO: Implement user location tracking
        return None

websocket_manager = WebSocketManager()