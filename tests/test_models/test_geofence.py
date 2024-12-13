import pytest
from datetime import datetime
from app.models.geofence import GeofenceZone, GeofenceEvent  # Changed from ...app
from app.core.database import get_db  # Changed from ...app 