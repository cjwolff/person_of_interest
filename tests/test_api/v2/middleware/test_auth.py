import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.api.v2.middleware.auth import AuthMiddleware  # Changed from .....api
from app.core.auth import verify_token  # Changed from .....core 