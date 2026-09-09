from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Review,Product,OrderItem,User
from ..schemas import ReviewIn
from ..security import get_current_user
router=APIRouter(prefix="/reviews",tags=["reviews"])
@router.post("/product/{product_id}")
def review(product_id:int,data:ReviewIn,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    if user.role!="consumer" or not db.get(Product,product_id): raise HTTPException(403,"Consumer/product check failed")
    bought=db.query(OrderItem).join(OrderItem.order).filter(OrderItem.product_id==product_id,OrderItem.order.has(consumer_id=user.id)).first()
    if not bought: raise HTTPException(403,"Buy the product before reviewing it")
    db.add(Review(product_id=product_id,consumer_id=user.id,rating=data.rating,comment=data.comment)); db.commit(); return {"message":"Review submitted"}
