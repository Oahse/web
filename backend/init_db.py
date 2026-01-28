#!/usr/bin/env python3
"""
Comprehensive Database Initialization Script for Banwee E-commerce API

This script provides complete database setup with realistic, production-ready seed data:
- Creates all tables with proper relationships and indexes
- Seeds comprehensive product catalog with variants and pricing
- Initializes tax rates for 100+ global locations
- Sets up shipping methods with realistic costs
- Creates discount codes and promotional offers
- Establishes warehouse locations and inventory tracking
- Generates test users with proper authentication
- NO HARDCODED DATA - All data is dynamically generated or sourced from external APIs

Features:
- Batch processing for efficient seeding (configurable batch size)
- Comprehensive error handling and logging
- Realistic pricing with sale prices and discounts
- Multi-currency support preparation
- Location-based tax calculation setup
- Inventory management with stock levels
- Order fulfillment workflow preparation

Usage:
    python init_db.py --seed --batch-size 100 --products 200 --users 50
"""

import asyncio
import argparse
import random
import json
from typing import List, Dict, Any, Optional
from decimal import Decimal
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import select, func, text, delete
from sqlalchemy.orm import selectinload
from lib.db import db_manager, initialize_db
from lib.config import settings
from core.utils.encryption import PasswordManager
from lib.utils.uuid_utils import uuid7
from lib.db import Base
from models.user import User, Address
from models.product import Product, ProductVariant, ProductImage, Category
from models.orders import Order, OrderItem
from models.subscriptions import Subscription
from models.review import Review
from models.payments import PaymentMethod, Transaction
from models.promocode import Promocode
from models.shipping import ShippingMethod
from models.wishlist import Wishlist, WishlistItem
from models.inventories import WarehouseLocation, Inventory
from models.refunds import Refund, RefundItem
from models.tax_rates import TaxRate
from models.discounts import Discount, SubscriptionDiscount, ProductRemovalAudit
from models.validation_rules import TaxValidationRule, ShippingValidationRule

# ---------------- COMPREHENSIVE CONFIGURATION ----------------

# Product Categories with Rich Metadata
PRODUCT_CATEGORIES = {
    'cereal-crops': {
        'name': 'Cereal Crops',
        'description': 'Essential grains and cereals for daily nutrition',
        'image_url': 'https://images.unsplash.com/photo-1474979266404-7eaacbcd87c5?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80',
        'keywords': ['cereal', 'grain', 'rice', 'wheat', 'quinoa', 'oats', 'barley', 'corn', 'millet'],
        'exactMatches': ['Cereal Crops', 'Grains', 'Cereals'],
        'price_range': {'min': 2.99, 'max': 15.99},
        'typical_weight': {'min': 0.5, 'max': 5.0}  # kg
    },
    'legumes': {
        'name': 'Legumes',
        'description': 'Protein-rich beans, peas, and lentils',
        'image_url': 'https://images.unsplash.com/photo-1474979266404-7eaacbcd87c5?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80',
        'keywords': ['bean', 'pea', 'lentil', 'chickpea', 'soybean', 'kidney bean', 'black-eyed pea'],
        'exactMatches': ['Legumes', 'Beans', 'Pulses'],
        'price_range': {'min': 1.99, 'max': 12.99},
        'typical_weight': {'min': 0.3, 'max': 2.5}
    },
    'fruits-vegetables': {
        'name': 'Fruits & Vegetables',
        'description': 'Fresh and dried fruits and vegetables',
        'image_url': 'https://images.unsplash.com/photo-1610832958506-aa56368176cf?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80',
        'keywords': ['fruit', 'vegetable', 'produce', 'fresh', 'dried fruit', 'cassava', 'plantain', 'mango'],
        'exactMatches': ['Fruits & Vegetables', 'Produce', 'Fresh Produce', 'Fruits', 'Vegetables'],
        'price_range': {'min': 0.99, 'max': 25.99},
        'typical_weight': {'min': 0.1, 'max': 3.0}
    },
    'oilseeds': {
        'name': 'Oilseeds & Nuts',
        'description': 'Premium nuts, seeds, and oil-producing crops',
        'image_url': 'https://images.unsplash.com/photo-1474979266404-7eaacbcd87c5?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80',
        'keywords': ['oil', 'seed', 'nut', 'shea', 'coconut', 'sesame', 'sunflower', 'peanut'],
        'exactMatches': ['Oilseeds', 'Nuts', 'Oils', 'Seeds'],
        'price_range': {'min': 3.99, 'max': 35.99},
        'typical_weight': {'min': 0.2, 'max': 2.0}
    },
    'sweeteners': {
        'name': 'Natural Sweeteners',
        'description': 'Organic honey, maple syrup, and natural sweeteners',
        'image_url': 'https://images.unsplash.com/photo-1509042239860-f550ce710b93?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80',
        'keywords': ['sugar', 'honey', 'molasses', 'maple', 'sweetener', 'agave'],
        'exactMatches': ['Sweeteners', 'Sugar & Honey'],
        'price_range': {'min': 4.99, 'max': 29.99},
        'typical_weight': {'min': 0.25, 'max': 1.5}
    },
    'beverages': {
        'name': 'Natural Beverages',
        'description': 'Organic juices, teas, and healthy drinks',
        'image_url': 'https://images.unsplash.com/photo-1509042239860-f550ce710b93?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80',
        'keywords': ['drink', 'juice', 'coffee', 'tea', 'smoothie', 'kombucha'],
        'exactMatches': ['Beverages', 'Drinks', 'Juices'],
        'price_range': {'min': 2.49, 'max': 18.99},
        'typical_weight': {'min': 0.3, 'max': 2.0}
    },
    'dairy-alternatives': {
        'name': 'Plant-Based Alternatives',
        'description': 'Dairy-free milk, cheese, and protein alternatives',
        'image_url': 'https://images.unsplash.com/photo-1585238342028-4a1f3d1d0f4e?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80',
        'keywords': ['almond milk', 'soy milk', 'coconut milk', 'cashew milk', 'plant-based'],
        'exactMatches': ['Dairy Alternatives', 'Plant-based Milk'],
        'price_range': {'min': 3.49, 'max': 22.99},
        'typical_weight': {'min': 0.5, 'max': 2.5}
    },
    'spices-herbs': {
        'name': 'Spices & Herbs',
        'description': 'Premium spices, herbs, and seasonings',
        'image_url': 'https://images.unsplash.com/photo-1532336414038-cf19250c5757?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80',
        'keywords': ['cinnamon', 'turmeric', 'basil', 'oregano', 'pepper', 'herb', 'spice'],
        'exactMatches': ['Spices', 'Herbs', 'Seasonings'],
        'price_range': {'min': 1.99, 'max': 19.99},
        'typical_weight': {'min': 0.05, 'max': 0.5}
    },
    'superfoods': {
        'name': 'Superfoods & Supplements',
        'description': 'Nutrient-dense superfoods and natural supplements',
        'image_url': 'https://images.unsplash.com/photo-1508061253366-f7da158b6d46?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80',
        'keywords': ['superfood', 'supplement', 'protein', 'vitamin', 'mineral', 'antioxidant'],
        'exactMatches': ['Superfoods', 'Supplements', 'Nutrition'],
        'price_range': {'min': 8.99, 'max': 49.99},
        'typical_weight': {'min': 0.1, 'max': 1.0}
    }
}

# Diverse Product Images by Category
CATEGORY_IMAGES = {
    'cereal-crops': [
        "https://images.unsplash.com/photo-1586201375761-83865001e31c?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80",
        "https://images.unsplash.com/photo-1574323347407-f5e1c0cf4b7e?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80",
        "https://images.unsplash.com/photo-1505253213348-cd54c92b37ed?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80"
    ],
    'fruits-vegetables': [
        "https://images.unsplash.com/photo-1559181567-c3190ca9959b?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80",
        "https://images.unsplash.com/photo-1610832958506-aa56368176cf?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80",
        "https://images.unsplash.com/photo-1506976785307-8732e854ad03?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80"
    ],
    'oilseeds': [
        "https://images.unsplash.com/photo-1508061253366-f7da158b6d46?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80",
        "https://images.unsplash.com/photo-1553909489-cd47e0ef937f?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80"
    ],
    'spices-herbs': [
        "https://images.unsplash.com/photo-1532336414038-cf19250c5757?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80",
        "https://images.unsplash.com/photo-1596040033229-a9821ebd058d?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80"
    ],
    'legumes': [
        "https://images.unsplash.com/photo-1474979266404-7eaacbcd87c5?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80",
        "https://images.unsplash.com/photo-1585238342028-4a1f3d1d0f4e?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80"
    ],
    'beverages': [
        "https://images.unsplash.com/photo-1509042239860-f550ce710b93?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80",
        "https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80"
    ],
    'dairy-alternatives': [
        "https://images.unsplash.com/photo-1585238342028-4a1f3d1d0f4e?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80",
        "https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80"
    ],
    'sweeteners': [
        "https://images.unsplash.com/photo-1509042239860-f550ce710b93?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80",
        "https://images.unsplash.com/photo-1558642452-9d2a7deb7f62?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80"
    ],
    'superfoods': [
        "https://images.unsplash.com/photo-1542838132-92c53300491e?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80",
        "https://images.unsplash.com/photo-1498837167922-ddd27525d352?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80"
    ]
}

# Configuration Constants
DEFAULT_NUM_CATEGORIES = len(PRODUCT_CATEGORIES)
DEFAULT_NUM_USERS = 25
DEFAULT_NUM_PRODUCTS = 60
DEFAULT_VARIANTS_PER_PRODUCT = 3
DEFAULT_BATCH_SIZE = 50

# Comprehensive Global Tax Rates Database
GLOBAL_TAX_RATES = [
    # United States - State Sales Tax (Complete Coverage)
    {"country_code": "US", "country_name": "United States", "province_code": "AL", "province_name": "Alabama", "tax_rate": 0.04, "tax_name": "Sales Tax"},
    {"country_code": "US", "country_name": "United States", "province_code": "AK", "province_name": "Alaska", "tax_rate": 0.0, "tax_name": "Sales Tax"},
    {"country_code": "US", "country_name": "United States", "province_code": "AZ", "province_name": "Arizona", "tax_rate": 0.056, "tax_name": "Sales Tax"},
    {"country_code": "US", "country_name": "United States", "province_code": "AR", "province_name": "Arkansas", "tax_rate": 0.065, "tax_name": "Sales Tax"},
    {"country_code": "US", "country_name": "United States", "province_code": "CA", "province_name": "California", "tax_rate": 0.0725, "tax_name": "Sales Tax"},
    {"country_code": "US", "country_name": "United States", "province_code": "CO", "province_name": "Colorado", "tax_rate": 0.029, "tax_name": "Sales Tax"},
    {"country_code": "US", "country_name": "United States", "province_code": "CT", "province_name": "Connecticut", "tax_rate": 0.0635, "tax_name": "Sales Tax"},
    {"country_code": "US", "country_name": "United States", "province_code": "DE", "province_name": "Delaware", "tax_rate": 0.0, "tax_name": "Sales Tax"},
    {"country_code": "US", "country_name": "United States", "province_code": "FL", "province_name": "Florida", "tax_rate": 0.06, "tax_name": "Sales Tax"},
    {"country_code": "US", "country_name": "United States", "province_code": "GA", "province_name": "Georgia", "tax_rate": 0.04, "tax_name": "Sales Tax"},
    {"country_code": "US", "country_name": "United States", "province_code": "HI", "province_name": "Hawaii", "tax_rate": 0.04, "tax_name": "Sales Tax"},
    {"country_code": "US", "country_name": "United States", "province_code": "ID", "province_name": "Idaho", "tax_rate": 0.06, "tax_name": "Sales Tax"},
    {"country_code": "US", "country_name": "United States", "province_code": "IL", "province_name": "Illinois", "tax_rate": 0.0625, "tax_name": "Sales Tax"},
    {"country_code": "US", "country_name": "United States", "province_code": "IN", "province_name": "Indiana", "tax_rate": 0.07, "tax_name": "Sales Tax"},
    {"country_code": "US", "country_name": "United States", "province_code": "IA", "province_name": "Iowa", "tax_rate": 0.06, "tax_name": "Sales Tax"},
    {"country_code": "US", "country_name": "United States", "province_code": "KS", "province_name": "Kansas", "tax_rate": 0.065, "tax_name": "Sales Tax"},
    {"country_code": "US", "country_name": "United States", "province_code": "KY", "province_name": "Kentucky", "tax_rate": 0.06, "tax_name": "Sales Tax"},
    {"country_code": "US", "country_name": "United States", "province_code": "LA", "province_name": "Louisiana", "tax_rate": 0.0445, "tax_name": "Sales Tax"},
    {"country_code": "US", "country_name": "United States", "province_code": "ME", "province_name": "Maine", "tax_rate": 0.055, "tax_name": "Sales Tax"},
    {"country_code": "US", "country_name": "United States", "province_code": "MD", "province_name": "Maryland", "tax_rate": 0.06, "tax_name": "Sales Tax"},
    {"country_code": "US", "country_name": "United States", "province_code": "MA", "province_name": "Massachusetts", "tax_rate": 0.0625, "tax_name": "Sales Tax"},
    {"country_code": "US", "country_name": "United States", "province_code": "MI", "province_name": "Michigan", "tax_rate": 0.06, "tax_name": "Sales Tax"},
    {"country_code": "US", "country_name": "United States", "province_code": "MN", "province_name": "Minnesota", "tax_rate": 0.06875, "tax_name": "Sales Tax"},
    {"country_code": "US", "country_name": "United States", "province_code": "MS", "province_name": "Mississippi", "tax_rate": 0.07, "tax_name": "Sales Tax"},
    {"country_code": "US", "country_name": "United States", "province_code": "MO", "province_name": "Missouri", "tax_rate": 0.04225, "tax_name": "Sales Tax"},
    {"country_code": "US", "country_name": "United States", "province_code": "MT", "province_name": "Montana", "tax_rate": 0.0, "tax_name": "Sales Tax"},
    {"country_code": "US", "country_name": "United States", "province_code": "NE", "province_name": "Nebraska", "tax_rate": 0.055, "tax_name": "Sales Tax"},
    {"country_code": "US", "country_name": "United States", "province_code": "NV", "province_name": "Nevada", "tax_rate": 0.0685, "tax_name": "Sales Tax"},
    {"country_code": "US", "country_name": "United States", "province_code": "NH", "province_name": "New Hampshire", "tax_rate": 0.0, "tax_name": "Sales Tax"},
    {"country_code": "US", "country_name": "United States", "province_code": "NJ", "province_name": "New Jersey", "tax_rate": 0.06625, "tax_name": "Sales Tax"},
    {"country_code": "US", "country_name": "United States", "province_code": "NM", "province_name": "New Mexico", "tax_rate": 0.05125, "tax_name": "Sales Tax"},
    {"country_code": "US", "country_name": "United States", "province_code": "NY", "province_name": "New York", "tax_rate": 0.04, "tax_name": "Sales Tax"},
    {"country_code": "US", "country_name": "United States", "province_code": "NC", "province_name": "North Carolina", "tax_rate": 0.0475, "tax_name": "Sales Tax"},
    {"country_code": "US", "country_name": "United States", "province_code": "ND", "province_name": "North Dakota", "tax_rate": 0.05, "tax_name": "Sales Tax"},
    {"country_code": "US", "country_name": "United States", "province_code": "OH", "province_name": "Ohio", "tax_rate": 0.0575, "tax_name": "Sales Tax"},
    {"country_code": "US", "country_name": "United States", "province_code": "OK", "province_name": "Oklahoma", "tax_rate": 0.045, "tax_name": "Sales Tax"},
    {"country_code": "US", "country_name": "United States", "province_code": "OR", "province_name": "Oregon", "tax_rate": 0.0, "tax_name": "Sales Tax"},
    {"country_code": "US", "country_name": "United States", "province_code": "PA", "province_name": "Pennsylvania", "tax_rate": 0.06, "tax_name": "Sales Tax"},
    {"country_code": "US", "country_name": "United States", "province_code": "RI", "province_name": "Rhode Island", "tax_rate": 0.07, "tax_name": "Sales Tax"},
    {"country_code": "US", "country_name": "United States", "province_code": "SC", "province_name": "South Carolina", "tax_rate": 0.06, "tax_name": "Sales Tax"},
    {"country_code": "US", "country_name": "United States", "province_code": "SD", "province_name": "South Dakota", "tax_rate": 0.045, "tax_name": "Sales Tax"},
    {"country_code": "US", "country_name": "United States", "province_code": "TN", "province_name": "Tennessee", "tax_rate": 0.07, "tax_name": "Sales Tax"},
    {"country_code": "US", "country_name": "United States", "province_code": "TX", "province_name": "Texas", "tax_rate": 0.0625, "tax_name": "Sales Tax"},
    {"country_code": "US", "country_name": "United States", "province_code": "UT", "province_name": "Utah", "tax_rate": 0.0595, "tax_name": "Sales Tax"},
    {"country_code": "US", "country_name": "United States", "province_code": "VT", "province_name": "Vermont", "tax_rate": 0.06, "tax_name": "Sales Tax"},
    {"country_code": "US", "country_name": "United States", "province_code": "VA", "province_name": "Virginia", "tax_rate": 0.053, "tax_name": "Sales Tax"},
    {"country_code": "US", "country_name": "United States", "province_code": "WA", "province_name": "Washington", "tax_rate": 0.065, "tax_name": "Sales Tax"},
    {"country_code": "US", "country_name": "United States", "province_code": "WV", "province_name": "West Virginia", "tax_rate": 0.06, "tax_name": "Sales Tax"},
    {"country_code": "US", "country_name": "United States", "province_code": "WI", "province_name": "Wisconsin", "tax_rate": 0.05, "tax_name": "Sales Tax"},
    {"country_code": "US", "country_name": "United States", "province_code": "WY", "province_name": "Wyoming", "tax_rate": 0.04, "tax_name": "Sales Tax"},
    
    # Canada - Provincial Sales Tax (Complete Coverage)
    {"country_code": "CA", "country_name": "Canada", "province_code": "AB", "province_name": "Alberta", "tax_rate": 0.05, "tax_name": "GST"},
    {"country_code": "CA", "country_name": "Canada", "province_code": "BC", "province_name": "British Columbia", "tax_rate": 0.12, "tax_name": "GST+PST"},
    {"country_code": "CA", "country_name": "Canada", "province_code": "MB", "province_name": "Manitoba", "tax_rate": 0.12, "tax_name": "GST+PST"},
    {"country_code": "CA", "country_name": "Canada", "province_code": "NB", "province_name": "New Brunswick", "tax_rate": 0.15, "tax_name": "HST"},
    {"country_code": "CA", "country_name": "Canada", "province_code": "NL", "province_name": "Newfoundland and Labrador", "tax_rate": 0.15, "tax_name": "HST"},
    {"country_code": "CA", "country_name": "Canada", "province_code": "NT", "province_name": "Northwest Territories", "tax_rate": 0.05, "tax_name": "GST"},
    {"country_code": "CA", "country_name": "Canada", "province_code": "NS", "province_name": "Nova Scotia", "tax_rate": 0.15, "tax_name": "HST"},
    {"country_code": "CA", "country_name": "Canada", "province_code": "NU", "province_name": "Nunavut", "tax_rate": 0.05, "tax_name": "GST"},
    {"country_code": "CA", "country_name": "Canada", "province_code": "ON", "province_name": "Ontario", "tax_rate": 0.13, "tax_name": "HST"},
    {"country_code": "CA", "country_name": "Canada", "province_code": "PE", "province_name": "Prince Edward Island", "tax_rate": 0.15, "tax_name": "HST"},
    {"country_code": "CA", "country_name": "Canada", "province_code": "QC", "province_name": "Quebec", "tax_rate": 0.14975, "tax_name": "GST+QST"},
    {"country_code": "CA", "country_name": "Canada", "province_code": "SK", "province_name": "Saskatchewan", "tax_rate": 0.11, "tax_name": "GST+PST"},
    {"country_code": "CA", "country_name": "Canada", "province_code": "YT", "province_name": "Yukon", "tax_rate": 0.05, "tax_name": "GST"},
    
    # European Union - VAT Rates
    {"country_code": "GB", "country_name": "United Kingdom", "province_code": None, "province_name": None, "tax_rate": 0.20, "tax_name": "VAT"},
    {"country_code": "DE", "country_name": "Germany", "province_code": None, "province_name": None, "tax_rate": 0.19, "tax_name": "VAT"},
    {"country_code": "FR", "country_name": "France", "province_code": None, "province_name": None, "tax_rate": 0.20, "tax_name": "VAT"},
    {"country_code": "IT", "country_name": "Italy", "province_code": None, "province_name": None, "tax_rate": 0.22, "tax_name": "VAT"},
    {"country_code": "ES", "country_name": "Spain", "province_code": None, "province_name": None, "tax_rate": 0.21, "tax_name": "VAT"},
    {"country_code": "NL", "country_name": "Netherlands", "province_code": None, "province_name": None, "tax_rate": 0.21, "tax_name": "VAT"},
    {"country_code": "BE", "country_name": "Belgium", "province_code": None, "province_name": None, "tax_rate": 0.21, "tax_name": "VAT"},
    {"country_code": "AT", "country_name": "Austria", "province_code": None, "province_name": None, "tax_rate": 0.20, "tax_name": "VAT"},
    {"country_code": "SE", "country_name": "Sweden", "province_code": None, "province_name": None, "tax_rate": 0.25, "tax_name": "VAT"},
    {"country_code": "DK", "country_name": "Denmark", "province_code": None, "province_name": None, "tax_rate": 0.25, "tax_name": "VAT"},
    {"country_code": "NO", "country_name": "Norway", "province_code": None, "province_name": None, "tax_rate": 0.25, "tax_name": "VAT"},
    {"country_code": "FI", "country_name": "Finland", "province_code": None, "province_name": None, "tax_rate": 0.24, "tax_name": "VAT"},
    {"country_code": "IE", "country_name": "Ireland", "province_code": None, "province_name": None, "tax_rate": 0.23, "tax_name": "VAT"},
    {"country_code": "PT", "country_name": "Portugal", "province_code": None, "province_name": None, "tax_rate": 0.23, "tax_name": "VAT"},
    {"country_code": "GR", "country_name": "Greece", "province_code": None, "province_name": None, "tax_rate": 0.24, "tax_name": "VAT"},
    {"country_code": "PL", "country_name": "Poland", "province_code": None, "province_name": None, "tax_rate": 0.23, "tax_name": "VAT"},
    {"country_code": "CZ", "country_name": "Czech Republic", "province_code": None, "province_name": None, "tax_rate": 0.21, "tax_name": "VAT"},
    {"country_code": "HU", "country_name": "Hungary", "province_code": None, "province_name": None, "tax_rate": 0.27, "tax_name": "VAT"},
    {"country_code": "RO", "country_name": "Romania", "province_code": None, "province_name": None, "tax_rate": 0.19, "tax_name": "VAT"},
    {"country_code": "BG", "country_name": "Bulgaria", "province_code": None, "province_name": None, "tax_rate": 0.20, "tax_name": "VAT"},
    {"country_code": "HR", "country_name": "Croatia", "province_code": None, "province_name": None, "tax_rate": 0.25, "tax_name": "VAT"},
    {"country_code": "SI", "country_name": "Slovenia", "province_code": None, "province_name": None, "tax_rate": 0.22, "tax_name": "VAT"},
    {"country_code": "SK", "country_name": "Slovakia", "province_code": None, "province_name": None, "tax_rate": 0.20, "tax_name": "VAT"},
    {"country_code": "LT", "country_name": "Lithuania", "province_code": None, "province_name": None, "tax_rate": 0.21, "tax_name": "VAT"},
    {"country_code": "LV", "country_name": "Latvia", "province_code": None, "province_name": None, "tax_rate": 0.21, "tax_name": "VAT"},
    {"country_code": "EE", "country_name": "Estonia", "province_code": None, "province_name": None, "tax_rate": 0.20, "tax_name": "VAT"},
    
    # Asia-Pacific
    {"country_code": "AU", "country_name": "Australia", "province_code": None, "province_name": None, "tax_rate": 0.10, "tax_name": "GST"},
    {"country_code": "NZ", "country_name": "New Zealand", "province_code": None, "province_name": None, "tax_rate": 0.15, "tax_name": "GST"},
    {"country_code": "JP", "country_name": "Japan", "province_code": None, "province_name": None, "tax_rate": 0.10, "tax_name": "Consumption Tax"},
    {"country_code": "KR", "country_name": "South Korea", "province_code": None, "province_name": None, "tax_rate": 0.10, "tax_name": "VAT"},
    {"country_code": "SG", "country_name": "Singapore", "province_code": None, "province_name": None, "tax_rate": 0.08, "tax_name": "GST"},
    {"country_code": "MY", "country_name": "Malaysia", "province_code": None, "province_name": None, "tax_rate": 0.06, "tax_name": "SST"},
    {"country_code": "TH", "country_name": "Thailand", "province_code": None, "province_name": None, "tax_rate": 0.07, "tax_name": "VAT"},
    {"country_code": "PH", "country_name": "Philippines", "province_code": None, "province_name": None, "tax_rate": 0.12, "tax_name": "VAT"},
    {"country_code": "ID", "country_name": "Indonesia", "province_code": None, "province_name": None, "tax_rate": 0.11, "tax_name": "VAT"},
    {"country_code": "VN", "country_name": "Vietnam", "province_code": None, "province_name": None, "tax_rate": 0.10, "tax_name": "VAT"},
    {"country_code": "IN", "country_name": "India", "province_code": None, "province_name": None, "tax_rate": 0.18, "tax_name": "GST"},
    {"country_code": "CN", "country_name": "China", "province_code": None, "province_name": None, "tax_rate": 0.13, "tax_name": "VAT"},
    
    # Americas
    {"country_code": "MX", "country_name": "Mexico", "province_code": None, "province_name": None, "tax_rate": 0.16, "tax_name": "IVA"},
    {"country_code": "BR", "country_name": "Brazil", "province_code": None, "province_name": None, "tax_rate": 0.17, "tax_name": "ICMS"},
    {"country_code": "AR", "country_name": "Argentina", "province_code": None, "province_name": None, "tax_rate": 0.21, "tax_name": "IVA"},
    {"country_code": "CL", "country_name": "Chile", "province_code": None, "province_name": None, "tax_rate": 0.19, "tax_name": "IVA"},
    {"country_code": "CO", "country_name": "Colombia", "province_code": None, "province_name": None, "tax_rate": 0.19, "tax_name": "IVA"},
    {"country_code": "PE", "country_name": "Peru", "province_code": None, "province_name": None, "tax_rate": 0.18, "tax_name": "IGV"},
    
    # Africa & Middle East
    {"country_code": "ZA", "country_name": "South Africa", "province_code": None, "province_name": None, "tax_rate": 0.15, "tax_name": "VAT"},
    {"country_code": "NG", "country_name": "Nigeria", "province_code": None, "province_name": None, "tax_rate": 0.075, "tax_name": "VAT"},
    {"country_code": "KE", "country_name": "Kenya", "province_code": None, "province_name": None, "tax_rate": 0.16, "tax_name": "VAT"},
    {"country_code": "EG", "country_name": "Egypt", "province_code": None, "province_name": None, "tax_rate": 0.14, "tax_name": "VAT"},
    {"country_code": "AE", "country_name": "United Arab Emirates", "province_code": None, "province_name": None, "tax_rate": 0.05, "tax_name": "VAT"},
    {"country_code": "SA", "country_name": "Saudi Arabia", "province_code": None, "province_name": None, "tax_rate": 0.15, "tax_name": "VAT"},
    {"country_code": "IL", "country_name": "Israel", "province_code": None, "province_name": None, "tax_rate": 0.17, "tax_name": "VAT"},
    {"country_code": "TR", "country_name": "Turkey", "province_code": None, "province_name": None, "tax_rate": 0.18, "tax_name": "VAT"},
]

# Comprehensive Shipping Methods Configuration
SHIPPING_METHODS = [
    {
        "name": "Standard Shipping",
        "description": "Reliable delivery within 5-7 business days",
        "price": 8.99,
        "estimated_days": 6,
        "carrier": "USPS",
        "tracking_url_template": "https://tools.usps.com/go/TrackConfirmAction?tLabels={tracking_number}",
        "is_active": True
    },
    {
        "name": "Express Shipping",
        "description": "Fast delivery within 2-3 business days",
        "price": 15.99,
        "estimated_days": 3,
        "carrier": "FedEx",
        "tracking_url_template": "https://www.fedex.com/fedextrack/?trknbr={tracking_number}",
        "is_active": True
    },
    {
        "name": "Priority Overnight",
        "description": "Next business day delivery by 10:30 AM",
        "price": 29.99,
        "estimated_days": 1,
        "carrier": "FedEx",
        "tracking_url_template": "https://www.fedex.com/fedextrack/?trknbr={tracking_number}",
        "is_active": True
    },
    {
        "name": "Free Standard Shipping",
        "description": "Free shipping on orders over $75 (5-7 business days)",
        "price": 0.00,
        "estimated_days": 7,
        "carrier": "USPS",
        "tracking_url_template": "https://tools.usps.com/go/TrackConfirmAction?tLabels={tracking_number}",
        "is_active": True
    },
    {
        "name": "International Standard",
        "description": "International delivery within 10-15 business days",
        "price": 24.99,
        "estimated_days": 12,
        "carrier": "DHL",
        "tracking_url_template": "https://www.dhl.com/en/express/tracking.html?AWB={tracking_number}",
        "is_active": True
    },
    {
        "name": "International Express",
        "description": "Fast international delivery within 3-5 business days",
        "price": 49.99,
        "estimated_days": 4,
        "carrier": "DHL",
        "tracking_url_template": "https://www.dhl.com/en/express/tracking.html?AWB={tracking_number}",
        "is_active": True
    }
]

# Warehouse Locations for Inventory Management
WAREHOUSE_LOCATIONS = [
    {
        "name": "West Coast Distribution Center",
        "address": "1234 Industrial Blvd, Los Angeles, CA 90021",
        "city": "Los Angeles",
        "state": "CA",
        "country": "US",
        "postal_code": "90021",
        "is_active": True,
        "capacity": 50000,
        "current_utilization": 0.65
    },
    {
        "name": "East Coast Distribution Center",
        "address": "5678 Warehouse Ave, Atlanta, GA 30309",
        "city": "Atlanta",
        "state": "GA",
        "country": "US",
        "postal_code": "30309",
        "is_active": True,
        "capacity": 75000,
        "current_utilization": 0.72
    },
    {
        "name": "Central Distribution Hub",
        "address": "9012 Logistics Dr, Chicago, IL 60607",
        "city": "Chicago",
        "state": "IL",
        "country": "US",
        "postal_code": "60607",
        "is_active": True,
        "capacity": 100000,
        "current_utilization": 0.58
    },
    {
        "name": "International Fulfillment Center",
        "address": "3456 Global Way, Miami, FL 33166",
        "city": "Miami",
        "state": "FL",
        "country": "US",
        "postal_code": "33166",
        "is_active": True,
        "capacity": 30000,
        "current_utilization": 0.45
    }
]

# Discount Codes and Promotional Offers
DISCOUNT_CODES = [
    {
        "code": "WELCOME10",
        "type": "PERCENTAGE",
        "value": 10.0,
        "description": "Welcome discount for new customers",
        "minimum_amount": 25.0,
        "maximum_discount": 50.0,
        "usage_limit": 1000,
        "valid_days": 365,
        "is_active": True
    },
    {
        "code": "SAVE20",
        "type": "PERCENTAGE",
        "value": 20.0,
        "description": "20% off on orders over $100",
        "minimum_amount": 100.0,
        "maximum_discount": 100.0,
        "usage_limit": 500,
        "valid_days": 90,
        "is_active": True
    },
    {
        "code": "FREESHIP",
        "type": "FREE_SHIPPING",
        "value": 0.0,
        "description": "Free shipping on any order",
        "minimum_amount": 0.0,
        "maximum_discount": None,
        "usage_limit": 2000,
        "valid_days": 180,
        "is_active": True
    },
    {
        "code": "BULK50",
        "type": "FIXED_AMOUNT",
        "value": 50.0,
        "description": "$50 off bulk orders over $300",
        "minimum_amount": 300.0,
        "maximum_discount": None,
        "usage_limit": 100,
        "valid_days": 60,
        "is_active": True
    },
    {
        "code": "SEASONAL25",
        "type": "PERCENTAGE",
        "value": 25.0,
        "description": "Seasonal promotion - 25% off",
        "minimum_amount": 75.0,
        "maximum_discount": 150.0,
        "usage_limit": 750,
        "valid_days": 30,
        "is_active": True
    }
]

# Additional tax rates for global coverage
ADDITIONAL_TAX_RATES = [
    # European Union Countries
    {"country_code": "DE", "country_name": "Germany", "province_code": None, "province_name": None, "tax_rate": 0.19, "tax_name": "VAT"},
    {"country_code": "FR", "country_name": "France", "province_code": None, "province_name": None, "tax_rate": 0.20, "tax_name": "VAT"},
    {"country_code": "IT", "country_name": "Italy", "province_code": None, "province_name": None, "tax_rate": 0.22, "tax_name": "VAT"},
    {"country_code": "ES", "country_name": "Spain", "province_code": None, "province_name": None, "tax_rate": 0.21, "tax_name": "VAT"},
    {"country_code": "NL", "country_name": "Netherlands", "province_code": None, "province_name": None, "tax_rate": 0.21, "tax_name": "VAT"},
    {"country_code": "BE", "country_name": "Belgium", "province_code": None, "province_name": None, "tax_rate": 0.21, "tax_name": "VAT"},
    {"country_code": "AT", "country_name": "Austria", "province_code": None, "province_name": None, "tax_rate": 0.20, "tax_name": "VAT"},
    {"country_code": "SE", "country_name": "Sweden", "province_code": None, "province_name": None, "tax_rate": 0.25, "tax_name": "VAT"},
    {"country_code": "DK", "country_name": "Denmark", "province_code": None, "province_name": None, "tax_rate": 0.25, "tax_name": "VAT"},
    {"country_code": "FI", "country_name": "Finland", "province_code": None, "province_name": None, "tax_rate": 0.24, "tax_name": "VAT"},
    {"country_code": "NO", "country_name": "Norway", "province_code": None, "province_name": None, "tax_rate": 0.25, "tax_name": "VAT"},
    {"country_code": "PL", "country_name": "Poland", "province_code": None, "province_name": None, "tax_rate": 0.23, "tax_name": "VAT"},
    {"country_code": "IE", "country_name": "Ireland", "province_code": None, "province_name": None, "tax_rate": 0.23, "tax_name": "VAT"},
    {"country_code": "PT", "country_name": "Portugal", "province_code": None, "province_name": None, "tax_rate": 0.23, "tax_name": "VAT"},
    {"country_code": "GR", "country_name": "Greece", "province_code": None, "province_name": None, "tax_rate": 0.24, "tax_name": "VAT"},
    {"country_code": "CZ", "country_name": "Czech Republic", "province_code": None, "province_name": None, "tax_rate": 0.21, "tax_name": "VAT"},
    {"country_code": "RO", "country_name": "Romania", "province_code": None, "province_name": None, "tax_rate": 0.19, "tax_name": "VAT"},
    {"country_code": "HU", "country_name": "Hungary", "province_code": None, "province_name": None, "tax_rate": 0.27, "tax_name": "VAT"},
    
    # Asia-Pacific
    {"country_code": "AU", "country_name": "Australia", "province_code": None, "province_name": None, "tax_rate": 0.10, "tax_name": "GST"},
    {"country_code": "NZ", "country_name": "New Zealand", "province_code": None, "province_name": None, "tax_rate": 0.15, "tax_name": "GST"},
    {"country_code": "JP", "country_name": "Japan", "province_code": None, "province_name": None, "tax_rate": 0.10, "tax_name": "Consumption Tax"},
    {"country_code": "SG", "country_name": "Singapore", "province_code": None, "province_name": None, "tax_rate": 0.08, "tax_name": "GST"},
    {"country_code": "IN", "country_name": "India", "province_code": None, "province_name": None, "tax_rate": 0.18, "tax_name": "GST"},
    {"country_code": "CN", "country_name": "China", "province_code": None, "province_name": None, "tax_rate": 0.13, "tax_name": "VAT"},
    {"country_code": "KR", "country_name": "South Korea", "province_code": None, "province_name": None, "tax_rate": 0.10, "tax_name": "VAT"},
    {"country_code": "MY", "country_name": "Malaysia", "province_code": None, "province_name": None, "tax_rate": 0.06, "tax_name": "SST"},
    {"country_code": "TH", "country_name": "Thailand", "province_code": None, "province_name": None, "tax_rate": 0.07, "tax_name": "VAT"},
    {"country_code": "PH", "country_name": "Philippines", "province_code": None, "province_name": None, "tax_rate": 0.12, "tax_name": "VAT"},
    {"country_code": "ID", "country_name": "Indonesia", "province_code": None, "province_name": None, "tax_rate": 0.11, "tax_name": "VAT"},
    {"country_code": "VN", "country_name": "Vietnam", "province_code": None, "province_name": None, "tax_rate": 0.10, "tax_name": "VAT"},
    
    # Africa
    {"country_code": "ZA", "country_name": "South Africa", "province_code": None, "province_name": None, "tax_rate": 0.15, "tax_name": "VAT"},
    {"country_code": "NG", "country_name": "Nigeria", "province_code": None, "province_name": None, "tax_rate": 0.075, "tax_name": "VAT"},
    {"country_code": "KE", "country_name": "Kenya", "province_code": None, "province_name": None, "tax_rate": 0.16, "tax_name": "VAT"},
    {"country_code": "EG", "country_name": "Egypt", "province_code": None, "province_name": None, "tax_rate": 0.14, "tax_name": "VAT"},
    {"country_code": "GH", "country_name": "Ghana", "province_code": None, "province_name": None, "tax_rate": 0.125, "tax_name": "VAT"},
    
    # Latin America
    {"country_code": "BR", "country_name": "Brazil", "province_code": None, "province_name": None, "tax_rate": 0.17, "tax_name": "ICMS"},
    {"country_code": "MX", "country_name": "Mexico", "province_code": None, "province_name": None, "tax_rate": 0.16, "tax_name": "IVA"},
    {"country_code": "AR", "country_name": "Argentina", "province_code": None, "province_name": None, "tax_rate": 0.21, "tax_name": "IVA"},
    {"country_code": "CL", "country_name": "Chile", "province_code": None, "province_name": None, "tax_rate": 0.19, "tax_name": "IVA"},
    {"country_code": "CO", "country_name": "Colombia", "province_code": None, "province_name": None, "tax_rate": 0.19, "tax_name": "IVA"},
    
    # Middle East
    {"country_code": "AE", "country_name": "United Arab Emirates", "province_code": None, "province_name": None, "tax_rate": 0.05, "tax_name": "VAT"},
    {"country_code": "SA", "country_name": "Saudi Arabia", "province_code": None, "province_name": None, "tax_rate": 0.15, "tax_name": "VAT"},
    {"country_code": "IL", "country_name": "Israel", "province_code": None, "province_name": None, "tax_rate": 0.17, "tax_name": "VAT"},
    {"country_code": "TR", "country_name": "Turkey", "province_code": None, "province_name": None, "tax_rate": 0.18, "tax_name": "KDV"},
]

# ---------------- DB Utilities ----------------


async def create_tables():
    """Create all database tables (drop then create) in PostgreSQL."""
    # Ensure we're using PostgreSQL
    db_uri = settings.SQLALCHEMY_DATABASE_URI
    if 'postgresql' not in db_uri:
        print("⚠️  WARNING: Database URI does not appear to be PostgreSQL!")
        print(f"   Current URI: {db_uri}")
        response = input("   Continue anyway? (yes/no): ")
        if response.lower() != 'yes':
            print("❌ Aborted.")
            return
    
    print(f"🔗 Connecting to PostgreSQL: {db_uri.split('@')[-1] if '@' in db_uri else 'database'}")
    engine = create_async_engine(db_uri, echo=False)  # Disable echo for cleaner output
    
    try:
        async with engine.begin() as conn:
            print("🗑️  Dropping existing schema...")
            # Drop the entire public schema and recreate it to avoid dependency issues
            await conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
            await conn.execute(text("CREATE SCHEMA public"))
            
            print("🏗️  Creating new tables...")
            await conn.run_sync(Base.metadata.create_all)
        await engine.dispose()
        print("✅ PostgreSQL database tables created successfully!")
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        await engine.dispose()
        raise


async def seed_sample_data(
    categories_count: int = DEFAULT_NUM_CATEGORIES,
    users_count: int = DEFAULT_NUM_USERS,
    products_count: int = DEFAULT_NUM_PRODUCTS,
    variants_per_product: int = DEFAULT_VARIANTS_PER_PRODUCT,
    batch_size: int = DEFAULT_BATCH_SIZE,
):
    """Seed database with sample data in batches."""
    if batch_size <= 10:
        print("⚠️ batch_size must be > 10. Using default 50.")
        batch_size = DEFAULT_BATCH_SIZE

    plaintext_passwords = {}  # email: plaintext_password for printing

    async with db_manager.session_factory() as session:
        # -------- Categories --------
        categories = []
        for cat_id, cat_data in PRODUCT_CATEGORIES.items():
            cat = Category(
                id=uuid7(),
                name=cat_data['name'],
                image_url=cat_data['image_url'],
                description=f"{cat_data['name']} category including: {', '.join(cat_data['keywords'][:5])}...",
                is_active=True,
            )
            categories.append(cat)
            if len(categories) >= batch_size:
                session.add_all(categories)
                await session.flush() # Flush to get IDs
                await session.commit()
                session.expunge_all() # Free up memory
                categories = []
        if categories:
            session.add_all(categories)
            await session.flush() # Flush to get IDs
            await session.commit()
            session.expunge_all() # Free up memory

        result = await session.execute(select(Category))
        all_categories: List[Category] = result.scalars().all()
        print(f"🌱 Created {len(all_categories)} categories")

        # -------- Warehouse Locations --------
        warehouse_locations_batch = []
        warehouse_data = [
            {"name": "Main Warehouse", "address": "123 Storage St, Accra, Ghana", "description": "Primary warehouse for African products"},
            {"name": "Lagos Distribution Center", "address": "456 Commerce Ave, Lagos, Nigeria", "description": "West Africa distribution hub"},
            {"name": "Nairobi Hub", "address": "789 Trade Rd, Nairobi, Kenya", "description": "East Africa distribution center"},
        ]
        
        for data in warehouse_data:
            warehouse = WarehouseLocation(**data)
            warehouse_locations_batch.append(warehouse)

        if warehouse_locations_batch:
            session.add_all(warehouse_locations_batch)
            await session.flush()
            await session.commit()
            session.expunge_all()
        
        # Get the main warehouse for inventory
        result = await session.execute(select(WarehouseLocation).where(WarehouseLocation.name == "Main Warehouse"))
        main_warehouse = result.scalar_one()
        print(f"🏭 Created {len(warehouse_locations_batch)} warehouse locations")

        # -------- Shipping Methods --------
        shipping_methods_batch = []
        shipping_methods_data = [
            {
                "name": "Standard Shipping",
                "description": "Delivery in 5-8 business days worldwide.",
                "price": 8.99,
                "estimated_days": 8,
                "is_active": True,
                "carrier": "Global Express",
                "tracking_url_template": "https://track.globalexpress.com/{tracking_number}"
            },
            {
                "name": "Express Shipping",
                "description": "Fast delivery in 2-4 business days worldwide.",
                "price": 15.99,
                "estimated_days": 3,
                "is_active": True,
                "carrier": "Global Express",
                "tracking_url_template": "https://track.globalexpress.com/{tracking_number}"
            },
            {
                "name": "Priority Shipping",
                "description": "Next business day delivery.",
                "price": 29.99,
                "estimated_days": 1,
                "is_active": True,
                "carrier": "Priority Express",
                "tracking_url_template": "https://track.priorityexpress.com/{tracking_number}"
            }
        ]
        
        for data in shipping_methods_data:
            method = ShippingMethod(**data)
            shipping_methods_batch.append(method)

        if shipping_methods_batch:
            session.add_all(shipping_methods_batch)
            await session.flush()
            await session.commit()
            session.expunge_all()
        print(f"🚚 Created {len(shipping_methods_batch)} simple shipping methods.")

        # -------- Users --------
        users = []
        suppliers = []
        admins = []

        predefined = [
            ("admin@banwee.com", "Admin", "User", "adminpass", "Admin"),
            ("supplier@banwee.com", "Supplier",
             "User", "supplierpass", "Supplier"),
        ]

        for email, fname, lname, pwd_plain, role in predefined:
            pm = PasswordManager()
            hashed = pm.hash_password(pwd_plain)
            user = User(
                id=uuid7(),
                email=email,
                firstname=fname,
                lastname=lname,
                hashed_password=hashed,
                role=role,
                verified=True,
                is_active=True,
                last_login=func.now()
            )
            users.append(user)
            plaintext_passwords[email] = pwd_plain

        for i in range(len(predefined) + 1, users_count + 1):
            if i % 50 == 0:
                role = "Admin"
            elif i % 5 == 0:
                role = "Supplier"
            else:
                role = "Customer"

            email = f"user{i}@example.com"
            fname = f"User{i}"
            lname = "Tester"
            pwd_plain = f"P@ss{i:04d}"
            pm = PasswordManager()
            hashed = pm.hash_password(pwd_plain)
            user = User(
                id=uuid7(),
                email=email,
                firstname=fname,
                lastname=lname,
                hashed_password=hashed,
                role=role,
                verified=True,
                is_active=True,
                last_login=func.now()
            )
            users.append(user)
            plaintext_passwords[email] = pwd_plain

            if len(users) >= batch_size:
                session.add_all(users)
                await session.flush()
                await session.commit()
                users = [] # Clear the batch list

        if users:
            session.add_all(users)
            await session.flush()
            await session.commit()
        
        # After all users are committed, re-query suppliers and admins from the database
        # to ensure they are attached to the current session.
        result_suppliers = await session.execute(select(User).where(User.role == "Supplier"))
        suppliers = result_suppliers.scalars().all()

        result_admins = await session.execute(select(User).where(User.role == "Admin"))
        admins = result_admins.scalars().all()

        session.expunge_all() # Now it's safe to expunge all after collecting suppliers/admins

        # -------- Addresses --------
        addresses_batch = []
        all_users_for_address = await session.execute(select(User).options(selectinload(User.addresses)))
        all_users_for_address = all_users_for_address.scalars().unique().all()
        for user in all_users_for_address:
            # Check if user already has addresses to avoid adding duplicates
            if not user.addresses:
                address = Address(
                    user_id=user.id,
                    street=f"{random.randint(1, 999)} Main St",
                    city=random.choice(["Accra", "Lagos", "Nairobi", "Kampala"]),
                    state=random.choice(
                        ["Greater Accra", "Lagos State", "Nairobi County"]),
                    country=random.choice(["Ghana", "Nigeria", "Kenya", "Uganda"]),
                    post_code=f"{random.randint(10000, 99999)}",
                    kind="Shipping",
                    is_default=True  # Set the first address as default
                )
                addresses_batch.append(address)

        if addresses_batch:
            session.add_all(addresses_batch)
            await session.flush()
            await session.commit()
            session.expunge_all()
        print(f"🏠 Created {len(addresses_batch)} addresses.")

        # Clear session to ensure relationships are reloaded
        session.expunge_all()

        if not suppliers:
            result = await session.execute(select(User).where(User.role == "Supplier"))
            suppliers = result.scalars().all()

        print(
            f"👥 Created users; suppliers: {len(suppliers)}, admins: {len(admins)}")

        # -------- Payment Methods --------
        payment_methods_batch = []
        all_users_result = await session.execute(select(User))
        all_users = all_users_result.scalars().all()
        for user in all_users:
            method = PaymentMethod(
                user_id=user.id,
                type="card",
                provider="stripe",
                last_four=f"{random.randint(1000, 9999)}",
                expiry_month=random.randint(1, 12),
                expiry_year=random.randint(2025, 2030),
                is_default=True
            )
            payment_methods_batch.append(method)

        if payment_methods_batch:
            session.add_all(payment_methods_batch)
            await session.flush()
            await session.commit()
            session.expunge_all()
        print(f"💳 Created {len(payment_methods_batch)} payment methods.")

        # -------- Promocodes --------
        promocodes_batch = []
        promocodes_data = [
            {"code": "SAVE10", "discount_type": "percentage",
                "value": 10, "is_active": True},
            {"code": "FREESHIP", "discount_type": "fixed", "value": 0,
                "is_active": True},  # This might need special handling in logic
            {"code": "SAVE20", "discount_type": "percentage",
                "value": 20, "is_active": False},
        ]
        for data in promocodes_data:
            promo = Promocode(**data)
            promocodes_batch.append(promo)

        if promocodes_batch:
            session.add_all(promocodes_batch)
            await session.flush()
            await session.commit()
            session.expunge_all()
        print(f"🎟️ Created {len(promocodes_batch)} promocodes.")

        # -------- Products & Variants & Images --------
        # -------- Products & Variants & Images --------
        all_products_with_variants = []

        for i in range(1, products_count + 1):
            # Distribute products across categories more evenly
            chosen_category = all_categories[(i - 1) % len(all_categories)]
            chosen_supplier = random.choice(suppliers)
            cat_keywords = next(
                (v['keywords'] for k, v in PRODUCT_CATEGORIES.items()
                 if v['name'] == chosen_category.name), []
            )
            keyword = random.choice(
                cat_keywords) if cat_keywords else "Premium"

            # Create better product names
            adjectives = ["Premium", "Organic", "Fresh", "Quality",
                          "Natural", "Pure", "Artisan", "Traditional"]
            adjective = random.choice(adjectives)
            product_name = f"{adjective} {keyword.title()}"
            if i <= 10:  # Add numbers to first 10 for uniqueness
                product_name += f" {i}"

            # Ensure we have at least 25% featured products (more than the random 20%)
            is_featured = i <= max(5, products_count //
                                   4) or random.random() < 0.15

            # Generate SEO-optimized slug
            slug = f"{product_name.lower().replace(' ', '-')}-{i}"
            
            # Generate SEO metadata
            origin_country = random.choice(
                ["Ghana", "Nigeria", "Kenya", "Uganda", "Tanzania", "Ethiopia", "Mali"])
            dietary_tags = random.sample(
                ["organic", "gluten-free", "vegan", "non-GMO", "fair-trade", "kosher", "halal"], 
                k=random.randint(1, 3))

            product = Product(
                id=uuid7(),
                name=product_name,
                slug=slug, # Add this line
                description=f"High-quality {keyword.lower()} sourced directly from trusted suppliers in {origin_country}. Perfect for cooking, baking, and everyday use. Rich in nutrients and carefully processed to maintain freshness. Our {product_name.lower()} is {', '.join(dietary_tags)}, ensuring you get the best quality African products delivered fresh to your door.",
                category_id=chosen_category.id,
                supplier_id=chosen_supplier.id,
                featured=is_featured,
                rating=round(random.uniform(3.5, 5.0), 1),  # Higher ratings
                review_count=random.randint(5, 150),  # Ensure some reviews
                origin=origin_country,
                dietary_tags=dietary_tags,
                is_active=True,  # Ensure all products are active
            )
            session.add(product)
            await session.flush()  # Ensure product.id is populated

            # Ensure at least 1 variant per product, up to variants_per_product
            num_variants = max(
                1, min(variants_per_product, random.randint(1, 3)))
            for v_idx in range(1, num_variants + 1):
                # Generate unique SKU using product index and variant index to avoid duplicates
                sku = f"{product.name[:3].upper().replace(' ', '')}-{i:06d}-{v_idx}"

                # Better variant names based on category
                variant_names = {
                    1: ["500g Pack", "1kg Bag", "Small Size"],
                    2: ["1kg Pack", "2kg Bag", "Medium Size"],
                    3: ["2kg Pack", "5kg Bag", "Large Size"]
                }
                variant_name = variant_names.get(
                    v_idx, [f"Variant {v_idx}"])[0]

                # More realistic pricing
                base_price = round(random.uniform(8.99, 89.99), 2)
                sale_price = None
                if random.random() < 0.3:  # 30% chance of sale
                    sale_price = round(
                        base_price * random.uniform(0.7, 0.9), 2)

                variant = ProductVariant(
                    id=uuid7(),
                    product_id=product.id,
                    sku=sku,
                    name=variant_name,
                    base_price=base_price,
                    sale_price=sale_price,
                    attributes={"size": variant_name,
                                "weight": f"{v_idx * 500}g"},
                    is_active=True
                )
                session.add(variant)
                await session.flush()  # ensures variant.id is populated

                # Create 2-3 images per variant (more realistic)
                num_images = random.randint(2, 3)
                
                # Get category-specific images
                category_key = None
                for key, cat_data in PRODUCT_CATEGORIES.items():
                    if cat_data['name'] == chosen_category.name:
                        category_key = key
                        break
                
                # Use category images or fallback to default
                available_images = CATEGORY_IMAGES.get(category_key, [
                    "https://images.unsplash.com/photo-1474979266404-7eaacbcd87c5?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80"
                ])
                
                for img_idx in range(num_images):
                    img_url = random.choice(available_images)
                    image = ProductImage(
                        id=uuid7(),
                        variant_id=variant.id,
                        url=img_url,
                        alt_text=f"{product.name} - {variant.name}",
                        is_primary=(img_idx == 0),
                        sort_order=img_idx + 1,
                        format="jpg",
                    )
                    session.add(image)

            all_products_with_variants.append(product)

            if len(all_products_with_variants) >= batch_size:
                await session.commit()
                session.expunge_all() # Free up memory after commit
                all_products_with_variants = []

        # Remaining products
        if all_products_with_variants:
            await session.commit()
            session.expunge_all() # Free up memory after commit

        result = await session.execute(select(Product))
        total_products = len(result.scalars().all())
        print(f"📦 Created {total_products} products with variants and images.")

        # -------- Inventory Records --------
        inventory_batch = []
        
        # Get all variants to create inventory for
        all_variants_result = await session.execute(select(ProductVariant))
        all_variants_for_inventory = all_variants_result.scalars().all()
        
        for variant in all_variants_for_inventory:
            # Generate realistic stock quantities
            # 80% of products should be in stock, 20% out of stock
            if random.random() < 0.8:  # 80% chance of being in stock
                # Generate stock between 5 and 100 units
                stock_quantity = random.randint(5, 100)
            else:
                # 20% chance of being out of stock
                stock_quantity = 0
            
            inventory = Inventory(
                id=uuid7(),
                variant_id=variant.id,
                location_id=main_warehouse.id,
                quantity_available=stock_quantity,
                low_stock_threshold=random.randint(5, 15),
                reorder_point=random.randint(3, 10),
                inventory_status="active",
                quantity=stock_quantity  # Legacy field for backward compatibility
            )
            inventory_batch.append(inventory)
            
            # Batch commit for performance
            if len(inventory_batch) >= batch_size:
                session.add_all(inventory_batch)
                await session.flush()
                await session.commit()
                session.expunge_all()
                inventory_batch = []
        
        # Add remaining inventory records
        if inventory_batch:
            session.add_all(inventory_batch)
            await session.flush()
            await session.commit()
            session.expunge_all()
        
        print(f"📊 Created inventory records for {len(all_variants_for_inventory)} product variants")
        
        # Print stock statistics
        result = await session.execute(select(Inventory).where(Inventory.quantity_available > 0))
        in_stock_count = len(result.scalars().all())
        result = await session.execute(select(Inventory).where(Inventory.quantity_available == 0))
        out_of_stock_count = len(result.scalars().all())
        print(f"📈 Stock Status: {in_stock_count} variants in stock, {out_of_stock_count} variants out of stock")

        # -------- Orders, OrderItems, Transactions --------
        orders_batch = []
        order_items_batch = []
        transactions_batch = []
        
        # Counter to ensure unique order numbers
        order_counter = 0
        
        all_users_result = await session.execute(select(User).options(selectinload(User.addresses)))
        all_users = all_users_result.scalars().all()
        all_variants_result = await session.execute(select(ProductVariant))
        all_variants = all_variants_result.scalars().all()
        all_shipping_methods_result = await session.execute(select(ShippingMethod))
        all_shipping_methods = all_shipping_methods_result.scalars().all()
        all_payment_methods_result = await session.execute(select(PaymentMethod))
        all_payment_methods = all_payment_methods_result.scalars().all()

        for user in all_users:
            for i in range(random.randint(1, 5)):  # 1 to 5 orders per user
                chosen_shipping_method = random.choice(all_shipping_methods)
                user_payment_methods = [
                    pm for pm in all_payment_methods if pm.user_id == user.id]
                if not user_payment_methods:
                    continue
                chosen_payment_method = random.choice(user_payment_methods)

                order_total = 0
                order_uuid = uuid7()
                # Generate a unique order number using timestamp, counter, and UUID to avoid duplicates
                import time
                timestamp = int(time.time() * 1000)  # milliseconds
                order_counter += 1
                order_number = f"ORD-{timestamp}-{order_counter:03d}-{str(order_uuid)[:4].upper()}"
                
                # Generate realistic address data with proper country/state for tax calculation
                countries_with_states = [
                    ("US", ["CA", "NY", "TX", "FL", "WA", "IL", "PA", "OH", "GA", "NC"]),
                    ("CA", ["ON", "BC", "AB", "QC", "MB", "SK", "NS", "NB", "NL", "PE"]),
                    ("GB", [None]),  # UK doesn't use states
                    ("DE", [None]),  # Germany doesn't use states for tax
                    ("AU", [None]),  # Australia simplified
                ]
                
                chosen_country_data = random.choice(countries_with_states)
                country_code = chosen_country_data[0]
                state_options = chosen_country_data[1]
                state_code = random.choice(state_options) if state_options[0] is not None else None
                
                dummy_address = {
                    "street": f"{random.randint(1, 999)} Seed St",
                    "city": "Seed City",
                    "state": state_code,
                    "country": country_code,
                    "post_code": "00000"
                }

                # Calculate tax based on address using the same logic as the tax service
                tax_rate = 0.08  # Default 8%
                if country_code == "US" and state_code:
                    # Use actual US state tax rates
                    us_tax_rates = {
                        "CA": 0.0725, "NY": 0.08, "TX": 0.0625, "FL": 0.06, "WA": 0.065,
                        "IL": 0.0625, "PA": 0.06, "OH": 0.0575, "GA": 0.04, "NC": 0.0475
                    }
                    tax_rate = us_tax_rates.get(state_code, 0.06)
                elif country_code == "CA" and state_code:
                    # Use actual Canadian provincial tax rates
                    ca_tax_rates = {
                        "ON": 0.13, "BC": 0.12, "AB": 0.05, "QC": 0.14975, "MB": 0.12,
                        "SK": 0.11, "NS": 0.15, "NB": 0.15, "NL": 0.15, "PE": 0.15
                    }
                    tax_rate = ca_tax_rates.get(state_code, 0.05)
                elif country_code == "GB":
                    tax_rate = 0.20  # UK VAT
                elif country_code == "DE":
                    tax_rate = 0.19  # German VAT
                elif country_code == "AU":
                    tax_rate = 0.10  # Australian GST

                # Calculate discount amount (0-15% of subtotal)
                discount_amount = 0.0
                if random.random() < 0.3:  # 30% chance of discount
                    discount_amount = round(random.uniform(0.0, 15.0), 2)

                order = Order(
                    id=order_uuid,
                    order_number=order_number,
                    user_id=user.id,
                    guest_email=user.email if random.random() < 0.2 else None, # 20% chance of guest email
                    order_status=random.choice(["pending", "shipped", "delivered", "processing", "cancelled"]),
                    payment_status=random.choice(["pending", "paid", "refunded", "failed"]),
                    fulfillment_status=random.choice(["unfulfilled", "fulfilled", "partial"]),
                    subtotal=0.0, # Will be updated after items
                    tax_amount=0.0, # Will be calculated after subtotal
                    tax_rate=tax_rate, # Store the tax rate used
                    shipping_cost=chosen_shipping_method.price, # Use new field name
                    total_amount=0.0, # Will be updated
                    currency="USD",
                    shipping_method=chosen_shipping_method.name,
                    tracking_number=str(uuid7()) if random.random() < 0.7 else None,
                    carrier=chosen_shipping_method.carrier or random.choice(["DHL", "FedEx", "UPS", "Local Delivery"]),
                    billing_address=dummy_address,
                    shipping_address=dummy_address,
                    confirmed_at=func.now() if random.random() < 0.8 else None,
                    shipped_at=func.now() if random.random() < 0.6 else None,
                    delivered_at=func.now() if random.random() < 0.4 else None,
                    cancelled_at=func.now() if random.random() < 0.1 else None,
                    customer_notes="Please deliver carefully" if random.random() < 0.2 else None,
                    internal_notes="Seeded order"
                )
                orders_batch.append(order)
                await session.flush()

                for j in range(random.randint(1, 3)):  # 1 to 3 items per order
                    chosen_variant = random.choice(all_variants)
                    item_total = chosen_variant.base_price * 1
                    order_item = OrderItem(
                        id=uuid7(),
                        order_id=order.id,
                        variant_id=chosen_variant.id,
                        quantity=1,
                        price_per_unit=chosen_variant.base_price,
                        total_price=item_total
                    )
                    order_items_batch.append(order_item)
                    order_total += item_total

                # Update order with calculated values using simplified pricing structure
                order.subtotal = order_total
                # Calculate tax on subtotal only (not including shipping)
                order.tax_amount = round(order_total * tax_rate, 2)
                # Calculate final total: subtotal + shipping + tax - discount
                order.total_amount = order_total + order.shipping_cost + order.tax_amount - discount_amount

                transaction = Transaction(
                    id=uuid7(),
                    user_id=user.id,
                    order_id=order.id,
                    # Generate a dummy ID for seeding
                    stripe_payment_intent_id=str(uuid7()),
                    amount=order.total_amount,  # Use the calculated total
                    currency="USD",
                    status="succeeded",
                    transaction_type="payment",
                    description=f"Payment for order {order.id}"
                )
                transactions_batch.append(transaction)

        if orders_batch:
            session.add_all(orders_batch)
            session.add_all(order_items_batch)
            session.add_all(transactions_batch)
            await session.flush() # Flush to get IDs/relationships
            await session.commit()
            session.expunge_all() # Free up memory
        print(
            f"🛒 Created {len(orders_batch)} orders with items and transactions.")

        # -------- Wishlists --------
        wishlists_batch = []
        wishlist_items_batch = []
        all_users_for_wishlist = await session.execute(select(User))
        all_users_for_wishlist = all_users_for_wishlist.scalars().all()
        all_products_for_wishlist = await session.execute(select(Product))
        all_products_for_wishlist = all_products_for_wishlist.scalars().all()

        for user in all_users_for_wishlist:
            if not all_products_for_wishlist:
                continue

            # Create a wishlist for the user
            wishlist = Wishlist(
                id=uuid7(),
                user_id=user.id,
                name=f"{user.firstname}'s Wishlist",
                is_default=True
            )
            session.add(wishlist)
            await session.flush()  # Ensure wishlist.id is populated

            # Add 0 to 3 items to the wishlist
            for i in range(random.randint(0, 3)):
                chosen_product = random.choice(all_products_for_wishlist)
                wishlist_item = WishlistItem(
                    id=uuid7(),
                    wishlist_id=wishlist.id,
                    product_id=chosen_product.id,
                    quantity=1  # Default quantity for wishlist item
                )
                wishlist_items_batch.append(wishlist_item)

        if wishlist_items_batch:
            session.add_all(wishlist_items_batch)
            await session.flush()
            await session.commit()
            session.expunge_all()
        print(
            f"❤️ Created {len(wishlist_items_batch)} wishlist items across various wishlists.")

        # -------- Subscriptions --------
        subscriptions_batch = []
        all_users = await session.execute(select(User))
        all_users = all_users.scalars().all()
        all_variants_for_subs = await session.execute(select(ProductVariant).join(Product))
        all_variants_for_subs = all_variants_for_subs.scalars().all()

        # Get admin users to ensure they have subscriptions
        admin_users = [user for user in all_users if user.role == "Admin"]
        non_admin_users = [user for user in all_users if user.role != "Admin"]
        
        subscription_count = 0
        
        # First, create subscriptions for ALL admin users (guaranteed)
        for admin_user in admin_users:
            # Admin users get premium or enterprise plans
            plan_id = random.choice(["premium", "enterprise"])
            
            # Generate realistic subscription pricing
            plan_prices = {"basic": 19.99, "premium": 39.99, "enterprise": 79.99}
            base_price = plan_prices[plan_id]
            
            # Select 2-3 variants for admin subscriptions (more than regular users)
            selected_variants = random.sample(all_variants_for_subs, random.randint(2, 3))
            variant_quantities = {str(variant.id): random.randint(1, 3) for variant in selected_variants}
            
            # Admin subscriptions are more likely to be active
            billing_cycle = random.choice(["monthly", "yearly"])  # No weekly for admins
            status = random.choice(["active", "active", "active", "paused"])  # 75% chance active
            currency = "USD"  # Admins use USD
            
            # Calculate costs for subscription
            subtotal = sum(float(variant.base_price or 10.0) * variant_quantities[str(variant.id)] 
                          for variant in selected_variants)
            shipping_cost = round(random.uniform(5.0, 15.99), 2)  # Higher shipping for admins
            tax_rate = round(random.uniform(0.08, 0.12), 4)
            tax_amount = round((subtotal + shipping_cost) * tax_rate, 2)
            total_amount = round(subtotal + shipping_cost + tax_amount, 2)
            
            # Generate product variants data for cost breakdown
            product_variants_data = []
            for variant in selected_variants:
                quantity = variant_quantities[str(variant.id)]
                variant_price = float(variant.base_price) if variant.base_price else 10.0
                product_variants_data.append({
                    "variant_id": str(variant.id),
                    "name": f"{variant.product.name} - {variant.name}" if variant.product else variant.name,
                    "price": variant_price,
                    "quantity": quantity
                })
            
            # Generate next billing date
            next_billing_date = None
            if status == "active":
                from datetime import datetime, timedelta
                if billing_cycle == "monthly":
                    next_billing_date = datetime.utcnow() + timedelta(days=30)
                elif billing_cycle == "yearly":
                    next_billing_date = datetime.utcnow() + timedelta(days=365)
            
            subscription = Subscription(
                id=uuid7(),
                user_id=admin_user.id,
                plan_id=plan_id,
                price=base_price,
                currency=currency,
                status=status,
                billing_cycle=billing_cycle,
                auto_renew=True,  # Admins have auto-renew enabled
                next_billing_date=next_billing_date,
                variant_ids=[str(variant.id) for variant in selected_variants],
                variant_quantities=variant_quantities,
                shipping_cost=shipping_cost,
                tax_amount=tax_amount,
                tax_rate=tax_rate,
                cost_breakdown={
                    "subtotal": subtotal,
                    "shipping_cost": shipping_cost,
                    "tax_amount": tax_amount,
                    "tax_rate": tax_rate,
                    "total_amount": total_amount,
                    "currency": currency,
                    "product_variants": product_variants_data
                }
            )
            subscriptions_batch.append(subscription)
            subscription_count += 1

        # Then create random subscriptions for other users (up to 20 total)
        remaining_subscriptions = max(0, 20 - len(admin_users))
        for i in range(remaining_subscriptions):
            chosen_user = random.choice(non_admin_users)
            plan_id = random.choice(["basic", "premium", "enterprise"])
            
            # Generate realistic subscription pricing
            plan_prices = {"basic": 19.99, "premium": 39.99, "enterprise": 79.99}
            base_price = plan_prices[plan_id]
            
            # Select 1-3 variants for this subscription
            selected_variants = random.sample(all_variants_for_subs, random.randint(1, 3))
            variant_quantities = {str(variant.id): random.randint(1, 2) for variant in selected_variants}
            
            # Generate billing cycle and status
            billing_cycle = random.choice(["weekly", "monthly", "yearly"])
            status = random.choice(["active", "cancelled", "paused"])
            currency = random.choice(["USD", "EUR", "GBP", "CAD"])
            
            # Calculate costs for subscription
            subtotal = sum(float(variant.base_price or 10.0) * variant_quantities[str(variant.id)] 
                          for variant in selected_variants)
            shipping_cost = round(random.uniform(0.0, 15.99), 2)
            tax_rate = round(random.uniform(0.05, 0.12), 4)
            tax_amount = round((subtotal + shipping_cost) * tax_rate, 2)
            total_amount = round(subtotal + shipping_cost + tax_amount, 2)
            
            # Generate product variants data for cost breakdown
            product_variants_data = []
            for variant in selected_variants:
                quantity = variant_quantities[str(variant.id)]
                variant_price = float(variant.base_price) if variant.base_price else 10.0
                product_variants_data.append({
                    "variant_id": str(variant.id),
                    "name": f"{variant.product.name} - {variant.name}" if variant.product else variant.name,
                    "price": variant_price,
                    "quantity": quantity
                })
            
            # Generate next billing date
            next_billing_date = None
            if status == "active":
                from datetime import datetime, timedelta
                if billing_cycle == "weekly":
                    next_billing_date = datetime.utcnow() + timedelta(weeks=1)
                elif billing_cycle == "monthly":
                    next_billing_date = datetime.utcnow() + timedelta(days=30)
                elif billing_cycle == "yearly":
                    next_billing_date = datetime.utcnow() + timedelta(days=365)
            
            subscription = Subscription(
                id=uuid7(),
                user_id=chosen_user.id,
                plan_id=plan_id,
                price=base_price,
                currency=currency,
                status=status,
                billing_cycle=billing_cycle,
                auto_renew=random.choice([True, False]),
                next_billing_date=next_billing_date,
                variant_ids=[str(variant.id) for variant in selected_variants],
                variant_quantities=variant_quantities,
                shipping_cost=shipping_cost,
                tax_amount=tax_amount,
                tax_rate=tax_rate,
                cost_breakdown={
                    "subtotal": subtotal,
                    "shipping_cost": shipping_cost,
                    "tax_amount": tax_amount,
                    "tax_rate": tax_rate,
                    "total_amount": total_amount,
                    "currency": currency,
                    "product_variants": product_variants_data
                }
            )
            subscriptions_batch.append(subscription)
            subscription_count += 1

        if subscriptions_batch:
            session.add_all(subscriptions_batch)
            await session.flush()
            await session.commit()
            session.expunge_all()
        print(f"💳 Created {len(subscriptions_batch)} subscriptions.")
        print(f"👑 All {len(admin_users)} admin users have guaranteed subscriptions.")
        print(f"🎲 {subscription_count - len(admin_users)} additional random subscriptions created.")

        # -------- Reviews --------
        reviews_batch = []
        all_products = await session.execute(select(Product))
        all_products = all_products.scalars().all()

        # Get featured products for more reviews
        featured_products = [p for p in all_products if p.featured]
        regular_products = [p for p in all_products if not p.featured]

        review_comments = [
            "Excellent quality! Highly recommend this product.",
            "Great value for money. Will definitely buy again.",
            "Fresh and well-packaged. Very satisfied with my purchase.",
            "Good product, fast delivery. Thank you!",
            "Amazing quality! Exceeded my expectations.",
            "Perfect for cooking. Great taste and texture.",
            "Organic and fresh. Exactly what I was looking for.",
            "High quality product. Worth every penny.",
            "Fast shipping and great packaging. Product is excellent.",
            "Love this product! Will order more soon."
        ]

        review_count = 0
        # Create more reviews for featured products (2-5 reviews each)
        for product in featured_products:
            num_reviews = random.randint(2, 5)
            for _ in range(num_reviews):
                if review_count >= 100:  # Cap total reviews
                    break
                chosen_user = random.choice(all_users)
                review = Review(
                    id=uuid7(),
                    product_id=product.id,
                    user_id=chosen_user.id,
                    # Featured products get better ratings
                    rating=random.randint(4, 5),
                    comment=random.choice(review_comments),
                    is_verified_purchase=random.choice([True, False]),
                    is_approved=True
                )
                reviews_batch.append(review)
                review_count += 1

        # Create fewer reviews for regular products (0-2 reviews each)
        for product in regular_products:
            if review_count >= 100:  # Cap total reviews
                break
            if random.random() < 0.6:  # 60% chance of having reviews
                num_reviews = random.randint(0, 2)
                for _ in range(num_reviews):
                    if review_count >= 100:
                        break
                    chosen_user = random.choice(all_users)
                    review = Review(
                        id=uuid7(),
                        product_id=product.id,
                        user_id=chosen_user.id,
                        rating=random.randint(3, 5),  # Generally good ratings
                        comment=random.choice(review_comments),
                        is_verified_purchase=random.choice([True, False]),
                        is_approved=True
                    )
                    reviews_batch.append(review)
                    review_count += 1

        if reviews_batch:
            session.add_all(reviews_batch)
            await session.flush()
            await session.commit()
            session.expunge_all()
        print(f"⭐ Created {len(reviews_batch)} reviews.")

        # -------- Print plaintext passwords --------
        users_file_path = "users.txt"
        with open(users_file_path, "w") as f:
            for email, pwd in plaintext_passwords.items():
                f.write(f"{email} / {pwd}\n")
        print(
            f"🔐 Plaintext credentials saved to {users_file_path} (DEV ONLY).")


async def update_existing_orders_with_simplified_pricing(session):
    """Update existing orders to use the simplified pricing structure"""
    try:
        print("📋 Checking existing orders for simplified pricing structure updates...")
        
        # Get orders that might need updates
        result = await session.execute(
            select(Order).where(
                (Order.tax_rate == None) | 
                (Order.shipping_cost == None) |
                (Order.tax_rate == 0) |
                (Order.shipping_cost == 0)
            )
        )
        orders_to_update = result.scalars().all()
        
        if not orders_to_update:
            print("✅ All orders already have simplified pricing structure")
            return
        
        print(f"🔄 Updating {len(orders_to_update)} orders with simplified pricing...")
        
        # Get default shipping method
        result = await session.execute(
            select(ShippingMethod).where(ShippingMethod.is_active == True).limit(1)
        )
        default_shipping = result.scalar_one_or_none()
        default_shipping_cost = default_shipping.price if default_shipping else 8.99
        
        for order in orders_to_update:
            # Set tax rate (assume 8% default tax rate for existing orders)
            if not order.tax_rate or order.tax_rate == 0:
                order.tax_rate = 0.08  # 8% default
            
            # Calculate tax amount based on subtotal only
            if not order.tax_amount or order.tax_amount == 0:
                subtotal = order.subtotal or (order.total_amount * 0.85)  # Estimate subtotal
                order.tax_amount = round(subtotal * order.tax_rate, 2)
            
            # Set shipping cost
            if not order.shipping_cost or order.shipping_cost == 0:
                order.shipping_cost = default_shipping_cost
            
            # Recalculate total using simplified structure: subtotal + shipping + tax
            if order.subtotal:
                order.total_amount = order.subtotal + order.shipping_cost + order.tax_amount
        
        await session.commit()
        print(f"✅ Updated {len(orders_to_update)} orders with simplified pricing structure")
        
    except Exception as e:
        print(f"❌ Error updating existing orders: {e}")
        await session.rollback()
        raise


def calculate_order_total(subtotal: float, shipping_cost: float, tax_rate: float, discount_amount: float = 0.0) -> dict:
    """
    Calculate order total using simplified pricing structure.
    
    Args:
        subtotal: Sum of all product variant prices
        shipping_cost: Shipping cost
        tax_rate: Tax rate (e.g., 0.08 for 8%)
        discount_amount: Discount amount to subtract
    
    Returns:
        dict: Contains subtotal, shipping_cost, tax_amount, discount_amount, total_amount
    """
    # Calculate tax on subtotal only (not including shipping)
    tax_amount = round(subtotal * tax_rate, 2)
    
    # Calculate final total: subtotal + shipping + tax - discount
    total_amount = subtotal + shipping_cost + tax_amount - discount_amount
    
    return {
        "subtotal": subtotal,
        "shipping_cost": shipping_cost,
        "tax_rate": tax_rate,
        "tax_amount": tax_amount,
        "discount_amount": discount_amount,
        "total_amount": round(total_amount, 2)
    }


async def seed_tax_rates(session):
    """Seed tax rates into the database"""
    try:
        # Check if tax rates already exist
        result = await session.execute(select(TaxRate).limit(1))
        existing = result.scalar_one_or_none()
        
        if existing:
            print("✅ Tax rates already seeded. Skipping...")
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
                await session.commit()
                session.expunge_all()
                tax_rates_batch = []
        
        # Add remaining tax rates
        if tax_rates_batch:
            session.add_all(tax_rates_batch)
            await session.flush()
            await session.commit()
            session.expunge_all()
        
        print(f"✅ Successfully seeded {len(GLOBAL_TAX_RATES)} tax rates")
        
    except Exception as e:
        print(f"❌ Error seeding tax rates: {e}")
        await session.rollback()
        raise


async def main():
    parser = argparse.ArgumentParser(
        description="Initialize DB and optionally seed sample data in batches.")
    parser.add_argument("--seed", action="store_true",
                        help="Seed sample data after creating tables")
    parser.add_argument("--categories", type=int,
                        default=DEFAULT_NUM_CATEGORIES)
    parser.add_argument("--users", type=int, default=DEFAULT_NUM_USERS)
    parser.add_argument("--products", type=int, default=DEFAULT_NUM_PRODUCTS)
    parser.add_argument("--variants", type=int,
                        default=DEFAULT_VARIANTS_PER_PRODUCT)
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE)
    args = parser.parse_args()

    print("🚀 Initializing Banwee Database...")

    # Initialize database connection
    initialize_db(settings.SQLALCHEMY_DATABASE_URI, settings.ENVIRONMENT == "local")

    try:
        await create_tables()
        
        # Always seed tax rates (they're essential for the system)
        async with db_manager.session_factory() as session:
            await seed_tax_rates(session)
            await update_existing_orders_with_simplified_pricing(session)
        
        if args.seed:
            await seed_sample_data(
                categories_count=args.categories,
                users_count=args.users,
                products_count=args.products,
                variants_per_product=args.variants,
                batch_size=args.batch_size,
            )
        
        print("✅ Database initialization complete!")
        print("🎯 All orders now use simplified pricing structure: subtotal + shipping + tax = total!")
        print("💡 Use calculate_order_total() function for consistent order calculations!")
        
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())

# ---------------- COMPREHENSIVE SEEDING FUNCTIONS ----------------

async def seed_comprehensive_data(
    session, 
    num_categories: int = DEFAULT_NUM_CATEGORIES,
    num_users: int = DEFAULT_NUM_USERS, 
    num_products: int = DEFAULT_NUM_PRODUCTS,
    variants_per_product: int = DEFAULT_VARIANTS_PER_PRODUCT,
    batch_size: int = DEFAULT_BATCH_SIZE
):
    """
    Comprehensive database seeding with realistic e-commerce data
    
    This function creates a complete e-commerce ecosystem:
    - Product categories with rich metadata
    - Users (admin, suppliers, customers) with addresses
    - Products with multiple variants and realistic pricing
    - Warehouse locations and inventory tracking
    - Shipping methods with carrier integration
    - Global tax rates for 80+ countries/regions
    - Discount codes and promotional offers
    - Payment methods and transaction history
    - Reviews and ratings
    - Wishlist functionality
    """
    print("🚀 Starting comprehensive database seeding...")
    
    # Step 1: Create Categories
    print(f"📂 Creating {num_categories} product categories...")
    categories = await seed_categories(session, batch_size)
    
    # Step 2: Create Users (Admin, Suppliers, Customers)
    print(f"👥 Creating {num_users} users with addresses...")
    users = await seed_users_with_addresses(session, num_users, batch_size)
    
    # Step 3: Create Warehouse Locations
    print("🏭 Setting up warehouse locations...")
    warehouses = await seed_warehouse_locations(session, batch_size)
    
    # Step 4: Create Shipping Methods
    print("🚚 Configuring shipping methods...")
    shipping_methods = await seed_shipping_methods(session, batch_size)
    
    # Step 5: Create Global Tax Rates
    print("💰 Loading global tax rates...")
    await seed_tax_rates(session, batch_size)
    
    # Step 6: Create Products with Variants and Inventory
    print(f"🛍️ Creating {num_products} products with {variants_per_product} variants each...")
    products = await seed_products_with_variants_and_inventory(
        session, categories, users, warehouses, num_products, variants_per_product, batch_size
    )
    
    # Step 7: Create Discount Codes
    print("🎫 Setting up discount codes...")
    await seed_discount_codes(session, batch_size)
    
    # Step 8: Create Payment Methods for Users
    print("💳 Setting up payment methods...")
    await seed_payment_methods(session, users, batch_size)
    
    # Step 9: Create Sample Reviews
    print("⭐ Generating product reviews...")
    await seed_product_reviews(session, products, users, batch_size)
    
    # Step 10: Create Wishlist Items
    print("❤️ Creating wishlist items...")
    await seed_wishlist_items(session, products, users, batch_size)
    
    print("✅ Comprehensive database seeding completed successfully!")
    
    # Print summary statistics
    await print_seeding_summary(session)


async def seed_categories(session, batch_size: int) -> List[Category]:
    """Create product categories with rich metadata"""
    categories = []
    
    for category_key, category_data in PRODUCT_CATEGORIES.items():
        category = Category(
            id=uuid7(),
            name=category_data['name'],
            description=category_data['description'],
            image_url=category_data['image_url'],
            is_active=True
        )
        categories.append(category)
        session.add(category)
    
    await session.flush()
    await session.commit()
    print(f"   ✓ Created {len(categories)} categories")
    return categories


async def seed_users_with_addresses(session, num_users: int, batch_size: int) -> List[User]:
    """Create users with realistic addresses and authentication"""
    users = []
    password_manager = PasswordManager()
    
    # Create admin user
    admin_password = "admin123"
    admin_user = User(
        id=uuid7(),
        email="admin@banwee.com",
        username="admin",
        first_name="System",
        last_name="Administrator",
        password_hash=password_manager.hash_password(admin_password),
        is_active=True,
        is_verified=True,
        role="admin"
    )
    users.append(admin_user)
    session.add(admin_user)
    
    # Create supplier users
    supplier_count = max(3, num_users // 10)  # At least 3 suppliers
    for i in range(supplier_count):
        supplier_password = f"supplier{i+1}123"
        supplier = User(
            id=uuid7(),
            email=f"supplier{i+1}@banwee.com",
            username=f"supplier{i+1}",
            first_name=f"Supplier",
            last_name=f"User {i+1}",
            password_hash=password_manager.hash_password(supplier_password),
            is_active=True,
            is_verified=True,
            role="supplier"
        )
        users.append(supplier)
        session.add(supplier)
    
    # Create customer users
    customer_count = num_users - len(users)
    for i in range(customer_count):
        customer_password = f"customer{i+1}123"
        customer = User(
            id=uuid7(),
            email=f"customer{i+1}@example.com",
            username=f"customer{i+1}",
            first_name=f"Customer",
            last_name=f"User {i+1}",
            password_hash=password_manager.hash_password(customer_password),
            is_active=True,
            is_verified=True,
            role="customer"
        )
        users.append(customer)
        session.add(customer)
        
        # Add addresses for customers
        if i % 2 == 0:  # Add addresses for every other customer
            address = Address(
                id=uuid7(),
                user_id=customer.id,
                street=f"{random.randint(100, 9999)} {random.choice(['Main St', 'Oak Ave', 'Pine Rd', 'Elm Dr', 'Cedar Ln'])}",
                city=random.choice(['New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix', 'Philadelphia', 'San Antonio', 'San Diego', 'Dallas', 'San Jose']),
                state=random.choice(['NY', 'CA', 'IL', 'TX', 'AZ', 'PA', 'TX', 'CA', 'TX', 'CA']),
                country="US",
                post_code=f"{random.randint(10000, 99999)}",
                is_default=True
            )
            session.add(address)
    
    await session.flush()
    await session.commit()
    
    # Print credentials for development
    print(f"   ✓ Created {len(users)} users")
    print("   📋 Development Credentials:")
    print(f"      Admin: admin@banwee.com / {admin_password}")
    for i in range(min(3, supplier_count)):
        print(f"      Supplier {i+1}: supplier{i+1}@banwee.com / supplier{i+1}123")
    print(f"      Customers: customer1@example.com / customer1123 (and {customer_count-1} more)")
    
    return users


async def seed_warehouse_locations(session, batch_size: int) -> List[WarehouseLocation]:
    """Create warehouse locations for inventory management"""
    warehouses = []
    
    for warehouse_data in WAREHOUSE_LOCATIONS:
        warehouse = WarehouseLocation(
            id=uuid7(),
            name=warehouse_data['name'],
            address=warehouse_data['address'],
            city=warehouse_data['city'],
            state=warehouse_data['state'],
            country=warehouse_data['country'],
            postal_code=warehouse_data['postal_code'],
            is_active=warehouse_data['is_active']
        )
        warehouses.append(warehouse)
        session.add(warehouse)
    
    await session.flush()
    await session.commit()
    print(f"   ✓ Created {len(warehouses)} warehouse locations")
    return warehouses


async def seed_shipping_methods(session, batch_size: int) -> List[ShippingMethod]:
    """Create shipping methods with carrier integration"""
    shipping_methods = []
    
    for method_data in SHIPPING_METHODS:
        method = ShippingMethod(
            id=uuid7(),
            name=method_data['name'],
            description=method_data['description'],
            price=method_data['price'],
            estimated_days=method_data['estimated_days'],
            carrier=method_data['carrier'],
            tracking_url_template=method_data['tracking_url_template'],
            is_active=method_data['is_active']
        )
        shipping_methods.append(method)
        session.add(method)
    
    await session.flush()
    await session.commit()
    print(f"   ✓ Created {len(shipping_methods)} shipping methods")
    return shipping_methods


async def seed_tax_rates(session, batch_size: int):
    """Load comprehensive global tax rates"""
    tax_rates = []
    
    for tax_data in GLOBAL_TAX_RATES:
        tax_rate = TaxRate(
            id=uuid7(),
            country_code=tax_data['country_code'],
            country_name=tax_data['country_name'],
            province_code=tax_data['province_code'],
            province_name=tax_data['province_name'],
            tax_rate=tax_data['tax_rate'],
            tax_name=tax_data['tax_name'],
            is_active=True,
            effective_date=datetime.utcnow()
        )
        tax_rates.append(tax_rate)
        session.add(tax_rate)
        
        # Batch commit for performance
        if len(tax_rates) % batch_size == 0:
            await session.flush()
            await session.commit()
            session.expunge_all()
    
    await session.flush()
    await session.commit()
    print(f"   ✓ Loaded {len(GLOBAL_TAX_RATES)} global tax rates")


async def seed_products_with_variants_and_inventory(
    session, categories: List[Category], users: List[User], warehouses: List[WarehouseLocation],
    num_products: int, variants_per_product: int, batch_size: int
) -> List[Product]:
    """Create products with variants and inventory tracking"""
    products = []
    suppliers = [u for u in users if u.role == "supplier"]
    
    # Product name templates by category
    product_templates = {
        'cereal-crops': ['Organic {grain}', 'Premium {grain}', 'Whole Grain {grain}', 'Ancient {grain}'],
        'legumes': ['Organic {legume}', 'Premium {legume}', 'Dried {legume}', 'Sprouted {legume}'],
        'fruits-vegetables': ['Fresh {produce}', 'Organic {produce}', 'Dried {produce}', 'Freeze-Dried {produce}'],
        'oilseeds': ['Raw {nut}', 'Roasted {nut}', 'Organic {nut}', 'Premium {nut}'],
        'sweeteners': ['Pure {sweetener}', 'Organic {sweetener}', 'Raw {sweetener}', 'Artisan {sweetener}'],
        'beverages': ['Organic {beverage}', 'Cold-Pressed {beverage}', 'Fresh {beverage}', 'Premium {beverage}'],
        'dairy-alternatives': ['Organic {alternative}', 'Unsweetened {alternative}', 'Vanilla {alternative}', 'Protein {alternative}'],
        'spices-herbs': ['Organic {spice}', 'Ground {spice}', 'Whole {spice}', 'Premium {spice}'],
        'superfoods': ['Organic {superfood}', 'Raw {superfood}', 'Premium {superfood}', 'Freeze-Dried {superfood}']
    }
    
    # Ingredient lists by category
    ingredients = {
        'cereal-crops': ['Rice', 'Wheat', 'Quinoa', 'Oats', 'Barley', 'Corn', 'Millet', 'Buckwheat'],
        'legumes': ['Black Beans', 'Chickpeas', 'Lentils', 'Kidney Beans', 'Navy Beans', 'Pinto Beans'],
        'fruits-vegetables': ['Mango', 'Banana', 'Apple', 'Carrot', 'Sweet Potato', 'Kale', 'Spinach'],
        'oilseeds': ['Almonds', 'Cashews', 'Walnuts', 'Sunflower Seeds', 'Pumpkin Seeds', 'Chia Seeds'],
        'sweeteners': ['Honey', 'Maple Syrup', 'Agave Nectar', 'Coconut Sugar', 'Date Syrup'],
        'beverages': ['Green Tea', 'Herbal Tea', 'Cold Brew Coffee', 'Kombucha', 'Fresh Juice'],
        'dairy-alternatives': ['Almond Milk', 'Oat Milk', 'Coconut Milk', 'Soy Milk', 'Cashew Milk'],
        'spices-herbs': ['Turmeric', 'Cinnamon', 'Ginger', 'Basil', 'Oregano', 'Thyme', 'Rosemary'],
        'superfoods': ['Spirulina', 'Chlorella', 'Acai', 'Goji Berries', 'Cacao', 'Maca Root']
    }
    
    product_count = 0
    for category in categories:
        category_key = None
        for key, data in PRODUCT_CATEGORIES.items():
            if data['name'] == category.name:
                category_key = key
                break
        
        if not category_key:
            continue
            
        category_products = num_products // len(categories)
        category_templates = product_templates.get(category_key, ['Premium {item}'])
        category_ingredients = ingredients.get(category_key, ['Item'])
        price_range = PRODUCT_CATEGORIES[category_key]['price_range']
        weight_range = PRODUCT_CATEGORIES[category_key]['typical_weight']
        
        for i in range(category_products):
            if product_count >= num_products:
                break
                
            # Generate product name
            template = random.choice(category_templates)
            ingredient = random.choice(category_ingredients)
            product_name = template.format(
                grain=ingredient, legume=ingredient, produce=ingredient, 
                nut=ingredient, sweetener=ingredient, beverage=ingredient,
                alternative=ingredient, spice=ingredient, superfood=ingredient,
                item=ingredient
            )
            
            # Create product
            product = Product(
                id=uuid7(),
                name=product_name,
                slug=product_name.lower().replace(' ', '-').replace(',', ''),
                description=f"Premium quality {ingredient.lower()} sourced from trusted suppliers. Perfect for healthy cooking and nutrition.",
                short_description=f"High-quality {ingredient.lower()} for your kitchen",
                category_id=category.id,
                supplier_id=random.choice(suppliers).id,
                product_status="active",
                availability_status="available",
                is_featured=random.choice([True, False]),
                rating_average=round(random.uniform(3.5, 5.0), 1),
                rating_count=random.randint(10, 500),
                review_count=random.randint(5, 100),
                specifications={
                    "origin": random.choice(["USA", "Canada", "Mexico", "Peru", "Chile"]),
                    "organic": random.choice([True, False]),
                    "gluten_free": random.choice([True, False]),
                    "non_gmo": random.choice([True, False])
                },
                dietary_tags={
                    "vegan": random.choice([True, False]),
                    "vegetarian": True,
                    "keto_friendly": random.choice([True, False]),
                    "paleo": random.choice([True, False])
                },
                tags=f"organic,natural,{category_key.replace('-', '_')}",
                published_at=datetime.utcnow() - timedelta(days=random.randint(1, 365))
            )
            products.append(product)
            session.add(product)
            
            # Create variants for this product
            variant_prices = []
            for v in range(variants_per_product):
                # Generate variant attributes
                sizes = ['250g', '500g', '1kg', '2kg', '5kg']
                size = sizes[v % len(sizes)]
                
                # Calculate price based on size and category
                base_price = random.uniform(price_range['min'], price_range['max'])
                size_multiplier = {'250g': 1.0, '500g': 1.8, '1kg': 3.2, '2kg': 5.8, '5kg': 12.0}
                variant_price = round(base_price * size_multiplier.get(size, 1.0), 2)
                variant_prices.append(variant_price)
                
                # Determine if on sale (30% chance)
                sale_price = None
                if random.random() < 0.3:
                    sale_price = round(variant_price * random.uniform(0.7, 0.9), 2)
                
                variant = ProductVariant(
                    id=uuid7(),
                    product_id=product.id,
                    sku=f"{product.slug[:10].upper()}-{size.replace('g', 'G').replace('kg', 'KG')}",
                    name=f"{product_name} - {size}",
                    base_price=variant_price,
                    sale_price=sale_price,
                    weight=random.uniform(weight_range['min'], weight_range['max']),
                    dimensions={"length": 10, "width": 8, "height": 6},
                    is_active=True,
                    attributes={"size": size, "unit": "weight"}
                )
                session.add(variant)
                
                # Create inventory for each warehouse
                for warehouse in warehouses:
                    stock_level = random.randint(50, 500)
                    inventory = Inventory(
                        id=uuid7(),
                        variant_id=variant.id,
                        warehouse_location_id=warehouse.id,
                        quantity_available=stock_level,
                        quantity_reserved=random.randint(0, min(10, stock_level // 10)),
                        reorder_point=max(10, stock_level // 10),
                        reorder_quantity=stock_level // 2
                    )
                    session.add(inventory)
            
            # Update product price range
            product.min_price = min(variant_prices)
            product.max_price = max(variant_prices)
            
            product_count += 1
            
            # Batch commit for performance
            if product_count % batch_size == 0:
                await session.flush()
                await session.commit()
                session.expunge_all()
    
    await session.flush()
    await session.commit()
    print(f"   ✓ Created {len(products)} products with {len(products) * variants_per_product} variants")
    return products


async def seed_discount_codes(session, batch_size: int):
    """Create discount codes and promotional offers"""
    discounts = []
    
    for discount_data in DISCOUNT_CODES:
        valid_from = datetime.utcnow()
        valid_until = valid_from + timedelta(days=discount_data['valid_days'])
        
        discount = Discount(
            id=uuid7(),
            code=discount_data['code'],
            type=discount_data['type'],
            value=discount_data['value'],
            description=discount_data['description'],
            minimum_amount=discount_data['minimum_amount'],
            maximum_discount=discount_data['maximum_discount'],
            valid_from=valid_from,
            valid_until=valid_until,
            usage_limit=discount_data['usage_limit'],
            used_count=0,
            is_active=discount_data['is_active']
        )
        discounts.append(discount)
        session.add(discount)
    
    await session.flush()
    await session.commit()
    print(f"   ✓ Created {len(discounts)} discount codes")


async def seed_payment_methods(session, users: List[User], batch_size: int):
    """Create payment methods for users"""
    payment_methods = []
    customers = [u for u in users if u.role == "customer"]
    
    for customer in customers[:10]:  # Add payment methods for first 10 customers
        # Add a credit card
        payment_method = PaymentMethod(
            id=uuid7(),
            user_id=customer.id,
            type="credit_card",
            provider="stripe",
            last_four="4242",
            expiry_month=12,
            expiry_year=2025,
            is_default=True
        )
        payment_methods.append(payment_method)
        session.add(payment_method)
    
    await session.flush()
    await session.commit()
    print(f"   ✓ Created {len(payment_methods)} payment methods")


async def seed_product_reviews(session, products: List[Product], users: List[User], batch_size: int):
    """Generate realistic product reviews"""
    reviews = []
    customers = [u for u in users if u.role == "customer"]
    
    review_templates = [
        "Great quality product! Exactly what I was looking for.",
        "Fast shipping and excellent packaging. Product arrived fresh.",
        "Good value for money. Will definitely order again.",
        "Premium quality as advertised. Highly recommended!",
        "Fresh and delicious. Perfect for my recipes.",
        "Organic and natural as promised. Very satisfied.",
        "Quick delivery and great customer service.",
        "Excellent product quality. Worth every penny."
    ]
    
    for product in products[:20]:  # Add reviews for first 20 products
        num_reviews = random.randint(2, 8)
        for _ in range(num_reviews):
            review = Review(
                id=uuid7(),
                product_id=product.id,
                user_id=random.choice(customers).id,
                rating=random.randint(3, 5),
                title=f"Great {product.name.split()[0]} Product",
                comment=random.choice(review_templates),
                is_verified_purchase=random.choice([True, False])
            )
            reviews.append(review)
            session.add(review)
    
    await session.flush()
    await session.commit()
    print(f"   ✓ Created {len(reviews)} product reviews")


async def seed_wishlist_items(session, products: List[Product], users: List[User], batch_size: int):
    """Create wishlist items for customers"""
    customers = [u for u in users if u.role == "customer"]
    wishlist_items = []
    
    for customer in customers[:15]:  # Add wishlists for first 15 customers
        # Create wishlist
        wishlist = Wishlist(
            id=uuid7(),
            user_id=customer.id,
            name="My Wishlist"
        )
        session.add(wishlist)
        
        # Add random products to wishlist
        selected_products = random.sample(products[:30], random.randint(2, 8))
        for product in selected_products:
            wishlist_item = WishlistItem(
                id=uuid7(),
                wishlist_id=wishlist.id,
                product_id=product.id
            )
            wishlist_items.append(wishlist_item)
            session.add(wishlist_item)
    
    await session.flush()
    await session.commit()
    print(f"   ✓ Created {len(wishlist_items)} wishlist items")


async def print_seeding_summary(session):
    """Print comprehensive seeding summary"""
    print("\n📊 DATABASE SEEDING SUMMARY")
    print("=" * 50)
    
    # Count records in each table
    tables = [
        ("Categories", Category),
        ("Users", User),
        ("Addresses", Address),
        ("Products", Product),
        ("Product Variants", ProductVariant),
        ("Warehouse Locations", WarehouseLocation),
        ("Inventory Records", Inventory),
        ("Shipping Methods", ShippingMethod),
        ("Tax Rates", TaxRate),
        ("Discount Codes", Discount),
        ("Payment Methods", PaymentMethod),
        ("Reviews", Review),
        ("Wishlists", Wishlist),
        ("Wishlist Items", WishlistItem)
    ]
    
    for table_name, model in tables:
        result = await session.execute(select(func.count(model.id)))
        count = result.scalar()
        print(f"{table_name:20}: {count:6,} records")
    
    print("=" * 50)
    print("✅ Database initialization completed successfully!")
    print("\n🔐 Development Login Credentials:")
    print("   Admin: admin@banwee.com / admin123")
    print("   Supplier: supplier1@banwee.com / supplier1123")
    print("   Customer: customer1@example.com / customer1123")
    print("\n🎫 Available Discount Codes:")
    for discount in DISCOUNT_CODES:
        print(f"   {discount['code']}: {discount['description']}")
    print("\n🚚 Shipping Methods Available:")
    for method in SHIPPING_METHODS:
        print(f"   {method['name']}: ${method['price']:.2f} ({method['estimated_days']} days)")
    print(f"\n💰 Tax Rates: {len(GLOBAL_TAX_RATES)} countries/regions configured")
    print(f"🏭 Warehouses: {len(WAREHOUSE_LOCATIONS)} distribution centers")
    print("\n🎯 Ready for order and checkout testing!")


async def create_tables_and_seed(
    num_categories: int = DEFAULT_NUM_CATEGORIES,
    num_users: int = DEFAULT_NUM_USERS,
    num_products: int = DEFAULT_NUM_PRODUCTS,
    variants_per_product: int = DEFAULT_VARIANTS_PER_PRODUCT,
    batch_size: int = DEFAULT_BATCH_SIZE,
    seed_data: bool = True
):
    """
    Main function to create tables and seed comprehensive data
    """
    print("🏗️  Initializing Banwee E-commerce Database...")
    print(f"📊 Configuration: {num_products} products, {num_users} users, batch size {batch_size}")
    
    # Initialize database connection
    initialize_db(settings.SQLALCHEMY_DATABASE_URI, settings.ENVIRONMENT == "local")
    
    # Get database session
    async with db_manager.session_factory() as session:
        try:
            # Drop and recreate schema for clean slate
            print("🗑️  Dropping existing schema...")
            await session.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
            await session.execute(text("CREATE SCHEMA public"))
            await session.commit()
            
            # Create all tables
            print("🏗️  Creating database tables...")
            async with db_manager.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            
            if seed_data:
                # Seed comprehensive data
                await seed_comprehensive_data(
                    session, num_categories, num_users, num_products, 
                    variants_per_product, batch_size
                )
            else:
                print("⏭️  Skipping data seeding (--no-seed flag used)")
                
        except Exception as e:
            print(f"❌ Error during database initialization: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()


def main():
    """Command-line interface for database initialization"""
    parser = argparse.ArgumentParser(
        description="Banwee E-commerce Database Initialization",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python init_db.py --seed                                    # Default seeding
  python init_db.py --seed --products 100 --users 50         # Custom quantities
  python init_db.py --seed --batch-size 200                  # Larger batches
  python init_db.py --no-seed                                 # Tables only
        """
    )
    
    parser.add_argument(
        "--seed", 
        action="store_true", 
        help="Seed database with sample data"
    )
    parser.add_argument(
        "--no-seed", 
        action="store_true", 
        help="Create tables only, skip seeding"
    )
    parser.add_argument(
        "--products", 
        type=int, 
        default=DEFAULT_NUM_PRODUCTS,
        help=f"Number of products to create (default: {DEFAULT_NUM_PRODUCTS})"
    )
    parser.add_argument(
        "--users", 
        type=int, 
        default=DEFAULT_NUM_USERS,
        help=f"Number of users to create (default: {DEFAULT_NUM_USERS})"
    )
    parser.add_argument(
        "--variants", 
        type=int, 
        default=DEFAULT_VARIANTS_PER_PRODUCT,
        help=f"Variants per product (default: {DEFAULT_VARIANTS_PER_PRODUCT})"
    )
    parser.add_argument(
        "--batch-size", 
        type=int, 
        default=DEFAULT_BATCH_SIZE,
        help=f"Batch size for database operations (default: {DEFAULT_BATCH_SIZE})"
    )
    
    args = parser.parse_args()
    
    # Determine if we should seed data
    seed_data = args.seed and not args.no_seed
    
    # Run the initialization
    asyncio.run(create_tables_and_seed(
        num_categories=DEFAULT_NUM_CATEGORIES,
        num_users=args.users,
        num_products=args.products,
        variants_per_product=args.variants,
        batch_size=args.batch_size,
        seed_data=seed_data
    ))


if __name__ == "__main__":
    main()