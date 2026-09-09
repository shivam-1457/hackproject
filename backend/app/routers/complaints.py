from fastapi import APIRouter,Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Complaint,User
from ..schemas import ComplaintIn
from ..security import get_current_user
router=APIRouter(prefix="/complaints",tags=["complaints"])
@router.post("")
def create(data:ComplaintIn,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    c=Complaint(raised_by=user.id,**data.model_dump()); db.add(c); db.commit(); db.refresh(c); return {"id":c.id,"status":c.status}
@router.get("/mine")
def mine(db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    return db.query(Complaint).filter(Complaint.raised_by==user.id).all()
