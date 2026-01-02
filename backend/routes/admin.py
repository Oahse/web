from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, Query, status, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, Dict, Any, List
from core.database import get_db
from core.utils.response import Response
from core.exceptions import APIException
from services.admin import AdminService
from services.orders import OrderService
from services.shipping import ShippingService
from models.user import User
from models.orders import Order
from services.auth import AuthService
from schemas.auth import UserCreate
from schemas.shipping import ShippingMethodCreate, ShippingMethodUpdate
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_auth_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> User:
    auth_service = AuthService(db)
    return await auth_service.get_current_user(token)

router = APIRouter(prefix="/admin", tags=["Admin"])

class ShipOrderRequest(BaseModel):
    tracking_number: str
    carrier_name: str

class UpdateOrderStatusRequest(BaseModel):
    status: str
    tracking_number: Optional[str] = None
    carrier_name: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None

def require_admin(current_user: User = Depends(get_current_auth_user)):
    """Require admin role."""
    if current_user.role not in ["Admin", "SuperAdmin"]:
        raise APIException(
            status_code=status.HTTP_403_FORBIDDEN,
            message="Admin access required"
        )
    return current_user

# Basic Admin Routes
@router.get("/stats")
async def get_admin_stats(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get admin dashboard statistics."""
    try:
        admin_service = AdminService(db)
        stats = await admin_service.get_dashboard_stats()
        return Response.success(data=stats)
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to fetch admin stats {str(e)}"
        )

@router.get("/overview")
async def get_platform_overview(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get platform overview."""
    try:
        admin_service = AdminService(db)
        overview = await admin_service.get_platform_overview()
        return Response.success(data=overview)
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to fetch platform overview  {str(e)}"
        )

# Order Management Routes
@router.get("/orders")
async def get_all_orders(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    order_status: Optional[str] = Query(None, alias="status"),
    q: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    min_price: Optional[float] = Query(None),
    max_price: Optional[float] = Query(None),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get all orders (admin only)."""
    try:
        admin_service = AdminService(db)
        orders = await admin_service.get_all_orders(page, limit, order_status, q, date_from, date_to, min_price, max_price)
        return Response.success(data=orders)
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to fetch orders {str(e)}"
        )

@router.get("/orders/{order_id}")
async def get_order_by_id(
    order_id: UUID,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get a single order by ID (admin only)."""
    try:
        admin_service = AdminService(db)
        order = await admin_service.get_order_by_id(str(order_id))
        if not order:
            raise APIException(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Order not found"
            )
        return Response.success(data=order)
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to fetch order: {str(e)}"
        )

@router.put("/orders/{order_id}/ship")
async def ship_order(
    order_id: str,
    request: ShipOrderRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Update an order with shipping information (admin only)."""
    try:
        order_service = OrderService(db)
        order = await order_service.update_order_shipping_info(
            order_id,
            request.tracking_number,
            request.carrier_name,
            background_tasks
        )
        return Response.success(data=order, message="Order status updated to shipped and notification sent.")
    except APIException:
        raise
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_400_BAD_REQUEST,
            message=f"Failed to update order: {str(e)}"
        )

@router.put("/orders/{order_id}/status")
async def update_order_status(
    order_id: str,
    request: UpdateOrderStatusRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Update order status with tracking information (admin only)."""
    try:
        from services.orders import OrderService as EnhancedOrderService
        
        order_service = EnhancedOrderService(db)
        order = await order_service.update_order_status(
            order_id=UUID(order_id),
            status=request.status,
            tracking_number=request.tracking_number,
            carrier_name=request.carrier_name,
            location=request.location,
            description=request.description
        )
        
        return Response.success(data={
            "id": str(order.id),
            "status": order.status,
            "tracking_number": order.tracking_number,
            "carrier_name": order.carrier_name
        }, message=f"Order status updated to {request.status}")
    except APIException:
        raise
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_400_BAD_REQUEST,
            message=f"Failed to update order status: {str(e)}"
        )

@router.get("/orders/{order_id}/invoice")
async def get_order_invoice_admin(
    order_id: UUID,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get order invoice (admin only)."""
    from fastapi.responses import FileResponse
    from services.orders import OrderService as EnhancedOrderService
    import os
    
    try:
        order_service = EnhancedOrderService(db)
        order_query = await db.execute(
            select(Order).where(Order.id == order_id)
        )
        order = order_query.scalar_one_or_none()
        
        if not order:
            raise APIException(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Order not found"
            )
        
        invoice = await order_service.generate_invoice(order_id, order.user_id)
        
        if 'invoice_path' in invoice and os.path.exists(invoice['invoice_path']):
            file_path = invoice['invoice_path']
            if file_path.endswith('.pdf'):
                return FileResponse(
                    path=file_path,
                    filename=f"invoice-{order_id}.pdf",
                    media_type="application/pdf"
                )
            else:
                return FileResponse(
                    path=file_path,
                    filename=f"invoice-{order_id}.docx",
                    media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
        
        return Response.success(data=invoice)
    except APIException:
        raise
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to generate invoice: {str(e)}"
        )

# User Management Routes
@router.get("/users")
async def get_all_users(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    role: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    verified: Optional[bool] = Query(None),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get all users (admin only)."""
    try:
        admin_service = AdminService(db)
        users = await admin_service.get_all_users(
            page=page, 
            limit=limit, 
            role_filter=role, 
            search=search, 
            status=status, 
            verified=verified
        )
        return Response.success(data=users)
    except Exception as e:
        import logging
        logging.error(f"Failed to fetch users: {str(e)}")
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to fetch users: {str(e)}"
        )

@router.post("/users")
async def create_user_admin(
    user_data: UserCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Create a new user (admin only)."""
    try:
        admin_service = AdminService(db)
        user = await admin_service.create_user(user_data, background_tasks)
        return Response.success(data=user, message="User created successfully")
    except APIException:
        raise
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to create user: {str(e)}"
        )

@router.get("/users/{user_id}")
async def get_user_by_id(
    user_id: str,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get a single user by ID (admin only)."""
    try:
        admin_service = AdminService(db)
        user = await admin_service.get_user_by_id(user_id)
        if not user:
            raise APIException(
                status_code=status.HTTP_404_NOT_FOUND,
                message="User not found"
            )
        return Response.success(data=user)
    except APIException:
        raise
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to fetch user: {str(e)}"
        )

@router.put("/users/{user_id}/status")
async def update_user_status(
    user_id: str,
    is_active: bool,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Update user status (admin only)."""
    try:
        admin_service = AdminService(db)
        user = await admin_service.update_user_status(user_id, is_active)
        return Response.success(data=user, message="User status updated")
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_400_BAD_REQUEST,
            message="Failed to update user status"
        )

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Delete user (admin only)."""
    try:
        admin_service = AdminService(db)
        await admin_service.delete_user(user_id)
        return Response.success(message="User deleted successfully")
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_400_BAD_REQUEST,
            message="Failed to delete user"
        )

@router.post("/users/{user_id}/reset-password")
async def reset_user_password(
    user_id: str,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Send password reset email to user (admin only)."""
    try:
        admin_service = AdminService(db)
        result = await admin_service.reset_user_password(user_id)
        return Response.success(data=result, message="Password reset email sent successfully")
    except APIException:
        raise
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to send password reset email: {str(e)}"
        )

@router.post("/users/{user_id}/deactivate")
async def deactivate_user_account(
    user_id: str,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Deactivate user account (admin only)."""
    try:
        admin_service = AdminService(db)
        result = await admin_service.deactivate_user(user_id)
        return Response.success(data=result, message="User account deactivated successfully")
    except APIException:
        raise
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to deactivate user: {str(e)}"
        )

@router.post("/users/{user_id}/activate")
async def activate_user_account(
    user_id: str,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Activate user account (admin only)."""
    try:
        admin_service = AdminService(db)
        result = await admin_service.activate_user(user_id)
        return Response.success(data=result, message="User account activated successfully")
    except APIException:
        raise
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to activate user: {str(e)}"
        )

# Product Management Routes
@router.get("/products")
async def get_all_products_admin(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    supplier: Optional[str] = Query(None),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get all products (admin only)."""
    print(f"DEBUG: Route handler called with page={page}, limit={limit}")
    try:
        admin_service = AdminService(db)
        products = await admin_service.get_all_products(page, limit, search, category, status, supplier)
        print(f"DEBUG: AdminService returned: {type(products)}")
        return Response.success(data=products)
    except Exception as e:
        print(f"DEBUG: Exception in route handler: {str(e)}")
        import traceback
        traceback.print_exc()
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Failed to fetch products"
        )

@router.get("/variants")
async def get_all_variants_admin(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = Query(None),
    product_id: Optional[str] = Query(None),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get all variants (admin only)."""
    try:
        admin_service = AdminService(db)
        variants = await admin_service.get_all_variants(page, limit, search, product_id)
        return Response.success(data=variants)
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Failed to fetch variants"
        )

# Export Routes
@router.get("/orders/export")
async def export_orders(
    format: str = Query("csv"),
    order_status: Optional[str] = Query(None, alias="status"),
    q: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    min_price: Optional[float] = Query(None),
    max_price: Optional[float] = Query(None),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Export orders to CSV, Excel, or PDF (admin only)."""
    from fastapi.responses import StreamingResponse
    from services.export import ExportService
    
    if format not in ['csv', 'excel', 'pdf']:
        raise APIException(
            status_code=status.HTTP_400_BAD_REQUEST,
            message="Invalid format. Use csv, excel, or pdf"
        )
    
    try:
        admin_service = AdminService(db)
        
        # Fetch all orders using pagination to avoid limit restrictions
        all_orders = []
        page = 1
        limit = 100
        
        while True:
            orders_data = await admin_service.get_all_orders(
                page=page, 
                limit=limit,
                order_status=order_status,
                q=q,
                date_from=date_from,
                date_to=date_to,
                min_price=min_price,
                max_price=max_price
            )
            
            orders_batch = orders_data.get('data', [])
            if not orders_batch:
                break
                
            all_orders.extend(orders_batch)
            
            # If we got less than the limit, we've reached the end
            if len(orders_batch) < limit:
                break
                
            page += 1
        
        orders = all_orders
        
        export_service = ExportService()
        
        if format == "csv":
            output = export_service.export_orders_to_csv(orders)
            media_type = "text/csv"
            filename = f"orders_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        elif format == "excel":
            output = export_service.export_orders_to_excel(orders)
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            filename = f"orders_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        elif format == "pdf":
            output = export_service.export_orders_to_pdf(orders)
            media_type = "application/pdf"
            filename = f"orders_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        else:
            raise APIException(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Invalid format. Use csv, excel, or pdf"
            )
        
        return StreamingResponse(
            output,
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except APIException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to export orders: {str(e)}"
        )

# Shipping Methods Management Routes
@router.get("/shipping-methods")
async def get_all_shipping_methods(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get all shipping methods (admin only)."""
    try:
        shipping_service = ShippingService(db)
        methods = await shipping_service.get_all_active_shipping_methods()
        
        # Convert to dict format for API response
        methods_data = []
        for method in methods:
            methods_data.append({
                "id": str(method.id),
                "name": method.name,
                "description": method.description,
                "price": float(method.price),
                "estimated_days": method.estimated_days,
                "is_active": method.is_active,
                "created_at": method.created_at.isoformat() if method.created_at else None,
                "updated_at": method.updated_at.isoformat() if method.updated_at else None
            })
        
        return Response.success(data=methods_data)
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to fetch shipping methods: {str(e)}"
        )

@router.get("/shipping-methods/{method_id}")
async def get_shipping_method(
    method_id: UUID,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get a single shipping method by ID (admin only)."""
    try:
        shipping_service = ShippingService(db)
        method = await shipping_service.get_shipping_method_by_id(method_id)
        
        if not method:
            raise APIException(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Shipping method not found"
            )
        
        method_data = {
            "id": str(method.id),
            "name": method.name,
            "description": method.description,
            "price": float(method.price),
            "estimated_days": method.estimated_days,
            "is_active": method.is_active,
            "created_at": method.created_at.isoformat() if method.created_at else None,
            "updated_at": method.updated_at.isoformat() if method.updated_at else None
        }
        
        return Response.success(data=method_data)
    except APIException:
        raise
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to fetch shipping method: {str(e)}"
        )

@router.post("/shipping-methods")
async def create_shipping_method(
    method_data: ShippingMethodCreate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Create a new shipping method (admin only)."""
    try:
        shipping_service = ShippingService(db)
        method = await shipping_service.create_shipping_method(method_data)
        
        method_response = {
            "id": str(method.id),
            "name": method.name,
            "description": method.description,
            "price": float(method.price),
            "estimated_days": method.estimated_days,
            "is_active": method.is_active,
            "created_at": method.created_at.isoformat() if method.created_at else None,
            "updated_at": method.updated_at.isoformat() if method.updated_at else None
        }
        
        return Response.success(data=method_response, message="Shipping method created successfully")
    except APIException:
        raise
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_400_BAD_REQUEST,
            message=f"Failed to create shipping method: {str(e)}"
        )

@router.put("/shipping-methods/{method_id}")
async def update_shipping_method(
    method_id: UUID,
    method_data: ShippingMethodUpdate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Update a shipping method (admin only)."""
    try:
        shipping_service = ShippingService(db)
        method = await shipping_service.update_shipping_method(method_id, method_data)
        
        if not method:
            raise APIException(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Shipping method not found"
            )
        
        method_response = {
            "id": str(method.id),
            "name": method.name,
            "description": method.description,
            "price": float(method.price),
            "estimated_days": method.estimated_days,
            "is_active": method.is_active,
            "created_at": method.created_at.isoformat() if method.created_at else None,
            "updated_at": method.updated_at.isoformat() if method.updated_at else None
        }
        
        return Response.success(data=method_response, message="Shipping method updated successfully")
    except APIException:
        raise
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_400_BAD_REQUEST,
            message=f"Failed to update shipping method: {str(e)}"
        )

@router.delete("/shipping-methods/{method_id}")
async def delete_shipping_method(
    method_id: UUID,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Delete a shipping method (admin only)."""
    try:
        shipping_service = ShippingService(db)
        success = await shipping_service.delete_shipping_method(method_id)
        
        if not success:
            raise APIException(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Shipping method not found"
            )
        
        return Response.success(message="Shipping method deleted successfully")
    except APIException:
        raise
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_400_BAD_REQUEST,
            message=f"Failed to delete shipping method: {str(e)}"
        )