from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.exc import SQLAlchemyError
from core.database import AsyncSessionDB, initialize_db, db_manager  # Add this import
from services.notification import NotificationService  # Add this import
import asyncio  # Add this import
from core.middleware import MaintenanceModeMiddleware, ActivityLoggingMiddleware  # Add this import
# Import exceptions and handlers
from core.exceptions import (
    APIException,
    api_exception_handler,
    http_exception_handler,
    validation_exception_handler,
    sqlalchemy_exception_handler,
    general_exception_handler
)
from core.config import settings
from routes.websockets import ws_router
from routes.auth import router as auth_router
from routes.user import router as user_router
from routes.products import router as products_router
from routes.cart import router as cart_router
from routes.orders import router as orders_router
from routes.admin import router as admin_router
from routes.analytics import router as analytics_router
from routes.social_auth import router as social_auth_router
from routes.blog import router as blog_router
from routes.subscription import router as subscription_router
from routes.review import router as review_router
from routes.payment import payment_method_router, payment_router
from routes.wishlist import router as wishlist_router
from routes.notification import router as notification_router
from routes.health import router as health_router
from routes.negotiator import router as negotiator_router

from routes.inventory import router as inventory_router


from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup event
    # Initialize the database engine and session factory
    from core.config import settings # Import settings here to avoid circular dependency
    initialize_db(settings.SQLALCHEMY_DATABASE_URI, settings.ENVIRONMENT == "local")
    
    asyncio.create_task(run_notification_cleanup())
    yield
    # Shutdown event (if any)
    # For example, gracefully stop background tasks here


app = FastAPI(
    title="Banwee API",
    description="E-commerce platform with user management, product catalog, and order tracking.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Add standard FastAPI middleware
# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS if hasattr(
        settings, 'BACKEND_CORS_ORIGINS') else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Session middleware for session management
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY
)

# Trusted host middleware for security
if hasattr(settings, 'ALLOWED_HOSTS'):
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.ALLOWED_HOSTS
    )

# Maintenance Mode Middleware (NEW ADDITION)
app.add_middleware(MaintenanceModeMiddleware)

# Activity Logging Middleware (NEW ADDITION)
app.add_middleware(ActivityLoggingMiddleware)


# Include all routers with API versioning
app.include_router(auth_router)
app.include_router(user_router)
app.include_router(products_router)
app.include_router(cart_router)
app.include_router(orders_router)
app.include_router(admin_router)
app.include_router(analytics_router)
app.include_router(social_auth_router)
app.include_router(blog_router)
app.include_router(subscription_router)
app.include_router(review_router)
app.include_router(payment_method_router)
app.include_router(payment_router)
app.include_router(wishlist_router)
app.include_router(notification_router)
app.include_router(health_router)
app.include_router(negotiator_router)
app.include_router(inventory_router)

# Include WebSocket router
app.include_router(ws_router)

async def run_notification_cleanup():
    while True:
        async with AsyncSessionDB() as db:
            notification_service = NotificationService(db)
            await notification_service.delete_old_notifications(days_old=settings.NOTIFICATION_CLEANUP_DAYS)
        # Run every X seconds
        await asyncio.sleep(settings.NOTIFICATION_CLEANUP_INTERVAL_SECONDS)





@app.get("/")
async def read_root():
    return {
        "service": "Banwee API",
        "status": "Running",
        "version": "1.0.0",
        "description": "E-commerce platform with user management, product catalog, and order tracking",
    }

# Legacy health endpoint - redirects to new health router


@app.get("/health")
async def legacy_health_check():
    """Legacy health check endpoint - use /health/ for detailed checks."""
    return {
        "status": "healthy",
        "service": "Banwee API",
        "version": "1.0.0",
        "note": "Use /health/ endpoints for detailed health checks"
    }


# Register exception handlers
app.add_exception_handler(APIException, api_exception_handler)
app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)
