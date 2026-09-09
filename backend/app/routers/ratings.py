from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models.rating import Rating
from app.models.product import Product
from app.models.user import User
from app.schemas.rating import RatingCreate, RatingResponse
from app.utils.dependencies import require_consumer

router = APIRouter(prefix="/api/ratings", tags=["Product Ratings & Reviews"])

@router.post("", response_model=RatingResponse, status_code=status.HTTP_201_CREATED)
def submit_rating(
    data: RatingCreate,
    consumer: User = Depends(require_consumer),
    db: Session = Depends(get_db)
):
    prod = db.query(Product).filter(Product.id == data.product_id).first()
    if not prod:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")

    # Create new rating
    new_rating = Rating(
        product_id=data.product_id,
        consumer_id=consumer.id,
        order_id=data.order_id,
        rating_score=data.rating_score,
        review_text=data.review_text
    )
    db.add(new_rating)
    db.commit()

    # Recalculate average rating and total count
    stats = db.query(
        func.avg(Rating.rating_score).label("avg_rating"),
        func.count(Rating.id).label("total_count")
    ).filter(Rating.product_id == data.product_id).first()

    prod.average_rating = round(float(stats.avg_rating or 0.0), 1)
    prod.total_reviews = int(stats.total_count or 0)
    db.commit()

    db.refresh(new_rating)
    return {
        "id": new_rating.id,
        "product_id": new_rating.product_id,
        "consumer_id": new_rating.consumer_id,
        "order_id": new_rating.order_id,
        "rating_score": new_rating.rating_score,
        "review_text": new_rating.review_text,
        "created_at": new_rating.created_at,
        "consumer_name": consumer.full_name
    }

@router.get("/product/{product_id}", response_model=List[RatingResponse])
def get_product_reviews(
    product_id: int,
    db: Session = Depends(get_db)
):
    ratings = db.query(Rating).filter(Rating.product_id == product_id).order_by(Rating.created_at.desc()).all()
    results = []
    for r in ratings:
        results.append({
            "id": r.id,
            "product_id": r.product_id,
            "consumer_id": r.consumer_id,
            "order_id": r.order_id,
            "rating_score": r.rating_score,
            "review_text": r.review_text,
            "created_at": r.created_at,
            "consumer_name": r.consumer.full_name if r.consumer else "Customer"
        })
    return results
