import sys
import subprocess
import os


# Базовые параметры
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
ALEMBIC_CFG = os.path.join(BASE_DIR, "alembic.ini")

def run_dev():
    """Запуск dev-сервера FastAPI"""
    os.environ["ENVIRONMENT"] = "development"
    subprocess.run([
        "uvicorn", "app.main:app", "--reload", "--host", "127.0.0.1", "--port", "8000"
    ])

def run_prod():
    """Запуск FastAPI без автоперезагрузки (prod)"""
    os.environ["ENVIRONMENT"] = "production"
    subprocess.run([
        "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"
    ])

def migrate():
    """Выполнить миграции Alembic"""
    subprocess.run(["alembic", "-c", ALEMBIC_CFG, "upgrade", "head"])

def makemigrations():
    """Создать новую миграцию Alembic"""
    subprocess.run(["alembic", "-c", ALEMBIC_CFG, "revision", "--autogenerate", "-m", "Auto migration"])

def downgrade():
    """Откатить последнюю миграцию"""
    subprocess.run(["alembic", "-c", ALEMBIC_CFG, "downgrade", "-1"])

def test():
    """Запустить pytest для всех тестов с нужным окружением"""
    os.environ["ENVIRONMENT"] = "test"
    subprocess.run(["pytest", "tests", "-v"])
    
def createsuperuser():
    """Создать суперпользователя (пример для интерактивного скрипта)"""
    subprocess.run([sys.executable, "scripts/create_superuser.py"])

def help():
    """Показать список доступных команд"""
    print("""
Доступные команды:

  run           — Запустить dev-сервер (uvicorn, hot-reload)
  prod          — Запустить prod-сервер (uvicorn, без reload)
  migrate       — Применить миграции Alembic
  makemigrations— Создать новую миграцию Alembic
  downgrade     — Откатить одну миграцию назад
  test          — Запустить тесты (pytest)
  createsuperuser — Создать суперпользователя (нужен скрипт scripts/create_superuser.py)
  help          — Показать это сообщение
""")

COMMANDS = {
    "run": run_dev,
    "prod": run_prod,
    "migrate": migrate,
    "makemigrations": makemigrations,
    "downgrade": downgrade,
    "test": test,
    "createsuperuser": createsuperuser,
    "help": help,
}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        help()
        sys.exit(0)
    COMMANDS[sys.argv[1]]()