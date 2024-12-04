from typing import List, Optional
from sqlalchemy.orm import Session
from geopy.distance import geodesic
from ..models.alert import Alert
from ..models.user import User
from ..schemas.analysis import AlertCreate, AlertResponse
from ..core.config import settings

class ProximityAlertService:
    ALERT_RADIUS_METERS = 200.0
    
    async def check_proximity(
        self,
        db: Session,
        user_id: int,
        latitude: float,
        longitude: float
    ) -> List[AlertResponse]:
        """Check for nearby persons of interest"""
        alerts = []
        
        # Get all active photo notes with faces
        photo_notes = db.query(PhotoNote).filter(
            PhotoNote.type == "face",
            PhotoNote.is_active == True
        ).all()
        
        user_location = (latitude, longitude)
        
        for note in photo_notes:
            if note.user_id == user_id:
                continue
                
            note_location = (note.latitude, note.longitude)
            distance = geodesic(user_location, note_location).meters
            
            if distance <= self.ALERT_RADIUS_METERS:
                # Get recent behavior analysis
                recent_behavior = db.query(BehaviorAnalysis).filter(
                    BehaviorAnalysis.target_id == note.id
                ).order_by(
                    BehaviorAnalysis.timestamp.desc()
                ).limit(5).all()
                
                risk_level = max(
                    (b.risk_level for b in recent_behavior),
                    default=RiskLevel.LOW
                )
                
                alert = await self.create_alert(
                    db,
                    user_id=user_id,
                    target_id=note.id,
                    distance=distance,
                    risk_level=risk_level,
                    recent_behavior=recent_behavior
                )
                alerts.append(alert)
                
        return alerts
        
    async def create_alert(
        self,
        db: Session,
        user_id: int,
        target_id: int,
        distance: float,
        risk_level: RiskLevel,
        recent_behavior: Optional[List[BehaviorAnalysis]] = None
    ) -> AlertResponse:
        alert = Alert(
            user_id=user_id,
            target_id=target_id,
            distance=distance,
            risk_level=risk_level
        )
        db.add(alert)
        db.commit()
        db.refresh(alert)
        
        return AlertResponse(
            id=alert.id,
            target=db.query(PhotoNote).get(target_id),
            distance=distance,
            timestamp=alert.created_at,
            risk_level=risk_level,
            recent_behavior=recent_behavior
        )
        
    async def get_user_alerts(
        self,
        db: Session,
        user_id: int
    ) -> List[AlertResponse]:
        alerts = db.query(Alert).filter(
            Alert.user_id == user_id
        ).order_by(
            Alert.created_at.desc()
        ).all()
        
        return [
            AlertResponse(
                id=alert.id,
                target=db.query(PhotoNote).get(alert.target_id),
                distance=alert.distance,
                timestamp=alert.created_at,
                risk_level=alert.risk_level,
                recent_behavior=self._get_recent_behavior(db, alert.target_id)
            )
            for alert in alerts
        ]
        
    def _get_recent_behavior(
        self,
        db: Session,
        target_id: int
    ) -> List[BehaviorAnalysis]:
        return db.query(BehaviorAnalysis).filter(
            BehaviorAnalysis.target_id == target_id
        ).order_by(
            BehaviorAnalysis.timestamp.desc()
        ).limit(5).all()