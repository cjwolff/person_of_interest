from fastapi import Request
import time
import logging
from app.core.config import get_settings  # Changed from ....core
from app.core.metrics import REQUEST_LATENCY  # Changed from ....core

settings = get_settings()
logger = logging.getLogger(__name__) 