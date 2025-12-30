# Consolidated route imports
from .admin import router as admin_router
from .analytics import router as analytics_router 
from .auth import router as auth_router
from .cart import router as cart_router
from .health import router as health_router
from .inventories import router as inventories_router
from .loyalty import router as loyalty_router
from .notifications import router as notifications_router
from .orders import router as orders_router
from .payments import router as payments_router
from .products import router as products_router
from .refunds import router as refunds_router
from .review import router as review_router
from .search import router as search_router
from .social_auth import router as social_auth_router
from .subscriptions import router as subscriptions_router
from .user import router as user_router
from .webhooks import router as webhooks_router
from .websockets import ws_router as websockets_router
from .wishlist import router as wishlist_router

# Export all routers for easy importing
__all__ = [
    "admin_router",
    "analytics_router",
    "auth_router",
    "cart_router",
    "health_router",
    "inventories_router",
    "loyalty_router",
    "notifications_router",
    "orders_router",
    "payments_router",
    "products_router",
    "refunds_router",
    "review_router",
    "search_router",
    "social_auth_router",
    "subscriptions_router",
    "user_router",
    "webhooks_router",
    "websockets_router",
    "wishlist_router",
]
