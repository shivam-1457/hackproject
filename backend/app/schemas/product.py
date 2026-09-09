from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field

class ProductBase(BaseModel):
    title: str
    description: Optional[str] = None
    category: str
    unit: str = "kg"
    price_per_unit: float = Field(..., gt=0)
    stock_quantity: float = Field(..., ge=0)
    harvest_date: Optional[str] = None
    image_url: Optional[str] = None
    is_organic: bool = False

    farm_location_name: Optional[str] = None
    farm_lat: Optional[float] = None
    farm_lng: Optional[float] = None

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    unit: Optional[str] = None
    price_per_unit: Optional[float] = None
    stock_quantity: Optional[float] = None
    harvest_date: Optional[str] = None
    image_url: Optional[str] = None
    is_organic: Optional[bool] = None
    farm_location_name: Optional[str] = None
    farm_lat: Optional[float] = None
    farm_lng: Optional[float] = None
    is_active: Optional[bool] = None

class FarmerSimpleResponse(BaseModel):
    id: int
    full_name: str
    farm_name: Optional[str] = None
    farm_city: Optional[str] = None
    farm_state: Optional[str] = None
    farm_lat: Optional[float] = None
    farm_lng: Optional[float] = None

    class Config:
        from_attributes = True

class ProductResponse(ProductBase):
    id: int
    farmer_id: int
    farmer: Optional[FarmerSimpleResponse] = None
    average_rating: float = 0.0
    total_reviews: int = 0
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    distance_km: Optional[float] = None # Computed when user passes coordinates

    class Config:
        from_attributes = True
