"""
Cache Middleware with Redis Integration
Handles product caching, response caching, and cache invalidation
"""
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from core.redis import RedisService, RedisKeyManager
from core.config import settings
import logging
import json
import hashlib

logger = logging.getLogger(__name__)

class CacheService(RedisService):
    """Unified Redis-based caching service for all application caching needs"""
    
    def __init__(self):
        super().__init__()
        # Response caching TTLs
        self.response_cache_ttls = {
            "/products": 1800,  # 30 minutes
            "/categories": 3600,  # 1 hour
            "/brands": 3600,     # 1 hour
        }
        
        # Product caching TTLs
        self.product_cache_expiry = 3600  # 1 hour
        self.product_list_cache_expiry = 1800  # 30 minutes
        self.inventory_cache_expiry = 300  # 5 minutes
    
    # Response Caching Methods
    async def get_cached_response(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached response"""
        try:
            return await self.get_data(cache_key)
        except Exception as e:
            logger.error(f"Error getting cached response for {cache_key}: {e}")
            return None
    
    async def cache_response(
        self, 
        cache_key: str, 
        response_data: Dict[str, Any], 
        expiry_seconds: int = 3600
    ) -> bool:
        """Cache response data"""
        try:
            return await self.set_with_expiry(cache_key, response_data, expiry_seconds)
        except Exception as e:
            logger.error(f"Error caching response for {cache_key}: {e}")
            return False
    
    # Product Caching Methods
    async def cache_product(self, product_data: Dict[str, Any]) -> bool:
        """Cache a single product with all its data"""
        try:
            product_id = product_data.get("id")
            if not product_id:
                return False
            
            cache_key = RedisKeyManager.product_cache_key(str(product_id))
            return await self.set_with_expiry(cache_key, product_data, self.product_cache_expiry)
            
        except Exception as e:
            logger.error(f"Error caching product: {e}")
            return False
    
    async def get_cached_product(self, product_id: UUID) -> Optional[Dict[str, Any]]:
        """Get product from cache"""
        try:
            cache_key = RedisKeyManager.product_cache_key(str(product_id))
            return await self.get_data(cache_key)
            
        except Exception as e:
            logger.error(f"Error getting cached product {product_id}: {e}")
            return None
    
    async def cache_product_list(
        self, 
        filters: Dict[str, Any], 
        products_data: List[Dict[str, Any]],
        total_count: int,
        page: int = 1,
        limit: int = 20
    ) -> bool:
        """Cache a product list with filters"""
        try:
            # Generate cache key based on filters
            filters_hash = RedisKeyManager.generate_filters_hash(filters)
            cache_key = RedisKeyManager.product_list_cache_key(filters_hash)
            
            # Cache data structure
            cache_data = {
                "products": products_data,
                "total_count": total_count,
                "page": page,
                "limit": limit,
                "filters": filters,
                "cached_at": datetime.utcnow().isoformat()
            }
            
            return await self.set_with_expiry(cache_key, cache_data, self.product_list_cache_expiry)
            
        except Exception as e:
            logger.error(f"Error caching product list: {e}")
            return False
    
    async def get_cached_product_list(
        self, 
        filters: Dict[str, Any],
        page: int = 1,
        limit: int = 20
    ) -> Optional[Dict[str, Any]]:
        """Get cached product list"""
        try:
            filters_hash = RedisKeyManager.generate_filters_hash(filters)
            cache_key = RedisKeyManager.product_list_cache_key(filters_hash)
            
            cached_data = await self.get_data(cache_key)
            
            if cached_data and cached_data.get("page") == page and cached_data.get("limit") == limit:
                return cached_data
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting cached product list: {e}")
            return None
    
    async def cache_inventory_status(self, variant_id: UUID, quantity: int) -> bool:
        """Cache inventory status for quick stock checks"""
        try:
            cache_key = f"inventory:{variant_id}"
            inventory_data = {
                "variant_id": str(variant_id),
                "quantity": quantity,
                "in_stock": quantity > 0,
                "cached_at": datetime.utcnow().isoformat()
            }
            
            return await self.set_with_expiry(cache_key, inventory_data, self.inventory_cache_expiry)
            
        except Exception as e:
            logger.error(f"Error caching inventory for variant {variant_id}: {e}")
            return False
    
    async def get_cached_inventory_status(self, variant_id: UUID) -> Optional[Dict[str, Any]]:
        """Get cached inventory status"""
        try:
            cache_key = f"inventory:{variant_id}"
            return await self.get_data(cache_key)
            
        except Exception as e:
            logger.error(f"Error getting cached inventory for variant {variant_id}: {e}")
            return None
    
    # Cache Invalidation Methods
    async def invalidate_product_cache(self, product_id: UUID) -> bool:
        """Invalidate cache for a specific product"""
        try:
            cache_key = RedisKeyManager.product_cache_key(str(product_id))
            return await self.delete_key(cache_key)
            
        except Exception as e:
            logger.error(f"Error invalidating product cache {product_id}: {e}")
            return False
    
    async def invalidate_product_list_cache(self) -> int:
        """Invalidate all product list caches"""
        try:
            return await self.invalidate_cache_pattern(f"{RedisKeyManager.PRODUCT_CACHE_PREFIX}:list:*")
        except Exception as e:
            logger.error(f"Error invalidating product list cache: {e}")
            return 0
    
    async def invalidate_cache_pattern(self, pattern: str) -> int:
        """Invalidate cache keys matching pattern"""
        try:
            redis_client = await self._get_redis()
            deleted_count = 0
            
            async for key in redis_client.scan_iter(match=pattern):
                await redis_client.delete(key)
                deleted_count += 1
            
            return deleted_count
        except Exception as e:
            logger.error(f"Error invalidating cache pattern {pattern}: {e}")
            return 0
    
    async def warm_product_cache(self, db: AsyncSession, limit: int = 100) -> Dict[str, int]:
        """Warm up cache with popular/recent products"""
        try:
            from models.product import Product
            from sqlalchemy.orm import selectinload
            
            # Fetch most recent products
            result = await db.execute(
                select(Product)
                .options(
                    selectinload(Product.variants).selectinload(Product.variants.images),
                    selectinload(Product.variants).selectinload(Product.variants.inventory),
                    selectinload(Product.images)
                )
                .order_by(Product.created_at.desc())
                .limit(limit)
            )
            products = result.scalars().all()
            
            cached_count = 0
            for product in products:
                product_data = await self._serialize_product(product)
                if await self.cache_product(product_data):
                    cached_count += 1
            
            logger.info(f"Warmed cache with {cached_count} products")
            return {
                "products_cached": cached_count,
                "total_attempted": len(products)
            }
            
        except Exception as e:
            logger.error(f"Error warming cache: {e}")
            return {"products_cached": 0, "total_attempted": 0}
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            redis_client = await self._get_redis()
            
            # Count cached products
            product_pattern = f"{RedisKeyManager.PRODUCT_CACHE_PREFIX}:*"
            product_count = 0
            async for key in redis_client.scan_iter(match=product_pattern):
                if ":list:" not in key.decode('utf-8'):  # Exclude list caches
                    product_count += 1
            
            # Count cached product lists
            list_pattern = f"{RedisKeyManager.PRODUCT_CACHE_PREFIX}:list:*"
            list_count = 0
            async for key in redis_client.scan_iter(match=list_pattern):
                list_count += 1
            
            # Count cached inventory
            inventory_pattern = "inventory:*"
            inventory_count = 0
            async for key in redis_client.scan_iter(match=inventory_pattern):
                inventory_count += 1
            
            # Count response cache
            response_pattern = "cache:response:*"
            response_count = 0
            async for key in redis_client.scan_iter(match=response_pattern):
                response_count += 1
            
            return {
                "cached_products": product_count,
                "cached_product_lists": list_count,
                "cached_inventory_items": inventory_count,
                "cached_responses": response_count,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {
                "cached_products": 0,
                "cached_product_lists": 0,
                "cached_inventory_items": 0,
                "cached_responses": 0,
                "error": str(e)
            }
    
    async def _serialize_product(self, product) -> Dict[str, Any]:
        """Serialize product object for caching"""
        try:
            # Serialize variants
            variants = []
            for variant in product.variants:
                variant_data = {
                    "id": str(variant.id),
                    "name": variant.name,
                    "sku": variant.sku,
                    "base_price": float(variant.base_price),
                    "sale_price": float(variant.sale_price) if variant.sale_price else None,
                    "weight": float(variant.weight) if variant.weight else None,
                    "dimensions": variant.dimensions,
                    "color": variant.color,
                    "size": variant.size,
                    "material": variant.material,
                    "is_active": variant.is_active,
                    "images": [
                        {
                            "id": str(img.id),
                            "url": img.url,
                            "alt_text": img.alt_text,
                            "is_primary": img.is_primary,
                            "sort_order": img.sort_order
                        }
                        for img in variant.images
                    ] if variant.images else [],
                    "inventory": {
                        "quantity": variant.inventory.quantity if variant.inventory else 0,
                        "in_stock": variant.inventory.quantity > 0 if variant.inventory else False
                    }
                }
                variants.append(variant_data)
            
            # Serialize main product
            product_data = {
                "id": str(product.id),
                "name": product.name,
                "description": product.description,
                "short_description": product.short_description,
                "category_id": str(product.category_id) if product.category_id else None,
                "brand": product.brand,
                "is_active": product.is_active,
                "is_featured": product.is_featured,
                "meta_title": product.meta_title,
                "meta_description": product.meta_description,
                "created_at": product.created_at.isoformat() if product.created_at else None,
                "updated_at": product.updated_at.isoformat() if product.updated_at else None,
                "variants": variants,
                "images": [
                    {
                        "id": str(img.id),
                        "url": img.url,
                        "alt_text": img.alt_text,
                        "is_primary": img.is_primary,
                        "sort_order": img.sort_order
                    }
                    for img in product.images
                ] if product.images else [],
                "cached_at": datetime.utcnow().isoformat()
            }
            
            return product_data
            
        except Exception as e:
            logger.error(f"Error serializing product {product.id}: {e}")
            return {}

class CacheMiddleware(BaseHTTPMiddleware):
    """
    Unified middleware for Redis-based caching (response caching and product caching)
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.cache_service = CacheService()
    
    def _generate_cache_key(self, request: Request) -> str:
        """Generate cache key for request"""
        # Include path, query parameters, and user context
        path = request.url.path
        query = str(request.url.query) if request.url.query else ""
        user_id = getattr(request.state, "user_id", "anonymous")
        
        # Create hash of the request components
        cache_components = f"{path}:{query}:{user_id}"
        cache_hash = hashlib.md5(cache_components.encode()).hexdigest()
        
        return f"cache:response:{cache_hash}"
    
    def _is_cacheable(self, request: Request) -> tuple[bool, int]:
        """Check if request is cacheable and return TTL"""
        # Only cache GET requests
        if request.method != "GET":
            return False, 0
        
        # Check if endpoint is in cacheable list
        for endpoint, ttl in self.cache_service.response_cache_ttls.items():
            if request.url.path.startswith(endpoint):
                return True, ttl
        
        return False, 0
    
    async def dispatch(self, request: Request, call_next):
        """Process request with unified caching"""
        
        # Check if request is cacheable
        is_cacheable, ttl = self._is_cacheable(request)
        
        if not is_cacheable:
            response = await call_next(request)
            # Add cache service to request state for use in routes
            request.state.cache_service = self.cache_service
            return response
        
        # Generate cache key
        cache_key = self._generate_cache_key(request)
        
        # Try to get cached response
        try:
            cached_response = await self.cache_service.get_cached_response(cache_key)
            
            if cached_response:
                logger.debug(f"Cache hit for {request.url.path}")
                # Return cached response
                from fastapi.responses import JSONResponse
                response = JSONResponse(
                    content=cached_response["content"],
                    status_code=cached_response.get("status_code", 200)
                )
                response.headers["X-Cache"] = "HIT"
                response.headers["X-Cache-Key"] = cache_key
                return response
        
        except Exception as e:
            logger.error(f"Cache retrieval error: {e}")
        
        # Add cache service to request state for use in routes
        request.state.cache_service = self.cache_service
        
        # Cache miss - process request
        response = await call_next(request)
        
        # Cache successful responses
        if response.status_code == 200:
            try:
                # Read response body
                response_body = b""
                async for chunk in response.body_iterator:
                    response_body += chunk
                
                # Parse JSON response
                response_content = json.loads(response_body.decode())
                
                # Cache the response
                cache_data = {
                    "content": response_content,
                    "status_code": response.status_code,
                    "cached_at": datetime.utcnow().isoformat()
                }
                
                await self.cache_service.cache_response(cache_key, cache_data, ttl)
                
                # Recreate response with cached indicator
                from fastapi.responses import JSONResponse
                new_response = JSONResponse(content=response_content)
                new_response.headers["X-Cache"] = "MISS"
                new_response.headers["X-Cache-Key"] = cache_key
                
                # Copy original headers
                for key, value in response.headers.items():
                    if key.lower() not in ["content-length", "content-type"]:
                        new_response.headers[key] = value
                
                return new_response
                
            except Exception as e:
                logger.error(f"Cache storage error: {e}")
        
        # Add cache miss header to original response
        response.headers["X-Cache"] = "MISS"
        return response