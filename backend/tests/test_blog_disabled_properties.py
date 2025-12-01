"""
Property-based tests for blog feature being disabled.

**Feature: app-enhancements, Property 47: Blog routes return 404**
**Validates: Requirements 14.2**
"""

import pytest
from hypothesis import given, strategies as st
from httpx import AsyncClient
from main import app


@pytest.mark.asyncio
@given(
    blog_path=st.sampled_from([
        "/api/blog",
        "/api/blog/posts",
        "/api/blog/123",
        "/api/blog/test-post",
        "/api/blog/category/tech",
    ])
)
async def test_property_blog_routes_return_404(blog_path: str):
    """
    Property 47: Blog routes return 404
    
    For any attempt to access blog routes, the system should return a 404 error.
    
    **Validates: Requirements 14.2**
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(blog_path)
        
        # Blog routes should return 404
        assert response.status_code == 404, (
            f"Blog route {blog_path} should return 404, got {response.status_code}"
        )


@pytest.mark.asyncio
async def test_blog_routes_not_accessible():
    """
    Test that common blog routes are not accessible.
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        blog_routes = [
            "/api/blog",
            "/api/blog/posts",
            "/api/blog/1",
            "/api/blog/test-slug",
        ]
        
        for route in blog_routes:
            response = await client.get(route)
            assert response.status_code == 404, (
                f"Blog route {route} should return 404, got {response.status_code}"
            )
