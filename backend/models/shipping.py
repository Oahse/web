from sqlalchemy import Column, String, Boolean, Float, Text, Integer, Index
from sqlalchemy.dialects.postgresql import JSONB
from core.database import BaseModel, CHAR_LENGTH


class ShippingMethod(BaseModel):
    __tablename__ = "shipping_methods"
    __table_args__ = (
        # Indexes for search and performance
        Index('idx_shipping_methods_name', 'name'),
        Index('idx_shipping_methods_active', 'is_active'),
        Index('idx_shipping_methods_price', 'price'),
        Index('idx_shipping_methods_estimated_days', 'estimated_days'),
        # Composite indexes for common queries
        Index('idx_shipping_methods_active_price', 'is_active', 'price'),
        {'extend_existing': True}
    )

    name = Column(String(CHAR_LENGTH), nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Float, nullable=False)
    estimated_days = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True)
    
    # Country-specific shipping support
    available_countries = Column(JSONB, nullable=True, comment="List of country codes where this method is available. If null, available worldwide")
    restricted_countries = Column(JSONB, nullable=True, comment="List of country codes where this method is NOT available")
    regions = Column(JSONB, nullable=True, comment="Supported regions like 'EU', 'North America', etc.")
    
    # Advanced pricing options
    min_order_amount = Column(Float, nullable=True, comment="Minimum order amount required for this shipping method")
    max_weight_kg = Column(Float, nullable=True, comment="Maximum weight in kg for this shipping method")
    price_per_kg = Column(Float, nullable=True, comment="Additional price per kg over base weight")
    base_weight_kg = Column(Float, default=1.0, comment="Base weight included in base price")
    
    # Additional metadata
    carrier = Column(String(100), nullable=True, comment="Shipping carrier name (e.g., FedEx, UPS, DHL)")
    tracking_url_template = Column(String(500), nullable=True, comment="URL template for tracking with {tracking_number} placeholder")
