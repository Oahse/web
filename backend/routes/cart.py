from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from core.database import get_db
from core.exceptions import APIException
from services.cart import CartService
from services.auth import AuthService
from models.user import User
from core.utils.response import Response
from schemas.cart import AddToCartRequest, ApplyPromocodeRequest, CartResponse, UpdateCartItemRequest # Import CartResponse
from core.dependencies import get_current_auth_user

router = APIRouter(prefix="/api/v1/cart", tags=["Cart"])

@router.get("/")
async def get_cart(
    current_user: User = Depends(get_current_auth_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        cart_service = CartService(db)
        cart = await cart_service.get_cart(current_user.id)
        return Response(success=True, data=cart)
    except Exception as e:
        raise APIException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, message=f"Failed to retrieve cart: {e}")

@router.post("/add")
async def add_to_cart(
    request: AddToCartRequest,
    current_user: User = Depends(get_current_auth_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        cart_service = CartService(db)
        cart = await cart_service.add_to_cart(current_user.id, UUID(request.variant_id), request.quantity)
        return Response(success=True, data=cart, message="Item added to cart")
    except HTTPException as e:
        raise APIException(status_code=e.status_code, message=e.detail)
    except Exception as e:
        print(f"Unexpected exception in add_to_cart: {e}")
        raise APIException(status_code=status.HTTP_400_BAD_REQUEST, message=f"Failed to add item to cart {str(e)}")

@router.put("/update/{item_id}")
async def update_cart_item(
    item_id: UUID,
    request: UpdateCartItemRequest,
    current_user: User = Depends(get_current_auth_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        cart_service = CartService(db)
        cart = await cart_service.update_cart_item_quantity(current_user.id, item_id, request.quantity)
        return Response(success=True, data=cart, message="Cart item quantity updated")
    except HTTPException as e:
        raise APIException(status_code=e.status_code, message=e.detail)
    except Exception as e:
        raise APIException(status_code=status.HTTP_400_BAD_REQUEST, message=f"Failed to update cart item quantity: {e}")


@router.delete("/remove/{item_id}")
async def remove_from_cart(
    item_id: UUID,
    current_user: User = Depends(get_current_auth_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        cart_service = CartService(db)
        cart = await cart_service.remove_from_cart(current_user.id, item_id)
        return Response(success=True, data=cart, message="Item removed from cart")
    except HTTPException as e:
        raise APIException(status_code=e.status_code, message=e.detail)
    except Exception as e:
        raise APIException(status_code=status.HTTP_400_BAD_REQUEST, message=f"Failed to remove item from cart: {e}")

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
        raise APIException(status_code=status.HTTP_400_BAD_REQUEST, message=f"Failed to apply promocode: {e}")


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
        raise APIException(status_code=status.HTTP_400_BAD_REQUEST, message="Failed to remove promocode")


@router.get("/count")
async def get_cart_item_count(
    current_user: User = Depends(get_current_auth_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        cart_service = CartService(db)
        count = await cart_service.get_cart_item_count(current_user.id)
        return Response(success=True, data=count)
    except Exception:
        raise APIException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, message="Failed to get cart count")


@router.post("/validate")
async def validate_cart(
    current_user: User = Depends(get_current_auth_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        cart_service = CartService(db)
        result = await cart_service.validate_cart(current_user.id)
        return Response(success=True, data=result)
    except Exception:
        raise APIException(status_code=status.HTTP_400_BAD_REQUEST, message="Failed to validate cart")


@router.post("/shipping-options")
async def get_shipping_options(
    address: dict,
    current_user: User = Depends(get_current_auth_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        cart_service = CartService(db)
        result = await cart_service.get_shipping_options(current_user.id, address)
        return Response(success=True, data=result)
    except Exception as e:
        raise APIException(status_code=status.HTTP_400_BAD_REQUEST, message=f"Failed to get shipping options: {e}")


@router.post("/calculate")
async def calculate_totals(
    data: dict,
    current_user: User = Depends(get_current_auth_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        cart_service = CartService(db)
        result = await cart_service.calculate_totals(current_user.id, data)
        return Response(success=True, data=result)
    except Exception:
        raise APIException(status_code=status.HTTP_400_BAD_REQUEST, message="Failed to calculate totals")


@router.post("/items/{item_id}/save-for-later")
async def save_for_later(
    item_id: UUID,
    current_user: User = Depends(get_current_auth_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        cart_service = CartService(db)
        result = await cart_service.save_for_later(current_user.id, item_id)
        return Response(success=True, data=result)
    except Exception:
        raise APIException(status_code=status.HTTP_400_BAD_REQUEST, message="Failed to save item for later")


@router.post("/items/{item_id}/move-to-cart")
async def move_to_cart(
    item_id: UUID,
    current_user: User = Depends(get_current_auth_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        cart_service = CartService(db)
        result = await cart_service.move_to_cart(current_user.id, item_id)
        return Response(success=True, data=result)
    except Exception:
        raise APIException(status_code=status.HTTP_400_BAD_REQUEST, message="Failed to move item to cart")


@router.get("/saved-items")
async def get_saved_items(
    current_user: User = Depends(get_current_auth_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        cart_service = CartService(db)
        result = await cart_service.get_saved_items(current_user.id)
        return Response(success=True, data=result)
    except Exception:
        raise APIException(status_code=status.HTTP_400_BAD_REQUEST, message="Failed to get saved items")


@router.post("/clear")
async def clear_cart_post(
    current_user: User = Depends(get_current_auth_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        cart_service = CartService(db)
        result = await cart_service.clear_cart(current_user.id)
        return Response(success=True, data=result, message="Cart cleared successfully")
    except Exception:
        raise APIException(status_code=status.HTTP_400_BAD_REQUEST, message="Failed to clear cart")

@router.delete("/clear")
async def clear_cart_delete(
    current_user: User = Depends(get_current_auth_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        cart_service = CartService(db)
        result = await cart_service.clear_cart(current_user.id)
        return Response(success=True, data=result, message="Cart cleared successfully")
    except Exception:
        raise APIException(status_code=status.HTTP_400_BAD_REQUEST, message="Failed to clear cart")


@router.post("/merge")
async def merge_cart(
    request: dict,
    current_user: User = Depends(get_current_auth_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        cart_service = CartService(db)
        items = request.get("items", [])
        result = await cart_service.merge_cart(current_user.id, items)
        return Response(success=True, data=result)
    except Exception as e:
        raise APIException(status_code=status.HTTP_400_BAD_REQUEST, message=f"Failed to merge cart: {e}")


@router.get("/checkout-summary")
async def get_checkout_summary(
    current_user: User = Depends(get_current_auth_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        cart_service = CartService(db)
        result = await cart_service.get_checkout_summary(current_user.id)
        return Response(success=True, data=result)
    except Exception:
        raise APIException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, message="Failed to get checkout summary")
