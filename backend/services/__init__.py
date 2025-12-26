# Services package - Consolidated imports only

# Core services
from .activity import ActivityService
from .auth import AuthService
from .blog import BlogService
from .cart import CartService
from .email import EmailService
from .loyalty import LoyaltyService
from .products import ProductService
from .promocode import PromocodeService
from .review import ReviewService
from .search import SearchService
from .shipping import ShippingService
from .tax import TaxService
from .user import UserService, AddressService
from .variant_tracking import VariantTrackingService
from .wishlist import WishlistService
from .websockets import ConnectionManager
from .barcode import BarcodeService

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
from .template_migration_service import TemplateMigrationService

__all__ = [
    # Core services
    "ActivityService",
    "AuthService",
    "BlogService", 
    "CartService",
    "EmailService",
    "LoyaltyService",
    "ProductService",
    "PromocodeService",
    "ReviewService",
    "SearchService",
    "ShippingService",
    "TaxService",
    "UserService",
    "AddressService",
    "VariantTrackingService",
    "WishlistService",
    "ConnectionManager",
    "BarcodeService",
    
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
    "TemplateMigrationService",
]