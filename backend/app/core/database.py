"""
Database engine and session factory.

Engine creation is deferred to a function so the test suite can override
DATABASE_URL via an environment variable before importing this module.
"""
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings


def _build_engine():
    url = settings.DATABASE_URL
    kwargs: dict = {"echo": False}
    if url.startswith("postgresql"):
        kwargs.update(pool_size=10, max_overflow=20, pool_recycle=1800)
    elif url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
    return create_engine(url, **kwargs)


engine = _build_engine()

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""
    pass


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
