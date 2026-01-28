from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_
from typing import List, Optional, Dict, Any
from uuid import UUID
from core.utils.uuid_utils import uuid7
from models.shipping import ShippingMethod
from schemas.shipping import ShippingMethodCreate, ShippingMethodUpdate, ShippingMethodAvailability
from core.exceptions import APIException
import logging

logger = logging.getLogger(__name__)


class ShippingService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_shipping_method(self, shipping_method_data: ShippingMethodCreate) -> ShippingMethod:
        new_shipping_method = ShippingMethod(
            id=uuid7(),
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

    async def get_available_shipping_methods(
        self, 
        country_code: str, 
        order_amount: float = 0.0, 
        total_weight_kg: float = 1.0
    ) -> List[ShippingMethodAvailability]:
        """
        Get shipping methods available for a specific country with calculated pricing
        
        Args:
            country_code: ISO 3166-1 alpha-2 country code (e.g., "US", "CA")
            order_amount: Total order amount for minimum order validation
            total_weight_kg: Total weight for weight-based pricing
        
        Returns:
            List of available shipping methods with calculated prices
        """
        logger.info(f"Getting available shipping methods for {country_code}, amount: ${order_amount}, weight: {total_weight_kg}kg")
        
        # Get all active shipping methods
        result = await self.db.execute(select(ShippingMethod).where(ShippingMethod.is_active == True))
        all_methods = result.scalars().all()
        
        available_methods = []
        
        for method in all_methods:
            availability = await self._check_method_availability(
                method, country_code, order_amount, total_weight_kg
            )
            available_methods.append(availability)
        
        # Sort by price (cheapest first)
        available_methods.sort(key=lambda x: x.calculated_price)
        
        logger.info(f"Found {len([m for m in available_methods if m.available])} available methods out of {len(all_methods)} total")
        return available_methods

    async def _check_method_availability(
        self, 
        method: ShippingMethod, 
        country_code: str, 
        order_amount: float, 
        total_weight_kg: float
    ) -> ShippingMethodAvailability:
        """Check if a shipping method is available for the given parameters"""
        
        # Check country restrictions
        if method.restricted_countries and country_code.upper() in method.restricted_countries:
            return ShippingMethodAvailability(
                method=method,
                available=False,
                reason=f"Not available in {country_code}",
                calculated_price=method.price
            )
        
        # Check country availability (if specified)
        if method.available_countries and country_code.upper() not in method.available_countries:
            return ShippingMethodAvailability(
                method=method,
                available=False,
                reason=f"Only available in: {', '.join(method.available_countries)}",
                calculated_price=method.price
            )
        
        # Check minimum order amount
        if method.min_order_amount and order_amount < method.min_order_amount:
            return ShippingMethodAvailability(
                method=method,
                available=False,
                reason=f"Minimum order amount: ${method.min_order_amount:.2f}",
                calculated_price=method.price
            )
        
        # Check maximum weight
        if method.max_weight_kg and total_weight_kg > method.max_weight_kg:
            return ShippingMethodAvailability(
                method=method,
                available=False,
                reason=f"Maximum weight: {method.max_weight_kg}kg",
                calculated_price=method.price
            )
        
        # Calculate final price including weight-based pricing
        calculated_price = await self._calculate_shipping_price(method, total_weight_kg)
        
        return ShippingMethodAvailability(
            method=method,
            available=True,
            reason=None,
            calculated_price=calculated_price
        )

    async def _calculate_shipping_price(self, method: ShippingMethod, total_weight_kg: float) -> float:
        """Calculate shipping price including weight-based pricing"""
        base_price = method.price
        
        # If no weight-based pricing, return base price
        if not method.price_per_kg or not method.base_weight_kg:
            return base_price
        
        # Calculate additional weight charges
        if total_weight_kg > method.base_weight_kg:
            additional_weight = total_weight_kg - method.base_weight_kg
            additional_cost = additional_weight * method.price_per_kg
            return base_price + additional_cost
        
        return base_price

    async def calculate_shipping_cost(
        self, 
        cart_subtotal: float, 
        address: dict, 
        shipping_method_id: Optional[UUID] = None,
        total_weight_kg: float = 1.0
    ) -> float:
        """
        Calculate shipping cost based on cart subtotal, address, selected method, and weight.
        Uses database shipping methods with country-specific availability.
        """
        country_code = address.get('country', 'US').upper()
        
        if shipping_method_id:
            method = await self.get_shipping_method_by_id(shipping_method_id)
            if method and method.is_active:
                # Check if method is available for this country
                availability = await self._check_method_availability(
                    method, country_code, cart_subtotal, total_weight_kg
                )
                if availability.available:
                    return availability.calculated_price
                else:
                    logger.warning(f"Shipping method {method.name} not available for {country_code}: {availability.reason}")

        # If no specific method or method not available, get cheapest available method
        available_methods = await self.get_available_shipping_methods(
            country_code, cart_subtotal, total_weight_kg
        )
        
        # Find cheapest available method
        available_only = [m for m in available_methods if m.available]
        if available_only:
            cheapest = min(available_only, key=lambda m: m.calculated_price)
            logger.info(f"Using cheapest available method: {cheapest.method.name} - ${cheapest.calculated_price}")
            return cheapest.calculated_price
        
        # No shipping methods available for this location
        logger.warning(f"No shipping methods available for {country_code}")
        return 0.0

    async def update_shipping_method(self, shipping_method_id: UUID, shipping_method_data: ShippingMethodUpdate) -> Optional[ShippingMethod]:
        shipping_method = await self.get_shipping_method_by_id(shipping_method_id)
        if not shipping_method:
            raise APIException(
                status_code=404, message="Shipping method not found")

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
