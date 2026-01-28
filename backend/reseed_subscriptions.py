#!/usr/bin/env python3
"""
Subscription reseeding script for Banwee API.
This script reseeds subscription data to match the updated Subscription interface.

Usage:
    python reseed_subscriptions.py [--count COUNT] [--clear-existing]
    
Options:
    --count COUNT        Number of subscriptions to create (default: 25)
    --clear-existing     Clear existing subscriptions before seeding
"""

import asyncio
import argparse
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, delete
from core.config import settings
from core.utils.uuid_utils import uuid7
from models.subscriptions import Subscription
from models.user import User
from models.product import Product, ProductVariant


class SubscriptionReseeder:
    """Handles reseeding of subscription data with the updated interface structure."""
    
    def __init__(self):
        self.plan_configs = {
            "basic": {
                "price": 19.99,
                "description": "Basic subscription plan with essential features"
            },
            "premium": {
                "price": 39.99,
                "description": "Premium subscription plan with advanced features"
            },
            "enterprise": {
                "price": 79.99,
                "description": "Enterprise subscription plan with full features"
            }
        }
        
        self.billing_cycles = ["weekly", "monthly", "yearly"]
        self.statuses = ["active", "cancelled", "paused"]
        self.currencies = ["USD", "EUR", "GBP", "CAD"]
        
        # Initialize database connection
        self.engine = create_async_engine(settings.SQLALCHEMY_DATABASE_URI, echo=False)
        self.async_session = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )
        
    async def clear_existing_subscriptions(self):
        """Clear all existing subscriptions from the database."""
        async with self.async_session() as session:
            print("🗑️  Clearing existing subscriptions...")
            
            # First clear the association table
            from sqlalchemy import text
            await session.execute(text("DELETE FROM subscription_product_association"))
            
            # Then clear subscriptions
            result = await session.execute(delete(Subscription))
            await session.commit()
            print(f"✅ Cleared {result.rowcount} existing subscriptions")
    
    async def get_sample_data(self):
        """Get sample users and product variants for subscription creation."""
        async with self.async_session() as session:
            # Get all users
            users_result = await session.execute(select(User))
            users = users_result.scalars().all()
            
            # Get all product variants with their products eagerly loaded
            from sqlalchemy.orm import selectinload
            variants_result = await session.execute(
                select(ProductVariant)
                .join(Product)
                .options(selectinload(ProductVariant.product))
                .options(selectinload(ProductVariant.images))
            )
            variants = variants_result.scalars().all()
            
            if not users:
                raise ValueError("No users found in database. Please seed users first.")
            if not variants:
                raise ValueError("No product variants found in database. Please seed products first.")
                
            return users, variants
    
    def generate_cost_breakdown(self, base_price: float, variants: List[ProductVariant], 
                              variant_quantities: Dict[str, int], currency: str) -> Dict[str, Any]:
        """Generate detailed cost breakdown matching the interface structure."""
        
        # Calculate subtotal from product variants
        product_variants_data = []
        subtotal = 0.0
        
        for variant in variants:
            variant_id = str(variant.id)
            quantity = variant_quantities.get(variant_id, 1)
            # Use current_price property which handles sale_price vs base_price
            variant_price = float(variant.current_price) if hasattr(variant, 'current_price') else float(variant.base_price)
            variant_total = variant_price * quantity
            subtotal += variant_total
            
            product_variants_data.append({
                "variant_id": variant_id,
                "name": f"{variant.product.name} - {variant.name}" if variant.product else variant.name,
                "price": variant_price,
                "quantity": quantity
            })
        
        # Generate shipping cost (0-15.99)
        shipping_cost = round(random.uniform(0.0, 15.99), 2)
        
        # Generate tax rate (5-12%) and calculate tax amount
        tax_rate = round(random.uniform(0.05, 0.12), 4)
        tax_amount = round((subtotal + shipping_cost) * tax_rate, 2)
        
        # Calculate total
        total_amount = round(subtotal + shipping_cost + tax_amount, 2)
        
        return {
            "subtotal": subtotal,
            "shipping_cost": shipping_cost,
            "tax_amount": tax_amount,
            "tax_rate": tax_rate,
            "total_amount": total_amount,
            "currency": currency,
            "product_variants": product_variants_data
        }
    
    def generate_products_data(self, variants: List[ProductVariant]) -> List[Dict[str, Any]]:
        """Generate products array matching the interface structure."""
        products_data = []
        
        for variant in variants:
            if variant.product:
                # Check if we already have this product
                existing_product = next(
                    (p for p in products_data if p["id"] == str(variant.product.id)), 
                    None
                )
                
                if not existing_product:
                    # Get product image if available
                    image_url = None
                    if variant.images:
                        primary_image = next((img for img in variant.images if img.is_primary), 
                                           variant.images[0] if variant.images else None)
                        if primary_image:
                            image_url = primary_image.url
                    
                    # Use current price if available, otherwise use base price
                    current_price = float(variant.current_price) if hasattr(variant, 'current_price') else float(variant.base_price)
                    base_price = float(variant.product.min_price) if variant.product.min_price else float(variant.base_price)
                    
                    products_data.append({
                        "id": str(variant.product.id),
                        "name": variant.product.name,
                        "price": base_price,
                        "current_price": current_price,
                        "image": image_url
                    })
        
        return products_data
    
    def generate_next_billing_date(self, billing_cycle: str, status: str) -> datetime:
        """Generate next billing date based on billing cycle and status."""
        if status in ["cancelled", "paused"]:
            return None
            
        base_date = datetime.utcnow()
        
        if billing_cycle == "weekly":
            return base_date + timedelta(weeks=1)
        elif billing_cycle == "monthly":
            return base_date + timedelta(days=30)
        elif billing_cycle == "yearly":
            return base_date + timedelta(days=365)
        else:
            return base_date + timedelta(days=30)  # Default to monthly
    
    async def create_subscription(self, user: User, variants: List[ProductVariant]) -> Subscription:
        """Create a single subscription with realistic data."""
        
        # Choose random plan
        plan_id = random.choice(list(self.plan_configs.keys()))
        plan_config = self.plan_configs[plan_id]
        
        # Choose random attributes
        status = random.choice(self.statuses)
        billing_cycle = random.choice(self.billing_cycles)
        currency = random.choice(self.currencies)
        auto_renew = random.choice([True, False])
        
        # Select 1-4 random variants for this subscription
        selected_variants = random.sample(variants, min(random.randint(1, 4), len(variants)))
        
        # Generate variant quantities
        variant_quantities = {}
        for variant in selected_variants:
            variant_quantities[str(variant.id)] = random.randint(1, 3)
        
        # Generate cost breakdown
        cost_breakdown = self.generate_cost_breakdown(
            plan_config["price"], selected_variants, variant_quantities, currency
        )
        
        # Generate products data
        products_data = self.generate_products_data(selected_variants)
        
        # Generate next billing date
        next_billing_date = self.generate_next_billing_date(billing_cycle, status)
        
        # Create subscription
        subscription = Subscription(
            id=uuid7(),
            user_id=user.id,
            plan_id=plan_id,
            status=status,
            price=plan_config["price"],
            currency=currency,
            billing_cycle=billing_cycle,
            auto_renew=auto_renew,
            next_billing_date=next_billing_date,
            variant_quantities=variant_quantities,
            cost_breakdown=cost_breakdown,
            shipping_cost=cost_breakdown["shipping_cost"],
            tax_amount=cost_breakdown["tax_amount"],
            tax_rate=cost_breakdown["tax_rate"],
            # Store products data in variant_ids for now (you might want to add a products field to the model)
            variant_ids=[str(v.id) for v in selected_variants]
        )
        
        return subscription
    
    async def reseed_subscriptions(self, count: int = 25, clear_existing: bool = False):
        """Main method to reseed subscriptions."""
        print(f"🌱 Starting subscription reseeding process...")
        print(f"   Target count: {count}")
        print(f"   Clear existing: {clear_existing}")
        print()
        
        if clear_existing:
            await self.clear_existing_subscriptions()
        
        # Get sample data
        print("📊 Fetching sample data...")
        users, variants = await self.get_sample_data()
        print(f"   Found {len(users)} users and {len(variants)} product variants")
        
        # Create subscriptions
        print(f"🔄 Creating {count} subscriptions...")
        subscriptions = []
        
        for i in range(count):
            user = random.choice(users)
            subscription = await self.create_subscription(user, variants)
            subscriptions.append(subscription)
            
            if (i + 1) % 10 == 0:
                print(f"   Generated {i + 1}/{count} subscriptions...")
        
        # Save to database
        print("💾 Saving subscriptions to database...")
        async with self.async_session() as session:
            session.add_all(subscriptions)
            await session.commit()
        
        print(f"✅ Successfully created {len(subscriptions)} subscriptions!")
        
        # Print summary
        await self.print_summary()
    
    async def print_summary(self):
        """Print a summary of created subscriptions."""
        async with self.async_session() as session:
            result = await session.execute(select(Subscription))
            subscriptions = result.scalars().all()
            
            if not subscriptions:
                print("📊 No subscriptions found in database.")
                return
            
            # Count by status
            status_counts = {}
            plan_counts = {}
            billing_cycle_counts = {}
            
            for sub in subscriptions:
                status_counts[sub.status] = status_counts.get(sub.status, 0) + 1
                plan_counts[sub.plan_id] = plan_counts.get(sub.plan_id, 0) + 1
                billing_cycle_counts[sub.billing_cycle] = billing_cycle_counts.get(sub.billing_cycle, 0) + 1
            
            print()
            print("📊 Subscription Summary:")
            print(f"   Total subscriptions: {len(subscriptions)}")
            print()
            print("   By Status:")
            for status, count in status_counts.items():
                print(f"     {status}: {count}")
            print()
            print("   By Plan:")
            for plan, count in plan_counts.items():
                print(f"     {plan}: {count}")
            print()
            print("   By Billing Cycle:")
            for cycle, count in billing_cycle_counts.items():
                print(f"     {cycle}: {count}")
            print()
    
    async def cleanup(self):
        """Clean up database connections."""
        await self.engine.dispose()


async def main():
    """Main function to handle command line arguments and run reseeding."""
    parser = argparse.ArgumentParser(description="Reseed subscription data for Banwee API")
    parser.add_argument(
        "--count", 
        type=int, 
        default=25, 
        help="Number of subscriptions to create (default: 25)"
    )
    parser.add_argument(
        "--clear-existing", 
        action="store_true", 
        help="Clear existing subscriptions before seeding"
    )
    
    args = parser.parse_args()
    
    try:
        reseeder = SubscriptionReseeder()
        await reseeder.reseed_subscriptions(
            count=args.count,
            clear_existing=args.clear_existing
        )
        await reseeder.cleanup()
        print("🎉 Subscription reseeding completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during reseeding: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())