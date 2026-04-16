from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from app.database import get_db
from app.models.user import User
from app.models.cart import Cart, CartItem
from app.models.order import Order, OrderItem, OrderStatus
from app.models.product import Product
from app.schemas.order import OrderResponse, OrderStatusUpdate
from app.core.dependencies import get_current_user, get_current_admin

router = APIRouter()


@router.post("", response_model=OrderResponse, status_code=201)
async def place_order(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    This is the most critical route in the entire app.
    It's where ACID compliance matters most.

    Everything below happens in ONE transaction:
    1. Validate cart isn't empty
    2. Validate stock for every item
    3. Create Order
    4. Create OrderItems (with price snapshots)
    5. Decrement stock for every product
    6. Clear the cart

    If ANY step fails, the entire transaction rolls back.
    No partial orders. No phantom stock decrements.
    No money charged for unavailable items.
    """
    # Get cart with items
    cart_result = await db.execute(
        select(Cart).where(Cart.user_id == current_user.id)
    )
    cart = cart_result.scalar_one_or_none()

    if not cart or not cart.items:
        raise HTTPException(
            status_code=400,
            detail="Cart is empty"
        )

    # Validate stock for ALL items before touching anything
    # We check everything first — fail fast before any writes
    for cart_item in cart.items:
        if cart_item.product.stock_quantity < cart_item.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient stock for {cart_item.product.name}"
            )

    # Calculate total
    total = sum(
        item.product.price * item.quantity
        for item in cart.items
    )

    # Create order
    order = Order(
        user_id=current_user.id,
        total_amount=total,
        status=OrderStatus.pending
    )
    db.add(order)
    await db.flush()  # get order.id

    # Create order items + decrement stock atomically
    for cart_item in cart.items:
        order_item = OrderItem(
            order_id=order.id,
            product_id=cart_item.product_id,
            quantity=cart_item.quantity,
            price_at_purchase=cart_item.product.price  # ← snapshot here
        )
        db.add(order_item)

        # Decrement stock — same transaction as order creation
        cart_item.product.stock_quantity -= cart_item.quantity

    # Clear cart — delete all items
    for cart_item in cart.items:
        await db.delete(cart_item)

    await db.flush()
    await db.refresh(order)
    return order


@router.get("", response_model=List[OrderResponse])
async def list_orders(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Users see only their own orders."""
    result = await db.execute(
        select(Order)
        .where(Order.user_id == current_user.id)
        .order_by(Order.created_at.desc())  # newest first
    )
    return result.scalars().all()


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Order).where(
            Order.id == order_id,
            Order.user_id == current_user.id  # ← ownership check
        )
    )
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    return order


@router.patch("/{order_id}/status", response_model=OrderResponse)
async def update_order_status(
    order_id: int,
    status_data: OrderStatusUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin)
):
    """
    State machine enforcement lives here.
    Not every transition is valid:

    pending    → confirmed, cancelled
    confirmed  → shipped, cancelled
    shipped    → delivered
    delivered  → (terminal, no transitions)
    cancelled  → (terminal, no transitions)

    Trying to move delivered → cancelled is rejected.
    This prevents data integrity issues — you can't
    un-deliver something in the real world.
    """
    valid_transitions = {
        OrderStatus.pending:   [OrderStatus.confirmed, OrderStatus.cancelled],
        OrderStatus.confirmed: [OrderStatus.shipped, OrderStatus.cancelled],
        OrderStatus.shipped:   [OrderStatus.delivered],
        OrderStatus.delivered: [],  # terminal
        OrderStatus.cancelled: [],  # terminal
    }

    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    allowed = valid_transitions.get(order.status, [])
    if status_data.status not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot transition from {order.status} to {status_data.status}"
        )

    # If cancelling, restore stock
    if status_data.status == OrderStatus.cancelled:
        for item in order.items:
            result = await db.execute(
                select(Product).where(Product.id == item.product_id)
            )
            product = result.scalar_one_or_none()
            if product:
                product.stock_quantity += item.quantity

    order.status = status_data.status
    await db.flush()
    await db.refresh(order)
    return order