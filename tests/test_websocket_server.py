import asyncio
import json
import base64
import cv2
import numpy as np
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from app.core.websocket import WebSocketManager
import logging
from typing import Dict

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"Client {client_id} connected")

    async def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info(f"Client {client_id} disconnected")

    async def send_message(self, client_id: str, message: dict):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_json(message)
            logger.debug(f"Sent message to client {client_id}: {message}")

manager = ConnectionManager()

def process_frame(frame_data: np.ndarray) -> dict:
    """Process the frame and return detection results."""
    try:
        # Example processing:
        # 1. Convert to grayscale
        gray = cv2.cvtColor(frame_data, cv2.COLOR_BGR2GRAY)
        
        # 2. Simple face detection
        face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)
        
        # 3. Return results
        detections = [
            {
                "type": "face",
                "confidence": 0.95,
                "bbox": [int(x), int(y), int(w), int(h)]
            }
            for (x, y, w, h) in faces
        ]
        
        return {
            "detections": detections,
            "ar_data": {
                "anchors": [
                    {"id": "test", "position": [0, 0, 0]}
                ]
            }
        }
    except Exception as e:
        logger.error(f"Error processing frame: {e}")
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="debug",
        access_log=True
    )