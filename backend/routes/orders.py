from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, Query, status, BackgroundTasks, Header
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import Optional
from core.database import get_db
from core.utils.response import Response
from core.exceptions import APIException
from services.orders import OrderService
from models.user import User, Address
from models.orders import Order
from models.shipping import ShippingMethod
from models.payments import PaymentMethod
from services.auth import AuthService
from schemas.orders import OrderCreate, CheckoutRequest
from core.dependencies import get_current_auth_user, get_order_service

from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_auth_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> User:
    auth_service = AuthService(db)
    return await auth_service.get_current_user(token)

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post("/")
async def create_order(
    request: OrderCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_auth_user),
    order_service: OrderService = Depends(get_order_service)
):
    """Create a new order."""
    try:
        order = await order_service.create_order(current_user.id, request, background_tasks)
        return Response.success(data=order, message="Order created successfully")
    except APIException:
        raise
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_400_BAD_REQUEST,
            message=f"Failed to create order: {str(e)}"
        )


@router.post("/checkout/validate")
async def validate_checkout(
    request: CheckoutRequest,
    current_user: User = Depends(get_current_auth_user),
    order_service: OrderService = Depends(get_order_service)
):
    """
    Validate checkout requirements before actual order placement
    This endpoint performs all validation checks without creating an order
    """
    try:
        # Import CartService here to avoid circular imports
        from services.cart import CartService
        
        cart_service = CartService(order_service.db)
        
        # Get location from shipping address if available, otherwise use defaults
        country_code = "US"
        province_code = None
        
        # Try to get shipping address to determine location for tax calculation
        if request.shipping_address_id:
            shipping_address_result = await order_service.db.execute(
                select(Address).where(
                    and_(Address.id == request.shipping_address_id, Address.user_id == current_user.id)
                )
            )
            shipping_address = shipping_address_result.scalar_one_or_none()
            if shipping_address:
                country_code = shipping_address.country or "US"
                province_code = shipping_address.state
        
        # Step 1: Validate cart with location for proper tax calculation
        cart_validation = await cart_service.validate_cart(
            current_user.id,
            country_code=country_code,
            province_code=province_code
        )
        
        if not cart_validation.get("valid", False) or not cart_validation.get("can_checkout", False):
            error_issues = [issue for issue in cart_validation.get("issues", []) if issue.get("severity") == "error"]
            return Response.error(
                message="Cart validation failed",
                data={
                    "cart_validation": cart_validation,
                    "can_proceed": False,
                    "error_count": len(error_issues)
                }
            )
        
        # Step 2: Validate shipping address
        shipping_address = await order_service.db.execute(
            select(Address).where(
                and_(Address.id == request.shipping_address_id, Address.user_id == current_user.id)
            )
        )
        shipping_address = shipping_address.scalar_one_or_none()
        
        # Step 3: Validate shipping method
        shipping_method = await order_service.db.execute(
            select(ShippingMethod).where(ShippingMethod.id == request.shipping_method_id)
        )
        shipping_method = shipping_method.scalar_one_or_none()
        
        # Step 4: Validate payment method
        payment_method = await order_service.db.execute(
            select(PaymentMethod).where(
                and_(PaymentMethod.id == request.payment_method_id, PaymentMethod.user_id == current_user.id)
            )
        )
        payment_method = payment_method.scalar_one_or_none()
        
        # Collect validation results
        validation_results = {
            "cart_validation": cart_validation,
            "shipping_address_valid": shipping_address is not None,
            "shipping_method_valid": shipping_method is not None,
            "payment_method_valid": payment_method is not None,
            "can_proceed": True
        }
        
        # Check for validation failures
        validation_errors = []
        
        if not shipping_address:
            validation_errors.append("Invalid shipping address")
            validation_results["can_proceed"] = False
            
        if not shipping_method:
            validation_errors.append("Invalid shipping method")
            validation_results["can_proceed"] = False
            
        if not payment_method:
            validation_errors.append("Invalid payment method")
            validation_results["can_proceed"] = False
        
        # Calculate estimated totals if validation passes
        if validation_results["can_proceed"]:
            try:
                cart = cart_validation["cart"]
                validated_cart_items = []
                
                # Convert cart items to format expected by price validation
                for item in cart.items:
                    validated_cart_items.append({
                        "variant_id": item.variant_id,
                        "quantity": item.quantity,
                        "backend_price": item.price_per_unit,
                        "backend_total": item.total_price
                    })
                
                # Calculate final totals
                final_total = await order_service._calculate_final_order_total(
                    validated_cart_items,
                    shipping_method,
                    shipping_address
                )
                
                validation_results["estimated_totals"] = final_total
                
            except Exception as e:
                validation_errors.append(f"Failed to calculate totals: {str(e)}")
                validation_results["can_proceed"] = False
        
        validation_results["validation_errors"] = validation_errors
        
        if validation_results["can_proceed"]:
            return Response.success(
                data=validation_results,
                message="Checkout validation successful - ready to place order"
            )
        else:
            return Response.error(
                message="Checkout validation failed",
                data=validation_results
            )
            
    except APIException:
        raise
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Checkout validation failed: {str(e)}"
        )


@router.post("/checkout")
async def checkout(
    request: CheckoutRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_auth_user),
    order_service: OrderService = Depends(get_order_service),
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key")
):
    """
    Place an order from the current cart with comprehensive validation and security checks.
    
    Cart validation is ALWAYS performed before order creation.
    Price tampering protection is enforced.
    Idempotency-Key header prevents duplicate orders from being created.
    If not provided, one will be generated based on cart contents.
    """
    try:
        # Import security service
        from core.middleware.rate_limit import SecurityService
        from fastapi import Request
        
        # Get request object for security checks
        # Note: In a real implementation, you'd get this from the middleware
        # For now, we'll perform price validation in the order service
        
        order = await order_service.place_order_with_security_validation(
            current_user.id, 
            request, 
            background_tasks,
            idempotency_key
        )
        return Response.success(data=order, message="Order placed successfully")
    except APIException:
        raise
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_400_BAD_REQUEST,
            message=f"Failed to place order: {str(e)}"
        )


@router.get("/")
async def get_orders(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    status_filter: Optional[str] = Query(None),
    current_user: User = Depends(get_current_auth_user),
    order_service: OrderService = Depends(get_order_service)
):
    """Get user's orders."""
    try:
        orders = await order_service.get_user_orders(
            current_user.id, page, limit, status_filter
        )
        return Response.success(data=orders)
    except APIException:
        raise
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to fetch orders: {str(e)}"
        )


@router.get("/{order_id}")
async def get_order(
    order_id: UUID,
    current_user: User = Depends(get_current_auth_user),
    order_service: OrderService = Depends(get_order_service)
):
    """Get a specific order."""
    try:
        order = await order_service.get_order_by_id(order_id, current_user.id)
        if not order:
            raise APIException(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Order not found"
            )
        return Response.success(data=order)
    except APIException:
        raise
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to fetch order: {str(e)}"
        )


@router.put("/{order_id}/cancel")
async def cancel_order(
    order_id: UUID,
    current_user: User = Depends(get_current_auth_user),
    order_service: OrderService = Depends(get_order_service)
):
    """Cancel an order."""
    try:
        order = await order_service.cancel_order(order_id, current_user.id)
        return Response.success(data=order, message="Order cancelled successfully")
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_400_BAD_REQUEST,
            message="Failed to cancel order"
        )


@router.get("/{order_id}/tracking")
async def get_order_tracking(
    order_id: UUID,
    current_user: User = Depends(get_current_auth_user),
    order_service: OrderService = Depends(get_order_service)
):
    """Get order tracking information (authenticated)."""
    try:
        tracking = await order_service.get_order_tracking(order_id, current_user.id)
        return Response.success(data=tracking)
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Failed to fetch tracking information"
        )


@router.get("/track/{order_id}")
async def track_order_public(
    order_id: UUID,
    order_service: OrderService = Depends(get_order_service)
):
    """Get order tracking information (public - no authentication required)."""
    try:
        tracking = await order_service.get_order_tracking_public(order_id)
        return Response.success(data=tracking)
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_404_NOT_FOUND,
            message="Order not found or tracking information unavailable"
        )


@router.post("/{order_id}/refund")
async def request_refund(
    order_id: UUID,
    request: dict,
    current_user: User = Depends(get_current_auth_user),
    order_service: OrderService = Depends(get_order_service)
):
    """Request order refund."""
    try:
        result = await order_service.request_refund(order_id, current_user.id, request)
        return Response.success(data=result, message="Refund request submitted")
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_400_BAD_REQUEST,
            message=f"Failed to request refund: {str(e)}"
        )


@router.post("/{order_id}/reorder")
async def reorder(
    order_id: UUID,
    current_user: User = Depends(get_current_auth_user),
    order_service: OrderService = Depends(get_order_service)
):
    """Create new order from existing order."""
    try:
        order = await order_service.reorder(order_id, current_user.id)
        return Response.success(data=order, message="Order recreated successfully")
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_400_BAD_REQUEST,
            message=f"Failed to reorder: {str(e)}"
        )


@router.get("/{order_id}/invoice")
async def get_order_invoice(
    order_id: UUID,
    current_user: User = Depends(get_current_auth_user),
    order_service: OrderService = Depends(get_order_service)
):
    """Get order invoice."""
    from fastapi.responses import FileResponse
    import os
    
    try:
        invoice = await order_service.generate_invoice(order_id, current_user.id)
        
        if 'invoice_path' in invoice and os.path.exists(invoice['invoice_path']):
            file_path = invoice['invoice_path']
            if file_path.endswith('.pdf'):
                return FileResponse(
                    path=file_path,
                    filename="invoice.pdf",
                    media_type="application/pdf"
                )
            else:
                return FileResponse(
                    path=file_path,
                    filename="invoice.docx",
                    media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
        
        return Response.success(data=invoice)
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to generate invoice: {str(e)}"
        )


@router.post("/{order_id}/notes")
async def add_order_note(
    order_id: UUID,
    request: dict,
    current_user: User = Depends(get_current_auth_user),
    order_service: OrderService = Depends(get_order_service)
):
    """Add note to order."""
    try:
        result = await order_service.add_order_note(order_id, current_user.id, request.get("note", ""))
        return Response.success(data=result, message="Note added successfully")
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_400_BAD_REQUEST,
            message=f"Failed to add note: {str(e)}"
        )


@router.get("/{order_id}/notes")
async def get_order_notes(
    order_id: UUID,
    current_user: User = Depends(get_current_auth_user),
    order_service: OrderService = Depends(get_order_service)
):
    """Get order notes."""
    try:
        notes = await order_service.get_order_notes(order_id, current_user.id)
        return Response.success(data=notes)
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Failed to fetch order notes"
        )