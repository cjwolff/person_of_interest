from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from ..core.websocket import WebSocketManager
from ..core.auth import WebSocketAuthManager
from .websocket_handler import SurveillanceWebSocketHandler
import logging
import json

router = APIRouter()
logger = logging.getLogger(__name__)

@router.websocket("/surveillance")
async def websocket_endpoint(websocket: WebSocket):
    try:
        # Get the global handler instance from main.py
        from ..main import ws_handler
        await ws_handler.handle_connection(websocket)
    except Exception as e:
        logger.error(f"Error in websocket endpoint: {e}")
        await websocket.close(code=1011)