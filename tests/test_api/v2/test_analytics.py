import pytest
from fastapi.testclient import TestClient
from app.main import app  # Changed from ....app
from app.services.analytics_service import AnalyticsService  # Changed from ....services 