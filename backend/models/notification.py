from sqlalchemy import Column, String, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from core.database import BaseModel, CHAR_LENGTH, GUID


class Notification(BaseModel):
    __tablename__ = "notifications"

    user_id = Column(GUID(), ForeignKey("users.id"), nullable=False)
    message = Column(Text, nullable=False)
    read = Column(Boolean, default=False)
    type = Column(String(CHAR_LENGTH), default="info") # e.g., 'info', 'warning', 'error', 'success'
    related_id = Column(String(CHAR_LENGTH), nullable=True) # e.g., order_id, product_id

    user = relationship("User", back_populates="notifications")

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "message": self.message,
            "read": self.read,
            "type": self.type,
            "related_id": self.related_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
