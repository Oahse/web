from fastapi import APIRouter, Depends, Query, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from uuid import UUID
from core.database import get_db
from core.utils.response import Response
from core.exceptions import APIException
from schemas.order import OrderCreate, OrderUpdate, CheckoutRequest
from services.order import OrderService
from models.user import User
from core.dependencies import get_current_auth_user

router = APIRouter(prefix="/api/v1/orders", tags=["Orders"])

@router.post("/")
async def create_order(
    request: OrderCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_auth_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new order."""
    try:
        order_service = OrderService(db)
        order = await order_service.create_order(current_user.id, request, background_tasks)
        return Response(success=True, data=order, message="Order created successfully")
    except APIException:
        raise
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_400_BAD_REQUEST,
            message=f"Failed to create order: {str(e)}"
        )

@router.post("/checkout")
async def checkout(
    request: CheckoutRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_auth_user),
    db: AsyncSession = Depends(get_db)
):
    """Place an order from the current cart."""
    try:
        order_service = OrderService(db)
        order = await order_service.place_order(current_user.id, request, background_tasks)
        return Response(success=True, data=order, message="Order placed successfully")
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
    status_filter: Optional[str] = None,
    current_user: User = Depends(get_current_auth_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user's orders."""
    try:
        order_service = OrderService(db)
        print(f"Fetching orders for user: {current_user.id}")
        orders = await order_service.get_user_orders(
            current_user.id, page, limit, status_filter
        )
        print(f"Successfully fetched {len(orders.get('orders', []))} orders")
        return Response(success=True, data=orders)
    except APIException:
        raise
    except Exception as e:
        print(f"Error fetching orders: {e}")
        import traceback
        traceback.print_exc()
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to fetch orders: {str(e)}"
        )

@router.get("/{order_id}")
async def get_order(
    order_id: UUID,
    current_user: User = Depends(get_current_auth_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific order."""
    try:
        order_service = OrderService(db)
        print(f"Fetching order {order_id} for user {current_user.id}")
        order = await order_service.get_order_by_id(order_id, current_user.id)
        if not order:
            raise APIException(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Order not found"
            )
        print(f"Successfully fetched order: {order.id}")
        return Response(success=True, data=order)
    except APIException:
        raise
    except Exception as e:
        print(f"Error fetching order {order_id}: {e}")
        import traceback
        traceback.print_exc()
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to fetch order: {str(e)}"
        )

@router.put("/{order_id}/cancel")
async def cancel_order(
    order_id: UUID,
    current_user: User = Depends(get_current_auth_user),
    db: AsyncSession = Depends(get_db)
):
    """Cancel an order."""
    try:
        order_service = OrderService(db)
        order = await order_service.cancel_order(order_id, current_user.id)
        return Response(success=True, data=order, message="Order cancelled successfully")
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_400_BAD_REQUEST,
            message="Failed to cancel order"
        )

@router.get("/{order_id}/tracking")
async def get_order_tracking(
    order_id: UUID,
    current_user: User = Depends(get_current_auth_user),
    db: AsyncSession = Depends(get_db)
):
    """Get order tracking information."""
    try:
        order_service = OrderService(db)
        tracking = await order_service.get_order_tracking(order_id, current_user.id)
        return Response(success=True, data=tracking)
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Failed to fetch tracking information"
        )

@router.post("/{order_id}/refund")
async def request_refund(
    order_id: UUID,
    request: dict,
    current_user: User = Depends(get_current_auth_user),
    db: AsyncSession = Depends(get_db)
):
    """Request order refund."""
    try:
        order_service = OrderService(db)
        result = await order_service.request_refund(order_id, current_user.id, request)
        return Response(success=True, data=result, message="Refund request submitted")
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_400_BAD_REQUEST,
            message=f"Failed to request refund: {str(e)}"
        )

@router.post("/{order_id}/reorder")
async def reorder(
    order_id: UUID,
    current_user: User = Depends(get_current_auth_user),
    db: AsyncSession = Depends(get_db)
):
    """Create new order from existing order."""
    try:
        order_service = OrderService(db)
        order = await order_service.reorder(order_id, current_user.id)
        return Response(success=True, data=order, message="Order recreated successfully")
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_400_BAD_REQUEST,
            message=f"Failed to reorder: {str(e)}"
        )

@router.get("/{order_id}/invoice")
async def get_order_invoice(
    order_id: UUID,
    current_user: User = Depends(get_current_auth_user),
    db: AsyncSession = Depends(get_db)
):
    """Get order invoice."""
    try:
        order_service = OrderService(db)
        invoice = await order_service.generate_invoice(order_id, current_user.id)
        return Response(success=True, data=invoice)
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Failed to generate invoice"
        )

@router.post("/{order_id}/notes")
async def add_order_note(
    order_id: UUID,
    request: dict,
    current_user: User = Depends(get_current_auth_user),
    db: AsyncSession = Depends(get_db)
):
    """Add note to order."""
    try:
        order_service = OrderService(db)
        result = await order_service.add_order_note(order_id, current_user.id, request.get("note", ""))
        return Response(success=True, data=result, message="Note added successfully")
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_400_BAD_REQUEST,
            message=f"Failed to add note: {str(e)}"
        )

@router.get("/{order_id}/notes")
async def get_order_notes(
    order_id: UUID,
    current_user: User = Depends(get_current_auth_user),
    db: AsyncSession = Depends(get_db)
):
    """Get order notes."""
    try:
        order_service = OrderService(db)
        notes = await order_service.get_order_notes(order_id, current_user.id)
        return Response(success=True, data=notes)
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Failed to fetch order notes"
        )