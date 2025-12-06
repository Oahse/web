from sqlalchemy import Column, String, ForeignKey, JSON
from sqlalchemy.orm import relationship
from core.database import BaseModel, CHAR_LENGTH, GUID


class ActivityLog(BaseModel):
    __tablename__ = "activity_logs"
    __table_args__ = {'extend_existing': True}

    user_id = Column(GUID(), ForeignKey("users.id"), nullable=True)
    action_type = Column(String(100), nullable=False)  # order, registration, review, low_stock, payment
    description = Column(String(CHAR_LENGTH), nullable=False)
    meta_data = Column(JSON, nullable=True)  # Renamed from metadata to avoid SQLAlchemy reserved name

    # Relationships
    user = relationship("User", back_populates="activity_logs", lazy="selectin")

    def to_dict(self) -> dict:
        """Convert activity log to dictionary for API responses"""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id) if self.user_id else None,
            "action_type": self.action_type,
            "description": self.description,
            "metadata": self.meta_data,  # Return as metadata in API
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
