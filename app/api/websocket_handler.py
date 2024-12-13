from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Optional
import base64
import cv2
import numpy as np
import logging
import asyncio
from datetime import datetime
from app.core.websocket import WebSocketManager
from app.services.video_processor import VideoProcessor
from app.services.object_detection_service import ObjectDetectionService
from app.services.face_detection_service import FaceDetectionService
from app.services.ar_service import ARService
from app.services.tracking_service import TrackingService
from app.core.config import get_settings
from app.services.behavior_analysis_service import BehaviorAnalysisService
from app.services.geofencing_service import GeofencingService

settings = get_settings()
logger = logging.getLogger(__name__)

class SurveillanceWebSocketHandler:
    def __init__(
        self,
        websocket_manager: WebSocketManager,
        video_processor: VideoProcessor,
        ar_service: ARService,
        behavior_service: BehaviorAnalysisService,
        geofencing_service: GeofencingService
    ):
        """Initialize WebSocket handler with required services"""
        self.websocket_manager = websocket_manager
        self.video_processor = video_processor
        self.ar_service = ar_service
        self.behavior_service = behavior_service
        self.geofencing_service = geofencing_service
        self._active_connections = {}
        self._connection_timeouts = {}
        self._max_reconnect_attempts = 3
        self._reconnect_delay = 5
        self._processing_tasks = {}
        
        logger.info("WebSocket handler initialized with all services")

    async def handle_connection(self, websocket: WebSocket):
        """Handle new WebSocket connection"""
        client_id = websocket.query_params.get("client_id")
        if not client_id:
            logger.warning("Connection attempt without client_id")
            await websocket.close(code=4000)
            return

        try:
            # Check for existing connection
            if client_id in self._active_connections:
                await self._handle_reconnection(websocket, client_id)
                return

            # Initialize connection
            await self._initialize_connection(websocket, client_id)
            
            # Handle messages
            while True:
                try:
                    message = await asyncio.wait_for(
                        websocket.receive_json(),
                        timeout=self._connection_timeouts.get(client_id, 30)
                    )
                    await self._handle_client_message(client_id, message)
                except asyncio.TimeoutError:
                    await self._handle_timeout(client_id)
                    break
                except WebSocketDisconnect:
                    logger.info(f"Client {client_id} disconnected normally")
                    break
                except Exception as e:
                    logger.error(f"Error handling message from {client_id}: {e}")
                    break

        except Exception as e:
            logger.error(f"Connection error for client {client_id}: {e}")
        finally:
            await self._cleanup_client(client_id)

    async def _initialize_connection(self, websocket: WebSocket, client_id: str):
        """Initialize new client connection"""
        await websocket.accept()
        self._active_connections[client_id] = {
            "websocket": websocket,
            "connected_at": datetime.now(),
            "last_activity": datetime.now(),
            "reconnect_attempts": 0
        }
        logger.info(f"Client {client_id} connected successfully")

    async def _handle_reconnection(self, websocket: WebSocket, client_id: str):
        """Handle client reconnection attempt"""
        conn_info = self._active_connections[client_id]
        if conn_info["reconnect_attempts"] >= self._max_reconnect_attempts:
            logger.warning(f"Too many reconnection attempts for {client_id}")
            await websocket.close(code=4001)
            return

        conn_info["reconnect_attempts"] += 1
        await asyncio.sleep(self._reconnect_delay)
        await self._initialize_connection(websocket, client_id)

    async def _handle_timeout(self, client_id: str):
        """Handle connection timeout"""
        logger.warning(f"Connection timeout for client {client_id}")
        if client_id in self._active_connections:
            websocket = self._active_connections[client_id]["websocket"]
            await websocket.close(code=4002)

    async def _handle_client_message(self, client_id: str, message: Dict):
        """Handle incoming messages from client"""
        if message["type"] == "frame":
            await self._process_frame(client_id, message)
        elif message["type"] == "metadata":
            await self._process_metadata(client_id, message)
        else:
            logger.warning(f"Unknown message type from client {client_id}")

    async def _process_frame(self, client_id: str, frame_data: Dict):
        """Process incoming frame with error handling"""
        try:
            # Extract and decode frame
            frame_bytes = base64.b64decode(frame_data["frame_data"])
            frame = self.video_processor.bytes_to_frame(frame_bytes)
            
            # Create processing task
            task = asyncio.create_task(
                self._process_frame_data(client_id, frame, frame_data.get("metadata", {}))
            )
            self._processing_tasks[client_id] = task
            
            # Wait for processing with timeout
            try:
                await asyncio.wait_for(task, timeout=5.0)
            except asyncio.TimeoutError:
                logger.error(f"Frame processing timeout for client {client_id}")
                task.cancel()
                
        except Exception as e:
            logger.error(f"Error processing frame for client {client_id}: {e}")

    async def _process_frame_data(self, client_id: str, frame: np.ndarray, metadata: Dict):
        """Process frame data and send results to client"""
        try:
            # Preprocess frame
            processed_frame = await self.video_processor.preprocess_frame(frame)
            
            # Run detections
            objects = await self.object_detector.detect(processed_frame)
            faces = await self.face_detector.detect_faces(processed_frame)
            
            # Update tracking
            tracked_objects = await self.tracker.update(objects, frame=processed_frame)
            
            # Generate AR data
            ar_data = await self.ar_service.process_frame(
                frame=processed_frame,
                faces=faces,
                tracked_objects=tracked_objects
            )
            
            # Send results
            await self.websocket_manager.send_message(
                client_id,
                {
                    "type": "frame_processed",
                    "ar_data": ar_data,
                    "metadata": metadata,
                    "timestamp": datetime.now().isoformat()
                }
            )
            
        except Exception as e:
            logger.error(f"Error in frame processing pipeline: {e}")
            raise

    async def _cleanup_client(self, client_id: str):
        """Cleanup client resources"""
        try:
            # Cancel any pending processing tasks
            if client_id in self._processing_tasks:
                self._processing_tasks[client_id].cancel()
                del self._processing_tasks[client_id]
            
            # Disconnect from WebSocket manager
            await self.websocket_manager.disconnect(client_id)
            
        except Exception as e:
            logger.error(f"Error cleaning up client {client_id}: {e}")

    async def cleanup(self):
        """Cleanup handler resources"""
        try:
            await self.object_detector.cleanup()
            await self.face_detector.cleanup()
            
            # Cancel all processing tasks
            for task in self._processing_tasks.values():
                task.cancel()
            
            # Wait for tasks to complete
            if self._processing_tasks:
                await asyncio.gather(*self._processing_tasks.values(), return_exceptions=True)
                
        except Exception as e:
            logger.error(f"Error in handler cleanup: {e}")