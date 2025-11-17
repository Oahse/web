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
        from_attributes = True  # For Pydantic v2
        # orm_mode = True # For Pydantic v1


class UserBase(BaseModel):
    email: EmailStr
    firstname: str
    lastname: str
    role: Optional[str] = "Customer"


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    firstname: Optional[str] = None
    lastname: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    country: Optional[str] = None
    language: Optional[str] = None
    timezone: Optional[str] = None
    active: Optional[bool] = None


class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    firstname: str
    lastname: str
    full_name: Optional[str] = None
    phone: Optional[str] = None
    role: str
    verified: bool
    active: bool
    age: Optional[int] = None
    gender: Optional[str] = None
    country: Optional[str] = None
    language: Optional[str] = None
    timezone: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
