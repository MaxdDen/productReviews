from typing import Optional
from pydantic import BaseModel, Field

class CategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(CategoryBase):
    name: Optional[str] = Field(None, min_length=1, max_length=255) # All fields optional for update
    description: Optional[str] = None

class CategoryInDBBase(CategoryBase):
    id: int
    user_id: Optional[int] = None
    model_config = {"from_attributes": True} # Replaces orm_mode in Pydantic v2

# Alias for CategoryInDBBase for simplicity in routes
Category = CategoryInDBBase
