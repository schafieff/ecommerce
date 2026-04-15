from sqlalchemy import Column, Integer, Float, ForeignKey, Enum
from sqlalchemy.orm import relationship
from app.database import Base
from app.models import TimestampMixin
import enum


class OrderStatus(str, enum.Enum):
    """
    str + enum.Enum means the values are both enum members
    AND strings — so they serialize to JSON naturally.
    Without str, you'd get "OrderStatus.pending" in your
    API response instead of just "pending".
    
    The state machine:
    pending → confirmed → shipped → delivered
         └──────────────→ cancelled (from pending or confirmed only)
    
    Business logic enforces valid transitions.
    The database just stores the current state.
    """
    pending = "pending"
    confirmed = "confirmed"
    shipped = "shipped"
    delivered = "delivered"
    cancelled = "cancelled"


class Order(TimestampMixin, Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    status = Column(
        Enum(OrderStatus),
        default=OrderStatus.pending,
        nullable=False
    )

    # Snapshot of total at time of purchase
    # Recalculated from OrderItems but stored for quick access
    total_amount = Column(Float, nullable=False)

    user = relationship("User", back_populates="orders")
    items = relationship(
        "OrderItem",
        back_populates="order",
        lazy="selectin",
        cascade="all, delete-orphan"
    )


class OrderItem(TimestampMixin, Base):
    """
    This is the most important model to understand deeply.
    
    We store price_at_purchase here — NOT a reference to
    Product.price. This is a deliberate snapshot.
    
    Why? Product prices change. Your receipt from last year
    must show what you ACTUALLY paid, not today's price.
    This is called "point-in-time data" — a snapshot of
    reality at the moment something happened.
    
    Real world: this same pattern is used in invoices,
    receipts, financial ledgers, audit logs. Anytime
    something is "final," snapshot it — don't reference
    a mutable source.
    """
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    price_at_purchase = Column(Float, nullable=False)  # ← snapshot, not reference

    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items", lazy="selectin")