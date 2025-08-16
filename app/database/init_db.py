from sqlalchemy.orm import Session
from app.database.sync_session import engine, SessionLocal
from app.models.user import User
from app.utils.security import hash_password
from app.core.config import settings
from app.database.base import Base


def create_root_user():
    db: Session = SessionLocal()
    try:
        existing = db.query(User).filter(User.username == "root").first()
        if not existing:
            root_user = User(
                username="root",
                hashed_password=hash_password(settings.ROOT_PASSWORD),
                is_superuser=True
            )
            db.add(root_user)
            db.commit()
            print("✅ Root-пользователь создан.")
        else:
            print("ℹ️ Root-пользователь уже существует.")
    finally:
        db.close()


def init_db():
    Base.metadata.create_all(bind=engine)
    create_root_user()
