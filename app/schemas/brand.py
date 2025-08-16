from typing import Optional
from pydantic import BaseModel, Field

class BrandBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None

class BrandCreate(BrandBase):
    pass

class BrandUpdate(BrandBase):
    name: Optional[str] = Field(None, min_length=1, max_length=255) # All fields optional for update
    description: Optional[str] = None

class BrandInDBBase(BrandBase):
    id: int
    user_id: Optional[int] = None
    model_config = {"from_attributes": True} # Replaces orm_mode in Pydantic v2

# Alias for BrandInDBBase for simplicity in routes
Brand = BrandInDBBase
