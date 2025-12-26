from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.exc import SQLAlchemyError
from core.database import AsyncSessionDB, initialize_db, db_manager, DatabaseOptimizer
from services.notifications import NotificationService 
import asyncio 
import os
# Import configuration and middleware
from core.config import settings, validate_startup_environment, get_setup_instructions
from core.middleware import SessionMiddleware, RateLimitMiddleware, CacheMiddleware, MaintenanceModeMiddleware
# Import exceptions and handlers
from core.exceptions import (
    APIException,
    api_exception_handler,
    http_exception_handler,
    validation_exception_handler,
    sqlalchemy_exception_handler,
    general_exception_handler
)
from core.kafka import consume_messages, get_kafka_producer_service, initialize_event_system, start_event_consumer 
from routes.websocket import ws_router
from routes.auth import router as auth_router
from routes.user import router as user_router
from routes.products import router as products_router
from routes.cart import router as cart_router
from routes.orders import router as orders_router
from routes.admin import router as admin_router
# Import WebSocket Kafka consumer
from services.websocket_kafka_consumer import start_websocket_kafka_consumer, stop_websocket_kafka_consumer
from routes.social_auth import router as social_auth_router
from routes.blog import router as blog_router
from routes.subscriptions import router as subscription_router
from routes.review import router as review_router
from routes.payments import router as payment_router
from routes.wishlist import router as wishlist_router
from routes.notifications import router as notification_router
from routes.health import router as health_router
# from routes.negotiator import router as negotiator_router
from routes.search import router as search_router
from routes.inventories import router as inventory_router
from routes.loyalty import router as loyalty_router


from contextlib import asynccontextmanager

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

    # Run database maintenance and optimization
    try:
        async with AsyncSessionDB() as db:
            await DatabaseOptimizer.run_maintenance(db)
    except Exception as e:
        logger.warning(f"Database optimization warning: {e}")

    # Initialize new event system
    try:
        await initialize_event_system()
        logger.info("Event system initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize event system: {e}")
        # Continue without event system for backward compatibility
    
    # Start new event consumer
    try:
        await start_event_consumer()
        logger.info("New event consumer started successfully")
    except Exception as e:
        logger.error(f"Failed to start new event consumer: {e}")

    # Start Kafka Producer (legacy)
    kafka_producer_service = await get_kafka_producer_service()

    # Start Kafka Consumer as a background task (legacy)
    consumer_task = asyncio.create_task(consume_messages())

    # Start WebSocket Kafka Consumer
    try:
        from services.websockets import start_websocket_kafka_consumer
        await start_websocket_kafka_consumer()
        logger.info("WebSocket Kafka consumer started successfully")
    except Exception as e:
        logger.error(f"Failed to start WebSocket Kafka consumer: {e}")

    asyncio.create_task(run_notification_cleanup())
    yield
    # Shutdown event
    # Stop WebSocket Kafka Consumer
    try:
        from services.websockets import stop_websocket_kafka_consumer
        await stop_websocket_kafka_consumer()
        logger.info("WebSocket Kafka consumer stopped successfully")
    except Exception as e:
        logger.error(f"Error stopping WebSocket Kafka consumer: {e}")
    
    # Stop Kafka Producer
    if kafka_producer_service:
        await kafka_producer_service.stop()

    # Cancel Kafka Consumer background task
    consumer_task.cancel()
    try:
        await consumer_task
    except asyncio.CancelledError:
        # Log or handle the cancellation, as it's expected during shutdown
        logger.info("Kafka consumer task cancelled successfully during shutdown.")


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

# Middleware Stack (order matters - last added is executed first)
app.add_middleware(MaintenanceModeMiddleware)
app.add_middleware(CacheMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(SessionMiddleware)


# Include all routers with API versioning v1
app.include_router(auth_router, prefix="/v1")
app.include_router(user_router, prefix="/v1")
app.include_router(products_router, prefix="/v1")
app.include_router(cart_router, prefix="/v1")
app.include_router(orders_router, prefix="/v1")
app.include_router(admin_router, prefix="/v1")
app.include_router(social_auth_router, prefix="/v1")
app.include_router(blog_router, prefix="/v1")
app.include_router(subscription_router, prefix="/v1")
app.include_router(review_router, prefix="/v1")
app.include_router(payment_router, prefix="/v1")
app.include_router(wishlist_router, prefix="/v1")
app.include_router(notification_router, prefix="/v1")
app.include_router(health_router, prefix="/v1")
# app.include_router(negotiator_router, prefix="/v1")
app.include_router(search_router, prefix="/v1")
app.include_router(inventory_router, prefix="/v1")
app.include_router(loyalty_router, prefix="/v1")

# Include WebSocket router
app.include_router(ws_router)

async def run_notification_cleanup():
    # Wait a bit for database initialization to complete
    await asyncio.sleep(5)
    while True:
        try:
            if AsyncSessionDB is not None:
                async with AsyncSessionDB() as db:
                    notification_service = NotificationService(db)
                    await notification_service.delete_old_notifications(days_old=settings.NOTIFICATION_CLEANUP_DAYS)
        except Exception as e:
            print(f"Notification cleanup error: {e}")
            # Continue the loop even if there's an error
        # Run every X seconds
        await asyncio.sleep(settings.NOTIFICATION_CLEANUP_INTERVAL_SECONDS)





@app.get("/")
async def read_root():
    return {
        "service": "Banwee API",
        "status": "Running",
        "version": "1.0.0",
        "description": "Discover premium organic products from Africa. Ethically sourced, sustainably produced, and delivered to your doorstep.",
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
