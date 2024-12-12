from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class FrameRequest(BaseModel):
    image: str  # base64 encoded image
    width: int
    height: int
    format: str = Field(default='jpeg')  # Using Field for better validation
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

    class Config:
        json_schema_extra = {
            "example": {
                "image": "base64_encoded_string",
                "width": 1280,
                "height": 720,
                "format": "jpeg",
                "metadata": {
                    "camera_info": {
                        "format_original": "bgra8888",
                        "platform": "ios"
                    }
                }
            }
        }