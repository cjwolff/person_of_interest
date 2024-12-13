from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db  # Changed from ....core
from app.services.geofencing_service import GeofencingService  # Changed from ....services 