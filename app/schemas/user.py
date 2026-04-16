from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional


class UserBase(BaseModel):
    """
    Shared fields between all user schemas.
    EmailStr is not just String — Pydantic actually
    validates the format. "notanemail" will be rejected
    automatically before your code even runs.
    
    This is one of FastAPI's superpowers — validation
    is declarative. You describe the shape, FastAPI
    enforces it.
    """
    email: EmailStr
    full_name: Optional[str] = None


class UserCreate(UserBase):
    """
    Used for registration endpoint.
    
    Field() lets you add constraints and documentation.
    min_length=8 means FastAPI auto-rejects short passwords
    with a clear error — you write zero validation code.
    
    Real world: you'd also add password strength validation
    here with a @field_validator. We'll add that in hardening.
    """
    password: str = Field(..., min_length=8)


class UserUpdate(BaseModel):
    """
    ALL fields optional for updates — because a user might
    only want to change their name, not their email.
    
    This is the PATCH pattern. You only update what's sent.
    If a field is None, leave it unchanged in the database.
    """
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = Field(None, min_length=8)


class UserResponse(UserBase):
    """
    What we send back. Notice:
    - No password field (never expose it)
    - Includes id and timestamps (DB-generated values)
    - is_admin included so frontend can adjust UI
    
    model_config tells Pydantic to read data from
    SQLAlchemy model attributes, not just dictionaries.
    Without this, UserResponse(user) would fail because
    SQLAlchemy objects aren't plain dicts.
    """
    id: int
    is_active: bool
    is_admin: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UserInDB(UserBase):
    """
    Internal schema — used inside services only,
    never returned to client. Carries hashed_password
    for auth logic.
    
    The "InDB" suffix is a convention that signals
    "this contains sensitive data, handle carefully."
    """
    id: int
    hashed_password: str
    is_active: bool
    is_admin: bool

    model_config = {"from_attributes": True}