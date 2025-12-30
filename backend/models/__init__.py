# Models package - Consolidated imports only
from .user import User, Address
from .product import Product, ProductVariant, ProductImage, Category
from .cart import Cart, CartItem
from .review import Review
from .promocode import Promocode
from .shipping import ShippingMethod
from .wishlist import Wishlist, WishlistItem
from .notifications import Notification, NotificationPreference, NotificationHistory
from .loyalty import LoyaltyAccount, PointsTransaction
from .variant_tracking import VariantTrackingEntry, VariantPriceHistory, VariantAnalytics, VariantSubstitution
from .analytics import UserSession, AnalyticsEvent, ConversionFunnel, UserAnalytics 

# Consolidated models - single source of truth
from .orders import Order, OrderItem, TrackingEvent
from .subscriptions import Subscription
from .payments import PaymentMethod, PaymentIntent, Transaction
from .inventories import WarehouseLocation, Inventory, StockAdjustment
from .admin import PricingConfig, SubscriptionCostHistory, SubscriptionAnalytics, PaymentAnalytics

# Import utils if they exist
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
    "Review",

    # Commerce models
    "Promocode",
    "ShippingMethod",

    # Wishlist models
    "Wishlist",
    "WishlistItem",

    # Loyalty models
    "LoyaltyAccount",
    "PointsTransaction",
    
    # Variant tracking models
    "VariantTrackingEntry",
    "VariantPriceHistory",
    "VariantAnalytics",
    "VariantSubstitution",
    
    # Analytics models
    "UserSession",
    "AnalyticsEvent",
    "ConversionFunnel",
    "UserAnalytics",
]
