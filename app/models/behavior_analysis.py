from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON, Enum
from sqlalchemy.orm import relationship
from .base import Base
from datetime import datetime
import enum

class RiskLevel(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class BehaviorAnalysis(Base):
    __tablename__ = "behavior_analyses"

    id = Column(Integer, primary_key=True, index=True)
    photo_note_id = Column(Integer, ForeignKey("photo_notes.id"))
    timestamp = Column(DateTime, default=datetime.utcnow)
    risk_level = Column(Enum(RiskLevel), nullable=False)
    behaviors = Column(JSON)  # List of detected behaviors
    confidence = Column(Float, nullable=False)
    pose_data = Column(JSON)  # Stores raw pose data
    notes = Column(String)

    photo_note = relationship("PhotoNote", back_populates="behavior_analyses")
    