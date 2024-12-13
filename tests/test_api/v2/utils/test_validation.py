import pytest
from fastapi import HTTPException
from app.api.v2.utils.validation import validate_request  # Changed from .....api
from app.core.config import get_settings  # Changed from .....core 