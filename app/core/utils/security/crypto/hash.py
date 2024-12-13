import hashlib
import hmac
from app.core.config import get_settings  # Changed from ....config
from app.core.metrics import HASH_ERROR_COUNT  # Changed from ....metrics

settings = get_settings() 