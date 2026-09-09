import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base

class OrderStatus(str):
    PENDING_PAYMENT = "PENDING_PAYMENT"
    CONFIRMED = "CONFIRMED"
    SHIPPED = "SHIPPED"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"

class PaymentStatus(str):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    consumer_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    total_amount = Column(Float, nullable=False, default=0.0)
    delivery_fee = Column(Float, nullable=False, default=0.0)
    grand_total = Column(Float, nullable=False, default=0.0)

    status = Column(String(50), default=OrderStatus.PENDING_PAYMENT, nullable=False)

    # Payment details
    payment_status = Column(String(50), default=PaymentStatus.PENDING, nullable=False)
    payment_method = Column(String(50), default="UPI_SIMULATION", nullable=True) # UPI, Card, NetBanking
    payment_transaction_id = Column(String(100), nullable=True)
    payment_timestamp = Column(DateTime, nullable=True)

    # Shipping delivery snapshot
    shipping_address = Column(String(300), nullable=False)
    shipping_city = Column(String(100), nullable=False)
    shipping_state = Column(String(100), nullable=False)
    shipping_pincode = Column(String(20), nullable=False)
    shipping_notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relationships
    consumer = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    complaints = relationship("Complaint", back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    farmer_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    product_title = Column(String(200), nullable=False)
    quantity = Column(Float, nullable=False)
    unit = Column(String(50), nullable=False)
    unit_price = Column(Float, nullable=False)
    subtotal = Column(Float, nullable=False)

    # Relationships
    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")
    farmer = relationship("User")

    @property
    def farm_lat(self):
        if self.product and self.product.farm_lat:
            return self.product.farm_lat
        if self.farmer and self.farmer.farm_lat:
            return self.farmer.farm_lat
        return 19.9975

    @property
    def farm_lng(self):
        if self.product and self.product.farm_lng:
            return self.product.farm_lng
        if self.farmer and self.farmer.farm_lng:
            return self.farmer.farm_lng
        return 73.7898

    @property
    def farm_name(self):
        if self.farmer and self.farmer.farm_name:
            return self.farmer.farm_name
        return "Direct Kisan Agro Farm"

    @property
    def farm_location(self):
        if self.product and self.product.farm_location_name:
            return self.product.farm_location_name
        if self.farmer:
            parts = [p for p in [self.farmer.farm_city, self.farmer.farm_state] if p]
            return ", ".join(parts) if parts else "India"
        return "India"
