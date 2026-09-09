from pathlib import Path
import uuid
from fastapi import APIRouter,Depends,HTTPException,UploadFile,File
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..database import get_db
from ..models import Product,Review,User
from ..schemas import ProductIn
from ..security import require_role
router=APIRouter(prefix="/products",tags=["products"])
@router.get("")
def list_products(db:Session=Depends(get_db)):
    rows=db.query(Product,func.coalesce(func.avg(Review.rating),0).label("rating")).outerjoin(Review).group_by(Product.id).all()
    return [{"id":p.id,"farmer_id":p.farmer_id,"name":p.name,"description":p.description,"category":p.category,"price":float(p.price),"stock":p.stock,"image_url":p.image_url,"latitude":p.latitude,"longitude":p.longitude,"rating":round(float(r),1)} for p,r in rows]
@router.post("")
def create(data:ProductIn,db:Session=Depends(get_db),user:User=Depends(require_role("farmer"))):
    p=Product(farmer_id=user.id,**data.model_dump()); db.add(p); db.commit(); db.refresh(p); return p
@router.put("/{product_id}")
def update(product_id:int,data:ProductIn,db:Session=Depends(get_db),user:User=Depends(require_role("farmer"))):
    p=db.get(Product,product_id)
    if not p or p.farmer_id!=user.id: raise HTTPException(404,"Product not found")
    for k,v in data.model_dump().items(): setattr(p,k,v)
    db.commit(); db.refresh(p); return p
@router.delete("/{product_id}")
def delete(product_id:int,db:Session=Depends(get_db),user:User=Depends(require_role("farmer"))):
    p=db.get(Product,product_id)
    if not p or p.farmer_id!=user.id: raise HTTPException(404,"Product not found")
    db.delete(p); db.commit(); return {"message":"Product deleted"}
@router.post("/{product_id}/image")
def image(product_id:int,image:UploadFile=File(...),db:Session=Depends(get_db),user:User=Depends(require_role("farmer"))):
    p=db.get(Product,product_id)
    if not p or p.farmer_id!=user.id: raise HTTPException(404,"Product not found")
    ext=Path(image.filename or "").suffix.lower()
    if ext not in {".jpg",".jpeg",".png",".webp"}: raise HTTPException(400,"Only image files are allowed")
    name=f"{uuid.uuid4().hex}{ext}"; Path("uploads",name).write_bytes(image.file.read()); p.image_url=f"/uploads/{name}"; db.commit(); return {"image_url":p.image_url}
