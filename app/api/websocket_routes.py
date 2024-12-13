from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.core.websocket import WebSocketManager
from app.services.video_processor import VideoProcessor
from .websocket_handler import SurveillanceWebSocketHandler
import logging
import json

router = APIRouter()
logger = logging.getLogger(__name__)

@router.websocket("/surveillance")
async def websocket_endpoint(websocket: WebSocket):
    try:
        from ..main import ws_handler  # Circular import risk
        await ws_handler.handle_connection(websocket)
    except Exception as e:
        logger.error(f"Error in websocket endpoint: {e}")
        await websocket.close(code=1011)