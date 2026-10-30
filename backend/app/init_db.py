"""Database initialization helpers."""

from .database import Base, engine


def init_db() -> None:
    """Create all registered database tables."""

    Base.metadata.create_all(bind=engine)
