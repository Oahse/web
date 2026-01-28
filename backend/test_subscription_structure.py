#!/usr/bin/env python3
"""
Test script to verify subscription data structure matches the interface.
This script fetches a few subscriptions and prints their structure.
"""

import asyncio
import json
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from core.config import settings
from models.subscriptions import Subscription
from models.user import User
from models.product import Product, ProductVariant


async def test_subscription_structure():
    """Test and display subscription data structure."""
    print("🔍 Testing Subscription Data Structure")
    print("=====================================")
    print()
    
    # Initialize database connection
    engine = create_async_engine(settings.SQLALCHEMY_DATABASE_URI, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    try:
        async with async_session() as session:
            # Get a few subscriptions with related data
            result = await session.execute(
                select(Subscription)
                .join(User)
                .limit(3)
            )
            subscriptions = result.scalars().all()
            
            if not subscriptions:
                print("❌ No subscriptions found in database.")
                print("   Please run the reseeding script first:")
                print("   ./reseed-subscriptions.sh")
                return
            
            print(f"📊 Found {len(subscriptions)} subscriptions to test")
            print()
            
            for i, subscription in enumerate(subscriptions, 1):
                print(f"🔸 Subscription {i}:")
                print(f"   ID: {subscription.id}")
                print(f"   Plan: {subscription.plan_id}")
                print(f"   Status: {subscription.status}")
                print(f"   Price: ${subscription.price}")
                print(f"   Currency: {subscription.currency}")
                print(f"   Billing Cycle: {subscription.billing_cycle}")
                print(f"   Auto Renew: {subscription.auto_renew}")
                print(f"   Next Billing: {subscription.next_billing_date}")
                print(f"   Created: {subscription.created_at}")
                print()
                
                # Test variant quantities
                if subscription.variant_quantities:
                    print("   📦 Variant Quantities:")
                    for variant_id, quantity in subscription.variant_quantities.items():
                        print(f"     {variant_id}: {quantity}")
                    print()
                
                # Test cost breakdown
                if subscription.cost_breakdown:
                    print("   💰 Cost Breakdown:")
                    cost_breakdown = subscription.cost_breakdown
                    print(f"     Subtotal: ${cost_breakdown.get('subtotal', 0)}")
                    print(f"     Shipping Cost: ${cost_breakdown.get('shipping_cost', 0)}")
                    print(f"     Tax Amount: ${cost_breakdown.get('tax_amount', 0)}")
                    print(f"     Tax Rate: {cost_breakdown.get('tax_rate', 0) * 100:.1f}%")
                    print(f"     Total Amount: ${cost_breakdown.get('total_amount', 0)}")
                    print(f"     Currency: {cost_breakdown.get('currency', 'USD')}")
                    
                    if cost_breakdown.get('product_variants'):
                        print("     📋 Product Variants:")
                        for variant in cost_breakdown['product_variants']:
                            print(f"       - {variant.get('name', 'Unknown')}")
                            print(f"         Price: ${variant.get('price', 0)} x {variant.get('quantity', 1)}")
                            print(f"         Variant ID: {variant.get('variant_id', 'N/A')}")
                    print()
                
                # Test simplified cost fields
                print("   💳 Simplified Cost Fields:")
                print(f"     Shipping Cost: ${subscription.shipping_cost or 0}")
                print(f"     Tax Amount: ${subscription.tax_amount or 0}")
                print(f"     Tax Rate: {(subscription.tax_rate or 0) * 100:.1f}%")
                print()
                
                # Test interface compliance
                print("   ✅ Interface Compliance Check:")
                interface_fields = [
                    'id', 'plan_id', 'status', 'price', 'currency', 'billing_cycle',
                    'auto_renew', 'next_billing_date', 'created_at', 'variant_quantities',
                    'cost_breakdown', 'shipping_cost', 'tax_amount', 'tax_rate'
                ]
                
                missing_fields = []
                for field in interface_fields:
                    if not hasattr(subscription, field):
                        missing_fields.append(field)
                
                if missing_fields:
                    print(f"     ❌ Missing fields: {', '.join(missing_fields)}")
                else:
                    print("     ✅ All required fields present")
                
                # Check cost_breakdown structure
                if subscription.cost_breakdown:
                    required_breakdown_fields = [
                        'subtotal', 'shipping_cost', 'tax_amount', 'tax_rate', 
                        'total_amount', 'currency'
                    ]
                    missing_breakdown = []
                    for field in required_breakdown_fields:
                        if field not in subscription.cost_breakdown:
                            missing_breakdown.append(field)
                    
                    if missing_breakdown:
                        print(f"     ❌ Missing cost_breakdown fields: {', '.join(missing_breakdown)}")
                    else:
                        print("     ✅ Cost breakdown structure complete")
                
                print("   " + "="*50)
                print()
            
            # Generate sample JSON for frontend testing
            print("📄 Sample JSON Structure for Frontend:")
            print("=====================================")
            
            if subscriptions:
                sample_subscription = subscriptions[0]
                
                # Create the structure matching your interface
                sample_json = {
                    "id": str(sample_subscription.id),
                    "plan_id": sample_subscription.plan_id,
                    "status": sample_subscription.status,
                    "price": sample_subscription.price,
                    "currency": sample_subscription.currency,
                    "billing_cycle": sample_subscription.billing_cycle,
                    "auto_renew": sample_subscription.auto_renew,
                    "next_billing_date": sample_subscription.next_billing_date.isoformat() if sample_subscription.next_billing_date else None,
                    "created_at": sample_subscription.created_at.isoformat() if sample_subscription.created_at else None,
                    "products": [],  # This would be populated from related data
                    "variant_quantities": sample_subscription.variant_quantities or {},
                    "cost_breakdown": sample_subscription.cost_breakdown,
                    "shipping_cost": sample_subscription.shipping_cost,
                    "tax_amount": sample_subscription.tax_amount,
                    "tax_rate": sample_subscription.tax_rate
                }
                
                print(json.dumps(sample_json, indent=2))
            
            print()
            print("🎉 Subscription structure test completed!")
    
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(test_subscription_structure())