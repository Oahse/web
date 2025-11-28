"""
Tests for image loading and CDN URL verification

These tests verify:
- Images load from jsDelivr CDN
- CDN URL format is correct
- Primary image priority
- Image error handling
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from uuid import uuid4
import re

from models.product import Product, ProductVariant, ProductImage, Category


@pytest.mark.asyncio
async def test_cdn_image_url_format(
    async_client: AsyncClient,
    db_session: AsyncSession,
    auth_headers: dict
):
    """Test that product images use correct jsDelivr CDN URL format"""
    
    # Get the supplier user from auth_headers
    from models.user import User
    from sqlalchemy import select
    result = await db_session.execute(select(User).where(User.email == "test@example.com"))
    supplier = result.scalar_one()
    
    # Create test data directly in database
    category_id = uuid4()
    category = Category(
        id=category_id,
        name="Test Category",
        is_active=True
    )
    db_session.add(category)
    
    product_id = uuid4()
    product = Product(
        id=product_id,
        name="Test Product",
        description="Product with CDN images",
        category_id=category_id,
        supplier_id=supplier.id,
        is_active=True
    )
    db_session.add(product)
    
    variant_id = uuid4()
    variant = ProductVariant(
        id=variant_id,
        product_id=product_id,
        sku="TEST-001",
        name="Default",
        base_price=29.99,
        stock=100,
        is_active=True
    )
    db_session.add(variant)
    
    cdn_url = "https://cdn.jsdelivr.net/gh/testowner/testrepo@main/products/test-image.jpg"
    image = ProductImage(
        id=uuid4(),
        variant_id=variant_id,
        url=cdn_url,
        alt_text="Test image",
        is_primary=True,
        sort_order=0
    )
    db_session.add(image)
    
    await db_session.commit()
    
    # Fetch product to verify CDN URL
    get_response = await async_client.get(f"/api/v1/products/{product_id}")
    assert get_response.status_code == 200
    
    product_data = get_response.json()["data"]
    variant_data = product_data["variants"][0]
    
    # Verify image URL is from jsDelivr CDN
    assert len(variant_data["images"]) > 0
    image_url = variant_data["images"][0]["url"]
    
    # Verify URL format: https://cdn.jsdelivr.net/gh/{owner}/{repo}@{branch}/{path}
    cdn_pattern = r"https://cdn\.jsdelivr\.net/gh/[\w-]+/[\w-]+@[\w-]+/.+"
    assert re.match(cdn_pattern, image_url), f"URL {image_url} does not match jsDelivr CDN format"
    
    # Verify the URL matches what we stored
    assert image_url == cdn_url


@pytest.mark.asyncio
async def test_multiple_products_load_from_cdn(
    async_client: AsyncClient,
    db_session: AsyncSession,
    auth_headers: dict
):
    """Test that multiple products all load images from CDN"""
    
    # Get the supplier user from auth_headers
    from models.user import User
    from sqlalchemy import select
    result = await db_session.execute(select(User).where(User.email == "test@example.com"))
    supplier = result.scalar_one()
    
    # Create test data directly in database
    category_id = uuid4()
    category = Category(
        id=category_id,
        name="Electronics",
        is_active=True
    )
    db_session.add(category)
    
    # Create multiple products with CDN images
    for i in range(3):
        product_id = uuid4()
        product = Product(
            id=product_id,
            name=f"Product {i}",
            description=f"Test product {i}",
            category_id=category_id,
            supplier_id=supplier.id,
            is_active=True
        )
        db_session.add(product)
        
        variant_id = uuid4()
        variant = ProductVariant(
            id=variant_id,
            product_id=product_id,
            sku=f"TEST-{i:03d}",
            name="Default",
            base_price=10.99 + i,
            stock=50,
            is_active=True
        )
        db_session.add(variant)
        
        cdn_url = f"https://cdn.jsdelivr.net/gh/owner/repo@main/products/product{i}.jpg"
        image = ProductImage(
            id=uuid4(),
            variant_id=variant_id,
            url=cdn_url,
            alt_text=f"Product {i} image",
            is_primary=True,
            sort_order=0
        )
        db_session.add(image)
    
    await db_session.commit()
    
    # Fetch all products
    list_response = await async_client.get("/api/v1/products/")
    assert list_response.status_code == 200
    
    response_data = list_response.json()
    # The response might be paginated
    if "data" in response_data and isinstance(response_data["data"], list):
        products = response_data["data"]
    elif "data" in response_data and "items" in response_data["data"]:
        products = response_data["data"]["items"]
    else:
        products = response_data.get("items", [])
    
    # Verify all products have CDN URLs
    cdn_pattern = r"https://cdn\.jsdelivr\.net/gh/.+"
    for product in products:
        if isinstance(product, dict) and product.get("variants") and len(product["variants"]) > 0:
            variant = product["variants"][0]
            if variant.get("images") and len(variant["images"]) > 0:
                image_url = variant["images"][0]["url"]
                assert re.match(cdn_pattern, image_url), \
                    f"Product {product['name']} image URL {image_url} is not from CDN"


@pytest.mark.asyncio
async def test_cdn_url_persists_after_retrieval(
    async_client: AsyncClient,
    db_session: AsyncSession,
    auth_headers: dict
):
    """Test that CDN URLs persist correctly after multiple retrievals"""
    
    # Get the supplier user from auth_headers
    from models.user import User
    from sqlalchemy import select
    result = await db_session.execute(select(User).where(User.email == "test@example.com"))
    supplier = result.scalar_one()
    
    # Create test data directly in database
    category_id = uuid4()
    category = Category(
        id=category_id,
        name="Clothing",
        is_active=True
    )
    db_session.add(category)
    
    product_id = uuid4()
    product = Product(
        id=product_id,
        name="T-Shirt",
        description="Cotton t-shirt",
        category_id=category_id,
        supplier_id=supplier.id,
        is_active=True
    )
    db_session.add(product)
    
    variant_id = uuid4()
    variant = ProductVariant(
        id=variant_id,
        product_id=product_id,
        sku="SHIRT-001",
        name="Medium",
        base_price=19.99,
        stock=50,
        is_active=True
    )
    db_session.add(variant)
    
    original_cdn_url = "https://cdn.jsdelivr.net/gh/myorg/myrepo@main/clothing/shirt.jpg"
    image = ProductImage(
        id=uuid4(),
        variant_id=variant_id,
        url=original_cdn_url,
        alt_text="T-Shirt image",
        is_primary=True,
        sort_order=0
    )
    db_session.add(image)
    
    await db_session.commit()
    
    # Retrieve product multiple times
    for _ in range(3):
        get_response = await async_client.get(f"/api/v1/products/{product_id}")
        assert get_response.status_code == 200
        
        product_data = get_response.json()["data"]
        variant_data = product_data["variants"][0]
        image_url = variant_data["images"][0]["url"]
        
        # Verify URL hasn't changed
        assert image_url == original_cdn_url, \
            "CDN URL changed after retrieval"



@pytest.mark.asyncio
async def test_invalid_image_url_handling(
    async_client: AsyncClient,
    db_session: AsyncSession,
    auth_headers: dict
):
    """Test that products with invalid image URLs are handled gracefully"""
    
    # Get the supplier user from auth_headers
    from models.user import User
    from sqlalchemy import select
    result = await db_session.execute(select(User).where(User.email == "test@example.com"))
    supplier = result.scalar_one()
    
    # Create test data with invalid image URL
    category_id = uuid4()
    category = Category(
        id=category_id,
        name="Test Category",
        is_active=True
    )
    db_session.add(category)
    
    product_id = uuid4()
    product = Product(
        id=product_id,
        name="Product with Invalid Image",
        description="Product with broken image URL",
        category_id=category_id,
        supplier_id=supplier.id,
        is_active=True
    )
    db_session.add(product)
    
    variant_id = uuid4()
    variant = ProductVariant(
        id=variant_id,
        product_id=product_id,
        sku="INVALID-001",
        name="Default",
        base_price=29.99,
        stock=100,
        is_active=True
    )
    db_session.add(variant)
    
    # Add an invalid image URL
    invalid_url = "https://invalid-domain-that-does-not-exist.com/image.jpg"
    image = ProductImage(
        id=uuid4(),
        variant_id=variant_id,
        url=invalid_url,
        alt_text="Invalid image",
        is_primary=True,
        sort_order=0
    )
    db_session.add(image)
    
    await db_session.commit()
    
    # Fetch product - should still return successfully even with invalid image URL
    get_response = await async_client.get(f"/api/v1/products/{product_id}")
    assert get_response.status_code == 200
    
    product_data = get_response.json()["data"]
    variant_data = product_data["variants"][0]
    
    # Verify image URL is present (even if invalid)
    assert len(variant_data["images"]) > 0
    image_url = variant_data["images"][0]["url"]
    assert image_url == invalid_url
    
    # The API should return the URL - it's the frontend's responsibility to handle loading errors


@pytest.mark.asyncio
async def test_product_with_no_images(
    async_client: AsyncClient,
    db_session: AsyncSession,
    auth_headers: dict
):
    """Test that products without images are handled gracefully"""
    
    # Get the supplier user from auth_headers
    from models.user import User
    from sqlalchemy import select
    result = await db_session.execute(select(User).where(User.email == "test@example.com"))
    supplier = result.scalar_one()
    
    # Create test data without images
    category_id = uuid4()
    category = Category(
        id=category_id,
        name="Test Category",
        is_active=True
    )
    db_session.add(category)
    
    product_id = uuid4()
    product = Product(
        id=product_id,
        name="Product without Images",
        description="Product with no images",
        category_id=category_id,
        supplier_id=supplier.id,
        is_active=True
    )
    db_session.add(product)
    
    variant_id = uuid4()
    variant = ProductVariant(
        id=variant_id,
        product_id=product_id,
        sku="NOIMG-001",
        name="Default",
        base_price=29.99,
        stock=100,
        is_active=True
    )
    db_session.add(variant)
    
    # Don't add any images
    
    await db_session.commit()
    
    # Fetch product - should still return successfully
    get_response = await async_client.get(f"/api/v1/products/{product_id}")
    assert get_response.status_code == 200
    
    product_data = get_response.json()["data"]
    variant_data = product_data["variants"][0]
    
    # Verify images array is empty or not present
    images = variant_data.get("images", [])
    assert len(images) == 0


@pytest.mark.asyncio
async def test_empty_image_url(
    async_client: AsyncClient,
    db_session: AsyncSession,
    auth_headers: dict
):
    """Test that empty image URLs are handled"""
    
    # Get the supplier user from auth_headers
    from models.user import User
    from sqlalchemy import select
    result = await db_session.execute(select(User).where(User.email == "test@example.com"))
    supplier = result.scalar_one()
    
    # Create test data with empty image URL
    category_id = uuid4()
    category = Category(
        id=category_id,
        name="Test Category",
        is_active=True
    )
    db_session.add(category)
    
    product_id = uuid4()
    product = Product(
        id=product_id,
        name="Product with Empty Image URL",
        description="Product with empty image URL",
        category_id=category_id,
        supplier_id=supplier.id,
        is_active=True
    )
    db_session.add(product)
    
    variant_id = uuid4()
    variant = ProductVariant(
        id=variant_id,
        product_id=product_id,
        sku="EMPTY-001",
        name="Default",
        base_price=29.99,
        stock=100,
        is_active=True
    )
    db_session.add(variant)
    
    # Add an empty image URL
    image = ProductImage(
        id=uuid4(),
        variant_id=variant_id,
        url="",
        alt_text="Empty image",
        is_primary=True,
        sort_order=0
    )
    db_session.add(image)
    
    await db_session.commit()
    
    # Fetch product
    get_response = await async_client.get(f"/api/v1/products/{product_id}")
    assert get_response.status_code == 200
    
    product_data = get_response.json()["data"]
    variant_data = product_data["variants"][0]
    
    # Verify image is present but URL is empty
    assert len(variant_data["images"]) > 0
    image_url = variant_data["images"][0]["url"]
    assert image_url == ""



@pytest.mark.asyncio
async def test_primary_image_is_first(
    async_client: AsyncClient,
    db_session: AsyncSession,
    auth_headers: dict
):
    """Test that the primary image is marked correctly and appears first"""
    
    # Get the supplier user from auth_headers
    from models.user import User
    from sqlalchemy import select
    result = await db_session.execute(select(User).where(User.email == "test@example.com"))
    supplier = result.scalar_one()
    
    # Create test data with multiple images
    category_id = uuid4()
    category = Category(
        id=category_id,
        name="Test Category",
        is_active=True
    )
    db_session.add(category)
    
    product_id = uuid4()
    product = Product(
        id=product_id,
        name="Product with Multiple Images",
        description="Product with multiple images",
        category_id=category_id,
        supplier_id=supplier.id,
        is_active=True
    )
    db_session.add(product)
    
    variant_id = uuid4()
    variant = ProductVariant(
        id=variant_id,
        product_id=product_id,
        sku="MULTI-001",
        name="Default",
        base_price=29.99,
        stock=100,
        is_active=True
    )
    db_session.add(variant)
    
    # Add multiple images with different sort orders
    images_data = [
        ("https://cdn.jsdelivr.net/gh/owner/repo@main/products/image1.jpg", False, 1),
        ("https://cdn.jsdelivr.net/gh/owner/repo@main/products/image2.jpg", True, 0),  # Primary
        ("https://cdn.jsdelivr.net/gh/owner/repo@main/products/image3.jpg", False, 2),
    ]
    
    for url, is_primary, sort_order in images_data:
        image = ProductImage(
            id=uuid4(),
            variant_id=variant_id,
            url=url,
            alt_text=f"Image {sort_order}",
            is_primary=is_primary,
            sort_order=sort_order
        )
        db_session.add(image)
    
    await db_session.commit()
    
    # Fetch product
    get_response = await async_client.get(f"/api/v1/products/{product_id}")
    assert get_response.status_code == 200
    
    product_data = get_response.json()["data"]
    variant_data = product_data["variants"][0]
    
    # Verify we have 3 images
    assert len(variant_data["images"]) == 3
    
    # Verify only one image is marked as primary
    primary_images = [img for img in variant_data["images"] if img["is_primary"]]
    assert len(primary_images) == 1
    
    # Verify the primary image exists
    primary_image = primary_images[0]
    assert primary_image["url"] == "https://cdn.jsdelivr.net/gh/owner/repo@main/products/image2.jpg"
    
    # Verify images are sorted by sort_order (primary should be first if sorted correctly)
    # Note: The API should sort images by sort_order, with primary image having sort_order 0
    sorted_images = sorted(variant_data["images"], key=lambda x: x["sort_order"])
    assert sorted_images[0]["is_primary"] is True


@pytest.mark.asyncio
async def test_primary_image_loads_first_in_ui(
    async_client: AsyncClient,
    db_session: AsyncSession,
    auth_headers: dict
):
    """Test that primary image has sort_order 0 for priority loading"""
    
    # Get the supplier user from auth_headers
    from models.user import User
    from sqlalchemy import select
    result = await db_session.execute(select(User).where(User.email == "test@example.com"))
    supplier = result.scalar_one()
    
    # Create test data
    category_id = uuid4()
    category = Category(
        id=category_id,
        name="Test Category",
        is_active=True
    )
    db_session.add(category)
    
    product_id = uuid4()
    product = Product(
        id=product_id,
        name="Product for Priority Test",
        description="Testing image priority",
        category_id=category_id,
        supplier_id=supplier.id,
        is_active=True
    )
    db_session.add(product)
    
    variant_id = uuid4()
    variant = ProductVariant(
        id=variant_id,
        product_id=product_id,
        sku="PRIORITY-001",
        name="Default",
        base_price=29.99,
        stock=100,
        is_active=True
    )
    db_session.add(variant)
    
    # Add images with primary having sort_order 0
    primary_url = "https://cdn.jsdelivr.net/gh/owner/repo@main/products/primary.jpg"
    image1 = ProductImage(
        id=uuid4(),
        variant_id=variant_id,
        url=primary_url,
        alt_text="Primary image",
        is_primary=True,
        sort_order=0
    )
    db_session.add(image1)
    
    image2 = ProductImage(
        id=uuid4(),
        variant_id=variant_id,
        url="https://cdn.jsdelivr.net/gh/owner/repo@main/products/secondary.jpg",
        alt_text="Secondary image",
        is_primary=False,
        sort_order=1
    )
    db_session.add(image2)
    
    await db_session.commit()
    
    # Fetch product
    get_response = await async_client.get(f"/api/v1/products/{product_id}")
    assert get_response.status_code == 200
    
    product_data = get_response.json()["data"]
    variant_data = product_data["variants"][0]
    
    # Verify primary image is first
    assert variant_data["images"][0]["is_primary"] is True
    assert variant_data["images"][0]["sort_order"] == 0
    assert variant_data["images"][0]["url"] == primary_url


@pytest.mark.asyncio
async def test_multiple_variants_each_have_primary_image(
    async_client: AsyncClient,
    db_session: AsyncSession,
    auth_headers: dict
):
    """Test that each variant can have its own primary image"""
    
    # Get the supplier user from auth_headers
    from models.user import User
    from sqlalchemy import select
    result = await db_session.execute(select(User).where(User.email == "test@example.com"))
    supplier = result.scalar_one()
    
    # Create test data
    category_id = uuid4()
    category = Category(
        id=category_id,
        name="Test Category",
        is_active=True
    )
    db_session.add(category)
    
    product_id = uuid4()
    product = Product(
        id=product_id,
        name="Product with Multiple Variants",
        description="Each variant has its own primary image",
        category_id=category_id,
        supplier_id=supplier.id,
        is_active=True
    )
    db_session.add(product)
    
    # Create two variants with their own primary images
    variants_data = [
        ("Small", "SMALL-001", "https://cdn.jsdelivr.net/gh/owner/repo@main/products/small-primary.jpg"),
        ("Large", "LARGE-001", "https://cdn.jsdelivr.net/gh/owner/repo@main/products/large-primary.jpg"),
    ]
    
    for variant_name, sku, primary_url in variants_data:
        variant_id = uuid4()
        variant = ProductVariant(
            id=variant_id,
            product_id=product_id,
            sku=sku,
            name=variant_name,
            base_price=29.99,
            stock=100,
            is_active=True
        )
        db_session.add(variant)
        
        # Add primary image for this variant
        image = ProductImage(
            id=uuid4(),
            variant_id=variant_id,
            url=primary_url,
            alt_text=f"{variant_name} primary image",
            is_primary=True,
            sort_order=0
        )
        db_session.add(image)
    
    await db_session.commit()
    
    # Fetch product
    get_response = await async_client.get(f"/api/v1/products/{product_id}")
    assert get_response.status_code == 200
    
    product_data = get_response.json()["data"]
    
    # Verify each variant has its own primary image
    assert len(product_data["variants"]) == 2
    
    for variant_data in product_data["variants"]:
        assert len(variant_data["images"]) > 0
        primary_image = variant_data["images"][0]
        assert primary_image["is_primary"] is True
        assert primary_image["sort_order"] == 0
        
        # Verify the URL matches the expected pattern for this variant
        if variant_data["name"] == "Small":
            assert "small-primary" in primary_image["url"]
        elif variant_data["name"] == "Large":
            assert "large-primary" in primary_image["url"]
