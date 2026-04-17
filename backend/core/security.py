from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
from core.config import settings
import hashlib

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = "HS256"


# ─────────────────────────────
# PASSWORD HASHING (FIXED)
# ─────────────────────────────

def _pre_hash(password: str) -> str:
    """
    🔐 Convert password to fixed-length using SHA256
    This removes bcrypt 72-char limitation safely
    """
    return hashlib.sha256(password.encode()).hexdigest()


def hash_password(password: str) -> str:
    """
    Hash password securely using SHA256 → bcrypt
    """
    pre_hashed = _pre_hash(password)
    return pwd_context.hash(pre_hashed)


def verify_password(plain: str, hashed: str) -> bool:
    """
    Verify password using same SHA256 → bcrypt flow
    """
    pre_hashed = _pre_hash(plain)
    return pwd_context.verify(pre_hashed, hashed)


# ─────────────────────────────
# JWT TOKEN FUNCTIONS
# ─────────────────────────────

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
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
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )