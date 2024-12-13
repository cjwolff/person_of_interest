from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db  # Changed from ....core
from app.services.analytics_service import AnalyticsService  # Changed from ....services
from app.models.analytics import AnalyticsDataV2  # Changed from ....models 