from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.complaint import Complaint, ComplaintStatus
from app.models.order import Order, OrderItem
from app.models.product import Product
from app.models.user import User
from app.schemas.complaint import ComplaintCreate, ComplaintUpdateStatus, ComplaintResponse
from app.utils.dependencies import require_consumer, require_farmer, get_current_user

router = APIRouter(prefix="/api/complaints", tags=["Complaints & Disputes"])

@router.post("", response_model=ComplaintResponse, status_code=status.HTTP_201_CREATED)
def raise_complaint(
    data: ComplaintCreate,
    consumer: User = Depends(require_consumer),
    db: Session = Depends(get_db)
):
    # Verify order belongs to consumer
    order = db.query(Order).filter(Order.id == data.order_id, Order.consumer_id == consumer.id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found or unauthorized.")

    # Determine farmer_id and product_id
    farmer_id = None
    product_id = data.product_id

    if product_id:
        prod = db.query(Product).filter(Product.id == product_id).first()
        if prod:
            farmer_id = prod.farmer_id
    else:
        # If no specific product passed, pick the first farmer from order items
        first_item = db.query(OrderItem).filter(OrderItem.order_id == order.id).first()
        if first_item:
            farmer_id = first_item.farmer_id
            product_id = first_item.product_id

    if not farmer_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unable to identify farmer for this complaint.")

    new_complaint = Complaint(
        order_id=order.id,
        product_id=product_id,
        consumer_id=consumer.id,
        farmer_id=farmer_id,
        issue_type=data.issue_type,
        description=data.description,
        proof_image_url=data.proof_image_url,
        requested_resolution=data.requested_resolution,
        status=ComplaintStatus.OPEN
    )

    db.add(new_complaint)
    db.commit()
    db.refresh(new_complaint)
    return new_complaint

@router.get("/my-complaints", response_model=List[ComplaintResponse])
def get_my_complaints(
    consumer: User = Depends(require_consumer),
    db: Session = Depends(get_db)
):
    complaints = db.query(Complaint).filter(Complaint.consumer_id == consumer.id).order_by(Complaint.created_at.desc()).all()
    return complaints

@router.get("/farmer-complaints", response_model=List[ComplaintResponse])
def get_farmer_complaints(
    farmer: User = Depends(require_farmer),
    db: Session = Depends(get_db)
):
    complaints = db.query(Complaint).filter(Complaint.farmer_id == farmer.id).order_by(Complaint.created_at.desc()).all()
    return complaints

@router.put("/{complaint_id}/resolve", response_model=ComplaintResponse)
def resolve_complaint(
    complaint_id: int,
    data: ComplaintUpdateStatus,
    farmer: User = Depends(require_farmer),
    db: Session = Depends(get_db)
):
    complaint = db.query(Complaint).filter(Complaint.id == complaint_id, Complaint.farmer_id == farmer.id).first()
    if not complaint:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found or unauthorized.")

    complaint.status = data.status
    if data.resolution_notes:
        complaint.resolution_notes = data.resolution_notes

    db.commit()
    db.refresh(complaint)
    return complaint
