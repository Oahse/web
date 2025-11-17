from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from uuid import UUID
from core.database import get_db
from core.utils.response import Response
from core.exceptions import APIException
from schemas.product import ProductCreate, ProductUpdate
from services.products import ProductService
from models.user import User
from services.auth import AuthService
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_auth_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> User:
    return await AuthService.get_current_user(token, db)

router = APIRouter(prefix="/api/v1/products", tags=["Products"])
# /products?sort_by=created_at&sort_order=desc&page=1&limit=12
@router.get("/")
async def get_products(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    category: Optional[str] = None,
    q: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    min_rating: Optional[int] = Query(None, ge=1, le=5),
    max_rating: Optional[int] = Query(None, ge=1, le=5),
    sort_by: Optional[str] = Query("created_at"),
    sort_order: Optional[str] = Query("desc"),
    availability: Optional[bool] = None,
    featured: Optional[bool] = None,
    popular: Optional[bool] = None,
    sale: Optional[bool] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get products with optional filtering and pagination."""
    try:
        product_service = ProductService(db)
        
        filters = {
            "category": category,
            "q": q,
            "min_price": min_price,
            "max_price": max_price,
            "min_rating": min_rating,
            "max_rating": max_rating,
            "availability": availability,
            "featured": featured,
            "popular": popular,
            "sale": sale
        }
        
        result = await product_service.get_products(
            page=page,
            limit=limit,
            filters=filters,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        return Response(success=True, data=result)
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to fetch products {str(e)}"
        )

# @router.get("/featured")
# async def get_featured_products(
#     limit: int = Query(4, ge=1, le=20),
#     db: AsyncSession = Depends(get_db)
# ):
#     """Get featured products."""
#     try:
#         product_service = ProductService(db)
#         products = await product_service.get_featured_products(limit)
#         return Response(success=True, data=products)
#     except Exception as e:
#         raise APIException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#              message=f"Failed to fetch featured products {str(e)}"
#         )

# @router.get("/popular")
# async def get_popular_products(
#     limit: int = Query(4, ge=1, le=20),
#     db: AsyncSession = Depends(get_db)
# ):
#     """Get featured products."""
#     try:
#         product_service = ProductService(db)
#         products = await product_service.get_popular_products(limit)
#         return Response(success=True, data=products)
#     except Exception as e:
#         raise APIException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#              message="Failed to fetch popular products"
#         )

@router.get("/categories")
async def get_categories(db: AsyncSession = Depends(get_db)):
    """Get all product categories."""
    try:
        product_service = ProductService(db)
        categories = await product_service.get_categories()
        return Response(success=True, data=categories)
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
             message=f"Failed to fetch categories {str(e)}"
        )

@router.get("/{product_id}/recommendations")
async def get_recommended_products(
    product_id: UUID,
    limit: int = Query(4, ge=1, le=20),
    db: AsyncSession = Depends(get_db)
):
    """Get recommended products based on a product."""
    try:
        product_service = ProductService(db)
        products = await product_service.get_recommended_products(product_id, limit)
        return Response(success=True, data=products)
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
             message=f"Failed to fetch recommended products - {str(e)}"
        )

@router.get("/{product_id}/variants")
async def get_product_variants(
    product_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get all variants for a product."""
    try:
        product_service = ProductService(db)
        variants = await product_service.get_product_variants(product_id)
        return Response(success=True, data=variants)
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to fetch product variants - {str(e)}"
        )

@router.get("/variants/{variant_id}")
async def get_variant(
    variant_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific product variant by ID."""
    try:
        product_service = ProductService(db)
        variant = await product_service.get_variant_by_id(variant_id)
        if not variant:
            raise APIException(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Product variant not found"
            )
        return Response(success=True, data=variant)
    except APIException:
        raise
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to fetch product variant - {str(e)}"
        )

@router.get("/variants/{variant_id}/qrcode")
async def get_variant_qr_code(
    variant_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get QR code for a product variant."""
    try:
        product_service = ProductService(db)
        qr_code_url = await product_service.generate_qr_code(variant_id)
        if not qr_code_url:
            raise APIException(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Product variant not found"
            )
        return Response(success=True, data={"qr_code_url": qr_code_url})
    except APIException:
        raise
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to generate QR code - {str(e)}"
        )

@router.get("/variants/{variant_id}/barcode")
async def get_variant_barcode(
    variant_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get barcode for a product variant."""
    try:
        product_service = ProductService(db)
        barcode_url = await product_service.generate_barcode(variant_id)
        if not barcode_url:
            raise APIException(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Product variant not found"
            )
        return Response(success=True, data={"barcode_url": barcode_url})
    except APIException:
        raise
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to generate barcode - {str(e)}"
        )

@router.get("/{product_id}")
async def get_product(
    product_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific product by ID."""
    try:
        print(f"Fetching product with ID: {product_id}")
        product_service = ProductService(db)
        product = await product_service.get_product_by_id(product_id)
        if not product:
            raise APIException(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Product not found"
            )
        print(f"Successfully fetched product: {product.name}")
        return Response(success=True, data=product)
    except APIException:
        raise
    except Exception as e:
        print(f"Error fetching product {product_id}: {e}")
        import traceback
        traceback.print_exc()
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to fetch product: {str(e)}"
        )

@router.get("/categories/{category_id}")
async def get_category(
    category_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific category by ID."""
    try:
        category_service = ProductService(db)
        category = await category_service.get_category_by_id(category_id)
        if not category:
            raise APIException(
                status_code=status.HTTP_404_NOT_FOUND,
                 message="Category not found"
            )
        return Response(success=True, data=category)
    except APIException:
        raise
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
             message="Failed to fetch category"
        )

@router.post("/")
async def create_product(
    product_data: ProductCreate,
    current_user: User = Depends(get_current_auth_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new product (suppliers only)."""
    try:
        if current_user.role not in ["Supplier", "Admin"]:
            raise APIException(
                status_code=status.HTTP_403_FORBIDDEN,
                 message="Only suppliers can create products"
            )
        
        product_service = ProductService(db)
        product = await product_service.create_product(product_data, current_user.id)
        return Response(success=True, data=product, message="Product created successfully")
    except APIException:
        raise
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
             message="Failed to create product"
        )

@router.put("/{product_id}")
async def update_product(
    product_id: UUID,
    product_data: ProductUpdate,
    current_user: User = Depends(get_current_auth_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a product (suppliers only)."""
    try:
        product_service = ProductService(db)
        product = await product_service.update_product(product_id, product_data, current_user.id)
        return Response(success=True, data=product, message="Product updated successfully")
    except APIException:
        raise
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
             message="Failed to update product"
        )

@router.delete("/{product_id}")
async def delete_product(
    product_id: UUID,
    current_user: User = Depends(get_current_auth_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a product (suppliers only)."""
    try:
        product_service = ProductService(db)
        await product_service.delete_product(product_id, current_user.id)
        return Response(success=True, message="Product deleted successfully")
    except APIException:
        raise
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
             message="Failed to delete product"
        )