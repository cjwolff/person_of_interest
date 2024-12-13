from passlib.context import CryptContext
from app.core.config import get_settings  # Changed from ....config
from app.core.metrics import PASSWORD_ERROR_COUNT  # Changed from ....metrics

settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto") 