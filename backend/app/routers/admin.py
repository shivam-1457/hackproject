import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models.user import User, UserRole
from app.models.product import Product
from app.models.order import Order, OrderItem, OrderStatus, PaymentStatus
from app.models.complaint import Complaint, ComplaintStatus
from app.schemas.complaint import ComplaintArbitrate, ComplaintResponse
from app.utils.dependencies import require_admin
from app.utils.email import send_dispute_verdict_email

router = APIRouter(prefix="/api/admin", tags=["Admin Portal & Dispute Arbitration"])

@router.get("/stats")
def get_admin_stats(
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Returns high-level platform metrics for the administrator dashboard.
    """
    total_users = db.query(User).count()
    total_farmers = db.query(User).filter(User.role == UserRole.FARMER).count()
    total_consumers = db.query(User).filter(User.role == UserRole.CONSUMER).count()
    total_products = db.query(Product).filter(Product.is_active == True).count()
    total_orders = db.query(Order).count()

    total_revenue = db.query(func.sum(Order.grand_total)).filter(
        Order.payment_status == PaymentStatus.COMPLETED
    ).scalar() or 0.0

    total_complaints = db.query(Complaint).count()
    open_complaints = db.query(Complaint).filter(
        Complaint.status.in_([ComplaintStatus.OPEN, ComplaintStatus.UNDER_INVESTIGATION])
    ).count()
    resolved_complaints = db.query(Complaint).filter(
        Complaint.status.in_([ComplaintStatus.RESOLVED_REFUND, ComplaintStatus.RESOLVED_REPLACED, ComplaintStatus.REJECTED])
    ).count()

    return {
        "total_users": total_users,
        "total_farmers": total_farmers,
        "total_consumers": total_consumers,
        "total_products": total_products,
        "total_orders": total_orders,
        "gross_merchandise_value": round(float(total_revenue), 2),
        "total_complaints": total_complaints,
        "open_complaints": open_complaints,
        "resolved_complaints": resolved_complaints
    }

@router.get("/complaints")
def get_all_complaints(
    status_filter: Optional[str] = None,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Returns all disputes/complaints across the entire platform with enriched consumer and farmer details.
    """
    query = db.query(Complaint).order_by(Complaint.created_at.desc())

    if status_filter and status_filter != "ALL":
        query = query.filter(Complaint.status == status_filter)

    complaints = query.all()
    results = []

    for c in complaints:
        order = db.query(Order).filter(Order.id == c.order_id).first()
        consumer = db.query(User).filter(User.id == c.consumer_id).first()
        farmer = db.query(User).filter(User.id == c.farmer_id).first()
        prod = db.query(Product).filter(Product.id == c.product_id).first() if c.product_id else None

        results.append({
            "id": c.id,
            "order_id": c.order_id,
            "order_grand_total": order.grand_total if order else 0.0,
            "order_date": order.created_at.isoformat() if order and order.created_at else None,
            "product_id": c.product_id,
            "product_title": prod.title if prod else "Order Item",
            "consumer_id": c.consumer_id,
            "consumer_name": consumer.full_name if consumer else "Unknown Consumer",
            "consumer_email": consumer.email if consumer else "",
            "consumer_phone": consumer.phone if consumer else "",
            "farmer_id": c.farmer_id,
            "farmer_name": farmer.full_name if farmer else "Unknown Farmer",
            "farmer_farm_name": farmer.farm_name if farmer else "Agro Farm",
            "farmer_email": farmer.email if farmer else "",
            "farmer_phone": farmer.phone if farmer else "",
            "issue_type": c.issue_type,
            "description": c.description,
            "proof_image_url": c.proof_image_url,
            "requested_resolution": c.requested_resolution,
            "status": c.status,
            "resolution_notes": c.resolution_notes,
            "admin_verdict": c.admin_verdict,
            "arbitrated_by": c.arbitrated_by,
            "resolved_at": c.resolved_at.isoformat() if c.resolved_at else None,
            "created_at": c.created_at.isoformat() if c.created_at else None
        })

    return results

@router.put("/complaints/{complaint_id}/arbitrate")
def arbitrate_complaint(
    complaint_id: int,
    data: ComplaintArbitrate,
    background_tasks: BackgroundTasks,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Arbitrates and resolves a conflict between farmer and consumer with official verdict.
    """
    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found.")

    complaint.status = data.status
    complaint.admin_verdict = data.admin_verdict
    if data.resolution_notes:
        complaint.resolution_notes = data.resolution_notes
    complaint.arbitrated_by = f"Admin: {admin.full_name}"
    complaint.resolved_at = datetime.datetime.utcnow()

    db.commit()
    db.refresh(complaint)

    # Fetch consumer and farmer to notify via email
    consumer = db.query(User).filter(User.id == complaint.consumer_id).first()
    farmer = db.query(User).filter(User.id == complaint.farmer_id).first()

    if consumer:
        background_tasks.add_task(
            send_dispute_verdict_email,
            consumer.email,
            consumer.full_name,
            complaint.id,
            complaint.order_id,
            complaint.status,
            complaint.admin_verdict
        )

    if farmer:
        background_tasks.add_task(
            send_dispute_verdict_email,
            farmer.email,
            farmer.full_name,
            complaint.id,
            complaint.order_id,
            complaint.status,
            complaint.admin_verdict
        )

    return {
        "status": "success",
        "message": f"Complaint #{complaint_id} arbitrated successfully as {complaint.status}.",
        "complaint_id": complaint.id,
        "arbitration_verdict": complaint.admin_verdict,
        "arbitrated_by": complaint.arbitrated_by,
        "resolved_at": complaint.resolved_at
    }

@router.get("/users")
def get_all_users(
    role_filter: Optional[str] = None,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Lists all platform users with role and verification details.
    """
    query = db.query(User).order_by(User.created_at.desc())
    if role_filter and role_filter != "ALL":
        query = query.filter(User.role == role_filter)

    users = query.all()
    return [
        {
            "id": u.id,
            "email": u.email,
            "full_name": u.full_name,
            "role": u.role,
            "phone": u.phone,
            "is_verified": u.is_verified,
            "location": u.farm_city or u.delivery_city or "India",
            "farm_name": u.farm_name,
            "created_at": u.created_at.isoformat() if u.created_at else None
        }
        for u in users
    ]
