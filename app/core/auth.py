from fastapi import HTTPException, WebSocket
from typing import Optional, Dict
import jwt
from datetime import datetime, timedelta
from ..config import get_settings

settings = get_settings()

class WebSocketAuthManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.client_info: Dict[str, dict] = {}
        self.secret_key = settings.SECRET_KEY

    async def authenticate_connection(
        self, 
        websocket: WebSocket,
        client_id: Optional[str] = None,
        auth_token: Optional[str] = None,
        client_type: Optional[str] = None,
        capabilities: Optional[list] = None
    ) -> bool:
        if not all([client_id, auth_token, client_type]):
            return False

        try:
            # Verify JWT token
            payload = jwt.decode(auth_token, self.secret_key, algorithms=[settings.JWT_ALGORITHM])
            
            # Store client information
            self.client_info[client_id] = {
                "client_type": client_type,
                "capabilities": capabilities or [],
                "connected_at": datetime.utcnow(),
                "last_seen": datetime.utcnow()
            }
            
            return True
        except jwt.InvalidTokenError:
            return False

    def generate_client_token(self, client_id: str, expires_delta: timedelta = None) -> str:
        if expires_delta is None:
            expires_delta = timedelta(days=settings.JWT_EXPIRATION_DAYS)
            
        payload = {
            "sub": client_id,
            "exp": datetime.utcnow() + expires_delta,
            "iat": datetime.utcnow()
        }
        return jwt.encode(payload, self.secret_key, algorithm=settings.JWT_ALGORITHM) 