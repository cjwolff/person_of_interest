import pytest
import numpy as np
from app.ml_engine import MLEngine  # Changed from ...app
from app.services.face_detection_service import FaceDetectionService
from app.services.object_detection_service import ObjectDetectionService
from app.services.tracking_service import TrackingService 