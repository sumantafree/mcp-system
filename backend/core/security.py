from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
from core.config import settings
import hashlib

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = "HS256"


# ─────────────────────────────
# PASSWORD HASHING (SAFE FIX)
# ─────────────────────────────

def _pre_hash(password: str) -> str:
    """
    Convert password to fixed-length SHA256 hash
    This completely removes bcrypt 72-char limitation
    """
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def hash_password(password: str) -> str:
    """
    Hash password securely (SHA256 → bcrypt)
    """
    if not password:
        raise ValueError("Password cannot be empty")

    pre_hashed = _pre_hash(password)

    # bcrypt now receives fixed 64-char string → always safe
    return pwd_context.hash(pre_hashed)


def verify_password(plain: str, hashed: str) -> bool:
    """
    Verify password using same SHA256 → bcrypt pipeline
    """
    if not plain or not hashed:
        return False

    pre_hashed = _pre_hash(plain)

    try:
        return pwd_context.verify(pre_hashed, hashed)
    except Exception:
        return False


# ─────────────────────────────
# JWT TOKEN FUNCTIONS
# ─────────────────────────────

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create JWT access token
    """
    to_encode = data.copy()

    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow()
    })

    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    """
    Decode JWT token safely
    """
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )