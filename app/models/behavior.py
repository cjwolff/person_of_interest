from sqlalchemy import Column, Integer, String, Float, JSON, ForeignKey
from .base import Base, TimestampMixin

class BehaviorPattern(Base, TimestampMixin):
    __tablename__ = "behavior_patterns"
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(String, nullable=False)
    movement_pattern = Column(JSON, nullable=False)
    interaction_pattern = Column(JSON, nullable=False)
    anomalies = Column(JSON, nullable=True)
    risk_score = Column(Float, nullable=False)