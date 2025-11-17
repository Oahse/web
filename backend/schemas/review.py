from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ReviewUser(BaseModel):
    id: str
    firstname: str
    lastname: str

    class Config:
        from_attributes = True


class ReviewResponse(BaseModel):
    id: str
    rating: int
    comment: Optional[str]
    created_at: datetime
    user: ReviewUser

    class Config:
        from_attributes = True


class ReviewBase(BaseModel):
    product_id: str
    user_id: Optional[str] = None  # Will be set by the backend
    # based on current user
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = Field(None, max_length=1000)


class ReviewCreate(ReviewBase):
    pass


class ReviewUpdate(ReviewBase):
    rating: Optional[int] = Field(None, ge=1, le=5)
    comment: Optional[str] = Field(None, max_length=1000)


class ReviewInDB(ReviewBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
