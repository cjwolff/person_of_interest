from typing import Dict, List, Optional
from datetime import datetime, timedelta
import numpy as np
from app.core.config import get_settings
from app.core.metrics import ERROR_COUNT
import logging
import asyncio
from collections import defaultdict

logger = logging.getLogger(__name__)
settings = get_settings()

class BehaviorAnalyzer:
    """Consolidated behavior analysis functionality"""
    def __init__(self):
        self.processing_lock = asyncio.Lock()
        self._init_tracking()
        self._init_thresholds()
        
    def _init_tracking(self):
        self.track_history = defaultdict(list)
        self.behavior_patterns = defaultdict(list)
        self.interaction_history = defaultdict(list)
        self.last_cleanup = datetime.now()
        self.cleanup_interval = timedelta(seconds=300)
        self.max_history_age = timedelta(seconds=60)
        
    def _init_thresholds(self):
        self.risk_thresholds = {
            "proximity": 50.0,
            "speed": 100.0,
            "direction_change": np.pi/4,
            "dwell_time": 5.0
        } 