from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc, func
from typing import Optional, List
from models.blog import BlogPost
from schemas.blog import BlogPostCreate, BlogPostUpdate, BlogPostResponse
from core.exceptions import APIException
from uuid import uuid4, UUID
from datetime import datetime
from sqlalchemy.orm import selectinload

class BlogService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_blog_post(self, post_data: BlogPostCreate, author_id: UUID) -> BlogPost:
        new_post = BlogPost(
            id=uuid4(),
            author_id=author_id,
            title=post_data.title,
            content=post_data.content,
            tags=post_data.tags,
            image_url=post_data.image_url,
            is_published=post_data.is_published,
        )
        self.db.add(new_post)
        await self.db.commit()
        await self.db.refresh(new_post)
        return new_post

    async def get_blog_posts(self, page: int = 1, limit: int = 10, is_published: Optional[bool] = None, search: Optional[str] = None) -> dict:
        offset = (page - 1) * limit
        query = select(BlogPost).options(selectinload(BlogPost.author))
        total_query = select(func.count()).select_from(BlogPost)

        if is_published is not None:
            query = query.filter(BlogPost.is_published == is_published)
            total_query = total_query.filter(BlogPost.is_published == is_published)

        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                (BlogPost.title.ilike(search_pattern)) |
                (BlogPost.content.ilike(search_pattern))
            )
            total_query = total_query.filter(
                (BlogPost.title.ilike(search_pattern)) |
                (BlogPost.content.ilike(search_pattern))
            )

        query = query.order_by(desc(BlogPost.created_at))

        total_posts = (await self.db.execute(total_query)).scalar_one()
        posts = (await self.db.execute(query.offset(offset).limit(limit))).scalars().all()

        return {
            "total": total_posts,
            "page": page,
            "limit": limit,
            "data": [BlogPostResponse.from_orm(p) for p in posts]
        }

    async def get_blog_post_by_id(self, post_id: UUID) -> Optional[BlogPost]:
        result = await self.db.execute(select(BlogPost).filter(BlogPost.id == post_id))
        return result.scalars().first()

    async def update_blog_post(self, post_id: UUID, post_data: BlogPostUpdate, author_id: UUID) -> BlogPost:
        post = await self.get_blog_post_by_id(post_id)
        if not post:
            raise APIException(status_code=404, detail="Blog post not found")
        
        if post.author_id != author_id:
            raise APIException(status_code=403, detail="Not authorized to update this post")

        for key, value in post_data.dict(exclude_unset=True).items():
            setattr(post, key, value)
        post.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(post)
        return post

    async def delete_blog_post(self, post_id: UUID, author_id: UUID):
        post = await self.get_blog_post_by_id(post_id)
        if not post:
            raise APIException(status_code=404, detail="Blog post not found")
        
        if post.author_id != author_id:
            raise APIException(status_code=403, detail="Not authorized to delete this post")

        await self.db.delete(post)
        await self.db.commit()
