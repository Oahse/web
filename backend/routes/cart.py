from fastapi import APIRouter, Depends, status, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from core.database import get_db
from core.exceptions import APIException
from core.logging_config import get_logger
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
    current_user: Optional[User] = Depends(get_current_auth_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        cart_service = CartService(db)
        session_id = get_session_id(req) if not current_user else None
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


@router.put("/update/{item_id}")
async def update_cart_item(
    item_id: UUID,
    request: UpdateCartItemRequest,
    req: Request,
    current_user: Optional[User] = Depends(get_current_auth_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        cart_service = CartService(db)
        
        # Get current cart to find the variant_id for this item_id
        cart_key = RedisKeyManager.cart_key(str(current_user.id))
        cart_data = await cart_service.get_hash(cart_key)
        
        if not cart_data or "items" not in cart_data:
            raise HTTPException(status_code=400, detail="Cart is empty")
        
        # Parse items if it's a string
        if isinstance(cart_data.get("items"), str):
            import json
            cart_data["items"] = json.loads(cart_data["items"])
        
        # Find the variant_id for this item_id
        target_variant_id = None
        for variant_key, item in cart_data["items"].items():
            if item.get("id") == str(item_id):
                target_variant_id = UUID(variant_key)
                break
        
        if not target_variant_id:
            raise HTTPException(status_code=404, detail="Item not found in cart")
        
        # Use the existing update_cart_item method
        cart = await cart_service.update_cart_item(
            user_id=current_user.id,
            variant_id=target_variant_id,
            request=request
        )
        return Response(success=True, data=cart, message="Cart item quantity updated")
    except HTTPException as e:
        raise APIException(status_code=e.status_code, message=e.detail)
    except Exception as e:
        raise APIException(status_code=status.HTTP_400_BAD_REQUEST,
                           message=f"Failed to update cart item quantity: {e}")


@router.delete("/remove/{item_id}")
async def remove_from_cart(
    item_id: UUID,
    req: Request,
    current_user: Optional[User] = Depends(get_current_auth_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        cart_service = CartService(db)
        session_id = get_session_id(req) if not current_user else None
        cart = await cart_service.remove_from_cart_by_item_id(
            user_id=current_user.id if current_user else None,
            item_id=item_id
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


@router.post("/promocode")
async def apply_promocode(
    request: ApplyPromocodeRequest,
    current_user: User = Depends(get_current_auth_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        cart_service = CartService(db)
        result = await cart_service.apply_promocode(current_user.id, request.code)
        return Response(success=True, data=result)
    except Exception as e:
        raise APIException(status_code=status.HTTP_400_BAD_REQUEST,
                           message=f"Failed to apply promocode: {e}")


@router.delete("/promocode")
async def remove_promocode(
    current_user: User = Depends(get_current_auth_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        cart_service = CartService(db)
        result = await cart_service.remove_promocode(current_user.id)
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
    except Exception:
        raise APIException(status_code=status.HTTP_400_BAD_REQUEST,
                           message="Failed to calculate totals")


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
