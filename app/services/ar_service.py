from typing import List, Dict
import numpy as np
import asyncio
import cv2
import logging
from datetime import datetime
from .object_detection_service import ObjectDetectionService
from .face_detection_service import FaceDetectionService
from fastapi import HTTPException

logger = logging.getLogger(__name__)

class ARService:
    def __init__(self, object_detector: ObjectDetectionService, face_detector: FaceDetectionService):
        self.object_detector = object_detector
        self.face_detector = face_detector
        
    async def process_frame(self, frame: np.ndarray, faces: List[Dict], tracked_objects: List[Dict]) -> Dict:
        """Generate AR data for visualization"""
        try:
            if frame is None:
                raise ValueError("Frame cannot be None")
                
            def convert_numpy_types(obj):
                if isinstance(obj, (np.int_, np.intc, np.intp, np.int8, np.int16, 
                                  np.int32, np.int64, np.uint8, np.uint16, np.uint32, 
                                  np.uint64)):
                    return int(obj)
                if isinstance(obj, (np.float_, np.float16, np.float32, np.float64)):
                    return float(obj)
                if isinstance(obj, np.ndarray):
                    return convert_numpy_types(obj.tolist())
                if isinstance(obj, dict):
                    return {k: convert_numpy_types(v) for k, v in obj.items()}
                if isinstance(obj, (list, tuple)):
                    return [convert_numpy_types(i) for i in obj]
                if obj is None:
                    return []  # Convert None to empty list for arrays
                return obj
                
            processed_faces = convert_numpy_types(faces or [])
            processed_objects = convert_numpy_types(tracked_objects or [])
            
            return {
                "detections": processed_objects,  # Add detections field
                "overlays": [],
                "anchors": [],
                "labels": [],
                "objects": processed_objects,
                "faces": processed_faces,
                "tracks": processed_objects,  # Add tracks field
                "position": [0.0, 0.0, 0.0],  # Add default position
                "timestamp": datetime.now().isoformat()  # Add timestamp
            }
            
        except Exception as e:
            logger.error(f"Error in AR processing: {e}")
            raise