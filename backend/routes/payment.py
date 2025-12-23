from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import List
import stripe

from core.database import get_db
from services.payment import PaymentService
from schemas.payment import PaymentMethodCreate, PaymentMethodUpdate, PaymentMethodResponse
from models.user import User
from core.dependencies import verify_user_or_admin_access
from pydantic import BaseModel, Field
from core.config import settings
from routes.user import get_current_authenticated_user  # Import the dependency

# Main router for payment methods
payment_method_router = APIRouter(
    prefix="/api/v1/users", tags=["Payment Methods"])

# Router for Stripe-related payment operations
payment_router = APIRouter(prefix="/api/v1/payments", tags=["Payments"])


class CreatePaymentIntentRequest(BaseModel):
    order_id: UUID
    amount: float = Field(..., gt=0)
    currency: str = Field("usd", max_length=3)


class ProcessPaymentRequest(BaseModel):
    amount: float = Field(..., gt=0)
    payment_method_id: UUID
    order_id: UUID
    currency: str = Field("USD", max_length=3)


@payment_method_router.get("/me/payment-methods", response_model=List[PaymentMethodResponse], summary="Get all payment methods for the current user")
async def get_my_payment_methods(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_authenticated_user)
):
    try:
        service = PaymentService(db)
        payment_methods = await service.get_payment_methods(current_user.id)
        return payment_methods
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch payment methods - {str(e)}"
        )


@payment_method_router.get("/{user_id}/payment-methods", response_model=List[PaymentMethodResponse], summary="Get all payment methods for a user")
async def get_payment_methods(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_user_or_admin_access)
):
    try:
        service = PaymentService(db)
        payment_methods = await service.get_payment_methods(user_id)
        return payment_methods
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch payment methods - {str(e)}"
        )


@payment_method_router.post("/{user_id}/payment-methods", response_model=PaymentMethodResponse, status_code=status.HTTP_201_CREATED, summary="Add a new payment method for a user")
async def add_payment_method(
    user_id: UUID,
    payload: PaymentMethodCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_user_or_admin_access)
):
    try:
        service = PaymentService(db)
        payment_method = await service.add_payment_method(user_id, payload)
        return payment_method
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to add payment method - {str(e)}"
        )


@payment_method_router.put("/{user_id}/payment-methods/{method_id}", response_model=PaymentMethodResponse, summary="Update a payment method")
async def update_payment_method(
    user_id: UUID,
    method_id: UUID,
    payload: PaymentMethodUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_user_or_admin_access)
):
    try:
        service = PaymentService(db)
        updated_method = await service.update_payment_method(user_id, method_id, payload)
        if not updated_method:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Payment method not found")
        return updated_method
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update payment method - {str(e)}"
        )


@payment_method_router.delete("/{user_id}/payment-methods/{method_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a payment method")
async def delete_payment_method(
    user_id: UUID,
    method_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_user_or_admin_access)
):
    try:
        service = PaymentService(db)
        deleted = await service.delete_payment_method(user_id, method_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Payment method not found")
        return
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to delete payment method - {str(e)}"
        )


@payment_method_router.put("/{user_id}/payment-methods/{method_id}/default", response_model=PaymentMethodResponse, summary="Set a payment method as default")
async def set_default_payment_method(
    user_id: UUID,
    method_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_user_or_admin_access)
):
    try:
        service = PaymentService(db)
        default_method = await service.set_default_payment_method(user_id, method_id)
        if not default_method:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Payment method not found")
        return default_method
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to set default payment method - {str(e)}"
        )


@payment_method_router.get("/me/payment-methods/default", response_model=PaymentMethodResponse, summary="Get default payment method for the current user")
async def get_my_default_payment_method(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_authenticated_user)
):
    try:
        service = PaymentService(db)
        payment_method = await service.get_default_payment_method(current_user.id)
        if not payment_method:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Default payment method not found")
        return payment_method
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch default payment method - {str(e)}"
        )


@payment_router.post("/create-payment-intent", summary="Create a Stripe Payment Intent")
async def create_payment_intent(
    payload: CreatePaymentIntentRequest,
    db: AsyncSession = Depends(get_db),
    # Ensure user is authenticated
    current_user: User = Depends(verify_user_or_admin_access)
):
    try:
        service = PaymentService(db)
        # The user_id for the payment intent should be the current_user's ID
        result = await service.create_payment_intent(
            user_id=current_user.id,
            order_id=payload.order_id,
            amount=payload.amount,
            currency=payload.currency
        )
        return result
    except stripe.StripeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@payment_router.post("/process", summary="Process a payment")
async def process_payment(
    payload: ProcessPaymentRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_authenticated_user)
):
    """
    Process a payment for an order.
    This endpoint handles the payment processing and returns the result.
    """
    try:
        service = PaymentService(db)
        result = await service.process_payment(
            user_id=current_user.id,
            amount=payload.amount,
            payment_method_id=payload.payment_method_id,
            order_id=payload.order_id
        )
        
        if result.get("status") == "failed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Payment processing failed")
            )
        
        return {
            "success": True,
            "data": result,
            "message": "Payment processed successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process payment - {str(e)}"
        )


@payment_router.post("/stripe-webhook", summary="Handle Stripe webhook events")
async def stripe_webhook(request: Request, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        # Retrieve the event by verifying the signature using the raw body and secret
        webhook_secret = settings.STRIPE_WEBHOOK_SECRET
        if not webhook_secret:
            logger.error("Stripe webhook secret not configured")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Stripe webhook secret not configured."
            )

        payload = await request.body()
        sig_header = request.headers.get('stripe-signature')
        
        # Enhanced signature verification with detailed error handling
        if not sig_header:
            logger.warning("Missing Stripe signature header in webhook request")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing Stripe signature header"
            )
        
        if not payload:
            logger.warning("Empty payload received in webhook request")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Empty webhook payload"
            )

        event = None
        try:
            # Verify webhook signature and construct event
            event = stripe.Webhook.construct_event(
                payload, sig_header, webhook_secret
            )
            logger.info(f"Successfully verified webhook signature for event: {event.get('id', 'unknown')}")
            
        except ValueError as e:
            # Invalid payload format
            logger.error(f"Invalid webhook payload format: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid payload format: {str(e)}"
            )
        except stripe.SignatureVerificationError as e:
            # Invalid signature - potential security issue
            logger.error(f"Webhook signature verification failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid webhook signature"
            )
        except Exception as e:
            # Unexpected error during signature verification
            logger.error(f"Unexpected error during webhook signature verification: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Webhook signature verification failed"
            )

        # Additional validation of event structure
        if not event or not isinstance(event, dict):
            logger.error("Invalid event structure after signature verification")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid event structure"
            )
        
        if not event.get('type'):
            logger.error("Missing event type in webhook payload")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing event type"
            )

        # Process the event in the background
        service = PaymentService(db)
        background_tasks.add_task(service.handle_stripe_webhook, event)
        
        logger.info(f"Webhook event {event.get('id')} queued for processing")
        return {"status": "success", "event_id": event.get('id')}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error processing Stripe webhook: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process Stripe webhook - {str(e)}"
        )
