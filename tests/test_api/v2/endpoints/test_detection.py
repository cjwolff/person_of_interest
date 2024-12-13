import pytest
from fastapi.testclient import TestClient
from app.main import app  # Changed from .....app
from app.services.face_detection_service import FaceDetectionService  # Changed from .....services 