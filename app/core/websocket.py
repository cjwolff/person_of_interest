from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Set, Optional
import logging
import asyncio
from datetime import datetime, timedelta
from app.core.metrics import WEBSOCKET_CONNECTIONS, ERROR_COUNT
from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

class WebSocketManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.client_heartbeats: Dict[str, datetime] = {}
        self.client_message_queues: Dict[str, asyncio.Queue] = {}
        self.heartbeat_interval = timedelta(seconds=30)
        self._cleanup_task = asyncio.create_task(self._periodic_cleanup())

    async def connect(self, websocket: WebSocket, client_id: str):
        """Handle new client connection"""
        try:
            await websocket.accept()
            self.active_connections[client_id] = websocket
            self.client_heartbeats[client_id] = datetime.now()
            self.client_message_queues[client_id] = asyncio.Queue(maxsize=100)
            WEBSOCKET_CONNECTIONS.inc()
            logger.info(f"Client {client_id} connected")
        except Exception as e:
            ERROR_COUNT.labels(service="websocket", type="connection").inc()
            logger.error(f"Error connecting client {client_id}: {e}")
            raise

    async def disconnect(self, client_id: str):
        """Handle client disconnection"""
        try:
            if client_id in self.active_connections:
                await self.active_connections[client_id].close()
                del self.active_connections[client_id]
                del self.client_heartbeats[client_id]
                del self.client_message_queues[client_id]
                WEBSOCKET_CONNECTIONS.dec()
                logger.info(f"Client {client_id} disconnected")
        except Exception as e:
            ERROR_COUNT.labels(service="websocket", type="disconnection").inc()
            logger.error(f"Error disconnecting client {client_id}: {e}")

    async def send_message(self, client_id: str, message: dict):
        """Send message to client with queuing"""
        try:
            if client_id not in self.active_connections:
                return

            queue = self.client_message_queues[client_id]
            try:
                await asyncio.wait_for(
                    queue.put(message),
                    timeout=1.0
                )
                await self._process_message_queue(client_id)
            except asyncio.TimeoutError:
                logger.warning(f"Message queue full for client {client_id}")
                ERROR_COUNT.labels(service="websocket", type="queue_full").inc()

        except Exception as e:
            ERROR_COUNT.labels(service="websocket", type="send_message").inc()
            logger.error(f"Error sending message to client {client_id}: {e}")
            await self.disconnect(client_id)

    async def _process_message_queue(self, client_id: str):
        """Process queued messages for client"""
        try:
            queue = self.client_message_queues[client_id]
            websocket = self.active_connections[client_id]

            while not queue.empty():
                message = await queue.get()
                await websocket.send_json(message)
                queue.task_done()

        except Exception as e:
            logger.error(f"Error processing message queue for {client_id}: {e}")
            await self.disconnect(client_id)

    async def _periodic_cleanup(self):
        """Cleanup stale connections"""
        while True:
            try:
                await asyncio.sleep(60)  # Run every minute
                current_time = datetime.now()
                stale_clients = [
                    client_id for client_id, last_heartbeat 
                    in self.client_heartbeats.items()
                    if current_time - last_heartbeat > self.heartbeat_interval
                ]
                
                for client_id in stale_clients:
                    logger.warning(f"Removing stale connection for client {client_id}")
                    await self.disconnect(client_id)

            except Exception as e:
                logger.error(f"Error in connection cleanup: {e}")

    async def broadcast(self, message: dict, exclude: Optional[Set[str]] = None):
        """Broadcast message to all connected clients"""
        exclude = exclude or set()
        tasks = []
        
        for client_id in self.active_connections:
            if client_id not in exclude:
                tasks.append(self.send_message(client_id, message))
                
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

# Global WebSocket manager instance
ws_manager = WebSocketManager() 