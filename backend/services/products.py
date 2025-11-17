from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload
from typing import Optional, List, Dict, Any
from fastapi import HTTPException
from uuid import UUID
from models.product import Product, ProductVariant, Category, ProductImage
from models.cart import CartItem
from models.user import User
from schemas.product import (
    ProductCreate, ProductUpdate, ProductResponse, ProductListResponse,
    ProductVariantResponse, CategoryResponse, SupplierResponse, 
    ProductImageResponse, PriceRange
)
from core.exceptions import APIException

class ProductService:
    def __init__(self, db: AsyncSession):
        self.db = db

    def _convert_image_to_response(self, image: ProductImage) -> ProductImageResponse:
        """Convert ProductImage model to response format."""
        return ProductImageResponse(
            id=image.id,
            variant_id=image.variant_id,
            url=image.url,
            alt_text=image.alt_text,
            is_primary=image.is_primary,
            sort_order=image.sort_order,
            format=image.format,
            created_at=image.created_at.isoformat() if image.created_at else ""
        )

    def _convert_variant_to_response(self, variant: ProductVariant) -> ProductVariantResponse:
        """Convert ProductVariant model to response format."""
        try:
            # Use the model's built-in to_dict method
            variant_dict = variant.to_dict(include_images=True)
            return ProductVariantResponse.model_validate(variant_dict)
        except Exception as e:
            print(f"Error converting variant {variant.id}: {e}")
            # Return minimal variant data
            return ProductVariantResponse(
                id=variant.id,
                product_id=variant.product_id,
                sku=getattr(variant, 'sku', ''),
                name=getattr(variant, 'name', ''),
                base_price=getattr(variant, 'base_price', 0.0),
                sale_price=getattr(variant, 'sale_price', None),
                current_price=getattr(variant, 'sale_price', None) or getattr(variant, 'base_price', 0.0),
                discount_percentage=0,
                stock=getattr(variant, 'stock', 0),
                attributes=getattr(variant, 'attributes', {}),
                is_active=getattr(variant, 'is_active', True),
                images=[],
                primary_image=None,
                created_at=variant.created_at.isoformat() if variant.created_at else "",
                updated_at=variant.updated_at.isoformat() if variant.updated_at else None
            )

    def _convert_product_to_response(self, product: Product, include_relationships: bool = True) -> ProductResponse:
        """Convert Product model to response format."""
        try:
            # Use the model's built-in to_dict method and then convert to response
            product_dict = product.to_dict(include_variants=True)
            
            # Convert category
            category = None
            if include_relationships and product.category:
                try:
                    category = CategoryResponse(
                        id=product.category.id,
                        name=product.category.name,
                        description=product.category.description,
                        image_url=product.category.image_url,
                        is_active=product.category.is_active,
                        created_at=product.category.created_at.isoformat() if product.category.created_at else "",
                        updated_at=product.category.updated_at.isoformat() if product.category.updated_at else None
                    )
                except Exception as e:
                    print(f"Error converting category: {e}")
                    category = None

            # Convert supplier
            supplier = None
            if include_relationships and product.supplier:
                try:
                    supplier = SupplierResponse(
                        id=product.supplier.id,
                        email=product.supplier.email,
                        firstname=product.supplier.firstname,
                        lastname=product.supplier.lastname,
                        phone=product.supplier.phone,
                        role=product.supplier.role
                    )
                except Exception as e:
                    print(f"Error converting supplier: {e}")
                    supplier = None

            # Convert variants using model's to_dict method
            variants = []
            for variant in (product.variants or []):
                try:
                    variant_dict = variant.to_dict(include_images=True)
                    variants.append(ProductVariantResponse.model_validate(variant_dict))
                except Exception as e:
                    print(f"Error converting variant {variant.id}: {e}")
                    continue
            
            # Get primary variant
            primary_variant = variants[0] if variants else None

            return ProductResponse(
                id=product.id,
                name=product.name,
                description=product.description,
                category_id=product.category_id,
                supplier_id=product.supplier_id,
                featured=product.featured,
                rating=product.rating,
                review_count=product.review_count,
                origin=product.origin,
                dietary_tags=product.dietary_tags,
                is_active=product.is_active,
                price_range=PriceRange(min=product.price_range["min"], max=product.price_range["max"]),
                in_stock=product.in_stock,
                created_at=product.created_at.isoformat() if product.created_at else "",
                updated_at=product.updated_at.isoformat() if product.updated_at else None,
                category=category,
                supplier=supplier,
                variants=variants,
                primary_variant=primary_variant
            )
        except Exception as e:
            print(f"Error converting product {product.id}: {e}")
            # Return minimal product data
            return ProductResponse(
                id=product.id,
                name=getattr(product, 'name', ''),
                description=getattr(product, 'description', ''),
                category_id=product.category_id,
                supplier_id=product.supplier_id,
                featured=getattr(product, 'featured', False),
                rating=getattr(product, 'rating', 0.0),
                review_count=getattr(product, 'review_count', 0),
                origin=getattr(product, 'origin', ''),
                dietary_tags=getattr(product, 'dietary_tags', []),
                is_active=getattr(product, 'is_active', True),
                price_range=PriceRange(min=0, max=0),
                in_stock=False,
                created_at=product.created_at.isoformat() if product.created_at else "",
                updated_at=product.updated_at.isoformat() if product.updated_at else None,
                category=None,
                supplier=None,
                variants=[],
                primary_variant=None
            )

    async def get_products(
        self,
        page: int = 1,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> Dict[str, Any]:
        """Get products with filtering and pagination."""
        print(f"Getting products: page={page}, limit={limit}, filters={filters}")
        offset = (page - 1) * limit
        
        query = select(Product).options(
            selectinload(Product.category),
            selectinload(Product.supplier),
            selectinload(Product.variants).selectinload(ProductVariant.images)
        ).where(Product.is_active == True)
        
        # Apply filters
        variant_joined = False
        if filters:
            if filters.get("category"):
                query = query.join(Category).where(Category.name == filters['category'])
            
            if filters.get("q"):
                search_term = f"%{filters['q']}%"
                query = query.where(
                    or_(
                        Product.name.ilike(search_term),
                        Product.description.ilike(search_term)
                    )
                )
            
            # Join ProductVariant only once if any price/availability/sale filters are applied
            price_filters = []
            if filters.get("min_price") is not None:
                price_filters.append(ProductVariant.base_price >= filters["min_price"])
            
            if filters.get("max_price") is not None:
                price_filters.append(ProductVariant.base_price <= filters["max_price"])
            
            if filters.get("availability") is not None:
                if filters["availability"]:
                    price_filters.append(ProductVariant.stock > 0)
                else:
                    price_filters.append(ProductVariant.stock == 0)
            
            if filters.get("sale"):
                price_filters.append(ProductVariant.sale_price.isnot(None))
            
            # Apply variant filters if any exist
            if price_filters:
                query = query.join(ProductVariant).where(and_(*price_filters))
                variant_joined = True
            
            if filters.get("min_rating") is not None:
                query = query.where(Product.rating >= filters["min_rating"])
            
            if filters.get("max_rating") is not None:
                query = query.where(Product.rating <= filters["max_rating"])
        
        # Apply sorting
        if hasattr(Product, sort_by):
            if sort_order.lower() == "desc":
                query = query.order_by(getattr(Product, sort_by).desc())
            else:
                query = query.order_by(getattr(Product, sort_by).asc())
        
        # Get total count for pagination
        count_query = select(func.count(Product.id.distinct())).where(Product.is_active == True)
        if filters:
            if filters.get("category"):
                count_query = count_query.select_from(Product).join(Category).where(
                    and_(Product.is_active == True, Category.name == filters['category'])
                )
            if filters.get("q"):
                search_term = f"%{filters['q']}%"
                count_query = count_query.where(
                    and_(
                        Product.is_active == True,
                        or_(
                            Product.name.ilike(search_term),
                            Product.description.ilike(search_term)
                        )
                    )
                )
        
        count_result = await self.db.execute(count_query)
        total = count_result.scalar()
        
        # Apply pagination
        query = query.offset(offset).limit(limit)
        
        result = await self.db.execute(query)
        products = result.scalars().all()
        
        print(f"Found {len(products)} products in database")
        print(f"Total count from count query: {total}")
        
        # Convert to response format
        products_data = []
        for product in products:
            try:
                product_response = self._convert_product_to_response(product)
                products_data.append(product_response)
            except Exception as e:
                print(f"Error converting product {product.id}: {e}")
                continue
        
        print(f"Successfully converted {len(products_data)} products")
        
        return {
            "data": products_data,
            "total": total,
            "page": page,
            "per_page": limit,
            "total_pages": (total + limit - 1) // limit
        }

    async def get_featured_products(self, limit: int = 4) -> List[ProductResponse]:
        """Fetch featured products with related data."""
        print(f"Fetching {limit} featured products...")

        # ✅ Use outerjoin if variants might be missing
        query = (
            select(Product)
            .options(
                selectinload(Product.category),
                selectinload(Product.supplier),
                selectinload(Product.variants).selectinload(ProductVariant.images),
            )
            .where(Product.featured.is_(True))  # safer than == True
            .order_by(Product.created_at.desc())
            .limit(limit)
        )

        result = await self.db.execute(query)
        products = result.scalars().unique().all()  # ✅ ensure uniqueness with .unique()

        print(f"Found {len(products)} featured products in DB.")
        for p in products:
            print(f"  - {p.name} (Featured: {p.featured}, Variants: {len(p.variants)})")

        if not products:
            print("⚠️ No featured products found. Check your DB data or 'featured' column values.")

        return [self._convert_product_to_response(product) for product in products]
    
    async def get_popular_products(self, limit: int = 4) -> List[ProductResponse]:
        """Get popular products based on cart additions or fallback to highest rated products."""
        # First, try to get products based on cart additions
        query = (
            select(Product, func.count(CartItem.id).label("added_to_cart"))
            .join(Product.variants)
            .join(CartItem, CartItem.variant_id == ProductVariant.id)
            .group_by(Product.id)
            .order_by(func.count(CartItem.id).desc())
            .limit(limit)
            .options(
                selectinload(Product.category),
                selectinload(Product.supplier),
                selectinload(Product.variants).selectinload(ProductVariant.images)
            )
        )

        result = await self.db.execute(query)
        rows = result.all()

        # If no products found (no cart items), fallback to highest rated products
        if not rows:
            fallback_query = select(Product).options(
                selectinload(Product.category),
                selectinload(Product.supplier),
                selectinload(Product.variants).selectinload(ProductVariant.images)
            ).order_by(Product.rating.desc(), Product.review_count.desc()).limit(limit)
            
            fallback_result = await self.db.execute(fallback_query)
            fallback_products = fallback_result.scalars().all()
            
            return [self._convert_product_to_response(product) for product in fallback_products]

        # Process cart-based popular products
        products = [row[0] for row in rows]  # Extract Product objects
        return [self._convert_product_to_response(product) for product in products]

    async def get_recommended_products(self, product_id: UUID, limit: int = 4) -> List[ProductResponse]:
        """Get recommended products based on a product."""
        # Get the product first
        product_query = select(Product).where(Product.id == product_id)
        product_result = await self.db.execute(product_query)
        product = product_result.scalar_one_or_none()
        
        if not product:
            return []
        
        # Get products from the same category
        query = select(Product).options(
            selectinload(Product.category),
            selectinload(Product.supplier),
            selectinload(Product.variants).selectinload(ProductVariant.images)
        ).where(
            and_(Product.category_id == product.category_id, Product.id != product_id)
        ).limit(limit)
        
        result = await self.db.execute(query)
        products = result.scalars().all()
        
        return [self._convert_product_to_response(product) for product in products]

    async def get_categories(self) -> List[CategoryResponse]:
        """Get all categories with their product counts."""
        query = (
            select(
                Category,
                func.count(Product.id).label("product_count")
            )
            .outerjoin(Product, Product.category_id == Category.id)
            .where(Category.is_active == True)
            .group_by(Category.id)
        )
        result = await self.db.execute(query)
        categories_with_counts = result.all()
        
        categories = []
        for category, product_count in categories_with_counts:
            categories.append(CategoryResponse(
                id=category.id,
                name=category.name,
                description=category.description,
                image_url=category.image_url,
                is_active=category.is_active,
                created_at=category.created_at.isoformat() if category.created_at else "",
                updated_at=category.updated_at.isoformat() if category.updated_at else None
            ))
        
        return categories
    
    async def get_category_by_id(self, category_id: UUID) -> Optional[CategoryResponse]:
        """Get Category by ID."""
        query = select(Category).where(Category.id == category_id)
        result = await self.db.execute(query)
        category = result.scalar_one_or_none()
        
        if category:
            return CategoryResponse(
                id=category.id,
                name=category.name,
                description=category.description,
                image_url=category.image_url,
                is_active=category.is_active,
                created_at=category.created_at.isoformat() if category.created_at else "",
                updated_at=category.updated_at.isoformat() if category.updated_at else None
            )
        return None

    async def get_product_by_id(self, product_id: UUID) -> Optional[ProductResponse]:
        """Get product by ID."""
        query = select(Product).options(
            selectinload(Product.category),
            selectinload(Product.supplier),
            selectinload(Product.variants).selectinload(ProductVariant.images)
        ).where(Product.id == product_id)
        
        result = await self.db.execute(query)
        product = result.scalar_one_or_none()
        
        if product:
            return self._convert_product_to_response(product)
        return None

    async def get_variant_by_id(self, variant_id: UUID) -> Optional[ProductVariantResponse]:
        """Get product variant by ID."""
        query = select(ProductVariant).options(
            selectinload(ProductVariant.images)
        ).where(ProductVariant.id == variant_id)
        
        result = await self.db.execute(query)
        variant = result.scalar_one_or_none()
        
        if variant:
            return self._convert_variant_to_response(variant)
        return None

    async def get_product_variants(self, product_id: UUID) -> List[ProductVariantResponse]:
        """Get all variants for a product."""
        query = select(ProductVariant).options(
            selectinload(ProductVariant.images)
        ).where(ProductVariant.product_id == product_id)
        
        result = await self.db.execute(query)
        variants = result.scalars().all()
        
        return [self._convert_variant_to_response(variant) for variant in variants]

    async def generate_qr_code(self, variant_id: UUID) -> Optional[str]:
        """Generate QR code for a product variant."""
        variant = await self.get_variant_by_id(variant_id)
        if not variant:
            return None
        
        # For now, return a placeholder QR code URL
        # In a real implementation, you would generate an actual QR code
        return f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=variant_{variant_id}"

    async def generate_barcode(self, variant_id: UUID) -> Optional[str]:
        """Generate barcode for a product variant."""
        variant = await self.get_variant_by_id(variant_id)
        if not variant:
            return None
        
        # For now, return a placeholder barcode URL
        # In a real implementation, you would generate an actual barcode
        return f"https://barcode.tec-it.com/barcode.ashx?data={variant.sku}&code=Code128&translate-esc=on"

    async def create_product(self, product_data: ProductCreate, supplier_id: UUID) -> ProductResponse:
        """Create a new product."""
        # Create product
        db_product = Product(
            name=product_data.name,
            description=product_data.description,
            category_id=product_data.category_id,
            supplier_id=supplier_id,
            origin=product_data.origin,
            dietary_tags=product_data.dietary_tags or []
        )
        
        self.db.add(db_product)
        await self.db.flush()  # Get the product ID
        
        # Create variants
        for variant_data in product_data.variants:
            db_variant = ProductVariant(
                product_id=db_product.id,
                sku=variant_data.sku,
                name=variant_data.name,
                base_price=variant_data.base_price,
                sale_price=variant_data.sale_price,
                stock=variant_data.stock,
                attributes=variant_data.attributes or {}
            )
            self.db.add(db_variant)
        
        await self.db.commit()
        
        # Return the created product
        return await self.get_product_by_id(db_product.id)

    async def update_product(self, product_id: UUID, product_data: ProductUpdate, user_id: UUID) -> ProductResponse:
        """Update a product."""
        query = select(Product).where(Product.id == product_id)
        result = await self.db.execute(query)
        product = result.scalar_one_or_none()
        
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        # Check if user owns the product (for suppliers) or is admin
        if product.supplier_id != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to update this product")
        
        # Update fields
        for field, value in product_data.dict(exclude_unset=True).items():
            setattr(product, field, value)
        
        await self.db.commit()
        
        # Return the updated product
        return await self.get_product_by_id(product_id)

    async def delete_product(self, product_id: UUID, user_id: UUID):
        """Delete a product."""
        query = select(Product).where(Product.id == product_id)
        result = await self.db.execute(query)
        product = result.scalar_one_or_none()
        
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        # Check if user owns the product (for suppliers) or is admin
        if product.supplier_id != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to delete this product")
        
        await self.db.delete(product)
        await self.db.commit()