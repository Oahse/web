from sqlalchemy import Column, String, Float, Boolean, DateTime, Index
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
from core.database import Base


class TaxRate(Base):
    """Tax rates by country and province/state"""
    __tablename__ = "tax_rates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    country_code = Column(String(2), nullable=False, index=True)  # ISO 3166-1 alpha-2
    country_name = Column(String(100), nullable=False)
    province_code = Column(String(10), nullable=True, index=True)  # State/Province code
    province_name = Column(String(100), nullable=True)
    tax_rate = Column(Float, nullable=False)  # Tax rate as decimal (e.g., 0.13 for 13%)
    tax_name = Column(String(50), nullable=True)  # e.g., "GST", "VAT", "Sales Tax"
    is_active = Column(Boolean, default=True, nullable=False)
    effective_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Composite index for fast lookups
    __table_args__ = (
        Index('idx_tax_country_province', 'country_code', 'province_code'),
    )

    def __repr__(self):
        location = f"{self.country_code}"
        if self.province_code:
            location += f"-{self.province_code}"
        return f"<TaxRate {location}: {self.tax_rate * 100}%>"
