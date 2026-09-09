from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field

class RatingCreate(BaseModel):
    product_id: int
    order_id: Optional[int] = None
    rating_score: float = Field(..., ge=1.0, le=5.0)
    review_text: Optional[str] = None

class RatingResponse(BaseModel):
    id: int
    product_id: int
    consumer_id: int
    order_id: Optional[int] = None
    rating_score: float
    review_text: Optional[str] = None
    created_at: Optional[datetime] = None
    consumer_name: Optional[str] = None

    class Config:
        from_attributes = True
