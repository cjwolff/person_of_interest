from typing import Dict, List, Optional, Any, Callable
from fastapi import HTTPException
from app.core.config import get_settings  # Changed from ...........core
from app.core.metrics import EVALUATOR_RULES_ERROR_COUNT  # Changed from ...........core

settings = get_settings() 