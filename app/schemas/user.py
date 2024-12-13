from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from app.core.config import get_settings  # Changed from ..core 