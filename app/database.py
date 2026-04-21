from sqlalchemy.orm.session import Session


from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import settings

# The engine is the actual connection to PostgreSQL
engine = create_async_engine(settings.DATABASE_URL, echo=True)

# SessionLocal is a factory — calling it gives you a session
AsyncSessionLocal = sessionmaker[Session](
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Base is what all our models will inherit from
Base = declarative_base()

# Dependency — used in every route that needs DB access
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise