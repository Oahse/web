"""
Tests for product creation API endpoint

These tests verify:
- Product creation with variants and images
- SKU auto-generation
- Image URL persistence
- Validation of required fields
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4

from models.product import Product, ProductVariant, ProductImage, Category
from models.user import User


@pytest.mark.asyncio
async def test_create_product_with_variants_and_images(
    async_client: AsyncClient,
    db_session: AsyncSession,
    auth_headers: dict
):
    """Test creating a product with variants and images"""
    
    # Create a test category first
    category = Category(
        id=uuid4(),
        name="Test Category",
        description="Test category for products",
        is_active=True
    )
    db_session.add(category)
    await db_session.commit()
    
    # Product data with variants and images
    product_data = {
        "name": "Test Product",
        "description": "A test product with variants",
        "category_id": str(category.id),
        "variants": [
            {
                "name": "Small",
                "base_price": 10.99,
                "sale_price": 8.99,
                "stock": 100,
                "attributes": {"size": "S", "color": "red"},
                "image_urls": [
                    "https://cdn.jsdelivr.net/gh/owner/repo@main/products/image1.jpg",
                    "https://cdn.jsdelivr.net/gh/owner/repo@main/products/image2.jpg"
                ]
            },
            {
                "name": "Large",
                "base_price": 15.99,
                "stock": 50,
                "attributes": {"size": "L", "color": "blue"},
                "image_urls": [
                    "https://cdn.jsdelivr.net/gh/owner/repo@main/products/image3.jpg"
                ]
            }
        ]
    }
    
    # Create product
    response = await async_client.post(
        "/api/v1/products",
        json=product_data,
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify response structure
    assert data["success"] is True
    assert "data" in data
    product = data["data"]
    
    # Verify product data
    assert product["name"] == "Test Product"
    assert product["description"] == "A test product with variants"
    assert len(product["variants"]) == 2
    
    # Verify first variant
    variant1 = product["variants"][0]
    assert variant1["name"] == "Small"
    assert variant1["base_price"] == 10.99
    assert variant1["sale_price"] == 8.99
    assert variant1["stock"] == 100
    assert variant1["sku"]  # SKU should be auto-generated
    assert len(variant1["images"]) == 2
    assert variant1["images"][0]["is_primary"] is True  # First image is primary
    
    # Verify second variant
    variant2 = product["variants"][1]
    assert variant2["name"] == "Large"
    assert variant2["base_price"] == 15.99
    assert variant2["stock"] == 50
    assert variant2["sku"]  # SKU should be auto-generated
    assert len(variant2["images"]) == 1
    
    # Verify SKUs are unique
    assert variant1["sku"] != variant2["sku"]
    
    # Verify SKU format: PREFIX-{product_id[:8]}-{index}
    assert "-" in variant1["sku"]
    assert "-" in variant2["sku"]


@pytest.mark.asyncio
async def test_sku_auto_generation(
    async_client: AsyncClient,
    db_session: AsyncSession,
    auth_headers: dict
):
    """Test that SKUs are auto-generated correctly"""
    
    # Create a test category
    category = Category(
        id=uuid4(),
        name="Electronics",
        is_active=True
    )
    db_session.add(category)
    await db_session.commit()
    
    product_data = {
        "name": "Laptop",
        "description": "Test laptop",
        "category_id": str(category.id),
        "variants": [
            {"name": "16GB RAM", "base_price": 999.99, "stock": 10},
            {"name": "32GB RAM", "base_price": 1299.99, "stock": 5}
        ]
    }
    
    response = await async_client.post(
        "/api/v1/products",
        json=product_data,
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()["data"]
    
    # Verify SKUs are generated
    variant1_sku = data["variants"][0]["sku"]
    variant2_sku = data["variants"][1]["sku"]
    
    assert variant1_sku
    assert variant2_sku
    assert variant1_sku != variant2_sku
    
    # Verify SKU format starts with product name prefix
    assert variant1_sku.startswith("LAP-")  # First 3 chars of "Laptop"
    assert variant2_sku.startswith("LAP-")


@pytest.mark.asyncio
async def test_image_url_persistence(
    async_client: AsyncClient,
    db_session: AsyncSession,
    auth_headers: dict
):
    """Test that image URLs are persisted correctly"""
    
    # Create a test category
    category = Category(
        id=uuid4(),
        name="Clothing",
        is_active=True
    )
    db_session.add(category)
    await db_session.commit()
    
    cdn_urls = [
        "https://cdn.jsdelivr.net/gh/owner/repo@main/clothing/shirt1.jpg",
        "https://cdn.jsdelivr.net/gh/owner/repo@main/clothing/shirt2.jpg",
        "https://cdn.jsdelivr.net/gh/owner/repo@main/clothing/shirt3.jpg"
    ]
    
    product_data = {
        "name": "T-Shirt",
        "description": "Cotton t-shirt",
        "category_id": str(category.id),
        "variants": [
            {
                "name": "Medium",
                "base_price": 19.99,
                "stock": 50,
                "image_urls": cdn_urls
            }
        ]
    }
    
    # Create product
    response = await async_client.post(
        "/api/v1/products",
        json=product_data,
        headers=auth_headers
    )
    
    assert response.status_code == 200
    product_id = response.json()["data"]["id"]
    
    # Fetch product again to verify persistence
    get_response = await async_client.get(f"/api/v1/products/{product_id}")
    assert get_response.status_code == 200
    
    product = get_response.json()["data"]
    variant = product["variants"][0]
    
    # Verify all images are persisted
    assert len(variant["images"]) == 3
    
    # Verify URLs match
    image_urls = [img["url"] for img in variant["images"]]
    assert set(image_urls) == set(cdn_urls)
    
    # Verify first image is primary
    assert variant["images"][0]["is_primary"] is True
    assert variant["images"][1]["is_primary"] is False
    assert variant["images"][2]["is_primary"] is False


@pytest.mark.asyncio
async def test_product_validation_missing_fields(
    async_client: AsyncClient,
    auth_headers: dict
):
    """Test validation of required fields"""
    
    # Missing product name
    product_data = {
        "description": "Test product",
        "variants": [
            {"name": "Default", "base_price": 10.99, "stock": 10}
        ]
    }
    
    response = await async_client.post(
        "/api/v1/products",
        json=product_data,
        headers=auth_headers
    )
    
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_product_validation_invalid_price(
    async_client: AsyncClient,
    db_session: AsyncSession,
    auth_headers: dict
):
    """Test validation of price fields"""
    
    # Create a test category
    category = Category(
        id=uuid4(),
        name="Test",
        is_active=True
    )
    db_session.add(category)
    await db_session.commit()
    
    # Negative price
    product_data = {
        "name": "Test Product",
        "category_id": str(category.id),
        "variants": [
            {"name": "Default", "base_price": -10.99, "stock": 10}
        ]
    }
    
    response = await async_client.post(
        "/api/v1/products",
        json=product_data,
        headers=auth_headers
    )
    
    # Should either reject or handle gracefully
    assert response.status_code in [400, 422]


@pytest.mark.asyncio
async def test_product_creation_requires_auth(
    async_client: AsyncClient,
    db_session: AsyncSession
):
    """Test that product creation requires authentication"""
    
    # Create a test category
    category = Category(
        id=uuid4(),
        name="Test",
        is_active=True
    )
    db_session.add(category)
    await db_session.commit()
    
    product_data = {
        "name": "Test Product",
        "category_id": str(category.id),
        "variants": [
            {"name": "Default", "base_price": 10.99, "stock": 10}
        ]
    }
    
    # Try without auth headers
    response = await async_client.post(
        "/api/v1/products",
        json=product_data
    )
    
    assert response.status_code == 401  # Unauthorized


@pytest.mark.asyncio
async def test_primary_image_marking(
    async_client: AsyncClient,
    db_session: AsyncSession,
    auth_headers: dict
):
    """Test that the first image is marked as primary"""
    
    # Create a test category
    category = Category(
        id=uuid4(),
        name="Test",
        is_active=True
    )
    db_session.add(category)
    await db_session.commit()
    
    product_data = {
        "name": "Test Product",
        "category_id": str(category.id),
        "variants": [
            {
                "name": "Default",
                "base_price": 10.99,
                "stock": 10,
                "image_urls": [
                    "https://cdn.jsdelivr.net/gh/owner/repo@main/test/img1.jpg",
                    "https://cdn.jsdelivr.net/gh/owner/repo@main/test/img2.jpg",
                    "https://cdn.jsdelivr.net/gh/owner/repo@main/test/img3.jpg"
                ]
            }
        ]
    }
    
    response = await async_client.post(
        "/api/v1/products",
        json=product_data,
        headers=auth_headers
    )
    
    assert response.status_code == 200
    variant = response.json()["data"]["variants"][0]
    
    # Verify only first image is primary
    primary_images = [img for img in variant["images"] if img["is_primary"]]
    assert len(primary_images) == 1
    assert primary_images[0]["url"] == "https://cdn.jsdelivr.net/gh/owner/repo@main/test/img1.jpg"
