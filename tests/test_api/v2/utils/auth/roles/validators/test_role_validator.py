import pytest
from fastapi import HTTPException
from app.api.v2.utils.auth.roles.validators.role_validator import RoleValidator  # Changed from ........api
from app.core.utils.security.auth.jwt import generate_jwt  # Changed from ........core 