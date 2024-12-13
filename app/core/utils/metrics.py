from prometheus_client import Counter, Histogram
from app.core.config import get_settings  # Changed from ..config

settings = get_settings() 