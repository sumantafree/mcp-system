"""
Authentication router — production-ready (fixed password handling)
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

from database.database import get_db
from database import models
from core.security import hash_password, verify_password, create_access_token
from core.dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ─────────────────────────────
# SCHEMAS
# ─────────────────────────────

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=72)

    username: Optional[str] = None
    full_name: Optional[str] = None
    phone: Optional[str] = None
    whatsapp_number: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    email: str
    username: Optional[str] = None
    full_name: Optional[str] = None
    role: str
    avatar_url: Optional[str] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class UpdateProfileRequest(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    whatsapp_number: Optional[str] = None
    timezone: Optional[str] = None
    avatar_url: Optional[str] = None


# ─────────────────────────────
# REGISTER
# ─────────────────────────────

@router.post("/register", response_model=TokenResponse, status_code=201)
def register(data: RegisterRequest, db: Session = Depends(get_db)):

    # ✅ Check email
    existing_user = db.query(models.User).filter_by(email=data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # ✅ Check username
    if data.username:
        existing_username = db.query(models.User).filter_by(username=data.username).first()
        if existing_username:
            raise HTTPException(status_code=400, detail="Username already taken")

    # ✅ Extra safety validation (optional)
    if len(data.password) > 128:
        raise HTTPException(status_code=400, detail="Password too long (max 128 characters)")

    # ✅ Create user
    user = models.User(
        email=data.email,
        username=data.username,
        full_name=data.full_name,
        hashed_password=hash_password(data.password),  # 🔐 secure hashing
        phone=data.phone,
        whatsapp_number=data.whatsapp_number,
        role=models.UserRole.admin,
        is_active=True,
        is_verified=True,
        created_at=datetime.utcnow(),
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    # ✅ Create token
    token = create_access_token({
        "sub": str(user.id),
        "role": _role_str(user.role),
    })

    return TokenResponse(
        access_token=token,
        user=UserResponse.model_validate(user)
    )


# ─────────────────────────────
# LOGIN
# ─────────────────────────────

def _role_str(role) -> str:
    """Safely extract role value — handles both Enum and plain string."""
    if hasattr(role, "value"):
        return role.value
    return str(role)


@router.post("/login", response_model=TokenResponse)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):

    user = db.query(models.User).filter(
        (models.User.email == form.username) |
        (models.User.username == form.username)
    ).first()

    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # 🔐 secure verification
    if not verify_password(form.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid password")

    if not user.is_active:
        raise HTTPException(status_code=400, detail="Account is inactive")

    # ✅ Update last login
    user.last_login = datetime.utcnow()
    db.commit()

    token = create_access_token({
        "sub": str(user.id),
        "role": _role_str(user.role),
    })

    return TokenResponse(
        access_token=token,
        user=UserResponse.model_validate(user)
    )


# ─────────────────────────────
# GET CURRENT USER
# ─────────────────────────────

@router.get("/me", response_model=UserResponse)
def get_me(current_user: models.User = Depends(get_current_user)):
    return current_user


# ─────────────────────────────
# UPDATE PROFILE
# ─────────────────────────────

@router.patch("/me", response_model=UserResponse)
def update_profile(
    data: UpdateProfileRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):

    update_data = data.model_dump(exclude_none=True)

    for field, value in update_data.items():
        setattr(current_user, field, value)

    current_user.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(current_user)

    return current_user


# ─────────────────────────────
# LOGOUT
# ─────────────────────────────

@router.post("/logout")
def logout(current_user: models.User = Depends(get_current_user)):
    return {"message": "Logged out successfully"}