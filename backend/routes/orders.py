from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, Query, status, BackgroundTasks, Header
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from core.database import get_db
from core.utils.response import Response
from core.exceptions import APIException
from services.orders import OrderService
from models.user import User
from models.orders import Order
from services.auth import AuthService
from schemas.orders import OrderCreate, CheckoutRequest
from core.dependencies import get_current_auth_user, get_order_service

from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_auth_user_alt(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> User:
    return await AuthService.get_current_user(token, db)

router = APIRouter(prefix="/v1/orders", tags=["Orders"])


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
    order_service: OrderService = Depends(get_order_service),
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key")
):
    """
    Place an order from the current cart with idempotency protection.
    
    Idempotency-Key header prevents duplicate orders from being created.
    If not provided, one will be generated based on cart contents.
    """
    try:
        order = await order_service.place_order_with_idempotency(
            current_user.id, 
            request, 
            background_tasks,
            idempotency_key
        )
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
    order_service: OrderService = Depends(get_order_service)
):
    """Get user's orders."""
    try:
        orders = await order_service.get_user_orders(
            current_user.id, page, limit, status_filter
        )
        return Response(success=True, data=orders)
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
        return Response(success=True, data=order)
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
    order_service: OrderService = Depends(get_order_service)
):
    """Get order tracking information (authenticated)."""
    try:
        tracking = await order_service.get_order_tracking(order_id, current_user.id)
        return Response(success=True, data=tracking)
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
        return Response(success=True, data=tracking)
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
    order_service: OrderService = Depends(get_order_service)
):
    """Create new order from existing order."""
    try:
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
        
        return Response(success=True, data=invoice)
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
    order_service: OrderService = Depends(get_order_service)
):
    """Get order notes."""
    try:
        notes = await order_service.get_order_notes(order_id, current_user.id)
        return Response(success=True, data=notes)
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Failed to fetch order notes"
        )