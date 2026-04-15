from app.database import Base
from sqlalchemy import Column, Integer, DateTime
from sqlalchemy.sql import func

class TimestampMixin:
    """
    Every table in a real application should track when rows
    were created and last updated. This mixin adds those columns
    automatically to any model that inherits it.
    
    Real-world use: auditing, debugging, sorting by newest,
    soft deletes, cache invalidation.
    """
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),  # DB sets this, not Python
        nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),        # DB updates this automatically
        nullable=False
    )