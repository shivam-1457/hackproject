import datetime
import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.order import Order, OrderItem, OrderStatus, PaymentStatus
from app.models.product import Product
from app.models.user import User, UserRole
from app.schemas.order import (
    OrderCreate, OrderResponse, PaymentSimulateRequest, OrderStatusUpdate
)
from app.utils.dependencies import require_consumer, require_farmer, get_current_user
from app.utils.email import send_order_confirmation_email, send_farmer_order_alert

router = APIRouter(prefix="/api/orders", tags=["Orders & Payments"])

@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def create_order(
    data: OrderCreate,
    consumer: User = Depends(require_consumer),
    db: Session = Depends(get_db)
):
    if not data.items:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Order must contain at least one item.")

    total_amount = 0.0
    items_to_create = []

    # Validate each item and calculate price
    for item in data.items:
        prod = db.query(Product).filter(Product.id == item.product_id, Product.is_active == True).first()
        if not prod:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Product with ID {item.product_id} not found.")

        if prod.stock_quantity < item.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient stock for '{prod.title}'. Requested: {item.quantity} {prod.unit}, Available: {prod.stock_quantity} {prod.unit}"
            )

        subtotal = round(prod.price_per_unit * item.quantity, 2)
        total_amount += subtotal

        items_to_create.append({
            "product_id": prod.id,
            "farmer_id": prod.farmer_id,
            "product_title": prod.title,
            "quantity": item.quantity,
            "unit": prod.unit,
            "unit_price": prod.price_per_unit,
            "subtotal": subtotal
        })

    # Fixed or dynamic delivery fee
    delivery_fee = 40.0 if total_amount < 500 else 0.0
    grand_total = round(total_amount + delivery_fee, 2)

    new_order = Order(
        consumer_id=consumer.id,
        total_amount=round(total_amount, 2),
        delivery_fee=round(delivery_fee, 2),
        grand_total=grand_total,
        status=OrderStatus.PENDING_PAYMENT,
        payment_status=PaymentStatus.PENDING,
        payment_method=data.payment_method,
        shipping_address=data.shipping_address,
        shipping_city=data.shipping_city,
        shipping_state=data.shipping_state,
        shipping_pincode=data.shipping_pincode,
        shipping_notes=data.shipping_notes
    )

    db.add(new_order)
    db.commit()
    db.refresh(new_order)

    # Add items
    for item_dict in items_to_create:
        order_item = OrderItem(
            order_id=new_order.id,
            product_id=item_dict["product_id"],
            farmer_id=item_dict["farmer_id"],
            product_title=item_dict["product_title"],
            quantity=item_dict["quantity"],
            unit=item_dict["unit"],
            unit_price=item_dict["unit_price"],
            subtotal=item_dict["subtotal"]
        )
        db.add(order_item)

    db.commit()
    db.refresh(new_order)
    return new_order

@router.post("/{order_id}/pay", response_model=OrderResponse)
def simulate_payment(
    order_id: int,
    data: PaymentSimulateRequest,
    background_tasks: BackgroundTasks,
    consumer: User = Depends(require_consumer),
    db: Session = Depends(get_db)
):
    order = db.query(Order).filter(Order.id == order_id, Order.consumer_id == consumer.id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")

    if order.payment_status == PaymentStatus.COMPLETED:
        return order

    # Deduct stock for all items
    items_summary_lines = []
    farmer_alerts = {}

    for item in order.items:
        prod = db.query(Product).filter(Product.id == item.product_id).first()
        if prod:
            if prod.stock_quantity >= item.quantity:
                prod.stock_quantity -= item.quantity
            else:
                prod.stock_quantity = 0

            # Group for farmer notifications
            farmer = db.query(User).filter(User.id == item.farmer_id).first()
            if farmer:
                farmer_alerts[farmer.email] = {
                    "farmer_name": farmer.full_name,
                    "farmer_email": farmer.email,
                    "product_title": item.product_title,
                    "quantity": item.quantity,
                    "unit": item.unit
                }

        items_summary_lines.append(f"• {item.product_title}: {item.quantity} {item.unit} @ ₹{item.unit_price} = ₹{item.subtotal:.2f}")

    # Generate transaction reference
    tx_id = f"K2C_TXN_{uuid.uuid4().hex[:12].upper()}"

    order.payment_status = PaymentStatus.COMPLETED
    order.status = OrderStatus.CONFIRMED
    order.payment_method = data.payment_method
    order.payment_transaction_id = tx_id
    order.payment_timestamp = datetime.datetime.utcnow()

    db.commit()
    db.refresh(order)

    # Trigger async emails
    items_summary = "\n".join(items_summary_lines)
    background_tasks.add_task(
        send_order_confirmation_email,
        consumer.email,
        consumer.full_name,
        order.id,
        order.grand_total,
        items_summary
    )

    for alert in farmer_alerts.values():
        background_tasks.add_task(
            send_farmer_order_alert,
            alert["farmer_email"],
            alert["farmer_name"],
            order.id,
            alert["product_title"],
            alert["quantity"],
            alert["unit"]
        )

    return order

@router.get("/my-orders", response_model=List[OrderResponse])
def get_my_orders(
    consumer: User = Depends(require_consumer),
    db: Session = Depends(get_db)
):
    orders = db.query(Order).filter(Order.consumer_id == consumer.id).order_by(Order.created_at.desc()).all()
    return orders

@router.get("/farmer-orders")
def get_farmer_orders(
    farmer: User = Depends(require_farmer),
    db: Session = Depends(get_db)
):
    # Fetch order items belonging to this farmer
    order_items = db.query(OrderItem).filter(OrderItem.farmer_id == farmer.id).all()
    order_ids = list(set([item.order_id for item in order_items]))

    orders = db.query(Order).filter(Order.id.in_(order_ids)).order_by(Order.created_at.desc()).all()

    # Format result specifically showing items relevant to this farmer
    response = []
    for ord in orders:
        farmer_specific_items = [
            {
                "id": it.id,
                "product_id": it.product_id,
                "product_title": it.product_title,
                "quantity": it.quantity,
                "unit": it.unit,
                "unit_price": it.unit_price,
                "subtotal": it.subtotal
            }
            for it in ord.items if it.farmer_id == farmer.id
        ]
        farmer_subtotal = sum(it["subtotal"] for it in farmer_specific_items)

        response.append({
            "order_id": ord.id,
            "consumer_name": ord.consumer.full_name if ord.consumer else "Customer",
            "consumer_email": ord.consumer.email if ord.consumer else "",
            "consumer_phone": ord.consumer.phone if ord.consumer else "",
            "shipping_address": f"{ord.shipping_address}, {ord.shipping_city}, {ord.shipping_state} - {ord.shipping_pincode}",
            "order_status": ord.status,
            "payment_status": ord.payment_status,
            "created_at": ord.created_at,
            "farmer_items": farmer_specific_items,
            "farmer_revenue": round(farmer_subtotal, 2)
        })

    return response

@router.put("/{order_id}/status", response_model=OrderResponse)
def update_order_status(
    order_id: int,
    data: OrderStatusUpdate,
    farmer: User = Depends(require_farmer),
    db: Session = Depends(get_db)
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")

    # Verify farmer has items in this order
    has_item = any(item.farmer_id == farmer.id for item in order.items)
    if not has_item:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have items in this order.")

    order.status = data.status
    db.commit()
    db.refresh(order)
    return order

@router.get("/{order_id}", response_model=OrderResponse)
def get_order_by_id(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")

    # Consumer or Farmer involved can view
    is_consumer = order.consumer_id == current_user.id
    is_farmer = any(item.farmer_id == current_user.id for item in order.items)

    if not is_consumer and not is_farmer:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    return order
