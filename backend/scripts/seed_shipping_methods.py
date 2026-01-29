#!/usr/bin/env python3
"""
Script to seed basic shipping methods into the database
"""

import asyncio
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import AsyncSession
from core.db import get_async_session
from services.shipping import ShippingService
from schemas.shipping import ShippingMethodCreate


async def seed_shipping_methods():
    """Seed basic shipping methods"""
    
    # Basic shipping methods to create
    shipping_methods = [
        ShippingMethodCreate(
            name="Standard Shipping",
            description="Standard delivery within 5-7 business days",
            price=5.99,
            estimated_days=7,
            is_active=True,
            carrier="USPS",
            tracking_url_template="https://tools.usps.com/go/TrackConfirmAction?tLabels={tracking_number}"
        ),
        ShippingMethodCreate(
            name="Express Shipping",
            description="Fast delivery within 2-3 business days",
            price=12.99,
            estimated_days=3,
            is_active=True,
            carrier="FedEx",
            tracking_url_template="https://www.fedex.com/fedextrack/?trknbr={tracking_number}"
        ),
        ShippingMethodCreate(
            name="Overnight Shipping",
            description="Next business day delivery",
            price=24.99,
            estimated_days=1,
            is_active=True,
            carrier="UPS",
            tracking_url_template="https://www.ups.com/track?tracknum={tracking_number}"
        ),
        ShippingMethodCreate(
            name="Free Shipping",
            description="Free standard shipping (orders over $50)",
            price=0.00,
            estimated_days=7,
            is_active=True,
            carrier="USPS",
            tracking_url_template="https://tools.usps.com/go/TrackConfirmAction?tLabels={tracking_number}"
        )
    ]
    
    async with get_async_session() as db:
        shipping_service = ShippingService(db)
        
        print("Seeding shipping methods...")
        
        for method_data in shipping_methods:
            try:
                # Check if method already exists
                existing_methods = await shipping_service.get_all_active_shipping_methods()
                if any(method.name == method_data.name for method in existing_methods):
                    print(f"Shipping method '{method_data.name}' already exists, skipping...")
                    continue
                
                # Create the shipping method
                method = await shipping_service.create_shipping_method(method_data)
                print(f"Created shipping method: {method.name} - ${method.price}")
                
            except Exception as e:
                print(f"Error creating shipping method '{method_data.name}': {e}")
        
        print("Shipping methods seeding completed!")


if __name__ == "__main__":
    asyncio.run(seed_shipping_methods())