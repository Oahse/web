# Consolidated order service
# This file includes all order-related functionality

import hashlib
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, BackgroundTasks
from models.orders import Order, OrderItem, TrackingEvent
from models.cart import Cart, CartItem
from models.user import User, Address
from models.product import ProductVariant
from models.shipping import ShippingMethod
from models.payments import PaymentMethod
from models.tax_rates import TaxRate
from schemas.orders import OrderResponse, OrderItemResponse, CheckoutRequest, OrderCreate
from schemas.inventories import StockAdjustmentCreate
from services.cart import CartService
from services.payments import PaymentService
from services.inventories import InventoryService 
from models.inventories import Inventory
from uuid import UUID
from core.utils.uuid_utils import uuid7
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from core.config import settings
from core.logging import get_structured_logger

logger = get_structured_logger(__name__)


class OrderService:
    """Consolidated order service with comprehensive order management"""
    
    def __init__(self, db: AsyncSession, lock_service=None):
        self.db = db
        self.inventory_service = InventoryService(db, lock_service)

    async def place_order_with_security_validation(
        self, 
        user_id: UUID, 
        request: CheckoutRequest, 
        background_tasks: BackgroundTasks,
        idempotency_key: Optional[str] = None
    ) -> OrderResponse:
        """
        Place an order with comprehensive security validation including price tampering protection
        """
        # Import security service
        from core.middleware.rate_limit import SecurityService
        
        # Initialize security service
        security_service = SecurityService()
        
        # Get client identifier for security tracking
        client_id = f"user:{user_id}"
        
        # Get location from shipping address for tax calculation
        country_code = "US"
        province_code = None
        if hasattr(request, 'shipping_address_id') and request.shipping_address_id:
            shipping_address_result = await self.db.execute(
                select(Address).where(Address.id == request.shipping_address_id)
            )
            shipping_address = shipping_address_result.scalar_one_or_none()
            if shipping_address:
                country_code = shipping_address.country or "US"
                province_code = shipping_address.state
        
        # STEP 1: Validate cart and get current prices with location for tax
        cart_service = CartService(self.db)
        validation_result = await cart_service.validate_cart(
            user_id,
            country_code=country_code,
            province_code=province_code
        )
        
        if not validation_result.get("valid", False) or not validation_result.get("can_checkout", False):
            error_issues = [issue for issue in validation_result.get("issues", []) if issue.get("severity") == "error"]
            if error_issues:
                error_messages = [issue["message"] for issue in error_issues]
                raise HTTPException(
                    status_code=400, 
                    detail={
                        "message": "Cart validation failed. Please review and update your cart.",
                        "issues": error_issues,
                        "validation_summary": validation_result.get("summary", {}),
                        "error_count": len(error_issues)
                    }
                )
        
        cart = validation_result["cart"]
        
        # STEP 2: Price tampering detection
        if hasattr(request, 'submitted_prices') and request.submitted_prices:
            # Extract actual prices from validated cart
            actual_prices = {}
            for item in cart.items:
                actual_prices[str(item.variant.id)] = float(item.price_per_unit)
            
            # Check for price tampering
            tampering_result = await security_service.detect_price_tampering(
                client_id, request.submitted_prices, actual_prices
            )
            
            if tampering_result.get("blocked"):
                if tampering_result["reason"] == "account_suspended":
                    raise HTTPException(status_code=403, detail=tampering_result["message"])
                else:
                    raise HTTPException(status_code=400, detail=tampering_result["message"])
        
        # STEP 3: Proceed with regular order placement
        return await self.place_order_with_idempotency(user_id, request, background_tasks, idempotency_key)

    async def place_order_with_idempotency(
        self, 
        user_id: UUID, 
        request: CheckoutRequest, 
        background_tasks: BackgroundTasks,
        idempotency_key: Optional[str] = None
    ) -> OrderResponse:
        """
        Place an order with idempotency protection
        Prevents duplicate orders from being created
        """
        # Generate idempotency key if not provided
        if not idempotency_key:
            # Create deterministic key based on user, cart state, and timestamp
            cart_service = CartService(self.db)
            cart = await cart_service.get_or_create_cart(user_id)
            
            # Create hash of cart contents + user + shipping details
            cart_hash = self._generate_cart_hash(cart, request)
            idempotency_key = f"order_{user_id}_{cart_hash}"
        
        # Check if order already exists with this idempotency key (with lock to prevent duplicates)
        existing_order = await self.db.execute(
            select(Order).where(Order.idempotency_key == idempotency_key).with_for_update()
        )
        existing = await existing_order.scalar_one_or_none()
        
        if existing:
            # Return existing order
            return await self._convert_order_to_response(existing)
        
        # If no existing order, delegate to the main place_order method
        return await self.place_order(user_id, request, background_tasks, idempotency_key)
    
    async def request_refund(
        self, 
        order_id: UUID, 
        user_id: UUID, 
        refund_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Request a refund for an order
        Delegates to the RefundService for comprehensive refund processing
        """
        try:
            from services.refunds import RefundService
            from schemas.refunds import RefundRequest
            
            # Create refund service
            refund_service = RefundService(self.db)
            
            # Convert refund_data to RefundRequest schema
            refund_request = RefundRequest(**refund_data)
            
            # Process refund request
            refund_response = await refund_service.request_refund(
                user_id=user_id,
                order_id=order_id,
                refund_request=refund_request
            )
            
            return refund_response.dict()
            
        except Exception as e:
            logger.error(f"Failed to request refund for order {order_id}: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to process refund request: {str(e)}"
            )

    async def place_order(
        self, 
        user_id: UUID, 
        request: CheckoutRequest, 
        background_tasks: BackgroundTasks,
        idempotency_key: Optional[str] = None
    ) -> OrderResponse:
        """
        Place an order from the user's cart with comprehensive validation and atomic operations
        ALWAYS validates cart before proceeding with checkout
        """
        # Generate idempotency key if not provided
        if not idempotency_key:
            cart_service = CartService(self.db)
            cart = await cart_service.get_or_create_cart(user_id)
            cart_hash = self._generate_cart_hash(cart, request)
            idempotency_key = f"order_{user_id}_{cart_hash}"
        
        # Check for existing order with this idempotency key
        existing_order = await self.db.execute(
            select(Order).where(Order.idempotency_key == idempotency_key)
        )
        existing = await existing_order.scalar_one_or_none()
        
        if existing:
            logger.info(f"Returning existing order for idempotency key: {idempotency_key}")
            return await self._convert_order_to_response(existing)
        
        # Start atomic transaction for entire checkout process
        async with self.db.begin():
            try:
                # STEP 1: MANDATORY CART VALIDATION - Never skip this step
                cart_service = CartService(self.db)
                
                # Get location from shipping address for tax calculation
                country_code = "US"
                province_code = None
                if hasattr(request, 'shipping_address_id') and request.shipping_address_id:
                    shipping_address_result = await self.db.execute(
                        select(Address).where(Address.id == request.shipping_address_id)
                    )
                    shipping_address = shipping_address_result.scalar_one_or_none()
                    if shipping_address:
                        country_code = shipping_address.country or "US"
                        province_code = shipping_address.state
                
                # Always validate cart first - this is critical for data integrity
                validation_result = await cart_service.validate_cart(
                    user_id,
                    country_code=country_code,
                    province_code=province_code
                )
                
                if not validation_result.get("valid", False) or not validation_result.get("can_checkout", False):
                    # Cart validation failed - return detailed error
                    error_issues = [issue for issue in validation_result.get("issues", []) if issue.get("severity") == "error"]
                    if error_issues:
                        error_messages = [issue["message"] for issue in error_issues]
                        raise HTTPException(
                            status_code=400, 
                            detail={
                                "message": "Cart validation failed. Please review and update your cart.",
                                "issues": error_issues,
                                "validation_summary": validation_result.get("summary", {}),
                                "error_count": len(error_issues)
                            }
                        )
                    else:
                        raise HTTPException(status_code=400, detail="Cart is empty or invalid")
                
                # Get validated cart
                cart = validation_result["cart"]
                
                # Check if cart has items after validation
                active_items = [item for item in cart.items if not getattr(item, 'saved_for_later', False)]
                if not active_items:
                    raise HTTPException(status_code=400, detail="No items available for checkout after validation")
                
                # Log validation results for monitoring
                validation_summary = validation_result.get("summary", {})
                if validation_summary.get("price_updates", 0) > 0 or validation_summary.get("stock_adjustments", 0) > 0:
                    logger.info(f"Cart validation updated items for user {user_id}: {validation_summary}")
                
                # STEP 2: BACKEND PRICE VALIDATION - Never trust frontend prices
                price_validation_result = await self._validate_and_recalculate_prices(cart)
                if not price_validation_result["valid"]:
                    raise HTTPException(
                        status_code=400, 
                        detail=f"Price validation failed: {price_validation_result['message']}"
                    )
                
                # Use backend-calculated prices, not frontend prices
                validated_cart_items = price_validation_result["validated_items"]
                backend_calculated_total = price_validation_result["total_amount"]
                price_updates = price_validation_result.get("price_updates", [])
                
                # STEP 3: CHECK STOCK AVAILABILITY (optimized for Checkout)
                stock_validation_results = []
                for item in active_items:
                    stock_check = await self.inventory_service.check_stock_availability(
                        variant_id=item.variant.id,
                        quantity=item.quantity
                    )
                    
                    if not stock_check.get("available", False):
                        stock_validation_results.append({
                            "variant_id": item.variant.id,
                            "product_name": item.variant.product.name if item.variant and item.variant.product else "Unknown Product",
                            "requested": item.quantity,
                            "available": stock_check.get("current_stock", 0),
                            "status": stock_check.get("stock_status", "out_of_stock"),
                            "message": stock_check.get("message", "Out of stock")
                        })
                
                # If any stock issues, return detailed error
                if stock_validation_results:
                    raise HTTPException(
                        status_code=400,
                        detail={
                            "message": "Stock validation failed",
                            "stock_issues": stock_validation_results,
                            "error_type": "STOCK_UNAVAILABLE"
                        }
                    )
                
                # STEP 4: VALIDATE CHECKOUT DEPENDENCIES
                # Verify shipping address exists
                shipping_address = await self.db.execute(
                    select(Address).where(
                        and_(Address.id == request.shipping_address_id, Address.user_id == user_id))
                )
                shipping_address = shipping_address.scalar_one_or_none()
                if not shipping_address:
                    raise HTTPException(status_code=404, detail="Shipping address not found")

                # Verify shipping method exists and get its cost
                shipping_method = await self.db.execute(
                    select(ShippingMethod).where(ShippingMethod.id == request.shipping_method_id)
                )
                shipping_method = shipping_method.scalar_one_or_none()
                if not shipping_method:
                    raise HTTPException(status_code=404, detail="Shipping method not found")

                # Verify payment method exists
                payment_method = await self.db.execute(
                    select(PaymentMethod).where(and_(PaymentMethod.id == request.payment_method_id, PaymentMethod.user_id == user_id))
                )
                payment_method = payment_method.scalar_one_or_none() 
            except HTTPException:
                # Re-raise HTTP exceptions to be handled by outer transaction
                raise
        
        # Initialize payment_method to None if not set, and handle validation
        if not request.payment_method_id:
            payment_method = None
        
        if payment_method is None: # This covers both cases: not provided, or provided but not found
            raise HTTPException(status_code=404, detail="Payment method not found")

        # STEP 4: CALCULATE FINAL TOTAL (backend calculation only)
        final_total = await self._calculate_final_order_total(
            validated_cart_items, 
            shipping_method, 
            shipping_address
        )

        # STEP 5: ATOMIC TRANSACTION FOR ORDER CREATION
        try:
            # Begin transaction - all operations below must succeed or all will be rolled back
            async with self.db.begin():
                # Generate order number
                order_number = f"ORD-{datetime.utcnow().strftime('%Y%m%d')}-{str(uuid7())[:8].upper()}"
                
                # Extract totals from final_total calculation
                subtotal = final_total["subtotal"]
                tax_amount = final_total["tax_amount"]
                shipping_amount = final_total["shipping_cost"]
                discount_amount = final_total["discount_amount"]
                total_amount = final_total["total_amount"]
                
                # Convert addresses to dict format for JSONB storage
                billing_address_dict = {
                    "street": shipping_address.street,
                    "city": shipping_address.city,
                    "state": shipping_address.state,
                    "country": shipping_address.country,
                    "postal_code": shipping_address.post_code,
                }
                
                # Use shipping address as billing address if no separate billing address
                shipping_address_dict = billing_address_dict.copy()
                
                # Create order with backend-calculated prices and idempotency key
                order = Order(
                    user_id=user_id,
                    status="pending",
                    order_number=order_number,
                    subtotal=subtotal,
                    tax_amount=tax_amount,
                    shipping_amount=shipping_amount,
                    discount_amount=discount_amount,
                    total_amount=total_amount,
                    currency=request.currency or "USD",  # Use user's currency from frontend
                    shipping_method=shipping_method.name,
                    tracking_number=None,
                    carrier=None,
                    billing_address=billing_address_dict,
                    shipping_address=shipping_address_dict,
                    shipping_address_id=request.shipping_address_id,
                    shipping_method_id=request.shipping_method_id,
                    payment_method_id=request.payment_method_id,
                    promocode_id=getattr(cart, 'promocode_id', None),
                    notes=request.notes,
                    idempotency_key=idempotency_key,
                    payment_status="pending",
                    fulfillment_status="unfulfilled",
                    order_status="pending",
                    source="web"
                )
                self.db.add(order)
                await self.db.flush()  # Get order ID without committing

                # Create order items with validated backend prices and atomic stock operations
                for validated_item in validated_cart_items:
                    # Atomically check and decrement stock in single operation
                    try:
                        stock_result = await self.inventory_service.decrement_stock_on_purchase(
                            variant_id=validated_item["variant_id"],
                            quantity=validated_item["quantity"],
                            location_id=None,  # Will be determined by service
                            order_id=order.id,
                            user_id=user_id
                        )
                        
                        if not stock_result["success"]:
                            raise HTTPException(
                                status_code=400, 
                                detail=f"Insufficient stock for variant {validated_item['variant_id']}: {stock_result.get('message', 'Stock unavailable')}"
                            )
                        
                        order_item = OrderItem(
                            order_id=order.id,
                            variant_id=validated_item["variant_id"],
                            quantity=validated_item["quantity"],
                            price_per_unit=validated_item["backend_price"],  # Use backend price
                            total_price=validated_item["backend_total"]     # Use backend total
                        )
                        self.db.add(order_item)
                        
                    except Exception as e:
                        # If stock decrement fails, rollback will happen automatically
                        logger.error(f"Stock decrement failed for variant {validated_item['variant_id']}: {e}")
                        raise HTTPException(
                            status_code=400,
                            detail=f"Stock unavailable for variant {validated_item['variant_id']}"
                        )

                # Process payment with backend-calculated amount and idempotency
                payment_service = PaymentService(self.db)
                payment_idempotency_key = f"payment_{order.id}_{idempotency_key}" if idempotency_key else None
                
                try:
                    payment_result = await payment_service.process_payment_idempotent(
                        user_id=user_id,
                        order_id=order.id,
                        amount=final_total["total_amount"],  # Use backend-calculated total
                        payment_method_id=request.payment_method_id,
                        idempotency_key=payment_idempotency_key,
                        request_id=str(uuid7())
                    )

                    if payment_result.get("status") != "succeeded":
                        # Payment failed - update order status and restore inventory
                        order.status = "payment_failed"
                        order.failure_reason = payment_result.get("error", "Payment processing failed")
                        
                        # Restore inventory for all items
                        for validated_item in validated_cart_items:
                            try:
                                await self.inventory_service.increment_stock_on_cancellation(
                                    variant_id=validated_item["variant_id"],
                                    quantity=validated_item["quantity"],
                                    location_id=None,  # Will be determined by service
                                    order_id=order.id,
                                    user_id=user_id
                                )
                            except Exception as restore_error:
                                logger.error(f"Failed to restore inventory for variant {validated_item['variant_id']}: {restore_error}")
                        
                        error_message = payment_result.get("error", "Payment processing failed")
                        raise HTTPException(status_code=400, detail=f"Payment failed: {error_message}")

                    # Payment succeeded - update order status
                    order.status = "confirmed"
                    order.version += 1  # Optimistic locking increment
                    
                except Exception as payment_error:
                    # Payment processing failed - update order and restore inventory
                    order.status = "payment_failed"
                    order.failure_reason = str(payment_error)
                    
                    # Restore inventory for all items
                    for validated_item in validated_cart_items:
                        try:
                            await self.inventory_service.increment_stock_on_cancellation(
                                variant_id=validated_item["variant_id"],
                                quantity=validated_item["quantity"],
                                location_id=None,
                                order_id=order.id,
                                user_id=user_id
                            )
                        except Exception as restore_error:
                            logger.error(f"Failed to restore inventory for variant {validated_item['variant_id']}: {restore_error}")
                    
                    raise

                # Create initial tracking event
                tracking_event = TrackingEvent(
                    order_id=order.id,
                    status="confirmed",
                    description="Order confirmed and payment processed",
                    location="Processing Center"
                )
                self.db.add(tracking_event)

                # Clear cart after successful order (validated cart)
                await cart_service.clear_cart(user_id=user_id)

                # Transaction will auto-commit here if no exceptions occurred
                
            # Refresh order after transaction commit
            await self.db.refresh(order)
            
            # Send ARQ events with idempotency after successful transaction commit
            try:
                await self._send_order_events_with_idempotency(order, user_id, validated_cart_items)
            except Exception as arq_error:
                # Log ARQ errors but don't fail the order
                logger.error(f"Failed to send order events for order {order.id}: {arq_error}")
                # Order is still successful even if events fail
                
        except HTTPException:
            # Re-raise HTTP exceptions (validation errors, payment failures, etc.)
            raise
        except Exception as e:
            # Any other exception during transaction will auto-rollback
            raise HTTPException(status_code=500, detail=f"Order processing failed: {str(e)}")

        return await self._format_order_response(order)

    async def get_user_orders(self, user_id: UUID, page: int = 1, limit: int = 10, status_filter: Optional[str] = None) -> Dict[str, Any]:
        """Get paginated list of user's orders"""
        
        query = select(Order).where(Order.user_id == user_id).options(
            selectinload(Order.items).selectinload(OrderItem.variant).selectinload(ProductVariant.images),
            selectinload(Order.items).selectinload(OrderItem.variant).selectinload(ProductVariant.product)
        )

        if status_filter:
            query = query.where(Order.status == status_filter)

        query = query.order_by(desc(Order.created_at))

        # Calculate offset
        offset = (page - 1) * limit

        # Get total count
        count_query = select(Order).where(Order.user_id == user_id)
        if status_filter:
            count_query = count_query.where(Order.status == status_filter)

        total_result = await self.db.execute(count_query)
        total = len(total_result.scalars().all())

        # Get paginated results
        result = await self.db.execute(query.offset(offset).limit(limit))
        orders = result.scalars().all()

        formatted_orders = []
        for order in orders:
            formatted_orders.append(await self._format_order_response(order))

        return {
            "orders": formatted_orders,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "pages": (total + limit - 1) // limit
            }
        }

    async def get_order_by_id(self, order_id: UUID, user_id: UUID) -> Optional[OrderResponse]:
        """Get a specific order by ID"""
        
        query = select(Order).where(and_(Order.id == order_id, Order.user_id == user_id)).options(
            selectinload(Order.items).selectinload(OrderItem.variant).selectinload(ProductVariant.images),
            selectinload(Order.items).selectinload(OrderItem.variant).selectinload(ProductVariant.product)
        )

        result = await self.db.execute(query)
        order = result.scalar_one_or_none()

        if not order:
            return None

        return await self._format_order_response(order)

    async def cancel_order(self, order_id: UUID, user_id: UUID) -> OrderResponse:
        """Cancel an order with transaction safety"""
        query = select(Order).where(and_(Order.id == order_id, Order.user_id == user_id)).with_for_update()
        result = await self.db.execute(query)
        order = result.scalar_one_or_none()

        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        if order.status not in ["pending", "confirmed"]:
            raise HTTPException(status_code=400, detail="Order cannot be cancelled")

        # Use transaction for order cancellation
        try:
            async with self.db.begin():
                order.status = "cancelled"

                # Increment stock for cancelled order items
                query_items = select(OrderItem).where(OrderItem.order_id == order.id).options(
                    selectinload(OrderItem.variant).selectinload(ProductVariant.inventory)
                )
                order_items_with_inventory = (await self.db.execute(query_items)).scalars().all()

                for item in order_items_with_inventory:
                    if not item.variant or not item.variant.inventory:
                        print(f"Warning: No inventory found for variant {item.variant_id} during order cancellation.")
                        continue
                    
                    # Use new increment stock method for cancellations
                    await self.inventory_service.increment_stock_on_cancellation(
                        variant_id=item.variant.id,
                        quantity=item.quantity,
                        location_id=item.variant.inventory.location_id,
                        order_id=order.id,
                        user_id=user_id
                    )

                # Add tracking event
                tracking_event = TrackingEvent(
                    order_id=order.id,
                    status="cancelled",
                    description="Order cancelled by customer",
                    location="System"
                )
                self.db.add(tracking_event)

                # Transaction will auto-commit here
                
            # Refresh order after transaction commit
            await self.db.refresh(order)

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Order cancellation failed: {str(e)}")

        return await self._format_order_response(order)

    async def update_order_status(
        self, 
        order_id: UUID, 
        status: str, 
        tracking_number: Optional[str] = None,
        carrier_name: Optional[str] = None,
        location: Optional[str] = None,
        description: Optional[str] = None
    ) -> Order:
        """Update order status (admin function)"""
        query = select(Order).where(Order.id == order_id)
        result = await self.db.execute(query)
        order = result.scalar_one_or_none()

        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        order.status = status
        if tracking_number:
            order.tracking_number = tracking_number
        if carrier_name:
            order.carrier_name = carrier_name

        # Generate appropriate description based on status
        if not description:
            status_descriptions = {
                'pending': 'Order placed and awaiting confirmation',
                'confirmed': 'Order confirmed and payment processed',
                'processing': 'Order is being prepared for shipment',
                'shipped': 'Package has been shipped and is in transit',
                'out_for_delivery': 'Package is out for delivery',
                'delivered': 'Package has been successfully delivered',
                'cancelled': 'Order has been cancelled'
            }
            description = status_descriptions.get(status, f"Order status updated to {status}")

        # Determine location based on status if not provided
        if not location:
            location_map = {
                'pending': 'System',
                'confirmed': 'Processing Center',
                'processing': 'Warehouse',
                'shipped': 'In Transit',
                'out_for_delivery': 'Local Distribution Center',
                'delivered': 'Delivery Address',
                'cancelled': 'System'
            }
            location = location_map.get(status, 'Fulfillment Center')

        # Add tracking event
        tracking_event = TrackingEvent(
            order_id=order.id,
            status=status,
            description=description,
            location=location
        )
        self.db.add(tracking_event)

        await self.db.commit()
        await self.db.refresh(order)
        
        # Send notification to user about status change
        from services.notifications import NotificationService
        notification_service = NotificationService(self.db)
        await notification_service.create_notification(
            user_id=order.user_id,
            message=f"Your order #{order_id} status has been updated to {status}",
            type="info",
            related_id=str(order_id)
        )
        
        return order

    async def _format_order_response(self, order: Order) -> OrderResponse:
        """Format order for response"""
        items = []
        for item in order.items:
            # Include variant details with images
            variant_data = None
            if item.variant:
                variant_data = {
                    "id": str(item.variant.id),
                    "name": item.variant.name,
                    "product_name": item.variant.product.name if item.variant.product else None,
                    "product_id": str(item.variant.product_id) if item.variant.product_id else None,
                    "sku": item.variant.sku,
                    "images": [
                        {
                            "id": str(img.id),
                            "url": img.url,
                            "is_primary": img.is_primary,
                            "sort_order": img.sort_order
                        }
                        for img in item.variant.images
                    ] if item.variant.images else []
                }
            
            items.append(OrderItemResponse(
                id=str(item.id),
                variant_id=str(item.variant.id),
                quantity=item.quantity,
                price_per_unit=item.price_per_unit,
                total_price=item.total_price,
                variant=variant_data
            ))

        # Calculate estimated delivery
        estimated_delivery = None
        if order.status in ["confirmed", "shipped"]:
            estimated_days = 5  # Default, could be from shipping method
            estimated_delivery = (order.created_at + timedelta(days=estimated_days)).isoformat()

        return OrderResponse(
            id=str(order.id),
            user_id=str(order.user_id),
            status=order.status,
            total_amount=order.total_amount,
            subtotal=order.subtotal,
            tax_amount=order.tax_amount,
            shipping_amount=order.shipping_amount,
            discount_amount=order.discount_amount,
            currency=order.currency,  # Use order's currency
            tracking_number=order.tracking_number,
            estimated_delivery=estimated_delivery,
            items=items,
            created_at=order.created_at.isoformat() if order.created_at else ""
        )

    async def _validate_and_recalculate_prices(self, cart) -> Dict[str, Any]:
        """
        CRITICAL SECURITY: Validate all prices against current database prices
        Never trust frontend prices - always recalculate on backend
        """
        try:
            validated_items = []
            total_discrepancies = []
            price_updates = []  # Track items with price changes for frontend notification
            
            active_cart_items = [item for item in cart.items if not getattr(item, 'saved_for_later', False)]
            
            for cart_item in active_cart_items:
                # Fetch current variant details from database
                variant_result = await self.db.execute(
                    select(ProductVariant).where(ProductVariant.id == cart_item.variant.id).options(
                        selectinload(ProductVariant.product)
                    )
                )
                variant = variant_result.scalar_one_or_none()
                
                if not variant:
                    return {
                        "valid": False,
                        "message": f"Product variant {cart_item.variant.id} no longer exists"
                    }
                
                # Get current backend price (sale_price takes precedence over base_price)
                backend_price = variant.sale_price if variant.sale_price else variant.base_price
                backend_total = backend_price * cart_item.quantity
                
                # Compare with cart price (allow small floating point differences)
                price_difference = abs(backend_price - cart_item.price_per_unit)
                total_difference = abs(backend_total - cart_item.total_price)
                
                if price_difference > 0.01 or total_difference > 0.01:
                    discrepancy_info = {
                        "variant_id": str(cart_item.variant.id),
                        "product_name": variant.product.name if variant.product else "Unknown",
                        "variant_name": variant.name,
                        "cart_price": cart_item.price_per_unit,
                        "backend_price": backend_price,
                        "difference": price_difference
                    }
                    total_discrepancies.append(discrepancy_info)
                    
                    # Add to price updates for frontend notification
                    price_updates.append({
                        "variant_id": str(cart_item.variant.id),
                        "product_name": variant.product.name if variant.product else "Unknown",
                        "variant_name": variant.name,
                        "old_price": cart_item.price_per_unit,
                        "new_price": backend_price,
                        "quantity": cart_item.quantity,
                        "old_total": cart_item.total_price,
                        "new_total": backend_total,
                        "is_sale": variant.sale_price is not None,
                        "price_increased": backend_price > cart_item.price_per_unit
                    })
                
                # Always use backend-calculated prices
                validated_items.append({
                    "variant_id": cart_item.variant.id,
                    "quantity": cart_item.quantity,
                    "cart_price": cart_item.price_per_unit,
                    "backend_price": backend_price,
                    "backend_total": backend_total,
                    "product_name": variant.product.name if variant.product else "Unknown",
                    "variant_name": variant.name
                })
            
            # Calculate backend subtotal
            backend_subtotal = sum(item["backend_total"] for item in validated_items)
            
            # If there are price discrepancies, we can either:
            # 1. Reject the order (strict security)
            # 2. Accept with backend prices (user-friendly)
            # For security, we'll log discrepancies but use backend prices
            
            if total_discrepancies:
                from core.logging import structured_logger
                structured_logger.warning(
                    message="Price discrepancies detected during checkout",
                    metadata={
                        "discrepancies": total_discrepancies,
                        "total_items": len(validated_items)
                    }
                )
            
            return {
                "valid": True,
                "validated_items": validated_items,
                "backend_subtotal": backend_subtotal,
                "total_amount": backend_subtotal,  # Will be updated with shipping/tax
                "price_discrepancies": total_discrepancies,
                "price_updates": price_updates  # For frontend notification
            }
            
        except Exception as e:
            return {
                "valid": False,
                "message": f"Price validation failed: {str(e)}"
            }

    async def _calculate_final_order_total(
        self, 
        validated_items: List[Dict], 
        shipping_method, 
        shipping_address
    ) -> Dict[str, float]:
        """
        Calculate final order total with shipping, taxes, and discounts
        All calculations done on backend - never trust frontend
        """
        try:
            # Calculate subtotal from validated backend prices
            subtotal = sum(item["backend_total"] for item in validated_items)
            
            # Calculate shipping cost using simplified logic
            shipping_cost = 0.0
            if shipping_method:
                # Use ShippingService for proper calculation
                from services.shipping import ShippingService
                shipping_service = ShippingService(self.db)
                
                # Extract address info for shipping calculation
                address_dict = {
                    'country': shipping_address.get('country', 'US'),
                    'state': shipping_address.get('state'),
                    'city': shipping_address.get('city'),
                    'postal_code': shipping_address.get('postal_code')
                }
                
                shipping_cost = await shipping_service.calculate_shipping_cost(
                    cart_subtotal=subtotal,
                    address=address_dict,
                    shipping_method_id=shipping_method.id if hasattr(shipping_method, 'id') else None
                )
            
            # Calculate tax based on shipping address (tax applies to subtotal + shipping)
            tax_rate = await self._get_tax_rate(shipping_address)
            taxable_amount = subtotal + shipping_cost  # Tax applies to subtotal + shipping
            tax_amount = taxable_amount * tax_rate
            
            # Apply any discounts (from promocodes, etc.)
            discount_amount = await self._calculate_discount_amount(validated_items, subtotal)
            
            # Calculate final total
            total_amount = subtotal + shipping_cost + tax_amount - discount_amount
            
            return {
                "subtotal": subtotal,
                "shipping_cost": shipping_cost,
                "tax_amount": tax_amount,
                "tax_rate": tax_rate,
                "discount_amount": discount_amount,
                "total_amount": total_amount
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to calculate order total: {str(e)}")
                "tax_amount": tax_amount,
                "tax_rate": tax_rate,
                "discount_amount": discount_amount,
                "total_amount": total_amount
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to calculate order total: {str(e)}")

    async def _calculate_discount_amount(self, cart_items: List, subtotal: float) -> float:
        """Calculate discount amount from applied promocodes and loyalty points"""
        try:
            discount_amount = 0.0
            
            # Check if any cart items have promocodes applied
            for item in cart_items:
                if hasattr(item, 'promocode') and item.promocode:
                    # Get promocode details
                    from models.promocode import Promocode
                    result = await self.db.execute(
                        select(Promocode).where(
                            and_(
                                Promocode.code == item.promocode,
                                Promocode.is_active == True,
                                Promocode.valid_from <= datetime.utcnow(),
                                Promocode.valid_until >= datetime.utcnow()
                            )
                        )
                    )
                    promocode = result.scalar_one_or_none()
                    
                    if promocode:
                        if promocode.discount_type == "percentage":
                            item_discount = (item.total_price * promocode.discount_value) / 100
                            # Apply maximum discount limit if set
                            if promocode.max_discount_amount:
                                item_discount = min(item_discount, promocode.max_discount_amount)
                            discount_amount += item_discount
                        elif promocode.discount_type == "fixed":
                            discount_amount += min(promocode.discount_value, item.total_price)
            
            # Apply cart-level promocodes (if any)
            # This would be implemented based on your cart structure
            
            return discount_amount
            
        except Exception as e:
            logger.error(f"Error calculating discount amount: {e}")
            return 0.0

    async def _get_tax_rate(self, shipping_address) -> float:
        """
        Get tax rate from database based on shipping address
        Returns 0.0 if no tax rate is found in database
        """
        try:
            if not shipping_address:
                logger.info("No shipping address provided, using 0.0 tax rate")
                return 0.0
            
            # Get state/country from address
            state = getattr(shipping_address, 'state', None) or shipping_address.get('state', '')
            country = getattr(shipping_address, 'country', None) or shipping_address.get('country', 'US')
            
            logger.info(f"Looking up tax rate for country: {country}, state: {state}")
            
            # First try to find tax rate with specific province/state
            if state:
                tax_rate_result = await self.db.execute(
                    select(TaxRate).where(
                        and_(
                            TaxRate.country_code == country.upper(),
                            TaxRate.province_code == state.upper(),
                            TaxRate.is_active == True
                        )
                    )
                )
                tax_rate_record = tax_rate_result.scalar_one_or_none()
                
                if tax_rate_record:
                    logger.info(f"Found state/province tax rate for {country}-{state}: {tax_rate_record.tax_rate} ({tax_rate_record.tax_name})")
                    return tax_rate_record.tax_rate
                else:
                    logger.info(f"No state/province tax rate found for {country}-{state}")
            
            # If no state-specific rate found, try country-level rate
            tax_rate_result = await self.db.execute(
                select(TaxRate).where(
                    and_(
                        TaxRate.country_code == country.upper(),
                        TaxRate.province_code.is_(None),  # Country-level rate
                        TaxRate.is_active == True
                    )
                )
            )
            tax_rate_record = tax_rate_result.scalar_one_or_none()
            
            if tax_rate_record:
                logger.info(f"Found country tax rate for {country}: {tax_rate_record.tax_rate} ({tax_rate_record.tax_name})")
                return tax_rate_record.tax_rate
            
            # No tax rate found in database
            logger.info(f"No tax rate found in database for {country}-{state}, using 0.0")
            return 0.0
            
        except Exception as e:
            logger.error(f"Error getting tax rate from database: {e}")
            return 0.0
    def _generate_price_update_message(self, price_updates: List[Dict], total_change: float) -> str:
        """
        Generate a user-friendly message about price updates
        """
        total_items = len(price_updates)
        
        if total_items == 1:
            update = price_updates[0]
            if update["price_increased"]:
                if update["is_sale"]:
                    return f"Good news! {update['product_name']} is now on sale for ${update['new_price']:.2f}"
                else:
                    return f"Price updated: {update['product_name']} is now ${update['new_price']:.2f} (was ${update['old_price']:.2f})"
            else:
                return f"Price reduced: {update['product_name']} is now ${update['new_price']:.2f} (was ${update['old_price']:.2f})"
        else:
            if total_change > 0:
                return f"Prices updated for {total_items} items in your cart. Total increase: ${total_change:.2f}"
            elif total_change < 0:
                return f"Great news! Prices reduced for {total_items} items in your cart. You save ${abs(total_change):.2f}!"
            else:
                return f"Prices updated for {total_items} items in your cart."

    def _generate_cart_hash(self, cart: Cart, request: CheckoutRequest, request_id: Optional[str] = None) -> str:
        """
        Generate deterministic hash for cart contents and checkout details
        Used for idempotency key generation
        """
        # If request_id provided, use it for better idempotency
        if request_id:
            return f"req_{request_id}"
        
        # Fallback to cart-based hash for backward compatibility
        cart_items = sorted([
            f"{item.variant.id}:{item.quantity}:{item.price_per_unit}"
            for item in cart.items if not getattr(item, 'saved_for_later', False)
        ])
        
        cart_string = "|".join(cart_items)
        
        # Include checkout details
        checkout_details = f"{request.shipping_address_id}:{request.shipping_method_id}:{request.payment_method_id}"
        
        # Create hash
        full_string = f"{cart_string}|{checkout_details}"
        return hashlib.md5(full_string.encode()).hexdigest()[:16]

    async def _send_order_events_with_idempotency(self, order: Order, user_id: UUID, validated_cart_items: List[Dict[str, Any]]):
        """
        Send immutable ARQ events for order creation using new event system.
        Events are versioned, validated, and idempotent.
        """
        try:
            from core.arq_worker import enqueue_email, enqueue_notification
            
            # Use correlation ID for event tracing
            correlation_id = str(order.id)
            
            # Prepare order items for event
            order_items = []
            for item in validated_cart_items:
                order_items.append({
                    "product_id": item.get("product_id"),
                    "variant_id": item["variant_id"],
                    "quantity": item["quantity"],
                    "price_per_unit": float(item["backend_price"]),
                    "total_price": float(item["backend_total"]),
                    "product_name": item.get("product_name", "")
                })
            
            # Get shipping address for event
            shipping_address = {}
            if order.shipping_address:
                shipping_address = {
                    "street": order.shipping_address.street,
                    "city": order.shipping_address.city,
                    "state": order.shipping_address.state,
                    "country": order.shipping_address.country,
                    "postal_code": order.shipping_address.post_code
                }
            
            # Order created event handled by hybrid task system
            
            # Send order confirmation email using ARQ
            user_result = await self.db.execute(select(User).where(User.id == user_id))
            user = user_result.scalar_one_or_none()
            if user:
                await enqueue_email(
                    "order_confirmation",
                    user.email,
                    order_id=str(order.id),
                    order_details={
                        "items": order_items,
                        "total_amount": float(order.total_amount),
                        "currency": order.currency,
                        "shipping_address": shipping_address
                    }
                )
                
                # Send order notification
                await enqueue_notification(
                    str(user_id),
                    "order_created",
                    title="Order Confirmed",
                    message=f"Your order #{order.id} has been confirmed and is being processed.",
                    data={
                        "order_id": str(order.id),
                        "total_amount": float(order.total_amount),
                        "currency": order.currency
                    }
                )
            
            # Order payment event handled by hybrid task system
            
            logger.info(f"Successfully published order events for order {order.id} using new event system")
            
        except Exception as e:
            logger.error(f"Failed to publish order events using new event system: {e}")
            raise
    async def request_refund(
        self, 
        order_id: UUID, 
        user_id: UUID, 
        refund_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Request a refund for an order
        Delegates to the RefundService for comprehensive refund processing
        """
        try:
            from services.refunds import RefundService
            from schemas.refunds import RefundRequest
            
            # Create refund service
            refund_service = RefundService(self.db)
            
            # Convert refund_data to RefundRequest schema
            refund_request = RefundRequest(**refund_data)
            
            # Process refund request
            refund_response = await refund_service.request_refund(
                user_id=user_id,
                order_id=order_id,
                refund_request=refund_request
            )
            
            return refund_response.dict()
            
        except Exception as e:
            logger.error(f"Failed to request refund for order {order_id}: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to process refund request: {str(e)}"
            )
    def _generate_cart_hash(self, cart, request: CheckoutRequest) -> str:
        """Generate deterministic hash for cart state and checkout request"""
        import hashlib
        
        # Create hash from cart items and checkout details
        cart_data = {
            "items": [
                {
                    "variant_id": str(item.variant.id),
                    "quantity": item.quantity,
                    "price": float(item.price_per_unit)
                }
                for item in cart.items if not getattr(item, 'saved_for_later', False)
            ],
            "shipping_address_id": str(request.shipping_address_id),
            "shipping_method_id": str(request.shipping_method_id),
            "payment_method_id": str(request.payment_method_id)
        }
        
        # Sort items for consistent hashing
        cart_data["items"].sort(key=lambda x: x["variant_id"])
        
        # Create hash
        cart_str = str(cart_data)
        return hashlib.md5(cart_str.encode()).hexdigest()[:16]

    async def _convert_order_to_response(self, order: Order) -> OrderResponse:
        """Convert Order model to OrderResponse"""
        # Load order items if not already loaded
        if not hasattr(order, 'items') or not order.items:
            order_with_items = await self.db.execute(
                select(Order).where(Order.id == order.id).options(
                    selectinload(Order.items)
                )
            )
            order = await order_with_items.scalar_one()
        
        return OrderResponse(
            id=order.id,
            order_number=order.order_number,
            status=order.order_status,
            payment_status=order.payment_status,
            fulfillment_status=order.fulfillment_status,
            total_amount=order.total_amount,
            currency=order.currency,
            created_at=order.created_at,
            items=[
                OrderItemResponse(
                    id=item.id,
                    variant_id=item.variant_id,
                    quantity=item.quantity,
                    price_per_unit=item.price_per_unit,
                    total_price=item.total_price
                )
                for item in order.items
            ]
        )

    async def get_order_tracking(self, order_id: UUID, user_id: UUID) -> Dict[str, Any]:
        """Get order tracking information for authenticated user"""
        try:
            # Get order with tracking events
            query = select(Order).where(
                and_(Order.id == order_id, Order.user_id == user_id)
            ).options(
                selectinload(Order.tracking_events)
            )
            
            result = await self.db.execute(query)
            order = result.scalar_one_or_none()
            
            if not order:
                raise HTTPException(status_code=404, detail="Order not found")
            
            # Format tracking events
            tracking_events = []
            for event in order.tracking_events:
                tracking_events.append({
                    "id": str(event.id),
                    "status": event.status,
                    "description": event.description,
                    "location": event.location,
                    "timestamp": event.created_at.isoformat() if event.created_at else None
                })
            
            # Sort events by timestamp (newest first)
            tracking_events.sort(key=lambda x: x["timestamp"] or "", reverse=True)
            
            return {
                "order_id": str(order.id),
                "order_number": order.order_number,
                "status": order.order_status,
                "tracking_number": order.tracking_number,
                "carrier": order.carrier,
                "estimated_delivery": self._calculate_estimated_delivery(order),
                "tracking_events": tracking_events,
                "shipping_address": order.shipping_address
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to get order tracking for order {order_id}: {e}")
            raise HTTPException(
                status_code=500,
                detail="Failed to retrieve tracking information"
            )

    async def get_order_tracking_public(self, order_id: UUID) -> Dict[str, Any]:
        """Get order tracking information without authentication (public endpoint)"""
        try:
            # Get order with tracking events (no user_id filter for public access)
            query = select(Order).where(Order.id == order_id).options(
                selectinload(Order.tracking_events)
            )
            
            result = await self.db.execute(query)
            order = result.scalar_one_or_none()
            
            if not order:
                raise HTTPException(status_code=404, detail="Order not found")
            
            # Only return limited information for public access
            tracking_events = []
            for event in order.tracking_events:
                # Only include public-safe tracking events
                if event.status in ["confirmed", "processing", "shipped", "out_for_delivery", "delivered"]:
                    tracking_events.append({
                        "status": event.status,
                        "description": event.description,
                        "location": event.location,
                        "timestamp": event.created_at.isoformat() if event.created_at else None
                    })
            
            # Sort events by timestamp (newest first)
            tracking_events.sort(key=lambda x: x["timestamp"] or "", reverse=True)
            
            return {
                "order_number": order.order_number,
                "status": order.order_status,
                "tracking_number": order.tracking_number,
                "carrier": order.carrier,
                "estimated_delivery": self._calculate_estimated_delivery(order),
                "tracking_events": tracking_events
                # Note: No shipping address or sensitive info for public access
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to get public order tracking for order {order_id}: {e}")
            raise HTTPException(
                status_code=404,
                detail="Order not found or tracking information unavailable"
            )

    async def reorder(self, order_id: UUID, user_id: UUID) -> OrderResponse:
        """Create a new order from an existing order"""
        try:
            # Get the original order with items
            query = select(Order).where(
                and_(Order.id == order_id, Order.user_id == user_id)
            ).options(
                selectinload(Order.items).selectinload(OrderItem.variant)
            )
            
            result = await self.db.execute(query)
            original_order = result.scalar_one_or_none()
            
            if not original_order:
                raise HTTPException(status_code=404, detail="Original order not found")
            
            # Clear user's current cart
            cart_service = CartService(self.db)
            await cart_service.clear_cart(user_id)
            
            # Add items from original order to cart
            for item in original_order.items:
                # Check if variant still exists and is available
                variant_query = select(ProductVariant).where(ProductVariant.id == item.variant_id)
                variant_result = await self.db.execute(variant_query)
                variant = variant_result.scalar_one_or_none()
                
                if variant and variant.is_active:
                    # Check stock availability
                    stock_check = await self.inventory_service.check_stock_availability(
                        variant_id=item.variant_id,
                        quantity=item.quantity
                    )
                    
                    # Add to cart with available quantity
                    quantity_to_add = min(item.quantity, stock_check.get("current_stock", 0))
                    if quantity_to_add > 0:
                        await cart_service.add_to_cart(
                            user_id=user_id,
                            variant_id=item.variant_id,
                            quantity=quantity_to_add
                        )
            
            # Get updated cart
            cart = await cart_service.get_or_create_cart(user_id)
            
            if not cart.items:
                raise HTTPException(
                    status_code=400,
                    detail="No items from the original order are currently available"
                )
            
            return {
                "message": "Items added to cart successfully",
                "cart_items": len(cart.items),
                "original_order_id": str(order_id),
                "cart_id": str(cart.id)
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to reorder from order {order_id}: {e}")
            raise HTTPException(
                status_code=500,
                detail="Failed to create reorder"
            )

    async def generate_invoice(self, order_id: UUID, user_id: UUID) -> Dict[str, Any]:
        """Generate invoice for an order"""
        try:
            # Get order with items
            query = select(Order).where(
                and_(Order.id == order_id, Order.user_id == user_id)
            ).options(
                selectinload(Order.items).selectinload(OrderItem.variant).selectinload(ProductVariant.product),
                selectinload(Order.user)
            )
            
            result = await self.db.execute(query)
            order = result.scalar_one_or_none()
            
            if not order:
                raise HTTPException(status_code=404, detail="Order not found")
            
            # Use invoice generator utility
            from core.utils.invoice_generator import InvoiceGenerator
            
            invoice_generator = InvoiceGenerator()
            
            # Prepare order data for invoice
            order_data = {
                "order_id": str(order.id),
                "order_number": order.order_number,
                "order_date": order.created_at,
                "customer": {
                    "name": f"{order.user.firstname} {order.user.lastname}",
                    "email": order.user.email,
                    "phone": order.user.phone
                },
                "billing_address": order.billing_address,
                "shipping_address": order.shipping_address,
                "items": [
                    {
                        "name": item.variant.product.name if item.variant and item.variant.product else "Unknown Product",
                        "variant_name": item.variant.name if item.variant else "",
                        "quantity": item.quantity,
                        "price": item.price_per_unit,
                        "total": item.total_price
                    }
                    for item in order.items
                ],
                "subtotal": order.subtotal,
                "tax_amount": order.tax_amount,
                "shipping_amount": order.shipping_amount,
                "discount_amount": order.discount_amount,
                "total_amount": order.total_amount,
                "currency": order.currency,
                "payment_status": order.payment_status
            }
            
            # Generate invoice
            invoice_result = await invoice_generator.generate_invoice(order_data)
            
            return invoice_result
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to generate invoice for order {order_id}: {e}")
            raise HTTPException(
                status_code=500,
                detail="Failed to generate invoice"
            )

    async def add_order_note(self, order_id: UUID, user_id: UUID, note: str) -> Dict[str, Any]:
        """Add a customer note to an order"""
        try:
            # Get order
            query = select(Order).where(
                and_(Order.id == order_id, Order.user_id == user_id)
            )
            
            result = await self.db.execute(query)
            order = result.scalar_one_or_none()
            
            if not order:
                raise HTTPException(status_code=404, detail="Order not found")
            
            # Add note to customer_notes (append if existing)
            if order.customer_notes:
                timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
                order.customer_notes += f"\n\n[{timestamp}] {note}"
            else:
                timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
                order.customer_notes = f"[{timestamp}] {note}"
            
            await self.db.commit()
            await self.db.refresh(order)
            
            return {
                "order_id": str(order.id),
                "note_added": note,
                "timestamp": timestamp,
                "all_notes": order.customer_notes
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to add note to order {order_id}: {e}")
            raise HTTPException(
                status_code=500,
                detail="Failed to add order note"
            )

    async def get_order_notes(self, order_id: UUID, user_id: UUID) -> Dict[str, Any]:
        """Get all customer notes for an order"""
        try:
            # Get order
            query = select(Order).where(
                and_(Order.id == order_id, Order.user_id == user_id)
            )
            
            result = await self.db.execute(query)
            order = result.scalar_one_or_none()
            
            if not order:
                raise HTTPException(status_code=404, detail="Order not found")
            
            # Parse notes if they exist
            notes = []
            if order.customer_notes:
                # Split notes by timestamp pattern
                import re
                note_pattern = r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\] (.*?)(?=\n\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\]|$)'
                matches = re.findall(note_pattern, order.customer_notes, re.DOTALL)
                
                for timestamp_str, note_text in matches:
                    notes.append({
                        "timestamp": timestamp_str,
                        "note": note_text.strip()
                    })
            
            return {
                "order_id": str(order.id),
                "notes": notes,
                "total_notes": len(notes)
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to get notes for order {order_id}: {e}")
            raise HTTPException(
                status_code=500,
                detail="Failed to retrieve order notes"
            )

    def _calculate_estimated_delivery(self, order: Order) -> Optional[str]:
        """Calculate estimated delivery date based on order status and shipping method"""
        try:
            if order.delivered_at:
                return order.delivered_at.isoformat()
            
            if order.order_status in ["cancelled", "refunded"]:
                return None
            
            # Base delivery estimate on shipping method and current status
            base_days = 5  # Default delivery time
            
            # Adjust based on shipping method
            if order.shipping_method:
                shipping_method_lower = order.shipping_method.lower()
                if "express" in shipping_method_lower or "overnight" in shipping_method_lower:
                    base_days = 1
                elif "priority" in shipping_method_lower or "2-day" in shipping_method_lower:
                    base_days = 2
                elif "standard" in shipping_method_lower:
                    base_days = 5
                elif "economy" in shipping_method_lower:
                    base_days = 7
            
            # Calculate from appropriate date
            if order.shipped_at:
                estimated_date = order.shipped_at + timedelta(days=base_days)
            elif order.confirmed_at:
                estimated_date = order.confirmed_at + timedelta(days=base_days + 2)  # Add processing time
            else:
                estimated_date = order.created_at + timedelta(days=base_days + 3)  # Add confirmation + processing time
            
            return estimated_date.isoformat()
            
        except Exception as e:
            logger.error(f"Failed to calculate estimated delivery for order {order.id}: {e}")
            return None