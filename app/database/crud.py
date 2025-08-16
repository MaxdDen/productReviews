from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update as sqlalchemy_update, delete as sqlalchemy_delete
from pydantic import BaseModel
from typing import List, Optional, Type, TypeVar
from app.database.base import Base
from app.models.user import User # Assuming User model is needed for user_id checks

# Define a TypeVar for the SQLAlchemy model type
ModelType = TypeVar("ModelType", bound=Base)
# Define a TypeVar for the Pydantic schema type
SchemaType = TypeVar("SchemaType", bound=BaseModel)

async def get_user(db: AsyncSession, user_id: int) -> Optional[User]:
    result = await db.execute(select(User).filter(User.id == user_id))
    return result.scalar_one_or_none()

async def get_user_by_username(db: AsyncSession, username: str) -> Optional[User]: # Changed user_id to username
    result = await db.execute(select(User).filter(User.username == username)) # Changed User.id to User.username
    return result.scalar_one_or_none()

async def create_directory_item(db: AsyncSession, item_data: SchemaType, model_class: Type[ModelType], user: Optional[User] = None) -> ModelType:
    item_dict = item_data.model_dump()
    if hasattr(model_class, "user_id") and user:
        item_dict["user_id"] = user.id

    db_item = model_class(**item_dict)
    db.add(db_item)
    await db.commit()
    await db.refresh(db_item)
    return db_item

async def get_directory_item(db: AsyncSession, item_id: int, model_class: Type[ModelType], user: Optional[User] = None) -> Optional[ModelType]:
    stmt = select(model_class).filter(model_class.id == item_id)
    if user and not user.is_superuser and hasattr(model_class, "user_id"):
        stmt = stmt.filter(model_class.user_id == user.id)

    result = await db.execute(stmt)
    return result.scalar_one_or_none()

async def get_directory_items(
    db: AsyncSession,
    model_class: Type[ModelType],
    user: Optional[User] = None,
    skip: int = 0,
    limit: int = 100
) -> List[ModelType]:
    stmt = select(model_class)
    if user and not user.is_superuser and hasattr(model_class, "user_id"):
        stmt = stmt.filter(model_class.user_id == user.id)

    stmt = stmt.offset(skip).limit(limit)
    if hasattr(model_class, "name"): # Default sort by name if exists
        stmt = stmt.order_by(model_class.name)
    elif hasattr(model_class, "id"): # Else sort by id
        stmt = stmt.order_by(model_class.id)

    result = await db.execute(stmt)
    return result.scalars().all()

async def update_directory_item(db: AsyncSession, item_id: int, item_data: SchemaType, model_class: Type[ModelType], user: Optional[User] = None) -> Optional[ModelType]:
    # First, retrieve the item to ensure it exists and the user has permission
    db_item = await get_directory_item(db, item_id, model_class, user)
    if not db_item:
        return None

    update_data = item_data.model_dump(exclude_unset=True)

    # Prevent user_id from being updated directly through this generic function
    if "user_id" in update_data:
        del update_data["user_id"]

    if not update_data: # No actual data to update
        return db_item

    stmt = (
        sqlalchemy_update(model_class)
        .where(model_class.id == item_id)
        .values(**update_data)
        .execution_options(synchronize_session="fetch")
    )
    await db.execute(stmt)
    await db.commit()
    await db.refresh(db_item) # Refresh the original instance
    return db_item

async def delete_directory_item(db: AsyncSession, item_id: int, model_class: Type[ModelType], user: Optional[User] = None) -> bool:
    # First, retrieve the item to ensure it exists and the user has permission
    db_item = await get_directory_item(db, item_id, model_class, user)
    if not db_item:
        return False # Item not found or no permission

    stmt = sqlalchemy_delete(model_class).where(model_class.id == item_id)
    # The permission check is implicitly handled by get_directory_item,
    # so we don't strictly need to re-filter by user_id here for deletion,
    # but it's safer if get_directory_item's permission logic were to change.
    # However, for simplicity, we rely on the fact that db_item would be None if user doesn't have access.

    await db.execute(stmt)
    await db.commit()
    return True

