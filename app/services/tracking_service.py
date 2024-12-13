from typing import List, Dict, Optional, Tuple
import numpy as np
import cv2
import logging
import asyncio
from datetime import datetime, timedelta
from collections import defaultdict
from app.core.config import get_settings
from app.core.metrics import ERROR_COUNT
from scipy.optimize import linear_sum_assignment

settings = get_settings()
logger = logging.getLogger(__name__)

class TrackingService:
    def __init__(self):
        try:
            self.tracking_lock = asyncio.Lock()
            self.tracked_objects = defaultdict(dict)
            self.track_history = defaultdict(list)
            self.last_cleanup = datetime.now()
            self.cleanup_interval = timedelta(seconds=30)
            self.max_track_age = timedelta(seconds=5)
            self.max_prediction_steps = 5
            self.iou_threshold = 0.3
            self.kalman_filters = {}
            
            logger.info("Tracking service initialized")
        except Exception as e:
            ERROR_COUNT.labels(service="tracking", type="init").inc()
            logger.error(f"Failed to initialize tracking: {e}")
            raise

    async def update(self, detections: List[Dict], frame: Optional[np.ndarray] = None) -> List[Dict]:
        """Update object tracking with new detections"""
        if not detections:
            return []
            
        try:
            async with self.tracking_lock:
                current_time = datetime.now()
                tracked_detections = []
                
                # Predict new locations using Kalman filters
                predictions = self._predict_tracks()
                
                # Associate detections with existing tracks
                matches, unmatched_detections, unmatched_tracks = \
                    await self._associate_detections(detections, predictions)
                
                # Update matched tracks
                for track_id, detection_idx in matches:
                    detection = detections[detection_idx]
                    await self._update_track(track_id, detection, current_time)
                    tracked_detections.append({
                        **detection,
                        "track_id": track_id,
                        "velocity": self._calculate_velocity(track_id)
                    })
                
                # Initialize new tracks
                for detection_idx in unmatched_detections:
                    detection = detections[detection_idx]
                    track_id = self._generate_track_id()
                    await self._initialize_track(track_id, detection, current_time)
                    tracked_detections.append({
                        **detection,
                        "track_id": track_id,
                        "velocity": (0.0, 0.0)
                    })
                
                # Handle lost tracks
                for track_id in unmatched_tracks:
                    if self._is_track_lost(track_id, current_time):
                        await self._remove_track(track_id)
                
                # Periodic cleanup
                if current_time - self.last_cleanup > self.cleanup_interval:
                    await self._cleanup_old_tracks()
                    self.last_cleanup = current_time
                
                return tracked_detections
                
        except Exception as e:
            ERROR_COUNT.labels(service="tracking", type="update").inc()
            logger.error(f"Error in tracking update: {e}")
            return []

    async def _associate_detections(
        self,
        detections: List[Dict],
        predictions: Dict[str, np.ndarray]
    ) -> Tuple[List[Tuple[str, int]], List[int], List[str]]:
        """Associate detections with predicted track locations"""
        try:
            if not detections or not predictions:
                return [], list(range(len(detections))), list(predictions.keys())

            # Build cost matrix using IoU
            cost_matrix = np.zeros((len(predictions), len(detections)))
            for i, (track_id, pred_bbox) in enumerate(predictions.items()):
                for j, detection in enumerate(detections):
                    cost_matrix[i, j] = 1 - self._calculate_iou(
                        pred_bbox, np.array(detection["bbox"])
                    )

            # Apply Hungarian algorithm
            track_indices, detection_indices = linear_sum_assignment(cost_matrix)

            # Filter matches using IoU threshold
            matches = []
            unmatched_detections = list(range(len(detections)))
            track_ids = list(predictions.keys())
            unmatched_tracks = track_ids.copy()

            for track_idx, det_idx in zip(track_indices, detection_indices):
                if cost_matrix[track_idx, det_idx] <= 1 - self.iou_threshold:
                    matches.append((track_ids[track_idx], det_idx))
                    unmatched_detections.remove(det_idx)
                    unmatched_tracks.remove(track_ids[track_idx])

            return matches, unmatched_detections, unmatched_tracks

        except Exception as e:
            logger.error(f"Error in detection association: {e}")
            return [], list(range(len(detections))), list(predictions.keys())

    def _calculate_iou(self, bbox1: np.ndarray, bbox2: np.ndarray) -> float:
        """Calculate Intersection over Union between two bounding boxes"""
        try:
            x1 = max(bbox1[0], bbox2[0])
            y1 = max(bbox1[1], bbox2[1])
            x2 = min(bbox1[2], bbox2[2])
            y2 = min(bbox1[3], bbox2[3])

            intersection = max(0, x2 - x1) * max(0, y2 - y1)
            area1 = (bbox1[2] - bbox1[0]) * (bbox1[3] - bbox1[1])
            area2 = (bbox2[2] - bbox2[0]) * (bbox2[3] - bbox2[1])
            union = area1 + area2 - intersection

            return intersection / max(union, 1e-6)
        except Exception as e:
            logger.error(f"Error calculating IoU: {e}")
            return 0.0

    async def _update_track(self, track_id: str, detection: Dict, current_time: datetime):
        """Update track with new detection"""
        try:
            # Update Kalman filter
            if track_id in self.kalman_filters:
                self.kalman_filters[track_id].update(np.array(detection["bbox"]))
            else:
                self._initialize_kalman_filter(track_id, detection["bbox"])

            # Update track history
            self.track_history[track_id].append({
                "position": self._get_bbox_center(detection["bbox"]),
                "bbox": detection["bbox"],
                "timestamp": current_time
            })

            # Limit history length
            if len(self.track_history[track_id]) > 30:
                self.track_history[track_id].pop(0)

            # Update tracked object data
            self.tracked_objects[track_id].update({
                "last_detection": detection,
                "last_seen": current_time,
                "consecutive_misses": 0
            })

        except Exception as e:
            logger.error(f"Error updating track {track_id}: {e}")

    def _calculate_velocity(self, track_id: str) -> Tuple[float, float]:
        """Calculate velocity vector for tracked object"""
        try:
            history = self.track_history[track_id]
            if len(history) < 2:
                return (0.0, 0.0)

            last_pos = history[-1]["position"]
            prev_pos = history[-2]["position"]
            time_diff = (history[-1]["timestamp"] - history[-2]["timestamp"]).total_seconds()

            if time_diff > 0:
                vx = (last_pos[0] - prev_pos[0]) / time_diff
                vy = (last_pos[1] - prev_pos[1]) / time_diff
                return (vx, vy)
            return (0.0, 0.0)

        except Exception as e:
            logger.error(f"Error calculating velocity: {e}")
            return (0.0, 0.0)

    async def cleanup(self):
        """Cleanup tracking resources"""
        try:
            self.tracked_objects.clear()
            self.track_history.clear()
            self.kalman_filters.clear()
            logger.info("Tracking service cleaned up")
        except Exception as e:
            logger.error(f"Error cleaning up tracking service: {e}")
