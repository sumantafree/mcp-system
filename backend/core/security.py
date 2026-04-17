from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from fastapi import HTTPException, status
from core.config import settings
import bcrypt

ALGORITHM = "HS256"


# ─────────────────────────────
# PASSWORD HASHING
# Using bcrypt library directly — no passlib, no 72-byte error.
# We clip to 72 bytes ourselves before hashing.
# ─────────────────────────────

def _to_bytes(password: str) -> bytes:
    """Encode password and clip to 72 bytes (bcrypt hard limit)."""
    return password.encode("utf-8")[:72]


def hash_password(password: str) -> str:
    hashed = bcrypt.hashpw(_to_bytes(password), bcrypt.gensalt(rounds=12))
    return hashed.decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(_to_bytes(plain), hashed.encode("utf-8"))
    except Exception:
        return False


# ─────────────────────────────
# JWT TOKEN FUNCTIONS
# ─────────────────────────────

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
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
