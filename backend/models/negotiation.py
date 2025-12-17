from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Integer, Enum, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime, UTC
import enum
from uuid import uuid4

from core.database import Base


class NegotiationStatus(enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    COUNTERED = "countered"
    EXPIRED = "expired"


class Negotiation(Base):
    __tablename__ = "negotiations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    buyer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    seller_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    product_variant_id = Column(UUID(as_uuid=True), ForeignKey("product_variants.id"), nullable=True) # Optional variant
    
    quantity = Column(Integer, default=1, nullable=False)
    initial_offer = Column(Float, nullable=False)
    current_price = Column(Float, nullable=False)
    last_offer_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    status = Column(Enum(NegotiationStatus, name="negotiation_status_enum"), default=NegotiationStatus.PENDING, nullable=False)
    
    # Store a history of offers in JSONB format
    # Each offer could be a dict: {"user_id": UUID, "offer_price": float, "timestamp": datetime}
    offers = Column(JSONB, default=lambda: []) 

    start_time = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=True) # When negotiation concludes
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)

    # Relationships
    buyer = relationship("User", foreign_keys=[buyer_id], back_populates="negotiations_as_buyer")
    seller = relationship("User", foreign_keys=[seller_id], back_populates="negotiations_as_seller")
    product = relationship("Product", back_populates="negotiations")
    product_variant = relationship("ProductVariant") # No back_populates needed for optional one-to-one or one-to-many
    last_offer_user = relationship("User", foreign_keys=[last_offer_by])

    def to_dict(self):
        return {
            "id": str(self.id),
            "buyer_id": str(self.buyer_id),
            "seller_id": str(self.seller_id),
            "product_id": str(self.product_id),
            "product_variant_id": str(self.product_variant_id) if self.product_variant_id else None,
            "quantity": self.quantity,
            "initial_offer": self.initial_offer,
            "current_price": self.current_price,
            "last_offer_by": str(self.last_offer_by),
            "status": self.status.value,
            "offers": self.offers,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

