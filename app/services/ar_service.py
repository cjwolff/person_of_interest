import numpy as np
import asyncio
from typing import List, Dict, Optional, Tuple
import cv2
import logging
from datetime import datetime
from app.core.config import get_settings
from app.core.metrics import ERROR_COUNT
import hashlib
from cachetools import TTLCache

settings = get_settings()
logger = logging.getLogger(__name__)

class ARService:
    def __init__(self, object_detector=None, face_detector=None):
        try:
            self.processing_lock = asyncio.Lock()
            self.result_cache = TTLCache(maxsize=100, ttl=0.5)  # 500ms cache
            self.min_confidence = settings.MIN_DETECTION_CONFIDENCE
            self.max_overlay_distance = 50  # pixels
            self.overlay_colors = {
                "face": (0, 255, 0),      # Green
                "person": (255, 0, 0),     # Red
                "vehicle": (0, 0, 255),    # Blue
                "restricted": (255, 0, 255) # Purple
            }
            # Store detector services
            self.object_detector = object_detector
            self.face_detector = face_detector
            
            logger.info("AR service initialized")
        except Exception as e:
            ERROR_COUNT.labels(service="ar", type="init").inc()
            logger.error(f"Failed to initialize AR service: {e}")
            raise

    async def process_frame(
        self,
        frame: np.ndarray,
        faces: List[Dict],
        tracked_objects: List[Dict]
    ) -> Dict:
        """Process frame and generate AR overlays"""
        try:
            frame_hash = self._compute_frame_hash(frame)
            if cached := self.result_cache.get(frame_hash):
                return cached

            async with self.processing_lock:
                # Process detections
                face_overlays = await self._process_faces(faces)
                object_overlays = await self._process_objects(tracked_objects)
                
                # Generate depth map for occlusion handling
                depth_map = await self._generate_depth_map(frame)
                
                # Combine overlays with occlusion handling
                ar_data = {
                    "overlays": {
                        "faces": face_overlays,
                        "objects": object_overlays
                    },
                    "depth_map": depth_map.tolist() if depth_map is not None else None,
                    "frame_metadata": {
                        "width": frame.shape[1],
                        "height": frame.shape[0],
                        "timestamp": datetime.now().isoformat()
                    }
                }
                
                self.result_cache[frame_hash] = ar_data
                return ar_data

        except Exception as e:
            ERROR_COUNT.labels(service="ar", type="processing").inc()
            logger.error(f"Error processing AR frame: {e}")
            return self._empty_ar_data(frame)

    async def _process_faces(self, faces: List[Dict]) -> List[Dict]:
        """Process face detections for AR"""
        try:
            processed_faces = []
            for face in faces:
                if face["confidence"] < self.min_confidence:
                    continue
                    
                processed_face = {
                    **face,
                    "overlay_type": "face_highlight",
                    "privacy_blur": True,  # Enable face privacy
                    "metadata": {
                        "distance": self._estimate_distance(face["bbox"]),
                        "orientation": self._estimate_orientation(face["landmarks"]),
                        "blur_level": self._calculate_blur_level(face["confidence"])
                    }
                }
                processed_faces.append(processed_face)
            return processed_faces
        except Exception as e:
            ERROR_COUNT.labels(service="ar", type="face_processing").inc()
            logger.error(f"Error processing faces: {e}")
            return []

    async def _process_objects(self, objects: List[Dict]) -> List[Dict]:
        """Process object detections for AR"""
        try:
            processed_objects = []
            for obj in objects:
                if obj["confidence"] < self.min_confidence:
                    continue
                    
                processed_obj = {
                    **obj,
                    "overlay_type": "object_highlight",
                    "color": self.overlay_colors.get(obj["class_name"], (255, 255, 255)),
                    "metadata": {
                        "distance": self._estimate_distance(obj["bbox"]),
                        "motion_vector": self._estimate_motion(obj),
                        "occlusion_level": self._estimate_occlusion(obj["bbox"])
                    }
                }
                processed_objects.append(processed_obj)
            return processed_objects
        except Exception as e:
            ERROR_COUNT.labels(service="ar", type="object_processing").inc()
            logger.error(f"Error processing objects: {e}")
            return []

    async def _generate_depth_map(self, frame: np.ndarray) -> Optional[np.ndarray]:
        """Generate simple depth map for occlusion handling"""
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            # Use Sobel operators for edge detection
            sobel_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
            sobel_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
            # Approximate depth from edge magnitude
            depth_map = np.sqrt(sobel_x**2 + sobel_y**2)
            # Normalize to 0-1 range
            depth_map = cv2.normalize(depth_map, None, 0, 1, cv2.NORM_MINMAX)
            return depth_map
        except Exception as e:
            logger.error(f"Error generating depth map: {e}")
            return None

    def _estimate_distance(self, bbox: List[float]) -> float:
        """Estimate relative distance based on bbox size"""
        try:
            width = bbox[2] - bbox[0]
            height = bbox[3] - bbox[1]
            area = width * height
            # Inverse relationship between area and distance
            return 1.0 / max(area, 1e-6)
        except Exception as e:
            logger.error(f"Error estimating distance: {e}")
            return 0.0

    def _estimate_orientation(self, landmarks: List[Dict]) -> Dict:
        """Estimate face orientation from landmarks"""
        try:
            if len(landmarks) < 3:
                return {"yaw": 0.0, "pitch": 0.0, "roll": 0.0}
                
            # Calculate basic orientation from landmark positions
            # This is a simplified estimation
            left_eye = landmarks[0]
            right_eye = landmarks[1]
            nose = landmarks[2]
            
            dx = right_eye["x"] - left_eye["x"]
            dy = right_eye["y"] - left_eye["y"]
            
            yaw = np.arctan2(dy, dx)
            pitch = np.arctan2(nose["y"] - (left_eye["y"] + right_eye["y"])/2,
                             nose["x"] - (left_eye["x"] + right_eye["x"])/2)
            
            return {
                "yaw": float(yaw),
                "pitch": float(pitch),
                "roll": 0.0  # Need more landmarks for roll
            }
        except Exception as e:
            logger.error(f"Error estimating orientation: {e}")
            return {"yaw": 0.0, "pitch": 0.0, "roll": 0.0}

    def _calculate_blur_level(self, confidence: float) -> float:
        """Calculate privacy blur level based on confidence"""
        try:
            # Higher confidence = more blur
            return min(1.0, max(0.3, confidence))
        except Exception as e:
            logger.error(f"Error calculating blur level: {e}")
            return 0.5

    def _estimate_motion(self, obj: Dict) -> Optional[Tuple[float, float]]:
        """Estimate object motion vector"""
        try:
            if "velocity" in obj:
                return (obj["velocity"]["x"], obj["velocity"]["y"])
            return None
        except Exception as e:
            logger.error(f"Error estimating motion: {e}")
            return None

    def _estimate_occlusion(self, bbox: List[float]) -> float:
        """Estimate object occlusion level"""
        try:
            # Simple implementation - could be improved with depth analysis
            x1, y1, x2, y2 = bbox
            if x1 < 0 or y1 < 0 or x2 > 1 or y2 > 1:
                return 0.5  # Partially occluded
            return 0.0  # Not occluded
        except Exception as e:
            logger.error(f"Error estimating occlusion: {e}")
            return 0.0

    def _compute_frame_hash(self, frame: np.ndarray) -> str:
        """Compute quick frame hash for caching"""
        try:
            small = cv2.resize(frame, (32, 32))
            return hashlib.md5(small.tobytes()).hexdigest()
        except Exception as e:
            logger.error(f"Error computing frame hash: {e}")
            return ""

    def _empty_ar_data(self, frame: np.ndarray) -> Dict:
        """Return empty AR data structure"""
        return {
            "overlays": {
                "faces": [],
                "objects": []
            },
            "depth_map": None,
            "frame_metadata": {
                "width": frame.shape[1],
                "height": frame.shape[0],
                "timestamp": datetime.now().isoformat()
            }
        }

    async def cleanup(self):
        """Cleanup AR service resources"""
        try:
            self.result_cache.clear()
            logger.info("AR service cleaned up")
        except Exception as e:
            logger.error(f"Error cleaning up AR service: {e}")