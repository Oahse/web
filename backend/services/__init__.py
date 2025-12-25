# Services package - Consolidated imports only

# Core services
from .activity import ActivityService
from .analytics import AnalyticsService
from .auth import AuthService
from .blog import BlogService
from .cart import CartService
from .email import EmailService
from .loyalty import LoyaltyService
from .products import ProductService
from .promocode import PromocodeService
from .review import ReviewService
from .search import SearchService
from .settings import SettingsService
from .shipping import ShippingService
from .tax import TaxService
from .user import UserService, AddressService
from .variant_tracking import VariantTrackingService
from .wishlist import WishlistService
from .websockets import WebSocketService

# Consolidated services - single source of truth
from .orders import OrderService
from .subscriptions import SubscriptionService
from .payments import PaymentService
from .notifications import NotificationService
from .inventories import InventoryService
from .admin import AdminService
from .export import ExportService

# Utility services
from .jinja_template import JinjaTemplateService
from .migration_service import MigrationService
from .template_migration_service import TemplateMigrationService

__all__ = [
    # Core services
    "ActivityService",
    "AnalyticsService",
    "AuthService",
    "BlogService", 
    "CartService",
    "EmailService",
    "LoyaltyService",
    "ProductService",
    "PromocodeService",
    "ReviewService",
    "SearchService",
    "SettingsService",
    "ShippingService",
    "TaxService",
    "UserService",
    "AddressService",
    "VariantTrackingService",
    "WishlistService",
    "WebSocketService",
    
    # Consolidated services
    "OrderService",
    "SubscriptionService", 
    "PaymentService",
    "NotificationService",
    "InventoryService",
    "AdminService",
    "ExportService",
    
    # Utility services
    "JinjaTemplateService",
    "MigrationService",
    "TemplateMigrationService",
]