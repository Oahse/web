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

    async def create_payment_intent(
        self, 
        user_id: UUID, 
        order_id: UUID, 
        subtotal: float, 
        currency: str = None,
        shipping_address_id: UUID = None,
        payment_method_id: UUID = None,
        expires_in_minutes: int = 30
    ) -> dict:
        """
        Creates an enhanced Stripe PaymentIntent with tax calculation and multi-currency support.
        
        Args:
            user_id: User creating the payment intent
            order_id: Associated order ID
            subtotal: Subtotal amount before tax and shipping
            currency: Currency code (auto-detected if not provided)
            shipping_address_id: Address for tax calculation
            payment_method_id: Specific payment method to use
            expires_in_minutes: Payment intent expiration time
        """
        from services.tax import TaxService
        from models.order import Order
        from decimal import Decimal
        import datetime
        
        try:
            # Fetch user to get Stripe customer ID
            user = await self.db.get(User, user_id)
            if not user:
                raise Exception("User not found.")
            
            # Get or create Stripe customer
            stripe_customer_id = await self._get_stripe_customer(user_id, user.email, user.full_name)
            
            # Get order details if available
            order = await self.db.get(Order, order_id) if order_id else None
            
            # Determine shipping address for tax calculation
            tax_address_id = shipping_address_id
            if not tax_address_id and order and order.shipping_address_id:
                tax_address_id = order.shipping_address_id
            elif not tax_address_id and user.default_address:
                tax_address_id = user.default_address.id
            
            # Calculate tax
            tax_service = TaxService(self.db)
            tax_info = await tax_service.calculate_tax(
                subtotal=Decimal(str(subtotal)),
                shipping_address_id=tax_address_id
            )
            
            # Determine currency if not provided
            if not currency:
                if tax_info.get("location", {}).get("country"):
                    country_code = tax_service._get_country_code(tax_info["location"]["country"])
                    currency = tax_service.get_currency_for_country(country_code)
                else:
                    currency = "USD"  # Default fallback
            
            # Calculate shipping (simplified - could be enhanced with shipping service)
            shipping_amount = 0.0
            if subtotal < 50:  # Free shipping over $50
                shipping_amount = 10.0
            
            # Calculate total amount
            total_amount = subtotal + tax_info["tax_amount"] + shipping_amount
            
            # Set payment intent expiration
            expires_at = int((datetime.datetime.utcnow() + datetime.timedelta(minutes=expires_in_minutes)).timestamp())
            
            # Prepare payment intent parameters
            payment_intent_params = {
                "amount": int(total_amount * 100),  # Stripe expects amount in cents
                "currency": currency.lower(),
                "customer": stripe_customer_id,
                "automatic_payment_methods": {"enabled": True},
                "metadata": {
                    "user_id": str(user_id),
                    "order_id": str(order_id) if order_id else "",
                    "subtotal": str(subtotal),
                    "tax_amount": str(tax_info["tax_amount"]),
                    "shipping_amount": str(shipping_amount),
                    "total_amount": str(total_amount),
                    "tax_rate": str(tax_info["tax_rate"]),
                    "currency": currency
                },
                # Set expiration time
                "payment_method_options": {
                    "card": {
                        "setup_future_usage": "off_session"  # Allow saving for future use
                    }
                }
            }
            
            # Add specific payment method if provided
            if payment_method_id:
                payment_method = await self.db.execute(
                    select(PaymentMethod).where(
                        PaymentMethod.id == payment_method_id,
                        PaymentMethod.user_id == user_id
                    )
                )
                payment_method = payment_method.scalar_one_or_none()
                if payment_method and payment_method.stripe_payment_method_id:
                    payment_intent_params["payment_method"] = payment_method.stripe_payment_method_id
            
            # Create Stripe PaymentIntent
            payment_intent = stripe.PaymentIntent.create(**payment_intent_params)
            
            # Create enhanced transaction record
            transaction_data = TransactionCreate(
                user_id=user_id,
                order_id=order_id,
                stripe_payment_intent_id=payment_intent.id,
                amount=total_amount,
                currency=currency.upper(),
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
                "status": payment_intent.status,
                "amount_breakdown": {
                    "subtotal": subtotal,
                    "tax_amount": tax_info["tax_amount"],
                    "tax_rate": tax_info["tax_rate"],
                    "shipping_amount": shipping_amount,
                    "total_amount": total_amount,
                    "currency": currency.upper()
                },
                "tax_info": tax_info,
                "expires_at": expires_at,
                "supported_payment_methods": ["card", "apple_pay", "google_pay"]
            }
            
        except stripe.StripeError as e:
            # Handle Stripe API errors
            raise Exception(f"Stripe error: {str(e)}")
        except Exception as e:
            # Handle other errors
            raise Exception(f"Payment intent creation failed: {str(e)}")

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

    async def handle_payment_intent_expiration(self, payment_intent_id: str) -> dict:
        """
        Handle expired payment intents by updating transaction status and notifying user.
        
        Args:
            payment_intent_id: Stripe payment intent ID
            
        Returns:
            Dict with expiration handling result
        """
        try:
            # Get transaction from database
            transaction_result = await self.db.execute(
                select(Transaction).where(Transaction.stripe_payment_intent_id == payment_intent_id)
            )
            transaction = transaction_result.scalar_one_or_none()
            
            if not transaction:
                return {"status": "error", "message": "Transaction not found"}
            
            # Update transaction status to expired
            transaction.status = "expired"
            transaction.updated_at = datetime.utcnow()
            await self.db.commit()
            
            # Get user for notification
            user = await self.db.get(User, transaction.user_id)
            if user:
                # Send expiration notification email
                await self.send_payment_expired_email(transaction, user)
            
            # Log activity
            from services.activity import ActivityService
            activity_service = ActivityService(self.db)
            await activity_service.log_activity(
                action_type="payment_expired",
                description=f"Payment intent expired for order #{transaction.order_id}",
                user_id=transaction.user_id,
                metadata={
                    "payment_intent_id": payment_intent_id,
                    "order_id": str(transaction.order_id),
                    "amount": float(transaction.amount)
                }
            )
            
            return {
                "status": "success", 
                "message": "Payment intent expiration handled",
                "transaction_id": str(transaction.id)
            }
            
        except Exception as e:
            return {"status": "error", "message": f"Failed to handle expiration: {str(e)}"}
    
    async def send_payment_expired_email(self, transaction: Transaction, user: User):
        """Send email notification for expired payment intent"""
        context = {
            "customer_name": user.firstname,
            "order_number": str(transaction.order_id),
            "transaction_amount": f"${transaction.amount:.2f}",
            "retry_payment_url": f"{settings.FRONTEND_URL}/checkout/{transaction.order_id}",
            "company_name": "Banwee",
        }

        try:
            await send_email(
                to_email=user.email,
                mail_type='payment_expired',
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

    async def confirm_payment_and_order(
        self, 
        payment_intent_id: str, 
        user_id: UUID = None,
        handle_3d_secure: bool = True
    ) -> dict:
        """
        Confirm payment and automatically update order status.
        Handles 3D Secure authentication and provides clear error messaging.
        
        Args:
            payment_intent_id: Stripe payment intent ID
            user_id: User ID for authorization (optional)
            handle_3d_secure: Whether to handle 3D Secure authentication
            
        Returns:
            Dict with confirmation result and order status
        """
        from models.order import Order
        from services.activity import ActivityService
        
        try:
            # Retrieve payment intent from Stripe
            payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            
            # Get transaction from database
            transaction_result = await self.db.execute(
                select(Transaction).where(Transaction.stripe_payment_intent_id == payment_intent_id)
            )
            transaction = transaction_result.scalar_one_or_none()
            
            if not transaction:
                return {
                    "status": "error",
                    "error_code": "TRANSACTION_NOT_FOUND",
                    "message": "Transaction not found in database"
                }
            
            # Verify user authorization if provided
            if user_id and transaction.user_id != user_id:
                return {
                    "status": "error",
                    "error_code": "UNAUTHORIZED",
                    "message": "User not authorized for this payment"
                }
            
            # Handle different payment intent statuses
            if payment_intent.status == "succeeded":
                # Payment already succeeded
                await self._handle_successful_payment_confirmation(transaction, payment_intent)
                return {
                    "status": "succeeded",
                    "message": "Payment confirmed successfully",
                    "order_id": str(transaction.order_id),
                    "transaction_id": str(transaction.id)
                }
                
            elif payment_intent.status == "requires_action":
                # 3D Secure authentication required
                if handle_3d_secure:
                    return {
                        "status": "requires_action",
                        "error_code": "REQUIRES_3D_SECURE",
                        "message": "3D Secure authentication required",
                        "client_secret": payment_intent.client_secret,
                        "next_action": payment_intent.next_action
                    }
                else:
                    return {
                        "status": "error",
                        "error_code": "AUTHENTICATION_REQUIRED",
                        "message": "Payment requires additional authentication"
                    }
                    
            elif payment_intent.status == "requires_payment_method":
                return {
                    "status": "error",
                    "error_code": "PAYMENT_METHOD_REQUIRED",
                    "message": "Payment method is required or invalid"
                }
                
            elif payment_intent.status == "requires_confirmation":
                # Attempt to confirm the payment
                try:
                    confirmed_intent = stripe.PaymentIntent.confirm(payment_intent_id)
                    
                    if confirmed_intent.status == "succeeded":
                        await self._handle_successful_payment_confirmation(transaction, confirmed_intent)
                        return {
                            "status": "succeeded",
                            "message": "Payment confirmed successfully",
                            "order_id": str(transaction.order_id),
                            "transaction_id": str(transaction.id)
                        }
                    elif confirmed_intent.status == "requires_action":
                        return {
                            "status": "requires_action",
                            "error_code": "REQUIRES_3D_SECURE",
                            "message": "3D Secure authentication required",
                            "client_secret": confirmed_intent.client_secret,
                            "next_action": confirmed_intent.next_action
                        }
                    else:
                        return {
                            "status": "error",
                            "error_code": "CONFIRMATION_FAILED",
                            "message": f"Payment confirmation failed: {confirmed_intent.status}"
                        }
                        
                except stripe.error.CardError as e:
                    return self._handle_card_error(e, transaction)
                    
            elif payment_intent.status in ["canceled", "payment_failed"]:
                # Payment failed or was canceled
                await self._handle_failed_payment_confirmation(transaction, payment_intent)
                return {
                    "status": "failed",
                    "error_code": "PAYMENT_FAILED",
                    "message": self._get_user_friendly_error_message(payment_intent.last_payment_error),
                    "order_id": str(transaction.order_id)
                }
                
            else:
                return {
                    "status": "error",
                    "error_code": "UNKNOWN_STATUS",
                    "message": f"Unknown payment status: {payment_intent.status}"
                }
                
        except stripe.error.CardError as e:
            return self._handle_card_error(e, transaction)
        except stripe.StripeError as e:
            return {
                "status": "error",
                "error_code": "STRIPE_ERROR",
                "message": f"Stripe API error: {str(e)}"
            }
        except Exception as e:
            return {
                "status": "error",
                "error_code": "INTERNAL_ERROR",
                "message": f"Internal error: {str(e)}"
            }
    
    async def _handle_successful_payment_confirmation(self, transaction: Transaction, payment_intent: dict):
        """Handle successful payment confirmation and order update"""
        from models.order import Order, TrackingEvent
        from services.activity import ActivityService
        
        # Update transaction status
        transaction.status = "succeeded"
        transaction.updated_at = datetime.utcnow()
        
        # Update order status if order exists
        if transaction.order_id:
            order = await self.db.get(Order, transaction.order_id)
            if order and order.status in ["pending", "payment_failed"]:
                order.status = "confirmed"
                order.updated_at = datetime.utcnow()
                
                # Create tracking event
                tracking_event = TrackingEvent(
                    order_id=order.id,
                    status="confirmed",
                    description="Order confirmed - payment successful",
                    location="Processing Center"
                )
                self.db.add(tracking_event)
        
        await self.db.commit()
        
        # Send confirmation email
        await self.send_payment_receipt_email(transaction)
        
        # Log activity
        activity_service = ActivityService(self.db)
        await activity_service.log_activity(
            action_type="payment_confirmed",
            description=f"Payment confirmed for order #{transaction.order_id}",
            user_id=transaction.user_id,
            metadata={
                "payment_intent_id": payment_intent.get("id"),
                "order_id": str(transaction.order_id),
                "amount": float(transaction.amount)
            }
        )
        
        # Send Kafka notification for order confirmation
        if transaction.order_id:
            from core.kafka import get_kafka_producer_service
            producer_service = await get_kafka_producer_service()
            await producer_service.send_message(settings.KAFKA_TOPIC_NOTIFICATION, {
                "service": "NotificationService",
                "method": "create_notification",
                "args": [],
                "kwargs": {
                    "user_id": str(transaction.user_id),
                    "message": f"Your order #{transaction.order_id} has been confirmed!",
                    "type": "success",
                    "related_id": str(transaction.order_id)
                }
            })
    
    async def _handle_failed_payment_confirmation(self, transaction: Transaction, payment_intent: dict):
        """Handle failed payment confirmation and order update"""
        from models.order import Order
        from services.activity import ActivityService
        
        # Update transaction status
        transaction.status = "failed"
        transaction.failure_reason = self._get_user_friendly_error_message(payment_intent.get("last_payment_error"))
        transaction.updated_at = datetime.utcnow()
        
        # Update order status if order exists
        if transaction.order_id:
            order = await self.db.get(Order, transaction.order_id)
            if order:
                order.status = "payment_failed"
                order.updated_at = datetime.utcnow()
        
        await self.db.commit()
        
        # Send failure email
        await self.send_payment_failed_email(transaction, transaction.failure_reason)
        
        # Log activity
        activity_service = ActivityService(self.db)
        await activity_service.log_activity(
            action_type="payment_failed",
            description=f"Payment failed for order #{transaction.order_id}",
            user_id=transaction.user_id,
            metadata={
                "payment_intent_id": payment_intent.get("id"),
                "order_id": str(transaction.order_id),
                "failure_reason": transaction.failure_reason
            }
        )
    
    def _handle_card_error(self, error: stripe.error.CardError, transaction: Transaction = None) -> dict:
        """Handle Stripe card errors with user-friendly messages"""
        error_code = error.code
        user_message = self._get_user_friendly_error_message({"code": error_code, "message": error.user_message})
        
        return {
            "status": "failed",
            "error_code": f"CARD_ERROR_{error_code.upper()}" if error_code else "CARD_ERROR",
            "message": user_message,
            "decline_code": error.decline_code,
            "order_id": str(transaction.order_id) if transaction and transaction.order_id else None
        }
    
    def _get_user_friendly_error_message(self, error_info: dict) -> str:
        """Convert Stripe error codes to user-friendly messages"""
        if not error_info:
            return "Payment failed due to an unknown error"
        
        error_code = error_info.get("code", "").lower()
        error_message = error_info.get("message", "")
        
        # Map common error codes to user-friendly messages
        error_messages = {
            "card_declined": "Your card was declined. Please try a different payment method or contact your bank.",
            "insufficient_funds": "Your card has insufficient funds. Please try a different payment method.",
            "expired_card": "Your card has expired. Please update your payment method with a valid card.",
            "incorrect_cvc": "The security code (CVC) you entered is incorrect. Please check and try again.",
            "incorrect_number": "The card number you entered is incorrect. Please check and try again.",
            "processing_error": "An error occurred while processing your payment. Please try again.",
            "authentication_required": "Your bank requires additional authentication. Please complete the verification process.",
            "generic_decline": "Your card was declined. Please contact your bank or try a different payment method.",
            "invalid_expiry_month": "The expiration month you entered is invalid.",
            "invalid_expiry_year": "The expiration year you entered is invalid.",
            "lost_card": "Your card has been reported as lost. Please use a different payment method.",
            "stolen_card": "Your card has been reported as stolen. Please use a different payment method.",
            "pickup_card": "Your card cannot be used for this payment. Please contact your bank.",
            "restricted_card": "Your card has restrictions that prevent this payment. Please contact your bank.",
            "security_violation": "This payment was flagged for security reasons. Please contact your bank.",
            "service_not_allowed": "Your card does not support this type of purchase.",
            "transaction_not_allowed": "This transaction is not allowed on your card.",
        }
        
        return error_messages.get(error_code, error_message or "Payment failed. Please try again or contact support.")

    async def create_refund(
        self,
        payment_intent_id: str,
        amount: float = None,
        reason: str = "requested_by_customer",
        user_id: UUID = None
    ) -> dict:
        """
        Create a refund for a payment intent.
        
        Args:
            payment_intent_id: Stripe payment intent ID
            amount: Refund amount (None for full refund)
            reason: Refund reason
            user_id: User ID for authorization
            
        Returns:
            Dict with refund result
        """
        from models.order import Order
        from services.activity import ActivityService
        
        try:
            # Get transaction from database
            transaction_result = await self.db.execute(
                select(Transaction).where(Transaction.stripe_payment_intent_id == payment_intent_id)
            )
            transaction = transaction_result.scalar_one_or_none()
            
            if not transaction:
                return {
                    "status": "error",
                    "error_code": "TRANSACTION_NOT_FOUND",
                    "message": "Transaction not found"
                }
            
            # Verify user authorization if provided
            if user_id and transaction.user_id != user_id:
                return {
                    "status": "error",
                    "error_code": "UNAUTHORIZED",
                    "message": "User not authorized for this refund"
                }
            
            # Check if transaction is refundable
            if transaction.status != "succeeded":
                return {
                    "status": "error",
                    "error_code": "NOT_REFUNDABLE",
                    "message": "Only successful payments can be refunded"
                }
            
            # Calculate refund amount
            refund_amount = amount if amount is not None else transaction.amount
            
            if refund_amount <= 0 or refund_amount > transaction.amount:
                return {
                    "status": "error",
                    "error_code": "INVALID_AMOUNT",
                    "message": f"Refund amount must be between 0 and {transaction.amount}"
                }
            
            # Create Stripe refund
            refund = stripe.Refund.create(
                payment_intent=payment_intent_id,
                amount=int(refund_amount * 100),  # Convert to cents
                reason=reason,
                metadata={
                    "user_id": str(transaction.user_id),
                    "order_id": str(transaction.order_id) if transaction.order_id else "",
                    "original_amount": str(transaction.amount),
                    "refund_amount": str(refund_amount)
                }
            )
            
            # Create refund transaction record
            refund_transaction = Transaction(
                user_id=transaction.user_id,
                order_id=transaction.order_id,
                stripe_payment_intent_id=payment_intent_id,
                amount=refund_amount,
                currency=transaction.currency,
                status=refund.status,
                transaction_type="refund",
                description=f"Refund for payment {payment_intent_id}"
            )
            self.db.add(refund_transaction)
            
            # Update order status if full refund
            if transaction.order_id and refund_amount == transaction.amount:
                order = await self.db.get(Order, transaction.order_id)
                if order:
                    order.status = "refunded"
                    order.updated_at = datetime.utcnow()
            
            await self.db.commit()
            await self.db.refresh(refund_transaction)
            
            # Send refund confirmation email
            await self.send_refund_confirmation_email(refund_transaction, refund)
            
            # Log activity
            activity_service = ActivityService(self.db)
            await activity_service.log_activity(
                action_type="refund_created",
                description=f"Refund created for order #{transaction.order_id}",
                user_id=transaction.user_id,
                metadata={
                    "refund_id": refund.id,
                    "payment_intent_id": payment_intent_id,
                    "refund_amount": float(refund_amount),
                    "reason": reason
                }
            )
            
            return {
                "status": "success",
                "refund_id": refund.id,
                "amount": refund_amount,
                "currency": transaction.currency,
                "status_detail": refund.status,
                "transaction_id": str(refund_transaction.id),
                "message": "Refund created successfully"
            }
            
        except stripe.StripeError as e:
            return {
                "status": "error",
                "error_code": "STRIPE_ERROR",
                "message": f"Stripe refund error: {str(e)}"
            }
        except Exception as e:
            return {
                "status": "error",
                "error_code": "INTERNAL_ERROR",
                "message": f"Refund creation failed: {str(e)}"
            }
    
    async def cancel_payment_intent(
        self,
        payment_intent_id: str,
        user_id: UUID = None,
        cancellation_reason: str = "requested_by_customer"
    ) -> dict:
        """
        Cancel a payment intent before it's confirmed.
        
        Args:
            payment_intent_id: Stripe payment intent ID
            user_id: User ID for authorization
            cancellation_reason: Reason for cancellation
            
        Returns:
            Dict with cancellation result
        """
        from models.order import Order
        from services.activity import ActivityService
        
        try:
            # Get transaction from database
            transaction_result = await self.db.execute(
                select(Transaction).where(Transaction.stripe_payment_intent_id == payment_intent_id)
            )
            transaction = transaction_result.scalar_one_or_none()
            
            if not transaction:
                return {
                    "status": "error",
                    "error_code": "TRANSACTION_NOT_FOUND",
                    "message": "Transaction not found"
                }
            
            # Verify user authorization if provided
            if user_id and transaction.user_id != user_id:
                return {
                    "status": "error",
                    "error_code": "UNAUTHORIZED",
                    "message": "User not authorized for this cancellation"
                }
            
            # Check if payment intent can be canceled
            if transaction.status in ["succeeded", "canceled"]:
                return {
                    "status": "error",
                    "error_code": "CANNOT_CANCEL",
                    "message": f"Payment intent with status '{transaction.status}' cannot be canceled"
                }
            
            # Cancel Stripe payment intent
            payment_intent = stripe.PaymentIntent.cancel(
                payment_intent_id,
                cancellation_reason=cancellation_reason
            )
            
            # Update transaction status
            transaction.status = "canceled"
            transaction.description = f"Canceled: {cancellation_reason}"
            transaction.updated_at = datetime.utcnow()
            
            # Update order status if order exists
            if transaction.order_id:
                order = await self.db.get(Order, transaction.order_id)
                if order:
                    order.status = "cancelled"
                    order.updated_at = datetime.utcnow()
            
            await self.db.commit()
            
            # Send cancellation email
            await self.send_payment_cancellation_email(transaction, cancellation_reason)
            
            # Log activity
            activity_service = ActivityService(self.db)
            await activity_service.log_activity(
                action_type="payment_canceled",
                description=f"Payment canceled for order #{transaction.order_id}",
                user_id=transaction.user_id,
                metadata={
                    "payment_intent_id": payment_intent_id,
                    "order_id": str(transaction.order_id),
                    "cancellation_reason": cancellation_reason
                }
            )
            
            return {
                "status": "success",
                "payment_intent_id": payment_intent_id,
                "cancellation_reason": cancellation_reason,
                "order_id": str(transaction.order_id) if transaction.order_id else None,
                "message": "Payment intent canceled successfully"
            }
            
        except stripe.StripeError as e:
            return {
                "status": "error",
                "error_code": "STRIPE_ERROR",
                "message": f"Stripe cancellation error: {str(e)}"
            }
        except Exception as e:
            return {
                "status": "error",
                "error_code": "INTERNAL_ERROR",
                "message": f"Payment cancellation failed: {str(e)}"
            }
    
    async def get_refund_status(self, refund_id: str) -> dict:
        """Get the status of a refund"""
        try:
            refund = stripe.Refund.retrieve(refund_id)
            return {
                "status": "success",
                "refund_id": refund.id,
                "amount": refund.amount / 100,  # Convert from cents
                "currency": refund.currency,
                "status_detail": refund.status,
                "reason": refund.reason,
                "created": refund.created
            }
        except stripe.StripeError as e:
            return {
                "status": "error",
                "message": f"Failed to retrieve refund: {str(e)}"
            }
    
    async def send_refund_confirmation_email(self, transaction: Transaction, refund: dict):
        """Send refund confirmation email"""
        user_result = await self.db.execute(select(User).where(User.id == transaction.user_id))
        user = user_result.scalar_one_or_none()
        if not user:
            return

        context = {
            "customer_name": user.firstname,
            "refund_amount": f"${transaction.amount:.2f}",
            "refund_id": refund.get("id"),
            "order_number": str(transaction.order_id),
            "processing_time": "3-5 business days",
            "account_url": f"{settings.FRONTEND_URL}/account/orders",
            "company_name": "Banwee",
        }

        try:
            await send_email(
                to_email=user.email,
                mail_type='refund_confirmation',
                context=context
            )
        except Exception as e:
            pass  # Email sending failure should not break the flow
    
    async def send_payment_cancellation_email(self, transaction: Transaction, reason: str):
        """Send payment cancellation email"""
        user_result = await self.db.execute(select(User).where(User.id == transaction.user_id))
        user = user_result.scalar_one_or_none()
        if not user:
            return

        context = {
            "customer_name": user.firstname,
            "order_number": str(transaction.order_id),
            "cancellation_reason": reason.replace("_", " ").title(),
            "amount": f"${transaction.amount:.2f}",
            "retry_url": f"{settings.FRONTEND_URL}/checkout/{transaction.order_id}",
            "company_name": "Banwee",
        }

        try:
            await send_email(
                to_email=user.email,
                mail_type='payment_canceled',
                context=context
            )
        except Exception as e:
            pass  # Email sending failure should not break the flow