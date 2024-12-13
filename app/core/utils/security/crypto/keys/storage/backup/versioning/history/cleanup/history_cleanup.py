from datetime import datetime, timedelta
from typing import Dict, List, Optional
from app.core.config import get_settings  # Changed from ...........config
from app.core.metrics import HISTORY_CLEANUP_ERROR_COUNT  # Changed from ...........metrics

settings = get_settings() 