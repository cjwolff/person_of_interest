import pytest
from fastapi import HTTPException
from app.api.v1.dependencies.auth import get_current_user 