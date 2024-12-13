import pytest
import numpy as np
import cv2
from app.services.ar_service import ARService  # Changed from ...app
from app.services.face_detection_service import FaceDetectionService
from app.services.object_detection_service import ObjectDetectionService 