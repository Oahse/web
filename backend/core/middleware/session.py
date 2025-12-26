"""
Session Middleware with Redis Integration
Handles user sessions using Redis for performance and scalability
"""
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from typing import Optional, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime, timedelta
from core.redis import RedisService, RedisKeyManager
from core.config import settings
import logging
import json

logger = logging.getLogger(__name__)

class SessionService(RedisService):
    """Redis-based session service integrated into middleware"""
    
    def __init__(self):
        super().__init__()
        self.session_expiry = 24 * 3600  # 24 hours in seconds
        self.remember_me_expiry = 30 * 24 * 3600  # 30 days for remember me
    
    async def create_session(
        self, 
        user_id: UUID, 
        user_data: Dict[str, Any],
        remember_me: bool = False,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create new user session in Redis"""
        try:
            if not session_id:
                session_id = str(uuid4())
            
            session_key = RedisKeyManager.session_key(session_id)
            
            session_data = {
                "session_id": session_id,
                "user_id": str(user_id),
                "user_data": user_data,
                "created_at": datetime.utcnow().isoformat(),
                "last_accessed": datetime.utcnow().isoformat(),
                "remember_me": remember_me,
                "ip_address": None,
                "user_agent": None
            }
            
            expiry = self.remember_me_expiry if remember_me else self.session_expiry
            
            success = await self.set_with_expiry(session_key, session_data, expiry)
            
            if success:
                return {
                    "success": True,
                    "session_id": session_id,
                    "expires_in": expiry
                }
            else:
                return {"success": False, "error": "Failed to create session"}
                
        except Exception as e:
            logger.error(f"Error creating session: {e}")
            return {"success": False, "error": "Session creation failed"}
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data from Redis"""
        try:
            session_key = RedisKeyManager.session_key(session_id)
            session_data = await self.get_data(session_key)
            
            if session_data:
                # Update last accessed time
                session_data["last_accessed"] = datetime.utcnow().isoformat()
                
                # Refresh expiry
                expiry = self.remember_me_expiry if session_data.get("remember_me") else self.session_expiry
                await self.set_with_expiry(session_key, session_data, expiry)
                
                return session_data
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting session {session_id}: {e}")
            return None
    
    async def update_session(self, session_id: str, updates: Dict[str, Any]) -> bool:
        """Update session data"""
        try:
            session_key = RedisKeyManager.session_key(session_id)
            session_data = await self.get_data(session_key)
            
            if not session_data:
                return False
            
            # Update session data
            session_data.update(updates)
            session_data["last_accessed"] = datetime.utcnow().isoformat()
            
            # Save with appropriate expiry
            expiry = self.remember_me_expiry if session_data.get("remember_me") else self.session_expiry
            return await self.set_with_expiry(session_key, session_data, expiry)
            
        except Exception as e:
            logger.error(f"Error updating session {session_id}: {e}")
            return False
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete session from Redis"""
        try:
            session_key = RedisKeyManager.session_key(session_id)
            return await self.delete_key(session_key)
            
        except Exception as e:
            logger.error(f"Error deleting session {session_id}: {e}")
            return False

class SessionMiddleware(BaseHTTPMiddleware):
    """
    Middleware for Redis-based session management
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.session_service = SessionService()
        self.session_cookie_name = "session_id"
    
    async def dispatch(self, request: Request, call_next):
        """Process request with Redis session handling"""
        
        # Skip session handling for health checks and static files
        if request.url.path in ["/health", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)
        
        # Get session ID from cookie or header
        session_id = request.cookies.get(self.session_cookie_name)
        if not session_id:
            session_id = request.headers.get("X-Session-ID")
        
        # Validate session if present
        if session_id:
            try:
                session_data = await self.session_service.get_session(session_id)
                if session_data:
                    # Store session data in request state
                    request.state.session_id = session_id
                    request.state.user_id = session_data.get("user_id")
                    request.state.session_data = session_data
                    
                    # Update session metadata
                    await self.session_service.update_session(session_id, {
                        "ip_address": request.client.host if request.client else None,
                        "user_agent": request.headers.get("user-agent")
                    })
            except Exception as e:
                logger.error(f"Session validation error: {e}")
        
        # Process request
        response = await call_next(request)
        
        return response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from typing import Optional
import time
import logging
from uuid import UUID
from services.redis_session import RedisSessionService
from services.redis_rate_limit import RedisRateLimitService
from core.config import settings

logger = logging.getLogger(__name__)

class RedisSessionMiddleware(BaseHTTPMiddleware):
    """
    Middleware for Redis-based session management
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.session_service = RedisSessionService()
        self.session_cookie_name = "session_id"
    
    async def dispatch(self, request: Request, call_next):
        """Process request with Redis session handling"""
        
        # Skip session handling for health checks and static files
        if request.url.path in ["/health", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)
        
        # Get session ID from cookie or header
        session_id = request.cookies.get(self.session_cookie_name)
        if not session_id:
            session_id = request.headers.get("X-Session-ID")
        
        # Validate session if present
        user_data = None
        if session_id:
            try:
                session_result = await self.session_service.validate_session(session_id)
                if session_result.get("valid"):
                    user_data = session_result.get("user_data")
                    # Store session data in request state
                    request.state.session_id = session_id
                    request.state.user_id = session_result.get("user_id")
                    request.state.session_data = session_result.get("session_data")
                    
                    # Update session metadata
                    await self.session_service.update_session(session_id, {
                        "ip_address": request.client.host if request.client else None,
                        "user_agent": request.headers.get("user-agent")
                    })
            except Exception as e:
                logger.error(f"Session validation error: {e}")
        
        # Process request
        response = await call_next(request)
        
        return response

class RedisRateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware for Redis-based rate limiting
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.rate_limit_service = RedisRateLimitService()
        
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

class RedisHealthMiddleware(BaseHTTPMiddleware):
    """
    Middleware to monitor Redis health and add to request context
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next):
        """Add Redis health status to request context"""
        
        # Check Redis health
        redis_healthy = True
        try:
            from core.redis import get_redis
            redis_client = await get_redis()
            await redis_client.ping()
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            redis_healthy = False
        
        # Add to request state
        request.state.redis_healthy = redis_healthy
        
        # Process request
        response = await call_next(request)
        
        # Add Redis health header
        response.headers["X-Redis-Status"] = "healthy" if redis_healthy else "unhealthy"
        
        return response