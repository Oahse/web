#!/usr/bin/env python3
"""
Database initialization + batched seeding script for Banwee API.

- Creates tables (drops then creates) in PostgreSQL.
- Optionally seeds with sample data in configurable batch sizes (default batch_size=50).
- Prints plaintext passwords for test accounts (ONLY FOR LOCAL/DEV USE).
"""

import asyncio
import argparse
import random
from typing import List

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import select, func, text
from sqlalchemy.orm import selectinload
from core.database import db_manager, initialize_db
from core.config import settings
from core.utils.encryption import PasswordManager
from core.utils.uuid_utils import uuid7
from core.database import Base
from models.user import User, Address
from models.product import Product, ProductVariant, ProductImage, Category
from models.orders import Order, OrderItem
from models.subscriptions import Subscription
from models.review import Review
from models.payments import PaymentMethod, Transaction
from models.promocode import Promocode
from models.shipping import ShippingMethod
from models.wishlist import Wishlist, WishlistItem

from models.inventories import WarehouseLocation, Inventory  # Added inventory imports
from models.refunds import Refund, RefundItem  # Added refund imports
from models.tax_rates import TaxRate  # Added tax rates import

# ---------------- Config ----------------
FILTER_CATEGORIES = {
    'cereal-crops': {
        'name': 'Cereal Crops',
        'image_url': 'https://images.unsplash.com/photo-1474979266404-7eaacbcd87c5?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80',
        'keywords': ['cereal', 'grain', 'rice', 'wheat', 'quinoa', 'oats', 'barley', 'corn', 'millet'],
        'exactMatches': ['Cereal Crops', 'Grains', 'Cereals'],
    },
    'legumes': {
        'name': 'Legumes',
        'image_url': 'https://images.unsplash.com/photo-1474979266404-7eaacbcd87c5?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80',
        'keywords': ['bean', 'pea', 'lentil', 'chickpea', 'soybean', 'kidney bean', 'black-eyed pea'],
        'exactMatches': ['Legumes', 'Beans', 'Pulses'],
    },
    'fruits-vegetables': {
        'name': 'Fruits & Veggies',
        'image_url': 'https://images.unsplash.com/photo-1610832958506-aa56368176cf?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80',
        'keywords': ['fruit', 'vegetable', 'produce', 'fresh', 'dried fruit', 'cassava', 'plantain', 'mango'],
        'exactMatches': ['Fruits & Vegetables', 'Produce', 'Fresh Produce', 'Fruits', 'Vegetables'],
    },
    'oilseeds': {
        'name': 'Oilseeds',
        'image_url': 'https://images.unsplash.com/photo-1474979266404-7eaacbcd87c5?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80',
        'keywords': ['oil', 'seed', 'nut', 'shea', 'coconut', 'sesame', 'sunflower', 'peanut'],
        'exactMatches': ['Oilseeds', 'Nuts', 'Oils', 'Seeds'],
    },
    'sweeteners': {
        'name': 'Sweeteners',
        'image_url': 'https://images.unsplash.com/photo-1509042239860-f550ce710b93?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80',
        'keywords': ['sugar', 'honey', 'molasses', 'maple', 'sweetener', 'agave'],
        'exactMatches': ['Sweeteners', 'Sugar & Honey'],
    },
    'beverages': {
        'name': 'Beverages',
        'image_url': 'https://images.unsplash.com/photo-1509042239860-f550ce710b93?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80',
        'keywords': ['drink', 'juice', 'coffee', 'tea', 'smoothie', 'kombucha'],
        'exactMatches': ['Beverages', 'Drinks', 'Juices'],
    },
    'dairy-alternatives': {
        'name': 'Dairy Alternatives',
        'image_url': 'https://images.unsplash.com/photo-1585238342028-4a1f3d1d0f4e?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80',
        'keywords': ['almond milk', 'soy milk', 'coconut milk', 'cashew milk', 'plant-based'],
        'exactMatches': ['Dairy Alternatives', 'Plant-based Milk'],
    },
    'spices-herbs': {
        'name': 'Spices & Herbs',
        'image_url': 'https://images.unsplash.com/photo-1532336414038-cf19250c5757?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80',
        'keywords': ['cinnamon', 'turmeric', 'basil', 'oregano', 'pepper', 'herb', 'spice'],
        'exactMatches': ['Spices', 'Herbs', 'Seasonings'],
    },
    'nuts-seeds': {
        'name': 'Nuts & Seeds',
        'image_url': 'https://images.unsplash.com/photo-1508061253366-f7da158b6d46?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80',
        'keywords': ['almond', 'cashew', 'walnut', 'pumpkin seed', 'sunflower seed', 'chia'],
        'exactMatches': ['Nuts', 'Seeds'],
    },
}

# Diverse product images for different categories
image_urls = [
    # Grains and cereals
    "https://images.unsplash.com/photo-1586201375761-83865001e31c?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80",
    "https://images.unsplash.com/photo-1574323347407-f5e1c0cf4b7e?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80",
    "https://images.unsplash.com/photo-1574323347407-f5e1c0cf4b7e?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80",
    # Fruits and vegetables
    "https://images.unsplash.com/photo-1559181567-c3190ca9959b?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80",
    "https://images.unsplash.com/photo-1610832958506-aa56368176cf?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80",
    "https://images.unsplash.com/photo-1506976785307-8732e854ad03?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80",
    # Nuts and seeds
    "https://images.unsplash.com/photo-1508061253366-f7da158b6d46?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80",
    "https://images.unsplash.com/photo-1553909489-cd47e0ef937f?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80",
    # Spices and herbs
    "https://images.unsplash.com/photo-1532336414038-cf19250c5757?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80",
    "https://images.unsplash.com/photo-1596040033229-a9821ebd058d?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80",
    # Legumes and beans
    "https://images.unsplash.com/photo-1474979266404-7eaacbcd87c5?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80",
    "https://images.unsplash.com/photo-1585238342028-4a1f3d1d0f4e?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80",
    # Beverages and liquids
    "https://images.unsplash.com/photo-1509042239860-f550ce710b93?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80",
    "https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80",
    # General food products
    "https://images.unsplash.com/photo-1542838132-92c53300491e?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80",
    "https://images.unsplash.com/photo-1498837167922-ddd27525d352?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80",
]

DEFAULT_NUM_CATEGORIES = len(FILTER_CATEGORIES)
DEFAULT_NUM_USERS = 20
DEFAULT_NUM_PRODUCTS = 40
DEFAULT_VARIANTS_PER_PRODUCT = 2
DEFAULT_BATCH_SIZE = 50

# Comprehensive tax rates data
TAX_RATES_DATA = [
    # United States - State Sales Tax
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
    
    # Canada - Provincial Sales Tax (PST/GST/HST)
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
    
    # United Kingdom
    {"country_code": "GB", "country_name": "United Kingdom", "province_code": None, "province_name": None, "tax_rate": 0.20, "tax_name": "VAT"},
    
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
        for cat_id, cat_data in FILTER_CATEGORIES.items():
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
                (v['keywords'] for k, v in FILTER_CATEGORIES.items()
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
                for img_idx in range(num_images):
                    img_url = random.choice(image_urls)
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
                order_number = f"ORD-{str(order_uuid)[:8].upper()}" # Generate a unique order number based on the order_uuid
                
                # Generate dummy address data
                dummy_address = {
                    "street": f"{random.randint(1, 999)} Seed St",
                    "city": "Seed City",
                    "state": "SD",
                    "country": "Seedland",
                    "post_code": "00000"
                }

                order = Order(
                    id=order_uuid,
                    order_number=order_number,
                    user_id=user.id,
                    guest_email=user.email if random.random() < 0.2 else None, # 20% chance of guest email
                    order_status=random.choice(["pending", "shipped", "delivered", "processing", "cancelled"]),
                    payment_status=random.choice(["pending", "paid", "refunded", "failed"]),
                    fulfillment_status=random.choice(["unfulfilled", "fulfilled", "partial"]),
                    subtotal=0.0, # Will be updated
                    tax_amount=round(random.uniform(5.0, 20.0), 2),
                    shipping_amount=chosen_shipping_method.price,
                    discount_amount=round(random.uniform(0.0, 15.0), 2) if random.random() < 0.3 else 0.0,
                    total_amount=0.0, # Will be updated
                    currency="USD",
                    shipping_method=chosen_shipping_method.name,
                    tracking_number=str(uuid7()) if random.random() < 0.7 else None,
                    carrier=random.choice(["DHL", "FedEx", "UPS", "Local Delivery"]) if random.random() < 0.8 else None,
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

                order.total_amount = order_total

                transaction = Transaction(
                    id=uuid7(),
                    user_id=user.id,
                    order_id=order.id,
                    # Generate a dummy ID for seeding
                    stripe_payment_intent_id=str(uuid7()),
                    amount=order_total,
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

        for i in range(1, 21):  # Create 20 dummy subscriptions
            chosen_user = random.choice(all_users)
            subscription = Subscription(
                id=uuid7(),
                user_id=chosen_user.id,
                plan_id=random.choice(["basic", "premium", "enterprise"]),
                status=random.choice(["active", "cancelled", "expired"]),
                auto_renew=random.choice([True, False]),
            )
            subscriptions_batch.append(subscription)

        if subscriptions_batch:
            session.add_all(subscriptions_batch)
            await session.flush()
            await session.commit()
            session.expunge_all()
        print(f"💳 Created {len(subscriptions_batch)} subscriptions.")

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


async def seed_tax_rates(session):
    """Seed tax rates into the database"""
    try:
        # Check if tax rates already exist
        result = await session.execute(select(TaxRate).limit(1))
        existing = result.scalar_one_or_none()
        
        if existing:
            print("Tax rates already seeded. Skipping...")
            return
        
        print(f"🌍 Seeding {len(TAX_RATES_DATA)} tax rates...")
        
        # Create tax rate objects in batches
        tax_rates_batch = []
        for data in TAX_RATES_DATA:
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
        
        print(f"✅ Successfully seeded {len(TAX_RATES_DATA)} tax rates")
        
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
        if args.seed:
            await seed_sample_data(
                categories_count=args.categories,
                users_count=args.users,
                products_count=args.products,
                variants_per_product=args.variants,
                batch_size=args.batch_size,
            )
            # Seed tax rates after other data
            async with db_manager.session_factory() as session:
                await seed_tax_rates(session)
        print("✅ Database initialization complete!")
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
