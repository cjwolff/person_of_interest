from prometheus_client import Counter, Histogram, Gauge
import time
from app.core.config import get_settings

settings = get_settings()

# Metrics
WEBSOCKET_CONNECTIONS = Gauge(
    'websocket_connections_total',
    'Number of active WebSocket connections'
)

FRAME_PROCESSING_TIME = Histogram(
    'frame_processing_seconds',
    'Time spent processing frames',
    buckets=(0.1, 0.5, 1, 2, 5)
)

DETECTION_COUNT = Counter(
    'detections_total',
    'Total number of detections',
    ['type']
)

ERROR_COUNT = Counter(
    'errors_total',
    'Total number of errors',
    ['service', 'type']
)

class MetricsMiddleware:
    async def __call__(self, request, call_next):
        start_time = time.time()
        response = await call_next(request)
        
        # Record request duration
        request_time = time.time() - start_time
        FRAME_PROCESSING_TIME.observe(request_time)
        
        return response 