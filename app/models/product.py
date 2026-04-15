from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base
from app.models import TimestampMixin


class Category(TimestampMixin, Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(Text, nullable=True)

    products = relationship("Product", back_populates="category", lazy="selectin")


class Product(TimestampMixin, Base):
    """
    Key design decision: stock_quantity lives here.
    When an order is placed, we decrement this.
    When an order is cancelled, we increment it back.
    
    This is called "inventory management" and it's where
    atomicity (from our ACID discussion) becomes critical.
    Decrementing stock and creating an order MUST be one
    atomic transaction — never two separate ones.
    """
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)
    price = Column(Float, nullable=False)
    stock_quantity = Column(Integer, default=0, nullable=False)
    is_available = Column(Boolean, default=True)
    image_url = Column(String, nullable=True)

    # Foreign key — links to categories table
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    category = relationship("Category", back_populates="products")

    # These back-reference from cart and order items
    cart_items = relationship("CartItem", back_populates="product")
    order_items = relationship("OrderItem", back_populates="product")