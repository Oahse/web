from core.utils.messages.email import send_email
from models.user import User
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from uuid import UUID
from typing import List, Optional
import stripe

from core.config import settings
from models.payment import PaymentMethod
from models.transaction import Transaction
from schemas.payment import PaymentMethodCreate, PaymentMethodUpdate, PaymentMethodResponse
from schemas.transaction import TransactionCreate

stripe.api_key = settings.STRIPE_SECRET_KEY


stripe.api_key = settings.STRIPE_SECRET_KEY


class PaymentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_payment_methods(self, user_id: UUID) -> List[PaymentMethod]:
        query = select(PaymentMethod).where(PaymentMethod.user_id == user_id)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def add_payment_method(self, user_id: UUID, payload: PaymentMethodCreate) -> PaymentMethod:
        # If stripe_token is provided, retrieve card details from Stripe
        if payload.stripe_token:
            try:
                # Retrieve token details from Stripe
                token = stripe.Token.retrieve(payload.stripe_token)
                
                # Extract card details from token
                card = token.card
                payload.provider = card.brand.lower()
                payload.last_four = card.last4
                payload.expiry_month = card.exp_month
                payload.expiry_year = card.exp_year
                
            except stripe.StripeError as e:
                print(f"Stripe Error: {e}")
                raise Exception(f"Failed to retrieve card details from Stripe: {str(e)}")
        
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
            is_default=payload.is_default
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
        try:
            # Create a Stripe PaymentIntent
            payment_intent = stripe.PaymentIntent.create(
                amount=int(amount * 100),  # Stripe expects amount in cents
                currency=currency,
                automatic_payment_methods={"enabled": True},
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
            print(f"Stripe Error: {e}")
            raise e
        except Exception as e:
            # Handle other errors
            print(f"Error creating payment intent: {e}")
            raise e

    async def handle_stripe_webhook(self, event: dict):
        event_type = event["type"]
        data = event["data"]["object"]

        if event_type == "payment_intent.succeeded":
            payment_intent_id = data["id"]
            status = data["status"]
            query = update(Transaction).where(
                Transaction.stripe_payment_intent_id == payment_intent_id).values(status=status)
            await self.db.execute(query)
            await self.db.commit()

            transaction_result = await self.db.execute(select(Transaction).where(Transaction.stripe_payment_intent_id == payment_intent_id))
            transaction = transaction_result.scalar_one_or_none()
            if transaction:
                await self.send_payment_receipt_email(transaction)

        elif event_type == "payment_intent.payment_failed":
            payment_intent_id = data["id"]
            status = data["status"]
            failure_reason = data.get("last_payment_error", {}).get(
                "message", "Unknown error")
            query = update(Transaction).where(
                Transaction.stripe_payment_intent_id == payment_intent_id).values(status=status)
            await self.db.execute(query)
            await self.db.commit()

            transaction_result = await self.db.execute(select(Transaction).where(Transaction.stripe_payment_intent_id == payment_intent_id))
            transaction = transaction_result.scalar_one_or_none()
            if transaction:
                await self.send_payment_failed_email(transaction, failure_reason)

        print(f"Unhandled event type: {event_type}")

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
            print(f"Payment receipt email sent to {user.email} successfully.")
        except Exception as e:
            print(
                f"Failed to send payment receipt email to {user.email}. Error: {e}")

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
            print(f"Payment failed email sent to {user.email} successfully.")
        except Exception as e:
            print(
                f"Failed to send payment failed email to {user.email}. Error: {e}")

    async def process_payment(self, user_id: UUID, amount: float, payment_method_id: UUID, order_id: UUID) -> dict:
        """
        Process payment for an order using Stripe.
        Returns payment result with status.
        """
        try:
            # Get payment method details
            payment_method = await self.db.execute(
                select(PaymentMethod).where(
                    PaymentMethod.id == payment_method_id,
                    PaymentMethod.user_id == user_id
                )
            )
            payment_method = payment_method.scalar_one_or_none()
            
            if not payment_method:
                return {
                    "status": "failed",
                    "error": "Payment method not found"
                }

            # Create a Stripe PaymentIntent
            payment_intent = stripe.PaymentIntent.create(
                amount=int(amount * 100),  # Stripe expects amount in cents
                currency="usd",
                automatic_payment_methods={"enabled": True},
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

            # For demo purposes, we'll consider the payment successful if intent is created
            # In production, you'd wait for webhook confirmation
            return {
                "status": "success",
                "payment_intent_id": payment_intent.id,
                "client_secret": payment_intent.client_secret,
                "transaction_id": str(new_transaction.id)
            }

        except stripe.CardError as e:
            # Card was declined
            error_message = e.user_message or "Card was declined"
            print(f"Card Error: {error_message}")
            return {
                "status": "failed",
                "error": error_message
            }
        except stripe.StripeError as e:
            # Other Stripe errors
            error_message = str(e)
            print(f"Stripe Error: {error_message}")
            return {
                "status": "failed",
                "error": error_message
            }
        except Exception as e:
            # Handle other errors
            error_message = str(e)
            print(f"Error processing payment: {error_message}")
            return {
                "status": "failed",
                "error": error_message
            }
