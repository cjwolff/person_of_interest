from sqlalchemy import Column, Integer, String, JSON, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.models.base import Base, TimestampMixin
from app.core.config import get_settings

class BehaviorPattern(Base, TimestampMixin):
    __tablename__ = "behavior_patterns"
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(String, nullable=False)
    movement_pattern = Column(JSON, nullable=False)
    interaction_pattern = Column(JSON, nullable=False)
    anomalies = Column(JSON, nullable=True)
    risk_score = Column(Float, nullable=False)