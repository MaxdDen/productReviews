from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

import os

#from app.database.base import Base
from app.database.sync_session import Base, engine
from app.models import *
from dotenv import load_dotenv
from app.core.config import settings as app_settings

# Выбери какой файл подгружать: development или production
env_file = os.getenv("ENV_FILE", ".env.development")

# Абсолютный путь к env-файлу (обычно на уровень выше alembic/)
dotenv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', env_file))
load_dotenv(dotenv_path=dotenv_path)

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

sync_db_url = app_settings.SYNC_DATABASE_URL

if not sync_db_url:
    # Fallback to direct environment variable read if not in Pydantic settings,
    # or use a hardcoded default if that also fails.
    # This provides a secondary fallback if app_settings isn't fully populated
    # when env.py runs, though ideally app_settings.SYNC_DATABASE_URL should be the source.
    sync_db_url = os.getenv("SYNC_DATABASE_URL")
    if not sync_db_url:
        # Last resort: hardcoded default synchronous URL for Alembic if SYNC_DATABASE_URL is nowhere to be found.
        # Consider raising an error here if SYNC_DATABASE_URL is strictly required.
        print("Warning: SYNC_DATABASE_URL not found in Pydantic settings or environment. "
              "Falling back to default Alembic DSN: postgresql+psycopg2://postgres:postgres@localhost:5432/product_reviews")
        sync_db_url = "postgresql+psycopg2://postgres:postgres@localhost:5432/product_reviews"

# Ensure the URL is synchronous for Alembic (though SYNC_DATABASE_URL should already be)
if "asyncpg" in sync_db_url:
    print(f"Warning: SYNC_DATABASE_URL ('{sync_db_url}') appears to be an async DSN. "
          "Alembic requires a synchronous DSN. Attempting to convert.")
    sync_db_url = sync_db_url.replace("+asyncpg", "+psycopg2", 1)

config.set_main_option("sqlalchemy.url", sync_db_url)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
#target_metadata = None
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
