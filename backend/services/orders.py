from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, update
from sqlalchemy.orm import selectinload
from typing import Optional, List
from fastapi import HTTPException, BackgroundTasks
from models.order import Order, OrderItem
from models.cart import Cart, CartItem
from models.product import ProductVariant, Product
from models.user import Address, User
from models.shipping import ShippingMethod
from models.payment import PaymentMethod
from schemas.order import OrderCreate, OrderResponse, CheckoutRequest
from core.exceptions import APIException
import uuid
from uuid import UUID
from services.cart import CartService
from services.user import AddressService
from services.shipping import ShippingService
from services.payment import PaymentService
from services.notification import NotificationService
from core.utils.messages.email import send_email
from core.config import settings
from services.kafka_producer import get_kafka_producer_service # ADD THIS LINE


class OrderService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.cart_service = CartService(db)
        self.address_service = AddressService(db)
        self.shipping_service = ShippingService(db)
        self.payment_service = PaymentService(db)
        self.notification_service = NotificationService(
            db)  # Initialize NotificationService

    async def place_order(self, user_id: UUID, checkout_request: CheckoutRequest, background_tasks: BackgroundTasks) -> OrderResponse:
        # 1. Get and validate cart
        cart = await self.cart_service.get_or_create_cart(user_id)
        if not cart.items:
            raise APIException(status_code=400, message="Cart is empty")

        # Validate stock for all items in cart
        for item in cart.items:
            if item.saved_for_later:  # Skip saved for later items
                continue
            variant = (await self.db.execute(
                select(ProductVariant).where(
                    ProductVariant.id == item.variant_id)
            )).scalar_one_or_none()
            if not variant or variant.stock < item.quantity:
                raise APIException(
                    status_code=400, message=f"Insufficient stock for {variant.name if variant else 'unknown product'}. Available: {variant.stock if variant else 0}")

        # 2. Get and validate shipping address, method, and payment method
        shipping_address = await self.address_service.get_address(checkout_request.shipping_address_id)
        if not shipping_address or shipping_address.user_id != user_id:
            raise APIException(
                status_code=404, message="Shipping address not found or does not belong to user")

        shipping_method = await self.shipping_service.get_shipping_method_by_id(checkout_request.shipping_method_id)
        if not shipping_method or not shipping_method.is_active:
            raise APIException(
                status_code=404, message="Shipping method not found or inactive")

        payment_method = await self.payment_service.get_payment_methods(user_id)
        payment_method = next(
            (pm for pm in payment_method if pm.id == checkout_request.payment_method_id), None)
        if not payment_method:
            raise APIException(
                status_code=404, message="Payment method not found or does not belong to user")

        # 3. Calculate final totals
        base_shipping_cost = await self.shipping_service.calculate_shipping_cost(
            cart.subtotal(), {}, checkout_request.shipping_method_id
        )

        final_total_amount = cart.subtotal() + cart.tax_amount() + \
            base_shipping_cost - cart.discount_amount

        # Create Order record before payment attempt
        new_order = Order(
            user_id=user_id,
            status="pending_payment",
            total_amount=final_total_amount,
            currency="USD",
            shipping_address_id=checkout_request.shipping_address_id,
            shipping_method_id=checkout_request.shipping_method_id,
            payment_method_id=checkout_request.payment_method_id,
            notes=checkout_request.notes
        )
        self.db.add(new_order)
        await self.db.flush()  # Flush to get the new_order.id

        # 4. Process payment
        try:
            payment_intent_data = await self.payment_service.create_payment_intent(
                user_id=user_id,
                order_id=new_order.id,
                amount=final_total_amount,
                currency="USD"  # Assuming USD for now
            )
            if payment_intent_data["status"] == "succeeded":
                new_order.status = "paid"
            else:
                new_order.status = "payment_pending"

        except Exception as e:
            await self.db.rollback()
            raise APIException(
                status_code=400, message=f"Payment failed: {str(e)}")

        # 6. Create Order Items and update product stock
        for item in cart.items:
            if item.saved_for_later:
                continue
            order_item = OrderItem(
                order_id=new_order.id,
                variant_id=item.variant_id,
                quantity=item.quantity,
                price_per_unit=item.price_per_unit,
                total_price=item.total_price
            )
            self.db.add(order_item)

            variant = (await self.db.execute(
                select(ProductVariant).where(
                    ProductVariant.id == item.variant_id)
            )).scalar_one()
            variant.stock -= item.quantity
            await self.db.execute(update(ProductVariant).where(ProductVariant.id == variant.id).values(stock=variant.stock))

        # 7. Clear Cart
        await self.cart_service.clear_cart(user_id)

        await self.db.commit()
        await self.db.refresh(new_order)

        # Send order confirmation email via Kafka
        producer_service = await get_kafka_producer_service()
        await producer_service.send_message(settings.KAFKA_TOPIC_EMAIL, {
            "service": "EmailService",
            "method": "send_order_confirmation",
            "args": [str(new_order.id)]
        })

        # --- Send Notifications for New Order ---
        # 1. Get Admin User ID
        admin_user_query = select(User.id).where(User.role == "Admin")
        admin_user_id = (await self.db.execute(admin_user_query)).scalar_one_or_none()

        # 2. Collect unique supplier IDs
        supplier_ids = set()
        for item in new_order.items:
            variant = (await self.db.execute(
                select(ProductVariant).where(
                    ProductVariant.id == item.variant_id)
            )).scalar_one_or_none()
            if variant and variant.product_id:
                product = (await self.db.execute(
                    select(Product).where(Product.id == variant.product_id)
                )).scalar_one_or_none()
                if product and product.supplier_id:
                    supplier_ids.add(str(product.supplier_id))

        # 3. Send notifications
        order_details_link = f"{settings.FRONTEND_URL}/admin/orders/{new_order.id}"

        # To Admin
        if admin_user_id:
            await self.notification_service.create_notification(
                user_id=str(admin_user_id),
                message=f"New Order #{new_order.id} placed by {user_id}. Total: ${new_order.total_amount:.2f}. View details: {order_details_link}",
                type="success",
                related_id=str(new_order.id)
            )

        # To Suppliers
        for supplier_id in supplier_ids:
            # Assuming a supplier order view
            supplier_order_link = f"{settings.FRONTEND_URL}/supplier/orders/{new_order.id}"
            await self.notification_service.create_notification(
                user_id=supplier_id,
                message=f"New Order #{new_order.id} received for your product(s). Total: ${new_order.total_amount:.2f}. View details: {supplier_order_link}",
                type="info",
                related_id=str(new_order.id)
            )
        # --- End Notifications ---

        return OrderResponse.from_orm(new_order)

    async def send_order_confirmation_email(self, order: Order): # Changed to async
        """Sends an order confirmation email to the user using Kafka."""
        try:
            producer_service = await get_kafka_producer_service()
            await producer_service.send_message(settings.KAFKA_TOPIC_ORDER, {
                "service": "OrderService", # Assuming a dedicated order processing service method
                "method": "process_order_confirmation",
                "args": [str(order.id)]
            })
            print(f"Order confirmation email queued for order: {order.id}")
        except Exception as e:
            print(f"Failed to queue order confirmation email: {e}")

    async def update_order_shipping_info(self, order_id: str, tracking_number: str, carrier_name: str, background_tasks: BackgroundTasks) -> Order:
        """Updates an order with shipping information and sends a notification."""
        query = select(Order).where(Order.id == order_id)
        result = await self.db.execute(query)
        order = result.scalar_one_or_none()

        if not order:
            raise APIException(status_code=404, message="Order not found")

        order.status = "shipped"
        order.tracking_number = tracking_number
        # We might need to add a carrier field to the Order model
        # For now, we'll just pass it to the email context.

        await self.db.commit()
        await self.db.refresh(order)

        # Send shipping update email via Kafka
        producer_service = await get_kafka_producer_service()
        await producer_service.send_message(settings.KAFKA_TOPIC_EMAIL, {
            "service": "EmailService",
            "method": "send_shipping_update",
            "args": [str(order.id), carrier_name, order.tracking_number]
        })

        return order

    async def send_shipping_update_email(self, order: Order, carrier_name: str): # Changed to async
        """Sends a shipping update email to the user using Kafka."""
        try:
            producer_service = await get_kafka_producer_service()
            await producer_service.send_message(settings.KAFKA_TOPIC_ORDER, {
                "service": "OrderService", # Assuming a dedicated order processing service method
                "method": "process_shipping_update",
                "args": [str(order.id)]
            })
            print(f"Shipping update email queued for order: {order.id}, carrier: {carrier_name}")
        except Exception as e:
            print(f"Failed to queue shipping update email: {e}")

    async def create_order(self, order_data: OrderCreate, user_id: UUID) -> Order:
        """Create a new order from direct items (e.g., for admin or specific scenarios)."""
        try:
            total_amount = 0.0
            order_items_to_add = []

            # Validate items and calculate total amount
            for item_data in order_data.items:
                variant = (await self.db.execute(
                    select(ProductVariant).where(
                        ProductVariant.id == item_data.variant_id)
                )).scalar_one_or_none()
                if not variant:
                    raise APIException(
                        status_code=404, message=f"Product variant {item_data.variant_id} not found")
                if variant.stock < item_data.quantity:
                    raise APIException(
                        status_code=400, message=f"Insufficient stock for {variant.name}. Available: {variant.stock}")

                price = variant.sale_price or variant.base_price
                order_item = OrderItem(
                    variant_id=item_data.variant_id,
                    quantity=item_data.quantity,
                    price_per_unit=price,
                    total_price=price * item_data.quantity
                )
                order_items_to_add.append(order_item)
                total_amount += order_item.total_price

            # Create order
            order = Order(
                user_id=user_id,
                status="pending",
                total_amount=total_amount,
                currency="USD",  # Assuming USD for now
                notes=order_data.notes,
                # shipping_address_id, shipping_method_id, payment_method_id are not part of OrderCreate
                # For direct order creation, these might be set later or handled differently.
                # For now, we'll leave them as None or default if nullable.
            )
            self.db.add(order)
            await self.db.flush()

            for order_item in order_items_to_add:
                order_item.order_id = order.id
                self.db.add(order_item)

                # Decrement stock
                variant = (await self.db.execute(
                    select(ProductVariant).where(
                        ProductVariant.id == order_item.variant_id)
                )).scalar_one()
                variant.stock -= order_item.quantity
                await self.db.execute(update(ProductVariant).where(ProductVariant.id == variant.id).values(stock=variant.stock))

            await self.db.commit()
            await self.db.refresh(order)

            return order
        except APIException:
            await self.db.rollback()
            raise
        except Exception as e:
            await self.db.rollback()
            raise APIException(
                status_code=500, message=f"Failed to create order: {str(e)}")

    async def get_user_orders(self, user_id: UUID, page: int = 1, limit: int = 10, status_filter: Optional[str] = None) -> dict:
        """Get user's orders with pagination."""
        offset = (page - 1) * limit

        query = select(Order).where(Order.user_id == user_id).options(
            selectinload(Order.items)
        )

        if status_filter:
            query = query.where(Order.status == status_filter)

        query = query.order_by(Order.created_at.desc()
                               ).offset(offset).limit(limit)

        result = await self.db.execute(query)
        orders = result.scalars().all()

        # Get total count
        count_query = select(Order).where(Order.user_id == user_id)
        if status_filter:
            count_query = count_query.where(Order.status == status_filter)

        count_result = await self.db.execute(count_query)
        total = len(count_result.scalars().all())
        print(orders, 'ooooooooooo')

        return {
            "data": [
                {
                    "id": str(order.id),
                    "user_id": str(order.user_id),
                    "shipping_address_id": str(order.shipping_address_id),
                    "shipping_method_id": str(order.shipping_method_id),
                    "payment_method_id": str(order.payment_method_id),
                    "status": order.status,
                    "total_amount": order.total_amount,
                    "currency": order.currency,
                    "tracking_number": order.tracking_number,
                    "carrier_name": order.carrier_name,
                    "estimated_delivery": order.estimated_delivery,
                    "notes": order.notes,
                    "created_at": order.created_at.isoformat() if order.created_at else None,
                    "updated_at": order.updated_at.isoformat() if order.updated_at else None,

                    "items": [
                        {
                            "id": str(item.id),
                            "variant_id": str(item.variant_id),
                            "quantity": item.quantity,
                            "total_price": item.total_price,
                            # add more order item fields as needed
                        }
                        for item in order.items
                    ] if order.items else [],


                }
                for order in orders
            ],
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "pages": (total + limit - 1) // limit
            }
        }

    async def get_order_by_id(self, order_id: UUID, user_id: UUID) -> Optional[dict]:
        """Get order by ID."""
        query = select(Order).options(
            selectinload(Order.items)
        ).where(and_(Order.id == order_id, Order.user_id == user_id))

        result = await self.db.execute(query)
        order = result.scalar_one_or_none()

        if not order:
            return None

        return {
            "id": str(order.id),
            "user_id": str(order.user_id),
            "status": order.status,
            "total_amount": order.total_amount,
            "currency": order.currency,
            "tracking_number": order.tracking_number,
            "estimated_delivery": order.estimated_delivery.isoformat() if order.estimated_delivery else None,
            "created_at": order.created_at.isoformat(),
            "items": [
                {
                    "id": str(item.id),
                    "variant_id": str(item.variant_id),
                    "quantity": item.quantity,
                    "price_per_unit": item.price_per_unit,
                    "total_price": item.total_price
                }
                for item in order.items
            ],
            "tracking_events": [
                {
                    "status": event.status,
                    "timestamp": event.timestamp.isoformat(),
                    "description": event.description,
                    "location": event.location,
                    "carrier": event.carrier
                }
                for event in order.tracking_events
            ]
        }

    async def cancel_order(self, order_id: UUID, user_id: UUID) -> dict:
        """Cancel an order."""
        query = select(Order).where(
            and_(Order.id == order_id, Order.user_id == user_id))
        result = await self.db.execute(query)
        order = result.scalar_one_or_none()

        if not order:
            raise APIException(status_code=404, message="Order not found")

        if order.status not in ["pending", "confirmed"]:
            raise APIException(
                status_code=400, message="Order cannot be cancelled")

        order.status = "cancelled"
        await self.db.commit()

        return {
            "id": str(order.id),
            "status": order.status,
            "message": "Order cancelled successfully"
        }

    async def get_order_tracking(self, order_id: UUID, user_id: UUID) -> dict:
        """Get order tracking information."""
        query = select(Order).options(
            selectinload(Order.tracking_events)
        ).where(and_(Order.id == order_id, Order.user_id == user_id))
        result = await self.db.execute(query)
        order = result.scalar_one_or_none()

        if not order:
            raise APIException(status_code=404, message="Order not found")

        tracking_events_data = []
        for event in order.tracking_events:
            tracking_events_data.append({
                "status": event.status,
                "timestamp": event.timestamp.isoformat(),
                "description": event.description,
                "location": event.location,
                "carrier": event.carrier
            })

        # Sort events by timestamp if not already sorted by default relationship loading
        tracking_events_data.sort(key=lambda x: x["timestamp"])

        return {
            "order_id": str(order.id),
            "tracking_number": order.tracking_number,
            "status": order.status,
            "events": tracking_events_data
        }

    async def update_order_status(self, order_id: str, new_status: str, background_tasks: BackgroundTasks) -> dict:
        """Update order status and notify customer."""
        query = select(Order).options(selectinload(Order.user)).where(Order.id == order_id)
        result = await self.db.execute(query)
        order = result.scalar_one_or_none()

        if not order:
            raise APIException(status_code=404, message="Order not found")

        # Validate status
        valid_statuses = ["pending", "confirmed", "processing", "shipped", "delivered", "cancelled"]
        if new_status not in valid_statuses:
            raise APIException(status_code=400, message=f"Invalid status. Must be one of: {', '.join(valid_statuses)}")

        old_status = order.status
        order.status = new_status

        await self.db.commit()
        await self.db.refresh(order)

        # Send notification to customer
        if order.user:
            producer_service = await get_kafka_producer_service()
            await producer_service.send_message(settings.KAFKA_TOPIC_NOTIFICATION, {
                "service": "NotificationService",
                "method": "create_notification",
                "args": [],
                "kwargs": {
                    "user_id": str(order.user_id),
                    "message": f"Your order #{order.id} status has been updated to {new_status}",
                    "type": "info",
                    "related_id": str(order.id)
                }
            })

        return {
            "id": str(order.id),
            "status": order.status,
            "previous_status": old_status,
            "user": {
                "firstname": order.user.firstname if order.user else None,
                "lastname": order.user.lastname if order.user else None,
                "email": order.user.email if order.user else None
            },
            "total_amount": order.total_amount,
            "created_at": order.created_at.isoformat()
        }