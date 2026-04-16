from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from app.database import get_db
from app.models.user import User
from app.models.product import Product, Category
from app.schemas.product import (
    ProductCreate, ProductUpdate, ProductResponse,
    CategoryCreate, CategoryResponse
)
from app.core.dependencies import get_current_admin

router = APIRouter()


@router.get("", response_model=List[ProductResponse])
async def list_products(
    db: AsyncSession = Depends(get_db),
    category_id: Optional[int] = Query(None),
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    search: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),       # pagination offset
    limit: int = Query(20, ge=1, le=100)  # pagination limit
):
    """
    Query parameters are optional filters — the user
    can combine any of them:
    GET /products?category_id=3&min_price=10&max_price=50

    skip/limit is called OFFSET pagination.
    skip=0, limit=20 → first page
    skip=20, limit=20 → second page
    skip=40, limit=20 → third page

    Real world: for large datasets, cursor-based
    pagination is more efficient. But offset pagination
    is simpler to understand and fine for most use cases.

    limit: le=100 prevents someone from requesting
    10000 products at once and hammering your DB.
    Always cap your limits.
    """
    query = select(Product).where(Product.is_available == True)

    if category_id:
        query = query.where(Product.category_id == category_id)
    if min_price is not None:
        query = query.where(Product.price >= min_price)
    if max_price is not None:
        query = query.where(Product.price <= max_price)
    if search:
        query = query.where(Product.name.ilike(f"%{search}%"))
        # ilike = case-insensitive LIKE
        # %search% means "contains search anywhere in name"

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(product_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    return product


@router.post("", response_model=ProductResponse, status_code=201)
async def create_product(
    product_data: ProductCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin)  # ← _ means "required but unused"
):
    """
    The admin dependency is the entire auth check.
    If the user isn't an admin, the dependency raises
    403 before this function body even runs.
    
    Using _ for the variable name is a Python convention
    meaning "I need this dependency to run for its side
    effects, but I don't need the return value."
    """
    product = Product(**product_data.model_dump())
    db.add(product)
    await db.flush()
    await db.refresh(product)
    return product


@router.patch("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int,
    product_data: ProductUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin)
):
    """
    PATCH vs PUT:
    PUT   = replace entire resource (all fields required)
    PATCH = partial update (only send what changes)
    
    We use PATCH because ProductUpdate has all optional
    fields. exclude_unset=True means "only update fields
    the client actually sent" — don't overwrite fields
    with None just because they weren't in the request.
    """
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # exclude_unset=True is critical for PATCH semantics
    update_data = product_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(product, field, value)

    await db.flush()
    await db.refresh(product)
    return product


@router.delete("/{product_id}", status_code=204)
async def delete_product(
    product_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin)
):
    """
    204 No Content — successful deletion returns no body.
    This is the HTTP standard for DELETE.
    Returning the deleted object would be redundant —
    it's gone, there's nothing to show.
    """
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    await db.delete(product)