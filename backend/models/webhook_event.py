from sqlalchemy import Column, String, DateTime, Text, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from core.database import BaseModel
import uuid


class WebhookEvent(BaseModel):
    __tablename__ = "webhook_events"

    stripe_event_id = Column(String(255), unique=True, nullable=False, index=True)
    event_type = Column(String(100), nullable=False, index=True)
    processed = Column(Boolean, default=False, nullable=False)
    processing_attempts = Column(Integer, default=0, nullable=False)
    last_processing_attempt = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    event_data = Column(JSONB, nullable=True)

    def __repr__(self):
        return f"<WebhookEvent(stripe_event_id='{self.stripe_event_id}', event_type='{self.event_type}', processed={self.processed})>"