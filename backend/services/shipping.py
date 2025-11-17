from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from typing import List, Optional
from uuid import UUID
from models.shipping import ShippingMethod
from schemas.shipping import ShippingMethodCreate, ShippingMethodUpdate
from core.exceptions import APIException

class ShippingService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_shipping_method(self, shipping_method_data: ShippingMethodCreate) -> ShippingMethod:
        new_shipping_method = ShippingMethod(
            **shipping_method_data.dict(exclude_unset=True)
        )
        self.db.add(new_shipping_method)
        await self.db.commit()
        await self.db.refresh(new_shipping_method)
        return new_shipping_method

    async def get_shipping_method_by_id(self, shipping_method_id: UUID) -> Optional[ShippingMethod]:
        result = await self.db.execute(select(ShippingMethod).where(ShippingMethod.id == shipping_method_id))
        return result.scalars().first()

    async def get_all_active_shipping_methods(self) -> List[ShippingMethod]:
        result = await self.db.execute(select(ShippingMethod).where(ShippingMethod.is_active == True))
        return result.scalars().all()

    async def update_shipping_method(self, shipping_method_id: UUID, shipping_method_data: ShippingMethodUpdate) -> Optional[ShippingMethod]:
        shipping_method = await self.get_shipping_method_by_id(shipping_method_id)
        if not shipping_method:
            raise APIException(status_code=404, detail="Shipping method not found")
        
        for key, value in shipping_method_data.dict(exclude_unset=True).items():
            setattr(shipping_method, key, value)
        
        await self.db.commit()
        await self.db.refresh(shipping_method)
        return shipping_method

    async def delete_shipping_method(self, shipping_method_id: UUID) -> bool:
        shipping_method = await self.get_shipping_method_by_id(shipping_method_id)
        if not shipping_method:
            return False
        
        await self.db.delete(shipping_method)
        await self.db.commit()
        return True

    async def calculate_shipping_cost(self, cart_subtotal: float, address: dict, shipping_method_id: Optional[UUID] = None) -> float:
        """Calculates shipping cost based on cart subtotal, address, and selected method.
        For demonstration, this is simplified. In a real app, this would involve complex logic
        and potentially external API calls.
        """
        if shipping_method_id:
            method = await self.get_shipping_method_by_id(shipping_method_id)
            if method and method.is_active:
                return method.price
        
        # Default logic if no specific method is chosen or found
        if cart_subtotal >= 50:
            return 0.0  # Free shipping for orders over $50
        return 5.99 # Standard shipping cost
