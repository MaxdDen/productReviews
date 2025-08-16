from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Type, TypeVar
from pydantic import BaseModel

from app.database.session import get_db
from app.models import User
from app.database import crud
from app.api.auth.dependencies import get_current_user
from app.utils.security import csrf_protect

T = TypeVar("T")
ModelType = TypeVar("ModelType")
SchemaType = TypeVar("SchemaType", bound=BaseModel)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)

def create_directory_router(
    *,
    model: Type[ModelType],
    schema: Type[SchemaType],
    create_schema: Type[CreateSchemaType],
    update_schema: Type[UpdateSchemaType],
    prefix: str,
    tags: List[str],
) -> APIRouter:
    router = APIRouter(prefix=prefix, tags=tags)
    model_name = model.__name__

    @router.post("/", response_model=schema, status_code=201, dependencies=[Depends(csrf_protect)])
    async def create_item(
        item_in: create_schema = Body(...),
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
    ):
        if not getattr(item_in, 'name', None) or getattr(item_in, 'name', '').isspace():
            raise HTTPException(status_code=422, detail=f"{model_name} name cannot be empty.")
        
        created_item = await crud.create_directory_item(db=db, item_data=item_in, model_class=model, user=current_user)
        return created_item

    @router.get("/{item_id}", response_model=schema)
    async def get_item(
        item_id: int,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
    ):
        item = await crud.get_directory_item(db=db, item_id=item_id, model_class=model, user=current_user)
        if not item:
            raise HTTPException(status_code=404, detail=f"{model_name} not found")
        return item

    @router.get("/", response_model=List[schema])
    async def get_items(
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user),
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=200)
    ):
        items = await crud.get_directory_items(db=db, model_class=model, user=current_user, skip=skip, limit=limit)
        return items

    @router.put("/{item_id}", response_model=schema, dependencies=[Depends(csrf_protect)])
    async def update_item(
        item_id: int,
        item_in: update_schema = Body(...),
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
    ):
        if getattr(item_in, 'name', None) is not None and (not getattr(item_in, 'name') or getattr(item_in, 'name').isspace()):
            raise HTTPException(status_code=422, detail=f"{model_name} name cannot be empty if provided.")
        
        updated_item = await crud.update_directory_item(db=db, item_id=item_id, item_data=item_in, model_class=model, user=current_user)
        if not updated_item:
            raise HTTPException(status_code=404, detail=f"{model_name} not found or not enough permissions")
        return updated_item

    @router.delete("/{item_id}", status_code=204, dependencies=[Depends(csrf_protect)])
    async def delete_item(
        item_id: int,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
    ):
        success = await crud.delete_directory_item(db=db, item_id=item_id, model_class=model, user=current_user)
        if not success:
            raise HTTPException(status_code=404, detail=f"{model_name} not found or not enough permissions")
        return {"ok": True}

    return router