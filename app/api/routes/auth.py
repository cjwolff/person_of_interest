from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ...core.auth import WebSocketAuthManager

router = APIRouter(prefix="/auth", tags=["auth"])
auth_manager = WebSocketAuthManager()

class TokenRequest(BaseModel):
    client_id: str
    client_type: str = "mobile"
    capabilities: list[str] = []

@router.post("/token")
async def get_auth_token(request: TokenRequest):
    try:
        token = auth_manager.generate_client_token(
            client_id=request.client_id,
            client_type=request.client_type,
            capabilities=request.capabilities
        )
        return {"token": token}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) 