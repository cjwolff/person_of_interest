from cryptography.fernet import Fernet
from app.core.config import get_settings  # Changed from ...config
from app.core.metrics import ENCRYPTION_ERROR_COUNT  # Changed from ...metrics

settings = get_settings() 