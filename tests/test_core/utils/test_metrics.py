import pytest
from prometheus_client import Counter, Histogram
from app.core.utils.metrics import track_latency, count_errors 