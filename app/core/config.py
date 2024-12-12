from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional

class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Database
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    
    # WebSocket
    WS_HOST: str = "0.0.0.0"
    WS_PORT: int = 8000
    WS_HEARTBEAT_INTERVAL: int = 30
    MAX_CONNECTIONS_PER_CLIENT: int = 1
    
    # ML Model Settings
    YOLO_MODEL_PATH: str = "yolov8n.pt"
    FACE_MODEL_PATH: str = "models/dlib_face_recognition_resnet_model_v1.dat"
    
    # Performance
    FRAME_PROCESSING_BATCH_SIZE: int = 4
    MAX_CONCURRENT_PROCESSORS: int = 4
    
    # Video Processing
    MAX_VIDEO_DIMENSION: int = 1280
    JPEG_QUALITY: int = 85
    
    # Geofencing
    MAX_GEOFENCE_RADIUS_METERS: float = 1000.0
    
    # CORS settings
    CORS_ORIGINS: list[str] = ["*"]
    CORS_ALLOW_METHODS: list[str] = ["*"]
    CORS_ALLOW_HEADERS: list[str] = ["*"]
    
    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Authentication settings
    SECRET_KEY: str = "0ur0buroS8888"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_DAYS: int = 1
    WS_PING_INTERVAL: int = 30
    WS_CONNECTION_TIMEOUT: int = 60

    model_config = {
        "env_file": ".env",
        "extra": "allow",
        "case_sensitive": True
    }

@lru_cache()
def get_settings() -> Settings:
    return Settings() 