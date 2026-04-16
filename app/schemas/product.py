from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class CategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None


class CategoryCreate(CategoryBase):
    pass  # no extra fields needed for creation


class CategoryResponse(CategoryBase):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class ProductBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    price: float = Field(..., gt=0)        # gt=0 means "greater than 0"
    stock_quantity: int = Field(..., ge=0) # ge=0 means "greater than or equal to 0"
    image_url: Optional[str] = None
    category_id: Optional[int] = None


class ProductCreate(ProductBase):
    """
    Admin sends this to create a product.
    All validation is inherited from ProductBase.
    price: gt=0 means a product can't be free or negative.
    stock_quantity: ge=0 means stock can't be negative.
    These constraints are business rules expressed as code.
    """
    pass


class ProductUpdate(BaseModel):
    """
    All optional — admin might only update price,
    or only restock quantity. Don't force them to
    resend every field just to change one thing.
    """
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    price: Optional[float] = Field(None, gt=0)
    stock_quantity: Optional[int] = Field(None, ge=0)
    is_available: Optional[bool] = None
    image_url: Optional[str] = None
    category_id: Optional[int] = None


class ProductResponse(ProductBase):
    id: int
    is_available: bool
    created_at: datetime
    category: Optional[CategoryResponse] = None

    model_config = {"from_attributes": True}