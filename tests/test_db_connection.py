import psycopg2
from sqlalchemy.engine.url import make_url
from app.core.config import settings


def test_db_connection():
    """Проверяет, что к тестовой базе можно подключиться и выполнить SELECT 1."""
    url = make_url(settings.SYNC_DATABASE_URL)
    logger.info("settings.SYNC_DATABASE_URL")
    print("settings.SYNC_DATABASE_URL ", url)
    logger.info(url)
    try:
        conn = psycopg2.connect(str(url))
        cur = conn.cursor()
        cur.execute("SELECT 1")
        result = cur.fetchone()
        assert result[0] == 1, "SELECT 1 не вернул 1"
        cur.close()
        conn.close()
    except Exception as e:
        assert False, f"Не удалось подключиться к тестовой базе: {e}"
