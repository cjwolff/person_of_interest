from typing import List, Dict, Any
from fastapi import HTTPException
from app.core.config import get_settings  # Changed from .........core
from app.core.metrics import PERMISSION_CONDITION_ERROR_COUNT  # Changed from .........core

settings = get_settings() 