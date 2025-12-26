from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from uuid import UUID
from core.database import get_db
from core.utils.response import Response
from core.exceptions import APIException
from schemas.blog import (
    BlogPostCreate, BlogPostUpdate, BlogPostResponse,
    BlogCategoryCreate, BlogCategoryUpdate, BlogCategoryResponse,
    BlogTagCreate, BlogTagUpdate, BlogTagResponse,
    CommentCreate, CommentUpdate, CommentResponse
)
from services.blog import BlogService
from models.user import User
from services.auth import AuthService

from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


async def get_current_auth_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> User:
    return await AuthService.get_current_user(token, db)

def require_admin(current_user: User = Depends(get_current_auth_user)):
    """Require admin role."""
    if current_user.role.lower() not in ["admin", "superadmin"]:
        raise APIException(
            status_code=status.HTTP_403_FORBIDDEN,
            message="Admin access required"
        )
    return current_user

router = APIRouter(prefix="/blog", tags=["Blog"])


# --- Blog Posts ---

@router.post("/posts")
async def create_blog_post(
    post_data: BlogPostCreate,
    current_user: User = Depends(get_current_auth_user), # Any authenticated user can create posts (then approved by admin)
    db: AsyncSession = Depends(get_db)
):
    """Create a new blog post."""
    try:
        blog_service = BlogService(db)
        post = await blog_service.create_blog_post(post_data, current_user.id)
        return Response.success(data=post, message="Blog post created successfully", status_code=status.HTTP_201_CREATED)
    except APIException:
        raise
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to create blog post: {str(e)}"
        )


@router.get("/posts")
async def get_blog_posts(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    is_published: Optional[bool] = Query(True), # Default to only published posts for public view
    search: Optional[str] = Query(None),
    category_slug: Optional[str] = Query(None),
    tag_slug: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_auth_user) # Allow unauthenticated access, but check for admin role
):
    """Get all blog posts (can filter by published status, search, category, tag).
    Admins can view unpublished posts.
    """
    try:
        blog_service = BlogService(db)
        if current_user and current_user.role.lower() in ["admin", "superadmin"]:
            # Admins can view all posts, so we respect the is_published filter
            posts_data = await blog_service.get_blog_posts(page, limit, is_published, search, category_slug, tag_slug)
        else:
            # Non-admins can only view published posts
            posts_data = await blog_service.get_blog_posts(page, limit, True, search, category_slug, tag_slug)

        return Response.success(data=posts_data)
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to fetch blog posts: {str(e)}"
        )


@router.get("/posts/{post_slug}")
async def get_blog_post(
    post_slug: str,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_auth_user)
):
    """Get a specific blog post by slug."""
    try:
        blog_service = BlogService(db)
        post = await blog_service.get_blog_post_by_slug(post_slug)
        if not post:
            raise APIException(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Blog post not found"
            )
        
        # Only allow viewing unpublished posts if user is admin or author
        if not post.is_published and (not current_user or (str(post.author_id) != str(current_user.id) and current_user.role.lower() not in ["admin", "superadmin"])):
             raise APIException(
                status_code=status.HTTP_404_NOT_FOUND, # Return 404 to avoid leaking existence of unpublished posts
                message="Blog post not found"
            )

        return Response.success(data=post)
    except APIException:
        raise
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to fetch blog post: {str(e)}"
        )


@router.put("/posts/{post_id}")
async def update_blog_post(
    post_id: UUID,
    post_data: BlogPostUpdate,
    current_user: User = Depends(get_current_auth_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a blog post (author or admin only)."""
    try:
        blog_service = BlogService(db)
        # The service layer will handle authorization logic
        post = await blog_service.update_blog_post(post_id, post_data, current_user.id)
        return Response.success(data=post, message="Blog post updated successfully")
    except APIException:
        raise
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to update blog post: {str(e)}"
        )


@router.delete("/posts/{post_id}")
async def delete_blog_post(
    post_id: UUID,
    current_user: User = Depends(get_current_auth_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a blog post (author or admin only)."""
    try:
        blog_service = BlogService(db)
        is_admin = current_user.role.lower() in ["admin", "superadmin"]
        await blog_service.delete_blog_post(post_id, current_user.id, is_admin)
        return Response.success(message="Blog post deleted successfully")
    except APIException:
        raise
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to delete blog post: {str(e)}"
        )

# --- Blog Categories ---

@router.post("/categories")
async def create_blog_category(
    category_data: BlogCategoryCreate,
    current_user: User = Depends(require_admin), # Admin only
    db: AsyncSession = Depends(get_db)
):
    """Create a new blog category (admin only)."""
    try:
        blog_service = BlogService(db)
        category = await blog_service.create_blog_category(category_data)
        return Response.success(data=category, message="Blog category created successfully", status_code=status.HTTP_201_CREATED)
    except APIException:
        raise
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to create blog category: {str(e)}"
        )

@router.get("/categories")
async def get_blog_categories(db: AsyncSession = Depends(get_db)):
    """Get all blog categories."""
    try:
        blog_service = BlogService(db)
        categories = await blog_service.get_blog_categories()
        return Response.success(data=categories)
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to fetch blog categories: {str(e)}"
        )

@router.get("/categories/{category_slug}")
async def get_blog_category(category_slug: str, db: AsyncSession = Depends(get_db)):
    """Get a specific blog category by slug."""
    try:
        blog_service = BlogService(db)
        category = await blog_service.get_blog_category_by_slug(category_slug)
        if not category:
            raise APIException(status_code=status.HTTP_404_NOT_FOUND, message="Blog category not found")
        return Response.success(data=category)
    except APIException:
        raise
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to fetch blog category: {str(e)}"
        )

@router.put("/categories/{category_id}")
async def update_blog_category(
    category_id: UUID,
    category_data: BlogCategoryUpdate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Update a blog category (admin only)."""
    try:
        blog_service = BlogService(db)
        category = await blog_service.update_blog_category(category_id, category_data)
        return Response.success(data=category, message="Blog category updated successfully")
    except APIException:
        raise
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to update blog category: {str(e)}"
        )

@router.delete("/categories/{category_id}")
async def delete_blog_category(
    category_id: UUID,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Delete a blog category (admin only)."""
    try:
        blog_service = BlogService(db)
        await blog_service.delete_blog_category(category_id)
        return Response.success(message="Blog category deleted successfully")
    except APIException:
        raise
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to delete blog category: {str(e)}"
        )

# --- Blog Tags ---

@router.post("/tags")
async def create_blog_tag(
    tag_data: BlogTagCreate,
    current_user: User = Depends(require_admin), # Admin only
    db: AsyncSession = Depends(get_db)
):
    """Create a new blog tag (admin only)."""
    try:
        blog_service = BlogService(db)
        tag = await blog_service.create_blog_tag(tag_data)
        return Response.success(data=tag, message="Blog tag created successfully", status_code=status.HTTP_201_CREATED)
    except APIException:
        raise
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to create blog tag: {str(e)}"
        )

@router.get("/tags")
async def get_blog_tags(db: AsyncSession = Depends(get_db)):
    """Get all blog tags."""
    try:
        blog_service = BlogService(db)
        tags = await blog_service.get_blog_tags()
        return Response.success(data=tags)
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to fetch blog tags: {str(e)}"
        )

@router.get("/tags/{tag_slug}")
async def get_blog_tag(tag_slug: str, db: AsyncSession = Depends(get_db)):
    """Get a specific blog tag by slug."""
    try:
        blog_service = BlogService(db)
        tag = await blog_service.get_blog_tag_by_slug(tag_slug)
        if not tag:
            raise APIException(status_code=status.HTTP_404_NOT_FOUND, message="Blog tag not found")
        return Response.success(data=tag)
    except APIException:
        raise
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to fetch blog tag: {str(e)}"
        )

@router.put("/tags/{tag_id}")
async def update_blog_tag(
    tag_id: UUID,
    tag_data: BlogTagUpdate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Update a blog tag (admin only)."""
    try:
        blog_service = BlogService(db)
        tag = await blog_service.update_blog_tag(tag_id, tag_data)
        return Response.success(data=tag, message="Blog tag updated successfully")
    except APIException:
        raise
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to update blog tag: {str(e)}"
        )

@router.delete("/tags/{tag_id}")
async def delete_blog_tag(
    tag_id: UUID,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Delete a blog tag (admin only)."""
    try:
        blog_service = BlogService(db)
        await blog_service.delete_blog_tag(tag_id)
        return Response.success(message="Blog tag deleted successfully")
    except APIException:
        raise
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to delete blog tag: {str(e)}"
        )

# --- Comments ---

@router.post("/posts/{post_id}/comments")
async def create_comment(
    post_id: UUID,
    comment_data: CommentCreate,
    current_user: User = Depends(get_current_auth_user),
    db: AsyncSession = Depends(get_db)
):
    """Add a comment to a blog post."""
    try:
        # Ensure the comment_data matches the target post_id
        if comment_data.blog_post_id != post_id:
            raise APIException(status_code=status.HTTP_400_BAD_REQUEST, message="Mismatched post_id in path and body")

        blog_service = BlogService(db)
        comment = await blog_service.create_comment(comment_data, current_user.id)
        return Response.success(data=comment, message="Comment added successfully", status_code=status.HTTP_201_CREATED)
    except APIException:
        raise
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to add comment: {str(e)}"
        )

@router.get("/posts/{post_id}/comments")
async def get_comments_for_post(
    post_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get all comments for a specific blog post."""
    try:
        blog_service = BlogService(db)
        comments = await blog_service.get_comments_for_post(post_id)
        return Response.success(data=comments)
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to fetch comments: {str(e)}"
        )

@router.put("/comments/{comment_id}")
async def update_comment(
    comment_id: UUID,
    comment_data: CommentUpdate,
    current_user: User = Depends(get_current_auth_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a comment (author or admin only)."""
    try:
        blog_service = BlogService(db)
        is_admin = current_user.role.lower() in ["admin", "superadmin"]
        comment = await blog_service.update_comment(comment_id, comment_data, current_user.id, is_admin)
        return Response.success(data=comment, message="Comment updated successfully")
    except APIException:
        raise
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to update comment: {str(e)}"
        )

@router.delete("/comments/{comment_id}")
async def delete_comment(
    comment_id: UUID,
    current_user: User = Depends(get_current_auth_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a comment (author or admin only)."""
    try:
        blog_service = BlogService(db)
        is_admin = current_user.role.lower() in ["admin", "superadmin"]
        await blog_service.delete_comment(comment_id, current_user.id, is_admin)
        return Response.success(message="Comment deleted successfully")
    except APIException:
        raise
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to delete comment: {str(e)}"
        )