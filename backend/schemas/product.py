from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID

class ProductImageResponse(BaseModel):
    id: UUID
    variant_id: UUID
    url: str
    alt_text: Optional[str]
    is_primary: bool
    sort_order: int
    format: Optional[str]
    created_at: str

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

class ProductVariantCreate(BaseModel):
    sku: str
    name: str
    base_price: float
    sale_price: Optional[float] = None
    stock: int
    attributes: Optional[Dict[str, Any]] = {}

class ProductCreate(BaseModel):
    name: str
    description: Optional[str] = None
    category_id: UUID
    variants: List[ProductVariantCreate]
    origin: Optional[str] = None
    dietary_tags: Optional[List[str]] = []

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[UUID] = None
    origin: Optional[str] = None
    dietary_tags: Optional[List[str]] = None

class CategoryResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    image_url: Optional[str]
    is_active: bool
    created_at: str
    updated_at: Optional[str]
    
    class Config:
        from_attributes = True

class SupplierResponse(BaseModel):
    id: UUID
    email: str
    firstname: str
    lastname: str
    phone: Optional[str]
    role: str
    
    class Config:
        from_attributes = True

class ProductVariantResponse(BaseModel):
    id: UUID
    product_id: UUID
    sku: str
    name: str
    base_price: float
    sale_price: Optional[float]
    current_price: float
    discount_percentage: float
    stock: int
    attributes: Optional[Dict[str, Any]]
    is_active: bool
    images: List[ProductImageResponse] = []
    primary_image: Optional[ProductImageResponse] = None
    created_at: str
    updated_at: Optional[str]
    product_name: Optional[str] = None
    product_description: Optional[str] = None
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

class PriceRange(BaseModel):
    min: float
    max: float

class ProductResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    category_id: UUID
    supplier_id: UUID
    featured: bool
    rating: float
    review_count: int
    origin: Optional[str]
    dietary_tags: Optional[List[str]]
    is_active: bool
    price_range: PriceRange
    in_stock: bool
    created_at: str
    updated_at: Optional[str]
    # Relationships
    category: Optional[CategoryResponse] = None
    supplier: Optional[SupplierResponse] = None
    variants: List[ProductVariantResponse] = []
    primary_variant: Optional[ProductVariantResponse] = None
    
    class Config:
        from_attributes = True

class ProductListResponse(BaseModel):
    products: List[ProductResponse]
    total: int
    page: int
    per_page: int
    pages: int

class ProductDetailResponse(ProductResponse):
    # Includes all product fields plus additional details
    pass