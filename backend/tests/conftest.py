"""
Shared pytest fixtures.

SQLite in-memory с StaticPool — одна БД на весь тест, без внешних зависимостей.
Rate limiter переопределяется через EnvironmentVar — отключаем в тестах.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from unittest.mock import patch

from app.core.database import Base, get_db
from app.main import app
from app.seed.seed import seed as run_seed


def _make_test_engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(bind=engine)
    return engine


@pytest.fixture(scope="function")
def db_engine():
    engine = _make_test_engine()
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def client(db_engine):
    TestingSession = sessionmaker(
        bind=db_engine, autocommit=False, autoflush=False, expire_on_commit=False
    )

    def override_get_db():
        session = TestingSession()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    # Disable rate limiting in tests
    with patch("app.core.limiter.limiter._storage", None):
        pass
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def seeded_client(db_engine):
    TestingSession = sessionmaker(
        bind=db_engine, autocommit=False, autoflush=False, expire_on_commit=False
    )

    import app.seed.seed as seed_module
    original = seed_module.SessionLocal
    seed_module.SessionLocal = TestingSession
    run_seed()
    seed_module.SessionLocal = original

    def override_get_db():
        session = TestingSession()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c
    app.dependency_overrides.clear()
