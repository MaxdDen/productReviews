from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

engine = create_engine(
    settings.SYNC_DATABASE_URL or "sqlite:///./test.db",
    echo=settings.DEBUG,
    future=True
)

SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()