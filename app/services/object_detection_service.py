from typing import List, Dict, Optional
import numpy as np
import logging
import asyncio
from ultralytics import YOLO
import torch
from app.core.config import get_settings
from app.core.metrics import DETECTION_COUNT, ERROR_COUNT
from cachetools import TTLCache
import hashlib

settings = get_settings()
logger = logging.getLogger(__name__)

class ObjectDetectionService:
    def __init__(self):
        try:
            # Initialize YOLO model with CUDA if available
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            self.model = YOLO(settings.YOLO_MODEL_PATH).to(self.device)
            self.confidence_threshold = settings.MIN_DETECTION_CONFIDENCE
            self.processing_lock = asyncio.Lock()
            self.result_cache = TTLCache(maxsize=100, ttl=1.0)  # 1 second cache
            self._batch_queue = asyncio.Queue(maxsize=settings.MAX_FRAME_QUEUE_SIZE)
            self._processing_task = asyncio.create_task(self._process_batch())
            
            logger.info(f"Object detection initialized on {self.device}")
        except Exception as e:
            ERROR_COUNT.labels(service="object_detection", type="init").inc()
            logger.error(f"Failed to initialize object detection: {e}")
            raise

    async def detect(self, frame: np.ndarray) -> List[Dict]:
        """Detect objects in frame with batching and caching"""
        try:
            # Check cache first
            frame_hash = self._compute_frame_hash(frame)
            if cached := self.result_cache.get(frame_hash):
                return cached

            # Add to batch queue
            future = asyncio.Future()
            await self._batch_queue.put((frame, frame_hash, future))
            
            # Wait for result with timeout
            try:
                result = await asyncio.wait_for(future, timeout=5.0)
                return result
            except asyncio.TimeoutError:
                ERROR_COUNT.labels(service="object_detection", type="timeout").inc()
                logger.error("Detection timeout")
                return []

        except Exception as e:
            ERROR_COUNT.labels(service="object_detection", type="detection").inc()
            logger.error(f"Error in object detection: {e}")
            return []

    async def _process_batch(self):
        """Process batched frames"""
        while True:
            try:
                batch = []
                futures = []
                frame_hashes = []

                # Collect batch
                while len(batch) < 4:  # Max batch size
                    try:
                        frame, frame_hash, future = await asyncio.wait_for(
                            self._batch_queue.get(),
                            timeout=0.1
                        )
                        batch.append(frame)
                        frame_hashes.append(frame_hash)
                        futures.append(future)
                    except asyncio.TimeoutError:
                        break

                if not batch:
                    await asyncio.sleep(0.01)
                    continue

                # Process batch
                async with self.processing_lock:
                    results = await self._detect_batch(batch)

                # Set results
                for i, (result, future, frame_hash) in enumerate(zip(results, futures, frame_hashes)):
                    self.result_cache[frame_hash] = result
                    if not future.done():
                        future.set_result(result)

            except Exception as e:
                ERROR_COUNT.labels(service="object_detection", type="batch_processing").inc()
                logger.error(f"Error processing detection batch: {e}")
                await asyncio.sleep(1)

    async def _detect_batch(self, frames: List[np.ndarray]) -> List[List[Dict]]:
        """Run model inference on batch"""
        try:
            results = self.model(frames, verbose=False)
            processed_results = []

            for result in results:
                detections = []
                boxes = result.boxes
                for box in boxes:
                    if box.conf.item() > self.confidence_threshold:
                        detection = {
                            "bbox": [float(x) for x in box.xyxy[0].tolist()],
                            "confidence": float(box.conf.item()),
                            "class_name": str(result.names[int(box.cls.item())]),
                            "class_id": int(box.cls.item())
                        }
                        detections.append(detection)
                        DETECTION_COUNT.labels(type=detection["class_name"]).inc()
                processed_results.append(detections)

            return processed_results

        except Exception as e:
            ERROR_COUNT.labels(service="object_detection", type="inference").inc()
            logger.error(f"Error in model inference: {e}")
            return [[] for _ in frames]

    def _compute_frame_hash(self, frame: np.ndarray) -> str:
        """Compute quick frame hash for caching"""
        try:
            # Downsample frame for faster hashing
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
            
            # Clear CUDA cache if using GPU
            if self.device == "cuda":
                torch.cuda.empty_cache()
                
            logger.info("Object detection service cleaned up")
        except Exception as e:
            logger.error(f"Error cleaning up object detection: {e}")