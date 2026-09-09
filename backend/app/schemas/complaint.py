from typing import Optional
from datetime import datetime
from pydantic import BaseModel

class ComplaintCreate(BaseModel):
    order_id: int
    product_id: Optional[int] = None
    issue_type: str # e.g. "Damaged Produce / Crushed during Transit"
    description: str
    proof_image_url: Optional[str] = None
    requested_resolution: str = "REFUND" # REFUND, REPLACEMENT, APOLOGY

class ComplaintUpdateStatus(BaseModel):
    status: str # UNDER_INVESTIGATION, RESOLVED_REFUND, RESOLVED_REPLACED, REJECTED
    resolution_notes: Optional[str] = None

class ComplaintArbitrate(BaseModel):
    status: str # RESOLVED_REFUND, RESOLVED_REPLACED, REJECTED, UNDER_INVESTIGATION
    admin_verdict: str
    resolution_notes: Optional[str] = None

class ComplaintResponse(BaseModel):
    id: int
    order_id: int
    order_item_id: Optional[int] = None
    product_id: Optional[int] = None
    consumer_id: int
    farmer_id: int
    issue_type: str
    description: str
    proof_image_url: Optional[str] = None
    requested_resolution: str
    status: str
    resolution_notes: Optional[str] = None
    admin_verdict: Optional[str] = None
    arbitrated_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
