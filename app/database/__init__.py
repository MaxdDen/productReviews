from sqlalchemy.orm import Session

from app.database import base as database_base
from app.database import crud as database_crud
from app.database import session as database_session

from app.database.session import get_db
from app.database.crud import get_user_by_username

from app.models.user import User
from app.utils.security import hash_password
from app.core.config import settings
from app.database.session import SessionLocal


def create_root_user():
    db: Session = SessionLocal()
    try:
        existing = db.query(User).filter(User.username == "root").first()
        if not existing:
            root_user = User(
                username="root",
                hashed_password=hash_password(settings.ROOT_PASSWORD),
                is_superuser=True,
                is_active=True,
            )
            db.add(root_user)
            db.commit()
            print("✅ Root-пользователь создан.")
        else:
            print("ℹ️ Root-пользователь уже существует.")
    finally:
        db.close()


def init_db():
    from database.base import Base
    from database.session import engine

    Base.metadata.create_all(bind=engine)
    create_root_user()


__all__ = ["get_db", "init_db", "get_user_by_username"]