import pytest
from fastapi.testclient import TestClient
from app.main import app  # Changed from ...app
from app.core.websocket import WebSocketManager  # Changed from ...core 