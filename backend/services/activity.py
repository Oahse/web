from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from models.activity_log import ActivityLog
from uuid import UUID
from typing import Optional, List, Dict, Any
from datetime import datetime


class ActivityService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def log_activity(
        self,
        action_type: str,
        description: str,
        user_id: Optional[UUID] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ActivityLog:
        """Log an activity to the activity log"""
        activity = ActivityLog(
            user_id=user_id,
            action_type=action_type,
            description=description,
            metadata=metadata
        )
        self.db.add(activity)
        await self.db.commit()
        await self.db.refresh(activity)
        return activity

    async def get_recent_activity(
        self,
        limit: int = 100,
        since: Optional[datetime] = None
    ) -> List[ActivityLog]:
        """Get recent activity logs"""
        query = select(ActivityLog).order_by(desc(ActivityLog.created_at))
        
        if since:
            query = query.where(ActivityLog.created_at >= since)
        
        query = query.limit(limit)
        
        result = await self.db.execute(query)
        return result.scalars().all()
