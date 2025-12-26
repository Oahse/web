"""
Maintenance Mode Middleware
Handles maintenance mode functionality
"""
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from core.config import settings
import logging

logger = logging.getLogger(__name__)

class MaintenanceModeMiddleware(BaseHTTPMiddleware):
    """
    Middleware for handling maintenance mode
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.maintenance_enabled = getattr(settings, 'MAINTENANCE_MODE', False)
    
    async def dispatch(self, request: Request, call_next):
        """Process request with maintenance mode check"""
        
        # Skip maintenance check for health endpoints
        if request.url.path in ["/health", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)
        
        # Check if maintenance mode is enabled
        if self.maintenance_enabled:
            # Allow admin users to bypass maintenance mode
            user_is_admin = False
            if hasattr(request.state, "user") and request.state.user:
                user = request.state.user
                if hasattr(user, "role") and user.role and user.role.lower() == "admin":
                    user_is_admin = True
            
            if not user_is_admin:
                return JSONResponse(
                    status_code=503,
                    content={
                        "error": "Service Unavailable",
                        "message": "The service is currently under maintenance. Please try again later.",
                        "maintenance_mode": True
                    },
                    headers={
                        "Retry-After": "3600"  # Suggest retry after 1 hour
                    }
                )
        
        # Continue with request processing
        response = await call_next(request)
        return response