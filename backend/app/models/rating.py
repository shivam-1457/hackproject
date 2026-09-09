import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base

class Rating(Base):
    __tablename__ = "ratings"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    consumer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=True)

    rating_score = Column(Float, nullable=False) # 1.0 to 5.0
    review_text = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    product = relationship("Product", back_populates="ratings")
    consumer = relationship("User", back_populates="ratings")
