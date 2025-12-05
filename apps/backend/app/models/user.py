from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None

class User(BaseModel):
    id: str
    email: EmailStr
    full_name: Optional[str] = None
    role: str = "user"  # user, superadmin, ops, seo, content
    totp_enabled: bool = False
    totp_secret: Optional[str] = None
    created_at: datetime = datetime.utcnow
    saved_searches: List[dict] = []
    price_alerts: List[dict] = []
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "user123",
                "email": "user@example.com",
                "full_name": "John Doe",
                "role": "user",
                "totp_enabled": False
            }
        }
