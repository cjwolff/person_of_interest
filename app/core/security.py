from datetime import datetime, timedelta
from typing import Optional
import jwt
from passlib.context import CryptContext
from app.core.config import get_settings  # Changed from .config

settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto") 