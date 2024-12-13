from fastapi import APIRouter, Response
from app.core.metrics import WEBSOCKET_CONNECTIONS, ERROR_COUNT  # Changed from ....core
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

router = APIRouter() 