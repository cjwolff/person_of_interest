from typing import Dict, Any
from fastapi import HTTPException
from app.core.config import get_settings  # Changed from ....core
from app.core.metrics import VALIDATION_ERROR_COUNT  # Changed from ....core

settings = get_settings() 