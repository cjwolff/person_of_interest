from ultralytics import YOLO
import numpy as np
import asyncio
from typing import List, Dict
from ..core.config import get_settings
from ..models.detection import Detection
import cv2

settings = get_settings()

class ObjectDetectionService:
    def __init__(self):
        self.model = YOLO('yolov8n.pt')  # Load the smallest YOLOv8 model
        self.processing_lock = asyncio.Lock()
        self.confidence_threshold = 0.5

    async def detect(self, frame: np.ndarray) -> List[Dict]:
        """Detect objects in frame and return their locations"""
        async with self.processing_lock:
            # Run YOLOv8 inference
            results = self.model(frame)
            detections = []
            
            # Process results
            for result in results:
                boxes = result.boxes
                for box in boxes:
                    if box.conf.item() > self.confidence_threshold:
                        x1, y1, x2, y2 = [float(x) for x in box.xyxy[0].tolist()]
                        detection = {
                            "bbox": [x1, y1, x2, y2],
                            "confidence": float(box.conf.item()),
                            "class_name": str(result.names[int(box.cls.item())]),
                            "class_id": int(box.cls.item())
                        }
                        detections.append(detection)
            
            return detections 