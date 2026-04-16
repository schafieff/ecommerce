import asyncio
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context

# Import your settings and Base
from app.core.config import settings
from app.database import Base

# Import ALL models so Alembic can see them
# This is a common gotcha — if you don't import a model
# here, Alembic won't know it exists and won't create
# its table. Every new model must be added here.
from app.models.user import User
from app.models.product import Product, Category
from app.models.cart import Cart, CartItem
from app.models.order import Order, OrderItem

# Alembic config object
config = context.config

# Override sqlalchemy.url with our .env value
# This means one source of truth — .env file
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Setup logging from alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# This is what Alembic inspects to detect changes
# It compares your models against the actual DB
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    Offline mode = generate SQL without a DB connection.
    Useful for reviewing what SQL will run before
    applying it to production. Good practice to always
    check this before deploying migrations.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True  # ← detects column type changes too
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """
    We use async engine because our app is async.
    Alembic itself is sync, so we bridge them here
    with asyncio.run() — this is the standard pattern
    for async SQLAlchemy + Alembic.
    """
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,  # no connection pooling for migrations
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()