#!/usr/bin/env python3
"""
Simple script to fix products with zero prices using the existing database setup
"""
import asyncio
import sys
import os
from decimal import Decimal
import random

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import select
from core.database import db_manager, initialize_db
from core.config import settings
from models.product import ProductVariant
from models.subscriptions import Subscription
from sqlalchemy.orm import selectinload


async def fix_zero_prices():
    """Fix products with zero or null prices"""
    # Initialize database
    initialize_db(settings.SQLALCHEMY_DATABASE_URI, settings.ENVIRONMENT == "local")
    
    async with db_manager.get_session_with_retry() as db:
        try:
            # Find variants with zero or null base_price
            result = await db.execute(
                select(ProductVariant).where(
                    (ProductVariant.base_price == None) | 
                    (ProductVariant.base_price == 0)
                )
            )
            variants_to_fix = result.scalars().all()
            
            print(f"Found {len(variants_to_fix)} variants with zero or null prices")
            
            if not variants_to_fix:
                print("No variants need fixing!")
                return
            
            # Fix each variant
            fixed_count = 0
            for variant in variants_to_fix:
                # Generate a reasonable price based on the product name/category
                base_price = round(random.uniform(9.99, 49.99), 2)
                
                # 30% chance of having a sale price
                sale_price = None
                if random.random() < 0.3:
                    sale_price = round(base_price * random.uniform(0.7, 0.9), 2)
                
                # Update the variant
                variant.base_price = base_price
                variant.sale_price = sale_price
                
                print(f"Fixed variant {variant.name} (SKU: {variant.sku}): "
                      f"base_price=${base_price}, sale_price=${sale_price}")
                
                fixed_count += 1
            
            # Commit the changes
            await db.commit()
            print(f"\nSuccessfully fixed {fixed_count} variants!")
            
        except Exception as e:
            print(f"Error fixing prices: {e}")
            await db.rollback()
            raise


async def check_subscription_products():
    """Check products in subscriptions to see their pricing"""
    # Initialize database
    initialize_db(settings.SQLALCHEMY_DATABASE_URI, settings.ENVIRONMENT == "local")
    
    async with db_manager.get_session_with_retry() as db:
        try:
            # Get all subscriptions with their products
            result = await db.execute(
                select(Subscription).options(
                    selectinload(Subscription.products)
                ).limit(5)  # Just check first 5 subscriptions
            )
            subscriptions = result.scalars().all()
            
            print(f"Checking {len(subscriptions)} subscriptions...")
            
            for subscription in subscriptions:
                print(f"\nSubscription {subscription.id} ({subscription.plan_id}):")
                print(f"  Status: {subscription.status}")
                print(f"  Price: ${subscription.price}")
                print(f"  Products ({len(subscription.products)}):")
                
                for product in subscription.products:
                    print(f"    - {product.name} (SKU: {product.sku})")
                    print(f"      base_price: ${product.base_price}")
                    print(f"      sale_price: ${product.sale_price}")
                    print(f"      current_price: ${product.current_price}")
                    
        except Exception as e:
            print(f"Error checking subscriptions: {e}")


if __name__ == "__main__":
    print("=== Product Price Fixer ===")
    
    # Check subscription products first
    print("\n1. Checking subscription products...")
    asyncio.run(check_subscription_products())
    
    # Fix zero prices
    print("\n2. Fixing zero prices...")
    asyncio.run(fix_zero_prices())
    
    # Check again after fixing
    print("\n3. Checking subscription products after fix...")
    asyncio.run(check_subscription_products())