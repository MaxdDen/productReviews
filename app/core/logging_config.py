import logging
from app.core import settings

csrf_logger = logging.getLogger("csrf")
auth_logger = logging.getLogger("auth")

def setup_logging():
    base_level = logging.INFO if settings.is_production else logging.WARNING

    # --- Основная настройка ---
    logging.basicConfig(
        level=base_level,
        format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
        handlers=[logging.StreamHandler()],
        force=True,
    )

    # --- Отдельные логгеры ---
    for logger in (csrf_logger, auth_logger):
        logger.setLevel(base_level)
        handler = logging.FileHandler("security.log", encoding="utf-8")
        formatter = logging.Formatter("%(asctime)s [%(levelname)s] [%(name)s] %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    # SQLAlchemy логирование
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if settings.is_production else logging.WARNING
    )
