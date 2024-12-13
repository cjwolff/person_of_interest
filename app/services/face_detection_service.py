import mediapipe as mp
import numpy as np
import logging
import asyncio
from typing import List, Dict, Optional
from app.core.config import get_settings
from app.core.metrics import DETECTION_COUNT, ERROR_COUNT
from cachetools import TTLCache
import hashlib
import cv2

settings = get_settings()
logger = logging.getLogger(__name__)

class FaceDetectionService:
    def __init__(self):
        try:
            # Initialize MediaPipe face detection
            self.mp_face_detection = mp.solutions.face_detection
            self.face_detection = self.mp_face_detection.FaceDetection(
                model_selection=1,  # 0=short range, 1=full range
                min_detection_confidence=settings.MIN_DETECTION_CONFIDENCE
            )
            self.processing_lock = asyncio.Lock()
            self.result_cache = TTLCache(maxsize=100, ttl=1.0)
            self._frame_queue = asyncio.Queue(maxsize=settings.MAX_FRAME_QUEUE_SIZE)
            self._processing_task = asyncio.create_task(self._process_queue())
            
            logger.info("Face detection service initialized")
        except Exception as e:
            ERROR_COUNT.labels(service="face_detection", type="init").inc()
            logger.error(f"Failed to initialize face detection: {e}")
            raise

    async def detect_faces(self, frame: np.ndarray) -> List[Dict]:
        """Detect faces in frame with queuing and caching"""
        try:
            # Check cache first
            frame_hash = self._compute_frame_hash(frame)
            if cached := self.result_cache.get(frame_hash):
                return cached

            # Add to processing queue
            future = asyncio.Future()
            await self._frame_queue.put((frame, frame_hash, future))
            
            # Wait for result with timeout
            try:
                result = await asyncio.wait_for(future, timeout=5.0)
                return result
            except asyncio.TimeoutError:
                ERROR_COUNT.labels(service="face_detection", type="timeout").inc()
                logger.error("Face detection timeout")
                return []

        except Exception as e:
            ERROR_COUNT.labels(service="face_detection", type="detection").inc()
            logger.error(f"Error in face detection: {e}")
            return []

    async def _process_queue(self):
        """Process queued frames"""
        while True:
            try:
                frame, frame_hash, future = await self._frame_queue.get()
                
                async with self.processing_lock:
                    result = await self._process_frame(frame)
                
                self.result_cache[frame_hash] = result
                if not future.done():
                    future.set_result(result)
                
                self._frame_queue.task_done()

            except Exception as e:
                ERROR_COUNT.labels(service="face_detection", type="queue_processing").inc()
                logger.error(f"Error processing face detection queue: {e}")
                await asyncio.sleep(1)

    async def _process_frame(self, frame: np.ndarray) -> List[Dict]:
        """Process single frame with MediaPipe"""
        try:
            # Convert to RGB for MediaPipe
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.face_detection.process(rgb_frame)
            
            faces = []
            if results.detections:
                height, width = frame.shape[:2]
                
                for detection in results.detections:
                    bbox = detection.location_data.relative_bounding_box
                    
                    # Convert relative coordinates to absolute
                    x1 = max(0, bbox.xmin * width)
                    y1 = max(0, bbox.ymin * height)
                    x2 = min(width, (bbox.xmin + bbox.width) * width)
                    y2 = min(height, (bbox.ymin + bbox.height) * height)

                    face_data = {
                        "bbox": [x1, y1, x2, y2],
                        "confidence": float(detection.score[0]),
                        "landmarks": [
                            {
                                "x": min(width, max(0, point.x * width)),
                                "y": min(height, max(0, point.y * height))
                            }
                            for point in detection.location_data.relative_keypoints
                        ]
                    }
                    faces.append(face_data)
                    DETECTION_COUNT.labels(type="face").inc()

            return faces

        except Exception as e:
            ERROR_COUNT.labels(service="face_detection", type="processing").inc()
            logger.error(f"Error processing frame: {e}")
            return []

    def _compute_frame_hash(self, frame: np.ndarray) -> str:
        """Compute quick frame hash for caching"""
        try:
            small = cv2.resize(frame, (32, 32))
            return hashlib.md5(small.tobytes()).hexdigest()
        except Exception as e:
            logger.error(f"Error computing frame hash: {e}")
            return ""

    async def cleanup(self):
        """Cleanup service resources"""
        try:
            self._processing_task.cancel()
            try:
                await self._processing_task
            except asyncio.CancelledError:
                pass
            
            self.face_detection.close()
            logger.info("Face detection service cleaned up")
        except Exception as e:
            logger.error(f"Error cleaning up face detection: {e}") 