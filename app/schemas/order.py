from pydantic import BaseModel
from typing import List
from datetime import datetime
from app.models.order import OrderStatus
from app.schemas.product import ProductResponse


class OrderItemResponse(BaseModel):
    """
    Notice we include product here even though
    we snapshot the price. Why?
    
    The product gives context (name, image, category).
    price_at_purchase gives accuracy (what was paid).
    Both together give a complete receipt.
    """
    id: int
    product: ProductResponse
    quantity: int
    price_at_purchase: float  # the snapshot, not product.price

    model_config = {"from_attributes": True}


class OrderResponse(BaseModel):
    id: int
    status: OrderStatus
    total_amount: float
    created_at: datetime
    items: List[OrderItemResponse] = []

    model_config = {"from_attributes": True}


class OrderStatusUpdate(BaseModel):
    """
    Admin-only schema for moving order through states.
    Just one field — status. Nothing else is editable
    on an order after placement.
    
    This tiny schema represents a big design decision:
    orders are immutable except for their status.
    """
    status: OrderStatus