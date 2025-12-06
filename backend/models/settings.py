from sqlalchemy import Column, String, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid # Import uuid explicitly

from core.database import Base


class SystemSettings(Base):
    __tablename__ = "system_settings"
    __table_args__ = {'extend_existing': True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4) # Use UUID type for ID
    key = Column(String, unique=True, nullable=False, index=True) # Unique key for the setting
    value = Column(Text, nullable=False) # The value of the setting (stored as text)
    value_type = Column(String, nullable=False, default="str") # Type of the value (e.g., "str", "int", "bool", "json")
    description = Column(Text, nullable=True) # Description of the setting

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    def to_dict(self) -> dict:
        return {
            "id": str(self.id), # Convert UUID to string for dict representation
            "key": self.key,
            "value": self.value,
            "value_type": self.value_type,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f"<SystemSettings(key='{self.key}', value='{self.value}')>"
