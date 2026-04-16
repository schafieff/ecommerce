from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.user import User
from app.models.cart import Cart
from app.schemas.user import UserCreate, UserResponse
from app.services.auth import Token
from app.core.security import hash_password, verify_password, create_access_token
from app.core.dependencies import get_current_user

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Registration flow:
    1. Check email not already taken
    2. Hash password
    3. Create user
    4. Create empty cart for user  ← important, cart is created here
    5. Return safe user data

    We create the cart immediately on registration so
    we never have to handle "user has no cart" edge cases
    anywhere else in the codebase. Cart always exists.
    This is called "eager initialization" — set up
    everything a user needs at creation time.
    """
    # Check duplicate email
    result = await db.execute(select(User).where(User.email == user_data.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create user
    user = User(
        email=user_data.email,
        hashed_password=hash_password(user_data.password),
        full_name=user_data.full_name
    )
    db.add(user)
    await db.flush()  # ← flush assigns user.id without committing
                      # we need user.id to create the cart below

    # Create cart immediately
    cart = Cart(user_id=user.id)
    db.add(cart)
    # commit happens automatically in get_db() dependency

    return user


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """
    OAuth2PasswordRequestForm is a FastAPI built-in.
    It expects form data (not JSON) with fields:
    username and password.
    
    We use email as username — this is standard practice.
    The field is called "username" because OAuth2 spec
    requires it, but we treat it as email.
    
    Security practice: always say "Invalid credentials"
    never "Email not found" or "Wrong password" separately.
    Telling an attacker which one is wrong helps them
    narrow down valid emails. Vague errors are safer.
    """
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalar_one_or_none()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",  # ← intentionally vague
            headers={"WWW-Authenticate": "Bearer"}
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account is disabled"
        )

    token = create_access_token(data={
        "sub": str(user.id),
        "is_admin": user.is_admin
    })

    return Token(access_token=token)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """
    The simplest protected route possible.
    get_current_user dependency does all the work.
    This route just returns whoever is authenticated.
    
    Notice: no DB call here. The user object was already
    fetched inside the dependency. FastAPI caches
    dependency results within a single request —
    get_current_user won't hit the DB twice even if
    two routes use it in the same request chain.
    """
    return current_user