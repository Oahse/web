from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import List, Optional
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
    subtotal: float = Field(..., gt=0)
    currency: Optional[str] = None
    shipping_address_id: Optional[UUID] = None
    payment_method_id: Optional[UUID] = None
    expires_in_minutes: int = Field(30, ge=5, le=120)  # 5 minutes to 2 hours


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


@payment_router.post("/create-payment-intent", summary="Create an enhanced Stripe Payment Intent with tax calculation")
async def create_payment_intent(
    payload: CreatePaymentIntentRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_authenticated_user)
):
    """
    Create a Stripe Payment Intent with enhanced features:
    - Automatic tax calculation based on shipping address
    - Multi-currency support with auto-detection
    - Payment method pre-selection
    - Configurable expiration time
    """
    try:
        service = PaymentService(db)
        result = await service.create_payment_intent(
            user_id=current_user.id,
            order_id=payload.order_id,
            subtotal=payload.subtotal,
            currency=payload.currency,
            shipping_address_id=payload.shipping_address_id,
            payment_method_id=payload.payment_method_id,
            expires_in_minutes=payload.expires_in_minutes
        )
        return {
            "success": True,
            "data": result,
            "message": "Payment intent created successfully"
        }
    except stripe.StripeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=f"Stripe error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Failed to create payment intent: {str(e)}"
        )


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


@payment_router.post("/handle-expiration/{payment_intent_id}", summary="Handle expired payment intent")
async def handle_payment_expiration(
    payment_intent_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_authenticated_user)
):
    """
    Handle expired payment intent by updating status and sending notifications.
    """
    try:
        service = PaymentService(db)
        result = await service.handle_payment_intent_expiration(payment_intent_id)
        
        if result["status"] == "error":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["message"]
            )
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to handle payment expiration: {str(e)}"
        )


@payment_router.get("/supported-currencies", summary="Get supported currencies")
async def get_supported_currencies():
    """Get list of supported currencies with their symbols"""
    from services.tax import TaxService
    
    # Create a temporary instance to access the method
    tax_service = TaxService(None)  # db not needed for this method
    currencies = tax_service.get_supported_currencies()
    
    return {
        "success": True,
        "data": {
            "currencies": currencies,
            "default": "USD"
        },
        "message": "Supported currencies retrieved successfully"
    }


class ConfirmPaymentRequest(BaseModel):
    payment_intent_id: str
    handle_3d_secure: bool = True


@payment_router.post("/confirm", summary="Confirm payment and update order status")
async def confirm_payment(
    payload: ConfirmPaymentRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_authenticated_user)
):
    """
    Confirm payment with enhanced features:
    - Automatic order status update
    - 3D Secure authentication handling
    - Clear error messaging for payment failures
    - Order confirmation notifications
    """
    try:
        service = PaymentService(db)
        result = await service.confirm_payment_and_order(
            payment_intent_id=payload.payment_intent_id,
            user_id=current_user.id,
            handle_3d_secure=payload.handle_3d_secure
        )
        
        # Return appropriate HTTP status based on result
        if result["status"] == "error":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["message"]
            )
        elif result["status"] == "failed":
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=result["message"]
            )
        
        return {
            "success": True,
            "data": result,
            "message": result.get("message", "Payment processed successfully")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to confirm payment: {str(e)}"
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
