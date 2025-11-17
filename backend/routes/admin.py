from uuid import UUID
from fastapi import APIRouter, Depends, Query, status, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from core.database import get_db
from core.utils.response import Response
from core.exceptions import APIException
from services.admin import AdminService
from services.orders import OrderService
from models.user import User
from services.auth import AuthService
from models.settings import SystemSettings
from schemas.auth import UserCreate # Added UserCreate import

from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class UpdateSystemSettingsRequest(BaseModel):
    maintenance_mode: Optional[bool] = None
    registration_enabled: Optional[bool] = None
    max_file_size: Optional[int] = None
    allowed_file_types: Optional[str] = None
    email_notifications: Optional[bool] = None
    sms_notifications: Optional[bool] = None

async def get_current_auth_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> User:
    return await AuthService.get_current_user(token, db)

router = APIRouter(prefix="/api/v1/admin", tags=["Admin"])

class ShipOrderRequest(BaseModel):
    tracking_number: str
    carrier_name: str

def require_admin(current_user: User = Depends(get_current_auth_user)):
    """Require admin role."""
    if current_user.role not in ["Admin", "SuperAdmin"]:
        raise APIException(
            status_code=status.HTTP_403_FORBIDDEN,
            message="Admin access required"
        )
    return current_user

@router.get("/stats")
async def get_admin_stats(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get admin dashboard statistics."""
    try:
        admin_service = AdminService(db)
        stats = await admin_service.get_dashboard_stats()
        return Response(success=True, data=stats)
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
        return Response(success=True, data=overview)
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to fetch platform overview  {str(e)}"
        )

@router.get("/orders")
async def get_all_orders(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    order_status: Optional[str] = Query(None, alias="status"),
    q: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get all orders (admin only)."""
    try:
        admin_service = AdminService(db)
        orders = await admin_service.get_all_orders(page, limit, order_status, q, date_from, date_to, min_price, max_price)
        return Response(success=True, data=orders)
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to fetch orders {str(e)}"
        )

@router.get("/users")
async def get_all_users(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    role_filter: Optional[str] = None,
    search: Optional[str] = None,
    status: Optional[str] = None,
    verified: Optional[bool] = None,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get all users (admin only)."""
    try:
        admin_service = AdminService(db)
        users = await admin_service.get_all_users(page, limit, role_filter, search, status, verified)
        return Response(success=True, data=users)
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Failed to fetch users"
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
        return Response(success=True, data=user, message="User created successfully")
    except APIException:
        raise
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to create user: {str(e)}"
        )

@router.get("/products")
async def get_all_products_admin(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
    supplier: Optional[str] = None,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get all products (admin only)."""
    try:
        admin_service = AdminService(db)
        products = await admin_service.get_all_products(page, limit, search, category, status, supplier)
        return Response(success=True, data=products)
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Failed to fetch products"
        )

@router.get("/variants")
async def get_all_variants_admin(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = None,
    product_id: Optional[str] = None,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get all variants (admin only)."""
    try:
        admin_service = AdminService(db)
        variants = await admin_service.get_all_variants(page, limit, search, product_id)
        return Response(success=True, data=variants)
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Failed to fetch variants"
        )



@router.put("/users/{user_id}/status")
async def update_user_status(
    user_id: str,
    active: bool,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Update user status (admin only)."""
    try:
        admin_service = AdminService(db)
        user = await admin_service.update_user_status(user_id, active)
        return Response(success=True, data=user, message="User status updated")
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
        return Response(success=True, message="User deleted successfully")
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_400_BAD_REQUEST,
            message="Failed to delete user"
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
        return Response(success=True, data=order)
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
        return Response(success=True, data=order, message="Order status updated to shipped and notification sent.")
    except APIException:
        raise
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_400_BAD_REQUEST,
            message=f"Failed to update order: {str(e)}"
        )

@router.get("/system/settings")
async def get_system_settings(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get system settings (admin only)."""
    try:
        admin_service = AdminService(db)
        settings = await admin_service.get_system_settings()
        return Response(success=True, data=settings)
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to fetch system settings {str(e)}"
        )

@router.put("/system/settings")
async def update_system_settings(
    request: UpdateSystemSettingsRequest,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Update system settings (admin only)."""
    try:
        admin_service = AdminService(db)
        settings = await admin_service.update_system_settings(request.dict(exclude_unset=True))
        return Response(success=True, data=settings, message="System settings updated successfully")
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to update system settings {str(e)}"
        )