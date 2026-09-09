from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

class OrderItemCreate(BaseModel):
    product_id: int
    quantity: float = Field(..., gt=0)

class OrderCreate(BaseModel):
    items: List[OrderItemCreate]
    shipping_address: str
    shipping_city: str
    shipping_state: str
    shipping_pincode: str
    shipping_notes: Optional[str] = None
    payment_method: str = "UPI_SIMULATION" # UPI_SIMULATION, CARD_SIMULATION, NET_BANKING, COD

class PaymentSimulateRequest(BaseModel):
    payment_method: str = "UPI_SIMULATION"
    upi_id: Optional[str] = None
    card_last4: Optional[str] = None

class OrderStatusUpdate(BaseModel):
    status: str # CONFIRMED, SHIPPED, DELIVERED, CANCELLED

class OrderItemResponse(BaseModel):
    id: int
    product_id: int
    farmer_id: int
    product_title: str
    quantity: float
    unit: str
    unit_price: float
    subtotal: float
    farm_lat: Optional[float] = None
    farm_lng: Optional[float] = None
    farm_name: Optional[str] = None
    farm_location: Optional[str] = None

    class Config:
        from_attributes = True

class OrderResponse(BaseModel):
    id: int
    consumer_id: int
    total_amount: float
    delivery_fee: float
    grand_total: float
    status: str
    payment_status: str
    payment_method: Optional[str] = None
    payment_transaction_id: Optional[str] = None
    payment_timestamp: Optional[datetime] = None

    shipping_address: str
    shipping_city: str
    shipping_state: str
    shipping_pincode: str
    shipping_notes: Optional[str] = None

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    items: List[OrderItemResponse] = []

    class Config:
        from_attributes = True
