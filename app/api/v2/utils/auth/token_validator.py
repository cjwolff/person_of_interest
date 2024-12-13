from fastapi import HTTPException, status
from app.core.config import get_settings  # Changed from .....core
from app.core.metrics import TOKEN_VALIDATION_ERROR_COUNT  # Changed from .....core
from app.core.utils.security.token import verify_token  # Changed from .....core

settings = get_settings() 