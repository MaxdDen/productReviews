import logging
import pytest
import subprocess
import os
from httpx import AsyncClient, ASGITransport
from sqlalchemy import create_engine
from sqlalchemy.engine.url import make_url
import psycopg2

from app.main import app
from app.database.base import Base
from app.core.config import settings

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

import pytest_asyncio

@pytest_asyncio.fixture
async def test_client_without_csrf():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

@pytest.fixture(scope="session")
def test_db_url():
    return "sqlite:///./test.db"

@pytest.fixture(scope="session", autouse=True)
def setup_test_db(test_db_url):
    """
    Перед тестами: дропает и пересоздаёт тестовую БД, применяет все Alembic миграции.
    """
    url = make_url(test_db_url)
    logger.info("test_db_url:")
    logger.info(test_db_url)

    db_name = url.database
    logger.info("db_name:")
    logger.info(db_name)
    admin_url = url.set(database="postgres")
    logger.info("admin_url:")
    logger.info(admin_url)
    # Используем psycopg2 для создания/удаления базы
#    conn = psycopg2.connect(str(admin_url))
#    conn.autocommit = True
#    cur = conn.cursor()
#    try:
#        cur.execute(f"DROP DATABASE IF EXISTS {db_name}")
#    except Exception:
#        pass
#    cur.execute(f"CREATE DATABASE {db_name}")
#    cur.close()
#    conn.close()

    # Применить миграции Alembic
#    env = os.environ.copy()
#    env["DATABASE_URL"] = test_db_url  # если alembic.ini использует DATABASE_URL
#    subprocess.run(["alembic", "upgrade", "head"], check=True, env=env)
    yield
    # (опционально) Можно дропнуть базу после тестов

@pytest.fixture(scope="session")
def sync_engine(test_db_url):
    """Синхронный engine для тестов (используется в тестах структуры БД)"""
    logger.info("test_db_url sync_engine:", test_db_url)

    engine = create_engine(test_db_url)
    yield engine
    engine.dispose()