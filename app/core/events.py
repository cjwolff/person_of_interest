from typing import Callable
from fastapi import FastAPI
from app.core.websocket import WebSocketManager  # Changed from .websocket
from app.core.database import engine  # Changed from .database 