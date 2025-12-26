"""
Rate Limiting Middleware with Redis Integration
Implements rate limiting using Redis for API protection
"""
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from typing import Dict, Optional
from datetime import datetime
from core.redis import RedisService, RedisKeyManager
from core.config import settings
import logging

logger = logging.getLogger(__name__)

class RateLimitService(RedisService):
    """Redis-based rate limiting service using sliding window algorithm"""
    
    def __init__(self):
        super().__init__()
        
        # Default rate limits (requests per minute)
        self.default_limits = {
            "auth": 10,      # Login/register attempts
            "api": 100,      # General API calls
            "cart": 50,      # Cart operations
            "checkout": 5,   # Checkout attempts
            "search": 30,    # Search requests
            "upload": 10     # File uploads
        }
    
    async def check_rate_limit(
        self, 
        identifier: str, 
        endpoint_type: str = "api",
        custom_limit: Optional[int] = None,
        window_seconds: int = 60
    ) -> Dict[str, any]:
        """Check if request is within rate limit using sliding window"""
        try:
            limit = custom_limit or self.default_limits.get(endpoint_type, self.default_limits["api"])
            rate_limit_key = RedisKeyManager.rate_limit_key(identifier, endpoint_type)
            
            redis_client = await self._get_redis()
            current_time = datetime.utcnow().timestamp()
            window_start = current_time - window_seconds
            
            # Use Redis sorted set for sliding window
            # Remove old entries outside the window
            await redis_client.zremrangebyscore(rate_limit_key, 0, window_start)
            
            # Count current requests in window
            current_count = await redis_client.zcard(rate_limit_key)
            
            if current_count >= limit:
                # Rate limit exceeded
                oldest_requests = await redis_client.zrange(rate_limit_key, 0, 0, withscores=True)
                reset_time = int(oldest_requests[0][1] + window_seconds) if oldest_requests else int(current_time + window_seconds)
                
                return {
                    "allowed": False,
                    "limit": limit,
                    "remaining": 0,
                    "reset_time": reset_time,
                    "retry_after": reset_time - int(current_time)
                }
            
            # Add current request to the window
            await redis_client.zadd(rate_limit_key, {str(current_time): current_time})
            
            # Set expiry for the key (cleanup)
            await redis_client.expire(rate_limit_key, window_seconds + 10)
            
            remaining = limit - current_count - 1
            reset_time = int(current_time + window_seconds)
            
            return {
                "allowed": True,
                "limit": limit,
                "remaining": remaining,
                "reset_time": reset_time,
                "retry_after": 0
            }
            
        except Exception as e:
            logger.error(f"Error checking rate limit for {identifier}: {e}")
            # On error, allow the request (fail open)
            return {
                "allowed": True,
                "limit": self.default_limits.get(endpoint_type, 100),
                "remaining": 99,
                "reset_time": int(datetime.utcnow().timestamp() + 60),
                "retry_after": 0,
                "error": str(e)
            }

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware for Redis-based rate limiting
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.rate_limit_service = RateLimitService()
        
        # Define endpoint types for different rate limits
        self.endpoint_types = {
            "/auth/login": "auth",
            "/auth/register": "auth",
            "/auth/forgot-password": "auth",
            "/cart/": "cart",
            "/orders/checkout": "checkout",
            "/search": "search",
            "/upload": "upload"
        }
    
    async def dispatch(self, request: Request, call_next):
        """Process request with rate limiting"""
        
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)
        
        # Determine identifier (user ID or IP address)
        identifier = None
        if hasattr(request.state, "user_id") and request.state.user_id:
            identifier = request.state.user_id
        elif request.client:
            identifier = request.client.host
        else:
            identifier = "unknown"
        
        # Determine endpoint type
        endpoint_type = "api"  # default
        for path_prefix, ep_type in self.endpoint_types.items():
            if request.url.path.startswith(path_prefix):
                endpoint_type = ep_type
                break
        
        # Check rate limit
        try:
            rate_limit_result = await self.rate_limit_service.check_rate_limit(
                identifier=identifier,
                endpoint_type=endpoint_type
            )
            
            if not rate_limit_result.get("allowed", True):
                # Rate limit exceeded
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": "Rate limit exceeded",
                        "message": f"Too many requests. Try again in {rate_limit_result.get('retry_after', 60)} seconds.",
                        "limit": rate_limit_result.get("limit"),
                        "reset_time": rate_limit_result.get("reset_time")
                    },
                    headers={
                        "X-RateLimit-Limit": str(rate_limit_result.get("limit", 100)),
                        "X-RateLimit-Remaining": str(rate_limit_result.get("remaining", 0)),
                        "X-RateLimit-Reset": str(rate_limit_result.get("reset_time", 0)),
                        "Retry-After": str(rate_limit_result.get("retry_after", 60))
                    }
                )
            
            # Process request
            response = await call_next(request)
            
            # Add rate limit headers to response
            response.headers["X-RateLimit-Limit"] = str(rate_limit_result.get("limit", 100))
            response.headers["X-RateLimit-Remaining"] = str(rate_limit_result.get("remaining", 99))
            response.headers["X-RateLimit-Reset"] = str(rate_limit_result.get("reset_time", 0))
            
            return response
            
        except Exception as e:
            logger.error(f"Rate limiting error: {e}")
            # On error, allow the request (fail open)
            return await call_next(request)