from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.user import User
from app.models.cart import Cart, CartItem
from app.models.product import Product
from app.schemas.cart import CartItemCreate, CartItemUpdate, CartResponse
from app.core.dependencies import get_current_user

router = APIRouter()


@router.get("", response_model=CartResponse)
async def get_cart(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    No cart_id in the URL — users access THEIR cart.
    The identity comes from the JWT token, not the URL.
    
    This is important security design. If cart_id was
    in the URL, a user could request /cart/5 and see
    someone else's cart. By deriving it from the token,
    that attack is impossible by design.
    """
    result = await db.execute(
        select(Cart).where(Cart.user_id == current_user.id)
    )
    cart = result.scalar_one_or_none()

    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")

    return cart


@router.post("/items", response_model=CartResponse, status_code=201)
async def add_to_cart(
    item_data: CartItemCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Two cases to handle:
    1. Product not in cart yet → create CartItem
    2. Product already in cart → increment quantity

    Never create duplicate CartItem rows for same
    product in same cart. Merge them instead.
    This is called "upsert" logic —
    UPDATE if exists, INSERT if not.
    """
    # Verify product exists and is available
    result = await db.execute(
        select(Product).where(
            Product.id == item_data.product_id,
            Product.is_available == True
        )
    )
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Check stock
    if product.stock_quantity < item_data.quantity:
        raise HTTPException(
            status_code=400,
            detail=f"Only {product.stock_quantity} items in stock"
        )

    # Get cart
    cart_result = await db.execute(
        select(Cart).where(Cart.user_id == current_user.id)
    )
    cart = cart_result.scalar_one_or_none()

    # Check if already in cart — upsert logic
    existing_item_result = await db.execute(
        select(CartItem).where(
            CartItem.cart_id == cart.id,
            CartItem.product_id == item_data.product_id
        )
    )
    existing_item = existing_item_result.scalar_one_or_none()

    if existing_item:
        existing_item.quantity += item_data.quantity
    else:
        new_item = CartItem(
            cart_id=cart.id,
            product_id=item_data.product_id,
            quantity=item_data.quantity
        )
        db.add(new_item)

    await db.flush()
    await db.refresh(cart)
    return cart


@router.patch("/items/{item_id}", response_model=CartResponse)
async def update_cart_item(
    item_id: int,
    item_data: CartItemUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Verify item belongs to THIS user's cart
    # This is an authorization check — not just "does
    # this item exist" but "does this item belong to you"
    result = await db.execute(
        select(CartItem)
        .join(Cart)
        .where(
            CartItem.id == item_id,
            Cart.user_id == current_user.id  # ← ownership check
        )
    )
    item = result.scalar_one_or_none()

    if not item:
        raise HTTPException(status_code=404, detail="Cart item not found")

    item.quantity = item_data.quantity

    cart_result = await db.execute(
        select(Cart).where(Cart.user_id == current_user.id)
    )
    cart = cart_result.scalar_one_or_none()
    await db.refresh(cart)
    return cart


@router.delete("/items/{item_id}", status_code=204)
async def remove_from_cart(
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(CartItem)
        .join(Cart)
        .where(
            CartItem.id == item_id,
            Cart.user_id == current_user.id
        )
    )
    item = result.scalar_one_or_none()

    if not item:
        raise HTTPException(status_code=404, detail="Cart item not found")

    await db.delete(item)