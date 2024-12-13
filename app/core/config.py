from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List
import secrets
import logging

class Settings(BaseSettings):
    # Database Configuration
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "surveillance_db"
    DB_ECHO_LOG: bool = False
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 1800
    DB_STATEMENT_TIMEOUT: int = 30000  # ms
    DB_IDLE_TIMEOUT: int = 60000  # ms
    
    # Security Settings
    SECRET_KEY: str = secrets.token_urlsafe(32)
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_DAYS: int = 1
    CORS_ORIGINS: List[str] = ["*"]
    
    # WebSocket Configuration
    WS_HOST: str = "0.0.0.0"
    WS_PORT: int = 8000
    WS_PING_INTERVAL: int = 30
    WS_CONNECTION_TIMEOUT: int = 60
    MAX_CONNECTIONS_PER_CLIENT: int = 3
    
    # ML Model Settings
    YOLO_MODEL_PATH: str = "yolov8n.pt"
    FACE_MODEL_PATH: str = "models/face_detection_model.dat"
    MIN_DETECTION_CONFIDENCE: float = 0.5
    
    # Video Processing Settings
    MAX_VIDEO_DIMENSION: int = 1280
    JPEG_QUALITY: int = 85
    MAX_FRAME_QUEUE_SIZE: int = 100
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        
    def configure_logging(self):
        """Configure logging with current settings"""
        logging.basicConfig(
            level=getattr(logging, self.LOG_LEVEL),
            format=self.LOG_FORMAT
        )

    @property
    def database_url(self) -> str:
        """Get the database connection URL"""
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    settings = Settings()
    settings.configure_logging()
    return settings 