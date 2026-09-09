from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field

class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    full_name: str
    phone: Optional[str] = None
    role: str = "consumer" # "farmer" or "consumer"

    # Farmer fields
    farm_name: Optional[str] = None
    farm_address: Optional[str] = None
    farm_city: Optional[str] = None
    farm_state: Optional[str] = None
    farm_pincode: Optional[str] = None
    farm_lat: Optional[float] = None
    farm_lng: Optional[float] = None

    # Consumer fields
    delivery_address: Optional[str] = None
    delivery_city: Optional[str] = None
    delivery_state: Optional[str] = None
    delivery_pincode: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class VerifyEmailRequest(BaseModel):
    token: str

class ResendVerificationRequest(BaseModel):
    email: EmailStr

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    user_id: int
    full_name: str
    email: str
    is_verified: bool

class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    phone: Optional[str] = None
    role: str
    is_verified: bool

    farm_name: Optional[str] = None
    farm_address: Optional[str] = None
    farm_city: Optional[str] = None
    farm_state: Optional[str] = None
    farm_pincode: Optional[str] = None
    farm_lat: Optional[float] = None
    farm_lng: Optional[float] = None

    delivery_address: Optional[str] = None
    delivery_city: Optional[str] = None
    delivery_state: Optional[str] = None
    delivery_pincode: Optional[str] = None

    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
