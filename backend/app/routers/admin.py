from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Complaint,Order,User
from ..schemas import ComplaintUpdate
from ..security import require_role
router=APIRouter(prefix="/admin",tags=["admin"])
@router.get("/dashboard")
def dashboard(db:Session=Depends(get_db),admin:User=Depends(require_role("admin"))):
    return {"users":db.query(User).count(),"orders":db.query(Order).count(),"open_complaints":db.query(Complaint).filter(Complaint.status=="open").count(),"farmers":db.query(User).filter(User.role=="farmer").count(),"consumers":db.query(User).filter(User.role=="consumer").count()}
@router.get("/complaints")
def complaints(db:Session=Depends(get_db),admin:User=Depends(require_role("admin"))): return db.query(Complaint).all()
@router.patch("/complaints/{complaint_id}")
def resolve(complaint_id:int,data:ComplaintUpdate,db:Session=Depends(get_db),admin:User=Depends(require_role("admin"))):
    c=db.get(Complaint,complaint_id)
    if not c: raise HTTPException(404,"Complaint not found")
    c.status=data.status; c.admin_note=data.admin_note; db.commit(); return {"message":"Complaint updated"}
