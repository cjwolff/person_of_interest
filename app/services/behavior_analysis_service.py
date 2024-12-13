from typing import List, Dict, Optional, Tuple
import numpy as np
import logging
import asyncio
from datetime import datetime, timedelta
from collections import defaultdict
from app.core.config import get_settings
from app.core.metrics import ERROR_COUNT
from scipy.spatial.distance import cdist

settings = get_settings()
logger = logging.getLogger(__name__)

class BehaviorAnalysisService:
    def __init__(self):
        try:
            self.processing_lock = asyncio.Lock()
            self.track_history = defaultdict(list)
            self.behavior_patterns = defaultdict(list)
            self.interaction_history = defaultdict(list)
            self.last_cleanup = datetime.now()
            self.cleanup_interval = timedelta(seconds=300)  # 5 minutes
            self.max_history_age = timedelta(seconds=60)
            self.min_track_points = 5
            
            # Risk thresholds
            self.risk_thresholds = {
                "proximity": 50.0,  # pixels
                "speed": 100.0,     # pixels/second
                "direction_change": np.pi/4,  # 45 degrees
                "dwell_time": 5.0   # seconds
            }
            
            logger.info("Behavior analysis service initialized")
        except Exception as e:
            ERROR_COUNT.labels(service="behavior", type="init").inc()
            logger.error(f"Failed to initialize behavior analysis: {e}")
            raise

    async def analyze(self, tracked_objects: List[Dict]) -> Dict:
        """Analyze behavior patterns in tracked objects"""
        if not tracked_objects:
            return self._empty_analysis_result()
            
        try:
            async with self.processing_lock:
                current_time = datetime.now()
                
                # Update track history
                await self._update_track_history(tracked_objects, current_time)
                
                # Analyze patterns
                movement_patterns = await self._analyze_movement_patterns()
                interaction_patterns = await self._analyze_interactions()
                anomalies = await self._detect_anomalies()
                
                # Calculate risk scores
                risk_scores = await self._calculate_risk_scores(
                    movement_patterns,
                    interaction_patterns,
                    anomalies
                )
                
                # Cleanup old data periodically
                if current_time - self.last_cleanup > self.cleanup_interval:
                    await self._cleanup_old_tracks(current_time)
                    self.last_cleanup = current_time
                
                return {
                    "movement_patterns": movement_patterns,
                    "interaction_patterns": interaction_patterns,
                    "anomalies": anomalies,
                    "risk_scores": risk_scores,
                    "timestamp": current_time.isoformat()
                }
                
        except Exception as e:
            ERROR_COUNT.labels(service="behavior", type="analysis").inc()
            logger.error(f"Error in behavior analysis: {e}")
            return self._empty_analysis_result()

    async def _cleanup_old_tracks(self, current_time: datetime):
        """Remove old tracking data"""
        try:
            cutoff_time = current_time - self.max_history_age
            expired_tracks = []
            
            for track_id, history in self.track_history.items():
                # Remove old points from history
                history[:] = [
                    point for point in history 
                    if point["timestamp"] > cutoff_time
                ]
                
                # Mark empty tracks for removal
                if not history:
                    expired_tracks.append(track_id)
            
            # Remove expired tracks
            for track_id in expired_tracks:
                del self.track_history[track_id]
                if track_id in self.behavior_patterns:
                    del self.behavior_patterns[track_id]
                    
        except Exception as e:
            logger.error(f"Error cleaning up old tracks: {e}")

    def _empty_analysis_result(self) -> Dict:
        """Return empty analysis result structure"""
        return {
            "movement_patterns": [],
            "interaction_patterns": [],
            "anomalies": [],
            "risk_scores": {},
            "timestamp": datetime.now().isoformat()
        }

    async def cleanup(self):
        """Cleanup analysis resources"""
        try:
            self.track_history.clear()
            self.behavior_patterns.clear()
            self.interaction_history.clear()
            logger.info("Behavior analysis service cleaned up")
        except Exception as e:
            ERROR_COUNT.labels(service="behavior", type="cleanup").inc()
            logger.error(f"Error in behavior analysis cleanup: {e}")