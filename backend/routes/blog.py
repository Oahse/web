from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from uuid import UUID
from core.database import get_db
from core.utils.response import Response
from core.exceptions import APIException
from schemas.blog import BlogPostCreate, BlogPostUpdate
from services.blog import BlogService
from models.user import User
from services.auth import AuthService

from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_auth_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> User:
    return await AuthService.get_current_user(token, db)

router = APIRouter(prefix="/api/v1/blog", tags=["Blog"])

@router.post("/")
async def create_blog_post(
    post_data: BlogPostCreate,
    current_user: User = Depends(get_current_auth_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new blog post (admin only)."""
    try:
        if current_user.role not in ["Admin", "SuperAdmin"]:
            raise APIException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        blog_service = BlogService(db)
        post = await blog_service.create_blog_post(post_data, current_user.id)
        return Response(success=True, data=post, message="Blog post created successfully")
    except APIException:
        raise
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create blog post: {str(e)}"
        )

@router.get("/")
async def get_blog_posts(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    is_published: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Get all blog posts."""
    try:
        blog_service = BlogService(db)
        posts = await blog_service.get_blog_posts(page, limit, is_published, search)
        return Response(success=True, data=posts)
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch blog posts: {str(e)}"
        )

@router.get("/{post_id}")
async def get_blog_post(
    post_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific blog post by ID."""
    try:
        blog_service = BlogService(db)
        post = await blog_service.get_blog_post_by_id(post_id)
        if not post:
            raise APIException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Blog post not found"
            )
        return Response(success=True, data=post)
    except APIException:
        raise
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch blog post: {str(e)}"
        )

@router.put("/{post_id}")
async def update_blog_post(
    post_id: UUID,
    post_data: BlogPostUpdate,
    current_user: User = Depends(get_current_auth_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a blog post (admin only)."""
    try:
        if current_user.role not in ["Admin", "SuperAdmin"]:
            raise APIException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        blog_service = BlogService(db)
        post = await blog_service.update_blog_post(post_id, post_data, current_user.id)
        return Response(success=True, data=post, message="Blog post updated successfully")
    except APIException:
        raise
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update blog post: {str(e)}"
        )

@router.delete("/{post_id}")
async def delete_blog_post(
    post_id: UUID,
    current_user: User = Depends(get_current_auth_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a blog post (admin only)."""
    try:
        if current_user.role not in ["Admin", "SuperAdmin"]:
            raise APIException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        blog_service = BlogService(db)
        await blog_service.delete_blog_post(post_id, current_user.id)
        return Response(success=True, message="Blog post deleted successfully")
    except APIException:
        raise
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete blog post: {str(e)}"
        )
