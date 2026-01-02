import asyncio
import os
from fastapi import FastAPI, HTTPException, APIRouter
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.exc import SQLAlchemyError

from core.database import AsyncSessionDB, initialize_db, db_manager, DatabaseOptimizer
# Import configuration and middleware
from core.config import settings, validate_startup_environment, get_setup_instructions
from core.middleware import RateLimitMiddleware
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

# Import all routers from routes package
from routes import (
    admin_router,
    analytics_router,
    auth_router,
    cart_router,
    health_router,
    inventories_router,
    loyalty_router,
    notifications_router,
    orders_router,
    payments_router,
    products_router,
    refunds_router,
    review_router,
    search_router,
    social_auth_router,
    subscriptions_router,
    user_router,
    webhooks_router,
    websockets_router,
    wishlist_router,
)

from services.notifications import NotificationService 
# Import WebSocket Kafka consumer
from services.websockets import start_websocket_kafka_consumer, stop_websocket_kafka_consumer


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

    # Initialize new event system (skip in development if Kafka is not available)
    kafka_enabled = os.getenv("ENABLE_KAFKA", "true").lower() == "true"
    if kafka_enabled:
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
        try:
            kafka_producer_service = await get_kafka_producer_service()
            # Start Kafka Consumer as a background task (legacy)
            consumer_task = asyncio.create_task(consume_messages())
        except Exception as e:
            logger.error(f"Failed to start Kafka services: {e}")
            kafka_producer_service = None
            consumer_task = None
    else:
        logger.info("Kafka disabled via ENABLE_KAFKA=false")
        kafka_producer_service = None
        consumer_task = None

    # Start WebSocket Kafka Consumer
    try:
        from services.websockets import start_websocket_kafka_consumer
        await start_websocket_kafka_consumer()
        logger.info("WebSocket Kafka consumer started successfully")
    except Exception as e:
        logger.error(f"Failed to start WebSocket Kafka consumer: {e}")

    # Start Subscription Scheduler
    try:
        from tasks.subscription_tasks import subscription_task_manager
        asyncio.create_task(subscription_task_manager.start_subscription_scheduler())
        logger.info("Subscription scheduler started successfully")
    except Exception as e:
        logger.error(f"Failed to start subscription scheduler: {e}")

    asyncio.create_task(run_notification_cleanup())
    yield
    # Shutdown event
    # Stop Subscription Scheduler
    try:
        from tasks.subscription_tasks import subscription_task_manager
        subscription_task_manager.stop_subscription_scheduler()
        logger.info("Subscription scheduler stopped successfully")
    except Exception as e:
        logger.error(f"Error stopping subscription scheduler: {e}")
    
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
    if consumer_task:
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
 
# Trusted host middleware for security
if hasattr(settings, 'ALLOWED_HOSTS'):
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.ALLOWED_HOSTS
    )

# Middleware Stack (order matters - last added is executed first)
# app.add_middleware(MaintenanceModeMiddleware)
# app.add_middleware(CacheMiddleware)
app.add_middleware(RateLimitMiddleware)

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
v1_router.include_router(notifications_router)
v1_router.include_router(health_router)
v1_router.include_router(search_router)
v1_router.include_router(inventories_router)
v1_router.include_router(loyalty_router)
v1_router.include_router(analytics_router)
v1_router.include_router(refunds_router)
v1_router.include_router(webhooks_router)

# Include the v1 router into the main app
app.include_router(v1_router)

# Include WebSocket router
app.include_router(websockets_router)

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

# Register exception handlers
app.add_exception_handler(APIException, api_exception_handler)
app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)
