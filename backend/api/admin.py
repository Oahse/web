from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, Query, status, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, Dict, Any, List
from core.db import get_db
from core.utils.response import Response
from core.errors import APIException
from core.logging import get_logger
from services.admin import AdminService
from services.orders import OrderService
from services.shipping import ShippingService
from models.user import User
from models.orders import Order
from services.auth import AuthService
from schemas.auth import UserCreate
from schemas.shipping import ShippingMethodCreate, ShippingMethodUpdate
from core.dependencies import get_current_auth_user

logger = get_logger(__name__)

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
    if current_user.role not in ["admin", "manager", "Admin", "SuperAdmin"]:
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
        return Response.success(data=order, message="Order status updated to shipped.")
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
    from fastapi.responses import StreamingResponse, FileResponse
    from services.orders import OrderService as EnhancedOrderService
    import os
    import io
    
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
        
        # Check if invoice generation was successful
        if not invoice.get('success', False):
            error_msg = invoice.get('message', 'Failed to generate invoice')
            raise APIException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=error_msg
            )
        
        # Handle pdf_bytes response (new format)
        if 'pdf_bytes' in invoice:
            pdf_bytes = invoice['pdf_bytes']
            return StreamingResponse(
                io.BytesIO(pdf_bytes),
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f"attachment; filename=invoice-{order_id}.pdf"
                }
            )
        
        # Handle invoice_path response (legacy format)
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
        
        # Fallback: return invoice data as JSON
        return Response.success(data=invoice)
    except APIException:
        raise
    except Exception as e:
        logger.exception(f"Failed to generate invoice for order {order_id}")
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
        logger.exception("Failed to fetch users")
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
    logger.debug(f"Fetching products: page={page}, limit={limit}, search={search}")
    try:
        admin_service = AdminService(db)
        products = await admin_service.get_all_products(page, limit, search, category, status, supplier)
        logger.debug(f"Successfully fetched {len(products.get('data', []))} products")
        return Response.success(data=products)
    except Exception as e:
        logger.exception("Failed to fetch products in admin route")
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Failed to fetch products"
        )

@router.get("/products/{product_id}")
async def get_product_by_id_admin(
    product_id: UUID,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get a single product by ID with all related data (admin only)."""
    try:
        from models.product import Product, ProductVariant, ProductImage, Category
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        
        # Query product with all related data
        query = select(Product).options(
            selectinload(Product.variants).selectinload(ProductVariant.images),
            selectinload(Product.variants).selectinload(ProductVariant.inventory),
            selectinload(Product.category),
            selectinload(Product.supplier)
        ).where(Product.id == product_id)
        
        result = await db.execute(query)
        product = result.scalar_one_or_none()
        
        if not product:
            raise APIException(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Product not found"
            )
        
        # Convert to detailed dict with all related data
        product_data = product.to_dict(include_variants=True)
        
        # Add detailed variant information
        detailed_variants = []
        for variant in product.variants:
            variant_data = variant.to_dict(include_images=True, include_product=False)
            
            # Add inventory details with error handling
            if variant.inventory:
                try:
                    variant_data["inventory"] = {
                        "quantity_available": getattr(variant.inventory, 'quantity_available', 0),
                        "quantity": getattr(variant.inventory, 'quantity', 0),
                        "reorder_level": getattr(variant.inventory, 'reorder_level', None),
                        "reorder_quantity": getattr(variant.inventory, 'reorder_quantity', None),
                        "warehouse_location": getattr(variant.inventory, 'warehouse_location', None),
                        "updated_at": variant.inventory.updated_at.isoformat() if variant.inventory.updated_at else None
                    }
                except Exception as inv_error:
                    logger.warning(f"Error processing inventory for variant {variant.id}: {inv_error}")
                    variant_data["inventory"] = {"error": "Failed to load inventory data"}
            
            detailed_variants.append(variant_data)
        
        product_data["variants"] = detailed_variants
        
        # Add category details with error handling
        if product.category:
            try:
                product_data["category"] = product.category.to_dict()
            except Exception as cat_error:
                logger.warning(f"Error processing category for product {product.id}: {cat_error}")
                product_data["category"] = {"error": "Failed to load category data"}
        
        # Add supplier details with error handling
        if product.supplier:
            try:
                supplier = product.supplier
                # Handle different possible name field combinations
                supplier_name = (
                    getattr(supplier, 'name', None) or 
                    getattr(supplier, 'firstname', None) and getattr(supplier, 'lastname', None) and 
                    f"{supplier.firstname} {supplier.lastname}".strip() or 
                    supplier.email
                )
                
                product_data["supplier"] = {
                    "id": str(supplier.id),
                    "name": supplier_name,
                    "email": getattr(supplier, 'email', None),
                    "phone": getattr(supplier, 'phone', None),
                }
            except Exception as sup_error:
                logger.warning(f"Error processing supplier for product {product.id}: {sup_error}")
                product_data["supplier"] = {"error": "Failed to load supplier data"}
        
        return Response.success(data=product_data)
    except APIException:
        raise
    except Exception as e:
        logger.exception(f"Failed to fetch product {product_id}")
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to fetch product: {str(e)}"
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

@router.put("/variants/{variant_id}/stock")
async def update_variant_stock_admin(
    variant_id: UUID,
    stock_data: dict,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Update variant stock (admin only)."""
    try:
        from models.inventories import Inventory
        from sqlalchemy import select
        
        stock = stock_data.get("stock")
        if stock is None or not isinstance(stock, int) or stock < 0:
            raise APIException(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Invalid stock value. Must be a non-negative integer."
            )
        
        # Find the inventory record for this variant
        query = select(Inventory).where(Inventory.variant_id == variant_id)
        result = await db.execute(query)
        inventory = result.scalar_one_or_none()
        
        if not inventory:
            raise APIException(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Inventory record not found for this variant"
            )
        
        # Update the stock
        inventory.quantity_available = stock
        inventory.quantity = stock  # Update legacy field too
        
        await db.commit()
        
        return Response.success(
            data={
                "variant_id": str(variant_id),
                "stock": stock,
                "updated_at": inventory.updated_at.isoformat() if inventory.updated_at else None
            },
            message="Variant stock updated successfully"
        )
    except APIException:
        raise
    except Exception as e:
        logger.error(f"Error updating variant stock: {e}")
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Failed to update variant stock"
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
        logger.exception("Failed to export orders")
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


# Include tax rates admin routes
# Tax Rates Admin Routes
from pydantic import Field
from typing import List

# Schemas for tax rates
class TaxRateCreate(BaseModel):
    country_code: str = Field(..., min_length=2, max_length=2, description="ISO 3166-1 alpha-2 country code")
    country_name: str = Field(..., min_length=1, max_length=100)
    province_code: Optional[str] = Field(None, max_length=10, description="State/Province code")
    province_name: Optional[str] = Field(None, max_length=100)
    tax_rate: float = Field(..., ge=0, le=1, description="Tax rate as decimal (e.g., 0.0725 for 7.25%)")
    tax_name: Optional[str] = Field(None, max_length=50, description="e.g., GST, VAT, Sales Tax")
    is_active: bool = True


class TaxRateUpdate(BaseModel):
    country_name: Optional[str] = Field(None, min_length=1, max_length=100)
    province_name: Optional[str] = Field(None, max_length=100)
    tax_rate: Optional[float] = Field(None, ge=0, le=1)
    tax_name: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = None


class TaxRateResponse(BaseModel):
    id: UUID
    country_code: str
    country_name: str
    province_code: Optional[str]
    province_name: Optional[str]
    tax_rate: float
    tax_percentage: float  # Computed: tax_rate * 100
    tax_name: Optional[str]
    is_active: bool
    created_at: str
    updated_at: Optional[str]

    class Config:
        from_attributes = True


@router.get("/tax-rates/", response_model=List[TaxRateResponse])
async def list_tax_rates(
    country_code: Optional[str] = Query(None, description="Filter by country code"),
    province_code: Optional[str] = Query(None, description="Filter by province code"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search in country/province names"),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """List all tax rates with filtering and pagination"""
    from models.tax_rates import TaxRate
    from sqlalchemy import select, and_, or_
    
    try:
        # Build query
        query = select(TaxRate)
        
        # Apply filters
        conditions = []
        if country_code:
            conditions.append(TaxRate.country_code == country_code.upper())
        if province_code:
            conditions.append(TaxRate.province_code == province_code.upper())
        if is_active is not None:
            conditions.append(TaxRate.is_active == is_active)
        if search:
            search_term = f"%{search}%"
            conditions.append(
                or_(
                    TaxRate.country_name.ilike(search_term),
                    TaxRate.province_name.ilike(search_term)
                )
            )
        
        if conditions:
            query = query.where(and_(*conditions))
        
        # Order by country, then province
        query = query.order_by(TaxRate.country_code, TaxRate.province_code)
        
        # Apply pagination
        offset = (page - 1) * per_page
        query = query.offset(offset).limit(per_page)
        
        result = await db.execute(query)
        tax_rates = result.scalars().all()
        
        # Format response
        response_data = []
        for rate in tax_rates:
            response_data.append(TaxRateResponse(
                id=rate.id,
                country_code=rate.country_code,
                country_name=rate.country_name,
                province_code=rate.province_code,
                province_name=rate.province_name,
                tax_rate=rate.tax_rate,
                tax_percentage=rate.tax_rate * 100,
                tax_name=rate.tax_name,
                is_active=rate.is_active,
                created_at=rate.created_at.isoformat(),
                updated_at=rate.updated_at.isoformat() if rate.updated_at else None
            ))
        
        return response_data
        
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to list tax rates: {str(e)}"
        )


@router.get("/tax-rates/countries", response_model=List[dict])
async def list_countries(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get list of unique countries with tax rates"""
    from models.tax_rates import TaxRate
    from sqlalchemy import select, func
    
    try:
        query = select(
            TaxRate.country_code,
            TaxRate.country_name,
            func.count(TaxRate.id).label('rate_count')
        ).group_by(
            TaxRate.country_code,
            TaxRate.country_name
        ).order_by(TaxRate.country_name)
        
        result = await db.execute(query)
        countries = result.all()
        
        return [
            {
                "country_code": row.country_code,
                "country_name": row.country_name,
                "rate_count": row.rate_count
            }
            for row in countries
        ]
        
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to list countries: {str(e)}"
        )


@router.get("/tax-rates/{tax_rate_id}", response_model=TaxRateResponse)
async def get_tax_rate(
    tax_rate_id: UUID,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific tax rate by ID"""
    from models.tax_rates import TaxRate
    from sqlalchemy import select
    
    try:
        result = await db.execute(
            select(TaxRate).where(TaxRate.id == tax_rate_id)
        )
        tax_rate = result.scalar_one_or_none()
        
        if not tax_rate:
            raise APIException(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Tax rate not found"
            )
        
        return TaxRateResponse(
            id=tax_rate.id,
            country_code=tax_rate.country_code,
            country_name=tax_rate.country_name,
            province_code=tax_rate.province_code,
            province_name=tax_rate.province_name,
            tax_rate=tax_rate.tax_rate,
            tax_percentage=tax_rate.tax_rate * 100,
            tax_name=tax_rate.tax_name,
            is_active=tax_rate.is_active,
            created_at=tax_rate.created_at.isoformat(),
            updated_at=tax_rate.updated_at.isoformat() if tax_rate.updated_at else None
        )
        
    except APIException:
        raise
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to get tax rate: {str(e)}"
        )


@router.post("/tax-rates/", response_model=TaxRateResponse, status_code=status.HTTP_201_CREATED)
async def create_tax_rate(
    data: TaxRateCreate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Create a new tax rate"""
    from models.tax_rates import TaxRate
    from sqlalchemy import select, and_
    
    try:
        # Check if tax rate already exists for this location
        existing_query = select(TaxRate).where(
            and_(
                TaxRate.country_code == data.country_code.upper(),
                TaxRate.province_code == (data.province_code.upper() if data.province_code else None)
            )
        )
        result = await db.execute(existing_query)
        existing = result.scalar_one_or_none()
        
        if existing:
            raise APIException(
                status_code=status.HTTP_400_BAD_REQUEST,
                message=f"Tax rate already exists for {data.country_code}" + 
                        (f"-{data.province_code}" if data.province_code else "")
            )
        
        # Create new tax rate
        tax_rate = TaxRate(
            country_code=data.country_code.upper(),
            country_name=data.country_name,
            province_code=data.province_code.upper() if data.province_code else None,
            province_name=data.province_name,
            tax_rate=data.tax_rate,
            tax_name=data.tax_name,
            is_active=data.is_active
        )
        
        db.add(tax_rate)
        await db.commit()
        await db.refresh(tax_rate)
        
        return TaxRateResponse(
            id=tax_rate.id,
            country_code=tax_rate.country_code,
            country_name=tax_rate.country_name,
            province_code=tax_rate.province_code,
            province_name=tax_rate.province_name,
            tax_rate=tax_rate.tax_rate,
            tax_percentage=tax_rate.tax_rate * 100,
            tax_name=tax_rate.tax_name,
            is_active=tax_rate.is_active,
            created_at=tax_rate.created_at.isoformat(),
            updated_at=tax_rate.updated_at.isoformat() if tax_rate.updated_at else None
        )
        
    except APIException:
        raise
    except Exception as e:
        await db.rollback()
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to create tax rate: {str(e)}"
        )


@router.put("/tax-rates/{tax_rate_id}", response_model=TaxRateResponse)
async def update_tax_rate(
    tax_rate_id: UUID,
    data: TaxRateUpdate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Update an existing tax rate"""
    from models.tax_rates import TaxRate
    from sqlalchemy import select
    
    try:
        result = await db.execute(
            select(TaxRate).where(TaxRate.id == tax_rate_id)
        )
        tax_rate = result.scalar_one_or_none()
        
        if not tax_rate:
            raise APIException(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Tax rate not found"
            )
        
        # Update fields
        if data.country_name is not None:
            tax_rate.country_name = data.country_name
        if data.province_name is not None:
            tax_rate.province_name = data.province_name
        if data.tax_rate is not None:
            tax_rate.tax_rate = data.tax_rate
        if data.tax_name is not None:
            tax_rate.tax_name = data.tax_name
        if data.is_active is not None:
            tax_rate.is_active = data.is_active
        
        await db.commit()
        await db.refresh(tax_rate)
        
        return TaxRateResponse(
            id=tax_rate.id,
            country_code=tax_rate.country_code,
            country_name=tax_rate.country_name,
            province_code=tax_rate.province_code,
            province_name=tax_rate.province_name,
            tax_rate=tax_rate.tax_rate,
            tax_percentage=tax_rate.tax_rate * 100,
            tax_name=tax_rate.tax_name,
            is_active=tax_rate.is_active,
            created_at=tax_rate.created_at.isoformat(),
            updated_at=tax_rate.updated_at.isoformat() if tax_rate.updated_at else None
        )
        
    except APIException:
        raise
    except Exception as e:
        await db.rollback()
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to update tax rate: {str(e)}"
        )


@router.delete("/tax-rates/{tax_rate_id}")
async def delete_tax_rate(
    tax_rate_id: UUID,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Delete a tax rate"""
    from models.tax_rates import TaxRate
    from sqlalchemy import select
    
    try:
        result = await db.execute(
            select(TaxRate).where(TaxRate.id == tax_rate_id)
        )
        tax_rate = result.scalar_one_or_none()
        
        if not tax_rate:
            raise APIException(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Tax rate not found"
            )
        
        await db.delete(tax_rate)
        await db.commit()
        
        return Response.success(message="Tax rate deleted successfully")
        
    except APIException:
        raise
    except Exception as e:
        await db.rollback()
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to delete tax rate: {str(e)}"
        )


@router.post("/tax-rates/bulk-update")
async def bulk_update_tax_rates(
    updates: List[dict],
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Bulk update multiple tax rates"""
    from models.tax_rates import TaxRate
    from sqlalchemy import select
    
    try:
        updated_count = 0
        errors = []
        
        for update_data in updates:
            try:
                tax_rate_id = UUID(update_data.get("id"))
                result = await db.execute(
                    select(TaxRate).where(TaxRate.id == tax_rate_id)
                )
                tax_rate = result.scalar_one_or_none()
                
                if tax_rate:
                    if "tax_rate" in update_data:
                        tax_rate.tax_rate = float(update_data["tax_rate"])
                    if "is_active" in update_data:
                        tax_rate.is_active = bool(update_data["is_active"])
                    if "tax_name" in update_data:
                        tax_rate.tax_name = update_data["tax_name"]
                    
                    updated_count += 1
                else:
                    errors.append(f"Tax rate {tax_rate_id} not found")
                    
            except Exception as e:
                errors.append(f"Error updating {update_data.get('id')}: {str(e)}")
        
        await db.commit()
        
        return Response.success(
            data={
                "updated_count": updated_count,
                "errors": errors
            },
            message=f"Successfully updated {updated_count} tax rates"
        )
        
    except Exception as e:
        await db.rollback()
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to bulk update tax rates: {str(e)}"
        )
