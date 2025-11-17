from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from typing import List, Optional
from uuid import UUID
from models.promocode import Promocode
from schemas.promocode import PromocodeCreate, PromocodeUpdate
from core.exceptions import APIException

class PromocodeService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_promocode(self, promocode_data: PromocodeCreate) -> Promocode:
        new_promocode = Promocode(
            **promocode_data.dict(exclude_unset=True)
        )
        self.db.add(new_promocode)
        await self.db.commit()
        await self.db.refresh(new_promocode)
        return new_promocode

    async def get_promocode_by_code(self, code: str) -> Optional[Promocode]:
        result = await self.db.execute(select(Promocode).where(Promocode.code == code, Promocode.is_active == True))
        return result.scalars().first()

    async def get_promocode_by_id(self, promocode_id: UUID) -> Optional[Promocode]:
        result = await self.db.execute(select(Promocode).where(Promocode.id == promocode_id))
        return result.scalars().first()

    async def get_all_promocodes(self) -> List[Promocode]:
        result = await self.db.execute(select(Promocode))
        return result.scalars().all()

    async def update_promocode(self, promocode_id: UUID, promocode_data: PromocodeUpdate) -> Optional[Promocode]:
        promocode = await self.get_promocode_by_id(promocode_id)
        if not promocode:
            raise APIException(status_code=404, detail="Promocode not found")
        
        for key, value in promocode_data.dict(exclude_unset=True).items():
            setattr(promocode, key, value)
        
        await self.db.commit()
        await self.db.refresh(promocode)
        return promocode

    async def delete_promocode(self, promocode_id: UUID) -> bool:
        promocode = await self.get_promocode_by_id(promocode_id)
        if not promocode:
            return False
        
        await self.db.delete(promocode)
        await self.db.commit()
        return True
