from ultralytics import YOLO
import mediapipe as mp
import numpy as np
import cv2
from datetime import datetime
from typing import List
from services.face_detection_service import FaceDetectionService
from services.object_detection_service import ObjectDetectionService
from services.tracking_service import TrackingService
import uuid

class MLEngine:
    def __init__(self):
        self.face_detector = FaceDetectionService()
        self.object_detector = ObjectDetectionService()
        self.tracker = TrackingService()

    async def process_frame(self, frame):
        try:
            # Run detections in parallel
            face_results = await self.face_detector.detect_faces(frame)
            object_results = await self.object_detector.detect(frame)
            
            # Update tracks with frame
            tracked_detections = await self.tracker.update(object_results, frame=frame)
            
            # Process detections with explicit type handling
            processed_detections = []
            for detection in tracked_detections:
                try:
                    bbox = detection.get('bbox', [0.0, 0.0, 0.0, 0.0])
                    if isinstance(bbox, (np.ndarray, list, tuple)):
                        bbox = [float(x) for x in bbox]
                    else:
                        bbox = [0.0, 0.0, 0.0, 0.0]
                    
                    processed_detection = {
                        'bbox': bbox,
                        'confidence': float(detection.get('confidence', 0.0)),
                        'class_name': str(detection.get('class_name', 'unknown')),
                        'track_id': str(detection.get('track_id', uuid.uuid4())),
                        'metadata': detection.get('metadata', {})
                    }
                    processed_detections.append(processed_detection)
                except Exception as e:
                    logger.error(f"Error processing detection: {e}")
                    continue
            
            # Convert numpy arrays and ensure no null values
            def convert_numpy(obj):
                if obj is None:
                    return {}
                if isinstance(obj, np.ndarray):
                    return obj.tolist()
                if isinstance(obj, (np.int_, np.float_)):
                    return float(obj)
                if isinstance(obj, dict):
                    return {str(k): convert_numpy(v) for k, v in obj.items()}
                if isinstance(obj, (list, tuple)):
                    return [convert_numpy(x) for x in obj]
                return str(obj)
            
            return {
                "timestamp": datetime.now().isoformat(),
                "detections": [convert_numpy(d) for d in processed_detections],
                "faces": [convert_numpy(f) for f in (face_results or [])],
                "objects": [convert_numpy(o) for o in (object_results or [])],
                "tracks": [convert_numpy(d) for d in processed_detections],
                "position": [0.0, 0.0, 0.0],
                "metadata": {}
            }
        
        except Exception as e:
            logger.error(f"Error in process_frame: {e}")
            return {
                "timestamp": datetime.now().isoformat(),
                "detections": [],
                "faces": [],
                "objects": [],
                "tracks": [],
                "position": [0.0, 0.0, 0.0],
                "metadata": {}
            }
