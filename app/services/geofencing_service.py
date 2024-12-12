from typing import List, Dict
import numpy as np
import asyncio
from shapely.geometry import Point, Polygon

class GeofencingService:
    def __init__(self):
        self.processing_lock = asyncio.Lock()
        self.restricted_areas = []  # List of Polygon objects
        self.alert_zones = []  # List of Polygon objects with metadata
        
    async def check(self, tracked_objects: List[Dict]) -> List[Dict]:
        """Check for geofencing violations"""
        async with self.processing_lock:
            alerts = []
            
            for obj in tracked_objects:
                bbox = obj["bbox"]
                center_x = (bbox[0] + bbox[2]) / 2
                center_y = (bbox[1] + bbox[3]) / 2
                point = Point(center_x, center_y)
                
                # Check restricted areas
                for area in self.restricted_areas:
                    if area["polygon"].contains(point):
                        alerts.append({
                            "type": "restricted_area",
                            "object_id": obj.get("track_id"),
                            "object_type": obj["class_name"],
                            "location": [center_x, center_y],
                            "area_id": area["id"],
                            "severity": "high"
                        })
                
                # Check alert zones
                for zone in self.alert_zones:
                    if zone["polygon"].contains(point):
                        alerts.append({
                            "type": "alert_zone",
                            "object_id": obj.get("track_id"),
                            "object_type": obj["class_name"],
                            "location": [center_x, center_y],
                            "zone_id": zone["id"],
                            "severity": "medium"
                        })
            
            return alerts
    
    def add_restricted_area(self, points: List[List[float]], area_id: str):
        """Add a new restricted area"""
        self.restricted_areas.append({
            "id": area_id,
            "polygon": Polygon(points)
        })
    
    def add_alert_zone(self, points: List[List[float]], zone_id: str):
        """Add a new alert zone"""
        self.alert_zones.append({
            "id": zone_id,
            "polygon": Polygon(points)
        }) 