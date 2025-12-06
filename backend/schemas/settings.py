from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field


class SystemSettingBase(BaseModel):
    key: str
    value: str
    value_type: str
    description: Optional[str] = None


class SystemSettingCreate(SystemSettingBase):
    pass


class SystemSettingUpdate(BaseModel):
    id: UUID
    key: Optional[str] = None
    value: Optional[str] = None
    value_type: Optional[str] = None
    description: Optional[str] = None


class SystemSettingResponse(SystemSettingBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
