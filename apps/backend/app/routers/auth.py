from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import Optional
import jwt
from datetime import datetime, timedelta
import bcrypt
import pyotp
from app.config import settings
from app.db.mongodb import get_users_collection
from app.models.user import User, UserCreate
import logging

logger = logging.getLogger(__name__)
router = APIRouter()
security = HTTPBearer()

class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    totp_code: Optional[str] = None

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: User
    requires_totp: bool = False

class TOTPSetupResponse(BaseModel):
    secret: str
    qr_code_url: str

def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash"""
    return bcrypt.checkpw(password.encode(), hashed.encode())

def create_access_token(user: User) -> str:
    """Create JWT access token"""
    payload = {
        "sub": user.id,
        "email": user.email,
        "role": user.role,
        "exp": datetime.utcnow() + timedelta(hours=24)
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")

def decode_token(token: str) -> dict:
    """Decode and verify JWT token"""
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Get current user from JWT token"""
    payload = decode_token(credentials.credentials)
    users_collection = get_users_collection()
    user_doc = await users_collection.find_one({"id": payload["sub"]})
    
    if not user_doc:
        raise HTTPException(status_code=401, detail="User not found")
    
    return User(**user_doc)

@router.post("/auth/register", response_model=User)
async def register(user_data: UserCreate):
    """Register new user"""
    users_collection = get_users_collection()
    
    # Check if user exists
    existing = await users_collection.find_one({"email": user_data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user
    user = User(
        id=str(uuid.uuid4()),
        email=user_data.email,
        full_name=user_data.full_name,
        role="user",
        created_at=datetime.utcnow()
    )
    
    # Hash password and store
    user_doc = user.dict()
    user_doc["password_hash"] = hash_password(user_data.password)
    
    await users_collection.insert_one(user_doc)
    
    logger.info(f"User registered: {user.email}")
    return user

@router.post("/auth/login", response_model=LoginResponse)
async def login(login_data: LoginRequest):
    """Login user and return JWT token"""
    users_collection = get_users_collection()
    
    # Find user
    user_doc = await users_collection.find_one({"email": login_data.email})
    if not user_doc:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Verify password
    if not verify_password(login_data.password, user_doc["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    user = User(**user_doc)
    
    # Check if TOTP is enabled
    if user.totp_enabled:
        if not login_data.totp_code:
            return LoginResponse(
                access_token="",
                user=user,
                requires_totp=True
            )
        
        # Verify TOTP
        totp = pyotp.TOTP(user.totp_secret)
        if not totp.verify(login_data.totp_code):
            raise HTTPException(status_code=401, detail="Invalid TOTP code")
    
    # Create token
    token = create_access_token(user)
    
    logger.info(f"User logged in: {user.email}")
    
    return LoginResponse(
        access_token=token,
        user=user,
        requires_totp=False
    )

@router.post("/auth/totp/setup", response_model=TOTPSetupResponse)
async def setup_totp(current_user: User = Depends(get_current_user)):
    """Setup TOTP 2FA for user"""
    # Generate TOTP secret
    secret = pyotp.random_base32()
    
    # Generate QR code URL
    totp = pyotp.TOTP(secret)
    qr_url = totp.provisioning_uri(
        name=current_user.email,
        issuer_name=settings.admin_totp_issuer
    )
    
    # Store secret (not enabled yet)
    users_collection = get_users_collection()
    await users_collection.update_one(
        {"id": current_user.id},
        {"$set": {"totp_secret": secret}}
    )
    
    return TOTPSetupResponse(secret=secret, qr_code_url=qr_url)

@router.post("/auth/totp/enable")
async def enable_totp(totp_code: str, current_user: User = Depends(get_current_user)):
    """Enable TOTP 2FA after verifying code"""
    users_collection = get_users_collection()
    user_doc = await users_collection.find_one({"id": current_user.id})
    
    if not user_doc.get("totp_secret"):
        raise HTTPException(status_code=400, detail="TOTP not set up")
    
    # Verify TOTP code
    totp = pyotp.TOTP(user_doc["totp_secret"])
    if not totp.verify(totp_code):
        raise HTTPException(status_code=400, detail="Invalid TOTP code")
    
    # Enable TOTP
    await users_collection.update_one(
        {"id": current_user.id},
        {"$set": {"totp_enabled": True}}
    )
    
    logger.info(f"TOTP enabled for user: {current_user.email}")
    
    return {"status": "success", "message": "TOTP enabled"}

@router.get("/auth/me", response_model=User)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current user info"""
    return current_user

import uuid
