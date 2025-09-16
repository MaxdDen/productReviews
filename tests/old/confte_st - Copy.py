import os
import asyncio
import pytest
import pytest_asyncio
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from httpx import AsyncClient, ASGITransport
import sqlalchemy
from sqlalchemy.orm import Session
import random
import string
import logging
logging.basicConfig(
    level=logging.INFO,  # Можно сменить на DEBUG при необходимости
    format="%(asctime)s %(levelname)s %(name)s %(message)s"
)
logger = logging.getLogger(__name__)

from app.core.config import settings
from app.database.base import Base
from app.main import app as fastapi_app
from app.database.session import get_db
from app.models.user import User
from app.models.product import Product
from app.schemas.product import ProductCreate


os.environ["ENVIRONMENT"] = "test"
print(f"[conftest] ENVIRONMENT={os.environ.get('ENVIRONMENT')}")

@pytest_asyncio.fixture(scope="function")
async def db_engine():
    logger.info("Старт db_engine")
    engine = create_async_engine(settings.DATABASE_URL, poolclass=NullPool)
    async with engine.begin() as conn:
        logger.info("Создаем таблицы")
        await conn.run_sync(Base.metadata.create_all)
        logger.info("Таблицы созданы")
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()
    logger.info("Конец db_engine")

@pytest.fixture(scope="function")
def sync_engine():
    logger.info("Старт sync_engine")
    engine = create_engine(settings.SYNC_DATABASE_URL, echo=False)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()
    logger.info("Конец sync_engine")

@pytest_asyncio.fixture(scope="function")
async def db_session():
    logger.info("Старт db_session")
    engine = create_async_engine(settings.DATABASE_URL, poolclass=NullPool)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    SessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)
    async with SessionLocal() as session:
        yield session
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()
    logger.info("Конец db_session")

@pytest_asyncio.fixture(scope="function")
async def client(db_session):
    logger.info("Старт client")
    fastapi_app.dependency_overrides[get_db] = lambda: db_session

    async with AsyncClient(transport=ASGITransport(app=fastapi_app), base_url="http://testserver") as ac:
        yield ac

    fastapi_app.dependency_overrides.clear()
    logger.info("client: yield завершён")

@pytest_asyncio.fixture(scope="function")
async def client_without_csrf(db_session):
    logger.info("Старт client_without_csrf")
    from app.utils.security import csrf_protect

    fastapi_app.dependency_overrides[get_db] = lambda: db_session
    fastapi_app.dependency_overrides[csrf_protect] = lambda: None

#    async with AsyncClient(transport=ASGITransport(app=fastapi_app), base_url="http://testserver") as ac:
#        yield ac

    fastapi_app.dependency_overrides.clear()
    logger.info("client_without_csrf: yield завершён")

# --- Очистка всех таблиц после каждого теста (sync) ---
@pytest.fixture(autouse=True)
def clean_tables(sync_engine):
    logger.info("Старт clean_tables")
    with sync_engine.connect() as conn:
        trans = conn.begin()
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())
        trans.commit()
    logger.info("Конец clean_tables")

# --- Очистка всех таблиц после каждого теста (async) ---
@pytest_asyncio.fixture(autouse=True)
async def async_clean_tables(db_engine):
    logger.info("Старт async_clean_tables")
    async with db_engine.connect() as conn:
        trans = await conn.begin()
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(sqlalchemy.delete(table))
        await trans.commit()
    logger.info("Конец async_clean_tables")

# --- Транзакционный откат для sync-тестов ---
@pytest.fixture(scope="function")
def db_session_with_rollback(sync_engine):
    logger.info("Старт db_session_with_rollback")
    connection = sync_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()
    logger.info("Конец db_session_with_rollback")

# --- Фикстура для sync тестов: создание пользователя ---
@pytest.fixture
def test_user(sync_engine):
    logger.info("Старт test_user")
    username = "user_" + ''.join(random.choices(string.ascii_lowercase, k=8))
    user = User(username=username, hashed_password="hashed", is_superuser=False)
    with sync_engine.connect() as conn:
        trans = conn.begin()
        conn.execute(User.__table__.insert().values(username=user.username, hashed_password=user.hashed_password, is_superuser=user.is_superuser))
        trans.commit()
    logger.info("Конец test_user")
    return user

# --- Фикстура для async тестов: создание пользователя ---
@pytest_asyncio.fixture
async def async_test_user(test_db_session):
    logger.info("Старт async_test_user")
    username = "user_" + ''.join(random.choices(string.ascii_lowercase, k=8))
    user = User(username=username, hashed_password="hashed", is_superuser=False)
    db = test_db_session
    db.add(user)
    await db.flush()
    await db.refresh(user)
    logger.info("Конец async_test_user")
    return user

# --- Фикстура для async тестов: создание продукта ---
@pytest_asyncio.fixture
async def async_test_product(test_db_session, async_test_user):
    logger.info("Старт async_test_product")
    db = test_db_session
    user = async_test_user
    product_data = ProductCreate(name="Test Product", description="desc")
    from app.database.crud import create_directory_item
    product = await create_directory_item(db, product_data, Product, user=user)
    return product

# --- Best practice: единая сессия для клиента и теста ---
@pytest_asyncio.fixture(scope="function")
async def test_db_session(db_engine):
    logger.info("Старт test_db_session")
    SessionLocal = async_sessionmaker(bind=db_engine, expire_on_commit=False, class_=AsyncSession)
    async with SessionLocal() as session:
        yield session
        logger.info("Конец test_db_session")

@pytest_asyncio.fixture(scope="function")
async def test_client_without_csrf(test_db_session):
    logger.info("Старт test_client_without_csrf")
    from app.utils.security import csrf_protect
    fastapi_app.dependency_overrides[get_db] = lambda: test_db_session
    fastapi_app.dependency_overrides[csrf_protect] = lambda: None
    async with AsyncClient(transport=ASGITransport(app=fastapi_app), base_url="http://testserver") as ac:
        yield ac
        logger.info("Конец test_client_without_csrf")
    fastapi_app.dependency_overrides.clear()