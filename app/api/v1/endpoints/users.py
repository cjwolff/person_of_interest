from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db  # Changed from ....core
from app.models.user import User  # Changed from ....models 