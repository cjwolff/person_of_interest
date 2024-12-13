import pytest
from fastapi import HTTPException
from app.api.v2.utils.auth.token_validator import validate_token  # Changed from ......api
from app.core.utils.security.token import generate_token  # Changed from ......core 