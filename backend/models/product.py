from sqlalchemy import Column, String, Boolean, ForeignKey, Text, Float, JSON, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from core.database import BaseModel, CHAR_LENGTH, GUID


class Category(BaseModel):
    __tablename__ = "categories"

    name = Column(String(CHAR_LENGTH), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    image_url = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True)

    # Relationships
    products = relationship("Product", back_populates="category")

    def to_dict(self) -> dict:
        """Convert category to dictionary for API responses"""
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "image_url": self.image_url,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Product(BaseModel):
    __tablename__ = "products"

    name = Column(String(CHAR_LENGTH), nullable=False)
    description = Column(Text, nullable=True)
    category_id = Column(GUID(), ForeignKey(
        "categories.id"), nullable=False)
    supplier_id = Column(GUID(),
                         ForeignKey("users.id"), nullable=False)
    featured = Column(Boolean, default=False)
    rating = Column(Float, default=0.0)
    review_count = Column(Integer, default=0)
    origin = Column(String(100), nullable=True)
    # ["organic", "gluten-free", etc.]
    dietary_tags = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True)

    # Relationships with lazy loading
    category = relationship("Category", back_populates="products")
    supplier = relationship("User", back_populates="supplied_products")
    variants = relationship("ProductVariant", back_populates="product",
                            cascade="all, delete-orphan", lazy="selectin")
    reviews = relationship("Review", back_populates="product")
    wishlist_items = relationship("WishlistItem", back_populates="product")

    @property
    def primary_variant(self):
        """Get the primary variant (first one or cheapest)"""
        if not self.variants:
            return None
        return min(self.variants, key=lambda v: v.base_price)

    @property
    def price_range(self) -> dict:
        """Get min and max price from variants"""
        if not self.variants:
            return {"min": 0, "max": 0}

        prices = [
            v.sale_price or v.base_price for v in self.variants if v.is_active]
        if not prices:
            return {"min": 0, "max": 0}

        return {"min": min(prices), "max": max(prices)}

    @property
    def in_stock(self) -> bool:
        """Check if any variant is in stock"""
        return any(v.stock > 0 for v in self.variants if v.is_active)

    def to_dict(self, include_variants=False) -> dict:
        """Convert product to dictionary for API responses"""
        data = {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "category_id": str(self.category_id),
            "supplier_id": str(self.supplier_id),
            "featured": self.featured,
            "rating": self.rating,
            "review_count": self.review_count,
            "origin": self.origin,
            "dietary_tags": self.dietary_tags,
            "is_active": self.is_active,
            "price_range": self.price_range,
            "in_stock": self.in_stock,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

        if include_variants:
            data["variants"] = [v.to_dict() for v in self.variants]

        return data


class ProductVariant(BaseModel):
    __tablename__ = "product_variants"

    product_id = Column(GUID(), ForeignKey(
        "products.id"), nullable=False)
    sku = Column(String(100), unique=True, nullable=False)
    # e.g., "1kg Bag", "5kg Pack"
    name = Column(String(CHAR_LENGTH), nullable=False)
    base_price = Column(Float, nullable=False)
    sale_price = Column(Float, nullable=True)
    stock = Column(Integer, default=0)
    # {"size": "1kg", "color": "red", etc.}
    attributes = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True)

    # Relationships with lazy loading
    product = relationship("Product", back_populates="variants")
    images = relationship("ProductImage", back_populates="variant",
                          cascade="all, delete-orphan", lazy="selectin")
    cart_items = relationship("CartItem", back_populates="variant")
    order_items = relationship("OrderItem", back_populates="variant")

    @property
    def current_price(self) -> float:
        """Get current price (sale price if available, otherwise base price)"""
        return self.sale_price if self.sale_price else self.base_price

    @property
    def discount_percentage(self) -> float:
        """Calculate discount percentage if on sale"""
        if not self.sale_price or self.sale_price >= self.base_price:
            return 0
        return round(((self.base_price - self.sale_price) / self.base_price) * 100, 2)

    @property
    def primary_image(self):
        """Get primary image"""
        return next((img for img in self.images if img.is_primary),
                    self.images[0] if self.images else None)

    def to_dict(self, include_images=True, include_product=False) -> dict:
        """Convert variant to dictionary for API responses"""
        data = {
            "id": str(self.id),
            "product_id": str(self.product_id),
            "sku": self.sku,
            "name": self.name,
            "base_price": self.base_price,
            "sale_price": self.sale_price,
            "current_price": self.current_price,
            "discount_percentage": self.discount_percentage,
            "stock": self.stock,
            "attributes": self.attributes,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

        if include_images:
            data["images"] = [img.to_dict() for img in self.images]
            data["primary_image"] = self.primary_image.to_dict(
            ) if self.primary_image else None

        if include_product and self.product:
            data["product_name"] = self.product.name
            data["product_description"] = self.product.description

        return data


class ProductImage(BaseModel):
    __tablename__ = "product_images"

    variant_id = Column(GUID(), ForeignKey(
        "product_variants.id"), nullable=False)
    url = Column(String(500), nullable=False)
    alt_text = Column(String(CHAR_LENGTH), nullable=True)
    is_primary = Column(Boolean, default=False)
    sort_order = Column(Integer, default=0)
    format = Column(String(10), nullable=True)  # jpg, png, webp

    # Relationships
    variant = relationship("ProductVariant", back_populates="images")

    def to_dict(self) -> dict:
        """Convert image to dictionary for API responses"""
        return {
            "id": str(self.id),
            "variant_id": str(self.variant_id),
            "url": self.url,
            "alt_text": self.alt_text,
            "is_primary": self.is_primary,
            "sort_order": self.sort_order,
            "format": self.format,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
