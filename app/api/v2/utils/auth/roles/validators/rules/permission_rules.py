from typing import List, Dict
from fastapi import HTTPException
from app.core.config import get_settings  # Changed from ........core
from app.core.metrics import PERMISSION_RULES_ERROR_COUNT  # Changed from ........core

settings = get_settings() 