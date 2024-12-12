from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from ....core.database import get_db
from ....services.analytics_service import AnalyticsService
from ....schemas.analytics import ClientAnalytics, TimeRange

router = APIRouter()
analytics_service = AnalyticsService()

@router.get("/client/{client_id}/analytics", response_model=ClientAnalytics)
async def get_client_analytics(
    client_id: str,
    time_range: Optional[TimeRange] = TimeRange.last_24h,
    db: AsyncSession = Depends(get_db)
):
    """Get analytics data for Flutter client dashboard"""
    try:
        time_delta = {
            TimeRange.last_hour: timedelta(hours=1),
            TimeRange.last_24h: timedelta(hours=24),
            TimeRange.last_week: timedelta(days=7),
        }[time_range]
        
        analytics = await analytics_service.get_client_analytics(
            client_id, time_delta, db
        )
        return analytics
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving analytics: {str(e)}"
        )

@router.get("/client/{client_id}/behavior-history")
async def get_behavior_history(
    client_id: str,
    start_time: datetime,
    end_time: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get historical behavior data for Flutter client visualization"""
    try:
        if end_time is None:
            end_time = datetime.utcnow()
            
        history = await analytics_service.get_behavior_history(
            client_id, start_time, end_time, db
        )
        return {"history": history}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving behavior history: {str(e)}"
        ) 