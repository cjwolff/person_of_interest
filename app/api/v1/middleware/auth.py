from fastapi import Request, HTTPException
from app.core.auth import verify_token  # Changed from ....core
from app.core.config import get_settings  # Changed from ....core 