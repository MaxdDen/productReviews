import os
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from httpx import AsyncClient, ASGITransport

from app.core.config import settings
from app.database.base import Base
from app.main import app as fastapi_app
from app.database.session import get_db

# 1. Один engine на тест
@pytest_asyncio.fixture(scope="function")
async def db_engine():
    engine = create_async_engine(settings.DATABASE_URL, poolclass=NullPool)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

# 2. Одна сессия на тест
@pytest_asyncio.fixture(scope="function")
async def test_db_session(db_engine):
    SessionLocal = async_sessionmaker(bind=db_engine, expire_on_commit=False, class_=AsyncSession)
    async with SessionLocal() as session:
        yield session

# 3. Клиент FastAPI, использующий эту сессию
@pytest_asyncio.fixture(scope="function")
async def test_client_without_csrf(test_db_session):
    from app.utils.security import csrf_protect
    fastapi_app.dependency_overrides[get_db] = lambda: test_db_session
    fastapi_app.dependency_overrides[csrf_protect] = lambda: None
    async with AsyncClient(transport=ASGITransport(app=fastapi_app), base_url="http://testserver") as ac:
        yield ac
    fastapi_app.dependency_overrides.clear()