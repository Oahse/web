# Consolidated subscription service
# This file includes all subscription-related functionality

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload
from fastapi import HTTPException
from models.subscriptions import Subscription
from models.user import User
from models.product import ProductVariant
from models.payments import PaymentMethod
from uuid import UUID
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from services.payments import PaymentService
from services.notifications import NotificationService


class SubscriptionService:
    """Consolidated subscription service with comprehensive subscription management"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.payment_service = PaymentService(db)
        self.notification_service = NotificationService(db)

    async def create_subscription(
        self,
        user_id: UUID,
        plan_id: str,
        variant_ids: List[UUID],
        delivery_type: str = "standard",
        delivery_address_id: Optional[UUID] = None,
        payment_method_id: Optional[UUID] = None
    ) -> Subscription:
        """Create a new subscription"""
        
        # Validate variants exist
        variant_result = await self.db.execute(
            select(ProductVariant).where(ProductVariant.id.in_(variant_ids))
        )
        variants = variant_result.scalars().all()
        
        if len(variants) != len(variant_ids):
            raise HTTPException(status_code=400, detail="Some variants not found")
        
        # Calculate subscription cost
        cost_breakdown = await self._calculate_subscription_cost(variants, delivery_type)
        
        # Create subscription
        subscription = Subscription(
            user_id=user_id,
            plan_id=plan_id,
            status="active",
            price=cost_breakdown["total_amount"],
            variant_ids=[str(vid) for vid in variant_ids],
            cost_breakdown=cost_breakdown,
            delivery_type=delivery_type,
            delivery_address_id=delivery_address_id,
            current_period_start=datetime.utcnow(),
            current_period_end=datetime.utcnow() + timedelta(days=30),  # Monthly by default
            next_billing_date=datetime.utcnow() + timedelta(days=30)
        )
        
        self.db.add(subscription)
        await self.db.commit()
        await self.db.refresh(subscription)
        
        # Process initial payment if payment method provided
        if payment_method_id:
            try:
                await self.process_subscription_payment(subscription.id, payment_method_id)
            except Exception as e:
                # If payment fails, mark subscription as payment_failed
                subscription.status = "payment_failed"
                await self.db.commit()
                raise HTTPException(status_code=400, detail=f"Payment failed: {str(e)}")
        
        # Send notification
        await self.notification_service.create_notification(
            user_id=user_id,
            message=f"Your subscription has been created successfully!",
            type="success",
            related_id=str(subscription.id)
        )
        
        return subscription

    async def get_user_subscriptions(
        self,
        user_id: UUID,
        status_filter: Optional[str] = None
    ) -> List[Subscription]:
        """Get all subscriptions for a user"""
        query = select(Subscription).where(Subscription.user_id == user_id).options(
            selectinload(Subscription.products)
        )
        
        if status_filter:
            query = query.where(Subscription.status == status_filter)
        
        query = query.order_by(Subscription.created_at.desc())
        
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_subscription_by_id(
        self,
        subscription_id: UUID,
        user_id: Optional[UUID] = None,
        for_update: bool = False
    ) -> Optional[Subscription]:
        """Get a subscription by ID with optional locking"""
        query = select(Subscription).where(Subscription.id == subscription_id).options(
            selectinload(Subscription.products)
        )
        
        if user_id:
            query = query.where(Subscription.user_id == user_id)
            
        if for_update:
            query = query.with_for_update()
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def update_subscription(
        self,
        subscription_id: UUID,
        user_id: UUID,
        variant_ids: Optional[List[UUID]] = None,
        delivery_type: Optional[str] = None,
        delivery_address_id: Optional[UUID] = None
    ) -> Subscription:
        """Update a subscription"""
        subscription = await self.get_subscription_by_id(subscription_id, user_id)
        
        if not subscription:
            raise HTTPException(status_code=404, detail="Subscription not found")
        
        if subscription.status not in ["active", "paused"]:
            raise HTTPException(status_code=400, detail="Cannot update inactive subscription")
        
        # Update fields if provided
        if variant_ids is not None:
            # Validate variants
            variant_result = await self.db.execute(
                select(ProductVariant).where(ProductVariant.id.in_(variant_ids))
            )
            variants = variant_result.scalars().all()
            
            if len(variants) != len(variant_ids):
                raise HTTPException(status_code=400, detail="Some variants not found")
            
            subscription.variant_ids = [str(vid) for vid in variant_ids]
            
            # Recalculate cost
            cost_breakdown = await self._calculate_subscription_cost(
                variants, 
                delivery_type or subscription.delivery_type
            )
            subscription.cost_breakdown = cost_breakdown
            subscription.price = cost_breakdown["total_amount"]
        
        if delivery_type is not None:
            subscription.delivery_type = delivery_type
            
            # Recalculate cost if delivery type changed
            if variant_ids is None:  # Only recalculate if we didn't already do it above
                current_variants = await self._get_subscription_variants(subscription)
                cost_breakdown = await self._calculate_subscription_cost(current_variants, delivery_type)
                subscription.cost_breakdown = cost_breakdown
                subscription.price = cost_breakdown["total_amount"]
        
        if delivery_address_id is not None:
            subscription.delivery_address_id = delivery_address_id
        
        await self.db.commit()
        await self.db.refresh(subscription)
        
        # Send notification
        await self.notification_service.create_notification(
            user_id=user_id,
            message=f"Your subscription has been updated successfully!",
            type="info",
            related_id=str(subscription.id)
        )
        
        return subscription

    async def cancel_subscription(
        self,
        subscription_id: UUID,
        user_id: UUID,
        reason: Optional[str] = None
    ) -> Subscription:
        """Cancel a subscription with atomic status update"""
        subscription = await self.get_subscription_by_id(subscription_id, user_id, for_update=True)
        
        if not subscription:
            raise HTTPException(status_code=404, detail="Subscription not found")
        
        if subscription.status == "cancelled":
            raise HTTPException(status_code=400, detail="Subscription already cancelled")
        
        subscription.status = "cancelled"
        subscription.cancelled_at = datetime.utcnow()
        subscription.auto_renew = False
        
        if reason:
            if not subscription.subscription_metadata:
                subscription.subscription_metadata = {}
            subscription.subscription_metadata["cancellation_reason"] = reason
        
        await self.db.commit()
        await self.db.refresh(subscription)
        
        # Send notification
        await self.notification_service.create_notification(
            user_id=user_id,
            message=f"Your subscription has been cancelled.",
            type="info",
            related_id=str(subscription.id)
        )
        
        return subscription

    async def pause_subscription(
        self,
        subscription_id: UUID,
        user_id: UUID,
        reason: Optional[str] = None
    ) -> Subscription:
        """Pause a subscription with atomic status update"""
        subscription = await self.get_subscription_by_id(subscription_id, user_id, for_update=True)
        
        if not subscription:
            raise HTTPException(status_code=404, detail="Subscription not found")
        
        if subscription.status != "active":
            raise HTTPException(status_code=400, detail="Can only pause active subscriptions")
        
        subscription.status = "paused"
        subscription.paused_at = datetime.utcnow()
        subscription.pause_reason = reason
        
        await self.db.commit()
        await self.db.refresh(subscription)
        
        # Send notification
        await self.notification_service.create_notification(
            user_id=user_id,
            message=f"Your subscription has been paused.",
            type="info",
            related_id=str(subscription.id)
        )
        
        return subscription

    async def resume_subscription(
        self,
        subscription_id: UUID,
        user_id: UUID
    ) -> Subscription:
        """Resume a paused subscription with atomic status update"""
        subscription = await self.get_subscription_by_id(subscription_id, user_id, for_update=True)
        
        if not subscription:
            raise HTTPException(status_code=404, detail="Subscription not found")
        
        if subscription.status != "paused":
            raise HTTPException(status_code=400, detail="Can only resume paused subscriptions")
        
        subscription.status = "active"
        subscription.paused_at = None
        subscription.pause_reason = None
        
        # Update next billing date
        subscription.next_billing_date = datetime.utcnow() + timedelta(days=30)
        
        await self.db.commit()
        await self.db.refresh(subscription)
        
        # Send notification
        await self.notification_service.create_notification(
            user_id=user_id,
            message=f"Your subscription has been resumed.",
            type="success",
            related_id=str(subscription.id)
        )
        
        return subscription

    async def process_subscription_payment(
        self,
        subscription_id: UUID,
        payment_method_id: UUID
    ) -> Dict[str, Any]:
        """Process payment for a subscription"""
        subscription = await self.get_subscription_by_id(subscription_id)
        
        if not subscription:
            raise HTTPException(status_code=404, detail="Subscription not found")
        
        # Process payment
        payment_result = await self.payment_service.process_payment(
            user_id=subscription.user_id,
            amount=subscription.price,
            payment_method_id=payment_method_id,
            subscription_id=subscription.id
        )
        
        if payment_result["status"] == "succeeded":
            # Update subscription billing dates
            subscription.current_period_start = datetime.utcnow()
            subscription.current_period_end = datetime.utcnow() + timedelta(days=30)
            subscription.next_billing_date = datetime.utcnow() + timedelta(days=30)
            
            await self.db.commit()
        
        return payment_result

    async def _calculate_subscription_cost(
        self,
        variants: List[ProductVariant],
        delivery_type: str
    ) -> Dict[str, Any]:
        """Calculate subscription cost breakdown"""
        # This is a simplified calculation - in reality you'd have complex pricing logic
        subtotal = sum(variant.current_price or 0 for variant in variants)
        
        # Delivery costs
        delivery_costs = {
            "standard": 5.0,
            "express": 15.0,
            "overnight": 25.0
        }
        delivery_cost = delivery_costs.get(delivery_type, 5.0)
        
        # Admin percentage (simplified)
        admin_percentage = 10.0  # 10%
        admin_fee = subtotal * (admin_percentage / 100)
        
        # Tax (simplified)
        tax_rate = 8.5  # 8.5%
        tax_amount = (subtotal + admin_fee + delivery_cost) * (tax_rate / 100)
        
        total_amount = subtotal + admin_fee + delivery_cost + tax_amount
        
        return {
            "subtotal": subtotal,
            "admin_fee": admin_fee,
            "admin_percentage": admin_percentage,
            "delivery_cost": delivery_cost,
            "delivery_type": delivery_type,
            "tax_amount": tax_amount,
            "tax_rate": tax_rate,
            "total_amount": total_amount,
            "currency": "USD"
        }

    async def _get_subscription_variants(self, subscription: Subscription) -> List[ProductVariant]:
        """Get variants for a subscription"""
        if not subscription.variant_ids:
            return []
        
        variant_uuids = [UUID(vid) for vid in subscription.variant_ids]
        result = await self.db.execute(
            select(ProductVariant).where(ProductVariant.id.in_(variant_uuids))
        )
        return result.scalars().all()

    async def get_subscription_analytics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get subscription analytics"""
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()
        
        # Get subscriptions in date range
        query = select(Subscription).where(
            and_(
                Subscription.created_at >= start_date,
                Subscription.created_at <= end_date
            )
        )
        
        result = await self.db.execute(query)
        subscriptions = result.scalars().all()
        
        # Calculate metrics
        total_subscriptions = len(subscriptions)
        active_subscriptions = len([s for s in subscriptions if s.status == "active"])
        cancelled_subscriptions = len([s for s in subscriptions if s.status == "cancelled"])
        paused_subscriptions = len([s for s in subscriptions if s.status == "paused"])
        
        total_revenue = sum(s.price or 0 for s in subscriptions if s.status == "active")
        average_subscription_value = total_revenue / active_subscriptions if active_subscriptions > 0 else 0
        
        return {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "metrics": {
                "total_subscriptions": total_subscriptions,
                "active_subscriptions": active_subscriptions,
                "cancelled_subscriptions": cancelled_subscriptions,
                "paused_subscriptions": paused_subscriptions,
                "total_revenue": total_revenue,
                "average_subscription_value": average_subscription_value,
                "churn_rate": (cancelled_subscriptions / total_subscriptions * 100) if total_subscriptions > 0 else 0
            }
        }
    # --- Subscription Cost Calculator (moved from separate service) ---
    async def calculate_subscription_cost(
        self,
        variant_ids: List[UUID],
        delivery_type: str,
        customer_location: str = None,
        currency: str = "USD",
        user_id: UUID = None,
        shipping_address_id: UUID = None
    ) -> 'CostBreakdown':
        """
        Calculate comprehensive subscription cost including variants, admin percentage, delivery, and tax.
        
        Args:
            variant_ids: List of product variant UUIDs
            delivery_type: Type of delivery ("standard", "express", "overnight")
            customer_location: Customer location for tax calculation
            currency: Target currency for calculation
            user_id: User ID for loyalty discount calculation
            shipping_address_id: Shipping address ID for tax calculation
            
        Returns:
            CostBreakdown object with detailed cost information
        """
        try:
            from services.admin import AdminService
            from services.tax import TaxService
            from decimal import Decimal
            
            # Get variants with their prices
            variant_result = await self.db.execute(
                select(ProductVariant).where(ProductVariant.id.in_(variant_ids))
            )
            variants = variant_result.scalars().all()
            
            if not variants:
                raise HTTPException(status_code=400, detail="No valid variants found")
            
            # Calculate variant costs
            variant_costs = []
            subtotal = Decimal('0')
            
            for variant in variants:
                variant_price = Decimal(str(variant.price))
                if currency != "USD":
                    # Convert currency if needed
                    variant_price = await self._convert_currency(variant_price, "USD", currency)
                
                variant_cost = {
                    "variant_id": str(variant.id),
                    "name": variant.name,
                    "price": float(variant_price),
                    "currency": currency
                }
                variant_costs.append(variant_cost)
                subtotal += variant_price
            
            # Get admin pricing configuration
            admin_service = AdminService(self.db)
            pricing_config = await admin_service.get_active_pricing_config()
            
            admin_percentage = pricing_config.subscription_percentage if pricing_config else 10.0
            admin_fee = subtotal * Decimal(str(admin_percentage / 100))
            
            # Calculate delivery cost
            delivery_costs = pricing_config.delivery_costs if pricing_config else {
                "standard": 5.0,
                "express": 15.0,
                "overnight": 25.0
            }
            delivery_cost = Decimal(str(delivery_costs.get(delivery_type, 5.0)))
            
            # Calculate tax
            tax_service = TaxService(self.db)
            tax_result = await tax_service.calculate_tax(
                subtotal=float(subtotal + delivery_cost),
                customer_location=customer_location,
                shipping_address_id=shipping_address_id
            )
            
            tax_rate = tax_result.get("tax_rate", 0.0)
            tax_amount = Decimal(str(tax_result.get("tax_amount", 0.0)))
            
            # Calculate loyalty discount if user provided
            loyalty_discount = Decimal('0')
            if user_id:
                try:
                    from services.loyalty import LoyaltyService
                    loyalty_service = LoyaltyService(self.db)
                    discount_result = await loyalty_service.calculate_loyalty_discount(
                        user_id=user_id,
                        subtotal=float(subtotal)
                    )
                    loyalty_discount = Decimal(str(discount_result.get("discount_amount", 0.0)))
                except Exception:
                    # If loyalty service fails, continue without discount
                    pass
            
            # Create cost breakdown
            cost_breakdown = CostBreakdown(
                variant_costs=variant_costs,
                subtotal=subtotal,
                admin_percentage=admin_percentage,
                admin_fee=admin_fee,
                delivery_type=delivery_type,
                delivery_cost=delivery_cost,
                tax_rate=tax_rate,
                tax_amount=tax_amount,
                loyalty_discount=loyalty_discount,
                currency=currency
            )
            
            return cost_breakdown
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to calculate subscription cost: {str(e)}"
            )

    async def recalculate_subscription_on_variant_change(
        self,
        subscription_id: UUID,
        added_variant_ids: List[UUID] = None,
        removed_variant_ids: List[UUID] = None,
        user_id: UUID = None
    ) -> Dict[str, Any]:
        """
        Recalculate subscription cost when variants are added or removed.
        
        Args:
            subscription_id: Subscription to recalculate
            added_variant_ids: List of variant IDs being added
            removed_variant_ids: List of variant IDs being removed
            user_id: User ID for authorization
            
        Returns:
            Dictionary with recalculation results
        """
        try:
            # Get current subscription
            subscription = await self._get_subscription_by_id(subscription_id)
            if not subscription:
                raise HTTPException(status_code=404, detail="Subscription not found")
            
            # Verify user authorization
            if user_id and subscription.user_id != user_id:
                raise HTTPException(status_code=403, detail="User not authorized")
            
            # Get current variant IDs
            current_variant_ids = [UUID(vid) for vid in (subscription.variant_ids or [])]
            
            # Apply changes
            new_variant_ids = current_variant_ids.copy()
            
            if added_variant_ids:
                for variant_id in added_variant_ids:
                    if variant_id not in new_variant_ids:
                        new_variant_ids.append(variant_id)
            
            if removed_variant_ids:
                for variant_id in removed_variant_ids:
                    if variant_id in new_variant_ids:
                        new_variant_ids.remove(variant_id)
            
            if not new_variant_ids:
                raise HTTPException(status_code=400, detail="Cannot remove all variants from subscription")
            
            # Calculate new cost
            new_cost_breakdown = await self.calculate_subscription_cost(
                variant_ids=new_variant_ids,
                delivery_type=subscription.delivery_type or "standard",
                currency=subscription.currency or "USD",
                user_id=subscription.user_id,
                shipping_address_id=subscription.delivery_address_id
            )
            
            # Calculate cost difference
            old_total = subscription.cost_breakdown.get("total_amount", 0) if subscription.cost_breakdown else 0
            new_total = float(new_cost_breakdown.total_amount)
            cost_difference = new_total - old_total
            
            # Update subscription
            subscription.variant_ids = [str(vid) for vid in new_variant_ids]
            subscription.cost_breakdown = new_cost_breakdown.to_dict()
            subscription.price = new_total
            subscription.updated_at = datetime.utcnow()
            
            await self.db.commit()
            
            # Create cost history record
            await self._create_cost_history_record(
                subscription_id=subscription_id,
                old_cost=old_total,
                new_cost=new_total,
                change_reason="variant_modification",
                change_details={
                    "added_variants": [str(vid) for vid in (added_variant_ids or [])],
                    "removed_variants": [str(vid) for vid in (removed_variant_ids or [])]
                }
            )
            
            result = {
                "subscription_id": str(subscription_id),
                "old_cost": old_total,
                "new_cost": new_total,
                "cost_difference": cost_difference,
                "new_cost_breakdown": new_cost_breakdown.to_dict(),
                "updated_variant_ids": [str(vid) for vid in new_variant_ids],
                "recalculated_at": datetime.utcnow().isoformat()
            }
            
            return result
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to recalculate subscription: {str(e)}"
            )

    async def recalculate_subscription_on_delivery_change(
        self,
        subscription_id: UUID,
        new_delivery_type: str = None,
        new_delivery_address_id: UUID = None,
        user_id: UUID = None
    ) -> Dict[str, Any]:
        """
        Recalculate subscription cost when delivery preferences change.
        
        Args:
            subscription_id: Subscription to recalculate
            new_delivery_type: New delivery type
            new_delivery_address_id: New delivery address ID
            user_id: User ID for authorization
            
        Returns:
            Dictionary with recalculation results
        """
        try:
            # Get current subscription
            subscription = await self._get_subscription_by_id(subscription_id)
            if not subscription:
                raise HTTPException(status_code=404, detail="Subscription not found")
            
            # Verify user authorization
            if user_id and subscription.user_id != user_id:
                raise HTTPException(status_code=403, detail="User not authorized")
            
            # Get current variant IDs
            variant_ids = [UUID(vid) for vid in (subscription.variant_ids or [])]
            
            if not variant_ids:
                raise HTTPException(status_code=400, detail="No variants in subscription")
            
            # Use new delivery settings or keep current ones
            delivery_type = new_delivery_type or subscription.delivery_type or "standard"
            delivery_address_id = new_delivery_address_id or subscription.delivery_address_id
            
            # Calculate new cost
            new_cost_breakdown = await self.calculate_subscription_cost(
                variant_ids=variant_ids,
                delivery_type=delivery_type,
                currency=subscription.currency or "USD",
                user_id=subscription.user_id,
                shipping_address_id=delivery_address_id
            )
            
            # Calculate cost difference
            old_total = subscription.cost_breakdown.get("total_amount", 0) if subscription.cost_breakdown else 0
            new_total = float(new_cost_breakdown.total_amount)
            cost_difference = new_total - old_total
            
            # Update subscription
            subscription.delivery_type = delivery_type
            subscription.delivery_address_id = delivery_address_id
            subscription.cost_breakdown = new_cost_breakdown.to_dict()
            subscription.price = new_total
            subscription.updated_at = datetime.utcnow()
            
            await self.db.commit()
            
            # Create cost history record
            await self._create_cost_history_record(
                subscription_id=subscription_id,
                old_cost=old_total,
                new_cost=new_total,
                change_reason="delivery_modification",
                change_details={
                    "new_delivery_type": delivery_type,
                    "new_delivery_address_id": str(delivery_address_id) if delivery_address_id else None
                }
            )
            
            result = {
                "subscription_id": str(subscription_id),
                "old_cost": old_total,
                "new_cost": new_total,
                "cost_difference": cost_difference,
                "new_cost_breakdown": new_cost_breakdown.to_dict(),
                "new_delivery_type": delivery_type,
                "recalculated_at": datetime.utcnow().isoformat()
            }
            
            return result
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to recalculate subscription: {str(e)}"
            )

    async def propagate_variant_price_changes(
        self,
        variant_id: UUID,
        old_price: 'Decimal',
        new_price: 'Decimal',
        admin_user_id: UUID = None
    ) -> List[Dict[str, Any]]:
        """
        Propagate variant price changes to all affected subscriptions.
        
        Args:
            variant_id: Variant that had price change
            old_price: Previous price
            new_price: New price
            admin_user_id: Admin making the change
            
        Returns:
            List of subscription updates
        """
        try:
            from decimal import Decimal
            
            # Find all subscriptions containing this variant
            subscriptions_result = await self.db.execute(
                select(Subscription).where(
                    and_(
                        Subscription.variant_ids.contains([str(variant_id)]),
                        Subscription.status.in_(["active", "paused"])
                    )
                )
            )
            subscriptions = subscriptions_result.scalars().all()
            
            updates = []
            
            for subscription in subscriptions:
                try:
                    # Recalculate subscription cost
                    variant_ids = [UUID(vid) for vid in subscription.variant_ids]
                    
                    new_cost_breakdown = await self.calculate_subscription_cost(
                        variant_ids=variant_ids,
                        delivery_type=subscription.delivery_type or "standard",
                        currency=subscription.currency or "USD",
                        user_id=subscription.user_id,
                        shipping_address_id=subscription.delivery_address_id
                    )
                    
                    # Calculate cost difference
                    old_total = subscription.cost_breakdown.get("total_amount", 0) if subscription.cost_breakdown else 0
                    new_total = float(new_cost_breakdown.total_amount)
                    cost_difference = new_total - old_total
                    
                    # Update subscription
                    subscription.cost_breakdown = new_cost_breakdown.to_dict()
                    subscription.price = new_total
                    subscription.updated_at = datetime.utcnow()
                    
                    # Create cost history record
                    await self._create_cost_history_record(
                        subscription_id=subscription.id,
                        old_cost=old_total,
                        new_cost=new_total,
                        change_reason="variant_price_change",
                        change_details={
                            "variant_id": str(variant_id),
                            "old_variant_price": float(old_price),
                            "new_variant_price": float(new_price),
                            "admin_user_id": str(admin_user_id) if admin_user_id else None
                        }
                    )
                    
                    updates.append({
                        "subscription_id": str(subscription.id),
                        "user_id": str(subscription.user_id),
                        "old_cost": old_total,
                        "new_cost": new_total,
                        "cost_difference": cost_difference,
                        "status": "updated"
                    })
                    
                except Exception as e:
                    updates.append({
                        "subscription_id": str(subscription.id),
                        "user_id": str(subscription.user_id),
                        "status": "failed",
                        "error": str(e)
                    })
            
            await self.db.commit()
            
            return updates
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to propagate price changes: {str(e)}"
            )

    # --- Helper Methods ---
    async def _get_subscription_by_id(self, subscription_id: UUID):
        """Get subscription by ID"""
        query = select(Subscription).where(Subscription.id == subscription_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def _create_cost_history_record(
        self,
        subscription_id: UUID,
        old_cost: float,
        new_cost: float,
        change_reason: str,
        change_details: Dict[str, Any]
    ) -> None:
        """Create a cost history record for audit purposes"""
        try:
            from models.admin import SubscriptionCostHistory
            
            history_record = SubscriptionCostHistory(
                subscription_id=subscription_id,
                old_cost=old_cost,
                new_cost=new_cost,
                cost_difference=new_cost - old_cost,
                change_reason=change_reason,
                change_details=change_details,
                created_at=datetime.utcnow()
            )
            
            self.db.add(history_record)
            # Note: commit is handled by calling method
            
        except Exception as e:
            # Log error but don't fail the main operation
            pass

    async def _convert_currency(self, amount: 'Decimal', from_currency: str, to_currency: str) -> 'Decimal':
        """Convert currency using exchange rates"""
        if from_currency == to_currency:
            return amount
        
        # Mock currency conversion - in real implementation would use actual exchange rates
        conversion_rates = {
            ("USD", "EUR"): 0.85,
            ("USD", "GBP"): 0.75,
            ("EUR", "USD"): 1.18,
            ("GBP", "USD"): 1.33
        }
        
        rate = conversion_rates.get((from_currency, to_currency), 1.0)
        return amount * Decimal(str(rate))


class CostBreakdown:
    """Data class for subscription cost breakdown"""
    
    def __init__(
        self,
        variant_costs: List[Dict[str, Any]],
        subtotal: 'Decimal',
        admin_percentage: float,
        admin_fee: 'Decimal',
        delivery_type: str,
        delivery_cost: 'Decimal',
        tax_rate: float,
        tax_amount: 'Decimal',
        loyalty_discount: 'Decimal' = None,
        total_amount: 'Decimal' = None,
        currency: str = "USD",
        breakdown_timestamp: datetime = None
    ):
        from decimal import Decimal
        
        self.variant_costs = variant_costs
        self.subtotal = subtotal
        self.admin_percentage = admin_percentage
        self.admin_fee = admin_fee
        self.delivery_type = delivery_type
        self.delivery_cost = delivery_cost
        self.tax_rate = tax_rate
        self.tax_amount = tax_amount
        self.loyalty_discount = loyalty_discount or Decimal('0')
        self.total_amount = total_amount or (subtotal + admin_fee + delivery_cost + tax_amount - self.loyalty_discount)
        self.currency = currency
        self.breakdown_timestamp = breakdown_timestamp or datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert cost breakdown to dictionary"""
        return {
            "variant_costs": self.variant_costs,
            "subtotal": float(self.subtotal),
            "admin_percentage": self.admin_percentage,
            "admin_fee": float(self.admin_fee),
            "delivery_type": self.delivery_type,
            "delivery_cost": float(self.delivery_cost),
            "tax_rate": self.tax_rate,
            "tax_amount": float(self.tax_amount),
            "loyalty_discount": float(self.loyalty_discount),
            "total_amount": float(self.total_amount),
            "currency": self.currency,
            "breakdown_timestamp": self.breakdown_timestamp.isoformat() if self.breakdown_timestamp else None
        }