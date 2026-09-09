from datetime import datetime, timezone
from sqlalchemy import String, Integer, Float, Boolean, DateTime, ForeignKey, Text, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base

def now(): return datetime.now(timezone.utc)

class User(Base):
    __tablename__="users"
    id: Mapped[int]=mapped_column(Integer,primary_key=True)
    name: Mapped[str]=mapped_column(String(120))
    email: Mapped[str]=mapped_column(String(255),unique=True,index=True)
    phone: Mapped[str|None]=mapped_column(String(30),unique=True,nullable=True)
    password_hash: Mapped[str]=mapped_column(String(255))
    role: Mapped[str]=mapped_column(String(20),default="consumer")
    is_verified: Mapped[bool]=mapped_column(Boolean,default=False)
    is_active: Mapped[bool]=mapped_column(Boolean,default=True)
    latitude: Mapped[float|None]=mapped_column(Float,nullable=True)
    longitude: Mapped[float|None]=mapped_column(Float,nullable=True)
    address: Mapped[str|None]=mapped_column(String(500),nullable=True)
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)
    products=relationship("Product",back_populates="farmer")
    orders=relationship("Order",back_populates="consumer",foreign_keys="Order.consumer_id")
    reviews=relationship("Review",back_populates="consumer")

class VerificationToken(Base):
    __tablename__="verification_tokens"
    id: Mapped[int]=mapped_column(Integer,primary_key=True)
    user_id: Mapped[int]=mapped_column(ForeignKey("users.id",ondelete="CASCADE"))
    token: Mapped[str]=mapped_column(String(255),unique=True,index=True)
    expires_at: Mapped[datetime]=mapped_column(DateTime(timezone=True))
    used: Mapped[bool]=mapped_column(Boolean,default=False)

class PasswordResetToken(Base):
    __tablename__="password_reset_tokens"
    id: Mapped[int]=mapped_column(Integer,primary_key=True)
    user_id: Mapped[int]=mapped_column(ForeignKey("users.id",ondelete="CASCADE"))
    token: Mapped[str]=mapped_column(String(255),unique=True,index=True)
    expires_at: Mapped[datetime]=mapped_column(DateTime(timezone=True))
    used: Mapped[bool]=mapped_column(Boolean,default=False)

class Product(Base):
    __tablename__="products"
    id: Mapped[int]=mapped_column(Integer,primary_key=True)
    farmer_id: Mapped[int]=mapped_column(ForeignKey("users.id",ondelete="CASCADE"))
    name: Mapped[str]=mapped_column(String(150))
    description: Mapped[str]=mapped_column(Text,default="")
    category: Mapped[str]=mapped_column(String(80))
    price: Mapped[float]=mapped_column(Numeric(10,2))
    stock: Mapped[int]=mapped_column(Integer,default=0)
    image_url: Mapped[str|None]=mapped_column(String(500),nullable=True)
    latitude: Mapped[float|None]=mapped_column(Float,nullable=True)
    longitude: Mapped[float|None]=mapped_column(Float,nullable=True)
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)
    farmer=relationship("User",back_populates="products")
    order_items=relationship("OrderItem",back_populates="product")
    reviews=relationship("Review",back_populates="product",cascade="all, delete-orphan")

class Order(Base):
    __tablename__="orders"
    id: Mapped[int]=mapped_column(Integer,primary_key=True)
    consumer_id: Mapped[int]=mapped_column(ForeignKey("users.id"))
    status: Mapped[str]=mapped_column(String(30),default="placed")
    payment_status: Mapped[str]=mapped_column(String(30),default="pending")
    payment_method: Mapped[str]=mapped_column(String(30),default="simulation")
    transaction_id: Mapped[str|None]=mapped_column(String(100),nullable=True)
    total_amount: Mapped[float]=mapped_column(Numeric(10,2),default=0)
    delivery_address: Mapped[str]=mapped_column(String(500))
    delivery_latitude: Mapped[float|None]=mapped_column(Float,nullable=True)
    delivery_longitude: Mapped[float|None]=mapped_column(Float,nullable=True)
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)
    updated_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now,onupdate=now)
    consumer=relationship("User",back_populates="orders",foreign_keys=[consumer_id])
    items=relationship("OrderItem",back_populates="order",cascade="all, delete-orphan")
    complaint=relationship("Complaint",back_populates="order",uselist=False)

class OrderItem(Base):
    __tablename__="order_items"
    id: Mapped[int]=mapped_column(Integer,primary_key=True)
    order_id: Mapped[int]=mapped_column(ForeignKey("orders.id",ondelete="CASCADE"))
    product_id: Mapped[int]=mapped_column(ForeignKey("products.id"))
    quantity: Mapped[int]=mapped_column(Integer)
    unit_price: Mapped[float]=mapped_column(Numeric(10,2))
    order=relationship("Order",back_populates="items")
    product=relationship("Product",back_populates="order_items")

class Review(Base):
    __tablename__="reviews"
    id: Mapped[int]=mapped_column(Integer,primary_key=True)
    product_id: Mapped[int]=mapped_column(ForeignKey("products.id",ondelete="CASCADE"))
    consumer_id: Mapped[int]=mapped_column(ForeignKey("users.id",ondelete="CASCADE"))
    rating: Mapped[int]=mapped_column(Integer)
    comment: Mapped[str]=mapped_column(Text,default="")
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)
    product=relationship("Product",back_populates="reviews")
    consumer=relationship("User",back_populates="reviews")

class Complaint(Base):
    __tablename__="complaints"
    id: Mapped[int]=mapped_column(Integer,primary_key=True)
    order_id: Mapped[int|None]=mapped_column(ForeignKey("orders.id",ondelete="SET NULL"),nullable=True)
    raised_by: Mapped[int]=mapped_column(ForeignKey("users.id"))
    against_user_id: Mapped[int|None]=mapped_column(ForeignKey("users.id"),nullable=True)
    subject: Mapped[str]=mapped_column(String(200))
    description: Mapped[str]=mapped_column(Text)
    status: Mapped[str]=mapped_column(String(30),default="open")
    admin_note: Mapped[str|None]=mapped_column(Text,nullable=True)
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)
    order=relationship("Order",back_populates="complaint")
