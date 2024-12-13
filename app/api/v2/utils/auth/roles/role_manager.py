from typing import Dict, List, Optional
from fastapi import HTTPException
from app.core.config import get_settings  # Changed from ......core
from app.core.metrics import ROLE_ERROR_COUNT  # Changed from ......core

settings = get_settings() 