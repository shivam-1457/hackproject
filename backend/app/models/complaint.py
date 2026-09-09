import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base

class ComplaintIssueType(str):
    DAMAGED_PRODUCE = "Damaged Produce / Crushed during Transit"
    ROTTEN_EXPIRED = "Rotten, Spoiled or Expired"
    WRONG_ITEM = "Wrong Item or Quantity Mismatch"
    POOR_QUALITY = "Substandard Quality / Not as Described"
    DELAYED_DELIVERY = "Severely Delayed Delivery"

class ComplaintStatus(str):
    OPEN = "OPEN"
    UNDER_INVESTIGATION = "UNDER_INVESTIGATION"
    RESOLVED_REFUND = "RESOLVED_REFUND"
    RESOLVED_REPLACED = "RESOLVED_REPLACED"
    REJECTED = "REJECTED"

class Complaint(Base):
    __tablename__ = "complaints"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    order_item_id = Column(Integer, ForeignKey("order_items.id"), nullable=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    consumer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    farmer_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    issue_type = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    proof_image_url = Column(String(500), nullable=True)
    requested_resolution = Column(String(50), default="REFUND", nullable=False) # REFUND, REPLACEMENT, APOLOGY

    status = Column(String(50), default=ComplaintStatus.OPEN, nullable=False)
    resolution_notes = Column(Text, nullable=True)
    admin_verdict = Column(Text, nullable=True)
    arbitrated_by = Column(String(100), nullable=True) # e.g. "Admin Desk", "Platform Ombudsman"
    resolved_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relationships
    order = relationship("Order", back_populates="complaints")
    product = relationship("Product", back_populates="complaints")
    consumer = relationship("User", foreign_keys=[consumer_id], back_populates="complaints")
    farmer = relationship("User", foreign_keys=[farmer_id], back_populates="farmer_complaints")
