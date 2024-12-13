import numpy as np
from typing import List, Dict, Optional, Tuple
import asyncio
import logging
from datetime import datetime, timedelta
from shapely.geometry import Point, Polygon, box
from app.core.config import get_settings
from app.core.metrics import ERROR_COUNT
from ..models.geofence import GeofenceZone, GeofenceEvent

settings = get_settings()
logger = logging.getLogger(__name__)

class GeofencingService:
    def __init__(self):
        try:
            self.processing_lock = asyncio.Lock()
            self.zones: Dict[str, Dict] = {}  # zone_id -> zone_data
            self.active_alerts: Dict[str, Dict] = {}  # alert_id -> alert_data
            self.last_cleanup = datetime.now()
            self.cleanup_interval = timedelta(minutes=5)
            self.alert_timeout = timedelta(minutes=1)
            
        except Exception as e:
            logger.error(f"Failed to initialize GeofencingService: {e}")
            raise

    async def add_zone(self, zone_data: Dict) -> str:
        """Add or update geofence zone"""
        try:
            async with self.processing_lock:
                zone_id = zone_data.get("zone_id", str(len(self.zones)))
                coordinates = zone_data["boundaries"]
                
                # Create polygon from coordinates
                if len(coordinates) >= 3:
                    polygon = Polygon(coordinates)
                else:
                    # Create circular zone if less than 3 points
                    center = coordinates[0]
                    radius = zone_data.get("radius", 100)  # meters
                    polygon = self._create_circular_zone(center, radius)
                
                self.zones[zone_id] = {
                    "polygon": polygon,
                    "type": zone_data.get("zone_type", "restricted"),
                    "risk_level": zone_data.get("risk_level", 1.0),
                    "metadata": zone_data.get("metadata", {}),
                    "created_at": datetime.now()
                }
                
                return zone_id
                
        except Exception as e:
            logger.error(f"Error adding geofence zone: {e}")
            raise

    async def check_violations(self, tracked_objects: List[Dict]) -> List[Dict]:
        """Check for geofencing violations"""
        try:
            async with self.processing_lock:
                current_time = datetime.now()
                violations = []
                
                for obj in tracked_objects:
                    if "bbox" not in obj:
                        continue
                        
                    center = self._get_object_center(obj["bbox"])
                    point = Point(center)
                    
                    # Check each zone
                    for zone_id, zone in self.zones.items():
                        if zone["polygon"].contains(point):
                            violation = {
                                "type": "zone_violation",
                                "zone_id": zone_id,
                                "zone_type": zone["type"],
                                "object_id": obj.get("track_id"),
                                "object_type": obj.get("class_name", "unknown"),
                                "location": center,
                                "risk_level": zone["risk_level"],
                                "timestamp": current_time.isoformat()
                            }
                            violations.append(violation)
                            await self._create_alert(violation)
                
                # Cleanup old alerts
                if current_time - self.last_cleanup > self.cleanup_interval:
                    await self._cleanup_old_alerts(current_time)
                    self.last_cleanup = current_time
                
                return violations
                
        except Exception as e:
            logger.error(f"Error checking geofence violations: {e}")
            return []

    async def get_active_alerts(self) -> List[Dict]:
        """Get list of active geofencing alerts"""
        try:
            async with self.processing_lock:
                current_time = datetime.now()
                active_alerts = []
                
                for alert_id, alert in self.active_alerts.items():
                    if current_time - alert["created_at"] <= self.alert_timeout:
                        active_alerts.append({
                            "alert_id": alert_id,
                            **alert["data"]
                        })
                
                return active_alerts
                
        except Exception as e:
            logger.error(f"Error getting active alerts: {e}")
            return []

    def _get_object_center(self, bbox: List[float]) -> Tuple[float, float]:
        """Calculate center point of object bounding box"""
        try:
            x1, y1, x2, y2 = bbox
            return ((x1 + x2) / 2, (y1 + y2) / 2)
        except Exception as e:
            logger.error(f"Error calculating object center: {e}")
            return (0.0, 0.0)

    def _create_circular_zone(self, center: Tuple[float, float], radius: float) -> Polygon:
        """Create circular geofence zone"""
        try:
            # Create box that bounds the circle
            x, y = center
            bounds = box(x - radius, y - radius, x + radius, y + radius)
            return bounds
        except Exception as e:
            logger.error(f"Error creating circular zone: {e}")
            raise

    async def _create_alert(self, violation: Dict):
        """Create new geofencing alert"""
        try:
            alert_id = f"{violation['zone_id']}_{violation['object_id']}_{datetime.now().timestamp()}"
            self.active_alerts[alert_id] = {
                "created_at": datetime.now(),
                "data": violation
            }
        except Exception as e:
            logger.error(f"Error creating alert: {e}")

    async def _cleanup_old_alerts(self, current_time: datetime):
        """Remove expired alerts"""
        try:
            expired_alerts = []
            for alert_id, alert in self.active_alerts.items():
                if current_time - alert["created_at"] > self.alert_timeout:
                    expired_alerts.append(alert_id)
                    
            for alert_id in expired_alerts:
                del self.active_alerts[alert_id]
                
        except Exception as e:
            logger.error(f"Error cleaning up alerts: {e}")

    async def cleanup(self):
        """Cleanup service resources"""
        try:
            self.zones.clear()
            self.active_alerts.clear()
        except Exception as e:
            logger.error(f"Error in geofencing cleanup: {e}") 