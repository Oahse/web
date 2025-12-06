import json
import time
from typing import List, Dict, Any, Optional
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from starlette.types import ASGIApp
from fastapi import status

from backend.services.settings import SettingsService
from backend.services.activity import ActivityService # NEW: Import ActivityService
from backend.core.database import AsyncSessionDB
from backend.core.constants import UserRole


# Helper function to filter sensitive data from request body
def filter_sensitive_data(data: Dict[str, Any]) -> Dict[str, Any]:
    sensitive_fields = ["password", "token", "access_token", "refresh_token", "secret"]
    filtered_data = data.copy()
    for field in sensitive_fields:
        if field in filtered_data:
            filtered_data[field] = "[FILTERED]"
    return filtered_data


class MaintenanceModeMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        # Allow health checks to pass through always
        if request.url.path == "/health" or request.url.path.startswith("/health/"):
            return await call_next(request)

        # Create a new async session for this request
        async with AsyncSessionDB() as session:
            settings_service = SettingsService(session)
            maintenance_enabled = await settings_service.is_maintenance_mode_enabled()

            if maintenance_enabled:
                user_is_admin = False
                # Attempt to get user from request state if authentication middleware has run
                # This assumes an authentication middleware runs BEFORE this one and sets request.state.user
                if hasattr(request.state, "user") and request.state.user:
                    user = request.state.user
                    # Assuming user object has a 'role' attribute (e.g., from an ORM model or Pydantic schema)
                    if hasattr(user, "role") and user.role.lower() == UserRole.ADMIN.value:
                        user_is_admin = True
                
                if not user_is_admin:
                    maintenance_message = await settings_service.get_maintenance_mode_message()
                    return JSONResponse(
                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        content={"detail": maintenance_message}
                    )
        
        response = await call_next(request)
        return response


class ActivityLoggingMiddleware(BaseHTTPMiddleware): # NEW: Activity Logging Middleware
    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        user_id: Optional[str] = None
        
        # Try to get user from request state (set by authentication middleware)
        if hasattr(request.state, "user") and request.state.user:
            user_id = str(request.state.user.id)

        # Read request body if applicable (only for POST, PUT, PATCH)
        request_body: Optional[Dict[str, Any]] = None
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                # Read the request body as bytes, then decode and parse
                body_bytes = await request.body()
                if body_bytes:
                    request_body = json.loads(body_bytes.decode('utf-8'))
                    request_body = filter_sensitive_data(request_body)
            except json.JSONDecodeError:
                request_body = {"error": "Could not parse JSON body"}
            except Exception as e:
                request_body = {"error": f"Failed to read body: {e}"}


        response = await call_next(request)

        process_time = time.time() - start_time
        
        # Log activity after response is generated
        async with AsyncSessionDB() as session:
            activity_service = ActivityService(session)
            await activity_service.log_activity(
                action_type=f"API_REQUEST_{request.method}",
                description=f"Request to {request.url.path} completed with status {response.status_code}",
                user_id=user_id,
                metadata={
                    "request_method": request.method,
                    "request_path": request.url.path,
                    "client_host": request.client.host if request.client else None,
                    "response_status_code": response.status_code,
                    "process_time": f"{process_time:.4f}s",
                    "request_body": request_body,
                    # Add more relevant data from request/response if needed
                }
            )

        return response