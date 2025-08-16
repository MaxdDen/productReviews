from typing import Optional
from pydantic import BaseModel, Field

class PromtBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None

class PromtCreate(PromtBase):
    pass

class PromtUpdate(PromtBase):
    name: Optional[str] = Field(None, min_length=1, max_length=255) # All fields optional for update
    description: Optional[str] = None

class PromtInDBBase(PromtBase):
    id: int
    user_id: Optional[int] = None
    model_config = {"from_attributes": True} # Replaces orm_mode in Pydantic v2

# Alias for PromtInDBBase for simplicity in routes
Promt = PromtInDBBase
