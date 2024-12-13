from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.core.auth import verify_token  # Changed from ....core
from app.models.user import User  # Changed from ....models 