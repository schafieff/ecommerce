from pydantic import BaseModel, Field
from typing import List
from app.schemas.product import ProductResponse


class CartItemBase(BaseModel):
    product_id: int
    quantity: int = Field(..., ge=1)  # can't add 0 items


class CartItemCreate(CartItemBase):
    """Client sends this to add item to cart."""
    pass


class CartItemUpdate(BaseModel):
    """Client sends this to change quantity."""
    quantity: int = Field(..., ge=1)


class CartItemResponse(CartItemBase):
    id: int
    product: ProductResponse  # nested — full product details included

    model_config = {"from_attributes": True}


class CartResponse(BaseModel):
    """
    Notice we compute total here as a property.
    
    @property means it's calculated on the fly —
    not stored in the database. The database stores
    items and prices. The total is derived from them.
    
    Real world practice: never store computed values
    in the database if you can derive them reliably.
    Stored computed values go stale. Derived values
    are always accurate.
    """
    id: int
    items: List[CartItemResponse] = []

    @property
    def total(self) -> float:
        return sum(
            item.product.price * item.quantity
            for item in self.items
        )

    model_config = {"from_attributes": True}