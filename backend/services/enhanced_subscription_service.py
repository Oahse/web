"""
Enhanced Subscription Service for subscription product management
Implements remove_product, apply_discount, and calculate_totals methods with atomic transactions
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, delete
from sqlalchemy.orm import selectinload
from fastapi import HTTPException
from models.subscriptions import Subscription, SubscriptionProduct
from models.discounts import Discount, SubscriptionDiscount
from models.validation_rules import TaxValidationRule, ShippingValidationRule
from models.user import User
from models.product import Product, ProductVariant
from services.validation_service import ValidationService
from services.transaction_service import TransactionService, transactional, TransactionError
from uuid import UUID
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


class EnhancedSubscriptionService:
    """Enhanced subscription service with product management and discount functionality"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.validation_service = ValidationService(db)
        self.transaction_service = TransactionService(db)

    @transactional(isolation_level="REPEATABLE READ", max_retries=2)
    async def remove_product(
        self,
        subscription_id: UUID,
        product_id: UUID,
        user_id: UUID,
        reason: Optional[str] = None
    ) -> Subscription:
        """
        Remove a product from a subscription with validation and total recalculation
        Uses atomic transactions with rollback capability
        Requirements: 1.1, 1.2, 1.4, 3.1, 7.5
        """
        try:
            # Get subscription and verify ownership
            subscription_result = await self.db.execute(
                select(Subscription).where(
                    and_(
                        Subscription.id == subscription_id,
                        Subscription.user_id == user_id
                    )
                ).options(selectinload(Subscription.subscription_products))
            )
            subscription = subscription_result.scalar_one_or_none()
            
            if not subscription:
                raise HTTPException(status_code=404, detail="Subscription not found")
            
            if subscription.status not in ["active", "paused"]:
                raise HTTPException(status_code=400, detail="Cannot modify inactive subscription")
            
            # Store original state for potential rollback
            original_subscription_state = {
                "subtotal": subscription.subtotal,
                "total": subscription.total,
                "tax_amount": subscription.tax_amount,
                "shipping_cost": subscription.shipping_cost,
                "discount_amount": subscription.discount_amount
            }
            
            # Find the subscription product to remove
            subscription_product = None
            for sp in subscription.subscription_products:
                if sp.product_id == product_id and sp.is_active:
                    subscription_product = sp
                    break
            
            if not subscription_product:
                raise HTTPException(status_code=404, detail="Product not found in subscription")
            
            # Store original product state for rollback
            original_product_state = {
                "removed_at": subscription_product.removed_at,
                "removed_by": subscription_product.removed_by
            }
            
            # Check if this is the last product
            active_products = [sp for sp in subscription.subscription_products if sp.is_active]
            if len(active_products) <= 1:
                raise HTTPException(
                    status_code=400, 
                    detail="Cannot remove the last product from subscription. Cancel subscription instead."
                )
            
            # Mark product as removed (soft delete)
            subscription_product.removed_at = datetime.utcnow()
            subscription_product.removed_by = user_id
            
            # Create audit trail
            from models.discounts import ProductRemovalAudit
            audit = ProductRemovalAudit(
                subscription_id=subscription_id,
                product_id=product_id,
                removed_by=user_id,
                reason=reason or "User requested removal"
            )
            self.db.add(audit)
            
            # Recalculate subscription totals
            await self._recalculate_subscription_totals(subscription)
            
            # Flush changes to get updated values but don't commit yet
            await self.db.flush()
            await self.db.refresh(subscription)
            
            logger.info(f"Removed product {product_id} from subscription {subscription_id}")
            return subscription
            
        except HTTPException:
            # Re-raise HTTP exceptions without wrapping
            raise
        except Exception as e:
            logger.error(f"Failed to remove product {product_id} from subscription {subscription_id}: {e}")
            raise TransactionError(
                f"Product removal failed: {e}",
                original_error=e,
                rollback_data={
                    "subscription_id": str(subscription_id),
                    "product_id": str(product_id),
                    "original_subscription_state": original_subscription_state,
                    "original_product_state": original_product_state
                }
            )

    @transactional(isolation_level="READ COMMITTED", max_retries=1)
    async def apply_discount(
        self,
        subscription_id: UUID,
        discount_code: str,
        user_id: UUID
    ) -> Dict[str, Any]:
        """
        Apply a discount to a subscription with validation and calculation
        Uses atomic transactions with rollback capability
        Requirements: 3.1, 3.2, 3.5, 7.5
        """
        try:
            # Get subscription and verify ownership
            subscription_result = await self.db.execute(
                select(Subscription).where(
                    and_(
                        Subscription.id == subscription_id,
                        Subscription.user_id == user_id
                    )
                ).options(selectinload(Subscription.applied_discounts))
            )
            subscription = subscription_result.scalar_one_or_none()
            
            if not subscription:
                raise HTTPException(status_code=404, detail="Subscription not found")
            
            if subscription.status not in ["active", "paused"]:
                raise HTTPException(status_code=400, detail="Cannot apply discount to inactive subscription")
            
            # Store original state for rollback
            original_state = {
                "total": subscription.total,
                "discount_amount": subscription.discount_amount,
                "applied_discounts": [ad.id for ad in subscription.applied_discounts]
            }
            
            # Find and validate discount
            discount_result = await self.db.execute(
                select(Discount).where(
                    and_(
                        Discount.code == discount_code,
                        Discount.is_active == True
                    )
                )
            )
            discount = discount_result.scalar_one_or_none()
            
            if not discount:
                raise HTTPException(status_code=404, detail="Invalid discount code")
            
            if not discount.is_valid():
                raise HTTPException(status_code=400, detail="Discount code has expired or reached usage limit")
            
            # Check if discount is already applied
            existing_discount = None
            for applied_discount in subscription.applied_discounts:
                if applied_discount.discount_id == discount.id:
                    existing_discount = applied_discount
                    break
            
            if existing_discount:
                raise HTTPException(status_code=400, detail="Discount already applied to this subscription")
            
            # Calculate discount amount
            subtotal = subscription.subtotal or 0.0
            discount_amount = discount.calculate_discount_amount(subtotal)
            
            if discount_amount <= 0:
                raise HTTPException(
                    status_code=400, 
                    detail="Discount does not apply to this subscription (minimum amount not met)"
                )
            
            # Store removed discounts for rollback
            removed_discounts = []
            
            # Check for optimal discount selection (remove less beneficial discounts)
            current_discounts = subscription.applied_discounts
            if current_discounts:
                total_current_discount = sum(ad.discount_amount for ad in current_discounts)
                if discount_amount > total_current_discount:
                    # Remove existing discounts as this one is better
                    for existing in current_discounts:
                        removed_discounts.append({
                            "id": existing.id,
                            "discount_id": existing.discount_id,
                            "discount_amount": existing.discount_amount
                        })
                        await self.db.delete(existing)
                        # Decrement usage count of removed discount
                        removed_discount_result = await self.db.execute(
                            select(Discount).where(Discount.id == existing.discount_id)
                        )
                        removed_discount = removed_discount_result.scalar_one_or_none()
                        if removed_discount:
                            removed_discount.used_count = max(0, removed_discount.used_count - 1)
                else:
                    raise HTTPException(
                        status_code=400,
                        detail="A better discount is already applied to this subscription"
                    )
            
            # Apply the discount
            subscription_discount = SubscriptionDiscount(
                subscription_id=subscription_id,
                discount_id=discount.id,
                discount_amount=discount_amount
            )
            self.db.add(subscription_discount)
            
            # Update discount usage count
            original_usage_count = discount.used_count
            discount.used_count += 1
            
            # Recalculate subscription totals
            await self._recalculate_subscription_totals(subscription)
            
            # Flush changes to get updated values but don't commit yet
            await self.db.flush()
            
            logger.info(f"Applied discount {discount_code} to subscription {subscription_id}")
            
            return {
                "discount_code": discount_code,
                "discount_amount": discount_amount,
                "discount_type": discount.type,
                "new_total": subscription.total,
                "applied_at": datetime.utcnow().isoformat()
            }
            
        except HTTPException:
            # Re-raise HTTP exceptions without wrapping
            raise
        except Exception as e:
            logger.error(f"Failed to apply discount {discount_code} to subscription {subscription_id}: {e}")
            raise TransactionError(
                f"Discount application failed: {e}",
                original_error=e,
                rollback_data={
                    "subscription_id": str(subscription_id),
                    "discount_code": discount_code,
                    "original_state": original_state,
                    "removed_discounts": removed_discounts,
                    "original_usage_count": original_usage_count
                }
            )

    async def calculate_totals(
        self,
        subscription: Subscription,
        validate_amounts: bool = True
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive subscription totals with validation
        Requirements: 1.1, 1.2, 1.4, 3.1
        """
        # Get active subscription products
        active_products_result = await self.db.execute(
            select(SubscriptionProduct).where(
                and_(
                    SubscriptionProduct.subscription_id == subscription.id,
                    SubscriptionProduct.removed_at.is_(None)
                )
            ).options(selectinload(SubscriptionProduct.product))
        )
        active_products = active_products_result.scalars().all()
        
        if not active_products:
            raise HTTPException(status_code=400, detail="No active products in subscription")
        
        # Calculate subtotal
        subtotal = Decimal('0.00')
        for product in active_products:
            subtotal += Decimal(str(product.total_price))
        
        # Get shipping cost (use existing or calculate)
        shipping_cost = Decimal(str(subscription.shipping_cost or 0.0))
        
        # Validate shipping cost if needed
        if validate_amounts and shipping_cost == 0:
            shipping_cost = await self.validation_service.validate_shipping_amount(
                amount=shipping_cost,
                products=active_products,
                location_code=self._get_location_code_from_subscription(subscription)
            )
        
        # Calculate tax
        tax_rate = Decimal(str(subscription.tax_rate or 0.0))
        tax_amount = subtotal * tax_rate
        
        # Validate tax amount if needed
        if validate_amounts and tax_amount == 0 and tax_rate > 0:
            tax_amount = await self.validation_service.validate_tax_amount(
                amount=tax_amount,
                location_code=self._get_location_code_from_subscription(subscription),
                subtotal=subtotal
            )
        
        # Get applied discounts
        discounts_result = await self.db.execute(
            select(SubscriptionDiscount).where(
                SubscriptionDiscount.subscription_id == subscription.id
            )
        )
        applied_discounts = discounts_result.scalars().all()
        
        total_discount = sum(Decimal(str(ad.discount_amount)) for ad in applied_discounts)
        
        # Calculate final total (ensure non-negative)
        total = max(Decimal('0.00'), subtotal + shipping_cost + tax_amount - total_discount)
        
        # Update subscription fields
        subscription.subtotal = float(subtotal)
        subscription.shipping_cost = float(shipping_cost)
        subscription.tax_amount = float(tax_amount)
        subscription.discount_amount = float(total_discount)
        subscription.total = float(total)
        
        # Update validation timestamps if validation was performed
        if validate_amounts:
            now = datetime.utcnow()
            if shipping_cost > 0:
                subscription.shipping_validated_at = now
            if tax_amount > 0:
                subscription.tax_validated_at = now
        
        return {
            "subtotal": float(subtotal),
            "shipping_cost": float(shipping_cost),
            "tax_amount": float(tax_amount),
            "tax_rate": float(tax_rate),
            "discount_amount": float(total_discount),
            "total": float(total),
            "currency": subscription.currency or "USD",
            "calculated_at": datetime.utcnow().isoformat()
        }

    async def _recalculate_subscription_totals(self, subscription: Subscription) -> None:
        """Recalculate and update subscription totals"""
        totals = await self.calculate_totals(subscription, validate_amounts=True)
        # Totals are already updated in calculate_totals method
        logger.info(f"Recalculated totals for subscription {subscription.id}: {totals['total']}")

    def _get_location_code_from_subscription(self, subscription: Subscription) -> str:
        """Extract location code from subscription for tax validation"""
        # This would typically come from the user's address
        # For now, return a default location code
        return "US-CA"  # Default to California, US

    @transactional(isolation_level="READ COMMITTED")
    async def remove_discount(
        self,
        subscription_id: UUID,
        discount_id: UUID,
        user_id: UUID
    ) -> Subscription:
        """Remove a discount from a subscription with atomic transaction"""
        try:
            # Get subscription and verify ownership
            subscription_result = await self.db.execute(
                select(Subscription).where(
                    and_(
                        Subscription.id == subscription_id,
                        Subscription.user_id == user_id
                    )
                )
            )
            subscription = subscription_result.scalar_one_or_none()
            
            if not subscription:
                raise HTTPException(status_code=404, detail="Subscription not found")
            
            # Store original state for rollback
            original_state = {
                "total": subscription.total,
                "discount_amount": subscription.discount_amount
            }
            
            # Find and remove the discount
            discount_result = await self.db.execute(
                select(SubscriptionDiscount).where(
                    and_(
                        SubscriptionDiscount.subscription_id == subscription_id,
                        SubscriptionDiscount.discount_id == discount_id
                    )
                )
            )
            subscription_discount = discount_result.scalar_one_or_none()
            
            if not subscription_discount:
                raise HTTPException(status_code=404, detail="Discount not applied to this subscription")
            
            # Store discount info for rollback
            discount_info = {
                "id": subscription_discount.id,
                "discount_amount": subscription_discount.discount_amount
            }
            
            # Remove the discount
            await self.db.delete(subscription_discount)
            
            # Decrement usage count
            discount_result = await self.db.execute(
                select(Discount).where(Discount.id == discount_id)
            )
            discount = discount_result.scalar_one_or_none()
            original_usage_count = None
            if discount:
                original_usage_count = discount.used_count
                discount.used_count = max(0, discount.used_count - 1)
            
            # Recalculate totals
            await self._recalculate_subscription_totals(subscription)
            
            # Flush changes but don't commit yet (handled by decorator)
            await self.db.flush()
            await self.db.refresh(subscription)
            
            logger.info(f"Removed discount {discount_id} from subscription {subscription_id}")
            return subscription
            
        except HTTPException:
            # Re-raise HTTP exceptions without wrapping
            raise
        except Exception as e:
            logger.error(f"Failed to remove discount {discount_id} from subscription {subscription_id}: {e}")
            raise TransactionError(
                f"Discount removal failed: {e}",
                original_error=e,
                rollback_data={
                    "subscription_id": str(subscription_id),
                    "discount_id": str(discount_id),
                    "original_state": original_state,
                    "discount_info": discount_info,
                    "original_usage_count": original_usage_count
                }
            )

    async def get_subscription_details(
        self,
        subscription_id: UUID,
        user_id: UUID
    ) -> Dict[str, Any]:
        """Get detailed subscription information for modal display"""
        # Get subscription with all related data
        subscription_result = await self.db.execute(
            select(Subscription).where(
                and_(
                    Subscription.id == subscription_id,
                    Subscription.user_id == user_id
                )
            ).options(
                selectinload(Subscription.subscription_products).selectinload(SubscriptionProduct.product),
                selectinload(Subscription.applied_discounts).selectinload(SubscriptionDiscount.discount)
            )
        )
        subscription = subscription_result.scalar_one_or_none()
        
        if not subscription:
            raise HTTPException(status_code=404, detail="Subscription not found")
        
        # Get active products
        active_products = [
            {
                "id": str(sp.product_id),
                "name": sp.product.name if sp.product else "Unknown Product",
                "quantity": sp.quantity,
                "unit_price": sp.unit_price,
                "total_price": sp.total_price,
                "added_at": sp.added_at.isoformat() if sp.added_at else None
            }
            for sp in subscription.subscription_products
            if sp.is_active
        ]
        
        # Get applied discounts
        applied_discounts = [
            {
                "id": str(ad.discount_id),
                "code": ad.discount.code if ad.discount else "Unknown",
                "discount_amount": ad.discount_amount,
                "applied_at": ad.applied_at.isoformat() if ad.applied_at else None
            }
            for ad in subscription.applied_discounts
        ]
        
        return {
            "subscription": subscription.to_dict(),
            "products": active_products,
            "discounts": applied_discounts,
            "totals": {
                "subtotal": subscription.subtotal,
                "shipping_cost": subscription.shipping_cost,
                "tax_amount": subscription.tax_amount,
                "discount_amount": subscription.discount_amount,
                "total": subscription.total
            }
        }