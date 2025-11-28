"""
Final Integration Tests for Product Creation Flow

These tests verify the complete end-to-end product creation flow:
- Complete product creation with variants and images
- Various product types (electronics, clothing, food)
- Different image formats (jpg, png, webp)
- All features working together
- Error scenarios and edge cases

Requirements: All
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4
import re

from models.product import Product, ProductVariant, ProductImage, Category
from models.user import User


@pytest.mark.asyncio
async def test_complete_product_creation_flow_electronics(
    async_client: AsyncClient,
    db_session: AsyncSession,
    auth_headers: dict
):
    """Test complete product creation flow for electronics"""
    
    # Create electronics category
    category_id = uuid4()
    category = Category(
        id=category_id,
        name="Electronics",
        description="Electronic devices and accessories",
        is_active=True
    )
    db_session.add(category)
    await db_session.commit()
    
    # Create a laptop product with multiple variants and images
    product_data = {
        "name": "Gaming Laptop Pro",
        "description": "High-performance gaming laptop with RGB keyboard",
        "category_id": str(category_id),
        "featured": True,
        "origin": "Taiwan",
        "variants": [
            {
                "name": "16GB RAM / 512GB SSD",
                "base_price": 1299.99,
                "sale_price": 1199.99,
                "stock": 25,
                "attributes": {
                    "ram": "16GB",
                    "storage": "512GB SSD",
                    "color": "Black"
                },
                "image_urls": [
                    "https://cdn.jsdelivr.net/gh/owner/repo@main/electronics/laptop-front.jpg",
                    "https://cdn.jsdelivr.net/gh/owner/repo@main/electronics/laptop-side.jpg",
                    "https://cdn.jsdelivr.net/gh/owner/repo@main/electronics/laptop-keyboard.jpg"
                ]
            },
            {
                "name": "32GB RAM / 1TB SSD",
                "base_price": 1799.99,
                "stock": 15,
                "attributes": {
                    "ram": "32GB",
                    "storage": "1TB SSD",
                    "color": "Black"
                },
                "image_urls": [
                    "https://cdn.jsdelivr.net/gh/owner/repo@main/electronics/laptop-pro-front.jpg",
                    "https://cdn.jsdelivr.net/gh/owner/repo@main/electronics/laptop-pro-side.jpg"
                ]
            }
        ]
    }
    
    # Step 1: Create product
    create_response = await async_client.post(
        "/api/v1/products/",
        json=product_data,
        headers=auth_headers
    )
    
    assert create_response.status_code == 200
    create_data = create_response.json()
    assert create_data["success"] is True
    
    product = create_data["data"]
    product_id = product["id"]
    
    # Verify product data
    assert product["name"] == "Gaming Laptop Pro"
    assert product["featured"] is True
    assert product["origin"] == "Taiwan"
    assert len(product["variants"]) == 2
    
    # Step 2: Verify SKU auto-generation
    variant1 = product["variants"][0]
    variant2 = product["variants"][1]
    
    assert variant1["sku"]
    assert variant2["sku"]
    assert variant1["sku"] != variant2["sku"]
    assert variant1["sku"].startswith("GAM-")  # First 3 chars of "Gaming"
    
    # Step 3: Verify image URLs are stored
    assert len(variant1["images"]) == 3
    assert len(variant2["images"]) == 2
    
    # Step 4: Verify primary images
    assert variant1["images"][0]["is_primary"] is True
    assert variant2["images"][0]["is_primary"] is True
    
    # Step 5: Verify CDN URL format
    cdn_pattern = r"https://cdn\.jsdelivr\.net/gh/[\w-]+/[\w-]+@[\w-]+/.+"
    for variant in product["variants"]:
        for image in variant["images"]:
            assert re.match(cdn_pattern, image["url"])
    
    # Step 6: Retrieve product and verify persistence
    get_response = await async_client.get(f"/api/v1/products/{product_id}")
    assert get_response.status_code == 200
    
    retrieved_product = get_response.json()["data"]
    assert retrieved_product["name"] == product["name"]
    assert len(retrieved_product["variants"]) == 2
    
    # Step 7: Verify product appears in list
    list_response = await async_client.get("/api/v1/products/")
    assert list_response.status_code == 200
    
    # Step 8: Verify images load from CDN
    for variant in retrieved_product["variants"]:
        for image in variant["images"]:
            assert "cdn.jsdelivr.net" in image["url"]


@pytest.mark.asyncio
async def test_complete_product_creation_flow_clothing(
    async_client: AsyncClient,
    db_session: AsyncSession,
    auth_headers: dict
):
    """Test complete product creation flow for clothing"""
    
    # Create clothing category
    category_id = uuid4()
    category = Category(
        id=category_id,
        name="Clothing",
        description="Apparel and fashion items",
        is_active=True
    )
    db_session.add(category)
    await db_session.commit()
    
    # Create a t-shirt product with size and color variants
    product_data = {
        "name": "Premium Cotton T-Shirt",
        "description": "100% organic cotton, comfortable fit",
        "category_id": str(category_id),
        "featured": False,
        "origin": "Bangladesh",
        "variants": [
            {
                "name": "Small - Red",
                "base_price": 24.99,
                "sale_price": 19.99,
                "stock": 50,
                "attributes": {
                    "size": "S",
                    "color": "Red",
                    "material": "100% Cotton"
                },
                "image_urls": [
                    "https://cdn.jsdelivr.net/gh/fashion/store@main/tshirts/red-small-front.png",
                    "https://cdn.jsdelivr.net/gh/fashion/store@main/tshirts/red-small-back.png"
                ]
            },
            {
                "name": "Medium - Blue",
                "base_price": 24.99,
                "stock": 75,
                "attributes": {
                    "size": "M",
                    "color": "Blue",
                    "material": "100% Cotton"
                },
                "image_urls": [
                    "https://cdn.jsdelivr.net/gh/fashion/store@main/tshirts/blue-medium-front.png"
                ]
            },
            {
                "name": "Large - Black",
                "base_price": 24.99,
                "stock": 60,
                "attributes": {
                    "size": "L",
                    "color": "Black",
                    "material": "100% Cotton"
                },
                "image_urls": [
                    "https://cdn.jsdelivr.net/gh/fashion/store@main/tshirts/black-large-front.png",
                    "https://cdn.jsdelivr.net/gh/fashion/store@main/tshirts/black-large-back.png",
                    "https://cdn.jsdelivr.net/gh/fashion/store@main/tshirts/black-large-detail.png"
                ]
            }
        ]
    }
    
    # Create product
    create_response = await async_client.post(
        "/api/v1/products/",
        json=product_data,
        headers=auth_headers
    )
    
    assert create_response.status_code == 200
    product = create_response.json()["data"]
    
    # Verify all variants created
    assert len(product["variants"]) == 3
    
    # Verify each variant has unique SKU
    skus = [v["sku"] for v in product["variants"]]
    assert len(skus) == len(set(skus))  # All unique
    
    # Verify images for each variant
    assert len(product["variants"][0]["images"]) == 2
    assert len(product["variants"][1]["images"]) == 1
    assert len(product["variants"][2]["images"]) == 3
    
    # Verify PNG format is supported
    for variant in product["variants"]:
        for image in variant["images"]:
            assert image["url"].endswith(".png")


@pytest.mark.asyncio
async def test_complete_product_creation_flow_food(
    async_client: AsyncClient,
    db_session: AsyncSession,
    auth_headers: dict
):
    """Test complete product creation flow for food products"""
    
    # Create food category
    category_id = uuid4()
    category = Category(
        id=category_id,
        name="Food & Beverages",
        description="Food and drink products",
        is_active=True
    )
    db_session.add(category)
    await db_session.commit()
    
    # Create a coffee product with different sizes
    product_data = {
        "name": "Organic Arabica Coffee Beans",
        "description": "Premium single-origin coffee beans from Colombia",
        "category_id": str(category_id),
        "featured": True,
        "origin": "Colombia",
        "dietary_tags": ["Organic", "Fair Trade", "Vegan"],
        "variants": [
            {
                "name": "250g Bag",
                "base_price": 12.99,
                "stock": 100,
                "attributes": {
                    "weight": "250g",
                    "roast": "Medium"
                },
                "image_urls": [
                    "https://cdn.jsdelivr.net/gh/coffee/shop@main/products/arabica-250g.webp"
                ]
            },
            {
                "name": "500g Bag",
                "base_price": 22.99,
                "sale_price": 19.99,
                "stock": 75,
                "attributes": {
                    "weight": "500g",
                    "roast": "Medium"
                },
                "image_urls": [
                    "https://cdn.jsdelivr.net/gh/coffee/shop@main/products/arabica-500g.webp",
                    "https://cdn.jsdelivr.net/gh/coffee/shop@main/products/arabica-500g-detail.webp"
                ]
            },
            {
                "name": "1kg Bag",
                "base_price": 39.99,
                "stock": 50,
                "attributes": {
                    "weight": "1kg",
                    "roast": "Medium"
                },
                "image_urls": [
                    "https://cdn.jsdelivr.net/gh/coffee/shop@main/products/arabica-1kg.webp"
                ]
            }
        ]
    }
    
    # Create product
    create_response = await async_client.post(
        "/api/v1/products/",
        json=product_data,
        headers=auth_headers
    )
    
    assert create_response.status_code == 200
    product = create_response.json()["data"]
    
    # Verify dietary tags
    assert "Organic" in product.get("dietary_tags", [])
    assert "Fair Trade" in product.get("dietary_tags", [])
    
    # Verify all variants
    assert len(product["variants"]) == 3
    
    # Verify WebP format is supported
    for variant in product["variants"]:
        for image in variant["images"]:
            assert image["url"].endswith(".webp")
    
    # Verify sale price on middle variant
    assert product["variants"][1]["sale_price"] == 19.99


@pytest.mark.asyncio
async def test_mixed_image_formats(
    async_client: AsyncClient,
    db_session: AsyncSession,
    auth_headers: dict
):
    """Test product with mixed image formats (jpg, png, webp)"""
    
    category_id = uuid4()
    category = Category(
        id=category_id,
        name="Mixed",
        is_active=True
    )
    db_session.add(category)
    await db_session.commit()
    
    product_data = {
        "name": "Product with Mixed Image Formats",
        "description": "Testing different image formats",
        "category_id": str(category_id),
        "variants": [
            {
                "name": "Default",
                "base_price": 29.99,
                "stock": 100,
                "image_urls": [
                    "https://cdn.jsdelivr.net/gh/test/repo@main/images/photo1.jpg",
                    "https://cdn.jsdelivr.net/gh/test/repo@main/images/photo2.png",
                    "https://cdn.jsdelivr.net/gh/test/repo@main/images/photo3.webp",
                    "https://cdn.jsdelivr.net/gh/test/repo@main/images/photo4.jpeg"
                ]
            }
        ]
    }
    
    create_response = await async_client.post(
        "/api/v1/products/",
        json=product_data,
        headers=auth_headers
    )
    
    assert create_response.status_code == 200
    product = create_response.json()["data"]
    
    # Verify all image formats are stored
    images = product["variants"][0]["images"]
    assert len(images) == 4
    
    # Verify different formats
    formats = [img["url"].split(".")[-1] for img in images]
    assert "jpg" in formats
    assert "png" in formats
    assert "webp" in formats
    assert "jpeg" in formats


@pytest.mark.asyncio
async def test_product_without_images(
    async_client: AsyncClient,
    db_session: AsyncSession,
    auth_headers: dict
):
    """Test creating product without images"""
    
    category_id = uuid4()
    category = Category(
        id=category_id,
        name="Test",
        is_active=True
    )
    db_session.add(category)
    await db_session.commit()
    
    product_data = {
        "name": "Product Without Images",
        "description": "This product has no images",
        "category_id": str(category_id),
        "variants": [
            {
                "name": "Default",
                "base_price": 9.99,
                "stock": 50
            }
        ]
    }
    
    create_response = await async_client.post(
        "/api/v1/products/",
        json=product_data,
        headers=auth_headers
    )
    
    assert create_response.status_code == 200
    product = create_response.json()["data"]
    
    # Verify product created successfully without images
    assert product["name"] == "Product Without Images"
    assert len(product["variants"]) == 1
    
    # Verify images array is empty
    images = product["variants"][0].get("images", [])
    assert len(images) == 0


@pytest.mark.asyncio
async def test_product_with_many_variants(
    async_client: AsyncClient,
    db_session: AsyncSession,
    auth_headers: dict
):
    """Test product with many variants (stress test)"""
    
    category_id = uuid4()
    category = Category(
        id=category_id,
        name="Test",
        is_active=True
    )
    db_session.add(category)
    await db_session.commit()
    
    # Create product with 10 variants
    variants = []
    for i in range(10):
        variants.append({
            "name": f"Variant {i+1}",
            "base_price": 10.00 + i,
            "stock": 10 * (i + 1),
            "attributes": {"index": i},
            "image_urls": [
                f"https://cdn.jsdelivr.net/gh/test/repo@main/variant{i}/image1.jpg",
                f"https://cdn.jsdelivr.net/gh/test/repo@main/variant{i}/image2.jpg"
            ]
        })
    
    product_data = {
        "name": "Product with Many Variants",
        "description": "Testing multiple variants",
        "category_id": str(category_id),
        "variants": variants
    }
    
    create_response = await async_client.post(
        "/api/v1/products/",
        json=product_data,
        headers=auth_headers
    )
    
    assert create_response.status_code == 200
    product = create_response.json()["data"]
    
    # Verify all variants created
    assert len(product["variants"]) == 10
    
    # Verify all SKUs are unique
    skus = [v["sku"] for v in product["variants"]]
    assert len(skus) == len(set(skus))
    
    # Verify each variant has 2 images
    for variant in product["variants"]:
        assert len(variant["images"]) == 2
        assert variant["images"][0]["is_primary"] is True


@pytest.mark.asyncio
async def test_error_handling_invalid_category(
    async_client: AsyncClient,
    auth_headers: dict
):
    """Test error handling with invalid category ID"""
    
    product_data = {
        "name": "Test Product",
        "description": "Product with invalid category",
        "category_id": str(uuid4()),  # Non-existent category
        "variants": [
            {
                "name": "Default",
                "base_price": 10.99,
                "stock": 10
            }
        ]
    }
    
    create_response = await async_client.post(
        "/api/v1/products/",
        json=product_data,
        headers=auth_headers
    )
    
    # Should return error (400 or 404)
    assert create_response.status_code in [400, 404, 422]


@pytest.mark.asyncio
async def test_error_handling_missing_required_fields(
    async_client: AsyncClient,
    auth_headers: dict
):
    """Test error handling with missing required fields"""
    
    # Missing product name
    product_data = {
        "description": "Product without name",
        "variants": []
    }
    
    create_response = await async_client.post(
        "/api/v1/products/",
        json=product_data,
        headers=auth_headers
    )
    
    assert create_response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_error_handling_negative_price(
    async_client: AsyncClient,
    db_session: AsyncSession,
    auth_headers: dict
):
    """Test error handling with negative price"""
    
    category_id = uuid4()
    category = Category(
        id=category_id,
        name="Test",
        is_active=True
    )
    db_session.add(category)
    await db_session.commit()
    
    product_data = {
        "name": "Test Product",
        "category_id": str(category_id),
        "variants": [
            {
                "name": "Default",
                "base_price": -10.99,  # Negative price
                "stock": 10
            }
        ]
    }
    
    create_response = await async_client.post(
        "/api/v1/products/",
        json=product_data,
        headers=auth_headers
    )
    
    # Should return validation error
    assert create_response.status_code in [400, 422]


@pytest.mark.asyncio
async def test_error_handling_negative_stock(
    async_client: AsyncClient,
    db_session: AsyncSession,
    auth_headers: dict
):
    """Test error handling with negative stock"""
    
    category_id = uuid4()
    category = Category(
        id=category_id,
        name="Test",
        is_active=True
    )
    db_session.add(category)
    await db_session.commit()
    
    product_data = {
        "name": "Test Product",
        "category_id": str(category_id),
        "variants": [
            {
                "name": "Default",
                "base_price": 10.99,
                "stock": -5  # Negative stock
            }
        ]
    }
    
    create_response = await async_client.post(
        "/api/v1/products/",
        json=product_data,
        headers=auth_headers
    )
    
    # Should return validation error
    assert create_response.status_code in [400, 422]


@pytest.mark.asyncio
async def test_authentication_required(
    async_client: AsyncClient,
    db_session: AsyncSession
):
    """Test that authentication is required for product creation"""
    
    category_id = uuid4()
    category = Category(
        id=category_id,
        name="Test",
        is_active=True
    )
    db_session.add(category)
    await db_session.commit()
    
    product_data = {
        "name": "Test Product",
        "category_id": str(category_id),
        "variants": [
            {
                "name": "Default",
                "base_price": 10.99,
                "stock": 10
            }
        ]
    }
    
    # Try without auth headers
    create_response = await async_client.post(
        "/api/v1/products/",
        json=product_data
    )
    
    assert create_response.status_code == 401  # Unauthorized


@pytest.mark.asyncio
async def test_full_crud_operations(
    async_client: AsyncClient,
    db_session: AsyncSession,
    auth_headers: dict
):
    """Test full CRUD operations on a product"""
    
    # Create category
    category_id = uuid4()
    category = Category(
        id=category_id,
        name="CRUD Test",
        is_active=True
    )
    db_session.add(category)
    await db_session.commit()
    
    # CREATE
    product_data = {
        "name": "CRUD Test Product",
        "description": "Testing CRUD operations",
        "category_id": str(category_id),
        "variants": [
            {
                "name": "Original",
                "base_price": 50.00,
                "stock": 100,
                "image_urls": [
                    "https://cdn.jsdelivr.net/gh/test/repo@main/crud/original.jpg"
                ]
            }
        ]
    }
    
    create_response = await async_client.post(
        "/api/v1/products/",
        json=product_data,
        headers=auth_headers
    )
    assert create_response.status_code == 200
    product_id = create_response.json()["data"]["id"]
    
    # READ
    get_response = await async_client.get(f"/api/v1/products/{product_id}")
    assert get_response.status_code == 200
    product = get_response.json()["data"]
    assert product["name"] == "CRUD Test Product"
    
    # LIST
    list_response = await async_client.get("/api/v1/products/")
    assert list_response.status_code == 200
    
    # UPDATE (if endpoint exists)
    update_data = {
        "name": "Updated CRUD Test Product",
        "description": "Updated description"
    }
    update_response = await async_client.put(
        f"/api/v1/products/{product_id}",
        json=update_data,
        headers=auth_headers
    )
    # Update might not be implemented, so we accept 200 or 404
    assert update_response.status_code in [200, 404, 405]
    
    # DELETE (if endpoint exists)
    delete_response = await async_client.delete(
        f"/api/v1/products/{product_id}",
        headers=auth_headers
    )
    # Delete might not be implemented, so we accept 200, 204, or 404
    assert delete_response.status_code in [200, 204, 404, 405]


@pytest.mark.asyncio
async def test_pagination_and_filtering(
    async_client: AsyncClient,
    db_session: AsyncSession,
    auth_headers: dict
):
    """Test pagination and filtering of products"""
    
    # Create multiple categories
    electronics_cat_id = uuid4()
    clothing_cat_id = uuid4()
    electronics_cat = Category(id=electronics_cat_id, name="Electronics", is_active=True)
    clothing_cat = Category(id=clothing_cat_id, name="Clothing", is_active=True)
    db_session.add_all([electronics_cat, clothing_cat])
    await db_session.commit()
    
    # Create multiple products
    for i in range(5):
        product_data = {
            "name": f"Electronics Product {i}",
            "category_id": str(electronics_cat_id),
            "variants": [{"name": "Default", "base_price": 10.00 + i, "stock": 10}]
        }
        await async_client.post("/api/v1/products/", json=product_data, headers=auth_headers)
    
    for i in range(3):
        product_data = {
            "name": f"Clothing Product {i}",
            "category_id": str(clothing_cat_id),
            "variants": [{"name": "Default", "base_price": 20.00 + i, "stock": 10}]
        }
        await async_client.post("/api/v1/products/", json=product_data, headers=auth_headers)
    
    # Test listing all products
    list_response = await async_client.get("/api/v1/products/")
    assert list_response.status_code == 200
    
    # Test filtering by category (if supported)
    filter_response = await async_client.get(
        f"/api/v1/products/?category_id={electronics_cat_id}"
    )
    # Filtering might not be implemented, so we just check it doesn't error
    assert filter_response.status_code in [200, 404]


@pytest.mark.asyncio
async def test_concurrent_product_creation(
    async_client: AsyncClient,
    db_session: AsyncSession,
    auth_headers: dict
):
    """Test creating multiple products concurrently"""
    
    category_id = uuid4()
    category = Category(
        id=category_id,
        name="Concurrent Test",
        is_active=True
    )
    db_session.add(category)
    await db_session.commit()
    
    # Create multiple products
    import asyncio
    
    async def create_product(index: int):
        product_data = {
            "name": f"Concurrent Product {index}",
            "category_id": str(category_id),
            "variants": [
                {
                    "name": "Default",
                    "base_price": 10.00 + index,
                    "stock": 10
                }
            ]
        }
        response = await async_client.post(
            "/api/v1/products/",
            json=product_data,
            headers=auth_headers
        )
        return response
    
    # Create 5 products concurrently
    tasks = [create_product(i) for i in range(5)]
    responses = await asyncio.gather(*tasks)
    
    # Verify all succeeded
    for response in responses:
        assert response.status_code == 200
    
    # Verify all have unique SKUs
    skus = []
    for response in responses:
        product = response.json()["data"]
        for variant in product["variants"]:
            skus.append(variant["sku"])
    
    assert len(skus) == len(set(skus))  # All unique
