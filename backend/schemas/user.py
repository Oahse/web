from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from uuid import UUID

class AddressBase(BaseModel):
    street: Optional[str]
    city: Optional[str]
    state: Optional[str]
    country: Optional[str]
    post_code: Optional[str]
    kind: str = "Shipping"

class AddressCreate(AddressBase):
    pass

class AddressUpdate(AddressBase):
    pass

class AddressResponse(AddressBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True # For Pydantic v2
        # orm_mode = True # For Pydantic v1

class UserBase(BaseModel):
    email: EmailStr
    firstname: str
    lastname: str
    role: Optional[str] = "Customer"

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    firstname: Optional[str]
    lastname: Optional[str]
    phone: Optional[str]
    active: Optional[bool]
