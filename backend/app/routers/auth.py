import datetime
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User, UserRole
from app.schemas.user import (
    UserRegister, UserLogin, VerifyEmailRequest, ResendVerificationRequest,
    TokenResponse, UserResponse
)
from app.utils.security import (
    hash_password, verify_password, create_access_token, generate_verification_token
)
from app.utils.email import send_verification_email, sent_emails_store
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/register", status_code=status.HTTP_201_CREATED)
def register_user(
    data: UserRegister,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == data.email.lower()).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists."
        )

    # Normalize role
    role = data.role.lower()
    if role not in [UserRole.FARMER, UserRole.CONSUMER, UserRole.ADMIN]:
        role = UserRole.CONSUMER

    # Generate verification token
    v_token = generate_verification_token()
    token_expires = datetime.datetime.utcnow() + datetime.timedelta(hours=24)

    # Create new user
    new_user = User(
        email=data.email.lower(),
        hashed_password=hash_password(data.password),
        full_name=data.full_name,
        phone=data.phone,
        role=role,
        farm_name=data.farm_name if role == UserRole.FARMER else None,
        farm_address=data.farm_address if role == UserRole.FARMER else None,
        farm_city=data.farm_city if role == UserRole.FARMER else None,
        farm_state=data.farm_state if role == UserRole.FARMER else None,
        farm_pincode=data.farm_pincode if role == UserRole.FARMER else None,
        farm_lat=data.farm_lat if role == UserRole.FARMER else None,
        farm_lng=data.farm_lng if role == UserRole.FARMER else None,
        delivery_address=data.delivery_address if role == UserRole.CONSUMER else None,
        delivery_city=data.delivery_city if role == UserRole.CONSUMER else None,
        delivery_state=data.delivery_state if role == UserRole.CONSUMER else None,
        delivery_pincode=data.delivery_pincode if role == UserRole.CONSUMER else None,
        is_verified=False,
        verification_token=v_token,
        verification_token_expires=token_expires
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Send verification email asynchronously
    background_tasks.add_task(send_verification_email, new_user.email, new_user.full_name, v_token)

    return {
        "message": "Registration successful! A verification link and token have been sent to your email.",
        "user_id": new_user.id,
        "email": new_user.email,
        "role": new_user.role,
        "dev_verification_token": v_token # Provided for instant frictionless testing
    }

@router.post("/verify-email")
def verify_email(data: VerifyEmailRequest, db: Session = Depends(get_db)):
    if not data.token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification token is required."
        )

    user = db.query(User).filter(User.verification_token == data.token.strip()).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification token."
        )

    if user.verification_token_expires and user.verification_token_expires < datetime.datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification token has expired. Please request a new verification email."
        )

    user.is_verified = True
    user.verification_token = None
    user.verification_token_expires = None
    db.commit()

    return {
        "message": "Email verified successfully! You can now log in and access all features.",
        "email": user.email,
        "role": user.role
    }

@router.post("/resend-verification")
def resend_verification(
    data: ResendVerificationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == data.email.lower()).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User with this email not found."
        )

    if user.is_verified:
        return {"message": "Account is already verified. You can log in directly."}

    v_token = generate_verification_token()
    user.verification_token = v_token
    user.verification_token_expires = datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    db.commit()

    background_tasks.add_task(send_verification_email, user.email, user.full_name, v_token)

    return {
        "message": "A new verification email has been sent.",
        "dev_verification_token": v_token
    }

@router.post("/login", response_model=TokenResponse)
def login_user(data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email.lower()).first()
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    access_token = create_access_token(data={"sub": str(user.id), "role": user.role, "email": user.email})

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user.role,
        "user_id": user.id,
        "full_name": user.full_name,
        "email": user.email,
        "is_verified": user.is_verified
    }

@router.get("/me", response_model=UserResponse)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    return current_user

@router.put("/me", response_model=UserResponse)
def update_profile(
    data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    allowed_fields = [
        "full_name", "phone", "farm_name", "farm_address", "farm_city",
        "farm_state", "farm_pincode", "farm_lat", "farm_lng",
        "delivery_address", "delivery_city", "delivery_state", "delivery_pincode"
    ]
    for key, val in data.items():
        if key in allowed_fields:
            setattr(current_user, key, val)

    db.commit()
    db.refresh(current_user)
    return current_user

@router.get("/recent-emails")
def get_recent_emails():
    """Development preview endpoint to inspect sent emails and verification tokens."""
    return {"emails": sent_emails_store[:10]}
