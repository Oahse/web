from fastapi import APIRouter, Depends, status, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from core.database import get_db
from core.exceptions import APIException
from core.logging import get_logger
from core.redis import RedisKeyManager
from services.cart import CartService
from models.user import User
from core.utils.response import Response
from schemas.cart import AddToCartRequest, ApplyPromocodeRequest, UpdateCartItemRequest
from core.dependencies import get_current_auth_user
from typing import Optional

logger = get_logger(__name__)

router = APIRouter(prefix="/cart", tags=["Cart"])


def get_session_id(request: Request) -> Optional[str]:
    """Extract session ID from request for guest carts"""
    # No longer using request.session for "strictly JWT" with no cookies
    return request.headers.get('X-Session-ID')


@router.get("/")
async def get_cart(
    request: Request,
    country: Optional[str] = None,  # Country code from query param or header
    province: Optional[str] = None,  # Province/state code from query param or header
    current_user: Optional[User] = Depends(get_current_auth_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        # Try to get location from query params, headers, or default to US
        country_code = country or request.headers.get('X-Country-Code', 'US')
        province_code = province or request.headers.get('X-Province-Code')
        
        cart_service = CartService(db)
        session_id = get_session_id(request) if not current_user else None
        cart = await cart_service.get_cart(
            user_id=current_user.id if current_user else None,
            session_id=session_id,
            country_code=country_code,
            province_code=province_code
        )
        return Response(success=True, data=cart)
    except Exception as e:
        raise APIException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                           message=f"Failed to retrieve cart: {e}")


@router.post("/add")
async def add_to_cart(
    request: AddToCartRequest,
    req: Request,
    country: Optional[str] = None,
    province: Optional[str] = None,
    current_user: Optional[User] = Depends(get_current_auth_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        cart_service = CartService(db)
        session_id = get_session_id(req) if not current_user else None
        
        # Add item to cart with ARQ background tasks
        cart = await cart_service.add_to_cart(
            user_id=current_user.id if current_user else None,
            variant_id=request.variant_id,
            quantity=request.quantity,
            session_id=session_id
        )
        
        return Response(success=True, data=cart, message="Item added to cart")
    except HTTPException as e:
        raise APIException(status_code=e.status_code, message=e.detail)
    except Exception as e:
        logger.exception("Unexpected exception in add_to_cart")
        raise APIException(status_code=status.HTTP_400_BAD_REQUEST,
                           message=f"Failed to add item to cart {str(e)}")


@router.put("/items/{cart_item_id}")
async def update_cart_item(
    cart_item_id: UUID,
    request: UpdateCartItemRequest,
    req: Request,
    country: Optional[str] = None,
    province: Optional[str] = None,
    current_user: Optional[User] = Depends(get_current_auth_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update cart item quantity by cart_item_id
    
    The cart_item_id is the unique ID assigned to each item when added to cart,
    not the variant_id or product_id.
    """
    try:
        logger.info(f"Update cart item endpoint hit: cart_item_id={cart_item_id}, quantity={request.quantity}, user_id={current_user.id if current_user else None}")
        
        if not current_user:
            raise HTTPException(status_code=401, detail="Authentication required")
        
        # Get location from query params or headers
        country_code = country or req.headers.get('X-Country-Code', 'US')
        province_code = province or req.headers.get('X-Province-Code')
        
        logger.info(f"Location: country={country_code}, province={province_code}")
        
        cart_service = CartService(db)
        
        # Use the update_cart_item_quantity method which handles cart_item_id
        logger.info(f"Calling update_cart_item_quantity...")
        result = await cart_service.update_cart_item_quantity(
            user_id=current_user.id,
            cart_item_id=cart_item_id,
            quantity=request.quantity
        )
        logger.info(f"Update result: {result}")
        
        # Re-fetch cart with location to recalculate tax
        logger.info(f"Re-fetching cart with location...")
        cart = await cart_service.get_cart(
            user_id=current_user.id,
            country_code=country_code,
            province_code=province_code
        )
        logger.info(f"Cart fetched successfully")
        
        return Response(success=True, data=cart, message="Cart item quantity updated")
    except HTTPException as e:
        logger.error(f"HTTPException in update_cart_item: {e.status_code} - {e.detail}")
        raise APIException(status_code=e.status_code, message=e.detail)
    except Exception as e:
        logger.exception("Error updating cart item")
        raise APIException(status_code=status.HTTP_400_BAD_REQUEST,
                           message=f"Failed to update cart item quantity: {e}")


@router.delete("/items/{cart_item_id}")
async def remove_from_cart(
    cart_item_id: UUID,
    req: Request,
    current_user: Optional[User] = Depends(get_current_auth_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Remove item from cart by cart_item_id
    
    The cart_item_id is the unique ID assigned to each item when added to cart.
    """
    try:
        cart_service = CartService(db)
        session_id = get_session_id(req) if not current_user else None
        cart = await cart_service.remove_from_cart_by_item_id(
            user_id=current_user.id if current_user else None,
            cart_item_id=cart_item_id
        )
        return Response(success=True, data=cart, message="Item removed from cart")
    except HTTPException as e:
        raise APIException(status_code=e.status_code, message=e.detail)
    except Exception as e:
        raise APIException(status_code=status.HTTP_400_BAD_REQUEST,
                           message=f"Failed to remove item from cart: {e}")


@router.post("/promocode")
async def apply_promocode(
    request: ApplyPromocodeRequest,
    req: Request,
    current_user: Optional[User] = Depends(get_current_auth_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        cart_service = CartService(db)
        session_id = get_session_id(req) if not current_user else None
        result = await cart_service.apply_promocode(
            user_id=current_user.id if current_user else None,
            code=request.code,
            session_id=session_id
        )
        return Response(success=True, data=result)
    except Exception as e:
        raise APIException(status_code=status.HTTP_400_BAD_REQUEST,
                           message=f"Failed to apply promocode: {e}")


@router.delete("/promocode")
async def remove_promocode(
    request: Request,
    current_user: Optional[User] = Depends(get_current_auth_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        cart_service = CartService(db)
        session_id = get_session_id(request) if not current_user else None
        result = await cart_service.remove_promocode(
            user_id=current_user.id if current_user else None,
            session_id=session_id
        )
        return Response(success=True, data=result)
    except Exception:
        raise APIException(status_code=status.HTTP_400_BAD_REQUEST,
                           message="Failed to remove promocode")


@router.get("/count")
async def get_cart_item_count(
    request: Request,
    current_user: Optional[User] = Depends(get_current_auth_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        cart_service = CartService(db)
        session_id = get_session_id(request) if not current_user else None
        count = await cart_service.get_cart_item_count(
            user_id=current_user.id if current_user else None,
            session_id=session_id
        )
        return Response(success=True, data=count)
    except Exception:
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, message="Failed to get cart count")


@router.post("/validate")
async def validate_cart(
    request: Request,
    country: Optional[str] = None,
    province: Optional[str] = None,
    current_user: Optional[User] = Depends(get_current_auth_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Comprehensive cart validation - should be called before checkout
    Validates availability, stock, prices, and product status
    """
    try:
        cart_service = CartService(db)
        
        if not current_user:
            raise APIException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                message="Authentication required for cart validation"
            )
        
        # Get location from query params or headers
        country_code = country or request.headers.get('X-Country-Code', 'US')
        province_code = province or request.headers.get('X-Province-Code')
        
        result = await cart_service.validate_cart(
            user_id=current_user.id,
            country_code=country_code,
            province_code=province_code
        )
        
        # Determine response status based on validation results
        if result.get("valid", False) and result.get("can_checkout", False):
            return Response(
                success=True, 
                data=result, 
                message="Cart validation successful - ready for checkout"
            )
        elif result.get("issues"):
            # Cart has issues but may be recoverable
            error_count = len([issue for issue in result["issues"] if issue.get("severity") == "error"])
            warning_count = len([issue for issue in result["issues"] if issue.get("severity") == "warning"])
            
            if error_count > 0:
                return Response(
                    success=False,
                    data=result,
                    message=f"Cart validation failed with {error_count} error(s) and {warning_count} warning(s). Please review your cart."
                )
            else:
                return Response(
                    success=True,
                    data=result,
                    message=f"Cart validation completed with {warning_count} warning(s). You can proceed to checkout."
                )
        else:
            return Response(
                success=False,
                data=result,
                message="Cart validation failed"
            )
            
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Cart validation error: {str(e)}"
        )


@router.post("/shipping-options")
async def get_shipping_options(
    address: dict,
    request: Request,
    current_user: Optional[User] = Depends(get_current_auth_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        cart_service = CartService(db)
        session_id = get_session_id(request) if not current_user else None
        result = await cart_service.get_shipping_options(
            user_id=current_user.id if current_user else None,
            address=address,
            session_id=session_id
        )
        return Response(success=True, data=result)
    except Exception as e:
        raise APIException(status_code=status.HTTP_400_BAD_REQUEST,
                           message=f"Failed to get shipping options: {e}")


@router.post("/calculate")
async def calculate_totals(
    data: dict,
    request: Request,
    current_user: Optional[User] = Depends(get_current_auth_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        cart_service = CartService(db)
        session_id = get_session_id(request) if not current_user else None
        result = await cart_service.calculate_totals(
            user_id=current_user.id if current_user else None,
            data=data,
            session_id=session_id
        )
        return Response(success=True, data=result)
    except Exception as e:
        logger.error(f"Failed to calculate totals: {str(e)}", exc_info=True)
        raise APIException(status_code=status.HTTP_400_BAD_REQUEST,
                           message=f"Failed to calculate totals: {str(e)}")


@router.post("/clear")
async def clear_cart_post(
    request: Request,
    current_user: Optional[User] = Depends(get_current_auth_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        cart_service = CartService(db)
        session_id = get_session_id(request) if not current_user else None
        result = await cart_service.clear_cart(
            user_id=current_user.id if current_user else None,
            session_id=session_id
        )
        return Response(success=True, data=result, message="Cart cleared successfully")
    except Exception:
        raise APIException(
            status_code=status.HTTP_400_BAD_REQUEST, message="Failed to clear cart")


@router.delete("/clear")
async def clear_cart_delete(
    request: Request,
    current_user: Optional[User] = Depends(get_current_auth_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        cart_service = CartService(db)
        session_id = get_session_id(request) if not current_user else None
        result = await cart_service.clear_cart(
            user_id=current_user.id if current_user else None,
            session_id=session_id
        )
        return Response(success=True, data=result, message="Cart cleared successfully")
    except Exception:
        raise APIException(
            status_code=status.HTTP_400_BAD_REQUEST, message="Failed to clear cart")


@router.post("/merge")
async def merge_cart(
    request: Request,
    current_user: User = Depends(get_current_auth_user),
    db: AsyncSession = Depends(get_db)
):
    """Merge guest cart with user cart when user logs in"""
    try:
        cart_service = CartService(db)
        session_id = get_session_id(request)
        
        if session_id:
            result = await cart_service.merge_carts(current_user.id, session_id)
            return Response(success=True, data=result, message="Carts merged successfully")
        else:
            # No session cart to merge
            result = await cart_service.get_cart(user_id=current_user.id)
            return Response(success=True, data=result, message="No guest cart to merge")
    except Exception as e:
        raise APIException(status_code=status.HTTP_400_BAD_REQUEST,
                           message=f"Failed to merge cart: {e}")


@router.get("/checkout-summary")
async def get_checkout_summary(
    request: Request,
    current_user: Optional[User] = Depends(get_current_auth_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        cart_service = CartService(db)
        session_id = get_session_id(request) if not current_user else None
        result = await cart_service.get_checkout_summary(
            user_id=current_user.id if current_user else None,
            session_id=session_id
        )
        return Response(success=True, data=result)
    except Exception:
        raise APIException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                           message="Failed to get checkout summary")
