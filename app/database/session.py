from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.config import settings

engine = create_async_engine(
    settings.DATABASE_URL, echo=settings.DEBUG, future=True
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession,
)

def get_async_engine():
    return engine

from fastapi import Request # Required for the new get_db
from typing import Optional # For type hinting

async def get_db(request: Request):
    session: Optional[AsyncSession] = request.scope.get("state", {}).get("db")

    if session is None:
        # This path is for cases where get_db is called outside a request
        # managed by DatabaseMiddleware or test client (e.g., a script).
        # It needs to manage its own session lifecycle.
        # print("get_db: Session not found in scope, creating new one (fallback).") # Debug
        async with AsyncSessionLocal() as new_session:
            try:
                yield new_session
                # For this fallback, we assume the caller of get_db will handle commit/rollback
                # on the yielded session if it's a unit of work.
            except Exception:
                # If an error occurs while the new_session is being used by the caller,
                # it's the caller's responsibility to rollback.
                # The 'async with' ensures close.
                if new_session.is_active: # Safety rollback
                    await new_session.rollback()
                raise
            # 'async with' handles new_session.close()
    else:
        # Session is from request.scope, managed by middleware or test fixture.
        # That manager is responsible for commit, rollback, and close.
        # get_db just yields the session for use within the route.
        # print(f"get_db: Using session {id(session)} from request scope.") # Debug
        yield session # No commit/rollback here.