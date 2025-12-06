from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from core.database import BaseModel, CHAR_LENGTH, GUID


class BlogCategory(BaseModel):
    __tablename__ = "blog_categories"
    __table_args__ = {'extend_existing': True}

    name = Column(String(CHAR_LENGTH), unique=True, nullable=False)
    slug = Column(String(CHAR_LENGTH), unique=True, nullable=False)
    description = Column(Text, nullable=True)

    posts = relationship("models.blog.BlogPost", back_populates="category")


class BlogTag(BaseModel):
    __tablename__ = "blog_tags"
    __table_args__ = {'extend_existing': True}

    name = Column(String(CHAR_LENGTH), unique=True, nullable=False)
    slug = Column(String(CHAR_LENGTH), unique=True, nullable=False)


class BlogPost(BaseModel):
    __tablename__ = "blog_posts"
    __table_args__ = {'extend_existing': True}

    title = Column(String(CHAR_LENGTH), nullable=False)
    slug = Column(String(CHAR_LENGTH), unique=True, nullable=False) # Add slug for SEO-friendly URLs
    content = Column(Text, nullable=False)
    excerpt = Column(Text, nullable=True)
    author_id = Column(GUID(), ForeignKey("users.id"), nullable=False)
    category_id = Column(GUID(), ForeignKey("blog_categories.id"), nullable=True) # Link to BlogCategory
    image_url = Column(String(500), nullable=True)
    is_published = Column(Boolean, default=False)
    published_at = Column(DateTime(timezone=True), nullable=True)
    seo_title = Column(String(CHAR_LENGTH), nullable=True) # Add SEO fields
    seo_description = Column(Text, nullable=True)
    seo_keywords = Column(Text, nullable=True) # Store as comma-separated string or JSON list if needed

    # Relationships
    author = relationship("models.user.User", back_populates="blog_posts")
    category = relationship("models.blog.BlogCategory", back_populates="posts")
    tags = relationship("models.blog.BlogPostTag", back_populates="blog_post", cascade="all, delete-orphan") # Link to BlogPostTag for many-to-many
    comments = relationship("models.blog.Comment", back_populates="blog_post", cascade="all, delete-orphan") # Link to Comment


class BlogPostTag(BaseModel):
    """Association table for BlogPost and BlogTag Many-to-Many relationship."""
    __tablename__ = "blog_post_tags"
    __table_args__ = {'extend_existing': True}

    blog_post_id = Column(GUID(), ForeignKey("blog_posts.id"), primary_key=True)
    blog_tag_id = Column(GUID(), ForeignKey("blog_tags.id"), primary_key=True)

    blog_post = relationship("models.blog.BlogPost", back_populates="tags")
    blog_tag = relationship("models.blog.BlogTag")


class Comment(BaseModel):
    __tablename__ = "comments"
    __table_args__ = {'extend_existing': True}

    content = Column(Text, nullable=False)
    author_id = Column(GUID(), ForeignKey("users.id"), nullable=False)
    blog_post_id = Column(GUID(), ForeignKey("blog_posts.id"), nullable=False)
    parent_id = Column(GUID(), ForeignKey("comments.id"), nullable=True) # For nested comments
    is_approved = Column(Boolean, default=False)

    # Relationships
    author = relationship("models.user.User", back_populates="comments") # Need to add comments relationship to User model
    blog_post = relationship("models.blog.BlogPost", back_populates="comments")
    parent = relationship("models.blog.Comment", remote_side='models.blog.Comment.id')
    replies = relationship("models.blog.Comment", back_populates="parent")