from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db  # Changed from ....core
from app.services.behavior_analysis_service import BehaviorAnalysisService  # Changed from ....services
from app.models.behavior import BehaviorPattern  # Changed from ....models 