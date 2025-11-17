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
from routes.user import get_current_authenticated_user # Import the dependency

# Main router for payment methods
payment_method_router = APIRouter(prefix="/api/v1/users", tags=["Payment Methods"])

# Router for Stripe-related payment operations
payment_router = APIRouter(prefix="/api/v1/payments", tags=["Payments"])

class CreatePaymentIntentRequest(BaseModel):
    order_id: UUID
    amount: float = Field(..., gt=0)
    currency: str = Field("usd", max_length=3)

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
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment method not found")
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
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment method not found")
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
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment method not found")
        return default_method
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to set default payment method - {str(e)}"
        )


@payment_router.post("/create-payment-intent", summary="Create a Stripe Payment Intent")
async def create_payment_intent(
    payload: CreatePaymentIntentRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_user_or_admin_access) # Ensure user is authenticated
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
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@payment_router.post("/stripe-webhook", summary="Handle Stripe webhook events")
async def stripe_webhook(request: Request, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    try:
        # Retrieve the event by verifying the signature using the raw body and secret
        webhook_secret = settings.STRIPE_WEBHOOK_SECRET
        if not webhook_secret:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Stripe webhook secret not configured.")

        event = None
        payload = await request.body()
        sig_header = request.headers.get('stripe-signature')

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, webhook_secret
            )
        except ValueError as e:
            # Invalid payload
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except stripe.error.SignatureVerificationError as e:
            # Invalid signature
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

        # Process the event in the background
        service = PaymentService(db)
        background_tasks.add_task(service.handle_stripe_webhook, event)

        return {"status": "success"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process Stripe webhook - {str(e)}"
        )
