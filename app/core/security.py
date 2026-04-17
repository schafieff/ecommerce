from datetime import datetime, timedelta
from typing import Optional
import hashlib
import base64
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _pre_hash(password: str) -> str:
    """
    Pre-hash password with SHA-256 before bcrypt.
    
    Why: bcrypt truncates at 72 bytes. Long passwords
    would be silently treated as identical — a security hole.
    SHA-256 output is always 32 bytes, safely under the limit.
    
    We base64-encode the SHA-256 output because bcrypt
    expects a string, not raw bytes.
    
    Real world: this is the pattern used by Django's
    password hasher and recommended by security researchers.
    """
    digest = hashlib.sha256(password.encode()).digest()
    return base64.b64encode(digest).decode()


def hash_password(password: str) -> str:
    return pwd_context.hash(_pre_hash(password))


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Must pre-hash here too — otherwise verification
    would compare SHA-256+bcrypt against plain+bcrypt
    and always fail. Both sides of the comparison
    must use the same pipeline.
    """
    return pwd_context.verify(_pre_hash(plain_password), hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        return None