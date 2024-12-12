from fastapi import WebSocket, WebSocketDisconnect
import logging
import json
from typing import Optional
from datetime import datetime
import base64
import numpy as np
import cv2

logger = logging.getLogger(__name__)

class SurveillanceWebSocketHandler:
    def __init__(self, websocket_manager, video_processor, ar_service, behavior_service, geofencing_service):
        self.websocket_manager = websocket_manager
        self.video_processor = video_processor
        self.ar_service = ar_service
        self.behavior_service = behavior_service
        self.geofencing_service = geofencing_service

    async def process_frame(self, data: dict) -> dict:
        try:
            # Process frame data
            frame_data = data.get('frame')
            metadata = data.get('metadata', {})

            # Process the frame through your services
            processed_frame = await self.video_processor.process_frame(frame_data)
            ar_results = await self.ar_service.process_frame(processed_frame)
            behavior_analysis = await self.behavior_service.analyze_behavior(ar_results)
            
            return {
                "type": "frame_processed",
                "ar_data": ar_results,
                "behavior_analysis": behavior_analysis,
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            logger.error(f"Error processing frame: {e}")
            return {
                "type": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    async def handle_connection(self, websocket: WebSocket):
        client_id = websocket.query_params.get("client_id")
        
        try:
            await websocket.accept()
            await self.websocket_manager.connect(websocket, client_id)
            
            while True:
                try:
                    # Receive frame data
                    frame_data = await websocket.receive_json()
                    
                    if frame_data["type"] == "frame":
                        # Extract frame and metadata
                        frame_bytes = base64.b64decode(frame_data["frame_data"])
                        frame = self._bytes_to_frame(frame_bytes)
                        metadata = frame_data.get("metadata", {})
                        
                        # Process frame
                        processed_frame = await self.video_processor.preprocess_frame(frame)
                        
                        # Detect objects and faces
                        objects = await self.object_detector.detect(processed_frame)
                        faces = await self.face_detector.detect_faces(processed_frame)
                        
                        # Update tracking with frame
                        tracked_objects = await self.tracker.update(objects, frame=processed_frame)
                        
                        # Generate AR data
                        ar_data = await self.ar_service.process_frame(
                            frame=processed_frame,
                            faces=faces,
                            tracked_objects=tracked_objects
                        )
                        
                        # Send results
                        await self.websocket_manager.send_personal_message(
                            client_id,
                            {
                                "type": "frame_processed",
                                "ar_data": ar_data,
                                "metadata": metadata,
                                "timestamp": datetime.now().isoformat()
                            }
                        )
                        
                except WebSocketDisconnect:
                    logger.info(f"Client {client_id} disconnected")
                    await self.websocket_manager.disconnect(client_id)
                    break
                except Exception as e:
                    logger.error(f"Error processing frame: {e}")
                    await websocket.send_json({
                        "type": "error",
                        "message": str(e)
                    })
                    
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
            if client_id:
                await self.websocket_manager.disconnect(client_id)

    def _bytes_to_frame(self, frame_bytes: bytes) -> np.ndarray:
        """Convert bytes to OpenCV frame"""
        nparr = np.frombuffer(frame_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if frame is None:
            raise ValueError("Failed to decode image")
        return frame