from sqlalchemy import Column, String, Boolean, Integer, Text
from core.database import BaseModel, CHAR_LENGTH


class SystemSettings(BaseModel):
    __tablename__ = "system_settings"

    maintenance_mode = Column(Boolean, default=False)
    registration_enabled = Column(Boolean, default=True)
    max_file_size = Column(Integer, default=10)  # Max file size in MB
    allowed_file_types = Column(Text, default="jpg,jpeg,png,pdf")  # Comma separated
    email_notifications = Column(Boolean, default=True)
    sms_notifications = Column(Boolean, default=False)

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "maintenance_mode": self.maintenance_mode,
            "registration_enabled": self.registration_enabled,
            "max_file_size": self.max_file_size,
            "allowed_file_types": self.allowed_file_types,
            "email_notifications": self.email_notifications,
            "sms_notifications": self.sms_notifications,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
