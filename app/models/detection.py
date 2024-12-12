from sqlalchemy import Column, Integer, String, Float, JSON, ForeignKey
from .base import Base, TimestampMixin
from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime

class FaceLandmarks(BaseModel):
    x: float
    y: float

class Detection(BaseModel):
    bbox: List[float]
    confidence: float
    class_name: str
    class_id: Optional[int] = None
    landmarks: Optional[List[FaceLandmarks]] = None
    trackId: Optional[str] = None

class DetectionResponse(BaseModel):
    faces: List[Dict]
    objects: List[Dict]
    ar_data: Dict
    behavior_analysis: Dict
    geofencing_alerts: List[Dict]

class DetectionDB(Base, TimestampMixin):
    __tablename__ = "detections"
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(String, nullable=False)
    frame_id = Column(String, nullable=False)
    object_type = Column(String, nullable=False)
    confidence = Column(Float, nullable=False)
    bbox = Column(JSON, nullable=False)  # {x, y, width, height}
    detection_metadata = Column(JSON, nullable=True)

class FaceDetection(Base, TimestampMixin):
    __tablename__ = "face_detections"
    
    id = Column(Integer, primary_key=True, index=True)
    detection_id = Column(Integer, ForeignKey("detections.id"))
    face_encoding = Column(JSON, nullable=False)
    landmarks = Column(JSON, nullable=True)
    face_metadata = Column(JSON, nullable=True)