from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List, Dict, Any
from uuid import UUID
from core.database import get_db
from core.utils.response import Response
from core.exceptions import APIException
from services.search import SearchService
from services.products import ProductService
from services.user import UserService

router = APIRouter(prefix="/v1/search", tags=["Search"])


@router.get("/autocomplete")
async def autocomplete_search(
    q: str = Query(..., min_length=2, description="Search query (minimum 2 characters)"),
    type: str = Query("product", regex="^(product|user|category)$", description="Search type: product, user, or category"),
    limit: int = Query(10, ge=1, le=20, description="Maximum number of suggestions"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get autocomplete suggestions for search queries.
    
    - **q**: Search query string (minimum 2 characters)
    - **type**: Type of search - "product", "user", or "category"
    - **limit**: Maximum number of suggestions (1-20, default 10)
    
    Returns suggestions with relevance scores for the specified type.
    """
    try:
        search_service = SearchService(db)
        suggestions = await search_service.autocomplete(
            query=q,
            search_type=type,
            limit=limit
        )
        
        return Response(
            success=True,
            data={
                "query": q,
                "type": type,
                "suggestions": suggestions,
                "count": len(suggestions)
            }
        )
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to fetch autocomplete suggestions: {str(e)}"
        )


@router.get("/products")
async def search_products(
    q: str = Query(..., min_length=2, description="Search query"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of results"),
    category_id: Optional[UUID] = Query(None, description="Filter by category ID"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price filter"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price filter"),
    db: AsyncSession = Depends(get_db)
):
    """
    Search products with fuzzy matching and weighted ranking.
    
    - **q**: Search query string (minimum 2 characters)
    - **limit**: Maximum number of results (1-100, default 20)
    - **category_id**: Optional category filter
    - **min_price**: Optional minimum price filter
    - **max_price**: Optional maximum price filter
    
    Returns products ranked by relevance with fuzzy search capabilities.
    """
    try:
        search_service = SearchService(db)
        
        # Build filters
        filters = {}
        if category_id:
            filters["category_id"] = category_id
        if min_price is not None:
            filters["min_price"] = min_price
        if max_price is not None:
            filters["max_price"] = max_price
        
        products = await search_service.fuzzy_search_products(
            query=q,
            limit=limit,
            filters=filters if filters else None
        )
        
        return Response(
            success=True,
            data={
                "query": q,
                "filters": filters,
                "products": products,
                "count": len(products)
            }
        )
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to search products: {str(e)}"
        )


@router.get("/users")
async def search_users(
    q: str = Query(..., min_length=2, description="Search query"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of results"),
    role: Optional[str] = Query(None, regex="^(Customer|Supplier|Admin)$", description="Filter by user role"),
    db: AsyncSession = Depends(get_db)
):
    """
    Search users with prefix matching on name and email.
    
    - **q**: Search query string (minimum 2 characters)
    - **limit**: Maximum number of results (1-100, default 20)
    - **role**: Optional role filter - "Customer", "Supplier", or "Admin"
    
    Returns users ranked by relevance with prefix and fuzzy matching.
    """
    try:
        search_service = SearchService(db)
        
        users = await search_service.search_users(
            query=q,
            limit=limit,
            role_filter=role
        )
        
        return Response(
            success=True,
            data={
                "query": q,
                "role_filter": role,
                "users": users,
                "count": len(users)
            }
        )
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to search users: {str(e)}"
        )


@router.get("/categories")
async def search_categories(
    q: str = Query(..., min_length=2, description="Search query"),
    limit: int = Query(20, ge=1, le=50, description="Maximum number of results"),
    db: AsyncSession = Depends(get_db)
):
    """
    Search categories with prefix matching and fuzzy search.
    
    - **q**: Search query string (minimum 2 characters)
    - **limit**: Maximum number of results (1-50, default 20)
    
    Returns categories ranked by relevance with product counts.
    """
    try:
        search_service = SearchService(db)
        
        categories = await search_service.search_categories(
            query=q,
            limit=limit
        )
        
        return Response(
            success=True,
            data={
                "query": q,
                "categories": categories,
                "count": len(categories)
            }
        )
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to search categories: {str(e)}"
        )