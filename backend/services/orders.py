# Consolidated order service
# This file includes all order-related functionality

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
from schemas.order import OrderResponse, OrderItemResponse, CheckoutRequest, OrderCreate
from schemas.inventory import StockAdjustmentCreate
from services.cart import CartService
from services.payments import PaymentService
from services.notifications import NotificationService
from services.activity import ActivityService
from services.inventories import InventoryService
from models.inventories import Inventory
from uuid import UUID
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from core.config import settings
from core.kafka import get_kafka_producer_service


class OrderService:
    """Consolidated order service with comprehensive order management"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.inventory_service = InventoryService(db)

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
            raise HTTPException(status_code=400, detail="Cart validation failed")

        # Verify shipping address exists
        shipping_address = await self.db.execute(
            select(Address).where(
                and_(Address.id == request.shipping_address_id, Address.user_id == user_id))
        )
        shipping_address = shipping_address.scalar_one_or_none()
        if not shipping_address:
            raise HTTPException(status_code=404, detail="Shipping address not found")

        # Verify shipping method exists
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
        await self.db.flush()

        # Create order items from cart items
        active_cart_items = [item for item in cart.items if not item.saved_for_later]
        for cart_item in active_cart_items:
            order_item = OrderItem(
                order_id=order.id,
                variant_id=cart_item.variant_id,
                quantity=cart_item.quantity,
                price_per_unit=cart_item.price_per_unit,
                total_price=cart_item.total_price
            )
            self.db.add(order_item)
            
            # Decrement stock for the ordered item
            inventory_item = await self.inventory_service.get_inventory_item_by_variant_id(cart_item.variant_id)

            if not inventory_item:
                raise HTTPException(status_code=400, detail=f"No inventory record found for variant {cart_item.variant_id}")

            await self.inventory_service.adjust_stock(
                StockAdjustmentCreate(
                    variant_id=cart_item.variant_id,
                    location_id=inventory_item.location_id,
                    quantity_change=-cart_item.quantity,
                    reason="order_placed"
                ),
                adjusted_by_user_id=user_id
            )

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

            if payment_result.get("status") == "succeeded":
                order.status = "confirmed"

                # Create initial tracking event
                tracking_event = TrackingEvent(
                    order_id=order.id,
                    status="confirmed",
                    description="Order confirmed and payment processed",
                    location="Processing Center"
                )
                self.db.add(tracking_event)

                # Commit order and tracking event BEFORE triggering Kafka tasks
                await self.db.commit()
                await self.db.refresh(order)

                # Log activity for new order
                activity_service = ActivityService(self.db)
                await activity_service.log_activity(
                    action_type="order",
                    description=f"New order placed: #{order.id}",
                    user_id=user_id,
                    metadata={
                        "order_id": str(order.id),
                        "total_amount": float(total_amount),
                        "status": order.status
                    }
                )

                # Clear cart after successful order and commit
                await cart_service.clear_cart(user_id)
                
                # Trigger Kafka tasks AFTER commit
                producer_service = await get_kafka_producer_service()
                await producer_service.send_message(settings.KAFKA_TOPIC_EMAIL, {
                    "service": "EmailService",
                    "method": "send_order_confirmation",
                    "args": [str(order.id)]
                })
                await producer_service.send_message(settings.KAFKA_TOPIC_NOTIFICATION, {
                    "service": "NotificationService",
                    "method": "create_notification",
                    "args": [],
                    "kwargs": {
                        "user_id": str(user_id),
                        "message": f"Your order #{order.id} has been confirmed!",
                        "type": "success",
                        "related_id": str(order.id)
                    }
                })

            else:
                # Payment failed
                order.status = "payment_failed"
                await self.db.commit()
                await self.db.refresh(order)
                
                error_message = payment_result.get("error", "Payment processing failed")
                raise HTTPException(status_code=400, detail=f"Payment failed: {error_message}")

        except HTTPException:
            raise
        except Exception as e:
            order.status = "payment_failed"
            await self.db.commit()
            await self.db.refresh(order)
            
            raise HTTPException(status_code=400, detail=f"Payment processing failed: {str(e)}")

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
        """Cancel an order"""
        query = select(Order).where(and_(Order.id == order_id, Order.user_id == user_id))
        result = await self.db.execute(query)
        order = result.scalar_one_or_none()

        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        if order.status not in ["pending", "confirmed"]:
            raise HTTPException(status_code=400, detail="Order cannot be cancelled")

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
            
            await self.inventory_service.adjust_stock(
                StockAdjustmentCreate(
                    variant_id=item.variant.id,
                    location_id=item.variant.inventory.location_id,
                    quantity_change=item.quantity,
                    reason="order_cancelled"
                ),
                adjusted_by_user_id=user_id
            )

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