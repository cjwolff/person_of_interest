import cv2
import numpy as np
import logging
import asyncio
from typing import Tuple, Dict, Optional
from app.core.config import get_settings
from app.core.metrics import ERROR_COUNT
from app.models.frame import FrameRequest
from cachetools import LRUCache
from queue import Queue
import hashlib

settings = get_settings()
logger = logging.getLogger(__name__)

class VideoProcessor:
    def __init__(self):
        try:
            self.max_dimension = settings.MAX_VIDEO_DIMENSION
            self.jpeg_quality = settings.JPEG_QUALITY
            self.processing_lock = asyncio.Lock()
            self._frame_cache = LRUCache(maxsize=30)  # Use LRU cache
            self._frame_pool = Queue(maxsize=100)  # Memory pool
            self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
        except Exception as e:
            logger.error(f"Failed to initialize VideoProcessor: {e}")
            raise

    async def preprocess_frame(self, frame: np.ndarray) -> Tuple[np.ndarray, Dict]:
        """Preprocess frame for efficient processing with error handling"""
        if frame is None or frame.size == 0:
            raise ValueError("Invalid frame input")
            
        try:
            async with self.processing_lock:
                # Check frame cache
                frame_hash = self._compute_frame_hash(frame)
                if cached := self._frame_cache.get(frame_hash):
                    return cached

                # Get frame dimensions
                height, width = frame.shape[:2]
                original_size = (width, height)
                
                # Resize if needed
                if max(height, width) > self.max_dimension:
                    scale = self.max_dimension / max(height, width)
                    new_size = (int(width * scale), int(height * scale))
                    frame = cv2.resize(frame, new_size, interpolation=cv2.INTER_AREA)

                # Basic preprocessing
                processed = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                processed = cv2.normalize(processed, None, 0, 255, cv2.NORM_MINMAX)
                
                # Cache result
                result = (processed, {
                    "original_size": original_size,
                    "processed_size": processed.shape[:2],
                    "scale_factor": scale if 'scale' in locals() else 1.0
                })
                self._frame_cache[frame_hash] = result
                return result

        except Exception as e:
            logger.error(f"Error preprocessing frame: {e}")
            raise

    def _compute_frame_hash(self, frame: np.ndarray) -> str:
        """Compute quick frame hash for caching"""
        try:
            # Downsample frame for faster hashing
            small = cv2.resize(frame, (32, 32))
            return hashlib.md5(small.tobytes()).hexdigest()
        except Exception as e:
            logger.error(f"Error computing frame hash: {e}")
            return ""

    async def _periodic_cleanup(self):
        """Periodically cleanup resources"""
        while True:
            try:
                await asyncio.sleep(300)  # Clean every 5 minutes
                self._frame_cache.clear()
                while not self._frame_pool.empty():
                    self._frame_pool.get_nowait()
            except Exception as e:
                logger.error(f"Error in periodic cleanup: {e}")

    def compress_frame(self, frame: np.ndarray) -> bytes:
        """Compress frame for WebSocket transmission with error handling"""
        try:
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), self.jpeg_quality]
            _, buffer = cv2.imencode('.jpg', frame, encode_param)
            return buffer.tobytes()
        except Exception as e:
            logger.error(f"Error compressing frame: {e}")
            raise

    def bytes_to_frame(self, frame_bytes: bytes) -> np.ndarray:
        """Convert bytes to frame with error handling"""
        try:
            nparr = np.frombuffer(frame_bytes, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if frame is None:
                raise ValueError("Failed to decode frame bytes")
            return frame
        except Exception as e:
            logger.error(f"Error converting bytes to frame: {e}")
            raise

    async def cleanup(self):
        """Cleanup processor resources"""
        try:
            self._frame_cache.clear()
        except Exception as e:
            logger.error(f"Error in video processor cleanup: {e}")