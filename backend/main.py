import asyncio
import os
from fastapi import FastAPI, HTTPException, APIRouter
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.exc import SQLAlchemyError

from core.database import AsyncSessionDB, initialize_db, db_manager, DatabaseOptimizer
from core.redis import redis_manager
# Import configuration and middleware
from core.config import settings, validate_startup_environment, get_setup_instructions
# Import exceptions and handlers
from core.exceptions import (
    APIException,
    api_exception_handler,
    http_exception_handler,
    validation_exception_handler,
    sqlalchemy_exception_handler,
    general_exception_handler
)

# Import all routers from routes package
from routes import (
    admin_router,
    analytics_router,
    auth_router,
    cart_router,
    health_router,
    inventories_router,
    loyalty_router,
    orders_router,
    payments_router,
    products_router,
    refunds_router,
    review_router,
    search_router,
    social_auth_router,
    subscriptions_router,
    tax_router,
    user_router,
    webhooks_router,
    wishlist_router,
)

from contextlib import asynccontextmanager

async def run_notification_cleanup():
    """Background task to clean up old notifications"""
    while True:
        try:
            # Clean up old notifications every hour
            await asyncio.sleep(3600)
            # Add cleanup logic here if needed
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Notification cleanup error: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup event
    # Validate environment variables first
    from core.config import validate_startup_environment, get_setup_instructions
    import logging
    
    logger = logging.getLogger(__name__)
    logger.info("Validating environment configuration...")
    
    validation_result = validate_startup_environment()
    if not validation_result.is_valid:
        logger.error("Environment validation failed!")
        if validation_result.error_message:
            logger.error(validation_result.error_message)
        
        # Print setup instructions
        instructions = get_setup_instructions()
        logger.error("Setup Instructions:")
        logger.error(instructions)
        
        # For development, just warn instead of failing
        if os.getenv("ENVIRONMENT", "local").lower() in ["local", "development", "dev"]:
            logger.warning("Continuing with invalid environment configuration in development mode")
        else:
            raise RuntimeError("Invalid environment configuration. Please check your .env file.")
    
    logger.info("Environment validation passed ✅")
    if validation_result.warnings:
        for warning in validation_result.warnings:
            logger.warning(warning)
    
    # Initialize the database engine and session factory with optimization
    from core.config import settings # Import settings here to avoid circular dependency
    optimized_engine = DatabaseOptimizer.get_optimized_engine()
    initialize_db(settings.SQLALCHEMY_DATABASE_URI, settings.ENVIRONMENT == "local", engine=optimized_engine)

    # Initialize Redis if enabled
    if settings.ENABLE_REDIS:
        try:
            redis_client = await redis_manager.get_client()
            await redis_client.ping()
            logger.info("Redis connection established ✅")
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
            if settings.ENVIRONMENT != "local":
                raise RuntimeError("Redis connection required for production")

    # Initialize ARQ if enabled
    if settings.ENABLE_ARQ:
        try:
            from core.arq_worker import get_arq_pool
            arq_pool = await get_arq_pool()
            await arq_pool.ping()
            logger.info("ARQ connection established ✅")
        except Exception as e:
            logger.error(f"ARQ connection failed: {e}")
            if settings.ENVIRONMENT != "local":
                raise RuntimeError("ARQ connection required for background tasks")

    # Run database maintenance and optimization
    try:
        async with AsyncSessionDB() as db:
            await DatabaseOptimizer.run_maintenance(db)
    except Exception as e:
        logger.warning(f"Database optimization warning: {e}")

    # Start notification cleanup task
    asyncio.create_task(run_notification_cleanup())
    
    yield
    
    # Shutdown event
    logger.info("Application shutting down...")
    
    # Close Redis connections
    if settings.ENABLE_REDIS:
        try:
            await redis_manager.close()
            logger.info("Redis connections closed")
        except Exception as e:
            logger.error(f"Error closing Redis connections: {e}")


app = FastAPI(
    title="Banwee API",
    description="Discover premium organic products from Africa. Ethically sourced, sustainably produced, and delivered to your doorstep.",
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
 
# Trusted host middleware for security
if hasattr(settings, 'ALLOWED_HOSTS'):
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.ALLOWED_HOSTS
    )

# Middleware Stack (order matters - last added is executed first)
# Note: Rate limiting disabled for MVP (was using Redis)
# app.add_middleware(RateLimitMiddleware)

# API v1 Router
v1_router = APIRouter(prefix="/v1")
v1_router.include_router(auth_router)
v1_router.include_router(user_router)
v1_router.include_router(products_router)
v1_router.include_router(cart_router)
v1_router.include_router(orders_router)
v1_router.include_router(admin_router)
v1_router.include_router(social_auth_router)
v1_router.include_router(subscriptions_router)
v1_router.include_router(review_router)
v1_router.include_router(payments_router)
v1_router.include_router(wishlist_router)
v1_router.include_router(health_router)
v1_router.include_router(search_router)
v1_router.include_router(inventories_router)
v1_router.include_router(loyalty_router)
v1_router.include_router(analytics_router)
v1_router.include_router(refunds_router)
v1_router.include_router(tax_router)
v1_router.include_router(webhooks_router)

# Include the v1 router into the main app
app.include_router(v1_router)

@app.get("/")
async def read_root():
    return {
        "service": "Banwee API",
        "status": "Running",
        "version": "1.0.0",
        "description": "Discover premium organic products from Africa. Ethically sourced, sustainably produced, and delivered to your doorstep.",
    }

# Register exception handlers
app.add_exception_handler(APIException, api_exception_handler)
app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)
