import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, Enum
from sqlalchemy.orm import relationship
from app.database import Base

class UserRole(str):
    FARMER = "farmer"
    CONSUMER = "consumer"
    ADMIN = "admin"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(150), nullable=False)
    phone = Column(String(20), nullable=True)
    role = Column(String(20), default=UserRole.CONSUMER, nullable=False) # 'farmer', 'consumer', or 'admin'

    # Farmer specific details
    farm_name = Column(String(200), nullable=True)
    farm_address = Column(String(300), nullable=True)
    farm_city = Column(String(100), nullable=True)
    farm_state = Column(String(100), nullable=True)
    farm_pincode = Column(String(20), nullable=True)
    farm_lat = Column(Float, nullable=True)
    farm_lng = Column(Float, nullable=True)

    # Consumer delivery details
    delivery_address = Column(String(300), nullable=True)
    delivery_city = Column(String(100), nullable=True)
    delivery_state = Column(String(100), nullable=True)
    delivery_pincode = Column(String(20), nullable=True)

    # Email verification system
    is_verified = Column(Boolean, default=False)
    verification_token = Column(String(255), nullable=True, index=True)
    verification_token_expires = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relationships
    products = relationship("Product", back_populates="farmer", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="consumer", cascade="all, delete-orphan")
    ratings = relationship("Rating", back_populates="consumer", cascade="all, delete-orphan")
    complaints = relationship("Complaint", foreign_keys="[Complaint.consumer_id]", back_populates="consumer")
    farmer_complaints = relationship("Complaint", foreign_keys="[Complaint.farmer_id]", back_populates="farmer")
