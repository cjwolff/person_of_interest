import cv2
import numpy as np
from typing import Tuple, Optional
from ..core.config import get_settings

settings = get_settings()

class VideoProcessor:
    def __init__(self):
        self.max_dimension = settings.MAX_VIDEO_DIMENSION
        self.jpeg_quality = settings.JPEG_QUALITY

    def preprocess_frame(self, frame: np.ndarray) -> Tuple[np.ndarray, Optional[dict]]:
        """Preprocess frame for efficient processing"""
        # Resize if needed
        height, width = frame.shape[:2]
        if max(height, width) > self.max_dimension:
            scale = self.max_dimension / max(height, width)
            new_width = int(width * scale)
            new_height = int(height * scale)
            frame = cv2.resize(frame, (new_width, new_height))
            
        # Convert to RGB for ML models
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        metadata = {
            "original_size": (width, height),
            "processed_size": frame_rgb.shape[:2],
            "scale_factor": width / frame_rgb.shape[1]
        }
        
        return frame_rgb, metadata

    def compress_frame(self, frame: np.ndarray) -> bytes:
        """Compress frame for WebSocket transmission"""
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), self.jpeg_quality]
        _, buffer = cv2.imencode('.jpg', frame, encode_param)
        return buffer.tobytes()