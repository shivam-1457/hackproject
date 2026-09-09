from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Order,OrderItem,Product,User
from ..schemas import OrderIn
from ..security import get_current_user
from ..payment_service import simulate_payment
from ..email_service import send_order_confirmation_to_farmer
router=APIRouter(prefix="/orders",tags=["orders"])
@router.post("")
def create(data:OrderIn,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    if user.role!="consumer": raise HTTPException(403,"Only consumers can order")
    order=Order(consumer_id=user.id,delivery_address=data.delivery_address,delivery_latitude=data.delivery_latitude,delivery_longitude=data.delivery_longitude,payment_method=data.payment_method); total=0; items=[]
    for x in data.items:
        p=db.get(Product,x.product_id)
        if not p or p.stock<x.quantity: raise HTTPException(400,"Insufficient stock")
        total+=float(p.price)*x.quantity; items.append((p,x)); p.stock-=x.quantity
    tid,ps=simulate_payment(total,data.payment_method); order.total_amount=total; order.transaction_id=tid; order.payment_status=ps; db.add(order); db.flush()
    for p,x in items: db.add(OrderItem(order_id=order.id,product_id=p.id,quantity=x.quantity,unit_price=p.price))
    db.commit()
    for p,x in items:
        f=db.get(User,p.farmer_id); send_order_confirmation_to_farmer(f.email,f.name,order.id,p.name,x.quantity)
    return {"order_id":order.id,"status":order.status,"payment_status":ps,"transaction_id":tid,"total_amount":total}
@router.get("/mine")
def mine(db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    out=[]
    for o in db.query(Order).filter(Order.consumer_id==user.id).all():
        out.append({"id":o.id,"status":o.status,"payment_status":o.payment_status,"total_amount":float(o.total_amount),"delivery_address":o.delivery_address,"delivery_latitude":o.delivery_latitude,"delivery_longitude":o.delivery_longitude,"items":[{"product_name":i.product.name,"quantity":i.quantity,"farmer_name":i.product.farmer.name,"farmer_latitude":i.product.latitude,"farmer_longitude":i.product.longitude} for i in o.items]})
    return out
@router.patch("/{order_id}/status")
def status(order_id:int,status:str,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    o=db.get(Order,order_id)
    if not o or user.role not in {"farmer","admin"}: raise HTTPException(404,"Order not found or not allowed")
    if status not in {"placed","confirmed","packed","out_for_delivery","delivered","cancelled"}: raise HTTPException(400,"Invalid status")
    o.status=status; db.commit(); return {"status":status}
