"""
Subscription Scheduler Service
Handles automatic creation of orders for periodic shipments
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from uuid import UUID
import logging

from models.subscriptions import Subscription
from models.orders import Order, OrderItem, OrderStatus, PaymentStatus, FulfillmentStatus, OrderSource
from models.product import ProductVariant
from models.user import User
from services.notifications import NotificationService
from core.database import get_db

logger = logging.getLogger(__name__)


class SubscriptionSchedulerService:
    """Service for managing subscription shipment scheduling"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.notification_service = NotificationService(db)
    
    async def process_due_subscriptions(self) -> Dict[str, Any]:
        """Process all subscriptions that are due for shipment"""
        current_time = datetime.utcnow()
        
        # Find active subscriptions due for next shipment
        result = await self.db.execute(
            select(Subscription).where(
                and_(
                    Subscription.status == "active",
                    Subscription.next_billing_date <= current_time,
                    Subscription.auto_renew == True
                )
            ).options(selectinload(Subscription.products))
        )
        
        due_subscriptions = result.scalars().all()
        
        processed_count = 0
        failed_count = 0
        results = []
        
        for subscription in due_subscriptions:
            try:
                order = await self.create_subscription_order(subscription)
                if order:
                    processed_count += 1
                    results.append({
                        "subscription_id": str(subscription.id),
                        "order_id": str(order.id),
                        "status": "success"
                    })
                    logger.info(f"Created order {order.order_number} for subscription {subscription.id}")
                else:
                    failed_count += 1
                    results.append({
                        "subscription_id": str(subscription.id),
                        "status": "failed",
                        "reason": "Order creation failed"
                    })
            except Exception as e:
                failed_count += 1
                results.append({
                    "subscription_id": str(subscription.id),
                    "status": "failed",
                    "reason": str(e)
                })
                logger.error(f"Failed to process subscription {subscription.id}: {e}")
        
        return {
            "processed_count": processed_count,
            "failed_count": failed_count,
            "total_due": len(due_subscriptions),
            "results": results
        }
    
    async def create_subscription_order(self, subscription: Subscription) -> Optional[Order]:
        """Create an order from a subscription with proper VAT calculation"""
        try:
            # Get user
            user_result = await self.db.execute(
                select(User).where(User.id == subscription.user_id)
            )
            user = user_result.scalar_one_or_none()
            if not user:
                raise Exception(f"User not found for subscription {subscription.id}")
            
            # Get product variants
            if not subscription.variant_ids:
                raise Exception(f"No products in subscription {subscription.id}")
            
            variant_result = await self.db.execute(
                select(ProductVariant).where(
                    ProductVariant.id.in_([UUID(vid) for vid in subscription.variant_ids])
                )
            )
            variants = variant_result.scalars().all()
            
            if not variants:
                raise Exception(f"No valid variants found for subscription {subscription.id}")
            
            # Recalculate pricing with current product prices and VAT
            updated_cost = await self._recalculate_subscription_pricing(subscription, variants)
            
            # Create order with updated pricing
            order = Order(
                user_id=subscription.user_id,
                order_number=await self._generate_order_number(),
                order_status=OrderStatus.PENDING,
                payment_status=PaymentStatus.PENDING,
                fulfillment_status=FulfillmentStatus.UNFULFILLED,
                source=OrderSource.API,
                subtotal=updated_cost["subtotal"],
                tax_amount=updated_cost["tax_amount"],
                shipping_amount=updated_cost["delivery_cost"],
                discount_amount=updated_cost.get("loyalty_discount", 0.0),
                total_amount=updated_cost["total_amount"],
                currency=subscription.currency or "USD",
                shipping_method=subscription.delivery_type or "standard",
                # Copy delivery info from subscription
                shipping_address=await self._get_delivery_address(subscription),
                billing_address=await self._get_delivery_address(subscription),  # Use same for billing
                subscription_id=subscription.id,
                order_metadata={
                    "subscription_order": True,
                    "subscription_id": str(subscription.id),
                    "billing_cycle": subscription.billing_cycle,
                    "delivery_type": subscription.delivery_type,
                    "cost_breakdown": updated_cost,
                    "order_created_at": datetime.utcnow().isoformat()
                }
            )
            
            self.db.add(order)
            await self.db.flush()  # Get order ID
            
            # Create order items with current prices
            for product_detail in updated_cost.get("product_details", []):
                variant_id = UUID(product_detail["variant_id"])
                variant = next((v for v in variants if v.id == variant_id), None)
                
                if variant:
                    # Get quantity from subscription metadata or default to 1
                    quantity = self._get_variant_quantity(subscription, variant_id)
                    unit_price = product_detail["price"]
                    line_total = unit_price * quantity
                    
                    order_item = OrderItem(
                        order_id=order.id,
                        product_variant_id=variant.id,
                        quantity=quantity,
                        unit_price=unit_price,
                        total_price=line_total,
                        product_name=getattr(variant, 'product_name', product_detail["name"]),
                        variant_name=getattr(variant, 'name', ''),
                        sku=getattr(variant, 'sku', ''),
                        item_metadata={
                            "subscription_item": True,
                            "original_price": unit_price,
                            "price_at_order": unit_price
                        }
                    )
                    
                    self.db.add(order_item)
            
            # Update subscription with new pricing (in case product prices changed)
            subscription.price = updated_cost["total_amount"]
            subscription.cost_breakdown = updated_cost
            subscription.tax_rate_applied = updated_cost.get("tax_rate")
            subscription.tax_amount = updated_cost.get("tax_amount")
            
            # Update subscription billing dates
            await self._update_subscription_billing_dates(subscription)
            
            await self.db.commit()
            
            # Send notification with order details
            await self.notification_service.create_notification(
                user_id=subscription.user_id,
                message=f"Your subscription order #{order.order_number} has been created! Total: {updated_cost['total_amount']} {subscription.currency}. It will be shipped soon.",
                type="info",
                related_id=str(order.id)
            )
            
            return order
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to create order for subscription {subscription.id}: {e}")
            raise
    
    async def _generate_order_number(self) -> str:
        """Generate unique order number"""
        from core.utils.uuid_utils import uuid7
        timestamp = datetime.utcnow().strftime("%Y%m%d")
        short_uuid = str(uuid7())[:8].upper()
        return f"SUB-{timestamp}-{short_uuid}"
    
    async def _recalculate_subscription_pricing(self, subscription: Subscription, variants: List[ProductVariant]) -> Dict[str, Any]:
        """Recalculate subscription pricing with current product prices and VAT"""
        from services.subscriptions.subscription import SubscriptionService
        from models.user import Address
        
        # Get customer address for tax calculation
        customer_address = None
        if subscription.delivery_address_id:
            address_result = await self.db.execute(
                select(Address).where(Address.id == subscription.delivery_address_id)
            )
            address = address_result.scalar_one_or_none()
            if address:
                customer_address = {
                    "street": address.street,
                    "city": address.city,
                    "state": address.state,
                    "country": address.country,
                    "post_code": address.post_code
                }
        
        # Use the enhanced cost calculation from SubscriptionService
        subscription_service = SubscriptionService(self.db)
        updated_cost = await subscription_service._calculate_subscription_cost(
            variants=variants,
            delivery_type=subscription.delivery_type or "standard",
            customer_address=customer_address,
            currency=subscription.currency or "USD",
            user_id=subscription.user_id
        )
        
        return updated_cost
    
    def _get_variant_quantity(self, subscription: Subscription, variant_id: UUID) -> int:
        """Get quantity for a variant from subscription metadata"""
        if not subscription.subscription_metadata:
            return 1
        
        # Check if quantities are stored in metadata
        quantities = subscription.subscription_metadata.get("variant_quantities", {})
        return quantities.get(str(variant_id), 1)
    
    async def _get_delivery_address(self, subscription: Subscription) -> Dict[str, Any]:
        """Get delivery address for subscription order"""
        if subscription.delivery_address_id:
            from models.user import Address
            address_result = await self.db.execute(
                select(Address).where(Address.id == subscription.delivery_address_id)
            )
            address = address_result.scalar_one_or_none()
            if address:
                return {
                    "street": address.street,
                    "city": address.city,
                    "state": address.state,
                    "country": address.country,
                    "post_code": address.post_code,
                    "type": "shipping",
                    "delivery_type": subscription.delivery_type or "standard"
                }
        
        # Fallback to basic structure
        return {
            "type": "shipping",
            "delivery_type": subscription.delivery_type or "standard"
        }
    
    async def _update_subscription_billing_dates(self, subscription: Subscription):
        """Update subscription billing dates after creating order"""
        current_period_end = subscription.current_period_end or datetime.utcnow()
        
        # Calculate next billing period based on billing cycle
        if subscription.billing_cycle == "weekly":
            next_period_start = current_period_end
            next_period_end = current_period_end + timedelta(weeks=1)
        elif subscription.billing_cycle == "yearly":
            next_period_start = current_period_end
            next_period_end = current_period_end + timedelta(days=365)
        else:  # monthly (default)
            next_period_start = current_period_end
            next_period_end = current_period_end + timedelta(days=30)
        
        subscription.current_period_start = next_period_start
        subscription.current_period_end = next_period_end
        subscription.next_billing_date = next_period_end
        
        # Update metadata
        if not subscription.subscription_metadata:
            subscription.subscription_metadata = {}
        
        subscription.subscription_metadata.update({
            "last_order_created": datetime.utcnow().isoformat(),
            "orders_created_count": subscription.subscription_metadata.get("orders_created_count", 0) + 1
        })


# Standalone function for background task
async def process_subscription_shipments():
    """Background task function to process subscription shipments"""
    async for db in get_db():
        try:
            scheduler = SubscriptionSchedulerService(db)
            result = await scheduler.process_due_subscriptions()
            logger.info(f"Processed subscription shipments: {result}")
            return result
        except Exception as e:
            logger.error(f"Error processing subscription shipments: {e}")
            raise
        finally:
            await db.close()