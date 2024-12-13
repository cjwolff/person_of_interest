from datetime import datetime
from typing import Dict, List, Optional
from app.core.config import get_settings  # Changed from ..........config
from app.core.metrics import VERSION_HISTORY_ERROR_COUNT  # Changed from ..........metrics

settings = get_settings() 