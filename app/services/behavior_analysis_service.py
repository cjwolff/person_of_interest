from typing import List, Dict
import numpy as np
import asyncio
from datetime import datetime, timedelta

class BehaviorAnalysisService:
    def __init__(self):
        self.processing_lock = asyncio.Lock()
        self.track_history = {}
        self.suspicious_threshold = 0.8
        
    async def analyze(self, tracked_objects: List[Dict]) -> Dict:
        """Analyze behavior patterns in tracked objects"""
        async with self.processing_lock:
            analysis_results = {
                "suspicious_activities": [],
                "crowd_density": 0,
                "movement_patterns": [],
                "risk_score": 0.0
            }
            
            # Update track history
            current_time = datetime.now()
            for obj in tracked_objects:
                track_id = obj.get("track_id")
                if track_id:
                    if track_id not in self.track_history:
                        self.track_history[track_id] = []
                    self.track_history[track_id].append({
                        "position": obj["bbox"],
                        "timestamp": current_time
                    })
            
            # Calculate crowd density
            if tracked_objects:
                analysis_results["crowd_density"] = len(tracked_objects)
            
            # Analyze movement patterns
            for track_id, history in self.track_history.items():
                if len(history) > 1:
                    # Calculate velocity and direction
                    recent_positions = history[-2:]
                    movement = {
                        "track_id": track_id,
                        "velocity": self._calculate_velocity(recent_positions),
                        "direction": self._calculate_direction(recent_positions)
                    }
                    analysis_results["movement_patterns"].append(movement)
            
            # Clean up old tracks
            self._cleanup_old_tracks(current_time - timedelta(seconds=30))
            
            return analysis_results
            
    def _calculate_velocity(self, positions: List[Dict]) -> float:
        # Simple velocity calculation
        if len(positions) < 2:
            return 0.0
        p1 = positions[0]["position"]
        p2 = positions[1]["position"]
        dt = (positions[1]["timestamp"] - positions[0]["timestamp"]).total_seconds()
        if dt == 0:
            return 0.0
        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        return np.sqrt(dx*dx + dy*dy) / dt
    
    def _calculate_direction(self, positions: List[Dict]) -> float:
        if len(positions) < 2:
            return 0.0
        p1 = positions[0]["position"]
        p2 = positions[1]["position"]
        return np.arctan2(p2[1] - p1[1], p2[0] - p1[0])
    
    def _cleanup_old_tracks(self, threshold_time: datetime):
        for track_id in list(self.track_history.keys()):
            self.track_history[track_id] = [
                pos for pos in self.track_history[track_id]
                if pos["timestamp"] > threshold_time
            ]
            if not self.track_history[track_id]:
                del self.track_history[track_id] 