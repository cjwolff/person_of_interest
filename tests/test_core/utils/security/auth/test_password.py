import pytest
from passlib.context import CryptContext
from app.core.utils.security.auth.password import verify_password, get_password_hash  # Changed from .....core 