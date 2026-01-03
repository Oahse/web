import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from backend.services.admin import AdminService
from backend.models.product import ProductVariant
from backend.models.inventories import Inventory

@pytest.mark.asyncio
async def test_get_all_variants_with_stock():
    """
    Test that get_all_variants returns variants with correct stock information.
    """
    # Create mock objects
    db_session = AsyncMock()
    
    # Sample data
    variant_id = uuid4()
    product_id = uuid4()
    sku = "TEST-SKU-001"
    variant_name = "Test Variant"
    base_price = 100.0
    sale_price = 90.0
    quantity_available = 50

    # Mock inventory
    mock_inventory = Inventory(
        id=uuid4(),
        variant_id=variant_id,
        quantity_available=quantity_available,
        status="in_stock"
    )

    # Mock product variant
    mock_variant = ProductVariant(
        id=variant_id,
        product_id=product_id,
        sku=sku,
        name=variant_name,
        base_price=base_price,
        sale_price=sale_price,
        is_active=True,
        inventory=mock_inventory
    )

    # Mock the database result
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [mock_variant]
    
    db_session.execute.return_value = mock_result
    db_session.scalar.return_value = 1

    # Initialize AdminService with the mock session
    admin_service = AdminService(db_session)

    # Call the method to be tested
    result = await admin_service.get_all_variants()

    # Assertions
    assert "data" in result
    assert len(result["data"]) == 1
    variant_data = result["data"][0]
    
    assert variant_data["id"] == str(variant_id)
    assert variant_data["product_id"] == str(product_id)
    assert variant_data["sku"] == sku
    assert variant_data["name"] == variant_name
    assert variant_data["base_price"] == base_price
    assert variant_data["sale_price"] == sale_price
    assert variant_data["stock"] == quantity_available
    assert variant_data["is_active"] is True
    assert "barcode" in variant_data
    assert "qr_code" in variant_data
    assert variant_data["barcode"].startswith("data:image/png;base64,")
    assert variant_data["qr_code"].startswith("data:image/png;base64,")
