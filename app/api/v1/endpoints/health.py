from fastapi import APIRouter
from app.core.config import get_settings  # Changed from ....core
from app.core.metrics import HEALTH_CHECK  # Changed from ....core

settings = get_settings()
router = APIRouter() 