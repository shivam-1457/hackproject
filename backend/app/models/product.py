import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base

class ProductCategory(str):
    GRAINS = "Grains & Cereals"
    VEGETABLES = "Fresh Vegetables"
    FRUITS = "Fresh Fruits"
    PULSES = "Pulses & Lentils"
    DAIRY = "Dairy & Organic Milk"
    SPICES = "Spices & Herbs"
    OTHER = "Other Produce"

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    farmer_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    title = Column(String(200), index=True, nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), index=True, default=ProductCategory.VEGETABLES, nullable=False)
    unit = Column(String(50), default="kg", nullable=False) # kg, quintal, crate, dozen, liter
    price_per_unit = Column(Float, nullable=False)
    stock_quantity = Column(Float, default=0.0, nullable=False)
    harvest_date = Column(String(50), nullable=True)
    image_url = Column(String(500), nullable=True)
    is_organic = Column(Boolean, default=False)

    # Location info for produce
    farm_location_name = Column(String(200), nullable=True)
    farm_lat = Column(Float, nullable=True)
    farm_lng = Column(Float, nullable=True)

    # Aggregated rating cache
    average_rating = Column(Float, default=0.0)
    total_reviews = Column(Integer, default=0)

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relationships
    farmer = relationship("User", back_populates="products")
    ratings = relationship("Rating", back_populates="product", cascade="all, delete-orphan")
    order_items = relationship("OrderItem", back_populates="product")
    complaints = relationship("Complaint", back_populates="product")
