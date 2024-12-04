from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, Enum, Boolean
from sqlalchemy.orm import relationship
from .base import Base
from datetime import datetime
from .behavior_analysis import RiskLevel

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    target_id = Column(Integer, ForeignKey("photo_notes.id"))
    distance = Column(Float, nullable=False)
    risk_level = Column(Enum(RiskLevel), nullable=False)
    is_dismissed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="alerts")
    target = relationship("PhotoNote", back_populates="alerts")