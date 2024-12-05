from fastapi import WebSocket
import numpy as np
import cv2
import base64
from ultralytics import YOLO
import dlib
from typing import List, Dict
import asyncio
import time
from ..models.detection import DetectionResult
from ..core.config import settings

class VideoProcessingService:
    def __init__(self):
        # Initialize models
        self.yolo_model = YOLO('yolov8n.pt')
        self.face_detector = dlib.get_frontal_face_detector()
        self.shape_predictor = dlib.shape_predictor('shape_predictor_68_face_landmarks.dat')
        self.face_recognition_model = dlib.face_recognition_model_v1('dlib_face_recognition_resnet_model_v1.dat')
        
        # Processing queues
        self.processing_queue = asyncio.Queue()
        self.result_queues: Dict[str, asyncio.Queue] = {}
        
        # Performance settings
        self.frame_interval = 1.0 / settings.MAX_FPS  # e.g., 1/30 for 30 FPS
        self.last_processed: Dict[str, float] = {}
        self.compression_quality = 80  # JPEG compression quality (0-100)
        self.max_image_size = 640  # Maximum dimension for processed images
        
    async def process_frame(self, frame_data: str, client_id: str) -> List[DetectionResult]:
        # Check frame rate limiting
        current_time = time.time()
        if client_id in self.last_processed:
            time_diff = current_time - self.last_processed[client_id]
            if time_diff < self.frame_interval:
                return []
        self.last_processed[client_id] = current_time

        # Decode and preprocess frame
        img_bytes = base64.b64decode(frame_data)
        nparr = np.frombuffer(img_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Resize if needed
        height, width = frame.shape[:2]
        if max(height, width) > self.max_image_size:
            scale = self.max_image_size / max(height, width)
            frame = cv2.resize(frame, None, fx=scale, fy=scale)
        
        # Run YOLO detection with hardware acceleration if available
        yolo_results = self.yolo_model(frame)
        
        # Run face detection
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_detector(gray)
        
        detections = []
        
        # Process YOLO results
        for result in yolo_results[0].boxes.data:
            x1, y1, x2, y2, conf, cls = result
            if float(conf) < settings.DETECTION_CONFIDENCE_THRESHOLD:
                continue
            detections.append(DetectionResult(
                label=self.yolo_model.names[int(cls)],
                confidence=float(conf),
                bbox=[float(x1), float(y1), float(x2), float(y2)]
            ))
        
        # Process face detections
        for face in faces:
            shape = self.shape_predictor(gray, face)
            face_descriptor = self.face_recognition_model.compute_face_descriptor(frame, shape)
            
            detections.append(DetectionResult(
                label="face",
                confidence=1.0,
                bbox=[float(face.left()), float(face.top()),
                      float(face.right()), float(face.bottom())],
                landmarks=[(shape.part(i).x, shape.part(i).y) for i in range(68)]
            ))
        
        return detections

    async def start_processing_worker(self):
        while True:
            frame_data, client_id = await self.processing_queue.get()
            try:
                results = await self.process_frame(frame_data, client_id)
                if results and client_id in self.result_queues:
                    await self.result_queues[client_id].put(results)
            except Exception as e:
                print(f"Error processing frame: {e}")
            finally:
                self.processing_queue.task_done() 