# Consolidated payment service
# This file includes all payment-related functionality

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from fastapi import HTTPException
from models.payments import PaymentMethod, PaymentIntent, Transaction
from models.user import User
from uuid import UUID
from datetime import datetime
from typing import Optional, List, Dict, Any
from core.config import settings
import stripe

# Configure Stripe
stripe.api_key = getattr(settings, 'STRIPE_SECRET_KEY', '')


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
        metadata: Dict[str, Any] = None
    ) -> PaymentIntent:
        """Create a payment intent"""
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
            await self.db.commit()
            await self.db.refresh(payment_intent)
            
            return payment_intent
            
        except stripe.error.StripeError as e:
            raise HTTPException(status_code=400, detail=f"Stripe error: {str(e)}")

    async def confirm_payment_intent(
        self,
        payment_intent_id: UUID,
        payment_method_id: str
    ) -> PaymentIntent:
        """Confirm a payment intent"""
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
            
            elif stripe_intent.status == "requires_action":
                payment_intent.requires_action = True
                payment_intent.client_secret = stripe_intent.client_secret
            
            await self.db.commit()
            await self.db.refresh(payment_intent)
            
            return payment_intent
            
        except stripe.error.StripeError as e:
            payment_intent.status = "failed"
            payment_intent.failed_at = datetime.utcnow()
            payment_intent.failure_reason = str(e)
            await self.db.commit()
            
            raise HTTPException(status_code=400, detail=f"Payment failed: {str(e)}")

    async def process_payment(
        self,
        user_id: UUID,
        amount: float,
        payment_method_id: UUID,
        order_id: Optional[UUID] = None,
        subscription_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Process a payment (simplified version)"""
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
                subscription_id=subscription_id
            )
            
            confirmed_intent = await self.confirm_payment_intent(
                payment_intent.id,
                payment_method.stripe_payment_method_id
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