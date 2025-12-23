from core.utils.messages.email import send_email
from models.user import User
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from uuid import UUID
from typing import List, Optional
from datetime import datetime
import stripe

from core.config import settings
from models.payment import PaymentMethod
from models.transaction import Transaction
from schemas.payment import PaymentMethodCreate, PaymentMethodUpdate, PaymentMethodResponse
from schemas.transaction import TransactionCreate
from services.activity import ActivityService

stripe.api_key = settings.STRIPE_SECRET_KEY


class PaymentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _get_stripe_customer(self, user_id: UUID, user_email: str, user_full_name: str) -> str:
        """
        Retrieves or creates a Stripe Customer ID for the given user.
        """
        user_obj = await self.db.get(User, user_id)
        if not user_obj:
            raise Exception("User not found for Stripe customer operation.")

        if user_obj.stripe_customer_id:
            return user_obj.stripe_customer_id
        
        # Create new Stripe customer
        customer = stripe.Customer.create(
            email=user_email,
            name=user_full_name,
            metadata={"user_id": str(user_id)}
        )
        user_obj.stripe_customer_id = customer.id
        await self.db.commit()
        await self.db.refresh(user_obj)
        return customer.id

    async def get_payment_methods(self, user_id: UUID) -> List[PaymentMethod]:
        query = select(PaymentMethod).where(PaymentMethod.user_id == user_id)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def add_payment_method(self, user_id: UUID, payload: PaymentMethodCreate) -> PaymentMethod:
        # Fetch user for email and full name
        user = await self.db.get(User, user_id)
        if not user:
            raise Exception("User not found for adding payment method.")
            
        stripe_customer_id = await self._get_stripe_customer(user_id, user.email, user.full_name)

        if payload.stripe_token:
            try:
                # Create Stripe PaymentMethod from token
                stripe_pm = stripe.PaymentMethod.create(
                    type="card",
                    card={"token": payload.stripe_token}
                )
                
                # Attach PaymentMethod to customer
                stripe.PaymentMethod.attach(
                    stripe_pm.id,
                    customer=stripe_customer_id
                )
                
                # Extract card details from the created PaymentMethod
                card_details = stripe_pm.card
                payload.provider = card_details.brand.lower()
                payload.last_four = card_details.last4
                payload.expiry_month = card_details.exp_month
                payload.expiry_year = card_details.exp_year
                payload.stripe_payment_method_id = stripe_pm.id
                payload.brand = card_details.brand # Store card brand
                
            except stripe.StripeError as e:
                raise Exception(f"Failed to process card details with Stripe: {str(e)}")
        else:
            raise Exception("Stripe token is required to add a new payment method.")
        
        # Check if this is the first payment method for the user
        existing_methods = await self.get_payment_methods(user_id)
        is_first_method = len(existing_methods) == 0
        
        # Set as default if it's the first payment method or explicitly requested
        if is_first_method or payload.is_default:
            await self._clear_default_payment_method(user_id)
            payload.is_default = True

        new_method = PaymentMethod(
            user_id=user_id,
            type=payload.type,
            provider=payload.provider,
            last_four=payload.last_four,
            expiry_month=payload.expiry_month,
            expiry_year=payload.expiry_year,
            is_default=payload.is_default,
            stripe_payment_method_id=payload.stripe_payment_method_id,
            brand=payload.brand # Assign brand
        )
        self.db.add(new_method)
        await self.db.commit()
        await self.db.refresh(new_method)
        return new_method

    async def update_payment_method(self, user_id: UUID, method_id: UUID, payload: PaymentMethodUpdate) -> Optional[PaymentMethod]:
        query = select(PaymentMethod).where(PaymentMethod.id ==
                                            method_id, PaymentMethod.user_id == user_id)
        result = await self.db.execute(query)
        method = result.scalar_one_or_none()

        if not method:
            return None

        # Ensure only one default payment method per user
        if payload.is_default is True:
            await self._clear_default_payment_method(user_id, exclude_method_id=method_id)
        elif payload.is_default is False and method.is_default:
            # Prevent unsetting default if it's the only one, or handle logic to set another as default
            pass  # More complex logic might be needed here

        for field, value in payload.dict(exclude_unset=True).items():
            setattr(method, field, value)

        await self.db.commit()
        await self.db.refresh(method)
        return method

    async def delete_payment_method(self, user_id: UUID, method_id: UUID) -> bool:
        query = select(PaymentMethod).where(PaymentMethod.id ==
                                            method_id, PaymentMethod.user_id == user_id)
        result = await self.db.execute(query)
        method = result.scalar_one_or_none()

        if not method:
            return False
            
        # Detach PaymentMethod from Stripe Customer if it exists
        if method.stripe_payment_method_id and method.user.stripe_customer_id:
            try:
                stripe.PaymentMethod.detach(method.stripe_payment_method_id)
            except stripe.StripeError as e:
                # Log the error, but don't prevent deletion from local DB if Stripe fails
                print(f"Warning: Failed to detach Stripe PaymentMethod {method.stripe_payment_method_id}: {e}")

        await self.db.delete(method)
        await self.db.commit()
        return True

    async def set_default_payment_method(self, user_id: UUID, method_id: UUID) -> Optional[PaymentMethod]:
        # Clear existing default for the user
        await self._clear_default_payment_method(user_id)

        # Set the new default
        query = update(PaymentMethod).where(PaymentMethod.id == method_id,
                                            PaymentMethod.user_id == user_id).values(is_default=True)
        await self.db.execute(query)
        await self.db.commit()

        query = select(PaymentMethod).where(PaymentMethod.id == method_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def _clear_default_payment_method(self, user_id: UUID, exclude_method_id: Optional[UUID] = None):
        query = update(PaymentMethod).where(
            PaymentMethod.user_id == user_id,
            PaymentMethod.is_default == True
        ).values(is_default=False)
        if exclude_method_id:
            query = query.where(PaymentMethod.id != exclude_method_id)
        await self.db.execute(query)
        await self.db.commit()

    async def get_default_payment_method(self, user_id: UUID) -> Optional[PaymentMethod]:
        """Get a user's default payment method."""
        # First, try to find a payment method marked as default
        query = select(PaymentMethod).where(
            PaymentMethod.user_id == user_id,
            PaymentMethod.is_default == True
        )
        result = await self.db.execute(query)
        method = result.scalars().first()

        if method:
            return method

        # If no default is set, return the most recent payment method
        query = select(PaymentMethod).where(
            PaymentMethod.user_id == user_id
        ).order_by(PaymentMethod.created_at.desc())
        result = await self.db.execute(query)
        return result.scalars().first()

    async def create_payment_intent(self, user_id: UUID, order_id: UUID, amount: float, currency: str) -> dict:
        """
        Creates a Stripe PaymentIntent.
        This method is typically called to set up a payment, usually from the frontend
        where the client secret is needed to confirm the payment.
        """
        try:
            # Fetch user to get Stripe customer ID
            user = await self.db.get(User, user_id)
            if not user or not user.stripe_customer_id:
                raise Exception("Stripe Customer ID not found for user.")

            payment_intent = stripe.PaymentIntent.create(
                amount=int(amount * 100),  # Stripe expects amount in cents
                currency=currency,
                customer=user.stripe_customer_id, # Link to customer
                automatic_payment_methods={"enabled": True}, # Still useful for displaying options
                metadata={
                    "user_id": str(user_id),
                    "order_id": str(order_id)
                }
            )

            # Create a transaction record in our database
            transaction_data = TransactionCreate(
                user_id=user_id,
                order_id=order_id,
                stripe_payment_intent_id=payment_intent.id,
                amount=amount,
                currency=currency,
                status=payment_intent.status,
                transaction_type="payment"
            )
            new_transaction = Transaction(**transaction_data.model_dump())
            self.db.add(new_transaction)
            await self.db.commit()
            await self.db.refresh(new_transaction)

            return {
                "client_secret": payment_intent.client_secret,
                "payment_intent_id": payment_intent.id,
                "status": payment_intent.status
            }
        except stripe.StripeError as e:
            # Handle Stripe API errors
            raise e
        except Exception as e:
            # Handle other errors
            raise e

    async def _process_successful_payment(self, payment_intent_id: str, status: str):
        query = update(Transaction).where(
            Transaction.stripe_payment_intent_id == payment_intent_id
        ).values(status=status)
        await self.db.execute(query)
        await self.db.commit()

        transaction_result = await self.db.execute(select(Transaction).where(Transaction.stripe_payment_intent_id == payment_intent_id))
        transaction = transaction_result.scalar_one_or_none()
        if transaction:
            await self.send_payment_receipt_email(transaction)

    async def handle_stripe_webhook(self, event: dict):
        import logging
        import asyncio
        from datetime import datetime, timedelta
        from models.webhook_event import WebhookEvent
        
        logger = logging.getLogger(__name__)
        event_id = event.get("id", "unknown")
        event_type = event["type"]
        data = event["data"]["object"]
        
        logger.info(f"Processing webhook event {event_id} of type {event_type}")
        
        # Check for idempotency - prevent duplicate processing
        webhook_record = await self._get_or_create_webhook_record(event_id, event_type, event)
        
        if webhook_record.processed:
            logger.info(f"Webhook event {event_id} already processed successfully, skipping")
            return
        
        # Update processing attempt
        webhook_record.processing_attempts += 1
        webhook_record.last_processing_attempt = datetime.utcnow()
        await self.db.commit()
        
        max_retries = 3
        base_delay = 1  # Base delay in seconds
        
        while webhook_record.processing_attempts <= max_retries:
            try:
                if event_type == "payment_intent.succeeded":
                    await self._handle_payment_intent_succeeded(data, event_id)
                    
                elif event_type == "payment_intent.payment_failed":
                    await self._handle_payment_intent_failed(data, event_id)
                    
                elif event_type == "charge.succeeded":
                    await self._handle_charge_succeeded(data, event_id)
                    
                elif event_type == "payment_method.attached":
                    await self._handle_payment_method_attached(data, event_id)
                    
                elif event_type == "customer.updated":
                    await self._handle_customer_updated(data, event_id)
                    
                else:
                    logger.info(f"Unhandled webhook event type: {event_type}")
                
                # Mark as successfully processed
                webhook_record.processed = True
                webhook_record.completed_at = datetime.utcnow()
                webhook_record.error_message = None
                await self.db.commit()
                
                logger.info(f"Successfully processed webhook event {event_id}")
                break
                
            except Exception as e:
                error_message = str(e)
                logger.error(f"Error processing webhook event {event_id} (attempt {webhook_record.processing_attempts}/{max_retries}): {error_message}")
                
                if webhook_record.processing_attempts < max_retries:
                    # Exponential backoff: 1s, 2s, 4s
                    delay = base_delay * (2 ** (webhook_record.processing_attempts - 1))
                    logger.info(f"Retrying webhook event {event_id} in {delay} seconds")
                    
                    # Update attempt count for next retry
                    webhook_record.processing_attempts += 1
                    webhook_record.last_processing_attempt = datetime.utcnow()
                    await self.db.commit()
                    
                    await asyncio.sleep(delay)
                else:
                    # Mark as failed after all retries exhausted
                    webhook_record.error_message = error_message
                    await self.db.commit()
                    
                    logger.error(f"Failed to process webhook event {event_id} after {max_retries} attempts")
                    
                    # Log final failure to activity log for monitoring
                    from services.activity import ActivityService
                    activity_service = ActivityService(self.db)
                    await activity_service.log_activity(
                        action_type="webhook_failed",
                        description=f"Failed to process webhook after {max_retries} attempts: {error_message}",
                        metadata={
                            "webhook_event_id": event_id,
                            "event_type": event_type,
                            "status": "failed",
                            "error": error_message,
                            "attempts": max_retries
                        }
                    )
                    raise
    
    async def _get_or_create_webhook_record(self, event_id: str, event_type: str, event_data: dict) -> 'WebhookEvent':
        """Get existing webhook record or create new one for idempotency tracking"""
        from models.webhook_event import WebhookEvent
        
        # Try to get existing record
        query = select(WebhookEvent).where(WebhookEvent.stripe_event_id == event_id)
        result = await self.db.execute(query)
        webhook_record = result.scalar_one_or_none()
        
        if webhook_record:
            return webhook_record
        
        # Create new record
        webhook_record = WebhookEvent(
            stripe_event_id=event_id,
            event_type=event_type,
            event_data=event_data,
            processed=False,
            processing_attempts=0
        )
        self.db.add(webhook_record)
        await self.db.commit()
        await self.db.refresh(webhook_record)
        
        return webhook_record
    
    async def _handle_payment_intent_succeeded(self, data: dict, event_id: str):
        """Handle successful payment intent events"""
        payment_intent_id = data["id"]
        status = data["status"]
        amount_received = data.get("amount_received", 0) / 100  # Convert from cents
        
        logger = logging.getLogger(__name__)
        logger.info(f"Processing payment_intent.succeeded for {payment_intent_id}")
        
        # Update transaction status
        query = update(Transaction).where(
            Transaction.stripe_payment_intent_id == payment_intent_id
        ).values(
            status=status,
            updated_at=datetime.utcnow()
        )
        result = await self.db.execute(query)
        
        if result.rowcount == 0:
            logger.warning(f"No transaction found for payment_intent_id: {payment_intent_id}")
            return
        
        await self.db.commit()
        
        # Get the updated transaction for further processing
        transaction_result = await self.db.execute(
            select(Transaction).where(Transaction.stripe_payment_intent_id == payment_intent_id)
        )
        transaction = transaction_result.scalar_one_or_none()
        
        if transaction:
            # Send payment receipt email
            await self.send_payment_receipt_email(transaction)
            
            # Log activity
            from services.activity import ActivityService
            activity_service = ActivityService(self.db)
            await activity_service.log_activity(
                action_type="payment_success",
                description=f"Payment succeeded for order #{transaction.order_id}",
                user_id=transaction.user_id,
                metadata={
                    "payment_intent_id": payment_intent_id,
                    "amount": float(amount_received),
                    "webhook_event_id": event_id
                }
            )
    
    async def _handle_payment_intent_failed(self, data: dict, event_id: str):
        """Handle failed payment intent events"""
        payment_intent_id = data["id"]
        status = data["status"]
        last_payment_error = data.get("last_payment_error", {})
        failure_reason = last_payment_error.get("message", "Unknown payment failure")
        failure_code = last_payment_error.get("code", "unknown")
        
        logger = logging.getLogger(__name__)
        logger.info(f"Processing payment_intent.payment_failed for {payment_intent_id}")
        
        # Update transaction status with failure details
        query = update(Transaction).where(
            Transaction.stripe_payment_intent_id == payment_intent_id
        ).values(
            status=status,
            failure_reason=failure_reason,
            updated_at=datetime.utcnow()
        )
        result = await self.db.execute(query)
        
        if result.rowcount == 0:
            logger.warning(f"No transaction found for payment_intent_id: {payment_intent_id}")
            return
        
        await self.db.commit()
        
        # Get the updated transaction for further processing
        transaction_result = await self.db.execute(
            select(Transaction).where(Transaction.stripe_payment_intent_id == payment_intent_id)
        )
        transaction = transaction_result.scalar_one_or_none()
        
        if transaction:
            # Send payment failure email
            await self.send_payment_failed_email(transaction, failure_reason)
            
            # Log activity
            from services.activity import ActivityService
            activity_service = ActivityService(self.db)
            await activity_service.log_activity(
                action_type="payment_failure",
                description=f"Payment failed for order #{transaction.order_id}: {failure_reason}",
                user_id=transaction.user_id,
                metadata={
                    "payment_intent_id": payment_intent_id,
                    "failure_reason": failure_reason,
                    "failure_code": failure_code,
                    "webhook_event_id": event_id
                }
            )
    
    async def _handle_charge_succeeded(self, data: dict, event_id: str):
        """Handle successful charge events (backup for payment_intent.succeeded)"""
        payment_intent_id = data.get("payment_intent")
        if not payment_intent_id:
            return
        
        logger = logging.getLogger(__name__)
        logger.info(f"Processing charge.succeeded for payment_intent {payment_intent_id}")
        
        # Check if we already processed the payment_intent.succeeded event
        transaction_result = await self.db.execute(
            select(Transaction).where(Transaction.stripe_payment_intent_id == payment_intent_id)
        )
        transaction = transaction_result.scalar_one_or_none()
        
        if transaction and transaction.status != "succeeded":
            await self._handle_payment_intent_succeeded(
                {"id": payment_intent_id, "status": "succeeded", "amount_received": data.get("amount", 0)},
                event_id
            )
    
    async def _handle_payment_method_attached(self, data: dict, event_id: str):
        """Handle payment method attachment events"""
        logger = logging.getLogger(__name__)
        logger.info(f"Processing payment_method.attached event {event_id}")
        # This is mainly for logging/monitoring purposes
        # The actual payment method creation is handled in our add_payment_method method
    
    async def _handle_customer_updated(self, data: dict, event_id: str):
        """Handle customer update events"""
        logger = logging.getLogger(__name__)
        logger.info(f"Processing customer.updated event {event_id}")
        # This could be used to sync customer data changes from Stripe
        # For now, we'll just log it

    async def send_payment_receipt_email(self, transaction: Transaction):
        user_result = await self.db.execute(select(User).where(User.id == transaction.user_id))
        user = user_result.scalar_one_or_none()
        if not user:
            return

        context = {
            "customer_name": user.firstname,
            "total_paid": f"${transaction.amount:.2f}",
            "transaction_id": str(transaction.id),
            "payment_date": transaction.created_at.strftime("%B %d, %Y"),
            "account_url": f"{settings.FRONTEND_URL}/account",
            "company_name": "Banwee",
        }

        try:
            await send_email(
                to_email=user.email,
                mail_type='payment_receipt',
                context=context
            )
        except Exception as e:
            pass  # Email sending failure should not break the flow

    async def send_payment_failed_email(self, transaction: Transaction, failure_reason: str):
        user_result = await self.db.execute(select(User).where(User.id == transaction.user_id))
        user = user_result.scalar_one_or_none()
        if not user:
            return

        context = {
            "customer_name": user.firstname,
            "order_number": str(transaction.order_id),
            "transaction_amount": f"${transaction.amount:.2f}",
            "failure_reason": failure_reason,
            "update_payment_url": f"{settings.FRONTEND_URL}/account/payment-methods",
            "company_name": "Banwee",
        }

        try:
            await send_email(
                to_email=user.email,
                mail_type='payment_failed',
                context=context
            )
        except Exception as e:
            pass  # Email sending failure should not break the flow

    async def process_payment(self, user_id: UUID, amount: float, payment_method_id: UUID, order_id: UUID) -> dict:
        """
        Process payment for an order using Stripe.
        Returns payment result with status.
        """
        try:
            # Fetch user and payment method from our DB
            user = await self.db.get(User, user_id)
            if not user:
                return {
                    "status": "failed",
                    "error": "User not found"
                }

            payment_method_db = await self.db.execute(
                select(PaymentMethod).where(
                    PaymentMethod.id == payment_method_id,
                    PaymentMethod.user_id == user_id
                )
            )
            payment_method_db = payment_method_db.scalar_one_or_none()
            
            if not payment_method_db:
                return {
                    "status": "failed",
                    "error": "Payment method not found in database"
                }

            if not user.stripe_customer_id:
                return {
                    "status": "failed",
                    "error": "Stripe Customer ID not found for user."
                }
            if not payment_method_db.stripe_payment_method_id:
                return {
                    "status": "failed",
                    "error": "Stripe Payment Method ID not found for saved payment method."
                }

            # Create a Stripe PaymentIntent
            # Use the saved Stripe Customer and Payment Method
            payment_intent = stripe.PaymentIntent.create(
                amount=int(amount * 100),  # Stripe expects amount in cents
                currency="usd",
                customer=user.stripe_customer_id,
                payment_method=payment_method_db.stripe_payment_method_id,
                confirm=True, # Attempt to confirm the payment immediately
                off_session=True, # Required for confirming payment with saved methods without user interaction
                metadata={
                    "user_id": str(user_id),
                    "order_id": str(order_id),
                    "payment_method_id": str(payment_method_id)
                }
            )

            # Create a transaction record in our database
            transaction_data = TransactionCreate(
                user_id=user_id,
                order_id=order_id,
                stripe_payment_intent_id=payment_intent.id,
                amount=amount,
                currency="USD",
                status=payment_intent.status,
                transaction_type="payment"
            )
            new_transaction = Transaction(**transaction_data.model_dump())
            self.db.add(new_transaction)
            await self.db.commit()
            await self.db.refresh(new_transaction)

            # Log activity for successful payment
            activity_service = ActivityService(self.db)
            await activity_service.log_activity(
                action_type="payment",
                description=f"Payment processed for order #{order_id}",
                user_id=user_id,
                metadata={
                    "order_id": str(order_id),
                    "amount": float(amount),
                    "currency": "USD",
                    "payment_intent_id": payment_intent.id,
                    "transaction_id": str(new_transaction.id)
                }
            )

            return {
                "status": payment_intent.status, # Return actual status from Stripe
                "payment_intent_id": payment_intent.id,
                "client_secret": payment_intent.client_secret,
                "transaction_id": str(new_transaction.id)
            }

        except stripe.error.CardError as e:
            # Card was declined or other card-related error
            return {
                "status": "failed",
                "error": e.user_message or str(e)
            }
        except stripe.StripeError as e:
            # Other Stripe errors (e.g., network, authentication)
            return {
                "status": "failed",
                "error": str(e)
            }
        except Exception as e:
            # Handle other errors
            return {
                "status": "failed",
                "error": str(e)
            }