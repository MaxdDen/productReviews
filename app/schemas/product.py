from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

# Properties shared by all product schemas
class ProductBase(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    ean: Optional[str] = None
    upc: Optional[str] = None
    brand_id: Optional[int] = None
    category_id: Optional[int] = None
    promt_id: Optional[int] = None
    analysis_result: Optional[str] = None

# Properties to receive on item creation
class ProductCreate(ProductBase):
    name: str # Name is required for creation

# Properties to receive on item update
class ProductUpdate(ProductBase):
    pass

# Properties stored in DB
class ProductInDBBase(ProductBase):
    id: int
    user_id: int
    # created_at: datetime # Assuming you might add timestamps
    # updated_at: datetime # Assuming you might add timestamps
    model_config = {"from_attributes": True} # Replaces orm_mode in Pydantic v2


# Additional properties to return to client
class Product(ProductInDBBase):
    brand: Optional[dict] = None # Simplified representation for now
    category: Optional[dict] = None # Simplified representation for now
    promt: Optional[dict] = None # Simplified representation for now
    main_image_filename: Optional[str] = None
    # Add other related data if needed, e.g., images, reviews

# Schema for product list items (could be a subset of Product)
class ProductListItem(BaseModel):
    id: int
    name: str
    ean: Optional[str] = None
    upc: Optional[str] = None
    brand_name: Optional[str] = None
    category_name: Optional[str] = None
    main_image_filename: Optional[str] = None
    model_config = {"from_attributes": True} # Replaces orm_mode in Pydantic v2


class ProductResponse(BaseModel):
    product: Product

class ProductListResponse(BaseModel):
    products: List[ProductListItem]
    total: int
    page: int
    limit: int
    highlight_page: Optional[int] = None
    highlight_id: Optional[int] = None
