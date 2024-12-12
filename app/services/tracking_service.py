from typing import List, Dict
import numpy as np
import cv2
from deep_sort_realtime.deepsort_tracker import DeepSort
import asyncio
import torch
import logging

logger = logging.getLogger(__name__)

class TrackingService:
    def __init__(self):
        # Suppress PyTorch future warnings about model loading
        import warnings
        warnings.filterwarnings('ignore', category=FutureWarning, module='torch.serialization')
        
        self.tracker = DeepSort(
            max_age=30,
            n_init=3,
            nms_max_overlap=1.0,
            max_cosine_distance=0.3,
            nn_budget=None,
            embedder="mobilenet",
            bgr=True,
            embedder_gpu=False,
            embedder_model_name=None,
            embedder_wts=None,
            polygon=False,
            today=None
        )
        self.processing_lock = asyncio.Lock()
        
    def _ensure_list_float(self, value) -> List[float]:
        """Convert various numeric types to list of floats"""
        if isinstance(value, (list, tuple, np.ndarray)):
            return [float(x) for x in value]
        if isinstance(value, (int, float, np.number)):
            return [float(value), 0.0, 0.0, 0.0]
        return [0.0, 0.0, 0.0, 0.0]
        
    async def update(self, detections: List[Dict], frame=None) -> List[Dict]:
        try:
            if not detections:
                return []
            
            # Convert detections to format expected by DeepSort
            detection_boxes = []
            detection_scores = []
            detection_classes = []
            
            for det in detections:
                bbox = det.get('bbox')
                # Use the helper method to ensure bbox is a list of floats
                bbox = self._ensure_list_float(bbox)
                if len(bbox) != 4:  # Skip invalid bboxes
                    continue
                    
                detection_boxes.append(bbox)
                detection_scores.append(float(det.get('confidence', 0.0)))
                detection_classes.append(str(det.get('class_name', 'unknown')))
                
            if not detection_boxes:
                return []
            
            # Convert to numpy arrays
            detection_boxes = np.array(detection_boxes)
            detection_scores = np.array(detection_scores)
            
            # Update tracker
            tracks = self.tracker.update_tracks(
                detection_boxes,
                detection_scores,
                frame=frame
            )
            
            # Process tracks
            tracked_detections = []
            for track in tracks:
                if not track.is_confirmed():
                    continue
                    
                track_box = track.to_tlbr()
                track_box = [float(x) for x in track_box]  # Convert to list of floats
                
                # Find matching original detection
                original_det = next(
                    (d for d in detections if np.allclose(
                        self._ensure_list_float(d['bbox']), 
                        track_box, 
                        rtol=1e-05, 
                        atol=1e-08
                    )), 
                    detections[0] if detections else None
                )
                
                if original_det:
                    tracked_det = {
                        'bbox': track_box,
                        'track_id': str(track.track_id),
                        'class_name': str(original_det.get('class_name', 'unknown')),
                        'confidence': float(track.confidence) if hasattr(track, 'confidence') else float(original_det.get('confidence', 0.0))
                    }
                    tracked_detections.append(tracked_det)
                    
            return tracked_detections
            
        except Exception as e:
            logger.error(f"Error in update: {e}")
            return []
