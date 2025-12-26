#!/usr/bin/env python3

import sys
import os

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(__file__))

try:
    # Try to import the barcode service directly
    from services.barcode import BarcodeService
    print("✅ Successfully imported BarcodeService")
    
    # Test basic functionality
    from unittest.mock import AsyncMock
    mock_db = AsyncMock()
    service = BarcodeService(mock_db)
    
    # Test QR code generation
    qr_result = service.generate_qr_code("test data")
    print(f"✅ QR code generated: {qr_result[:50]}...")
    
    # Test barcode generation
    barcode_result = service.generate_barcode("TEST123")
    print(f"✅ Barcode generated: {barcode_result[:50]}...")
    
    print("✅ All barcode functionality works!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()