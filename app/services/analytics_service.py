from typing import List, Dict, Optional
from datetime import datetime, timedelta
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from ..models.behavior import BehaviorPattern
from ..models.detection import Detection, FaceDetection
from ..models.geofence import GeofenceEvent

class AnalyticsService:
    async def get_client_analytics(
        self,
        db: AsyncSession,
        client_id: str,
        time_range: Optional[timedelta] = None
    ) -> Dict:
        """Get analytics data for Flutter client dashboard"""
        if time_range is None:
            time_range = timedelta(hours=24)
            
        start_time = datetime.utcnow() - time_range
        
        # Gather analytics data in parallel
        behavior_task = self._get_behavior_patterns(client_id, start_time, db)
        detection_task = self._get_detection_summary(client_id, start_time, db)
        geofence_task = self._get_geofence_events(client_id, start_time, db)
        
        behavior_data, detection_data, geofence_data = await asyncio.gather(
            behavior_task, detection_task, geofence_task
        )
        
        return {
            "behavior_patterns": behavior_data,
            "detections": detection_data,
            "geofence_events": geofence_data,
            "risk_assessment": self._calculate_risk_assessment(
                behavior_data, detection_data, geofence_data
            )
        }

    async def _get_behavior_patterns(
        self,
        client_id: str,
        start_time: datetime,
        db: AsyncSession
    ) -> List[Dict]:
        """Get behavior patterns for time period"""
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
                "risk_score": p.risk_score
            }
            for p in patterns
        ]

    def _calculate_risk_assessment(
        self,
        behavior_data: List[Dict],
        detection_data: Dict,
        geofence_data: List[Dict]
    ) -> Dict:
        """Calculate overall risk assessment for client display"""
        risk_factors = []
        
        # Analyze behavior patterns
        if behavior_data:
            recent_risk_scores = [p["risk_score"] for p in behavior_data[-10:]]
            risk_factors.append(sum(recent_risk_scores) / len(recent_risk_scores))
            
        # Analyze detection patterns
        if detection_data["high_risk_objects"]:
            risk_factors.append(0.8)  # High risk if dangerous objects detected
            
        # Analyze geofence violations
        recent_violations = [
            e for e in geofence_data 
            if e["event_type"] in ["enter", "dwell"]
        ]
        if recent_violations:
            risk_factors.append(0.6)
            
        return {
            "overall_score": sum(risk_factors) / len(risk_factors) if risk_factors else 0,
            "risk_level": self._classify_risk_level(risk_factors),
            "contributing_factors": self._identify_risk_factors(
                behavior_data, detection_data, geofence_data
            )
        } 