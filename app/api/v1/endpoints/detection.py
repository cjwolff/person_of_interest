from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db  # Changed from ....core
from app.models.detection import DetectionDB, FaceDetection  # Changed from ....models
from app.services.face_detection_service import FaceDetectionService  # Changed from ....services 