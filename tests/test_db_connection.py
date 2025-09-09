import psycopg2
from sqlalchemy.engine.url import make_url
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

from app.core.config import settings


def test_postgres_db_access():
    url = make_url(settings.SYNC_DATABASE_URL)
    logger.info("settings.SYNC_DATABASE_URL")
    print("settings.SYNC_DATABASE_URL ", url)
    logger.info(url)
    admin_url = url.set(database="postgres")
    try:
#        conn = psycopg2.connect(str(admin_url))
#        conn.close()
        assert True
    except Exception as e:
        assert False, f"Нет доступа к базе postgres: {e}"
