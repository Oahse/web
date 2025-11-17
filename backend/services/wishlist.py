from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload
from uuid import UUID
from typing import List, Optional

from models.wishlist import Wishlist, WishlistItem
from models.product import Product, ProductVariant # Import Product and ProductVariant
from schemas.wishlist import WishlistCreate, WishlistUpdate, WishlistItemCreate

class WishlistService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_wishlists(self, user_id: UUID) -> List[Wishlist]:
        try:
            query = select(Wishlist).where(Wishlist.user_id == user_id).options(
                selectinload(Wishlist.items).selectinload(WishlistItem.product).selectinload(Product.variants).selectinload(ProductVariant.images),
                selectinload(Wishlist.items).selectinload(WishlistItem.variant).selectinload(ProductVariant.images)
            )
            result = await self.db.execute(query)
            return result.scalars().all()
        except Exception as e:
            print(f"Error in get_wishlists: {e}")
            # Return empty list if there's an error
            return []

    async def get_wishlist_by_id(self, wishlist_id: UUID, user_id: UUID) -> Optional[Wishlist]:
        query = select(Wishlist).where(Wishlist.id == wishlist_id, Wishlist.user_id == user_id).options(
            selectinload(Wishlist.items).selectinload(WishlistItem.product).selectinload(Product.variants).selectinload(ProductVariant.images),
            selectinload(Wishlist.items).selectinload(WishlistItem.variant).selectinload(ProductVariant.images)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create_wishlist(self, user_id: UUID, payload: WishlistCreate) -> Wishlist:
        # Ensure only one default wishlist per user
        if payload.is_default:
            await self._clear_default_wishlist(user_id)

        new_wishlist = Wishlist(
            user_id=user_id,
            name=payload.name,
            is_default=payload.is_default
        )
        self.db.add(new_wishlist)
        await self.db.commit()
        await self.db.refresh(new_wishlist)

        # Re-fetch the wishlist with items eagerly loaded
        refetched_wishlist = await self.get_wishlist_by_id(new_wishlist.id, user_id)
        if not refetched_wishlist:
            # This should ideally not happen if creation was successful
            raise Exception("Failed to retrieve newly created wishlist with items.")

        return refetched_wishlist

    async def update_wishlist(self, wishlist_id: UUID, user_id: UUID, payload: WishlistUpdate) -> Optional[Wishlist]:
        query = select(Wishlist).where(Wishlist.id == wishlist_id, Wishlist.user_id == user_id)
        result = await self.db.execute(query)
        wishlist = result.scalar_one_or_none()

        if not wishlist:
            return None

        if payload.is_default is True:
            await self._clear_default_wishlist(user_id, exclude_wishlist_id=wishlist_id)
        elif payload.is_default is False and wishlist.is_default:
            # More complex logic might be needed here if unsetting default
            pass

        for field, value in payload.dict(exclude_unset=True).items():
            setattr(wishlist, field, value)

        await self.db.commit()
        await self.db.refresh(wishlist)
        return wishlist

    async def delete_wishlist(self, wishlist_id: UUID, user_id: UUID) -> bool:
        query = select(Wishlist).where(Wishlist.id == wishlist_id, Wishlist.user_id == user_id)
        result = await self.db.execute(query)
        wishlist = result.scalar_one_or_none()

        if not wishlist:
            return False

        await self.db.delete(wishlist)
        await self.db.commit()
        return True

    async def add_item_to_wishlist(self, wishlist_id: UUID, payload: WishlistItemCreate) -> WishlistItem:
        new_item = WishlistItem(
            wishlist_id=wishlist_id,
            product_id=payload.product_id,
            variant_id=payload.variant_id,
            quantity=payload.quantity
        )
        self.db.add(new_item)
        await self.db.commit()
        await self.db.refresh(new_item)

        # Re-fetch the wishlist item with product and variant eagerly loaded
        query = select(WishlistItem).where(WishlistItem.id == new_item.id).options(
            selectinload(WishlistItem.product),
            selectinload(WishlistItem.variant).selectinload(ProductVariant.images)
        )
        refetched_item = await self.db.execute(query)
        refetched_item = refetched_item.scalar_one_or_none()

        if not refetched_item:
            raise Exception("Failed to retrieve newly created wishlist item with relationships.")

        return refetched_item

    async def remove_item_from_wishlist(self, wishlist_id: UUID, item_id: UUID) -> bool:
        query = select(WishlistItem).where(WishlistItem.id == item_id, WishlistItem.wishlist_id == wishlist_id)
        result = await self.db.execute(query)
        item = result.scalar_one_or_none()

        if not item:
            return False

        await self.db.delete(item)
        await self.db.commit()
        return True

    async def set_default_wishlist(self, user_id: UUID, wishlist_id: UUID) -> Optional[Wishlist]:
        await self._clear_default_wishlist(user_id)

        query = update(Wishlist).where(Wishlist.id == wishlist_id, Wishlist.user_id == user_id).values(is_default=True)
        await self.db.execute(query)
        await self.db.commit()

        query = select(Wishlist).where(Wishlist.id == wishlist_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def _clear_default_wishlist(self, user_id: UUID, exclude_wishlist_id: Optional[UUID] = None):
        query = update(Wishlist).where(
            Wishlist.user_id == user_id,
            Wishlist.is_default == True
        ).values(is_default=False)
        if exclude_wishlist_id:
            query = query.where(Wishlist.id != exclude_wishlist_id)
        await self.db.execute(query)
        await self.db.commit()