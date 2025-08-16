from fastapi import Depends, HTTPException, Request
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession # Changed
from sqlalchemy.future import select # Added

from app.core import settings
from app.database.session import get_db
from app.models import User


async def get_current_user( # Changed to async
    request: Request,
    db: AsyncSession = Depends(get_db) # Changed to AsyncSession
) -> User:
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        user_id_str = payload.get("sub") # Renamed to avoid confusion before int conversion
        if user_id_str is None:
            raise HTTPException(status_code=401, detail="Token missing user_id")

        try:
            user_id = int(user_id_str)
        except ValueError:
            raise HTTPException(status_code=401, detail="Invalid user_id format in token")

        # Changed to async query
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return user

    except JWTError: # More specific exception handling
        raise HTTPException(status_code=403, detail="Invalid token: JWTError")
    except Exception as e: # Catch any other unexpected errors during token processing/db query
        # Log this error in a real app: logger.error(f"Unexpected error in get_current_user: {e}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")


async def get_current_superuser( # Changed to async
    current_user: User = Depends(get_current_user)
) -> User:
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not a superuser")
    return current_user
