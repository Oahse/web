from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, BackgroundTasks
from models.order import Order, OrderItem, TrackingEvent
from models.cart import Cart, CartItem
from models.user import User, Address
from models.product import ProductVariant
from models.shipping import ShippingMethod
from models.payment import PaymentMethod
from schemas.order import OrderResponse, OrderItemResponse, CheckoutRequest, OrderCreate
from services.cart import CartService
from services.payment import PaymentService
from services.notification import NotificationService
from uuid import UUID
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any


class OrderService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def place_order(self, user_id: UUID, request: CheckoutRequest, background_tasks: BackgroundTasks) -> OrderResponse:
        """Place an order from the user's cart"""
        # Get user's cart
        cart_service = CartService(self.db)
        cart = await cart_service.get_or_create_cart(user_id)

        if not cart.items or len([item for item in cart.items if not item.saved_for_later]) == 0:
            raise HTTPException(status_code=400, detail="Cart is empty")

        # Validate cart items availability
        validation_result = await cart_service.validate_cart(user_id)
        if not validation_result.get("valid", False):
            raise HTTPException(
                status_code=400, detail="Cart validation failed")

        # Verify shipping address exists
        shipping_address = await self.db.execute(
            select(Address).where(
                and_(Address.id == request.shipping_address_id, Address.user_id == user_id))
        )
        shipping_address = shipping_address.scalar_one_or_none()
        if not shipping_address:
            raise HTTPException(
                status_code=404, detail="Shipping address not found")

        # Verify shipping method exists
        shipping_method = await self.db.execute(
            select(ShippingMethod).where(
                ShippingMethod.id == request.shipping_method_id)
        )
        shipping_method = shipping_method.scalar_one_or_none()
        if not shipping_method:
            raise HTTPException(
                status_code=404, detail="Shipping method not found")

        # Verify payment method exists
        payment_method = await self.db.execute(
            select(PaymentMethod).where(and_(PaymentMethod.id ==
                                             request.payment_method_id, PaymentMethod.user_id == user_id))
        )
        payment_method = payment_method.scalar_one_or_none()
        if not payment_method:
            raise HTTPException(
                status_code=404, detail="Payment method not found")

        # Calculate total amount
        total_amount = cart.total_amount()

        # Create order
        order = Order(
            user_id=user_id,
            status="pending",
            total_amount=total_amount,
            shipping_address_id=request.shipping_address_id,
            shipping_method_id=request.shipping_method_id,
            payment_method_id=request.payment_method_id,
            promocode_id=cart.promocode_id,
            notes=request.notes
        )
        self.db.add(order)
        await self.db.flush()  # Get the order ID

        # Create order items from cart items
        active_cart_items = [
            item for item in cart.items if not item.saved_for_later]
        for cart_item in active_cart_items:
            order_item = OrderItem(
                order_id=order.id,
                variant_id=cart_item.variant_id,
                quantity=cart_item.quantity,
                price_per_unit=cart_item.price_per_unit,
                total_price=cart_item.total_price
            )
            self.db.add(order_item)

        # Process payment
        payment_service = PaymentService(self.db)
        payment_result = None
        
        try:
            payment_result = await payment_service.process_payment(
                user_id=user_id,
                amount=total_amount,
                payment_method_id=request.payment_method_id,
                order_id=order.id
            )

            if payment_result.get("status") == "success":
                order.status = "confirmed"

                # Create initial tracking event
                tracking_event = TrackingEvent(
                    order_id=order.id,
                    status="confirmed",
                    description="Order confirmed and payment processed",
                    location="Processing Center"
                )
                self.db.add(tracking_event)

                # Commit order and tracking event
                await self.db.commit()
                await self.db.refresh(order)

                # Clear cart after successful order and commit
                await cart_service.clear_cart(user_id)
                
                # Send order confirmation email and notification in background
                background_tasks.add_task(self._send_order_confirmation, order.id)
                background_tasks.add_task(self._notify_order_created, str(order.id), str(user_id))

            else:
                # Payment failed
                order.status = "payment_failed"
                await self.db.commit()
                await self.db.refresh(order)
                
                error_message = payment_result.get("error", "Payment processing failed")
                raise HTTPException(
                    status_code=400, 
                    detail=f"Payment failed: {error_message}"
                )

        except HTTPException:
            # Re-raise HTTP exceptions
            raise
        except Exception as e:
            # Handle unexpected errors
            order.status = "payment_failed"
            await self.db.commit()
            await self.db.refresh(order)
            
            raise HTTPException(
                status_code=400, 
                detail=f"Payment processing failed: {str(e)}"
            )

        # Send order confirmation email in background
        background_tasks.add_task(self._send_order_confirmation, order.id)

        return await self._format_order_response(order)

    async def get_user_orders(self, user_id: UUID, page: int = 1, limit: int = 10, status_filter: Optional[str] = None) -> Dict[str, Any]:
        """Get paginated list of user's orders"""
        query = select(Order).where(Order.user_id == user_id).options(
            selectinload(Order.items).selectinload(OrderItem.variant),
            selectinload(Order.tracking_events)
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
            selectinload(Order.items).selectinload(OrderItem.variant),
            selectinload(Order.tracking_events)
        )

        result = await self.db.execute(query)
        order = result.scalar_one_or_none()

        if not order:
            return None

        return await self._format_order_response(order)

    async def cancel_order(self, order_id: UUID, user_id: UUID) -> OrderResponse:
        """Cancel an order"""
        query = select(Order).where(
            and_(Order.id == order_id, Order.user_id == user_id))
        result = await self.db.execute(query)
        order = result.scalar_one_or_none()

        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        if order.status not in ["pending", "confirmed"]:
            raise HTTPException(
                status_code=400, detail="Order cannot be cancelled")

        order.status = "cancelled"

        # Add tracking event
        tracking_event = TrackingEvent(
            order_id=order.id,
            status="cancelled",
            description="Order cancelled by customer",
            location="System"
        )
        self.db.add(tracking_event)

        await self.db.commit()
        await self.db.refresh(order)

        return await self._format_order_response(order)

    async def get_order_tracking(self, order_id: UUID, user_id: UUID) -> Dict[str, Any]:
        """Get order tracking information"""
        query = select(Order).where(and_(Order.id == order_id, Order.user_id == user_id)).options(
            selectinload(Order.tracking_events)
        )

        result = await self.db.execute(query)
        order = result.scalar_one_or_none()

        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        tracking_events = []
        for event in order.tracking_events:
            tracking_events.append({
                "id": str(event.id),
                "status": event.status,
                "description": event.description,
                "location": event.location,
                "timestamp": event.created_at.isoformat()
            })

        # Calculate estimated delivery
        estimated_delivery = None
        if order.status in ["confirmed", "shipped"] and hasattr(order, 'shipping_method'):
            estimated_days = getattr(
                order.shipping_method, 'estimated_days', 5)
            estimated_delivery = (
                order.created_at + timedelta(days=estimated_days)).isoformat()

        return {
            "order_id": str(order.id),
            "status": order.status,
            "tracking_number": order.tracking_number,
            "carrier_name": order.carrier_name,
            "estimated_delivery": estimated_delivery,
            "tracking_events": tracking_events
        }

    async def add_tracking_event(self, order_id: UUID, status: str, description: str, location: Optional[str] = None) -> TrackingEvent:
        """Add a tracking event to an order (admin function)"""
        tracking_event = TrackingEvent(
            order_id=order_id,
            status=status,
            description=description,
            location=location
        )
        self.db.add(tracking_event)
        await self.db.commit()
        await self.db.refresh(tracking_event)
        return tracking_event

    async def update_order_status(self, order_id: UUID, status: str, tracking_number: Optional[str] = None) -> Order:
        """Update order status (admin function)"""
        query = select(Order).where(Order.id == order_id)
        result = await self.db.execute(query)
        order = result.scalar_one_or_none()

        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        order.status = status
        if tracking_number:
            order.tracking_number = tracking_number

        # Add tracking event
        tracking_event = TrackingEvent(
            order_id=order.id,
            status=status,
            description=f"Order status updated to {status}",
            location="Fulfillment Center"
        )
        self.db.add(tracking_event)

        await self.db.commit()
        await self.db.refresh(order)
        
        # Send notification to user about status change
        notification_service = NotificationService(self.db)
        await notification_service.notify_order_updated(str(order_id), str(order.user_id), status)
        
        return order

    async def _format_order_response(self, order: Order) -> OrderResponse:
        """Format order for response"""
        items = []
        for item in order.items:
            items.append(OrderItemResponse(
                id=str(item.id),
                variant_id=str(item.variant_id),
                quantity=item.quantity,
                price_per_unit=item.price_per_unit,
                total_price=item.total_price
            ))

        # Calculate estimated delivery
        estimated_delivery = None
        if order.status in ["confirmed", "shipped"]:
            estimated_days = 5  # Default, could be from shipping method
            estimated_delivery = (
                order.created_at + timedelta(days=estimated_days)).isoformat()

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

    async def create_order(self, user_id: UUID, request: OrderCreate, background_tasks: BackgroundTasks) -> OrderResponse:
        """Create a new order directly (not from cart)"""
        # Validate items availability
        total_amount = 0.0
        order_items = []

        for item_data in request.items:
            variant = await self.db.execute(
                select(ProductVariant).where(
                    ProductVariant.id == UUID(item_data.variant_id))
            )
            variant = variant.scalar_one_or_none()
            if not variant:
                raise HTTPException(
                    status_code=404, detail=f"Product variant {item_data.variant_id} not found")

            if variant.stock < item_data.quantity:
                raise HTTPException(
                    status_code=400, detail=f"Insufficient stock for {variant.name}")

            price = variant.sale_price or variant.base_price
            item_total = price * item_data.quantity
            total_amount += item_total

            order_items.append({
                "variant_id": variant.id,
                "quantity": item_data.quantity,
                "price_per_unit": price,
                "total_price": item_total
            })

        # Create order
        order = Order(
            user_id=user_id,
            status="pending",
            total_amount=total_amount,
            notes=request.notes
        )
        self.db.add(order)
        await self.db.flush()

        # Create order items
        for item_data in order_items:
            order_item = OrderItem(
                order_id=order.id,
                variant_id=item_data["variant_id"],
                quantity=item_data["quantity"],
                price_per_unit=item_data["price_per_unit"],
                total_price=item_data["total_price"]
            )
            self.db.add(order_item)

        return await self._format_order_response(order)

    async def request_refund(self, order_id: UUID, user_id: UUID, request_data: dict) -> dict:
        """Request refund for an order"""
        order = await self.get_order_by_id(order_id, user_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        # Create refund request (simplified - would need proper refund model)
        refund_id = str(UUID())

        return {
            "message": "Refund request submitted successfully",
            "refund_id": refund_id
        }

    async def reorder(self, order_id: UUID, user_id: UUID) -> OrderResponse:
        """Create new order from existing order"""
        original_order = await self.get_order_by_id(order_id, user_id)
        if not original_order:
            raise HTTPException(status_code=404, detail="Order not found")

        # Get original order items
        query = select(Order).where(and_(Order.id == order_id, Order.user_id == user_id)).options(
            selectinload(Order.items)
        )
        result = await self.db.execute(query)
        order = result.scalar_one_or_none()

        # Create new order with same items
        new_order = Order(
            user_id=user_id,
            status="pending",
            total_amount=order.total_amount
        )
        self.db.add(new_order)
        await self.db.flush()

        # Copy order items
        for item in order.items:
            new_item = OrderItem(
                order_id=new_order.id,
                variant_id=item.variant_id,
                quantity=item.quantity,
                price_per_unit=item.price_per_unit,
                total_price=item.total_price
            )
            self.db.add(new_item)

        await self.db.commit()
        await self.db.refresh(new_order)

        return await self._format_order_response(new_order)

    async def generate_invoice(self, order_id: UUID, user_id: UUID) -> dict:
        """Generate invoice for order"""
        order = await self.get_order_by_id(order_id, user_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        # Simplified invoice data
        return {
            "invoice_id": f"INV-{order_id}",
            "order_id": str(order_id),
            "invoice_url": f"/invoices/{order_id}.pdf",
            "generated_at": datetime.now().isoformat()
        }

    async def add_order_note(self, order_id: UUID, user_id: UUID, note: str) -> dict:
        """Add note to order"""
        order = await self.get_order_by_id(order_id, user_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        # For now, just return success (would need proper notes model)
        return {
            "message": "Note added successfully",
            "note_id": str(UUID())
        }

    async def get_order_notes(self, order_id: UUID, user_id: UUID) -> list:
        """Get order notes"""
        order = await self.get_order_by_id(order_id, user_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        # Return empty list for now (would need proper notes model)
        return []

    async def _send_order_confirmation(self, order_id: UUID):
        """Send order confirmation email (background task)"""
        try:
            notification_service = NotificationService(self.db)
            await notification_service.send_order_confirmation(order_id)
        except Exception as e:
            # Log error but don't fail the order
            print(f"Failed to send order confirmation email: {e}")

    async def _notify_order_created(self, order_id: UUID, user_id: UUID):
        """Send WebSocket notification for order creation (background task)"""
        try:
            notification_service = NotificationService(self.db)
            await notification_service.notify_order_created(order_id, user_id)
        except Exception as e:
            # Log error but don't fail the order
            print(f"Failed to send order created notification: {e}")

    async def _notify_order_updated(self, order_id: UUID, user_id: UUID, status: str):
        """Send WebSocket notification for order update (background task)"""
        try:
            notification_service = NotificationService(self.db)
            await notification_service.notify_order_updated(order_id, user_id, status)
        except Exception as e:
            # Log error but don't fail the order
            print(f"Failed to send order updated notification: {e}")
