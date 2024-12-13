from fastapi import APIRouter, Depends, HTTPException
from app.core.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])

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