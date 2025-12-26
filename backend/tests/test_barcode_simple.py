import pytest
import sys
import os

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

def test_barcode_imports():
    """Test that we can import the barcode service"""
    try:
        from services.barcode import BarcodeService
        assert BarcodeService is not None
        print("✅ BarcodeService imported successfully")
    except ImportError as e:
        pytest.fail(f"Failed to import BarcodeService: {e}")

def test_qr_code_generation():
    """Test QR code generation functionality"""
    from services.barcode import BarcodeService
    from unittest.mock import AsyncMock
    
    # Create a mock database session
    mock_db = AsyncMock()
    
    # Create barcode service instance
    barcode_service = BarcodeService(mock_db)
    
    # Test QR code generation
    test_data = "https://banwee.com/products/variant/123"
    result = barcode_service.generate_qr_code(test_data)
    
    assert result.startswith("data:image/png;base64,")
    assert len(result) > 50  # Should contain actual base64 data
    print("✅ QR code generation works")

def test_barcode_generation():
    """Test barcode generation functionality"""
    from services.barcode import BarcodeService
    from unittest.mock import AsyncMock
    
    # Create a mock database session
    mock_db = AsyncMock()
    
    # Create barcode service instance
    barcode_service = BarcodeService(mock_db)
    
    # Test barcode generation
    test_code = "TEST123456"
    result = barcode_service.generate_barcode(test_code)
    
    assert result.startswith("data:image/png;base64,")
    assert len(result) > 50  # Should contain actual base64 data
    print("✅ Barcode generation works")

if __name__ == "__main__":
    test_barcode_imports()
    test_qr_code_generation()
    test_barcode_generation()
    print("✅ All barcode tests passed!")