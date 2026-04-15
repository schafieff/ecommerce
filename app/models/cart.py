from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base
from app.models import TimestampMixin


class Cart(TimestampMixin, Base):
    """
    A Cart is created once when a user registers (or on first
    item add) and persists until checkout. After checkout,
    we CLEAR it — not delete it. The cart always exists,
    it just becomes empty again.
    
    This is simpler than creating/destroying carts repeatedly
    and avoids race conditions.
    """
    __tablename__ = "carts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)

    user = relationship("User", back_populates="cart")
    items = relationship(
        "CartItem",
        back_populates="cart",
        lazy="selectin",
        cascade="all, delete-orphan"  # ← important, explained below
    )


class CartItem(TimestampMixin, Base):
    """
    Represents one product line in the cart.
    If the same product is added twice, we increment
    quantity — we never create duplicate CartItem rows
    for the same product in the same cart.
    """
    __tablename__ = "cart_items"

    id = Column(Integer, primary_key=True, index=True)
    cart_id = Column(Integer, ForeignKey("carts.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, default=1, nullable=False)

    cart = relationship("Cart", back_populates="items")
    product = relationship("Product", back_populates="cart_items", lazy="selectin")