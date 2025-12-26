from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from core.database import get_db
from services.wishlist import WishlistService
from schemas.wishlist import WishlistCreate, WishlistUpdate, WishlistResponse, WishlistItemCreate, WishlistItemResponse
from models.user import User
from core.dependencies import get_current_auth_user
from core.utils.response import Response
from core.exceptions import APIException

router = APIRouter(prefix="/users", tags=["Wishlists"])


@router.post("/{user_id}/wishlists/default")
async def create_default_wishlist(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_auth_user)
):
    """Create a default wishlist for the user if none exists."""
    try:
        # Verify user has access to this user_id
        if str(current_user.id) != str(user_id) and current_user.role != "Admin":
            raise APIException(
                status_code=status.HTTP_403_FORBIDDEN,
                message="Access denied: Cannot create wishlist for other users"
            )

        service = WishlistService(db)

        # Check if user already has a default wishlist
        existing_wishlists = await service.get_wishlists(user_id)
        default_wishlist = next(
            (w for w in existing_wishlists if w.is_default), None)

        if default_wishlist:
            # Return existing default wishlist
            wishlist_data = {
                "id": default_wishlist.id,
                "user_id": default_wishlist.user_id,
                "name": default_wishlist.name or "My Wishlist",
                "is_default": default_wishlist.is_default,
                "created_at": default_wishlist.created_at.isoformat() if default_wishlist.created_at else None,
                "updated_at": default_wishlist.updated_at.isoformat() if default_wishlist.updated_at else None,
                "items": []
            }
            return Response.success(data=WishlistResponse.model_validate(wishlist_data))

        # Create new default wishlist
        from schemas.wishlist import WishlistCreate
        payload = WishlistCreate(name="My Wishlist", is_default=True)
        wishlist = await service.create_wishlist(user_id, payload)

        wishlist_data = {
            "id": wishlist.id,
            "user_id": wishlist.user_id,
            "name": wishlist.name or "My Wishlist",
            "is_default": wishlist.is_default,
            "created_at": wishlist.created_at.isoformat() if wishlist.created_at else None,
            "updated_at": wishlist.updated_at.isoformat() if wishlist.updated_at else None,
            "items": []
        }

        return Response.success(data=WishlistResponse.model_validate(wishlist_data), status_code=status.HTTP_201_CREATED)
    except APIException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to create default wishlist: {str(e)}"
        )


@router.get("/{user_id}/wishlists")
async def get_wishlists(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_auth_user)
):
    try:
        # Verify user has access to this user_id (either their own or admin)
        if str(current_user.id) != str(user_id) and current_user.role != "Admin":
            raise APIException(
                status_code=status.HTTP_403_FORBIDDEN,
                message="Access denied: Cannot access other user's wishlists"
            )

        service = WishlistService(db)
        wishlists = await service.get_wishlists(user_id)

        # Serialize wishlists with proper datetime handling
        serialized_wishlists = []
        for wishlist in wishlists:
            try:
                # Serialize items with better error handling
                items = []
                for item in (wishlist.items or []):
                    try:
                        item_data = {
                            "id": item.id,
                            "wishlist_id": item.wishlist_id,
                            "product_id": item.product_id,
                            "variant_id": item.variant_id,
                            "quantity": item.quantity,
                            "added_at": item.created_at.isoformat() if item.created_at else None,
                            "product": item.product.to_dict() if item.product else None,
                            "variant": item.variant.to_dict() if item.variant else None
                        }
                        items.append(item_data)
                    except Exception as e:
                        # Add minimal item data
                        items.append({
                            "id": item.id,
                            "wishlist_id": item.wishlist_id,
                            "product_id": item.product_id,
                            "variant_id": item.variant_id,
                            "quantity": item.quantity,
                            "added_at": item.created_at.isoformat() if item.created_at else None,
                            "product": None,
                            "variant": None
                        })

                wishlist_data = {
                    "id": wishlist.id,
                    "user_id": wishlist.user_id,
                    "name": wishlist.name or "My Wishlist",
                    "is_default": wishlist.is_default,
                    "created_at": wishlist.created_at.isoformat() if wishlist.created_at else None,
                    "updated_at": wishlist.updated_at.isoformat() if wishlist.updated_at else None,
                    "items": items
                }
                serialized_wishlists.append(
                    WishlistResponse.model_validate(wishlist_data))
            except Exception as e:
                # Add minimal wishlist data
                try:
                    minimal_data = {
                        "id": wishlist.id,
                        "user_id": wishlist.user_id,
                        "name": getattr(wishlist, 'name', None) or "My Wishlist",
                        "is_default": getattr(wishlist, 'is_default', False),
                        "created_at": wishlist.created_at.isoformat() if wishlist.created_at else None,
                        "updated_at": wishlist.updated_at.isoformat() if wishlist.updated_at else None,
                        "items": []
                    }
                    serialized_wishlists.append(
                        WishlistResponse.model_validate(minimal_data))
                except Exception as e2:
                    continue

        return Response.success(data=serialized_wishlists)
    except APIException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to fetch wishlists: {str(e)}"
        )


@router.post("/{user_id}/wishlists")
async def create_wishlist(
    user_id: UUID,
    payload: WishlistCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_auth_user)
):
    try:
        # Verify user has access to this user_id
        if str(current_user.id) != str(user_id) and current_user.role != "Admin":
            raise APIException(
                status_code=status.HTTP_403_FORBIDDEN,
                message="Access denied: Cannot create wishlist for other users"
            )

        service = WishlistService(db)
        wishlist = await service.create_wishlist(user_id, payload)

        # Serialize the created wishlist
        wishlist_data = {
            "id": wishlist.id,
            "user_id": wishlist.user_id,
            "name": wishlist.name or "My Wishlist",
            "is_default": wishlist.is_default,
            "created_at": wishlist.created_at.isoformat() if wishlist.created_at else None,
            "updated_at": wishlist.updated_at.isoformat() if wishlist.updated_at else None,
            "items": []
        }

        return Response.success(data=WishlistResponse.model_validate(wishlist_data), status_code=status.HTTP_201_CREATED)
    except APIException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to create wishlist: {str(e)}"
        )


@router.get("/{user_id}/wishlists/{wishlist_id}")
async def get_wishlist_by_id(
    user_id: UUID,
    wishlist_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_auth_user)
):
    service = WishlistService(db)
    wishlist = await service.get_wishlist_by_id(wishlist_id, user_id)
    if not wishlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, message="Wishlist not found")
    return Response.success(data=WishlistResponse.from_orm(wishlist))


@router.put("/{user_id}/wishlists/{wishlist_id}")
async def update_wishlist(
    user_id: UUID,
    wishlist_id: UUID,
    payload: WishlistUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_auth_user)
):
    service = WishlistService(db)
    updated_wishlist = await service.update_wishlist(wishlist_id, user_id, payload)
    if not updated_wishlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, message="Wishlist not found")
    return Response.success(data=WishlistResponse.from_orm(updated_wishlist))


@router.delete("/{user_id}/wishlists/{wishlist_id}")
async def delete_wishlist(
    user_id: UUID,
    wishlist_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_auth_user)
):
    service = WishlistService(db)
    deleted = await service.delete_wishlist(wishlist_id, user_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, message="Wishlist not found")
    return Response.success(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{user_id}/wishlists/{wishlist_id}/items")
async def add_item_to_wishlist(
    user_id: UUID,
    wishlist_id: UUID,
    payload: WishlistItemCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_auth_user)
):
    try:
        # Verify user has access to this user_id
        if str(current_user.id) != str(user_id) and current_user.role != "Admin":
            raise APIException(
                status_code=status.HTTP_403_FORBIDDEN,
                message="Access denied: Cannot add items to other user's wishlists"
            )

        service = WishlistService(db)
        item = await service.add_item_to_wishlist(wishlist_id, payload)

        # Serialize the item properly
        item_data = {
            "id": item.id,
            "wishlist_id": item.wishlist_id,
            "product_id": item.product_id,
            "variant_id": item.variant_id,
            "quantity": item.quantity,
            "added_at": item.created_at.isoformat() if item.created_at else None,
            "product": item.product.to_dict() if item.product else None,
            "variant": item.variant.to_dict() if item.variant else None
        }

        return Response.success(data=WishlistItemResponse.model_validate(item_data), status_code=status.HTTP_201_CREATED)
    except APIException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to add item to wishlist: {str(e)}"
        )


@router.delete("/{user_id}/wishlists/{wishlist_id}/items/{item_id}")
async def remove_item_from_wishlist(
    user_id: UUID,
    wishlist_id: UUID,
    item_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_auth_user)
):
    try:
        # Verify user has access to this user_id
        if str(current_user.id) != str(user_id) and current_user.role != "Admin":
            raise APIException(
                status_code=status.HTTP_403_FORBIDDEN,
                message="Access denied: Cannot remove items from other user's wishlists"
            )

        service = WishlistService(db)
        deleted = await service.remove_item_from_wishlist(wishlist_id, item_id)
        if not deleted:
            raise APIException(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Wishlist item not found"
            )
        return Response.success(data=None, message="Item removed successfully")
    except APIException:
        raise
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to remove item from wishlist: {str(e)}"
        )


@router.put("/{user_id}/wishlists/{wishlist_id}/default")
async def set_default_wishlist(
    user_id: UUID,
    wishlist_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_auth_user)
):
    try:
        # Verify user has access to this user_id
        if str(current_user.id) != str(user_id) and current_user.role != "Admin":
            raise APIException(
                status_code=status.HTTP_403_FORBIDDEN,
                message="Access denied: Cannot modify other user's wishlists"
            )

        service = WishlistService(db)
        default_wishlist = await service.set_default_wishlist(user_id, wishlist_id)
        if not default_wishlist:
            raise APIException(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Wishlist not found"
            )

        # Serialize the wishlist properly
        wishlist_data = {
            "id": default_wishlist.id,
            "user_id": default_wishlist.user_id,
            "name": default_wishlist.name or "My Wishlist",
            "is_default": default_wishlist.is_default,
            "created_at": default_wishlist.created_at.isoformat() if default_wishlist.created_at else None,
            "updated_at": default_wishlist.updated_at.isoformat() if default_wishlist.updated_at else None,
            "items": []  # Simplified for this endpoint
        }

        return Response.success(data=WishlistResponse.model_validate(wishlist_data))
    except APIException:
        raise
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to set default wishlist: {str(e)}"
        )
