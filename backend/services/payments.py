# Consolidated payment service
# This file includes all payment-related functionality

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from fastapi import HTTPException
from models.payments import PaymentMethod, PaymentIntent, Transaction
from models.user import User
from uuid import UUID, uuid4
from datetime import datetime
from typing import Optional, List, Dict, Any
from core.config import settings
from core.kafka import get_kafka_producer_service
import stripe
import logging
import time

# Configure Stripe
stripe.api_key = getattr(settings, 'STRIPE_SECRET_KEY', '')

logger = logging.getLogger(__name__)


class PaymentService:
    """Consolidated payment service with comprehensive payment management"""
    
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_payment_method(
        self,
        user_id: UUID,
        stripe_payment_method_id: str,
        is_default: bool = False
    ) -> PaymentMethod:
        """Create a new payment method"""
        try:
            # Get payment method details from Stripe
            stripe_pm = stripe.PaymentMethod.retrieve(stripe_payment_method_id)
            
            # If this is set as default, unset other defaults
            if is_default:
                await self.db.execute(
                    select(PaymentMethod).where(
                        and_(PaymentMethod.user_id == user_id, PaymentMethod.is_default == True)
                    ).update({"is_default": False})
                )
            
            payment_method = PaymentMethod(
                user_id=user_id,
                type=stripe_pm.type,
                provider="stripe",
                stripe_payment_method_id=stripe_payment_method_id,
                is_default=is_default,
                is_active=True
            )
            
            # Set card-specific details if it's a card
            if stripe_pm.type == "card" and stripe_pm.card:
                payment_method.last_four = stripe_pm.card.last4
                payment_method.expiry_month = stripe_pm.card.exp_month
                payment_method.expiry_year = stripe_pm.card.exp_year
                payment_method.brand = stripe_pm.card.brand
            
            self.db.add(payment_method)
            await self.db.commit()
            await self.db.refresh(payment_method)
            
            return payment_method
            
        except stripe.error.StripeError as e:
            raise HTTPException(status_code=400, detail=f"Stripe error: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to create payment method: {str(e)}")

    async def get_user_payment_methods(self, user_id: UUID) -> List[PaymentMethod]:
        """Get all payment methods for a user"""
        result = await self.db.execute(
            select(PaymentMethod).where(
                and_(PaymentMethod.user_id == user_id, PaymentMethod.is_active == True)
            ).order_by(PaymentMethod.is_default.desc(), PaymentMethod.created_at.desc())
        )
        return result.scalars().all()

    async def delete_payment_method(self, payment_method_id: UUID, user_id: UUID) -> bool:
        """Delete a payment method"""
        result = await self.db.execute(
            select(PaymentMethod).where(
                and_(
                    PaymentMethod.id == payment_method_id,
                    PaymentMethod.user_id == user_id
                )
            )
        )
        payment_method = result.scalar_one_or_none()
        
        if not payment_method:
            raise HTTPException(status_code=404, detail="Payment method not found")
        
        try:
            # Detach from Stripe
            if payment_method.stripe_payment_method_id:
                stripe.PaymentMethod.detach(payment_method.stripe_payment_method_id)
            
            # Mark as inactive instead of deleting
            payment_method.is_active = False
            await self.db.commit()
            
            return True
            
        except stripe.error.StripeError as e:
            raise HTTPException(status_code=400, detail=f"Stripe error: {str(e)}")

    async def create_payment_intent(
        self,
        user_id: UUID,
        amount: float,
        currency: str = "USD",
        order_id: Optional[UUID] = None,
        subscription_id: Optional[UUID] = None,
        metadata: Dict[str, Any] = None,
        commit: bool = True
    ) -> PaymentIntent:
        """Create a payment intent with optional transaction control"""
        try:
            # Create Stripe payment intent
            stripe_intent = stripe.PaymentIntent.create(
                amount=int(amount * 100),  # Convert to cents
                currency=currency.lower(),
                metadata=metadata or {}
            )
            
            # Create our payment intent record
            payment_intent = PaymentIntent(
                stripe_payment_intent_id=stripe_intent.id,
                user_id=user_id,
                order_id=order_id,
                subscription_id=subscription_id,
                amount_breakdown={"total": amount, "currency": currency},
                currency=currency,
                status=stripe_intent.status,
                client_secret=stripe_intent.client_secret,
                payment_metadata=metadata
            )
            
            self.db.add(payment_intent)
            if commit:
                await self.db.commit()
                await self.db.refresh(payment_intent)
            
            return payment_intent
            
        except stripe.error.StripeError as e:
            raise HTTPException(status_code=400, detail=f"Stripe error: {str(e)}")

    async def confirm_payment_intent(
        self,
        payment_intent_id: UUID,
        payment_method_id: str,
        commit: bool = True
    ) -> PaymentIntent:
        """Confirm a payment intent with optional transaction control"""
        result = await self.db.execute(
            select(PaymentIntent).where(PaymentIntent.id == payment_intent_id)
        )
        payment_intent = result.scalar_one_or_none()
        
        if not payment_intent:
            raise HTTPException(status_code=404, detail="Payment intent not found")
        
        try:
            # Confirm with Stripe
            stripe_intent = stripe.PaymentIntent.confirm(
                payment_intent.stripe_payment_intent_id,
                payment_method=payment_method_id
            )
            
            # Update our record
            payment_intent.status = stripe_intent.status
            payment_intent.payment_method_id = payment_method_id
            
            if stripe_intent.status == "succeeded":
                payment_intent.confirmed_at = datetime.utcnow()
                
                # Create transaction record
                transaction = Transaction(
                    user_id=payment_intent.user_id,
                    order_id=payment_intent.order_id,
                    payment_intent_id=payment_intent.id,
                    stripe_payment_intent_id=payment_intent.stripe_payment_intent_id,
                    amount=payment_intent.amount_breakdown.get("total", 0),
                    currency=payment_intent.currency,
                    status="succeeded",
                    transaction_type="payment",
                    description="Payment processed successfully"
                )
                self.db.add(transaction)
                
                # Send Kafka notification for successful payment (only if committing)
                if commit:
                    await self._send_payment_notification(
                        payment_intent.user_id,
                        payment_intent.order_id,
                        "payment_succeeded",
                        {
                            "payment_intent_id": str(payment_intent.id),
                            "amount": payment_intent.amount_breakdown.get("total", 0),
                            "currency": payment_intent.currency
                        }
                    )
            
            elif stripe_intent.status == "requires_action":
                payment_intent.requires_action = True
                payment_intent.client_secret = stripe_intent.client_secret
            
            if commit:
                await self.db.commit()
                await self.db.refresh(payment_intent)
            
            return payment_intent
            
        except stripe.error.StripeError as e:
            payment_intent.status = "failed"
            payment_intent.failed_at = datetime.utcnow()
            payment_intent.failure_reason = str(e)
            if commit:
                await self.db.commit()
                
                # Send Kafka notification for failed payment
                await self._send_payment_notification(
                    payment_intent.user_id,
                    payment_intent.order_id,
                    "payment_failed",
                    {
                        "payment_intent_id": str(payment_intent.id),
                        "error": str(e)
                    }
                )
            
            raise HTTPException(status_code=400, detail=f"Payment failed: {str(e)}")

    async def process_payment(
        self,
        user_id: UUID,
        amount: float,
        payment_method_id: UUID,
        order_id: Optional[UUID] = None,
        subscription_id: Optional[UUID] = None,
        commit: bool = True
    ) -> Dict[str, Any]:
        """Process a payment with optional transaction control"""
        try:
            # Get payment method
            result = await self.db.execute(
                select(PaymentMethod).where(
                    and_(
                        PaymentMethod.id == payment_method_id,
                        PaymentMethod.user_id == user_id,
                        PaymentMethod.is_active == True
                    )
                )
            )
            payment_method = result.scalar_one_or_none()
            
            if not payment_method:
                raise HTTPException(status_code=404, detail="Payment method not found")
            
            # Create and confirm payment intent
            payment_intent = await self.create_payment_intent(
                user_id=user_id,
                amount=amount,
                order_id=order_id,
                subscription_id=subscription_id,
                commit=commit
            )
            
            confirmed_intent = await self.confirm_payment_intent(
                payment_intent.id,
                payment_method.stripe_payment_method_id,
                commit=commit
            )
            
            return {
                "status": confirmed_intent.status,
                "payment_intent_id": str(confirmed_intent.id),
                "requires_action": confirmed_intent.requires_action,
                "client_secret": confirmed_intent.client_secret
            }
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Payment processing failed: {str(e)}")

    async def process_payment_idempotent(
        self,
        user_id: UUID,
        order_id: UUID,
        amount: float,
        payment_method_id: UUID,
        idempotency_key: str,
        request_id: Optional[str] = None,
        frontend_calculated_amount: Optional[float] = None  # Amount calculated by frontend
    ) -> Dict[str, Any]:
        """
        Process payment with idempotency guarantee and price validation
        Validates that frontend-calculated prices match backend calculations
        """
        start_time = time.time()
        
        if not request_id:
            request_id = str(uuid4())
        
        try:
            # Validate frontend price against backend calculation
            if frontend_calculated_amount is not None:
                price_difference = abs(amount - frontend_calculated_amount)
                if price_difference > 0.01:  # Allow 1 cent tolerance for rounding
                    raise HTTPException(
                        status_code=400, 
                        detail=f"Price mismatch: frontend calculated {frontend_calculated_amount}, backend calculated {amount}"
                    )
            
            # Check for existing transaction with idempotency key
            existing_result = await self.db.execute(
                select(Transaction).where(
                    Transaction.idempotency_key == idempotency_key
                )
            )
            existing_transaction = existing_result.scalar_one_or_none()
            
            if existing_transaction:
                logger.info(f"Returning cached payment result for {idempotency_key}")
                return {
                    "status": existing_transaction.status,
                    "transaction_id": str(existing_transaction.id),
                    "cached": True,
                    "amount": existing_transaction.amount
                }
            
            # Get payment method with validation
            pm_result = await self.db.execute(
                select(PaymentMethod).where(
                    and_(
                        PaymentMethod.id == payment_method_id,
                        PaymentMethod.user_id == user_id,
                        PaymentMethod.is_active == True
                    )
                )
            )
            payment_method = pm_result.scalar_one_or_none()
            
            if not payment_method:
                raise HTTPException(status_code=404, detail="Payment method not found")
            
            # Create Stripe payment intent with idempotency key
            stripe_intent = stripe.PaymentIntent.create(
                amount=int(amount * 100),  # Convert to cents
                currency="USD",
                idempotency_key=idempotency_key,  # Stripe-level deduplication
                metadata={
                    "order_id": str(order_id),
                    "user_id": str(user_id),
                    "request_id": request_id
                }
            )
            
            # Confirm payment
            confirmed = stripe.PaymentIntent.confirm(
                stripe_intent.id,
                payment_method=payment_method.stripe_payment_method_id,
                idempotency_key=f"{idempotency_key}:confirm"  # Separate idempotency for confirm
            )
            
            # Create transaction record with idempotency key
            transaction = Transaction(
                user_id=user_id,
                order_id=order_id,
                payment_intent_id=None,
                stripe_payment_intent_id=stripe_intent.id,
                amount=amount,
                currency="USD",
                status=confirmed.status,
                transaction_type="payment",
                idempotency_key=idempotency_key,  # Store for deduplication
                request_id=request_id,
                transaction_details_metadata={
                    "stripe_request_id": getattr(confirmed, 'request_id', None),
                    "timestamp": datetime.utcnow().isoformat(),
                    "payment_method_type": payment_method.type,
                    "frontend_amount": frontend_calculated_amount,
                    "price_validated": frontend_calculated_amount is not None
                }
            )
            
            self.db.add(transaction)
            await self.db.commit()
            await self.db.refresh(transaction)
            
            return {
                "status": confirmed.status,
                "transaction_id": str(transaction.id),
                "cached": False,
                "amount": amount,
                "processing_time_ms": (time.time() - start_time) * 1000
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error for idempotency key {idempotency_key}: {e}")
            raise HTTPException(status_code=400, detail=f"Payment failed: {str(e)}")
        
        except Exception as e:
            logger.error(f"Payment processing error for idempotency key {idempotency_key}: {e}")
            raise HTTPException(status_code=500, detail=f"Payment processing failed: {str(e)}")

    async def validate_order_pricing(
        self,
        order_items: List[Dict[str, Any]],
        shipping_cost: float = 0.0,
        tax_amount: float = 0.0,
        discount_amount: float = 0.0
    ) -> Dict[str, Any]:
        """
        Validate order pricing by recalculating from backend data
        Never trust frontend prices - always validate against backend
        """
        from models.product import ProductVariant
        
        total_items_cost = 0.0
        validated_items = []
        
        for item in order_items:
            variant_id = UUID(item["variant_id"])
            quantity = int(item["quantity"])
            frontend_price = float(item.get("price_per_unit", 0))
            
            # Get actual price from database
            variant_result = await self.db.execute(
                select(ProductVariant).where(ProductVariant.id == variant_id)
            )
            variant = variant_result.scalar_one_or_none()
            
            if not variant:
                raise HTTPException(status_code=404, detail=f"Product variant {variant_id} not found")
            
            backend_price = float(variant.price)
            
            # Validate price matches (allow small rounding differences)
            if abs(frontend_price - backend_price) > 0.01:
                raise HTTPException(
                    status_code=400,
                    detail=f"Price mismatch for variant {variant_id}: frontend {frontend_price}, backend {backend_price}"
                )
            
            item_total = backend_price * quantity
            total_items_cost += item_total
            
            validated_items.append({
                "variant_id": str(variant_id),
                "quantity": quantity,
                "price_per_unit": backend_price,
                "total_price": item_total,
                "variant_name": variant.name
            })
        
        # Calculate final total
        subtotal = total_items_cost
        total_after_discount = subtotal - discount_amount
        total_with_tax = total_after_discount + tax_amount
        final_total = total_with_tax + shipping_cost
        
        return {
            "items": validated_items,
            "subtotal": subtotal,
            "discount_amount": discount_amount,
            "tax_amount": tax_amount,
            "shipping_cost": shipping_cost,
            "final_total": final_total,
            "validation_passed": True
        }

    async def get_user_transactions(
        self,
        user_id: UUID,
        page: int = 1,
        limit: int = 20
    ) -> Dict[str, Any]:
        """Get user transaction history"""
        offset = (page - 1) * limit
        
        query = select(Transaction).where(Transaction.user_id == user_id).order_by(
            Transaction.created_at.desc()
        ).offset(offset).limit(limit)
        
        result = await self.db.execute(query)
        transactions = result.scalars().all()
        
        # Get total count
        count_result = await self.db.execute(
            select(Transaction).where(Transaction.user_id == user_id)
        )
        total = len(count_result.scalars().all())
        
        return {
            "transactions": [transaction.to_dict() for transaction in transactions],
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "pages": (total + limit - 1) // limit
            }
        }

    async def create_refund(
        self,
        payment_intent_id: UUID,
        amount: Optional[float] = None,
        reason: str = "requested_by_customer"
    ) -> Transaction:
        """Create a refund for a payment"""
        result = await self.db.execute(
            select(PaymentIntent).where(PaymentIntent.id == payment_intent_id)
        )
        payment_intent = result.scalar_one_or_none()
        
        if not payment_intent:
            raise HTTPException(status_code=404, detail="Payment intent not found")
        
        if payment_intent.status != "succeeded":
            raise HTTPException(status_code=400, detail="Cannot refund unsuccessful payment")
        
        try:
            # Create refund in Stripe
            refund_amount = amount or payment_intent.amount_breakdown.get("total", 0)
            stripe_refund = stripe.Refund.create(
                payment_intent=payment_intent.stripe_payment_intent_id,
                amount=int(refund_amount * 100),  # Convert to cents
                reason=reason
            )
            
            # Create transaction record
            transaction = Transaction(
                user_id=payment_intent.user_id,
                order_id=payment_intent.order_id,
                payment_intent_id=payment_intent.id,
                stripe_payment_intent_id=payment_intent.stripe_payment_intent_id,
                amount=-refund_amount,  # Negative for refund
                currency=payment_intent.currency,
                status="succeeded",
                transaction_type="refund",
                description=f"Refund processed: {reason}",
                transaction_metadata={"stripe_refund_id": stripe_refund.id}
            )
            
            self.db.add(transaction)
            await self.db.commit()
            await self.db.refresh(transaction)
            
            return transaction
            
        except stripe.error.StripeError as e:
            raise HTTPException(status_code=400, detail=f"Refund failed: {str(e)}")
    
    async def _send_payment_notification(
        self,
        user_id: UUID,
        order_id: Optional[UUID],
        event_type: str,
        data: Dict[str, Any]
    ):
        """Send payment notification via Kafka for real-time updates"""
        try:
            kafka_producer = await get_kafka_producer_service()
            
            message = {
                'user_id': str(user_id),
                'order_id': str(order_id) if order_id else None,
                'event_type': event_type,
                'data': data,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Send to both payment and websocket topics for real-time notifications
            await kafka_producer.send_message(
                settings.KAFKA_TOPIC_PAYMENT,
                message,
                key=str(user_id)
            )
            
            await kafka_producer.send_message(
                settings.KAFKA_TOPIC_WEBSOCKET,
                {
                    'type': 'payment_update',
                    'user_id': str(user_id),
                    'message': message
                },
                key=str(user_id)
            )
            
            logger.info(f"Payment notification sent: {event_type} for user {user_id}")
            
        except Exception as e:
            logger.error(f"Failed to send payment notification: {e}")
            # Don't raise exception as this is not critical for payment functionality