from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, text
from sqlalchemy.orm import selectinload
from typing import Optional, List, Dict, Any
from fastapi import HTTPException
from uuid import UUID
from models.product import Product, ProductVariant, Category, ProductImage
from models.inventories import Inventory
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
        
        # Search configuration
        self.similarity_threshold = 0.3
        self.weights = {
            "exact": 1.0,
            "prefix": 0.8,
            "fuzzy": 0.5
        }
        self.product_field_weights = {
            "name": 1.0,
            "description": 0.6,
            "category": 0.4,
            "tags": 0.3
        }

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
                current_price=getattr(variant, 'sale_price', None) or getattr(
                    variant, 'base_price', 0.0),
                discount_percentage=0,
                stock=getattr(variant.inventory, 'quantity_available', 0) if hasattr(variant, 'inventory') and variant.inventory else 0,
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
                        created_at=product.category.created_at.isoformat(
                        ) if product.category.created_at else "",
                        updated_at=product.category.updated_at.isoformat(
                        ) if product.category.updated_at else None
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
                    variants.append(
                        ProductVariantResponse.model_validate(variant_dict))
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
                price_range=PriceRange(
                    min=product.price_range["min"], max=product.price_range["max"]),
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
        print(
            f"Getting products: page={page}, limit={limit}, filters={filters}")
        offset = (page - 1) * limit

        # Build filter conditions
        base_conditions = [Product.is_active == True]
        
        if filters:
            if filters.get("q"):
                search_term = f"%{filters['q']}%"
                base_conditions.append(
                    or_(
                        Product.name.ilike(search_term),
                        Product.description.ilike(search_term)
                    )
                )
            
            if filters.get("min_rating") is not None:
                base_conditions.append(Product.rating >= filters["min_rating"])
            
            if filters.get("max_rating") is not None:
                base_conditions.append(Product.rating <= filters["max_rating"])
        
        # Build subquery for filtering by category
        if filters and filters.get("category"):
            # Get category first
            cat_query = select(Category.id).where(Category.name == filters['category'])
            cat_result = await self.db.execute(cat_query)
            category_id = cat_result.scalar_one_or_none()
            if category_id:
                base_conditions.append(Product.category_id == category_id)
        
        # Build subquery for filtering by variant properties
        if filters:
            price_filters = []
            if filters.get("min_price") is not None:
                price_filters.append(ProductVariant.base_price >= filters["min_price"])
            
            if filters.get("max_price") is not None:
                price_filters.append(ProductVariant.base_price <= filters["max_price"])
            
            if filters.get("availability") is not None:
                if filters["availability"]:
                    # Join with inventory and check quantity_available > 0
                    price_filters.append(
                        ProductVariant.inventory.has(
                            Inventory.quantity_available > 0
                        )
                    )
                else:
                    # Join with inventory and check quantity_available == 0 or no inventory
                    price_filters.append(
                        or_(
                            ~ProductVariant.inventory.has(),
                            ProductVariant.inventory.has(
                                Inventory.quantity_available == 0
                            )
                        )
                    )
            
            if filters.get("sale"):
                price_filters.append(ProductVariant.sale_price.isnot(None))
            
            if price_filters:
                # Use EXISTS with correlated subquery for better performance
                variant_subquery = (
                    select(1)
                    .where(
                        and_(
                            ProductVariant.product_id == Product.id,
                            *price_filters
                        )
                    )
                    .exists()
                )
                base_conditions.append(variant_subquery)
        
        # Build the main query
        query = (
            select(Product)
            .where(and_(*base_conditions))
            .options(
                selectinload(Product.category),
                selectinload(Product.supplier),
                selectinload(Product.variants).selectinload(ProductVariant.images)
            )
        )

        # Apply sorting
        if hasattr(Product, sort_by):
            if sort_order.lower() == "desc":
                query = query.order_by(getattr(Product, sort_by).desc())
            else:
                query = query.order_by(getattr(Product, sort_by).asc())

        # Get total count for pagination - must match the main query filters
        count_query = select(func.count(Product.id))
        for condition in base_conditions:
            count_query = count_query.where(condition)

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
                selectinload(Product.variants).selectinload(
                    ProductVariant.images),
            )
            .where(Product.featured.is_(True))  # safer than == True
            .order_by(Product.created_at.desc())
            .limit(limit)
        )

        result = await self.db.execute(query)
        products = result.scalars().unique().all()  # ✅ ensure uniqueness with .unique()

        print(f"Found {len(products)} featured products in DB.")
        for p in products:
            print(
                f"  - {p.name} (Featured: {p.featured}, Variants: {len(p.variants)})")

        if not products:
            print(
                "⚠️ No featured products found. Check your DB data or 'featured' column values.")

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
                selectinload(Product.variants).selectinload(
                    ProductVariant.images)
            )
        )

        result = await self.db.execute(query)
        rows = result.all()

        # If no products found (no cart items), fallback to highest rated products
        if not rows:
            fallback_query = select(Product).options(
                selectinload(Product.category),
                selectinload(Product.supplier),
                selectinload(Product.variants).selectinload(
                    ProductVariant.images)
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
            and_(Product.category_id == product.category_id,
                 Product.id != product_id)
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
                product_count=product_count,
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
            # Get product count for this category
            product_count_query = select(func.count(Product.id)).where(
                Product.category_id == category.id,
                Product.is_active == True
            )
            product_count_result = await self.db.execute(product_count_query)
            product_count = product_count_result.scalar()
            
            return CategoryResponse(
                id=category.id,
                name=category.name,
                description=category.description,
                image_url=category.image_url,
                is_active=category.is_active,
                product_count=product_count,
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
        from services.barcode import BarcodeService
        barcode_service = BarcodeService(self.db)
        
        try:
            codes = await barcode_service.generate_variant_codes(variant_id)
            return codes.get("qr_code")
        except Exception as e:
            print(f"Error generating QR code: {e}")
            return None

    async def generate_barcode(self, variant_id: UUID) -> Optional[str]:
        """Generate barcode for a product variant."""
        from services.barcode import BarcodeService
        barcode_service = BarcodeService(self.db)
        
        try:
            codes = await barcode_service.generate_variant_codes(variant_id)
            return codes.get("barcode")
        except Exception as e:
            print(f"Error generating barcode: {e}")
            return None
    
    async def generate_variant_codes(self, variant_id: UUID) -> dict:
        """Generate both barcode and QR code for a product variant."""
        from services.barcode import BarcodeService
        barcode_service = BarcodeService(self.db)
        
        try:
            return await barcode_service.generate_variant_codes(variant_id)
        except Exception as e:
            print(f"Error generating variant codes: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to generate codes: {str(e)}")
    
    async def update_variant_codes(self, variant_id: UUID, barcode: Optional[str] = None, qr_code: Optional[str] = None) -> dict:
        """Update barcode and/or QR code for a product variant."""
        from services.barcode import BarcodeService
        barcode_service = BarcodeService(self.db)
        
        try:
            return await barcode_service.update_variant_codes(variant_id, barcode, qr_code)
        except Exception as e:
            print(f"Error updating variant codes: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to update codes: {str(e)}")

    async def search_products(
        self, 
        query: str, 
        limit: int = 20,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Advanced search for products with fuzzy matching and weighted ranking.
        """
        if not query or len(query.strip()) < 2:
            return []
            
        query = query.strip().lower()
        
        # Build base conditions
        base_conditions = ["p.is_active = true"]
        params = {
            "query": query,
            "similarity_threshold": self.similarity_threshold,
            "limit": limit,
            "exact_weight": self.weights["exact"],
            "prefix_weight": self.weights["prefix"],
            "fuzzy_weight": self.weights["fuzzy"],
            "name_weight": self.product_field_weights["name"],
            "desc_weight": self.product_field_weights["description"],
            "cat_weight": self.product_field_weights["category"],
            "tag_weight": self.product_field_weights["tags"]
        }
        
        # Add filters
        if filters:
            if filters.get("category_id"):
                base_conditions.append("p.category_id = :category_id")
                params["category_id"] = filters["category_id"]
                
            if filters.get("min_price") is not None:
                base_conditions.append("""
                    EXISTS (
                        SELECT 1 FROM product_variants pv 
                        WHERE pv.product_id = p.id 
                        AND pv.base_price >= :min_price
                    )
                """)
                params["min_price"] = filters["min_price"]
                
            if filters.get("max_price") is not None:
                base_conditions.append("""
                    EXISTS (
                        SELECT 1 FROM product_variants pv 
                        WHERE pv.product_id = p.id 
                        AND pv.base_price <= :max_price
                    )
                """)
                params["max_price"] = filters["max_price"]
        
        where_clause = " AND ".join(base_conditions)
        
        sql_query = text(f"""
            SELECT 
                p.id,
                p.name,
                p.description,
                p.rating,
                p.review_count,
                c.name as category_name,
                -- Calculate weighted relevance score
                (
                    -- Name matching (highest weight)
                    CASE WHEN LOWER(p.name) = :query THEN :exact_weight * :name_weight
                         WHEN LOWER(p.name) LIKE CONCAT(:query, '%') THEN :prefix_weight * :name_weight * 0.9
                         WHEN LOWER(p.name) LIKE CONCAT('%', :query, '%') THEN :prefix_weight * :name_weight * 0.7
                         ELSE similarity(LOWER(p.name), :query) * :fuzzy_weight * :name_weight
                    END +
                    -- Description matching
                    CASE WHEN LOWER(p.description) LIKE CONCAT('%', :query, '%') THEN :prefix_weight * :desc_weight
                         ELSE similarity(LOWER(p.description), :query) * :fuzzy_weight * :desc_weight
                    END +
                    -- Category matching
                    CASE WHEN LOWER(c.name) = :query THEN :exact_weight * :cat_weight
                         WHEN LOWER(c.name) LIKE CONCAT(:query, '%') THEN :prefix_weight * :cat_weight
                         WHEN LOWER(c.name) LIKE CONCAT('%', :query, '%') THEN :prefix_weight * :cat_weight * 0.7
                         ELSE similarity(LOWER(c.name), :query) * :fuzzy_weight * :cat_weight
                    END +
                    -- Dietary tags matching (if tags contain the query)
                    CASE WHEN p.dietary_tags::text ILIKE CONCAT('%', :query, '%') THEN :prefix_weight * :tag_weight
                         ELSE 0
                    END +
                    -- Boost for higher rated products
                    (p.rating / 5.0) * 0.1 +
                    -- Boost for products with more reviews
                    LEAST(p.review_count / 100.0, 0.1)
                ) as relevance_score
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE {where_clause}
            AND (
                LOWER(p.name) LIKE CONCAT('%', :query, '%')
                OR LOWER(p.description) LIKE CONCAT('%', :query, '%')
                OR LOWER(c.name) LIKE CONCAT('%', :query, '%')
                OR p.dietary_tags::text ILIKE CONCAT('%', :query, '%')
                OR similarity(LOWER(p.name), :query) > :similarity_threshold
                OR similarity(LOWER(p.description), :query) > :similarity_threshold
                OR similarity(LOWER(c.name), :query) > :similarity_threshold
            )
            ORDER BY relevance_score DESC, p.rating DESC, p.review_count DESC
            LIMIT :limit
        """)
        
        result = await self.db.execute(sql_query, params)
        
        products = []
        for row in result:
            products.append({
                "id": str(row.id),
                "name": row.name,
                "description": row.description,
                "rating": float(row.rating) if row.rating else 0.0,
                "review_count": row.review_count or 0,
                "category_name": row.category_name,
                "relevance_score": float(row.relevance_score),
                "type": "product"
            })
            
        return products

    async def search_categories(
        self, 
        query: str, 
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Search categories with prefix matching and fuzzy search.
        """
        if not query or len(query.strip()) < 2:
            return []
            
        query = query.strip().lower()
        
        sql_query = text("""
            SELECT 
                c.id,
                c.name,
                c.description,
                c.image_url,
                COUNT(p.id) as product_count,
                (
                    -- Name matching (highest weight)
                    CASE WHEN LOWER(c.name) = :query THEN :exact_weight
                         WHEN LOWER(c.name) LIKE CONCAT(:query, '%') THEN :prefix_weight
                         WHEN LOWER(c.name) LIKE CONCAT('%', :query, '%') THEN :prefix_weight * 0.7
                         ELSE similarity(LOWER(c.name), :query) * :fuzzy_weight
                    END +
                    -- Description matching
                    CASE WHEN LOWER(c.description) LIKE CONCAT('%', :query, '%') THEN :prefix_weight * 0.5
                         ELSE similarity(LOWER(c.description), :query) * :fuzzy_weight * 0.5
                    END +
                    -- Boost for categories with more products
                    LEAST(COUNT(p.id) / 10.0, 0.2)
                ) as relevance_score
            FROM categories c
            LEFT JOIN products p ON c.id = p.category_id AND p.is_active = true
            WHERE c.is_active = true
            AND (
                LOWER(c.name) LIKE CONCAT('%', :query, '%')
                OR LOWER(c.description) LIKE CONCAT('%', :query, '%')
                OR similarity(LOWER(c.name), :query) > :similarity_threshold
                OR similarity(LOWER(c.description), :query) > :similarity_threshold
            )
            GROUP BY c.id, c.name, c.description, c.image_url
            ORDER BY relevance_score DESC, product_count DESC
            LIMIT :limit
        """)
        
        result = await self.db.execute(sql_query, {
            "query": query,
            "similarity_threshold": self.similarity_threshold,
            "limit": limit,
            "exact_weight": self.weights["exact"],
            "prefix_weight": self.weights["prefix"],
            "fuzzy_weight": self.weights["fuzzy"]
        })
        
        categories = []
        for row in result:
            categories.append({
                "id": str(row.id),
                "name": row.name,
                "description": row.description,
                "image_url": row.image_url,
                "product_count": row.product_count,
                "relevance_score": float(row.relevance_score),
                "type": "category"
            })
            
        return categories

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
        for v_idx, variant_data in enumerate(product_data.variants):
            # Auto-generate SKU: PROD-{product_id[:8]}-{variant_index}
            # Format: First 3 chars of product name + first 8 chars of product ID + variant index
            product_prefix = db_product.name[:3].upper().replace(' ', '')
            auto_sku = f"{product_prefix}-{str(db_product.id)[:8]}-{v_idx}"
            final_sku = variant_data.sku if variant_data.sku else auto_sku
            
            # Create variant first to get the ID
            db_variant = ProductVariant(
                product_id=db_product.id,
                sku=final_sku,
                name=variant_data.name,
                barcode=None,  # Will be set after generation
                qr_code=None,  # Will be set after generation
                base_price=variant_data.base_price,
                sale_price=variant_data.sale_price,
                attributes=variant_data.attributes or {}
            )
            self.db.add(db_variant)
            await self.db.flush()  # Get variant ID
            
            # Now generate barcode and QR code with the actual variant ID
            from services.barcode import BarcodeService
            barcode_service = BarcodeService(self.db)
            
            # Generate QR code data for this specific variant
            qr_data = f"https://banwee.com/products/variant/{db_variant.id}"
            
            try:
                barcode_b64 = barcode_service.generate_barcode(final_sku)
                qr_code_b64 = barcode_service.generate_qr_code(qr_data)
                
                # Update the variant with generated codes
                db_variant.barcode = barcode_b64
                db_variant.qr_code = qr_code_b64
                
            except Exception as e:
                print(f"Warning: Failed to generate codes for variant {final_sku}: {e}")
                # Leave as None if generation fails
            
            # Create inventory record for the variant
            if hasattr(variant_data, 'stock') and variant_data.stock is not None:
                from models.inventories import Inventory, WarehouseLocation
                
                # Get or create default warehouse location
                default_location_result = await self.db.execute(
                    select(WarehouseLocation).where(WarehouseLocation.name == "Default")
                )
                default_location = default_location_result.scalar_one_or_none()
                
                if not default_location:
                    default_location = WarehouseLocation(
                        name="Default",
                        description="Default warehouse location"
                    )
                    self.db.add(default_location)
                    await self.db.flush()
                
                # Create inventory record
                inventory = Inventory(
                    variant_id=db_variant.id,
                    location_id=default_location.id,
                    quantity_available=variant_data.stock,
                    quantity_reserved=0,
                    low_stock_threshold=10
                )
                self.db.add(inventory)
            
            # Create variant images from CDN URLs
            if variant_data.image_urls:
                from models.product import ProductImage
                for img_idx, image_url in enumerate(variant_data.image_urls):
                    db_image = ProductImage(
                        variant_id=db_variant.id,
                        url=image_url,
                        is_primary=(img_idx == 0),  # First image is primary
                        sort_order=img_idx
                    )
                    self.db.add(db_image)

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
            raise HTTPException(
                status_code=403, detail="Not authorized to update this product")

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
            raise HTTPException(
                status_code=403, detail="Not authorized to delete this product")

        await self.db.delete(product)
        await self.db.commit()
