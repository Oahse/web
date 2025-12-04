from sqlalchemy import Column, String, Float, Boolean, Integer, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

import uuid

from core.database import Base


class NegotiationSession(Base):
    __tablename__ = "negotiation_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # User who initiated the negotiation (e.g., the buyer)
    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Store serialized buyer and seller data
    buyer_data = Column(Text, nullable=False, comment="Serialized Buyer object data (JSON)")
    seller_data = Column(Text, nullable=False, comment="Serialized Seller object data (JSON)")

    round = Column(Integer, default=0, nullable=False)
    finished = Column(Boolean, default=False, nullable=False)
    final_price = Column(Float, nullable=True)
    status = Column(String, default="ongoing", nullable=False) # e.g., "ongoing", "deal_reached", "cancelled"

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    # Relationship to the User model (assuming a User model exists)
    creator = relationship("User", back_populates="negotiation_sessions")

    def __repr__(self):
        return f"<NegotiationSession(id='{self.id}', status='{self.status}', round={self.round})>"
