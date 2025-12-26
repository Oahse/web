import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
import sys
import os

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from services.barcode import BarcodeService
from models.product import ProductVariant
from core.exceptions import APIException


class TestBarcodeService:
    """Test cases for BarcodeService"""

    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        return AsyncMock(spec=AsyncSession)

    @pytest.fixture
    def barcode_service(self, mock_db):
        """Create BarcodeService instance with mocked database"""
        return BarcodeService(mock_db)

    @pytest.fixture
    def sample_variant(self):
        """Sample product variant for testing"""
        variant = MagicMock(spec=ProductVariant)
        variant.id = uuid4()
        variant.sku = "TEST-SKU-001"
        variant.name = "Test Variant"
        variant.base_price = 29.99
        variant.sale_price = 24.99
        variant.current_price = 24.99
        variant.barcode = None
        variant.qr_code = None
        return variant

    def test_generate_qr_code_success(self, barcode_service):
        """Test successful QR code generation"""
        data = "https://banwee.com/products/variant/123"
        result = barcode_service.generate_qr_code(data)
        
        assert result.startswith("data:image/png;base64,")
        assert len(result) > 50  # Should contain actual base64 data

    def test_generate_qr_code_with_custom_size(self, barcode_service):
        """Test QR code generation with custom size"""
        data = "test-data"
        result = barcode_service.generate_qr_code(data, size=100)
        
        assert result.startswith("data:image/png;base64,")

    def test_generate_qr_code_empty_data(self, barcode_service):
        """Test QR code generation with empty data"""
        with pytest.raises(APIException):
            barcode_service.generate_qr_code("")

    def test_generate_barcode_success(self, barcode_service):
        """Test successful barcode generation"""
        code = "TEST123456"
        result = barcode_service.generate_barcode(code)
        
        assert result.startswith("data:image/png;base64,")
        assert len(result) > 50  # Should contain actual base64 data

    def test_generate_barcode_with_different_type(self, barcode_service):
        """Test barcode generation with different barcode type"""
        code = "123456789012"
        result = barcode_service.generate_barcode(code, barcode_type='ean13')
        
        assert result.startswith("data:image/png;base64,")

    def test_generate_barcode_invalid_type(self, barcode_service):
        """Test barcode generation with invalid barcode type"""
        with pytest.raises(APIException):
            barcode_service.generate_barcode("123", barcode_type='invalid_type')

    @pytest.mark.asyncio
    async def test_generate_variant_codes_success(self, barcode_service, mock_db, sample_variant):
        """Test successful variant codes generation"""
        # Mock database query
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_variant
        mock_db.execute.return_value = mock_result
        mock_db.commit = AsyncMock()

        variant_id = sample_variant.id
        result = await barcode_service.generate_variant_codes(variant_id)

        assert "barcode" in result
        assert "qr_code" in result
        assert result["barcode"].startswith("data:image/png;base64,")
        assert result["qr_code"].startswith("data:image/png;base64,")
        
        # Verify variant was updated
        assert sample_variant.barcode == result["barcode"]
        assert sample_variant.qr_code == result["qr_code"]
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_variant_codes_variant_not_found(self, barcode_service, mock_db):
        """Test variant codes generation when variant doesn't exist"""
        # Mock database query returning None
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        variant_id = uuid4()
        
        with pytest.raises(APIException, match="Product variant not found"):
            await barcode_service.generate_variant_codes(variant_id)

    @pytest.mark.asyncio
    async def test_update_variant_codes_success(self, barcode_service, mock_db, sample_variant):
        """Test successful variant codes update"""
        # Mock database query
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_variant
        mock_db.execute.return_value = mock_result
        mock_db.commit = AsyncMock()

        variant_id = sample_variant.id
        new_barcode = "data:image/png;base64,new_barcode_data"
        new_qr_code = "data:image/png;base64,new_qr_code_data"

        result = await barcode_service.update_variant_codes(
            variant_id, 
            barcode=new_barcode, 
            qr_code=new_qr_code
        )

        assert result["barcode"] == new_barcode
        assert result["qr_code"] == new_qr_code
        assert sample_variant.barcode == new_barcode
        assert sample_variant.qr_code == new_qr_code
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_variant_codes_partial_update(self, barcode_service, mock_db, sample_variant):
        """Test partial variant codes update (only barcode)"""
        # Set initial values
        sample_variant.barcode = "old_barcode"
        sample_variant.qr_code = "old_qr_code"

        # Mock database query
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_variant
        mock_db.execute.return_value = mock_result
        mock_db.commit = AsyncMock()

        variant_id = sample_variant.id
        new_barcode = "data:image/png;base64,new_barcode_data"

        result = await barcode_service.update_variant_codes(
            variant_id, 
            barcode=new_barcode
        )

        assert result["barcode"] == new_barcode
        assert result["qr_code"] == "old_qr_code"  # Should remain unchanged
        assert sample_variant.barcode == new_barcode
        assert sample_variant.qr_code == "old_qr_code"

    @pytest.mark.asyncio
    async def test_update_variant_codes_variant_not_found(self, barcode_service, mock_db):
        """Test variant codes update when variant doesn't exist"""
        # Mock database query returning None
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        variant_id = uuid4()
        
        with pytest.raises(APIException, match="Product variant not found"):
            await barcode_service.update_variant_codes(variant_id, barcode="test")

    def test_generate_product_url_qr(self, barcode_service):
        """Test product URL QR code generation"""
        product_id = uuid4()
        result = barcode_service.generate_product_url_qr(product_id)
        
        assert result.startswith("data:image/png;base64,")

    def test_generate_sku_barcode(self, barcode_service):
        """Test SKU barcode generation"""
        sku = "TEST-SKU-123"
        result = barcode_service.generate_sku_barcode(sku)
        
        assert result.startswith("data:image/png;base64,")


class TestBarcodeServiceIntegration:
    """Integration tests for BarcodeService"""

    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        return AsyncMock(spec=AsyncSession)

    @pytest.fixture
    def barcode_service(self, mock_db):
        """Create BarcodeService instance with mocked database"""
        return BarcodeService(mock_db)

    @pytest.fixture
    def sample_variant(self):
        """Sample product variant for testing"""
        variant = MagicMock(spec=ProductVariant)
        variant.id = uuid4()
        variant.sku = "TEST-SKU-001"
        variant.name = "Test Variant"
        variant.base_price = 29.99
        variant.sale_price = 24.99
        variant.current_price = 24.99
        variant.barcode = None
        variant.qr_code = None
        return variant

    @pytest.mark.asyncio
    async def test_full_workflow(self, barcode_service, mock_db, sample_variant):
        """Test complete workflow: generate codes, then update them"""
        # Mock database query for generation
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_variant
        mock_db.execute.return_value = mock_result
        mock_db.commit = AsyncMock()

        variant_id = sample_variant.id

        # Step 1: Generate codes
        generated_codes = await barcode_service.generate_variant_codes(variant_id)
        
        assert "barcode" in generated_codes
        assert "qr_code" in generated_codes
        
        # Step 2: Update codes
        new_barcode = "data:image/png;base64,updated_barcode"
        updated_codes = await barcode_service.update_variant_codes(
            variant_id, 
            barcode=new_barcode
        )
        
        assert updated_codes["barcode"] == new_barcode
        assert updated_codes["qr_code"] == generated_codes["qr_code"]

    @pytest.mark.asyncio
    async def test_concurrent_code_generation(self, barcode_service, mock_db):
        """Test concurrent code generation for multiple variants"""
        # Create multiple sample variants
        variants = []
        for i in range(3):
            variant = MagicMock(spec=ProductVariant)
            variant.id = uuid4()
            variant.sku = f"TEST-SKU-{i:03d}"
            variant.name = f"Test Variant {i}"
            variant.current_price = 29.99
            variant.barcode = None
            variant.qr_code = None
            variants.append(variant)

        # Mock database queries
        mock_results = []
        for variant in variants:
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = variant
            mock_results.append(mock_result)
        
        mock_db.execute.side_effect = mock_results
        mock_db.commit = AsyncMock()

        # Generate codes concurrently
        tasks = [
            barcode_service.generate_variant_codes(variant.id) 
            for variant in variants
        ]
        results = await asyncio.gather(*tasks)

        # Verify all codes were generated
        assert len(results) == 3
        for result in results:
            assert "barcode" in result
            assert "qr_code" in result
            assert result["barcode"].startswith("data:image/png;base64,")
            assert result["qr_code"].startswith("data:image/png;base64,")


if __name__ == "__main__":
    pytest.main([__file__])