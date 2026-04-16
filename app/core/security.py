from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.core.config import settings

# CryptContext manages the hashing algorithm
# bcrypt is the industry standard for passwords —
# it's intentionally slow, which makes brute force attacks
# computationally expensive
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    Never store plaintext passwords. Ever.
    Even if your database gets stolen, bcrypt hashes
    are computationally infeasible to reverse.
    
    Real world: LinkedIn had 117 million passwords
    leaked in 2012. The ones stored as MD5 hashes
    were cracked within days. The bcrypt ones weren't.
    That's why algorithm choice matters.
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    We never "decrypt" a password — that's not how
    hashing works. We hash the attempt and compare
    the two hashes. If they match, password is correct.
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    JWT = JSON Web Token
    
    Structure: header.payload.signature
    
    The payload carries claims — facts about the user:
    - sub (subject): who this token is for
    - exp (expiry): when it stops being valid
    - is_admin: what they're allowed to do
    
    The signature is cryptographically signed with
    SECRET_KEY — so we can verify the token wasn't
    tampered with. If someone changes the payload,
    the signature breaks.
    
    Real world: JWTs are stateless — the server doesn't
    store them. Any server with the SECRET_KEY can
    verify any token. This is why microservices love JWTs.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> Optional[dict]:
    """
    Returns the payload if valid, None if expired or tampered.
    JWTError is raised for any verification failure —
    expired, wrong signature, malformed. We catch all of them.
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        return None