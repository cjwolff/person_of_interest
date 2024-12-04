from fastapi import APIRouter, Depends, HTTPException, WebSocket
from sqlalchemy.orm import Session
from typing import List
import numpy as np
from ....core.deps import get_db, get_current_user
from ....schemas.analysis import (
    BehaviorAnalysis,
    PoseData,
    AlertCreate,
    AlertResponse
)
from ....services.behavior import BehaviorAnalysisService
from ....services.proximity import ProximityAlertService
from ....models.user import User

router = APIRouter()
behavior_service = BehaviorAnalysisService()
alert_service = ProximityAlertService()

@router.websocket("/ws/behavior")
async def behavior_analysis_websocket(
    websocket: WebSocket,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            
            if data["type"] == "pose_data":
                pose_data = PoseData(**data["data"])
                analysis = behavior_service.analyze_pose(pose_data)
                
                if analysis.risk_level >= RiskLevel.HIGH:
                    await alert_service.create_alert(
                        db=db,
                        user_id=user.id,
                        analysis=analysis
                    )
                
                await websocket.send_json({
                    "type": "analysis_result",
                    "data": analysis.dict()
                })
            
            elif data["type"] == "location_update":
                alerts = await alert_service.check_proximity(
                    db=db,
                    user_id=user.id,
                    latitude=data["data"]["latitude"],
                    longitude=data["data"]["longitude"]
                )
                
                if alerts:
                    await websocket.send_json({
                        "type": "proximity_alerts",
                        "data": [alert.dict() for alert in alerts]
                    })
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await websocket.close()

@router.post("/alerts", response_model=AlertResponse)
async def create_alert(
    alert: AlertCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await alert_service.create_alert(
        db=db,
        user_id=current_user.id,
        **alert.dict()
    )

@router.get("/alerts", response_model=List[AlertResponse])
async def get_alerts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await alert_service.get_user_alerts(db, current_user.id)