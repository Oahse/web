# Consolidated admin service
# This file includes all admin-related functionality including pricing and analytics

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.orm import selectinload
from fastapi import HTTPException
from models.admin import PricingConfig, SubscriptionCostHistory, SubscriptionAnalytics, PaymentAnalytics
from models.user import User
from models.subscriptions import Subscription
from models.payments import Transaction
from uuid import UUID
from datetime import datetime, timedelta, date
from typing import Optional, List, Dict, Any
from decimal import Decimal


class AdminService:
    """Consolidated admin service with comprehensive admin functionality"""
    
    def __init__(self, db: AsyncSession):
        self.db = db

    # --- Pricing Configuration Management ---
    async def create_pricing_config(
        self,
        admin_user_id: UUID,
        subscription_percentage: float,
        delivery_costs: Dict[str, float],
        tax_rates: Dict[str, float],
        currency_settings: Dict[str, Any],
        change_reason: Optional[str] = None
    ) -> PricingConfig:
        """Create a new pricing configuration"""
        
        # Deactivate current active config
        await self.db.execute(
            select(PricingConfig).where(PricingConfig.is_active == "active").update({"is_active": "inactive"})
        )
        
        # Create new config
        config = PricingConfig(
            subscription_percentage=subscription_percentage,
            delivery_costs=delivery_costs,
            tax_rates=tax_rates,
            currency_settings=currency_settings,
            updated_by=admin_user_id,
            version="1.0",
            is_active="active",
            change_reason=change_reason
        )
        
        self.db.add(config)
        await self.db.commit()
        await self.db.refresh(config)
        
        return config

    async def get_active_pricing_config(self) -> Optional[PricingConfig]:
        """Get the currently active pricing configuration"""
        result = await self.db.execute(
            select(PricingConfig).where(PricingConfig.is_active == "active").order_by(desc(PricingConfig.created_at))
        )
        return result.scalar_one_or_none()

    async def get_pricing_config_history(
        self,
        page: int = 1,
        limit: int = 20
    ) -> Dict[str, Any]:
        """Get pricing configuration history"""
        offset = (page - 1) * limit
        
        query = select(PricingConfig).order_by(desc(PricingConfig.created_at)).offset(offset).limit(limit)
        result = await self.db.execute(query)
        configs = result.scalars().all()
        
        # Get total count
        total = await self.db.scalar(select(func.count(PricingConfig.id)))
        
        return {
            "configs": [config.to_dict() for config in configs],
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "pages": (total + limit - 1) // limit
            }
        }

    async def update_pricing_config(
        self,
        admin_user_id: UUID,
        subscription_percentage: Optional[float] = None,
        delivery_costs: Optional[Dict[str, float]] = None,
        tax_rates: Optional[Dict[str, float]] = None,
        currency_settings: Optional[Dict[str, Any]] = None,
        change_reason: Optional[str] = None
    ) -> PricingConfig:
        """Update the active pricing configuration"""
        
        current_config = await self.get_active_pricing_config()
        if not current_config:
            raise HTTPException(status_code=404, detail="No active pricing configuration found")
        
        # Create new version with updated values
        new_config = PricingConfig(
            subscription_percentage=subscription_percentage or current_config.subscription_percentage,
            delivery_costs=delivery_costs or current_config.delivery_costs,
            tax_rates=tax_rates or current_config.tax_rates,
            currency_settings=currency_settings or current_config.currency_settings,
            updated_by=admin_user_id,
            version=f"{float(current_config.version) + 0.1:.1f}",
            is_active="active",
            change_reason=change_reason
        )
        
        # Deactivate current config
        current_config.is_active = "inactive"
        
        self.db.add(new_config)
        await self.db.commit()
        await self.db.refresh(new_config)
        
        return new_config

    # --- Subscription Cost History ---
    async def log_subscription_cost_change(
        self,
        subscription_id: UUID,
        old_cost_breakdown: Optional[Dict[str, Any]],
        new_cost_breakdown: Dict[str, Any],
        change_reason: str,
        changed_by: Optional[UUID] = None,
        effective_date: Optional[datetime] = None
    ) -> SubscriptionCostHistory:
        """Log a subscription cost change"""
        
        history = SubscriptionCostHistory(
            subscription_id=subscription_id,
            old_cost_breakdown=old_cost_breakdown,
            new_cost_breakdown=new_cost_breakdown,
            change_reason=change_reason,
            effective_date=effective_date or datetime.utcnow(),
            changed_by=changed_by
        )
        
        self.db.add(history)
        await self.db.commit()
        await self.db.refresh(history)
        
        return history

    async def get_subscription_cost_history(
        self,
        subscription_id: UUID,
        page: int = 1,
        limit: int = 20
    ) -> Dict[str, Any]:
        """Get cost history for a subscription"""
        offset = (page - 1) * limit
        
        query = select(SubscriptionCostHistory).where(
            SubscriptionCostHistory.subscription_id == subscription_id
        ).order_by(desc(SubscriptionCostHistory.created_at)).offset(offset).limit(limit)
        
        result = await self.db.execute(query)
        history = result.scalars().all()
        
        # Get total count
        total = await self.db.scalar(
            select(func.count(SubscriptionCostHistory.id)).where(
                SubscriptionCostHistory.subscription_id == subscription_id
            )
        )
        
        return {
            "history": [h.to_dict() for h in history],
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "pages": (total + limit - 1) // limit
            }
        }

    # --- Analytics Management ---
    async def generate_subscription_analytics(
        self,
        target_date: date,
        force_regenerate: bool = False
    ) -> SubscriptionAnalytics:
        """Generate subscription analytics for a specific date"""
        
        # Check if analytics already exist for this date
        existing = await self.db.scalar(
            select(SubscriptionAnalytics).where(SubscriptionAnalytics.date == target_date)
        )
        
        if existing and not force_regenerate:
            return existing
        
        # Calculate analytics
        start_of_day = datetime.combine(target_date, datetime.min.time())
        end_of_day = datetime.combine(target_date, datetime.max.time())
        
        # Get all subscriptions
        all_subscriptions = await self.db.execute(
            select(Subscription).where(Subscription.created_at <= end_of_day)
        )
        all_subs = all_subscriptions.scalars().all()
        
        # Calculate metrics
        total_active = len([s for s in all_subs if s.status == "active"])
        new_subscriptions = len([s for s in all_subs if s.created_at.date() == target_date])
        canceled_subscriptions = len([s for s in all_subs if s.cancelled_at and s.cancelled_at.date() == target_date])
        paused_subscriptions = len([s for s in all_subs if s.status == "paused"])
        
        # Revenue calculations
        active_subs = [s for s in all_subs if s.status == "active"]
        total_revenue = sum(s.price or 0 for s in active_subs)
        average_subscription_value = total_revenue / len(active_subs) if active_subs else 0
        
        # Create or update analytics record
        if existing:
            analytics = existing
        else:
            analytics = SubscriptionAnalytics(date=target_date)
        
        analytics.total_active_subscriptions = total_active
        analytics.new_subscriptions = new_subscriptions
        analytics.canceled_subscriptions = canceled_subscriptions
        analytics.paused_subscriptions = paused_subscriptions
        analytics.total_revenue = total_revenue
        analytics.average_subscription_value = average_subscription_value
        analytics.monthly_recurring_revenue = total_revenue  # Simplified
        
        # Calculate rates
        if total_active > 0:
            analytics.churn_rate = (canceled_subscriptions / total_active) * 100
            analytics.retention_rate = 100 - analytics.churn_rate
        
        if not existing:
            self.db.add(analytics)
        
        await self.db.commit()
        await self.db.refresh(analytics)
        
        return analytics

    async def generate_payment_analytics(
        self,
        target_date: date,
        force_regenerate: bool = False
    ) -> PaymentAnalytics:
        """Generate payment analytics for a specific date"""
        
        # Check if analytics already exist for this date
        existing = await self.db.scalar(
            select(PaymentAnalytics).where(PaymentAnalytics.date == target_date)
        )
        
        if existing and not force_regenerate:
            return existing
        
        # Calculate analytics
        start_of_day = datetime.combine(target_date, datetime.min.time())
        end_of_day = datetime.combine(target_date, datetime.max.time())
        
        # Get transactions for the day
        transactions_result = await self.db.execute(
            select(Transaction).where(
                and_(
                    Transaction.created_at >= start_of_day,
                    Transaction.created_at <= end_of_day,
                    Transaction.transaction_type == "payment"
                )
            )
        )
        transactions = transactions_result.scalars().all()
        
        # Calculate metrics
        total_payments = len(transactions)
        successful_payments = len([t for t in transactions if t.status == "succeeded"])
        failed_payments = len([t for t in transactions if t.status == "failed"])
        pending_payments = len([t for t in transactions if t.status == "pending"])
        
        success_rate = (successful_payments / total_payments * 100) if total_payments > 0 else 0
        
        # Volume calculations
        successful_txns = [t for t in transactions if t.status == "succeeded"]
        total_volume = sum(t.amount for t in transactions)
        successful_volume = sum(t.amount for t in successful_txns)
        average_payment_amount = successful_volume / len(successful_txns) if successful_txns else 0
        
        # Create or update analytics record
        if existing:
            analytics = existing
        else:
            analytics = PaymentAnalytics(date=target_date)
        
        analytics.total_payments = total_payments
        analytics.successful_payments = successful_payments
        analytics.failed_payments = failed_payments
        analytics.pending_payments = pending_payments
        analytics.success_rate = success_rate
        analytics.total_volume = total_volume
        analytics.successful_volume = successful_volume
        analytics.average_payment_amount = average_payment_amount
        
        if not existing:
            self.db.add(analytics)
        
        await self.db.commit()
        await self.db.refresh(analytics)
        
        return analytics

    async def get_analytics_dashboard(
        self,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """Get comprehensive analytics dashboard data"""
        
        # Get subscription analytics
        sub_analytics_result = await self.db.execute(
            select(SubscriptionAnalytics).where(
                and_(
                    SubscriptionAnalytics.date >= start_date,
                    SubscriptionAnalytics.date <= end_date
                )
            ).order_by(SubscriptionAnalytics.date)
        )
        sub_analytics = sub_analytics_result.scalars().all()
        
        # Get payment analytics
        payment_analytics_result = await self.db.execute(
            select(PaymentAnalytics).where(
                and_(
                    PaymentAnalytics.date >= start_date,
                    PaymentAnalytics.date <= end_date
                )
            ).order_by(PaymentAnalytics.date)
        )
        payment_analytics = payment_analytics_result.scalars().all()
        
        # Calculate summary metrics
        total_revenue = sum(sa.total_revenue for sa in sub_analytics)
        total_active_subscriptions = sub_analytics[-1].total_active_subscriptions if sub_analytics else 0
        average_success_rate = sum(pa.success_rate for pa in payment_analytics) / len(payment_analytics) if payment_analytics else 0
        
        return {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "summary": {
                "total_revenue": total_revenue,
                "total_active_subscriptions": total_active_subscriptions,
                "average_payment_success_rate": round(average_success_rate, 2),
                "total_days": len(sub_analytics)
            },
            "subscription_analytics": [sa.to_dict() for sa in sub_analytics],
            "payment_analytics": [pa.to_dict() for pa in payment_analytics]
        }

    # --- User Management ---
    async def get_all_users(
        self,
        page: int = 1,
        limit: int = 20,
        search: Optional[str] = None,
        role_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get all users with pagination and filtering"""
        offset = (page - 1) * limit
        
        query = select(User)
        count_query = select(func.count(User.id))
        
        conditions = []
        if search:
            conditions.append(
                or_(
                    User.email.ilike(f"%{search}%"),
                    User.firstname.ilike(f"%{search}%"),
                    User.lastname.ilike(f"%{search}%")
                )
            )
        
        if role_filter:
            conditions.append(User.role == role_filter)
        
        if conditions:
            query = query.where(and_(*conditions))
            count_query = count_query.where(and_(*conditions))
        
        query = query.order_by(desc(User.created_at)).offset(offset).limit(limit)
        
        result = await self.db.execute(query)
        users = result.scalars().all()
        
        total = await self.db.scalar(count_query)
        
        return {
            "users": [
                {
                    "id": str(user.id),
                    "email": user.email,
                    "firstname": user.firstname,
                    "lastname": user.lastname,
                    "role": user.role,
                    "is_active": user.is_active,
                    "created_at": user.created_at.isoformat() if user.created_at else None,
                    "last_login": user.last_login.isoformat() if user.last_login else None
                }
                for user in users
            ],
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "pages": (total + limit - 1) // limit
            }
        }

    async def update_user_role(
        self,
        user_id: UUID,
        new_role: str,
        admin_user_id: UUID
    ) -> User:
        """Update a user's role"""
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        old_role = user.role
        user.role = new_role
        
        await self.db.commit()
        await self.db.refresh(user)
        
        # Log the role change (you might want to create an audit log model)
        # For now, we'll just return the updated user
        
        return user

    async def deactivate_user(
        self,
        user_id: UUID,
        admin_user_id: UUID
    ) -> User:
        """Deactivate a user account"""
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        user.is_active = False
        
        await self.db.commit()
        await self.db.refresh(user)
        
        return user

    # --- Dynamic Cost Recalculation (moved from separate service) ---
    async def handle_real_time_variant_change(
        self,
        subscription_id: UUID,
        variant_changes: Dict[str, List[UUID]],
        user_id: UUID = None,
        notify_user: bool = True
    ) -> Dict[str, Any]:
        """
        Handle real-time recalculation when variants are added/removed from subscription.
        
        Args:
            subscription_id: Subscription ID to update
            variant_changes: Dict with 'added' and 'removed' variant ID lists
            user_id: User ID for authorization
            notify_user: Whether to send notification to user
            
        Returns:
            Dictionary with recalculation results and notification status
        """
        try:
            from services.subscriptions import SubscriptionService
            
            added_variants = variant_changes.get('added', [])
            removed_variants = variant_changes.get('removed', [])
            
            # Get subscription service for recalculation
            subscription_service = SubscriptionService(self.db)
            
            # Perform the recalculation
            recalc_result = await subscription_service.recalculate_subscription_on_variant_change(
                subscription_id=subscription_id,
                added_variant_ids=added_variants,
                removed_variant_ids=removed_variants,
                user_id=user_id
            )
            
            # Send real-time notification if requested
            notification_result = None
            if notify_user:
                notification_result = await self._send_cost_change_notification(
                    subscription_id=subscription_id,
                    cost_change_info=recalc_result,
                    change_type="variant_modification"
                )
            
            # Log the real-time change
            await self._log_real_time_change(
                subscription_id=subscription_id,
                change_type="variant_modification",
                change_details=variant_changes,
                cost_impact=recalc_result.get('cost_difference', 0)
            )
            
            result = {
                "recalculation": recalc_result,
                "notification": notification_result,
                "real_time_processing": {
                    "processed_at": datetime.utcnow().isoformat(),
                    "processing_time_ms": self._calculate_processing_time(),
                    "change_type": "variant_modification",
                    "immediate_effect": True
                }
            }
            
            return result
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail="Failed to process real-time variant change"
            )

    async def handle_real_time_delivery_change(
        self,
        subscription_id: UUID,
        delivery_changes: Dict[str, Any],
        user_id: UUID = None,
        notify_user: bool = True
    ) -> Dict[str, Any]:
        """
        Handle real-time recalculation when delivery preferences change.
        
        Args:
            subscription_id: Subscription ID to update
            delivery_changes: Dict with delivery type and address changes
            user_id: User ID for authorization
            notify_user: Whether to send notification to user
            
        Returns:
            Dictionary with recalculation results and notification status
        """
        try:
            from services.subscriptions import SubscriptionService
            
            new_delivery_type = delivery_changes.get('delivery_type')
            new_delivery_address_id = delivery_changes.get('delivery_address_id')
            
            # Get subscription service for recalculation
            subscription_service = SubscriptionService(self.db)
            
            # Perform the recalculation
            recalc_result = await subscription_service.recalculate_subscription_on_delivery_change(
                subscription_id=subscription_id,
                new_delivery_type=new_delivery_type,
                new_delivery_address_id=new_delivery_address_id,
                user_id=user_id
            )
            
            # Send real-time notification if requested
            notification_result = None
            if notify_user:
                notification_result = await self._send_cost_change_notification(
                    subscription_id=subscription_id,
                    cost_change_info=recalc_result,
                    change_type="delivery_modification"
                )
            
            # Log the real-time change
            await self._log_real_time_change(
                subscription_id=subscription_id,
                change_type="delivery_modification",
                change_details=delivery_changes,
                cost_impact=recalc_result.get('cost_difference', 0)
            )
            
            result = {
                "recalculation": recalc_result,
                "notification": notification_result,
                "real_time_processing": {
                    "processed_at": datetime.utcnow().isoformat(),
                    "processing_time_ms": self._calculate_processing_time(),
                    "change_type": "delivery_modification",
                    "immediate_effect": True
                }
            }
            
            return result
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail="Failed to process real-time delivery change"
            )

    async def propagate_price_changes_to_subscriptions(
        self,
        price_change_events: List[Dict[str, Any]],
        admin_user_id: UUID = None,
        batch_size: int = 50
    ) -> Dict[str, Any]:
        """
        Propagate multiple price changes to existing subscriptions in batches.
        
        Args:
            price_change_events: List of price change events
            admin_user_id: Admin user making the changes
            batch_size: Number of subscriptions to process per batch
            
        Returns:
            Dictionary with propagation results
        """
        try:
            from services.subscriptions import SubscriptionService
            
            total_affected_subscriptions = 0
            successful_updates = 0
            failed_updates = 0
            propagation_results = []
            
            subscription_service = SubscriptionService(self.db)
            
            for price_event in price_change_events:
                variant_id = UUID(price_event['variant_id'])
                old_price = Decimal(str(price_event['old_price']))
                new_price = Decimal(str(price_event['new_price']))
                
                try:
                    # Propagate this specific price change
                    updates = await subscription_service.propagate_variant_price_changes(
                        variant_id=variant_id,
                        old_price=old_price,
                        new_price=new_price,
                        admin_user_id=admin_user_id
                    )
                    
                    total_affected_subscriptions += len(updates)
                    successful_updates += len(updates)
                    
                    propagation_results.append({
                        "variant_id": str(variant_id),
                        "price_change": {
                            "old_price": float(old_price),
                            "new_price": float(new_price),
                            "difference": float(new_price - old_price)
                        },
                        "affected_subscriptions": len(updates),
                        "status": "success",
                        "updates": updates
                    })
                    
                except Exception as e:
                    failed_updates += 1
                    propagation_results.append({
                        "variant_id": str(variant_id),
                        "price_change": {
                            "old_price": float(old_price),
                            "new_price": float(new_price),
                            "difference": float(new_price - old_price)
                        },
                        "affected_subscriptions": 0,
                        "status": "failed",
                        "error": str(e)
                    })
            
            # Send batch notification to affected users
            if successful_updates > 0:
                await self._send_batch_price_change_notifications(propagation_results)
            
            result = {
                "propagation_summary": {
                    "total_price_changes": len(price_change_events),
                    "total_affected_subscriptions": total_affected_subscriptions,
                    "successful_updates": successful_updates,
                    "failed_updates": failed_updates,
                    "success_rate": (successful_updates / total_affected_subscriptions * 100) if total_affected_subscriptions > 0 else 0
                },
                "propagation_results": propagation_results,
                "processing_info": {
                    "processed_at": datetime.utcnow().isoformat(),
                    "batch_size": batch_size,
                    "admin_user_id": str(admin_user_id) if admin_user_id else None
                }
            }
            
            return result
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail="Failed to propagate price changes to subscriptions"
            )

    async def get_real_time_cost_preview(
        self,
        subscription_id: UUID,
        proposed_changes: Dict[str, Any],
        user_id: UUID = None
    ) -> Dict[str, Any]:
        """
        Get real-time cost preview for proposed subscription changes without applying them.
        
        Args:
            subscription_id: Subscription ID to preview changes for
            proposed_changes: Dictionary of proposed changes
            user_id: User ID for authorization
            
        Returns:
            Dictionary with cost preview information
        """
        try:
            from services.subscriptions import SubscriptionService
            
            # Get current subscription
            subscription = await self._get_subscription_by_id(subscription_id)
            if not subscription:
                raise HTTPException(status_code=404, detail="Subscription not found")
            
            # Verify user authorization if provided
            if user_id and subscription.user_id != user_id:
                raise HTTPException(status_code=403, detail="User not authorized for this subscription")
            
            # Get current cost breakdown
            current_cost = subscription.cost_breakdown or {}
            current_total = current_cost.get("total_amount", 0)
            
            # Calculate proposed cost based on changes
            variant_ids = subscription.variant_ids or []
            delivery_type = subscription.delivery_type or "standard"
            delivery_address_id = subscription.delivery_address_id
            
            # Apply proposed variant changes
            if 'variant_changes' in proposed_changes:
                variant_changes = proposed_changes['variant_changes']
                if 'added' in variant_changes:
                    for variant_id in variant_changes['added']:
                        if str(variant_id) not in variant_ids:
                            variant_ids.append(str(variant_id))
                if 'removed' in variant_changes:
                    for variant_id in variant_changes['removed']:
                        if str(variant_id) in variant_ids:
                            variant_ids.remove(str(variant_id))
            
            # Apply proposed delivery changes
            if 'delivery_type' in proposed_changes:
                delivery_type = proposed_changes['delivery_type']
            if 'delivery_address_id' in proposed_changes:
                delivery_address_id = proposed_changes['delivery_address_id']
            
            # Calculate new cost using subscription service
            if variant_ids:
                subscription_service = SubscriptionService(self.db)
                new_cost_breakdown = await subscription_service.calculate_subscription_cost(
                    variant_ids=[UUID(v_id) for v_id in variant_ids],
                    delivery_type=delivery_type,
                    currency=subscription.currency or "USD",
                    user_id=subscription.user_id,
                    shipping_address_id=delivery_address_id
                )
                
                new_total = float(new_cost_breakdown.total_amount)
                cost_difference = new_total - current_total
                percentage_change = self._calculate_percentage_change(current_total, new_total)
                
                preview = {
                    "subscription_id": str(subscription_id),
                    "current_cost": current_cost,
                    "proposed_cost": new_cost_breakdown.to_dict(),
                    "cost_comparison": {
                        "current_total": current_total,
                        "proposed_total": new_total,
                        "cost_difference": cost_difference,
                        "percentage_change": percentage_change,
                        "is_increase": cost_difference > 0,
                        "is_decrease": cost_difference < 0
                    },
                    "proposed_changes": proposed_changes,
                    "preview_generated_at": datetime.utcnow().isoformat(),
                    "preview_valid_for_minutes": 15
                }
            else:
                preview = {
                    "subscription_id": str(subscription_id),
                    "error": "No variants remaining after proposed changes",
                    "current_cost": current_cost,
                    "proposed_changes": proposed_changes
                }
            
            return preview
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail="Failed to generate cost preview"
            )

    # --- Helper Methods ---
    async def _send_cost_change_notification(
        self,
        subscription_id: UUID,
        cost_change_info: Dict[str, Any],
        change_type: str
    ) -> Dict[str, Any]:
        """Send real-time notification about cost changes"""
        try:
            # Mock notification result
            notification_result = {
                "notification_sent": True,
                "notification_type": "cost_change",
                "change_type": change_type,
                "cost_difference": cost_change_info.get('cost_difference', 0),
                "notification_channels": ["email", "websocket"],
                "sent_at": datetime.utcnow().isoformat()
            }
            
            return notification_result
            
        except Exception as e:
            return {
                "notification_sent": False,
                "error": str(e)
            }

    async def _send_batch_price_change_notifications(
        self,
        propagation_results: List[Dict[str, Any]]
    ) -> None:
        """Send batch notifications for price changes"""
        try:
            # Group notifications by user
            user_notifications = {}
            
            for result in propagation_results:
                if result.get('status') == 'success':
                    for update in result.get('updates', []):
                        user_id = update.get('user_id')
                        if user_id not in user_notifications:
                            user_notifications[user_id] = []
                        user_notifications[user_id].append({
                            "subscription_id": update.get('subscription_id'),
                            "cost_difference": update.get('cost_difference'),
                            "variant_id": result.get('variant_id')
                        })
            
            # Mock batch notification sending
            for user_id, notifications in user_notifications.items():
                pass  # Would send actual notifications here
            
        except Exception as e:
            pass  # Log error in real implementation

    async def _log_real_time_change(
        self,
        subscription_id: UUID,
        change_type: str,
        change_details: Dict[str, Any],
        cost_impact: float
    ) -> None:
        """Log real-time changes for audit purposes"""
        try:
            # Mock logging - would use structured logger in real implementation
            pass
        except Exception as e:
            pass

    async def _get_subscription_by_id(self, subscription_id: UUID):
        """Get subscription by ID"""
        from models.subscriptions import Subscription
        query = select(Subscription).where(Subscription.id == subscription_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    def _calculate_processing_time(self) -> int:
        """Calculate processing time in milliseconds (mock implementation)"""
        return 150  # Mock 150ms processing time

    def _calculate_percentage_change(self, old_value: float, new_value: float) -> float:
        """Calculate percentage change between two values"""
        if old_value == 0:
            return 100.0 if new_value > 0 else 0.0
        
        return ((new_value - old_value) / old_value) * 100