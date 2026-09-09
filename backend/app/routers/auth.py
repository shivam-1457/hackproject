from datetime import datetime,timedelta,timezone
import secrets
from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User,VerificationToken,PasswordResetToken
from ..schemas import RegisterIn,LoginIn,ResetRequest,ResetPasswordIn
from ..security import hash_password,verify_password,create_access_token
from ..email_service import send_verification_email,send_reset_email
router=APIRouter(prefix="/auth",tags=["auth"])
@router.post("/register")
def register(data:RegisterIn,db:Session=Depends(get_db)):
    if data.role not in {"consumer","farmer"}: raise HTTPException(400,"Role must be consumer or farmer")
    if db.query(User).filter(User.email==data.email).first(): raise HTTPException(409,"Email already registered")
    u=User(name=data.name,email=data.email,phone=data.phone,password_hash=hash_password(data.password),role=data.role,latitude=data.latitude,longitude=data.longitude,address=data.address); db.add(u); db.commit(); db.refresh(u)
    t=secrets.token_urlsafe(32); db.add(VerificationToken(user_id=u.id,token=t,expires_at=datetime.now(timezone.utc)+timedelta(minutes=30))); db.commit(); send_verification_email(u.email,u.name,t)
    return {"message":"Registration successful. Check your email to verify your account."}
@router.get("/verify")
def verify(token:str,db:Session=Depends(get_db)):
    x=db.query(VerificationToken).filter(VerificationToken.token==token,VerificationToken.used==False).first()
    if not x or x.expires_at<datetime.now(timezone.utc): raise HTTPException(400,"Invalid or expired verification link")
    u=db.get(User,x.user_id); u.is_verified=True; x.used=True; db.commit(); return {"message":"Email verified successfully"}
@router.post("/login")
def login(data:LoginIn,db:Session=Depends(get_db)):
    u=db.query(User).filter(User.email==data.email).first()
    if not u or not verify_password(data.password,u.password_hash): raise HTTPException(401,"Invalid email or password")
    if not u.is_verified: raise HTTPException(403,"Please verify your email first")
    return {"access_token":create_access_token(u),"token_type":"bearer","user":{"id":u.id,"name":u.name,"role":u.role}}
@router.post("/forgot-password")
def forgot(data:ResetRequest,db:Session=Depends(get_db)):
    u=db.query(User).filter(User.email==data.email).first()
    if u:
        t=secrets.token_urlsafe(32); db.add(PasswordResetToken(user_id=u.id,token=t,expires_at=datetime.now(timezone.utc)+timedelta(minutes=30))); db.commit(); send_reset_email(u.email,t)
    return {"message":"If the email exists, a reset link has been sent"}
@router.post("/reset-password")
def reset(data:ResetPasswordIn,db:Session=Depends(get_db)):
    x=db.query(PasswordResetToken).filter(PasswordResetToken.token==data.token,PasswordResetToken.used==False).first()
    if not x or x.expires_at<datetime.now(timezone.utc): raise HTTPException(400,"Reset token invalid or expired")
    u=db.get(User,x.user_id); u.password_hash=hash_password(data.new_password); x.used=True; db.commit(); return {"message":"Password reset successfully"}
