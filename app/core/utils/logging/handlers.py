import logging
from logging.handlers import RotatingFileHandler
from app.core.config import get_settings  # Changed from ...config

settings = get_settings() 