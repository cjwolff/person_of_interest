from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional

class Settings(BaseSettings):
    # Existing Database Configuration
    POSTGRES_USER: str = "surveillance_user"
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "surveillance_db"
    
    # New Security Settings (with defaults)
    SECRET_KEY: str = "0ur0buroS8888"  # Change in production!
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_DAYS: int = 1
    
    # WebSocket Configuration
    WS_PING_INTERVAL: int = 30
    WS_CONNECTION_TIMEOUT: int = 60

    class Config:
        env_file = ".env"
        case_sensitive = True

    @property
    def database_url(self) -> str:
        """Get the database connection URL"""
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

@lru_cache()
def get_settings() -> Settings:
    return Settings() 