import asyncio
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from ..models.behavior import BehaviorPattern
from ..models.detection import Detection, FaceDetection
from ..models.geofence import GeofenceEvent
from app.core.config import get_settings
from app.core.metrics import ERROR_COUNT
from cachetools import TTLCache

settings = get_settings()
logger = logging.getLogger(__name__)

class AnalyticsService:
    def __init__(self):
        self._cache = TTLCache(maxsize=1000, ttl=300)  # 5 minute cache
        self._batch_size = 1000
        self._min_query_interval = timedelta(seconds=1)
        self._last_query_time = {}

    async def get_client_analytics(
        self,
        client_id: str,
        time_range: timedelta,
        db: AsyncSession
    ) -> Dict:
        try:
            cache_key = f"{client_id}_{time_range.total_seconds()}"
            if cached := self._cache.get(cache_key):
                return cached

            # Rate limiting
            now = datetime.utcnow()
            if client_id in self._last_query_time:
                time_since_last = now - self._last_query_time[client_id]
                if time_since_last < self._min_query_interval:
                    await asyncio.sleep(
                        (self._min_query_interval - time_since_last).total_seconds()
                    )

            # Parallel queries
            start_time = now - time_range
            queries = await asyncio.gather(
                self._get_behavior_patterns(client_id, start_time, db),
                self._get_detections(client_id, start_time, db),
                self._get_geofence_events(client_id, start_time, db),
                return_exceptions=True
            )

            # Process results
            results = []
            for query_result in queries:
                if isinstance(query_result, Exception):
                    logger.error(f"Query error: {query_result}")
                    results.append([])
                else:
                    results.append(query_result)

            behavior_data, detection_data, geofence_data = results

            # Cache results
            result = {
                "behavior_patterns": behavior_data,
                "detections": detection_data,
                "geofence_events": geofence_data,
                "timestamp": now.isoformat()
            }
            self._cache[cache_key] = result
            self._last_query_time[client_id] = now

            return result

        except Exception as e:
            logger.error(f"Error getting analytics: {e}")
            return self._empty_analytics_result()

    async def _get_behavior_patterns(
        self,
        client_id: str,
        start_time: datetime,
        db: AsyncSession
    ) -> List[Dict]:
        """Get behavior patterns for time period"""
        try:
            query = select(BehaviorPattern).where(
                and_(
                    BehaviorPattern.client_id == client_id,
                    BehaviorPattern.created_at >= start_time
                )
            ).order_by(BehaviorPattern.created_at.desc())
            
            result = await db.execute(query)
            patterns = result.scalars().all()
            
            return [
                {
                    "timestamp": p.created_at.isoformat(),
                    "movement_pattern": p.movement_pattern,
                    "interaction_pattern": p.interaction_pattern,
                    "risk_score": p.risk_score,
                    "metadata": p.metadata
                }
                for p in patterns
            ]
        except Exception as e:
            logger.error(f"Error getting behavior patterns: {e}")
            return []

    async def _get_detection_summary(
        self,
        client_id: str,
        start_time: datetime,
        db: AsyncSession
    ) -> Dict:
        """Get detection statistics summary"""
        try:
            # Get total detections count
            count_query = select(func.count(Detection.id)).where(
                and_(
                    Detection.client_id == client_id,
                    Detection.created_at >= start_time
                )
            )
            
            # Get high risk objects
            risk_query = select(Detection).where(
                and_(
                    Detection.client_id == client_id,
                    Detection.created_at >= start_time,
                    Detection.confidence >= self.risk_thresholds["high"]
                )
            ).order_by(Detection.created_at.desc())
            
            # Get detection types distribution
            type_query = select(
                Detection.object_type,
                func.count(Detection.id).label('count')
            ).where(
                and_(
                    Detection.client_id == client_id,
                    Detection.created_at >= start_time
                )
            ).group_by(Detection.object_type)
            
            total_count = await db.scalar(count_query) or 0
            high_risk = (await db.execute(risk_query)).scalars().all()
            type_dist = (await db.execute(type_query)).all()
            
            return {
                "total_detections": total_count,
                "high_risk_objects": [
                    {
                        "id": obj.id,
                        "object_type": obj.object_type,
                        "confidence": obj.confidence,
                        "timestamp": obj.created_at.isoformat(),
                        "location": obj.location,
                        "metadata": obj.metadata
                    }
                    for obj in high_risk
                ],
                "type_distribution": {
                    t.object_type: t.count
                    for t in type_dist
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting detection summary: {e}")
            return {
                "total_detections": 0,
                "high_risk_objects": [],
                "type_distribution": {}
            }

    async def _get_face_detection_summary(
        self,
        client_id: str,
        start_time: datetime,
        db: AsyncSession
    ) -> Dict:
        """Get face detection statistics"""
        try:
            query = select(FaceDetection).where(
                and_(
                    FaceDetection.client_id == client_id,
                    FaceDetection.created_at >= start_time,
                    FaceDetection.confidence >= self.risk_thresholds["medium"]
                )
            ).order_by(FaceDetection.created_at.desc())
            
            result = await db.execute(query)
            faces = result.scalars().all()
            
            return {
                "total_faces": len(faces),
                "face_detections": [
                    {
                        "id": face.id,
                        "confidence": face.confidence,
                        "timestamp": face.created_at.isoformat(),
                        "landmarks": face.landmarks,
                        "metadata": face.metadata
                    }
                    for face in faces
                ]
            }
        except Exception as e:
            logger.error(f"Error getting face detection summary: {e}")
            return {"total_faces": 0, "face_detections": []}

    async def _get_geofence_events(
        self,
        client_id: str,
        start_time: datetime,
        db: AsyncSession
    ) -> List[Dict]:
        """Get geofence events for time period"""
        try:
            query = select(GeofenceEvent).where(
                and_(
                    GeofenceEvent.client_id == client_id,
                    GeofenceEvent.created_at >= start_time
                )
            ).order_by(GeofenceEvent.created_at.desc())
            
            result = await db.execute(query)
            events = result.scalars().all()
            
            return [
                {
                    "event_id": event.id,
                    "zone_id": event.zone_id,
                    "event_type": event.event_type,
                    "timestamp": event.created_at.isoformat(),
                    "location": event.location,
                    "metadata": event.metadata
                }
                for event in events
            ]
        except Exception as e:
            logger.error(f"Error getting geofence events: {e}")
            return []

    async def _calculate_risk_assessment(
        self,
        behavior_data: List[Dict],
        detection_data: Dict,
        geofence_data: List[Dict],
        face_data: Dict
    ) -> Dict:
        """Calculate comprehensive risk assessment"""
        try:
            risk_factors = []
            contributing_factors = []
            
            # Analyze behavior patterns
            if behavior_data:
                recent_risk_scores = [p["risk_score"] for p in behavior_data[-10:]]
                behavior_risk = sum(recent_risk_scores) / len(recent_risk_scores)
                risk_factors.append(behavior_risk)
                
                if behavior_risk >= self.risk_thresholds["medium"]:
                    contributing_factors.append({
                        "type": "behavior",
                        "risk_level": self._get_risk_level(behavior_risk),
                        "details": "Suspicious behavior patterns detected"
                    })
            
            # Analyze detection patterns
            if detection_data["high_risk_objects"]:
                detection_risk = 0.8
                risk_factors.append(detection_risk)
                contributing_factors.append({
                    "type": "detection",
                    "risk_level": "high",
                    "details": f"{len(detection_data['high_risk_objects'])} high-risk objects detected"
                })
            
            # Analyze face detections
            if face_data["total_faces"] > 0:
                face_risk = min(0.7, face_data["total_faces"] / 100)
                risk_factors.append(face_risk)
                
                if face_risk >= self.risk_thresholds["medium"]:
                    contributing_factors.append({
                        "type": "face_detection",
                        "risk_level": self._get_risk_level(face_risk),
                        "details": f"High number of face detections: {face_data['total_faces']}"
                    })
            
            # Analyze geofence violations
            recent_violations = [
                e for e in geofence_data 
                if e["event_type"] in ["enter", "dwell"]
            ]
            if recent_violations:
                geofence_risk = 0.6
                risk_factors.append(geofence_risk)
                contributing_factors.append({
                    "type": "geofence",
                    "risk_level": "medium",
                    "details": f"{len(recent_violations)} geofence violations detected"
                })
            
            # Calculate overall risk
            overall_risk = sum(risk_factors) / len(risk_factors) if risk_factors else 0
            
            return {
                "overall_score": overall_risk,
                "risk_level": self._get_risk_level(overall_risk),
                "contributing_factors": contributing_factors,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error calculating risk assessment: {e}")
            return self._empty_risk_assessment()

    def _get_risk_level(self, risk_score: float) -> str:
        """Convert risk score to risk level"""
        if risk_score >= self.risk_thresholds["high"]:
            return "high"
        elif risk_score >= self.risk_thresholds["medium"]:
            return "medium"
        return "low"

    async def _update_cache(self, cache_key: str, data: Dict):
        """Update cache with size management"""
        try:
            # Remove oldest entries if cache is too large
            if len(self.cache) >= self.max_cache_size:
                oldest_key = min(
                    self.cache.keys(),
                    key=lambda k: self.cache[k]["timestamp"]
                )
                del self.cache[oldest_key]
            
            self.cache[cache_key] = {
                "data": data,
                "timestamp": datetime.now()
            }
        except Exception as e:
            logger.error(f"Error updating cache: {e}")

    def _empty_analytics_result(self) -> Dict:
        """Return empty analytics result structure"""
        return {
            "behavior_patterns": [],
            "detections": {
                "total_detections": 0,
                "high_risk_objects": [],
                "type_distribution": {}
            },
            "geofence_events": [],
            "face_detections": {
                "total_faces": 0,
                "face_detections": []
            },
            "risk_assessment": self._empty_risk_assessment(),
            "timestamp": datetime.utcnow().isoformat()
        }

    def _empty_risk_assessment(self) -> Dict:
        """Return empty risk assessment structure"""
        return {
            "overall_score": 0.0,
            "risk_level": "low",
            "contributing_factors": [],
            "timestamp": datetime.utcnow().isoformat()
        }

    async def cleanup(self):
        """Cleanup analytics resources"""
        try:
            self.cache.clear()
        except Exception as e:
            logger.error(f"Error in analytics cleanup: {e}")
</code_block_to_apply_changes_from>