from prometheus_client import Counter, Histogram
from app.core.config import get_settings  # Changed from ....core
from app.core.metrics import REQUEST_COUNT  # Changed from ....core

settings = get_settings() 