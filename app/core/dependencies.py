from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.core.security import decode_access_token
from app.models.user import User

# This tells FastAPI where to find the token
# It looks for: Authorization: Bearer <token>
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    This dependency:
    1. Extracts JWT from Authorization header
    2. Decodes and validates it
    3. Fetches the user from DB
    4. Returns the user object to your route
    
    If anything fails, it raises 401 automatically.
    Your route never runs with an invalid token.
    
    Usage in any route:
    async def my_route(current_user: User = Depends(get_current_user))
    
    That one line locks the entire route behind auth.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    user_id: int = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None or not user.is_active:
        raise credentials_exception

    return user


async def get_current_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Builds ON TOP of get_current_user.
    First validates auth, then checks admin role.
    
    This is dependency chaining — dependencies can
    depend on other dependencies. FastAPI resolves
    the entire chain automatically.
    
    Non-admin users get 403 Forbidden (authenticated
    but not authorized — different from 401 which
    means not authenticated at all).
    
    401 = "Who are you?"
    403 = "I know who you are, you can't do this"
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user