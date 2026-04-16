from pydantic import BaseModel


class Token(BaseModel):
    """
    What the login endpoint returns.
    access_token is the JWT string.
    token_type is always "bearer" — this is an
    industry standard, not our invention.
    
    Bearer means: "whoever bears (carries) this token
    is authenticated." The client stores it and sends
    it in every request header:
    Authorization: Bearer <token>
    """
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """
    What we decode FROM a JWT token internally.
    This is never sent to or from the client —
    it's just a convenient Python object to hold
    decoded token contents.
    """
    user_id: Optional[int] = None
    is_admin: bool = False

from typing import Optional  # add at top in real code