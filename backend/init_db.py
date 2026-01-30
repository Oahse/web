#!/usr/bin/env python3
"""
Database Seeding Script for Banwee E-commerce API

This script provides data seeding capabilities for the Banwee database:
- Seeds essential tax rates (required for system operation)
- Seeds comprehensive sample data for development/testing
- Uses actual models from the models/ directory
- Assumes schema is managed by Alembic migrations

Features:
- Batch processing for efficient seeding (configurable batch size)
- Comprehensive error handling and logging
- Realistic sample data generation
- Essential business data seeding (tax rates, etc.)

Schema Management:
- Use 'alembic upgrade head' to create/update tables
- Use 'alembic downgrade base' to remove tables
- This script focuses only on data seeding

Usage:
    # Seed only essential data (tax rates)
    python init_db.py
    
    # Seed essential data + sample data
    python init_db.py --seed
    
    # Legacy mode: recreate tables + seed data
    python init_db.py --force-recreate --seed
"""

import asyncio
import sys
import random
import hashlib
import argparse
from datetime import datetime, timedelta
from uuid import uuid4, UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text, delete
from sqlalchemy.orm import selectinload
from core.db import db_manager, initialize_db
from core.config import settings
from core.utils.encryption import PasswordManager
from core.utils.uuid_utils import uuid7

# Import models locally to avoid conflicts
def get_models():
    """Import models dynamically to avoid registry conflicts"""
    from models.user import User, Address
    from models.product import Product, ProductVariant, ProductImage, Category
    from models.cart import Cart, CartItem
    from models.review import Review
    from models.promocode import Promocode
    from models.shipping import ShippingMethod
    from models.wishlist import Wishlist, WishlistItem
    from models.loyalty import LoyaltyAccount, PointsTransaction
    from models.analytics import UserSession, AnalyticsEvent
    from models.refunds import Refund, RefundItem
    from models.tax_rates import TaxRate
    from models.shipping_tracking import ShipmentTracking, ShippingCarrier
    from models.orders import Order, OrderItem, TrackingEvent
    from models.subscriptions import Subscription, SubscriptionProduct
    from models.payments import PaymentMethod, PaymentIntent, Transaction
    from models.inventories import WarehouseLocation, Inventory, StockAdjustment
    from models.admin import PricingConfig, SubscriptionCostHistory
    from models.discounts import Discount, SubscriptionDiscount
    from models.validation_rules import TaxValidationRule, ShippingValidationRule
    
    return {
        'User': User, 'Address': Address,
        'Product': Product, 'ProductVariant': ProductVariant, 'ProductImage': ProductImage, 'Category': Category,
        'Cart': Cart, 'CartItem': CartItem,
        'Review': Review,
        'Promocode': Promocode,
        'ShippingMethod': ShippingMethod,
        'Wishlist': Wishlist, 'WishlistItem': WishlistItem,
        'LoyaltyAccount': LoyaltyAccount, 'PointsTransaction': PointsTransaction,
        'UserSession': UserSession, 'AnalyticsEvent': AnalyticsEvent,
        'Refund': Refund, 'RefundItem': RefundItem,
        'TaxRate': TaxRate,
        'ShipmentTracking': ShipmentTracking, 'ShippingCarrier': ShippingCarrier,
        'Order': Order, 'OrderItem': OrderItem, 'TrackingEvent': TrackingEvent,
        'Subscription': Subscription, 'SubscriptionProduct': SubscriptionProduct,
        'PaymentMethod': PaymentMethod, 'PaymentIntent': PaymentIntent, 'Transaction': Transaction,
        'WarehouseLocation': WarehouseLocation, 'Inventory': Inventory, 'StockAdjustment': StockAdjustment,
        'PricingConfig': PricingConfig, 'SubscriptionCostHistory': SubscriptionCostHistory,
        'Discount': Discount, 'SubscriptionDiscount': SubscriptionDiscount,
        'TaxValidationRule': TaxValidationRule, 'ShippingValidationRule': ShippingValidationRule,
    }

# Global tax rates data
GLOBAL_TAX_RATES = [
    {"country_code": "US", "country_name": "United States", "province_code": None, "province_name": None, "tax_rate": 0.0, "tax_name": "No Tax"},
    {"country_code": "CA", "country_name": "Canada", "province_code": "ON", "province_name": "Ontario", "tax_rate": 0.13, "tax_name": "HST"},
    {"country_code": "CA", "country_name": "Canada", "province_code": "QC", "province_name": "Quebec", "tax_rate": 0.14975, "tax_name": "GST + QST"},
    {"country_code": "CA", "country_name": "Canada", "province_code": "BC", "province_name": "British Columbia", "tax_rate": 0.12, "tax_name": "GST + PST"},
    {"country_code": "GB", "country_name": "United Kingdom", "province_code": None, "province_name": None, "tax_rate": 0.20, "tax_name": "VAT"},
    {"country_code": "DE", "country_name": "Germany", "province_code": None, "province_name": None, "tax_rate": 0.19, "tax_name": "MwSt"},
    {"country_code": "FR", "country_name": "France", "province_code": None, "province_name": None, "tax_rate": 0.20, "tax_name": "TVA"},
    {"country_code": "IT", "country_name": "Italy", "province_code": None, "province_name": None, "tax_rate": 0.22, "tax_name": "IVA"},
    {"country_code": "ES", "country_name": "Spain", "province_code": None, "province_name": None, "tax_rate": 0.21, "tax_name": "IVA"},
    {"country_code": "NL", "country_name": "Netherlands", "province_code": None, "province_name": None, "tax_rate": 0.21, "tax_name": "BTW"},
    {"country_code": "AU", "country_name": "Australia", "province_code": None, "province_name": None, "tax_rate": 0.10, "tax_name": "GST"},
    {"country_code": "JP", "country_name": "Japan", "province_code": None, "province_name": None, "tax_rate": 0.10, "tax_name": "Consumption Tax"},
    {"country_code": "CN", "country_name": "China", "province_code": None, "province_name": None, "tax_rate": 0.13, "tax_name": "VAT"},
    {"country_code": "IN", "country_name": "India", "province_code": None, "province_name": None, "tax_rate": 0.18, "tax_name": "GST"},
    {"country_code": "BR", "country_name": "Brazil", "province_code": None, "province_name": None, "tax_rate": 0.17, "tax_name": "ICMS"},
    {"country_code": "MX", "country_name": "Mexico", "province_code": None, "province_name": None, "tax_rate": 0.16, "tax_name": "IVA"},
]

# Sample data constants for Agricultural E-commerce
CATEGORIES = [
    {"name": "Cereal Crops", "description": "Grains and cereals like wheat, rice, corn, barley"},
    {"name": "Brands", "description": "Agricultural brands and certified products"},
    {"name": "Legumes", "description": "Beans, lentils, peas, and other leguminous crops"},
    {"name": "Fruits & Vegetables", "description": "Fresh fruits and vegetables"},
    {"name": "Oilseeds", "description": "Seeds used for oil extraction like soybeans, sunflower"},
    {"name": "Fibers", "description": "Natural fibers like cotton, jute, hemp"},
    {"name": "Spices and Herbs", "description": "Culinary spices, herbs, and seasonings"},
    {"name": "Meat, Fish & Sweeteners", "description": "Livestock, fish, honey, and natural sweeteners"},
    {"name": "Nuts, Flowers & Beverages", "description": "Tree nuts, flowers, coffee, tea, and other beverages"},
]

PRODUCTS = [
    {"name": "Organic Wheat", "category": "Cereal Crops", "price": 12.99, "description": "Premium organic wheat grains, high protein content", "dietary_tags": ["organic", "whole-grain", "high-protein"]},
    {"name": "Basmati Rice", "category": "Cereal Crops", "price": 18.50, "description": "Long-grain aromatic basmati rice", "dietary_tags": ["gluten-free", "aromatic", "long-grain"]},
    {"name": "Corn", "category": "Cereal Crops", "price": 6.75, "description": "Sweet yellow corn kernels", "dietary_tags": ["gluten-free", "non-gmo", "sweet"]},
    {"name": "Organic Lentils", "category": "Legumes", "price": 9.99, "description": "High-quality organic lentils", "dietary_tags": ["organic", "high-protein", "gluten-free"]},
    {"name": "Fresh Tomatoes", "category": "Fruits & Vegetables", "price": 4.99, "description": "Vine-ripened fresh tomatoes", "dietary_tags": ["fresh", "vine-ripened", "non-gmo"]},
    {"name": "Apples", "category": "Fruits & Vegetables", "price": 7.25, "description": "Crisp red apples", "dietary_tags": ["fresh", "crisp", "natural"]},
    {"name": "Soybeans", "category": "Oilseeds", "price": 8.75, "description": "Non-GMO soybeans for oil extraction", "dietary_tags": ["non-gmo", "high-protein", "organic"]},
    {"name": "Sunflower Seeds", "category": "Oilseeds", "price": 5.50, "description": "Premium sunflower seeds", "dietary_tags": ["organic", "high-protein", "gluten-free"]},
    {"name": "Cotton Bolls", "category": "Fibers", "price": 3.75, "description": "Raw cotton bolls for textile production", "dietary_tags": ["natural", "textile-grade", "raw"]},
    {"name": "Hemp Seeds", "category": "Fibers", "price": 11.25, "description": "Nutritious hemp seeds for food and fiber", "dietary_tags": ["organic", "high-protein", "gluten-free"]},
    {"name": "Black Pepper", "category": "Spices and Herbs", "price": 8.99, "description": "Premium black pepper corns", "dietary_tags": ["organic", "spice", "whole-pepper"]},
    {"name": "Raw Honey", "category": "Meat, Fish & Sweeteners", "price": 15.99, "description": "Pure raw honey from local farms", "dietary_tags": ["raw", "natural", "unprocessed"]},
    {"name": "Almonds", "category": "Nuts, Flowers & Beverages", "price": 22.50, "description": "Premium quality almonds", "dietary_tags": ["organic", "high-protein", "gluten-free"]},
    {"name": "Coffee Beans", "category": "Nuts, Flowers & Beverages", "price": 19.99, "description": "Premium arabica coffee beans", "dietary_tags": ["organic", "arabica", "medium-roast"]},
    {"name": "Turmeric Powder", "category": "Spices and Herbs", "price": 12.75, "description": "Pure turmeric powder", "dietary_tags": ["organic", "spice", "anti-inflammatory"]},
]

PRODUCT_VARIANTS = [
    # Organic Wheat variants
    {"product_name": "Organic Wheat", "name": "Organic Wheat - 5kg", "price": 12.99, "sale_price": 11.99, "sku": "WHT-ORG-5KG", "barcode": "1234567890123", "qr_code": "QR-WHT-ORG-5KG", "attributes": {"weight": "5kg", "grade": "premium", "organic": True}},
    {"product_name": "Organic Wheat", "name": "Organic Wheat - 10kg", "price": 24.99, "sale_price": 22.99, "sku": "WHT-ORG-10KG", "barcode": "1234567890124", "qr_code": "QR-WHT-ORG-10KG", "attributes": {"weight": "10kg", "grade": "premium", "organic": True}},
    {"product_name": "Organic Wheat", "name": "Organic Wheat - 25kg", "price": 59.99, "sale_price": 54.99, "sku": "WHT-ORG-25KG", "barcode": "1234567890125", "qr_code": "QR-WHT-ORG-25KG", "attributes": {"weight": "25kg", "grade": "premium", "organic": True}},
    
    # Basmati Rice variants
    {"product_name": "Basmati Rice", "name": "Basmati Rice - 2kg", "price": 18.50, "sku": "RICE-BSM-2KG", "barcode": "2345678901234", "qr_code": "QR-RICE-BSM-2KG", "attributes": {"weight": "2kg", "origin": "India", "aromatic": True}},
    {"product_name": "Basmati Rice", "name": "Basmati Rice - 5kg", "price": 45.99, "sale_price": 42.99, "sku": "RICE-BSM-5KG", "barcode": "2345678901235", "qr_code": "QR-RICE-BSM-5KG", "attributes": {"weight": "5kg", "origin": "India", "aromatic": True}},
    {"product_name": "Basmati Rice", "name": "Basmati Rice - 10kg", "price": 89.99, "sale_price": 84.99, "sku": "RICE-BSM-10KG", "barcode": "2345678901236", "qr_code": "QR-RICE-BSM-10KG", "attributes": {"weight": "10kg", "origin": "India", "aromatic": True}},
    
    # Soybeans variants
    {"product_name": "Soybeans", "name": "Soybeans - 1kg", "price": 8.75, "sku": "SOY-1KG", "barcode": "3456789012345", "qr_code": "QR-SOY-1KG", "attributes": {"weight": "1kg", "type": "non-GMO", "protein_content": "36%"}},
    {"product_name": "Soybeans", "name": "Soybeans - 5kg", "price": 42.99, "sale_price": 39.99, "sku": "SOY-5KG", "barcode": "3456789012346", "qr_code": "QR-SOY-5KG", "attributes": {"weight": "5kg", "type": "non-GMO", "protein_content": "36%"}},
    
    # Fresh Tomatoes variants
    {"product_name": "Fresh Tomatoes", "name": "Tomatoes - 500g", "price": 4.99, "sku": "TOM-500G", "barcode": "4567890123456", "qr_code": "QR-TOM-500G", "attributes": {"weight": "500g", "freshness": "vine-ripened", "variety": "beefsteak"}},
    {"product_name": "Fresh Tomatoes", "name": "Tomatoes - 1kg", "price": 8.99, "sku": "TOM-1KG", "barcode": "4567890123457", "qr_code": "QR-TOM-1KG", "attributes": {"weight": "1kg", "freshness": "vine-ripened", "variety": "beefsteak"}},
    
    # Coffee Beans variants
    {"product_name": "Coffee Beans", "name": "Coffee Beans - 250g", "price": 19.99, "sku": "COF-250G", "barcode": "5678901234567", "qr_code": "QR-COF-250G", "attributes": {"weight": "250g", "roast": "medium", "origin": "Colombia"}},
    {"product_name": "Coffee Beans", "name": "Coffee Beans - 500g", "price": 37.99, "sale_price": 34.99, "sku": "COF-500G", "barcode": "5678901234568", "qr_code": "QR-COF-500G", "attributes": {"weight": "500g", "roast": "medium", "origin": "Colombia"}},
    {"product_name": "Coffee Beans", "name": "Coffee Beans - 1kg", "price": 69.99, "sale_price": 64.99, "sku": "COF-1KG", "barcode": "5678901234569", "qr_code": "QR-COF-1KG", "attributes": {"weight": "1kg", "roast": "medium", "origin": "Colombia"}},
]

PRODUCT_IMAGES = [
    {"product_name": "Organic Wheat", "url": "https://example.com/images/wheat.jpg", "alt_text": "Organic wheat grains", "is_primary": True},
    {"product_name": "Basmati Rice", "url": "https://example.com/images/rice.jpg", "alt_text": "Basmati rice grains", "is_primary": True},
    {"product_name": "Soybeans", "url": "https://example.com/images/soybeans.jpg", "alt_text": "Soybeans", "is_primary": True},
    {"product_name": "Fresh Tomatoes", "url": "https://example.com/images/tomatoes.jpg", "alt_text": "Fresh tomatoes", "is_primary": True},
    {"product_name": "Coffee Beans", "url": "https://example.com/images/coffee.jpg", "alt_text": "Coffee beans", "is_primary": True},
    {"product_name": "Turmeric Powder", "url": "https://example.com/images/turmeric.jpg", "alt_text": "Turmeric powder", "is_primary": True},
    {"product_name": "Almonds", "url": "https://example.com/images/almonds.jpg", "alt_text": "Almonds", "is_primary": True},
    {"product_name": "Raw Honey", "url": "https://example.com/images/honey.jpg", "alt_text": "Raw honey", "is_primary": True},
]

USERS = [
    {
        "email": "admin@agrihub.com", 
        "first_name": "Admin", 
        "last_name": "User", 
        "role": "admin",
        "phone": "+1-555-0101",
        "phone_verified": True,
        "country": "US",
        "language": "en",
        "timezone": "America/New_York",
        "avatar_url": "https://example.com/avatars/admin.jpg",
        "age": "35",
        "gender": "other",
        "preferences": {"notifications": "all", "theme": "light", "currency": "USD"}
    },
    {
        "email": "farmer.john@agrihub.com", 
        "first_name": "John", 
        "last_name": "Farmer", 
        "role": "supplier",
        "phone": "+1-555-0102",
        "phone_verified": True,
        "country": "US",
        "language": "en",
        "timezone": "America/Chicago",
        "avatar_url": "https://example.com/avatars/john.jpg",
        "age": "42",
        "gender": "male",
        "preferences": {"notifications": "email_only", "theme": "light", "currency": "USD"}
    },
    {
        "email": "buyer.sarah@agrihub.com", 
        "first_name": "Sarah", 
        "last_name": "Buyer", 
        "role": "customer",
        "phone": "+1-555-0103",
        "phone_verified": True,
        "country": "US",
        "language": "en",
        "timezone": "America/New_York",
        "avatar_url": "https://example.com/avatars/sarah.jpg",
        "age": "28",
        "gender": "female",
        "preferences": {"notifications": "all", "theme": "dark", "currency": "USD"}
    },
    {
        "email": "distributor.mike@agrihub.com", 
        "first_name": "Mike", 
        "last_name": "Distributor", 
        "is_admin": False, 
        "role": "customer",
        "phone": "+1-555-0104",
        "phone_verified": True,
        "country": "US",
        "language": "en",
        "timezone": "America/Chicago",
        "avatar_url": "https://example.com/avatars/mike.jpg",
        "age": "45",
        "gender": "male",
        "preferences": {"notifications": "important_only", "theme": "light", "currency": "USD"}
    },
    {
        "email": "retailer.jane@agrihub.com", 
        "first_name": "Jane", 
        "last_name": "Retailer", 
        "is_admin": False, 
        "role": "customer",
        "phone": "+1-555-0105",
        "phone_verified": False,
        "country": "US",
        "language": "en",
        "timezone": "America/Los_Angeles",
        "avatar_url": "https://example.com/avatars/jane.jpg",
        "age": "31",
        "gender": "female",
        "preferences": {"notifications": "email_only", "theme": "light", "currency": "USD"}
    },
]

SHIPPING_METHODS = [
    {"name": "Standard Ground", "price": 8.99, "estimated_days": 5, "carrier": "AgriShip"},
    {"name": "Express Delivery", "price": 15.99, "estimated_days": 2, "carrier": "AgriShip Express"},
    {"name": "Bulk Freight", "price": 45.99, "estimated_days": 7, "carrier": "BulkTrans"},
]

PROMO_CODES = [
    {"code": "FARMFRESH10", "discount_type": "percentage", "value": 10.0, "min_order": 50.0},
    {"code": "BULKSAVE20", "discount_type": "percentage", "value": 20.0, "min_order": 200.0},
    {"code": "FREESHIP75", "discount_type": "fixed", "value": 8.99, "min_order": 75.0},
    {"code": "ORGANIC15", "discount_type": "percentage", "value": 15.0, "min_order": 100.0},
]

WAREHOUSES = [
    {"name": "Main Distribution Center", "location": "Kansas City, MO", "description": "Primary agricultural distribution hub"},
    {"name": "West Coast Warehouse", "location": "Fresno, CA", "description": "West coast agricultural products center"},
    {"name": "East Coast Facility", "location": "Richmond, VA", "description": "East coast distribution facility"},
    {"name": "International Hub", "location": "Miami, FL", "description": "International import/export facility"},
]

# Additional comprehensive data for all models
ADDRESSES = [
    {"user_email": "farmer.john@agrihub.com", "street": "123 Farm Road", "city": "Des Moines", "state": "IA", "post_code": "50301", "country": "US", "kind": "shipping", "is_default": True},
    {"user_email": "farmer.john@agrihub.com", "street": "456 Billing Ave", "city": "Des Moines", "state": "IA", "post_code": "50302", "country": "US", "kind": "billing", "is_default": True},
    {"user_email": "buyer.sarah@agrihub.com", "street": "789 Market Street", "city": "Chicago", "state": "IL", "post_code": "60601", "country": "US", "kind": "shipping", "is_default": True},
    {"user_email": "buyer.sarah@agrihub.com", "street": "321 Commerce Blvd", "city": "Chicago", "state": "IL", "post_code": "60602", "country": "US", "kind": "billing", "is_default": False},
    {"user_email": "distributor.mike@agrihub.com", "street": "555 Distribution Way", "city": "Atlanta", "state": "GA", "post_code": "30301", "country": "US", "kind": "shipping", "is_default": True},
    {"user_email": "retailer.jane@agrihub.com", "street": "999 Retail Plaza", "city": "Los Angeles", "state": "CA", "post_code": "90001", "country": "US", "kind": "shipping", "is_default": True},
]

CARTS = [
    {"user_email": "buyer.sarah@agrihub.com"},
    {"user_email": "distributor.mike@agrihub.com"},
    {"user_email": "retailer.jane@agrihub.com"},
]

CART_ITEMS = [
    {"user_email": "buyer.sarah@agrihub.com", "product_name": "Organic Wheat - 5kg", "quantity": 2, "price_per_unit": 12.99},
    {"user_email": "buyer.sarah@agrihub.com", "product_name": "Fresh Tomatoes - 1kg", "quantity": 3, "price_per_unit": 8.99},
    {"user_email": "distributor.mike@agrihub.com", "product_name": "Basmati Rice - 5kg", "quantity": 1, "price_per_unit": 45.99},
    {"user_email": "distributor.mike@agrihub.com", "product_name": "Coffee Beans - 500g", "quantity": 4, "price_per_unit": 37.99},
    {"user_email": "retailer.jane@agrihub.com", "product_name": "Organic Lentils - 1kg", "quantity": 2, "price_per_unit": 9.99},
]

REVIEWS = [
    {"user_email": "buyer.sarah@agrihub.com", "product_name": "Organic Wheat", "rating": 5, "title": "Excellent Quality", "comment": "Great organic wheat, very fresh! Perfect for our bakery.", "is_verified_purchase": True, "is_approved": True},
    {"user_email": "distributor.mike@agrihub.com", "product_name": "Basmati Rice", "rating": 4, "title": "Good Product", "comment": "Nice aromatic rice, customers love it. Good value for bulk orders.", "is_verified_purchase": True, "is_approved": True},
    {"user_email": "retailer.jane@agrihub.com", "product_name": "Coffee Beans", "rating": 5, "title": "Premium Quality", "comment": "Best coffee beans we've sourced! Consistent quality and great flavor profile.", "is_verified_purchase": True, "is_approved": True},
    {"user_email": "farmer.john@agrihub.com", "product_name": "Turmeric Powder", "rating": 4, "title": "High Quality", "comment": "Good turmeric powder, vibrant color and strong aroma.", "is_verified_purchase": False, "is_approved": True},
]

WISHLISTS = [
    {"user_email": "buyer.sarah@agrihub.com", "name": "My Farm Favorites", "is_default": True, "is_public": False},
    {"user_email": "distributor.mike@agrihub.com", "name": "Bulk Orders", "is_default": True, "is_public": False},
    {"user_email": "retailer.jane@agrihub.com", "name": "Seasonal Products", "is_default": True, "is_public": True},
]

WISHLIST_ITEMS = [
    {"user_email": "buyer.sarah@agrihub.com", "product_name": "Almonds", "quantity": 5},
    {"user_email": "buyer.sarah@agrihub.com", "product_name": "Raw Honey", "quantity": 3},
    {"user_email": "distributor.mike@agrihub.com", "product_name": "Soybeans - 5kg", "quantity": 10},
    {"user_email": "distributor.mike@agrihub.com", "product_name": "Hemp Seeds", "quantity": 15},
    {"user_email": "retailer.jane@agrihub.com", "product_name": "Turmeric Powder", "quantity": 2},
    {"user_email": "retailer.jane@agrihub.com", "product_name": "Black Pepper", "quantity": 1},
]

LOYALTY_ACCOUNTS = [
    {"user_email": "buyer.sarah@agrihub.com", "total_points": 150, "available_points": 120, "tier": "bronze", "tier_progress": 0.15, "points_earned_lifetime": 150, "points_redeemed_lifetime": 30, "referrals_made": 2, "successful_referrals": 1, "tier_benefits": {"discount_percentage": 2, "early_access": False}, "status": "active", "loyalty_metadata": {"join_date": "2024-01-15", "preferred_rewards": "discounts"}},
    {"user_email": "distributor.mike@agrihub.com", "total_points": 450, "available_points": 380, "tier": "silver", "tier_progress": 0.45, "points_earned_lifetime": 450, "points_redeemed_lifetime": 70, "referrals_made": 5, "successful_referrals": 3, "tier_benefits": {"discount_percentage": 5, "early_access": True}, "status": "active", "loyalty_metadata": {"join_date": "2023-12-01", "preferred_rewards": "discounts"}},
    {"user_email": "retailer.jane@agrihub.com", "total_points": 1200, "available_points": 950, "tier": "gold", "tier_progress": 0.20, "points_earned_lifetime": 1200, "points_redeemed_lifetime": 250, "referrals_made": 8, "successful_referrals": 6, "tier_benefits": {"discount_percentage": 10, "early_access": True, "free_shipping": True}, "status": "active", "loyalty_metadata": {"join_date": "2023-10-15", "preferred_rewards": "discounts"}},
]

POINTS_TRANSACTIONS = [
    {"user_email": "buyer.sarah@agrihub.com", "points": 50, "transaction_type": "earned", "description": "Purchase bonus - Organic Wheat order", "reason_code": "purchase_bonus", "related_amount": 25.98, "currency": "USD", "status": "completed", "reference_id": "order_123", "expires_at": "2025-01-31", "transaction_metadata": {"source": "web", "campaign": "spring_sale"}},
    {"user_email": "buyer.sarah@agrihub.com", "points": -20, "transaction_type": "redeemed", "description": "Discount applied on bulk order", "reason_code": "discount_redemption", "related_amount": 5.00, "currency": "USD", "status": "completed", "reference_id": "order_124", "expires_at": None, "transaction_metadata": {"source": "web", "discount_type": "points"}},
    {"user_email": "distributor.mike@agrihub.com", "points": 100, "transaction_type": "earned", "description": "Bulk order bonus - Basmati Rice", "reason_code": "bulk_bonus", "related_amount": 45.99, "currency": "USD", "status": "completed", "reference_id": "order_125", "expires_at": "2025-02-28", "transaction_metadata": {"source": "web", "bulk_threshold": 100.0}},
    {"user_email": "distributor.mike@agrihub.com", "points": 25, "transaction_type": "earned", "description": "Referral bonus - new customer", "reason_code": "referral_bonus", "related_amount": 0.00, "currency": "USD", "status": "completed", "reference_id": "ref_001", "expires_at": "2025-03-31", "transaction_metadata": {"source": "referral", "referred_customer": "new_user_123"}},
    {"user_email": "retailer.jane@agrihub.com", "points": 200, "transaction_type": "earned", "description": "Loyalty bonus - Gold tier", "reason_code": "tier_bonus", "related_amount": 0.00, "currency": "USD", "status": "completed", "reference_id": "loyalty_001", "expires_at": "2025-06-30", "transaction_metadata": {"source": "loyalty", "tier": "gold"}},
    {"user_email": "retailer.jane@agrihub.com", "points": -50, "transaction_type": "redeemed", "description": "Free shipping redemption", "reason_code": "shipping_redemption", "related_amount": 15.99, "currency": "USD", "status": "completed", "reference_id": "shipping_001", "expires_at": None, "transaction_metadata": {"source": "web", "shipping_method": "express"}},
]

INVENTORY_ITEMS = [
    {"variant_name": "Organic Wheat - 5kg", "warehouse_name": "Main Distribution Center", "quantity_available": 500, "low_stock_threshold": 50, "reorder_point": 25, "inventory_status": "active", "last_restocked_at": "2024-01-15", "last_sold_at": "2024-01-20"},
    {"variant_name": "Basmati Rice - 5kg", "warehouse_name": "West Coast Warehouse", "quantity_available": 300, "low_stock_threshold": 30, "reorder_point": 15, "inventory_status": "active", "last_restocked_at": "2024-01-10", "last_sold_at": "2024-01-18"},
    {"variant_name": "Fresh Tomatoes - 1kg", "warehouse_name": "East Coast Facility", "quantity_available": 200, "low_stock_threshold": 25, "reorder_point": 12, "inventory_status": "active", "last_restocked_at": "2024-01-12", "last_sold_at": "2024-01-19"},
    {"variant_name": "Coffee Beans - 500g", "warehouse_name": "International Hub", "quantity_available": 150, "low_stock_threshold": 20, "reorder_point": 10, "inventory_status": "active", "last_restocked_at": "2024-01-08", "last_sold_at": "2024-01-17"},
    {"variant_name": "Soybeans - 1kg", "warehouse_name": "Main Distribution Center", "quantity_available": 75, "low_stock_threshold": 15, "reorder_point": 8, "inventory_status": "active", "last_restocked_at": "2024-01-14", "last_sold_at": "2024-01-21"},
    {"variant_name": "Turmeric Powder", "warehouse_name": "West Coast Warehouse", "quantity_available": 120, "low_stock_threshold": 20, "reorder_point": 10, "inventory_status": "active", "last_restocked_at": "2024-01-11", "last_sold_at": "2024-01-16"},
]

PRICING_CONFIGS = [
    {"key": "default_markup_percentage", "value": "15.0", "description": "Default markup for all products"},
    {"key": "bulk_discount_threshold", "value": "100.0", "description": "Minimum order for bulk discount"},
    {"key": "bulk_discount_percentage", "value": "5.0", "description": "Discount percentage for bulk orders"},
]

SUBSCRIPTIONS = [
    {"user_email": "buyer.sarah@agrihub.com", "plan_type": "monthly", "status": "active", "product_name": "Organic Wheat - 5kg", "quantity": 2},
    {"user_email": "distributor.mike@agrihub.com", "plan_type": "quarterly", "status": "active", "product_name": "Basmati Rice - 5kg", "quantity": 5},
    {"user_email": "retailer.jane@agrihub.com", "plan_type": "monthly", "status": "active", "product_name": "Coffee Beans - 500g", "quantity": 3},
]

PAYMENT_METHODS = [
    {"user_email": "buyer.sarah@agrihub.com", "method_type": "credit_card", "provider": "visa", "last_four": "1234", "is_default": True},
    {"user_email": "distributor.mike@agrihub.com", "method_type": "bank_transfer", "provider": "chase", "last_four": "5678", "is_default": True},
    {"user_email": "retailer.jane@agrihub.com", "method_type": "credit_card", "provider": "mastercard", "last_four": "9012", "is_default": True},
]

DISCOUNTS = [
    {"name": "Seasonal Harvest Discount", "discount_type": "percentage", "value": 10.0, "applicable_to": "all_products"},
    {"name": "Bulk Order Savings", "discount_type": "percentage", "value": 15.0, "applicable_to": "bulk_orders"},
    {"name": "Organic Premium", "discount_type": "fixed", "value": 5.0, "applicable_to": "organic_products"},
]

DEFAULT_BATCH_SIZE = 100

async def seed_tax_rates(session: AsyncSession):
    """Seed tax rates into the database using models"""
    models = get_models()
    TaxRate = models['TaxRate']
    
    try:
        # Check if tax rates already exist
        result = await session.execute(select(TaxRate).limit(1))
        existing = result.scalar_one_or_none()
        
        if existing:
            print("✅ Tax rates already exist. Skipping...")
            return
        
        print(f"🌍 Seeding {len(GLOBAL_TAX_RATES)} tax rates...")
        
        # Create tax rate objects in batches
        tax_rates_batch = []
        for data in GLOBAL_TAX_RATES:
            tax_rate = TaxRate(**data)
            tax_rates_batch.append(tax_rate)
            
            if len(tax_rates_batch) >= DEFAULT_BATCH_SIZE:
                session.add_all(tax_rates_batch)
                await session.flush()
                tax_rates_batch.clear()
        
        # Add remaining tax rates
        if tax_rates_batch:
            session.add_all(tax_rates_batch)
        
        await session.commit()
        print(f"✅ Successfully seeded {len(GLOBAL_TAX_RATES)} tax rates")
        
    except Exception as e:
        print(f"❌ Error seeding tax rates: {e}")
        await session.rollback()
        raise

async def seed_categories(session: AsyncSession):
    """Seed product categories using models"""
    models = get_models()
    Category = models['Category']
    
    try:
        # Check if categories already exist
        result = await session.execute(select(Category).limit(1))
        existing = result.scalar_one_or_none()
        
        if existing:
            print("✅ Categories already exist. Skipping...")
            return
        
        print(f"📦 Seeding {len(CATEGORIES)} categories...")
        
        categories = []
        for category_data in CATEGORIES:
            category = Category(
                name=category_data["name"],
                description=category_data["description"],
                is_active=True
            )
            categories.append(category)
        
        session.add_all(categories)
        await session.commit()
        print(f"✅ Successfully seeded {len(CATEGORIES)} categories")
        
    except Exception as e:
        print(f"❌ Error seeding categories: {e}")
        await session.rollback()
        raise

async def seed_products(session: AsyncSession):
    """Seed sample products using models"""
    models = get_models()
    Product = models['Product']
    Category = models['Category']
    
    try:
        # Check if products already exist
        result = await session.execute(select(Product).limit(1))
        existing = result.scalar_one_or_none()
        
        if existing:
            print("✅ Products already exist. Skipping...")
            return
        
        print(f"🛍️ Seeding {len(PRODUCTS)} products...")
        
        # Get category mapping and first user as supplier
        categories_result = await session.execute(select(Category))
        categories = {cat.name: cat for cat in categories_result.scalars()}
        
        users_result = await session.execute(select(models['User']))
        users = users_result.scalars().all()
        
        if not categories:
            print("⚠️ No categories found, skipping products")
            return
            
        if not users:
            print("⚠️ No users found, skipping products")
            return
        
        supplier = users[0]  # Use first user as supplier
        
        products = []
        for product_data in PRODUCTS:
            category = categories.get(product_data["category"])
            if category:
                product = Product(
                    name=product_data["name"],
                    slug=product_data["name"].lower().replace(" ", "-").replace(",", "").replace(".", ""),
                    description=product_data["description"],
                    short_description=product_data["description"][:100] + "...",
                    category_id=category.id,
                    supplier_id=supplier.id,
                    product_status="active",
                    availability_status="available",
                    min_price=product_data["price"],
                    max_price=product_data["price"],
                    dietary_tags=product_data["dietary_tags"],
                    tags=",".join(product_data["dietary_tags"]),
                    is_active=True
                )
                products.append(product)
        
        session.add_all(products)
        await session.commit()
        print(f"✅ Successfully seeded {len(products)} products")
        
    except Exception as e:
        print(f"❌ Error seeding products: {e}")
        await session.rollback()
        raise

async def seed_users(session: AsyncSession):
    """Seed sample users using models"""
    models = get_models()
    User = models['User']
    
    try:
        # Check if users already exist
        result = await session.execute(select(User).limit(1))
        existing = result.scalar_one_or_none()
        
        if existing:
            print("✅ Users already exist. Skipping...")
            return
        
        print(f"👥 Seeding {len(USERS)} users...")
        
        users = []
        for user_data in USERS:
            user = User(
                email=user_data["email"],
                firstname=user_data["first_name"],
                lastname=user_data["last_name"],
                hashed_password=PasswordManager.hash_password("password123"),
                role=user_data["role"],
                account_status="active",
                verification_status="verified",
                verified=True,
                is_active=True,
                phone=user_data["phone"],
                phone_verified=user_data["phone_verified"],
                country=user_data["country"],
                language=user_data["language"],
                timezone=user_data["timezone"],
                avatar_url=user_data["avatar_url"],
                age=user_data["age"],
                gender=user_data["gender"],
                preferences=user_data["preferences"],
                last_login=datetime.utcnow() - timedelta(hours=random.randint(1, 24)),
                login_count=random.randint(1, 100),
                failed_login_attempts=0,
                stripe_customer_id=f"cus_{uuid7().hex[:16]}"
            )
            users.append(user)
        
        session.add_all(users)
        await session.commit()
        print(f"✅ Successfully seeded {len(users)} users")
        
    except Exception as e:
        print(f"❌ Error seeding users: {e}")
        await session.rollback()
        raise

async def seed_product_variants(session: AsyncSession):
    """Seed product variants using models"""
    models = get_models()
    ProductVariant = models['ProductVariant']
    Product = models['Product']
    
    try:
        # Check if variants already exist
        result = await session.execute(select(ProductVariant).limit(1))
        existing = result.scalar_one_or_none()
        
        if existing:
            print("✅ Product variants already exist. Skipping...")
            return
        
        print(f"📦 Seeding {len(PRODUCT_VARIANTS)} product variants...")
        
        # Get product mapping
        products_result = await session.execute(select(Product))
        products = {prod.name: prod for prod in products_result.scalars()}
        
        variants = []
        for variant_data in PRODUCT_VARIANTS:
            product = products.get(variant_data["product_name"])
            if product:
                # Generate SKU if not provided
                sku = variant_data.get("sku", f"{variant_data['product_name'][:3].upper()}-{variant_data['name'].replace(' ', '-').upper()}")
                
                variant = ProductVariant(
                    product_id=product.id,
                    name=variant_data["name"],
                    sku=variant_data["sku"],
                    base_price=variant_data["price"],
                    sale_price=variant_data.get("sale_price"),
                    barcode=variant_data.get("barcode"),
                    qr_code=variant_data.get("qr_code"),
                    attributes=variant_data.get("attributes"),
                    is_active=True
                )
                variants.append(variant)
        
        session.add_all(variants)
        await session.commit()
        print(f"✅ Successfully seeded {len(variants)} product variants")
        
    except Exception as e:
        print(f"❌ Error seeding product variants: {e}")
        await session.rollback()
        raise

async def seed_product_images(session: AsyncSession):
    """Seed product images using models"""
    models = get_models()
    ProductImage = models['ProductImage']
    ProductVariant = models['ProductVariant']
    Product = models['Product']
    
    try:
        # Check if images already exist
        result = await session.execute(select(ProductImage).limit(1))
        existing = result.scalar_one_or_none()
        
        if existing:
            print("✅ Product images already exist. Skipping...")
            return
        
        print(f"🖼️ Seeding {len(PRODUCT_IMAGES)} product images...")
        
        # Get product and variant mapping
        products_result = await session.execute(select(Product))
        products = {prod.name: prod for prod in products_result.scalars()}
        
        variants_result = await session.execute(select(ProductVariant))
        variants = list(variants_result.scalars())
        
        # Create a mapping from product name to first variant
        product_to_variant = {}
        for variant in variants:
            if variant.product and variant.product.name not in product_to_variant:
                product_to_variant[variant.product.name] = variant
        
        images = []
        for image_data in PRODUCT_IMAGES:
            product = products.get(image_data["product_name"])
            variant = product_to_variant.get(image_data["product_name"])
            
            if product and variant:
                image = ProductImage(
                    variant_id=variant.id,
                    url=image_data["url"],
                    alt_text=image_data["alt_text"],
                    is_primary=image_data["is_primary"],
                    sort_order=1,
                    format="jpg"
                )
                images.append(image)
        
        session.add_all(images)
        await session.commit()
        print(f"✅ Successfully seeded {len(images)} product images")
        
    except Exception as e:
        print(f"❌ Error seeding product images: {e}")
        await session.rollback()
        raise

async def seed_addresses(session: AsyncSession):
    """Seed addresses using models"""
    models = get_models()
    Address = models['Address']
    User = models['User']
    
    try:
        # Check if addresses already exist
        result = await session.execute(select(Address).limit(1))
        existing = result.scalar_one_or_none()
        
        if existing:
            print("✅ Addresses already exist. Skipping...")
            return
        
        print(f"🏠 Seeding {len(ADDRESSES)} addresses...")
        
        # Get user mapping
        users_result = await session.execute(select(User))
        users = {user.email: user for user in users_result.scalars()}
        
        addresses = []
        for address_data in ADDRESSES:
            user = users.get(address_data["user_email"])
            if user:
                address = Address(
                    user_id=user.id,
                    street=address_data["street"],
                    city=address_data["city"],
                    state=address_data["state"],
                    post_code=address_data["post_code"],
                    country=address_data["country"],
                    kind=address_data["kind"],
                    is_default=address_data["is_default"]
                )
                addresses.append(address)
        
        session.add_all(addresses)
        await session.commit()
        print(f"✅ Successfully seeded {len(addresses)} addresses")
        
    except Exception as e:
        print(f"❌ Error seeding addresses: {e}")
        await session.rollback()
        raise

async def seed_carts(session: AsyncSession):
    """Seed carts using models"""
    models = get_models()
    Cart = models['Cart']
    User = models['User']
    
    try:
        # Check if carts already exist
        result = await session.execute(select(Cart).limit(1))
        existing = result.scalar_one_or_none()
        
        if existing:
            print("✅ Carts already exist. Skipping...")
            return
        
        print(f"🛒 Seeding {len(CARTS)} carts...")
        
        # Get user mapping
        users_result = await session.execute(select(User))
        users = {user.email: user for user in users_result.scalars()}
        
        carts = []
        for cart_data in CARTS:
            user = users.get(cart_data["user_email"])
            if user:
                cart = Cart(
                    user_id=user.id
                )
                carts.append(cart)
        
        session.add_all(carts)
        await session.commit()
        print(f"✅ Successfully seeded {len(carts)} carts")
        
    except Exception as e:
        print(f"❌ Error seeding carts: {e}")
        await session.rollback()
        raise

async def seed_cart_items(session: AsyncSession):
    """Seed cart items using models"""
    models = get_models()
    CartItem = models['CartItem']
    Cart = models['Cart']
    ProductVariant = models['ProductVariant']
    User = models['User']
    
    try:
        # Check if cart items already exist
        result = await session.execute(select(CartItem).limit(1))
        existing = result.scalar_one_or_none()
        
        if existing:
            print("✅ Cart items already exist. Skipping...")
            return
        
        print(f"🛒 Seeding {len(CART_ITEMS)} cart items...")
        
        # Get mappings
        users_result = await session.execute(select(User))
        users = {user.email: user for user in users_result.scalars()}
        
        carts_result = await session.execute(select(Cart))
        carts = {cart.user_id: cart for cart in carts_result.scalars()}
        
        variants_result = await session.execute(select(ProductVariant))
        variants = {variant.name: variant for variant in variants_result.scalars()}
        
        cart_items = []
        for item_data in CART_ITEMS:
            user = users.get(item_data["user_email"])
            variant = variants.get(item_data["product_name"])
            
            if user and variant:
                cart = carts.get(user.id)
                if cart:
                    cart_item = CartItem(
                        cart_id=cart.id,
                        variant_id=variant.id,
                        product_id=variant.product_id,
                        quantity=item_data["quantity"],
                        price_per_unit=item_data["price_per_unit"]
                    )
                    cart_items.append(cart_item)
        
        session.add_all(cart_items)
        await session.commit()
        print(f"✅ Successfully seeded {len(cart_items)} cart items")
        
    except Exception as e:
        print(f"❌ Error seeding cart items: {e}")
        await session.rollback()
        raise

async def seed_reviews(session: AsyncSession):
    """Seed reviews using models"""
    models = get_models()
    Review = models['Review']
    Product = models['Product']
    User = models['User']
    
    try:
        # Check if reviews already exist
        result = await session.execute(select(Review).limit(1))
        existing = result.scalar_one_or_none()
        
        if existing:
            print("✅ Reviews already exist. Skipping...")
            return
        
        print(f"⭐ Seeding {len(REVIEWS)} reviews...")
        
        # Get mappings
        users_result = await session.execute(select(User))
        users = {user.email: user for user in users_result.scalars()}
        
        products_result = await session.execute(select(Product))
        products = {product.name: product for product in products_result.scalars()}
        
        reviews = []
        for review_data in REVIEWS:
            user = users.get(review_data["user_email"])
            product = products.get(review_data["product_name"])
            
            if user and product:
                review = Review(
                    user_id=user.id,
                    product_id=product.id,
                    rating=review_data["rating"],
                    comment=review_data["comment"],
                    is_verified_purchase=review_data["is_verified_purchase"],
                    is_approved=review_data["is_approved"]
                )
                reviews.append(review)
        
        session.add_all(reviews)
        await session.commit()
        print(f"✅ Successfully seeded {len(reviews)} reviews")
        
    except Exception as e:
        print(f"❌ Error seeding reviews: {e}")
        await session.rollback()
        raise

async def seed_wishlists(session: AsyncSession):
    """Seed wishlists using models"""
    models = get_models()
    Wishlist = models['Wishlist']
    User = models['User']
    
    try:
        # Check if wishlists already exist
        result = await session.execute(select(Wishlist).limit(1))
        existing = result.scalar_one_or_none()
        
        if existing:
            print("✅ Wishlists already exist. Skipping...")
            return
        
        print(f"💝 Seeding {len(WISHLISTS)} wishlists...")
        
        # Get user mapping
        users_result = await session.execute(select(User))
        users = {user.email: user for user in users_result.scalars()}
        
        wishlists = []
        for wishlist_data in WISHLISTS:
            user = users.get(wishlist_data["user_email"])
            if user:
                wishlist = Wishlist(
                    user_id=user.id,
                    name=wishlist_data["name"],
                    is_default=wishlist_data["is_default"],
                    is_public=wishlist_data["is_public"]
                )
                wishlists.append(wishlist)
        
        session.add_all(wishlists)
        await session.commit()
        print(f"✅ Successfully seeded {len(wishlists)} wishlists")
        
    except Exception as e:
        print(f"❌ Error seeding wishlists: {e}")
        await session.rollback()
        raise

async def seed_wishlist_items(session: AsyncSession):
    """Seed wishlist items using models"""
    models = get_models()
    WishlistItem = models['WishlistItem']
    Wishlist = models['Wishlist']
    Product = models['Product']
    User = models['User']
    
    try:
        # Check if wishlist items already exist
        result = await session.execute(select(WishlistItem).limit(1))
        existing = result.scalar_one_or_none()
        
        if existing:
            print("✅ Wishlist items already exist. Skipping...")
            return
        
        print(f"💝 Seeding {len(WISHLIST_ITEMS)} wishlist items...")
        
        # Get mappings
        users_result = await session.execute(select(User))
        users = {user.email: user for user in users_result.scalars()}
        
        wishlists_result = await session.execute(select(Wishlist))
        wishlists = {wishlist.user_id: wishlist for wishlist in wishlists_result.scalars()}
        
        products_result = await session.execute(select(Product))
        products = {product.name: product for product in products_result.scalars()}
        
        wishlist_items = []
        for item_data in WISHLIST_ITEMS:
            user = users.get(item_data["user_email"])
            product = products.get(item_data["product_name"])
            
            if user and product:
                wishlist = wishlists.get(user.id)
                if wishlist:
                    wishlist_item = WishlistItem(
                        wishlist_id=wishlist.id,
                        product_id=product.id,
                        quantity=item_data["quantity"]
                    )
                    wishlist_items.append(wishlist_item)
        
        session.add_all(wishlist_items)
        await session.commit()
        print(f"✅ Successfully seeded {len(wishlist_items)} wishlist items")
        
    except Exception as e:
        print(f"❌ Error seeding wishlist items: {e}")
        await session.rollback()
        raise

async def seed_loyalty_accounts(session: AsyncSession):
    """Seed loyalty accounts using models"""
    models = get_models()
    LoyaltyAccount = models['LoyaltyAccount']
    User = models['User']
    
    try:
        # Check if loyalty accounts already exist
        result = await session.execute(select(LoyaltyAccount).limit(1))
        existing = result.scalar_one_or_none()
        
        if existing:
            print("✅ Loyalty accounts already exist. Skipping...")
            return
        
        print(f"🏆 Seeding {len(LOYALTY_ACCOUNTS)} loyalty accounts...")
        
        # Get user mapping
        users_result = await session.execute(select(User))
        users = {user.email: user for user in users_result.scalars()}
        
        loyalty_accounts = []
        for account_data in LOYALTY_ACCOUNTS:
            user = users.get(account_data["user_email"])
            if user:
                account = LoyaltyAccount(
                    user_id=user.id,
                    total_points=account_data["total_points"],
                    available_points=account_data["available_points"],
                    tier=account_data["tier"],
                    tier_progress=account_data["tier_progress"],
                    points_earned_lifetime=account_data["points_earned_lifetime"],
                    points_redeemed_lifetime=account_data["points_redeemed_lifetime"],
                    referrals_made=account_data["referrals_made"],
                    successful_referrals=account_data["successful_referrals"],
                    tier_benefits=account_data["tier_benefits"],
                    status=account_data["status"],
                    loyalty_metadata=account_data["loyalty_metadata"]
                )
                loyalty_accounts.append(account)
        
        session.add_all(loyalty_accounts)
        await session.commit()
        print(f"✅ Successfully seeded {len(loyalty_accounts)} loyalty accounts")
        
    except Exception as e:
        print(f"❌ Error seeding loyalty accounts: {e}")
        await session.rollback()
        raise

async def seed_points_transactions(session: AsyncSession):
    """Seed points transactions using models"""
    models = get_models()
    PointsTransaction = models['PointsTransaction']
    LoyaltyAccount = models['LoyaltyAccount']
    User = models['User']
    
    try:
        # Check if points transactions already exist
        result = await session.execute(select(PointsTransaction).limit(1))
        existing = result.scalar_one_or_none()
        
        if existing:
            print("✅ Points transactions already exist. Skipping...")
            return
        
        print(f"🏆 Seeding {len(POINTS_TRANSACTIONS)} points transactions...")
        
        # Get mappings
        users_result = await session.execute(select(User))
        users = {user.email: user for user in users_result.scalars()}
        
        loyalty_accounts_result = await session.execute(select(LoyaltyAccount))
        loyalty_accounts = {account.user_id: account for account in loyalty_accounts_result.scalars()}
        
        transactions = []
        for transaction_data in POINTS_TRANSACTIONS:
            user = users.get(transaction_data["user_email"])
            loyalty_account = loyalty_accounts.get(user.id)
            
            if user and loyalty_account:
                transaction = PointsTransaction(
                    loyalty_account_id=loyalty_account.id,
                    points_amount=transaction_data["points"],
                    transaction_type=transaction_data["transaction_type"],
                    description=transaction_data["description"],
                    reason_code=transaction_data["reason_code"],
                    related_amount=transaction_data.get("related_amount"),
                    currency=transaction_data.get("currency", "USD"),
                    expires_at=transaction_data.get("expires_at"),
                    status=transaction_data.get("status", "completed"),
                    transaction_metadata=transaction_data.get("transaction_metadata"),
                    created_at=datetime.utcnow() - timedelta(days=random.randint(1, 30))
                )
                transactions.append(transaction)
        
        session.add_all(transactions)
        await session.commit()
        print(f"✅ Successfully seeded {len(transactions)} points transactions")
        
    except Exception as e:
        print(f"❌ Error seeding points transactions: {e}")
        await session.rollback()
        raise

async def seed_inventory(session: AsyncSession):
    """Seed inventory using models"""
    models = get_models()
    Inventory = models['Inventory']
    ProductVariant = models['ProductVariant']
    WarehouseLocation = models['WarehouseLocation']
    
    try:
        # Check if inventory already exist
        result = await session.execute(select(Inventory).limit(1))
        existing = result.scalar_one_or_none()
        
        if existing:
            print("✅ Inventory already exist. Skipping...")
            return
        
        print(f"📦 Seeding {len(INVENTORY_ITEMS)} inventory items...")
        
        # Get mappings
        variants_result = await session.execute(select(ProductVariant))
        variants = {variant.name: variant for variant in variants_result.scalars()}
        
        warehouses_result = await session.execute(select(WarehouseLocation))
        warehouses = {warehouse.name: warehouse for warehouse in warehouses_result.scalars()}
        
        inventory_items = []
        for item_data in INVENTORY_ITEMS:
            variant = variants.get(item_data["variant_name"])
            warehouse = warehouses.get(item_data["warehouse_name"])
            
            if variant and warehouse:
                inventory = Inventory(
                    variant_id=variant.id,
                    location_id=warehouse.id,
                    quantity_available=item_data["quantity_available"],
                    low_stock_threshold=item_data["low_stock_threshold"],
                    reorder_point=item_data["reorder_point"],
                    inventory_status=item_data["inventory_status"],
                    last_restocked_at=datetime.fromisoformat(item_data["last_restocked_at"]) if item_data.get("last_restocked_at") else None,
                    last_sold_at=datetime.fromisoformat(item_data["last_sold_at"]) if item_data.get("last_sold_at") else None,
                    quantity=item_data["quantity_available"]  # Legacy field
                )
                inventory_items.append(inventory)
        
        session.add_all(inventory_items)
        await session.commit()
        print(f"✅ Successfully seeded {len(inventory_items)} inventory items")
        
    except Exception as e:
        print(f"❌ Error seeding inventory: {e}")
        await session.rollback()
        raise

async def seed_shipping_methods(session: AsyncSession):
    """Seed shipping methods using models"""
    models = get_models()
    ShippingMethod = models['ShippingMethod']
    
    try:
        # Check if shipping methods already exist
        result = await session.execute(select(ShippingMethod).limit(1))
        existing = result.scalar_one_or_none()
        
        if existing:
            print("✅ Shipping methods already exist. Skipping...")
            return
        
        print(f"🚚 Seeding {len(SHIPPING_METHODS)} shipping methods...")
        
        methods = []
        for method_data in SHIPPING_METHODS:
            method = ShippingMethod(
                name=method_data["name"],
                price=method_data["price"],
                estimated_days=method_data["estimated_days"],
                carrier=method_data["carrier"],
                is_active=True
            )
            methods.append(method)
        
        session.add_all(methods)
        await session.commit()
        print(f"✅ Successfully seeded {len(methods)} shipping methods")
        
    except Exception as e:
        print(f"❌ Error seeding shipping methods: {e}")
        await session.rollback()
        raise

async def seed_promo_codes(session: AsyncSession):
    """Seed promo codes using models"""
    models = get_models()
    Promocode = models['Promocode']
    
    try:
        # Check if promo codes already exist
        result = await session.execute(select(Promocode).limit(1))
        existing = result.scalar_one_or_none()
        
        if existing:
            print("✅ Promo codes already exist. Skipping...")
            return
        
        print(f"🎫 Seeding {len(PROMO_CODES)} promo codes...")
        
        promo_codes = []
        for promo_data in PROMO_CODES:
            promo = Promocode(
                code=promo_data["code"],
                discount_type=promo_data["discount_type"],
                value=promo_data["value"],
                minimum_order_amount=promo_data["min_order"],
                is_active=True,
                valid_from=datetime.utcnow(),
                valid_until=datetime.utcnow() + timedelta(days=365)
            )
            promo_codes.append(promo)
        
        session.add_all(promo_codes)
        await session.commit()
        print(f"✅ Successfully seeded {len(promo_codes)} promo codes")
        
    except Exception as e:
        print(f"❌ Error seeding promo codes: {e}")
        await session.rollback()
        raise

async def seed_warehouses(session: AsyncSession):
    """Seed warehouses using models"""
    models = get_models()
    WarehouseLocation = models['WarehouseLocation']
    
    try:
        # Check if warehouses already exist
        result = await session.execute(select(WarehouseLocation).limit(1))
        existing = result.scalar_one_or_none()
        
        if existing:
            print("✅ Warehouses already exist. Skipping...")
            return
        
        print(f"🏭 Seeding {len(WAREHOUSES)} warehouses...")
        
        warehouses = []
        for warehouse_data in WAREHOUSES:
            warehouse = WarehouseLocation(
                name=warehouse_data["name"],
                address=warehouse_data["location"],
                description=f"Main warehouse in {warehouse_data['location']}"
            )
            warehouses.append(warehouse)
        
        session.add_all(warehouses)
        await session.commit()
        print(f"✅ Successfully seeded {len(warehouses)} warehouses")
        
    except Exception as e:
        print(f"❌ Error seeding warehouses: {e}")
        await session.rollback()
        raise

async def seed_sample_orders(session: AsyncSession):
    """Seed sample orders using models"""
    models = get_models()
    Order = models['Order']
    OrderItem = models['OrderItem']
    Product = models['Product']
    ProductVariant = models['ProductVariant']
    User = models['User']
    Address = models['Address']
    OrderStatus = models['OrderStatus'] if hasattr(models, 'OrderStatus') else None
    PaymentStatus = models['PaymentStatus'] if hasattr(models, 'PaymentStatus') else None
    FulfillmentStatus = models['FulfillmentStatus'] if hasattr(models, 'FulfillmentStatus') else None
    
    try:
        # Check if orders already exist
        result = await session.execute(select(Order).limit(1))
        existing = result.scalar_one_or_none()
        
        if existing:
            print("✅ Orders already exist. Skipping...")
            return
        
        print("📦 Seeding sample orders...")
        
        # Get users, products, variants, and addresses
        users_result = await session.execute(select(User))
        users = users_result.scalars().all()
        
        products_result = await session.execute(select(Product))
        products = products_result.scalars().all()
        
        variants_result = await session.execute(select(ProductVariant))
        variants = variants_result.scalars().all()
        
        addresses_result = await session.execute(select(Address))
        addresses = addresses_result.scalars().all()
        
        if not users or not products:
            print("⚠️ No users or products found, skipping orders")
            return
        
        # Create sample orders
        orders = []
        order_items = []
        order_counter = 1000  # Starting order number
        
        for i, user in enumerate(users[:3]):  # Create orders for first 3 users
            for j in range(random.randint(1, 3)):  # 1-3 orders per user
                order_counter += 1
                
                # Generate order number
                order_number = f"ORD-{order_counter:06d}"
                
                # Random order status
                order_status = random.choice(['pending', 'confirmed', 'processing', 'shipped', 'delivered'])
                payment_status = 'paid' if order_status in ['processing', 'shipped', 'delivered'] else 'pending'
                fulfillment_status = 'unfulfilled'
                if order_status == 'shipped':
                    fulfillment_status = 'fulfilled'
                elif order_status == 'delivered':
                    fulfillment_status = 'fulfilled'
                
                # Get user's addresses for billing and shipping
                user_addresses = [addr for addr in addresses if addr.user_id == user.id]
                billing_addr = user_addresses[0] if user_addresses else None
                
                if not billing_addr:
                    # Create a default address if none exists
                    billing_addr = Address(
                        user_id=user.id,
                        street="123 Main St",
                        city="Anytown",
                        state="CA",
                        country="USA",
                        post_code="12345",
                        kind="billing",
                        is_default=True
                    )
                    session.add(billing_addr)
                    await session.flush()
                
                # Use billing address for shipping if no separate shipping address
                shipping_addr = billing_addr
                
                order = Order(
                    order_number=order_number,
                    user_id=user.id,
                    billing_address={
                        "street": billing_addr.street,
                        "city": billing_addr.city,
                        "state": billing_addr.state,
                        "country": billing_addr.country,
                        "post_code": billing_addr.post_code
                    },
                    shipping_address={
                        "street": shipping_addr.street,
                        "city": shipping_addr.city,
                        "state": shipping_addr.state,
                        "country": shipping_addr.country,
                        "post_code": shipping_addr.post_code
                    },
                    order_status=order_status,
                    payment_status=payment_status,
                    fulfillment_status=fulfillment_status,
                    currency="USD",
                    created_at=datetime.utcnow() - timedelta(days=random.randint(1, 30))
                )
                orders.append(order)
                
                # Add 1-5 items per order
                selected_products = random.sample(products, random.randint(1, min(5, len(products))))
                order_total = 0.0
                
                for product in selected_products:
                    quantity = random.randint(1, 3)
                    # Get a variant for this product
                    product_variants = [v for v in variants if v.product_id == product.id]
                    if not product_variants:
                        continue
                    variant = random.choice(product_variants)
                    
                    # Use variant price
                    unit_price = variant.base_price
                    item_total = unit_price * quantity
                    order_total += item_total
                    
                    order_item = OrderItem(
                        order_id=order.id,  # Will be set after flush
                        variant_id=variant.id,
                        quantity=quantity,
                        price_per_unit=unit_price,
                        total_price=item_total
                    )
                    order_items.append(order_item)
                
                # Set order totals
                shipping_cost = random.uniform(5.0, 25.0)
                tax_amount = order_total * 0.1  # 10% tax
                total_amount = order_total + tax_amount + shipping_cost
                
                order.subtotal = order_total
                order.tax_amount = tax_amount
                order.shipping_cost = shipping_cost
                order.total_amount = total_amount
        
        # Save orders first to get IDs
        session.add_all(orders)
        await session.flush()
        
        # Set order IDs for order items
        order_index = 0
        items_per_order = len(selected_products) if 'selected_products' in locals() else 1
        
        for i, order_item in enumerate(order_items):
            if i > 0 and i % items_per_order == 0:
                order_index += 1
            if order_index < len(orders):
                order_item.order_id = orders[order_index].id
        
        session.add_all(order_items)
        await session.commit()
        print(f"✅ Successfully seeded {len(orders)} orders with {len(order_items)} items")
        
    except Exception as e:
        print(f"❌ Error seeding orders: {e}")
        await session.rollback()
        raise

async def count_records(session: AsyncSession):
    """Count records in all tables for verification"""
    models = get_models()
    
    tables = [
        ("Users", models['User']),
        ("Products", models['Product']),
        ("Product Variants", models['ProductVariant']),
        ("Categories", models['Category']),
        ("Orders", models['Order']),
        ("Order Items", models['OrderItem']),
        ("Carts", models['Cart']),
        ("Cart Items", models['CartItem']),
        ("Reviews", models['Review']),
        ("Promo Codes", models['Promocode']),
        ("Shipping Methods", models['ShippingMethod']),
        ("Wishlists", models['Wishlist']),
        ("Wishlist Items", models['WishlistItem']),
        ("Loyalty Accounts", models['LoyaltyAccount']),
        ("Points Transactions", models['PointsTransaction']),
        ("Refunds", models['Refund']),
        ("Refund Items", models['RefundItem']),
        ("Tax Rates", models['TaxRate']),
        ("Shipping Carriers", models['ShippingCarrier']),
        ("Shipment Tracking", models['ShipmentTracking']),
        ("Tracking Events", models['TrackingEvent']),
        ("Subscriptions", models['Subscription']),
        ("Payment Methods", models['PaymentMethod']),
        ("Payment Intents", models['PaymentIntent']),
        ("Transactions", models['Transaction']),
        ("Warehouse Locations", models['WarehouseLocation']),
        ("Inventory", models['Inventory']),
        ("Discounts", models['Discount']),
    ]
    
    print("\n📊 Database Summary:")
    print("=" * 50)
    
    for table_name, model in tables:
        try:
            result = await session.execute(select(func.count(model.id)))
            count = result.scalar()
            print(f"{table_name:25}: {count:6,} records")
        except Exception as e:
            print(f"{table_name:25}: Error - {e}")
    
    print("=" * 50)
    print("✅ Database seeding completed successfully!")
    print("\n🔐 Development Login Credentials:")
    print("   Email: admin@example.com")
    print("   Password: password123")

async def main():
    """Main seeding function"""
    print("🚀 Banwee Database Seeding Tool")
    print("📝 Note: Use 'alembic upgrade head' for schema management")
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Database seeding script')
    parser.add_argument('--seed', action='store_true', help='Seed sample data')
    args = parser.parse_args()
    
    # Initialize database manager
    initialize_db(settings.SQLALCHEMY_DATABASE_URI, settings.ENVIRONMENT == "local")

    try:
        print("📋 Seeding essential tax rates...")
        async with db_manager.session_factory() as session:
            await seed_tax_rates(session)
        
        if args.seed:
            print("\n📦 Seeding comprehensive sample data...")
            async with db_manager.session_factory() as session:
                # Seed in order of dependencies
                await seed_categories(session)
                await seed_products(session)
                await seed_product_variants(session)
                await seed_product_images(session)
                await seed_users(session)
                await seed_addresses(session)
                await seed_carts(session)
                await seed_cart_items(session)
                await seed_reviews(session)
                await seed_wishlists(session)
                await seed_wishlist_items(session)
                await seed_loyalty_accounts(session)
                await seed_points_transactions(session)
                await seed_shipping_methods(session)
                await seed_promo_codes(session)
                await seed_warehouses(session)
                await seed_inventory(session)
                # Create a completely fresh connection for orders to avoid cached statements
                from core.db import DatabaseManager
                fresh_db_manager = DatabaseManager()
                fresh_db_manager.initialize(settings.SQLALCHEMY_DATABASE_URI, settings.ENVIRONMENT == "local")
                async with fresh_db_manager.session_factory() as order_session:
                    await seed_sample_orders(order_session)
        
        # Show summary
        async with db_manager.session_factory() as session:
            await count_records(session)
        
        print("\n💡 Schema management: Use 'alembic upgrade head' for table creation")
        print("🌱 Data seeding: Use 'python init_db.py --seed' for sample data")
        
    except Exception as e:
        print(f"❌ Error seeding database: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
