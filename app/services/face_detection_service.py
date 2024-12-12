import mediapipe as mp
import numpy as np
import asyncio
from typing import List, Dict
import cv2

class FaceDetectionService:
    def __init__(self):
        self.face_detection = mp.solutions.face_detection.FaceDetection(
            model_selection=1,  # 0 for close-range, 1 for long-range
            min_detection_confidence=0.5
        )
        self.processing_lock = asyncio.Lock()

    async def detect_faces(self, frame: np.ndarray) -> List[Dict]:
        """Detect faces in frame and return their locations and landmarks"""
        async with self.processing_lock:
            results = self.face_detection.process(frame)
            faces = []

            if results.detections:
                height, width = frame.shape[:2]
                for detection in results.detections:
                    bbox = detection.location_data.relative_bounding_box
                    
                    # Convert relative coordinates to absolute and match YOLO format
                    x1 = bbox.xmin * width
                    y1 = bbox.ymin * height
                    x2 = (bbox.xmin + bbox.width) * width
                    y2 = (bbox.ymin + bbox.height) * height

                    face_data = {
                        "bbox": [x1, y1, x2, y2],
                        "confidence": detection.score[0],
                        "class_name": "face",
                        "landmarks": [
                            {"x": point.x * width, "y": point.y * height}
                            for point in detection.location_data.relative_keypoints
                        ]
                    }
                    faces.append(face_data)

            return faces

    def __del__(self):
        self.face_detection.close() 