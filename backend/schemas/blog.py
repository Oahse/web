from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class BlogAuthor(BaseModel):
    id: str
    firstname: str
    lastname: str

    class Config:
        from_attributes = True

class BlogPostResponse(BaseModel):
    id: str
    title: str
    content: str
    author: BlogAuthor
    tags: Optional[List[str]] = []
    image_url: Optional[str] = None
    is_published: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class BlogPostBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1)
    author_id: Optional[str] = None
    tags: Optional[List[str]] = []
    image_url: Optional[str] = None
    is_published: bool = True

class BlogPostCreate(BlogPostBase):
    pass

class BlogPostUpdate(BlogPostBase):
    title: Optional[str] = None
    content: Optional[str] = None
    is_published: Optional[bool] = None

class BlogPostInDB(BlogPostBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True