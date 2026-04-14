from fastapi import FastAPI
from app.routers import auth, products, cart, orders

app = FastAPI(
    title="E-Commerce API",
    description="A production-grade e-commerce backend",
    version="0.1.0"
)

# Register all routers
app.include_router(auth.router,     prefix="/auth",     tags=["Auth"])
app.include_router(products.router, prefix="/products", tags=["Products"])
app.include_router(cart.router,     prefix="/cart",     tags=["Cart"])
app.include_router(orders.router,   prefix="/orders",   tags=["Orders"])

@app.get("/health")
async def health_check():
    return {"status": "ok"}