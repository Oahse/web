# Models package - Consolidated imports only
from .user import User, Address
from .product import Product, ProductVariant, ProductImage, Category
from .cart import Cart, CartItem
from .blog import BlogPost
from .review import Review
from .promocode import Promocode
from .shipping import ShippingMethod
from .wishlist import Wishlist, WishlistItem
from .activity_log import ActivityLog
from .webhook_event import WebhookEvent
from .loyalty import LoyaltyAccount, PointsTransaction
from .variant_tracking import VariantTrackingEntry, VariantPriceHistory, VariantAnalytics, VariantSubstitution

# Consolidated models - single source of truth
from .orders import Order, OrderItem, TrackingEvent
from .subscriptions import Subscription
from .payments import PaymentMethod, PaymentIntent, Transaction
from .notifications import Notification, NotificationPreference, NotificationHistory
from .inventories import WarehouseLocation, Inventory, StockAdjustment
from .admin import PricingConfig, SubscriptionCostHistory, SubscriptionAnalytics, PaymentAnalytics

# Import settings and utils if they exist
try:
    from .settings import Settings
except ImportError:
    pass

try:
    from .utils import ModelUtils
except ImportError:
    pass

__all__ = [
    # User models
    "User",
    "Address",

    # Product models
    "Product",
    "ProductVariant",
    "ProductImage",
    "Category",

    # Cart models
    "Cart",
    "CartItem",

    # Order models (consolidated)
    "Order",
    "OrderItem",
    "TrackingEvent",

    # Subscription models (consolidated)
    "Subscription",

    # Payment models (consolidated)
    "PaymentMethod",
    "PaymentIntent",
    "Transaction",

    # Notification models (consolidated)
    "Notification",
    "NotificationPreference",
    "NotificationHistory",

    # Inventory models (consolidated)
    "WarehouseLocation",
    "Inventory",
    "StockAdjustment",

    # Admin models (consolidated)
    "PricingConfig",
    "SubscriptionCostHistory",
    "SubscriptionAnalytics",
    "PaymentAnalytics",

    # Content models
    "BlogPost",
    "Review",

    # Commerce models
    "Promocode",
    "ShippingMethod",

    # Wishlist models
    "Wishlist",
    "WishlistItem",

    # Activity models
    "ActivityLog",
    
    # Webhook models
    "WebhookEvent",
    
    # Loyalty models
    "LoyaltyAccount",
    "PointsTransaction",
    
    # Variant tracking models
    "VariantTrackingEntry",
    "VariantPriceHistory",
    "VariantAnalytics",
    "VariantSubstitution",
]
