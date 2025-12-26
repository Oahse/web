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
from schemas.orders import OrderResponse, OrderItemResponse, CheckoutRequest, OrderCreate
from schemas.inventories import StockAdjustmentCreate
from services.cart import CartService
from services.payments import PaymentService
from services.inventories import InventoryService 
from models.inventories import Inventory
from uuid import UUID, uuid4
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from core.config import settings
from core.kafka import get_kafka_producer_service
from services.event_service import event_service
import logging

logger = logging.getLogger(__name__)


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
        
        # STEP 1: Validate cart and get current prices
        cart_service = CartService(self.db)
        validation_result = await cart_service.validate_cart(user_id)
        
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
                actual_prices[str(item.variant_id)] = float(item.price_per_unit)
            
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
        existing = existing_order.scalar_one_or_none()
        
        if existing:
            # Return existing order
            return await self._format_order_response(existing)
        
        # Proceed with order creation
        return await self.place_order(user_id, request, background_tasks, idempotency_key)

    async def place_order(
        self, 
        user_id: UUID, 
        request: CheckoutRequest, 
        background_tasks: BackgroundTasks,
        idempotency_key: Optional[str] = None
    ) -> OrderResponse:
        """
        Place an order from the user's cart with comprehensive validation
        ALWAYS validates cart before proceeding with checkout
        """
        # STEP 1: MANDATORY CART VALIDATION - Never skip this step
        cart_service = CartService(self.db)
        
        # Always validate cart first - this is critical for data integrity
        validation_result = await cart_service.validate_cart(user_id)
        
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
        
        # If there are price updates, send notification to frontend via WebSocket
        if price_updates:
            await self._send_price_update_notification(user_id, price_updates)
        
        # STEP 3: VALIDATE CHECKOUT DEPENDENCIES
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
        if not payment_method:
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
                # Create order with backend-calculated prices and idempotency key
                order = Order(
                    user_id=user_id,
                    status="pending",
                    total_amount=final_total["total_amount"],
                    shipping_address_id=request.shipping_address_id,
                    shipping_method_id=request.shipping_method_id,
                    payment_method_id=request.payment_method_id,
                    promocode_id=getattr(cart, 'promocode_id', None),
                    notes=request.notes,
                    idempotency_key=idempotency_key  # Store idempotency key
                )
                self.db.add(order)
                await self.db.flush()  # Get order ID without committing

                # Create order items with validated backend prices
                for validated_item in validated_cart_items:
                    # FINAL STOCK CHECK - Double-check stock availability using atomic method
                    stock_check = await self.inventory_service.check_stock_availability(
                        variant_id=validated_item["variant_id"],
                        quantity=validated_item["quantity"]
                    )
                    
                    if not stock_check["available"]:
                        raise HTTPException(
                            status_code=400, 
                            detail=f"Stock validation failed: {stock_check['message']}"
                        )
                    
                    order_item = OrderItem(
                        order_id=order.id,
                        variant_id=validated_item["variant_id"],
                        quantity=validated_item["quantity"],
                        price_per_unit=validated_item["backend_price"],  # Use backend price
                        total_price=validated_item["backend_total"]     # Use backend total
                    )
                    self.db.add(order_item)
                    
                    # Atomically decrement stock using SELECT ... FOR UPDATE
                    await self.inventory_service.decrement_stock_on_purchase(
                        variant_id=validated_item["variant_id"],
                        quantity=validated_item["quantity"],
                        location_id=stock_check["location_id"],
                        order_id=order.id,
                        user_id=user_id
                    )

                # Process payment with backend-calculated amount and idempotency
                payment_service = PaymentService(self.db)
                payment_idempotency_key = f"payment_{order.id}_{idempotency_key}" if idempotency_key else None
                
                payment_result = await payment_service.process_payment_idempotent(
                    user_id=user_id,
                    order_id=order.id,
                    amount=final_total["total_amount"],  # Use backend-calculated total
                    payment_method_id=request.payment_method_id,
                    idempotency_key=payment_idempotency_key,
                    request_id=str(uuid4())
                )

                if payment_result.get("status") != "succeeded":
                    error_message = payment_result.get("error", "Payment processing failed")
                    raise HTTPException(status_code=400, detail=f"Payment failed: {error_message}")

                # Payment succeeded - update order status
                order.status = "confirmed"
                order.version += 1  # Optimistic locking increment

                # Create initial tracking event
                tracking_event = TrackingEvent(
                    order_id=order.id,
                    status="confirmed",
                    description="Order confirmed and payment processed",
                    location="Processing Center"
                )
                self.db.add(tracking_event)

                # Clear cart after successful order (validated cart)
                await cart_service.clear_cart(user_id)

                # Transaction will auto-commit here if no exceptions occurred
                
            # Refresh order after transaction commit
            await self.db.refresh(order)
            
            # Send Kafka events with idempotency after successful transaction commit
            try:
                await self._send_order_events_with_idempotency(order, user_id, validated_cart_items)
            except Exception as kafka_error:
                # Log Kafka errors but don't fail the order
                logger.error(f"Failed to send order events for order {order.id}: {kafka_error}")
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
            currency="USD",
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
            
            active_cart_items = [item for item in cart.items if not item.saved_for_later]
            
            for cart_item in active_cart_items:
                # Fetch current variant details from database
                variant_result = await self.db.execute(
                    select(ProductVariant).where(ProductVariant.id == cart_item.variant_id).options(
                        selectinload(ProductVariant.product)
                    )
                )
                variant = variant_result.scalar_one_or_none()
                
                if not variant:
                    return {
                        "valid": False,
                        "message": f"Product variant {cart_item.variant_id} no longer exists"
                    }
                
                # Get current backend price (sale_price takes precedence over base_price)
                backend_price = variant.sale_price if variant.sale_price else variant.base_price
                backend_total = backend_price * cart_item.quantity
                
                # Compare with cart price (allow small floating point differences)
                price_difference = abs(backend_price - cart_item.price_per_unit)
                total_difference = abs(backend_total - cart_item.total_price)
                
                if price_difference > 0.01 or total_difference > 0.01:
                    discrepancy_info = {
                        "variant_id": str(cart_item.variant_id),
                        "product_name": variant.product.name if variant.product else "Unknown",
                        "variant_name": variant.name,
                        "cart_price": cart_item.price_per_unit,
                        "backend_price": backend_price,
                        "difference": price_difference
                    }
                    total_discrepancies.append(discrepancy_info)
                    
                    # Add to price updates for frontend notification
                    price_updates.append({
                        "variant_id": str(cart_item.variant_id),
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
                    "variant_id": cart_item.variant_id,
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
                from core.utils.logging import structured_logger
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
            
            # Calculate shipping cost
            shipping_cost = 0.0
            if shipping_method:
                if hasattr(shipping_method, 'cost'):
                    shipping_cost = shipping_method.cost
                elif hasattr(shipping_method, 'price'):
                    shipping_cost = shipping_method.price
                else:
                    # Default shipping logic if no cost field
                    shipping_cost = 0.0 if subtotal >= 50 else 10.0
            
            # Calculate tax based on shipping address
            tax_rate = await self._get_tax_rate(shipping_address)
            tax_amount = subtotal * tax_rate
            
            # Apply any discounts (from promocodes, etc.)
            discount_amount = 0.0  # TODO: Implement discount calculation
            
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

    async def _get_tax_rate(self, shipping_address) -> float:
        """
        Get tax rate based on shipping address
        This should be implemented based on your tax requirements
        """
        # Default tax rate - implement proper tax calculation based on address
        default_tax_rate = 0.08  # 8%
        
        # TODO: Implement proper tax calculation based on:
        # - shipping_address.state
        # - shipping_address.country
        # - Local tax regulations
        # - Tax service integration
        
        return default_tax_rate
    async def _send_price_update_notification(self, user_id: UUID, price_updates: List[Dict]) -> None:
        """
        Send real-time price update notification to frontend via WebSocket
        """
        try:
            from core.kafka import get_kafka_producer_service
            from core.config import settings
            
            # Calculate summary statistics
            total_items_updated = len(price_updates)
            price_increases = [update for update in price_updates if update["price_increased"]]
            price_decreases = [update for update in price_updates if not update["price_increased"]]
            total_price_change = sum(update["new_total"] - update["old_total"] for update in price_updates)
            
            # Create notification message
            notification_data = {
                "type": "price_update",
                "user_id": str(user_id),
                "timestamp": datetime.utcnow().isoformat(),
                "summary": {
                    "total_items_updated": total_items_updated,
                    "price_increases": len(price_increases),
                    "price_decreases": len(price_decreases),
                    "total_price_change": round(total_price_change, 2),
                    "currency": "USD"
                },
                "items": price_updates,
                "message": self._generate_price_update_message(price_updates, total_price_change)
            }
            
            # Send via Kafka to WebSocket service
            producer_service = await get_kafka_producer_service()
            await producer_service.send_message(
                settings.KAFKA_TOPIC_WEBSOCKET,
                {
                    "type": "price_update_notification",
                    "user_id": str(user_id),
                    "data": notification_data
                },
                key=str(user_id)
            )
            
            # Also send as regular notification for persistence
            await producer_service.send_message(
                settings.KAFKA_TOPIC_NOTIFICATION,
                {
                    "service": "NotificationService",
                    "method": "create_notification",
                    "args": [],
                    "kwargs": {
                        "user_id": str(user_id),
                        "message": notification_data["message"],
                        "type": "info",
                        "title": "Price Update",
                        "metadata": {
                            "type": "price_update",
                            "items_updated": total_items_updated,
                            "total_change": total_price_change
                        }
                    }
                }
            )
            
        except Exception as e:
            # Don't fail checkout if notification fails
            from core.utils.logging import structured_logger
            structured_logger.error(
                message="Failed to send price update notification",
                metadata={
                    "user_id": str(user_id),
                    "price_updates_count": len(price_updates),
                    "error": str(e)
                },
                exception=e
            )
    
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

    def _generate_cart_hash(self, cart: Cart, request: CheckoutRequest) -> str:
        """
        Generate deterministic hash for cart contents and checkout details
        Used for idempotency key generation
        """
        # Create string representation of cart state
        cart_items = sorted([
            f"{item.variant_id}:{item.quantity}:{item.price_per_unit}"
            for item in cart.items if not item.saved_for_later
        ])
        
        cart_string = "|".join(cart_items)
        
        # Include checkout details
        checkout_details = f"{request.shipping_address_id}:{request.shipping_method_id}:{request.payment_method_id}"
        
        # Create hash
        full_string = f"{cart_string}|{checkout_details}"
        return hashlib.md5(full_string.encode()).hexdigest()[:16]

    async def _send_order_events_with_idempotency(self, order: Order, user_id: UUID, validated_cart_items: List[Dict[str, Any]]):
        """
        Send immutable Kafka events for order creation using new event system.
        Events are versioned, validated, and idempotent.
        """
        try:
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
                    "postal_code": order.shipping_address.postal_code
                }
            
            # Publish order.created event using new event system
            await event_service.publish_order_created(
                order_id=str(order.id),
                user_id=str(user_id),
                amount=float(order.total_amount),
                currency="USD",  # You can make this configurable
                items=order_items,
                shipping_address=shipping_address,
                payment_method="card",  # You can get this from payment method
                correlation_id=correlation_id
            )
            
            # If order is already confirmed (payment succeeded), also publish order.paid event
            if order.status == "confirmed":
                # Get payment information (you might need to adjust this based on your payment model)
                payment_id = getattr(order, 'payment_id', str(uuid4()))
                
                await event_service.publish_order_paid(
                    order_id=str(order.id),
                    payment_id=payment_id,
                    amount=float(order.total_amount),
                    currency="USD",
                    payment_method="card",
                    correlation_id=correlation_id
                )
            
            # Publish inventory reservation events for each item
            for item in validated_cart_items:
                reservation_id = str(uuid4())
                expires_at = (datetime.utcnow() + timedelta(minutes=15)).isoformat()
                
                # Note: Inventory reservation removed - implement as needed
                    quantity=item["quantity"],
                    order_id=str(order.id),
                    reservation_id=reservation_id,
                    expires_at=expires_at,
                    correlation_id=correlation_id
                )
            
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"Successfully published order events for order {order.id} using new event system")
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to publish order events using new event system: {e}")
            raise