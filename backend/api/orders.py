from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, Query, status, BackgroundTasks, Header
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import Optional
from core.db import get_db
from core.utils.response import Response
from core.errors import APIException
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

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post("/")
async def create_order(
    request: OrderCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_auth_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new order from OrderCreate request."""
    try:
        # First, create or get shipping address
        from services.user import AddressService
        address_service = AddressService(db)
        
        # Create shipping address
        shipping_address = await address_service.create_address(
            user_id=current_user.id,
            street=request.shipping_address.street,
            city=request.shipping_address.city,
            state=request.shipping_address.state,
            country=request.shipping_address.country,
            post_code=request.shipping_address.post_code,
            kind="Shipping"
        )
        
        # Get a default shipping method
        from models.shipping import ShippingMethod
        shipping_method_result = await db.execute(
            select(ShippingMethod).where(ShippingMethod.is_active == True).limit(1)
        )
        shipping_method = shipping_method_result.scalar_one_or_none()
        
        if not shipping_method:
            raise APIException(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="No shipping methods available"
            )
        
        # Get or create a payment method (simplified for testing)
        from models.payments import PaymentMethod
        payment_method_result = await db.execute(
            select(PaymentMethod).where(PaymentMethod.user_id == current_user.id).limit(1)
        )
        payment_method = payment_method_result.scalar_one_or_none()
        
        if not payment_method:
            # Create a dummy payment method for testing
            from core.utils.uuid_utils import uuid7
            payment_method = PaymentMethod(
                id=uuid7(),
                user_id=current_user.id,
                type="card",
                provider="stripe",  # Use valid enum value
                last_four="1234",
                is_default=True
            )
            db.add(payment_method)
            await db.commit()
            await db.refresh(payment_method)
        
        # Add items to cart first
        from services.cart import CartService
        cart_service = CartService(db)
        
        for item in request.items:
            await cart_service.add_item_to_cart(
                user_id=current_user.id,
                variant_id=item.variant_id,
                quantity=item.quantity
            )
        
        # Create CheckoutRequest from OrderCreate
        checkout_request = CheckoutRequest(
            shipping_address_id=shipping_address.id,
            shipping_method_id=shipping_method.id,
            payment_method_id=payment_method.id,
            notes=request.notes,
            currency="USD",
            country_code="US"
        )
        
        # Now use the existing place_order method
        order_service = OrderService(db)
        order = await order_service.place_order(current_user.id, checkout_request, background_tasks)
        
        return Response.success(data=order, message="Order created successfully")
    except APIException:
        raise
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_400_BAD_REQUEST,
            message=f"Failed to create order: {str(e)}"
        )


@router.post("/create-payment-intent")
async def create_payment_intent(
    request: dict,
    current_user: User = Depends(get_current_auth_user),
    db: AsyncSession = Depends(get_db)
):
    """Create payment intent for order"""
    try:
        from services.payments import PaymentService
        payment_service = PaymentService(db)
        
        payment_intent = await payment_service.create_payment_intent(
            user_id=current_user.id,
            amount=request.get("amount", 0),
            currency=request.get("currency", "USD"),
            order_id=request.get("order_id"),
            metadata=request.get("metadata", {})
        )
        
        return Response.success(data=payment_intent)
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to create payment intent: {str(e)}"
        )


@router.post("/checkout/validate")
async def validate_checkout(
    request: CheckoutRequest,
    current_user: User = Depends(get_current_auth_user),
    order_service: OrderService = Depends(get_order_service)
):
    """
    Comprehensive checkout validation with pricing calculation
    Returns detailed validation results and pricing breakdown
    """
    try:
        logger.info(f"Validating checkout for user {current_user.id}")
        logger.info(f"Request data: {request.dict()}")
        
        # Perform comprehensive validation
        validation_result = await order_service.validate_checkout_requirements(
            current_user.id, 
            request
        )
        
        logger.info(f"Validation result: valid={validation_result['valid']}, can_proceed={validation_result['can_proceed']}")
        
        if validation_result['valid']:
            return Response.success(
                data=validation_result,
                message="Checkout validation successful"
            )
        else:
            # Return validation errors but still with success=True so frontend can handle
            return Response.success(
                data=validation_result,
                message="Checkout validation completed with issues"
            )
            
    except APIException:
        raise
    except Exception as e:
        logger.error(f"Checkout validation error: {e}")
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Checkout validation failed: {str(e)}"
        )


@router.post("/checkout")
async def place_order(
    request: CheckoutRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_auth_user),
    order_service: OrderService = Depends(get_order_service)
):
    """
    Place order with comprehensive validation and security checks
    """
    try:
        logger.info(f"Placing order for user {current_user.id}")
        
        # Generate idempotency key if not provided
        idempotency_key = request.idempotency_key or f"order_{current_user.id}_{int(datetime.utcnow().timestamp())}"
        
        # Place order with comprehensive validation
        order = await order_service.place_order_with_comprehensive_validation(
            current_user.id,
            request,
            background_tasks,
            idempotency_key
        )
        
        logger.info(f"Order placed successfully: {order.id}")
        
        return Response.success(
            data=order,
            message="Order placed successfully"
        )
        
    except APIException:
        raise
    except Exception as e:
        logger.error(f"Order placement error: {e}")
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Order placement failed: {str(e)}"
        )
        
        # Step 1: Validate cart with location for proper tax calculation
        logger.info("Step 1: Validating cart")    
        
        # First, check if user has any items in cart
        cart_count = await cart_service.get_cart_item_count(current_user.id)
        logger.info(f"User has {cart_count} items in cart")
        
        if cart_count == 0:
            logger.warning("Cart is empty - cannot proceed with checkout")
            return Response.error(
                message="Cart is empty",
                data={
                    "can_proceed": False,
                    "validation_errors": ["Your cart is empty. Please add items before checking out."],
                    "cart_validation": {
                        "valid": False,
                        "can_checkout": False,
                        "issues": [{
                            "issue": "empty_cart",
                            "message": "Cart is empty",
                            "severity": "error"
                        }],
                        "summary": {
                            "total_items_checked": 0,
                            "valid_items": 0,
                            "removed_items": 0,
                            "price_updates": 0,
                            "stock_adjustments": 0,
                            "availability_issues": 0,
                            "cart_updated": False
                        }
                    }
                },
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        cart_validation = await cart_service.validate_cart(
            current_user.id,
            country_code=country_code,
            province_code=province_code
        )
        
        logger.info(f"Cart validation result: valid={cart_validation.get('valid')}, can_checkout={cart_validation.get('can_checkout')}")
        logger.info(f"Cart validation summary: {cart_validation.get('summary', {})}")
        
        # Check if cart has any issues
        issues = cart_validation.get("issues", [])
        if issues:
            logger.info(f"Cart validation found {len(issues)} issues:")
            for issue in issues:
                logger.info(f"  - {issue.get('severity', 'unknown')}: {issue.get('message', 'no message')}")
        
        if not cart_validation.get("valid", False) or not cart_validation.get("can_checkout", False):
            error_issues = [issue for issue in cart_validation.get("issues", []) if issue.get("severity") == "error"]
            all_issues = cart_validation.get("issues", [])
            logger.warning(f"Cart validation failed with {len(error_issues)} errors out of {len(all_issues)} total issues")
            logger.warning(f"Cart validation details: valid={cart_validation.get('valid')}, can_checkout={cart_validation.get('can_checkout')}")
            logger.warning(f"Error issues: {error_issues}")
            
            # Serialize cart_validation to avoid Pydantic serialization issues
            cart_obj = cart_validation.get("cart")
            serialized_cart = None
            if cart_obj:
                # Convert CartResponse to dict
                if hasattr(cart_obj, 'model_dump'):
                    serialized_cart = cart_obj.model_dump()
                elif hasattr(cart_obj, 'dict'):
                    serialized_cart = cart_obj.dict()
                else:
                    serialized_cart = cart_obj
            
            serialized_cart_validation = {
                "valid": cart_validation.get("valid"),
                "can_checkout": cart_validation.get("can_checkout"),
                "cart": serialized_cart,
                "issues": cart_validation.get("issues", []),
                "summary": cart_validation.get("summary", {}),
                "validation_timestamp": cart_validation.get("validation_timestamp"),
                "error": cart_validation.get("error")
            }
            
            return Response.error(
                message="Cart validation failed" if error_issues else "Cart is empty or invalid",
                data={
                    "cart_validation": serialized_cart_validation,
                    "can_proceed": False,
                    "validation_errors": [issue.get("message") for issue in error_issues] if error_issues else ["Cart is empty or has no valid items"],
                    "error_count": len(error_issues)
                },
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Step 2: Validate shipping address
        logger.info("Step 2: Validating shipping address")
        shipping_address = await order_service.db.execute(
            select(Address).where(
                and_(Address.id == request.shipping_address_id, Address.user_id == current_user.id)
            )
        )
        shipping_address = shipping_address.scalar_one_or_none()
        logger.info(f"Shipping address valid: {shipping_address is not None}")
        
        # Step 3: Validate shipping method
        logger.info("Step 3: Validating shipping method")
        shipping_method = await order_service.db.execute(
            select(ShippingMethod).where(ShippingMethod.id == request.shipping_method_id)
        )
        shipping_method = shipping_method.scalar_one_or_none()
        logger.info(f"Shipping method exists: {shipping_method is not None}")
        
        # Simple validation - just check if method exists and is active
        shipping_method_valid = shipping_method is not None and shipping_method.is_active
        
        # Step 4: Validate payment method
        logger.info("Step 4: Validating payment method")
        payment_method = await order_service.db.execute(
            select(PaymentMethod).where(
                and_(PaymentMethod.id == request.payment_method_id, PaymentMethod.user_id == current_user.id)
            )
        )
        payment_method = payment_method.scalar_one_or_none()
        logger.info(f"Payment method valid: {payment_method is not None}")
        
        # Collect validation results
        validation_results = {
            "cart_validation": cart_validation,
            "shipping_address_valid": shipping_address is not None,
            "shipping_method_valid": shipping_method_valid,
            "payment_method_valid": payment_method is not None,
            "can_proceed": True
        }
        
        # Check for validation failures
        validation_errors = []
        
        if not shipping_address:
            validation_errors.append("Invalid or missing shipping address")
            validation_results["can_proceed"] = False
            
        if not shipping_method_valid:
            validation_errors.append("Invalid or missing shipping method")
            validation_results["can_proceed"] = False
            
        if not payment_method:
            validation_errors.append("Invalid or missing payment method")
            validation_results["can_proceed"] = False
        
        # Calculate estimated totals if validation passes
        if validation_results["can_proceed"]:
            try:
                logger.info("Calculating estimated totals")
                cart = cart_validation["cart"]
                validated_cart_items = []
                
                # Handle both CartResponse object and dict
                if hasattr(cart, 'items'):
                    # It's a Pydantic CartResponse object
                    cart_items = cart['items']
                    logger.info(f"Cart is a Pydantic object with {len(cart_items)} items")
                elif isinstance(cart, dict) and 'items' in cart:
                    # It's a dictionary
                    cart_items = cart['items']
                    logger.info(f"Cart is a dict with {len(cart_items)} items")
                else:
                    raise ValueError(f"Unexpected cart structure: {type(cart)}")
                
                logger.info(f"Processing {len(cart_items)} cart items for totals calculation")
                
                for idx, item in enumerate(cart_items):
                    try:
                        # Handle both Pydantic CartItemResponse and dict
                        if hasattr(item, 'variant'):
                            # Pydantic CartItemResponse object
                            variant = item.variant
                            if hasattr(variant, 'id'):
                                variant_id = variant.id
                            else:
                                variant_id = variant
                            quantity = item.quantity
                            price_per_unit = item.price_per_unit
                            total_price = item.total_price
                            logger.debug(f"Item {idx}: Pydantic object, variant_id={variant_id}, type(item)={type(item)}, type(variant)={type(variant)}")
                        elif isinstance(item, dict):
                            # Dictionary format
                            variant_data = item.get('variant', {})
                            if isinstance(variant_data, dict):
                                variant_id = variant_data.get('id')
                            else:
                                variant_id = variant_data
                            quantity = item.get('quantity', 0)
                            price_per_unit = item.get('price_per_unit', 0.0)
                            total_price = item.get('total_price', 0.0)
                            logger.debug(f"Item {idx}: Dict, variant_id={variant_id}")
                        else:
                            logger.error(f"Item {idx}: Unexpected type {type(item)}, item={item}")
                            raise ValueError(f"Unexpected item structure at index {idx}: {type(item)}")
                        
                        validated_cart_items.append({
                            "variant_id": variant_id,
                            "quantity": quantity,
                            "backend_price": price_per_unit,
                            "backend_total": total_price
                        })
                    except Exception as item_error:
                        logger.error(f"Error processing cart item {idx}: {str(item_error)}", exc_info=True)
                        raise
                
                logger.info(f"Successfully processed {len(validated_cart_items)} items")
                
                # Calculate final totals
                final_total = await order_service._calculate_final_order_total(
                    validated_cart_items,
                    shipping_method,
                    shipping_address
                )
                
                validation_results["estimated_totals"] = final_total
                logger.info(f"Estimated total: {final_total.get('total_amount')}")
                
            except Exception as e:
                logger.error(f"Failed to calculate totals: {str(e)}", exc_info=True)
                logger.error(f"Cart type: {type(cart)}")
                if hasattr(cart, 'items'):
                    logger.error(f"Cart.items type: {type(cart.items)}")
                    if cart.items:
                        logger.error(f"First item type: {type(cart.items[0])}")
                        logger.error(f"First item: {cart.items[0]}")
                elif isinstance(cart, dict) and 'items' in cart:
                    logger.error(f"Cart['items'] type: {type(cart['items'])}")
                    if cart['items']:
                        logger.error(f"First item type: {type(cart['items'][0])}")
                        logger.error(f"First item: {cart['items'][0]}")
                validation_errors.append(f"Failed to calculate totals: {str(e)}")
                validation_results["can_proceed"] = False
        
        validation_results["validation_errors"] = validation_errors
        
        # Serialize cart_validation to ensure proper JSON serialization
        if "cart_validation" in validation_results:
            cart_val = validation_results["cart_validation"]
            cart_obj = cart_val.get("cart")
            if cart_obj and hasattr(cart_obj, 'model_dump'):
                cart_val["cart"] = cart_obj.model_dump()
            elif cart_obj and hasattr(cart_obj, 'dict'):
                cart_val["cart"] = cart_obj.dict()
        
        if validation_results["can_proceed"]:
            logger.info("Checkout validation successful")
            return Response.success(
                data=validation_results,
                message="Checkout validation successful - ready to place order"
            )
        else:
            logger.warning(f"Checkout validation failed: {validation_errors}")
            return Response.error(
                message="Checkout validation failed",
                data=validation_results,
                status_code=status.HTTP_400_BAD_REQUEST
            )
            
    except APIException:
        raise
    except Exception as e:
        logger.error(f"Checkout validation error: {str(e)}", exc_info=True)
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Checkout validation failed: {str(e)}"
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


@router.get("/supplier/orders")
async def get_supplier_orders(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    status_filter: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    current_user: User = Depends(get_current_auth_user),
    order_service: OrderService = Depends(get_order_service)
):
    """Get supplier's orders"""
    try:
        # Check if user is a supplier
        if current_user.role != "supplier":
            raise APIException(
                status_code=status.HTTP_403_FORBIDDEN,
                message="Access denied. Supplier role required."
            )
        
        orders = await order_service.get_supplier_orders(
            supplier_id=current_user.id,
            page=page,
            limit=limit,
            status_filter=status_filter,
            date_from=date_from,
            date_to=date_to
        )
        return Response.success(data=orders)
    except APIException:
        raise
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to fetch supplier orders: {str(e)}"
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
        invoice_result = await order_service.generate_invoice(order_id, current_user.id)
        if invoice_result.get('success') and invoice_result.get('pdf_bytes'):
            # Return PDF bytes as response
            from fastapi.responses import Response
            return Response(
                content=invoice_result['pdf_bytes'],
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f"attachment; filename=invoice-{invoice_result.get('invoice_ref', 'unknown')}.pdf"
                }
            )
        else:
            raise APIException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=invoice_result.get('message', 'Failed to generate invoice')
            )
            
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