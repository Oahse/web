import qrcode
import barcode
from barcode.writer import ImageWriter
from io import BytesIO
import base64
from typing import Optional, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.product import ProductVariant
from lib.errors import APIException


class BarcodeService:
    """Service for generating barcodes and QR codes for product variants."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    def generate_qr_code(self, data: str, size: int = 200) -> str:
        """
        Generate QR code and return as base64 encoded string.
        
        Args:
            data: Data to encode in QR code
            size: Size of the QR code (default 200x200)
            
        Returns:
            Base64 encoded QR code image
        """
        if not data or not data.strip():
            raise APIException("QR code data cannot be empty")
            
        try:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(data)
            qr.make(fit=True)
            
            # Create QR code image
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Convert to base64
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            img_str = base64.b64encode(buffer.getvalue()).decode()
            
            return f"data:image/png;base64,{img_str}"
            
        except Exception as e:
            raise APIException(f"Failed to generate QR code: {str(e)}")
    
    def generate_barcode(self, code: str, barcode_type: str = 'code128') -> str:
        """
        Generate barcode and return as base64 encoded string.
        
        Args:
            code: Code to encode in barcode
            barcode_type: Type of barcode (default: code128)
            
        Returns:
            Base64 encoded barcode image
        """
        try:
            # Get barcode class
            barcode_class = barcode.get_barcode_class(barcode_type)
            
            # Generate barcode
            code_instance = barcode_class(code, writer=ImageWriter())
            
            # Convert to base64
            buffer = BytesIO()
            code_instance.write(buffer)
            img_str = base64.b64encode(buffer.getvalue()).decode()
            
            return f"data:image/png;base64,{img_str}"
            
        except Exception as e:
            raise APIException(f"Failed to generate barcode: {str(e)}")
    
    async def generate_variant_codes(self, variant_id: UUID) -> Dict[str, str]:
        """
        Generate both barcode and QR code for a product variant.
        
        Args:
            variant_id: UUID of the product variant
            
        Returns:
            Dictionary containing barcode and qr_code as base64 strings
        """
        # Get variant from database
        query = select(ProductVariant).where(ProductVariant.id == variant_id)
        result = await self.db.execute(query)
        variant = result.scalar_one_or_none()
        
        if not variant:
            raise APIException("Product variant not found")
        
        # Generate QR code with variant information
        qr_data = {
            "variant_id": str(variant_id),
            "sku": variant.sku,
            "name": variant.name,
            "price": variant.current_price
        }
        qr_code_data = f"https://banwee.com/products/variant/{variant_id}"
        
        # Generate codes
        barcode_b64 = self.generate_barcode(variant.sku)
        qr_code_b64 = self.generate_qr_code(qr_code_data)
        
        # Update variant with generated codes
        variant.barcode = barcode_b64
        variant.qr_code = qr_code_b64
        
        await self.db.commit()
        
        return {
            "barcode": barcode_b64,
            "qr_code": qr_code_b64
        }
    
    async def update_variant_codes(self, variant_id: UUID, barcode: Optional[str] = None, qr_code: Optional[str] = None) -> Dict[str, str]:
        """
        Update barcode and/or QR code for a product variant.
        
        Args:
            variant_id: UUID of the product variant
            barcode: New barcode (optional)
            qr_code: New QR code (optional)
            
        Returns:
            Dictionary containing updated barcode and qr_code
        """
        # Get variant from database
        query = select(ProductVariant).where(ProductVariant.id == variant_id)
        result = await self.db.execute(query)
        variant = result.scalar_one_or_none()
        
        if not variant:
            raise APIException("Product variant not found")
        
        # Update codes if provided
        if barcode is not None:
            variant.barcode = barcode
        if qr_code is not None:
            variant.qr_code = qr_code
        
        await self.db.commit()
        
        return {
            "barcode": variant.barcode,
            "qr_code": variant.qr_code
        }
    
    def generate_product_url_qr(self, product_id: UUID) -> str:
        """Generate QR code for product URL."""
        product_url = f"https://banwee.com/products/{product_id}"
        return self.generate_qr_code(product_url)
    
    def generate_sku_barcode(self, sku: str) -> str:
        """Generate barcode for SKU."""
        return self.generate_barcode(sku)