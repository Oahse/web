"""
Webhook Service - Secure Stripe webhook handling with signature verification
Processes Stripe webhooks without storing webhook events
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from fastapi import HTTPException, Request
from models.payments import Transaction, PaymentIntent
from models.orders import Order
from services.payments import PaymentService
from services.inventories import InventoryService
from uuid import UUID
from datetime import datetime
from typing import Dict, Any, Optional
from core.config import settings
import stripe
import logging
import json

logger = logging.getLogger(__name__)


class WebhookService:
    """
    Secure Stripe webhook handling with signature verification
    Processes webhooks in real-time without storing webhook events
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.payment_service = PaymentService(db)
        self.inventory_service = InventoryService(db)
        
    async def handle_stripe_webhook(
        self,
        request_body: bytes,
        signature: str,
        ip_address: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Handle Stripe webhook with signature verification
        Process webhook events immediately without storing them
        """
        start_time = datetime.utcnow()
        
        # Verify webhook signature
        try:
            event = stripe.Webhook.construct_event(
                request_body,
                signature,
                settings.STRIPE_WEBHOOK_SECRET
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail="Invalid payload")
        except stripe.error.SignatureVerificationError as e:
            
            raise HTTPException(status_code=400, detail="Invalid signature")
        
        event_id = event["id"]
        event_type = event["type"]
        
        
    async def _process_webhook_event(
        self,
        event: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process webhook event based on type"""
        event_type = event["type"]
        event_data = event["data"]["object"]
        
        if event_type == "payment_intent.succeeded":
            return await self._handle_payment_succeeded(event_data)
        
        elif event_type == "payment_intent.payment_failed":
            return await self._handle_payment_failed(event_data)
        
        elif event_type == "payment_intent.canceled":
            return await self._handle_payment_canceled(event_data)
        
        elif event_type == "charge.refunded":
            return await self._handle_refund(event_data)
        
        else:
            logger.info(f"Unhandled webhook event type: {event_type}")
            return {"status": "ignored", "reason": "unhandled_event_type"}

    async def _handle_payment_succeeded(self, payment_intent_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle successful payment webhook"""
        stripe_payment_intent_id = payment_intent_data["id"]
        
        # Find the transaction with lock to prevent race conditions
        transaction_result = await self.db.execute(
            select(Transaction).where(
                Transaction.stripe_payment_intent_id == stripe_payment_intent_id
            ).with_for_update()
        )
        transaction = transaction_result.scalar_one_or_none()
        
        if transaction:
            # Update transaction status atomically
            transaction.status = "succeeded"
            transaction.transaction_details_metadata = {
                **transaction.transaction_details_metadata,
                "webhook_confirmed_at": datetime.utcnow().isoformat(),
                "stripe_charges": payment_intent_data.get("charges", {})
            }
            
            # If this is an order payment, update order status atomically
            if transaction.order_id:
                order_result = await self.db.execute(
                    select(Order).where(Order.id == transaction.order_id).with_for_update()
                )
                order = order_result.scalar_one_or_none()
                
                if order:
                    # Update order status to confirmed atomically
                    order.status = "confirmed"
                    order.version += 1  # Optimistic locking increment
                    
            
            await self.db.commit()
            
            return {
                "action": "payment_confirmed",
                "transaction_id": str(transaction.id),
                "order_id": str(transaction.order_id) if transaction.order_id else None
            }
        
        else:
            logger.warning(f"Transaction not found for payment intent {stripe_payment_intent_id}")
            return {
                "action": "payment_confirmed",
                "warning": "transaction_not_found",
                "stripe_payment_intent_id": stripe_payment_intent_id
            }

    async def _handle_payment_failed(self, payment_intent_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle failed payment webhook"""
        stripe_payment_intent_id = payment_intent_data["id"]
        
        # Find the transaction with lock to prevent race conditions
        transaction_result = await self.db.execute(
            select(Transaction).where(
                Transaction.stripe_payment_intent_id == stripe_payment_intent_id
            ).with_for_update()
        )
        transaction = transaction_result.scalar_one_or_none()
        
        if transaction:
            # Update transaction status atomically
            transaction.status = "failed"
            transaction.failure_reason = payment_intent_data.get("last_payment_error", {}).get("message", "Payment failed")
            transaction.transaction_details_metadata = {
                **transaction.transaction_details_metadata,
                "webhook_failed_at": datetime.utcnow().isoformat(),
                "failure_details": payment_intent_data.get("last_payment_error", {})
            }
            
            # If this is an order payment, update order status atomically
            if transaction.order_id:
                order_result = await self.db.execute(
                    select(Order).where(Order.id == transaction.order_id).with_for_update()
                )
                order = order_result.scalar_one_or_none()
                if order:
                    order.status = "payment_failed"
                    order.version += 1  # Optimistic locking increment
                    
            
            await self.db.commit()
            
            return {
                "action": "payment_failed",
                "transaction_id": str(transaction.id),
                "order_id": str(transaction.order_id) if transaction.order_id else None,
                "failure_reason": transaction.failure_reason
            }
        
        else:
            logger.warning(f"Transaction not found for failed payment intent {stripe_payment_intent_id}")
            return {
                "action": "payment_failed",
                "warning": "transaction_not_found",
                "stripe_payment_intent_id": stripe_payment_intent_id
            }

    async def _handle_payment_canceled(self, payment_intent_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle canceled payment webhook"""
        stripe_payment_intent_id = payment_intent_data["id"]
        
        # Find the transaction with lock to prevent race conditions
        transaction_result = await self.db.execute(
            select(Transaction).where(
                Transaction.stripe_payment_intent_id == stripe_payment_intent_id
            ).with_for_update()
        )
        transaction = transaction_result.scalar_one_or_none()
        
        if transaction:
            transaction.status = "cancelled"
            
            # Update order status if applicable atomically
            if transaction.order_id:
                order_result = await self.db.execute(
                    select(Order).where(Order.id == transaction.order_id).with_for_update()
                )
                order = order_result.scalar_one_or_none()
                if order:
                    order.status = "cancelled"
                    order.version += 1
            
            await self.db.commit()
            
            return {
                "action": "payment_cancelled",
                "transaction_id": str(transaction.id)
            }
        
        return {"action": "payment_cancelled", "warning": "transaction_not_found"}

    async def _handle_refund(self, charge_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle refund webhook"""
        
        return {"action": "refund_processed", "charge_id": charge_data["id"]}