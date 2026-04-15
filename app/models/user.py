from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship
from app.database import Base
from app.models import TimestampMixin


class User(TimestampMixin, Base):
    """
    The central entity. Almost everything in this system
    belongs to a User — orders, cart, reviews.
    
    Design decisions worth noting:
    - We store hashed_password, NEVER plaintext
    - is_active allows "soft banning" without deletion
    - is_admin is simple RBAC — for complex systems you'd
      use a separate Role model with permissions
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)

    # Relationships — SQLAlchemy loads these lazily by default
    # We use lazy="selectin" for async compatibility
    # It means: when you load a User, also load their orders
    # in a separate SELECT automatically
    cart = relationship("Cart", back_populates="user", uselist=False, lazy="selectin")
    orders = relationship("Order", back_populates="user", lazy="selectin")