from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, selectinload
from core.database import BaseModel, CHAR_LENGTH


class BlogPost(BaseModel):
    __tablename__ = "blog_posts"

    title = Column(String(CHAR_LENGTH), nullable=False)
    content = Column(Text, nullable=False)
    excerpt = Column(Text, nullable=True)
    author_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    tags = Column(JSON, nullable=True)  # ["organic", "farming", "health"]
    image_url = Column(String(500), nullable=True)
    is_published = Column(Boolean, default=False)
    published_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    author = relationship("User", back_populates="blog_posts")