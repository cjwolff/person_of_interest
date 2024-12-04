from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from .base import Base
from datetime import datetime

class PhotoNote(Base):
    __tablename__ = "photo_notes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    photo_url = Column(String, nullable=False)
    note = Column(String)
    type = Column(String, nullable=False)  # face, landmark, object
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    address = Column(String)
    faces = Column(JSON)  # Stores face detection data
    objects = Column(JSON)  # Stores object detection data
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="photo_notes")
    behavior_analyses = relationship("BehaviorAnalysis", back_populates="photo_note")
    alerts = relationship("Alert", back_populates="target")