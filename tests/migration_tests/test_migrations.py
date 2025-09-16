import os
import sys
import pytest
import subprocess
import psycopg2

# Устанавливаем тестовое окружение для alembic и settings
os.environ["ENVIRONMENT"] = "test"
print(f"[test_migrations] ENVIRONMENT={os.environ.get('ENVIRONMENT')}")
print(f"[test_migrations] sys.argv={sys.argv}")

# Скипать только если файл не указан явно в sys.argv (более надёжно)
if not any("test_migrations.py" in arg for arg in sys.argv):
    pytest.skip("test_migrations.py должен запускаться отдельно от других тестов!", allow_module_level=True)

from app.core.config import settings
MIGRATIONS_TEST_DB_URL = os.getenv("MIGRATIONS_TEST_DB_URL", settings.SYNC_DATABASE_URL)

def test_alembic_migrations_on_clean_db():
    """
    Проверяет, что alembic миграции применяются без ошибок на чистой отдельной БД.
    Перед тестом дропает и создаёт БД, чтобы не было конфликтов с существующими таблицами.
    """
    # Парсим параметры подключения
    import re
    m = re.match(r"postgresql://(.*?):(.*?)@(.*?):(\d+)/(.*)", MIGRATIONS_TEST_DB_URL)
    assert m, f"Can't parse MIGRATIONS_TEST_DB_URL: {MIGRATIONS_TEST_DB_URL}"
    user, password, host, port, dbname = m.groups()
    admin_db = "postgres"
    # Дропаем и создаём БД
    conn = psycopg2.connect(dbname=admin_db, user=user, password=password, host=host, port=port)
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute(f"SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '{dbname}' AND pid <> pg_backend_pid();")
    cur.execute(f"DROP DATABASE IF EXISTS {dbname};")
    cur.execute(f"CREATE DATABASE {dbname};")
    cur.close()
    conn.close()
    # Запускаем alembic upgrade head
    env = os.environ.copy()
    env["DATABASE_URL"] = MIGRATIONS_TEST_DB_URL
    env["SYNC_DATABASE_URL"] = MIGRATIONS_TEST_DB_URL
    result = subprocess.run(["alembic", "upgrade", "head"], capture_output=True, env=env)
    assert result.returncode == 0, result.stderr.decode() + "\n" + result.stdout.decode() 