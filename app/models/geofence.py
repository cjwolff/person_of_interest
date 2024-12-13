from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.models.base import Base, TimestampMixin
from app.core.config import get_settings

class GeofenceZone(Base, TimestampMixin):
    __tablename__ = "geofence_zones"
    
    id = Column(Integer, primary_key=True, index=True)
    zone_id = Column(String, nullable=False)
    name = Column(String, nullable=False)
    boundaries = Column(JSON, nullable=False)  # [{lat, lng}, ...]
    zone_type = Column(String, nullable=False)  # restricted, safe, etc.
    risk_level = Column(Float, nullable=False)
    zone_metadata = Column(JSON, nullable=True)

class GeofenceEvent(Base, TimestampMixin):
    __tablename__ = "geofence_events"
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(String, nullable=False)
    geofence_id = Column(String, nullable=False)
    event_type = Column(String, nullable=False)  # enter, exit, dwell
    location = Column(JSON, nullable=False)  # {lat, lng}
    event_metadata = Column(JSON, nullable=True) 