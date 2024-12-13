from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin  # Changed from .base
from app.core.config import get_settings  # Changed from ..core