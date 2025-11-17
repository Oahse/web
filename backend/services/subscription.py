from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc, func
from typing import Optional
from fastapi import BackgroundTasks
from models.subscription import Subscription
from models.user import User
from schemas.subscription import SubscriptionCreate, SubscriptionUpdate
from core.exceptions import APIException
from core.utils.messages.email import send_email
from core.config import settings
from uuid import uuid4, UUID
from datetime import datetime

class SubscriptionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_subscription(self, subscription_data: SubscriptionCreate, user_id: UUID) -> Subscription:
        new_subscription = Subscription(
            id=uuid4(),
            user_id=user_id,
            **subscription_data.dict(exclude_unset=True)
        )
        self.db.add(new_subscription)
        await self.db.commit()
        await self.db.refresh(new_subscription)
        return new_subscription

    async def get_user_subscriptions(self, user_id: UUID, page: int = 1, limit: int = 10) -> dict:
        offset = (page - 1) * limit
        query = select(Subscription).filter(Subscription.user_id == user_id).order_by(desc(Subscription.created_at))
        total_query = select(func.count()).select_from(Subscription).filter(Subscription.user_id == user_id)

        total_subscriptions = (await self.db.execute(total_query)).scalar_one()
        subscriptions = (await self.db.execute(query.offset(offset).limit(limit))).scalars().all()

        return {
            "total": total_subscriptions,
            "page": page,
            "limit": limit,
            "data": subscriptions
        }

    async def get_subscription_by_id(self, subscription_id: UUID, user_id: UUID) -> Optional[Subscription]:
        result = await self.db.execute(select(Subscription).filter(Subscription.id == subscription_id, Subscription.user_id == user_id))
        return result.scalars().first()

    async def update_subscription(self, subscription_id: UUID, subscription_data: SubscriptionUpdate, user_id: UUID, background_tasks: BackgroundTasks) -> Subscription:
        subscription = await self.get_subscription_by_id(subscription_id, user_id)
        if not subscription:
            raise APIException(status_code=404, detail="Subscription not found")
        
        old_plan_id = subscription.plan_id

        for key, value in subscription_data.dict(exclude_unset=True).items():
            setattr(subscription, key, value)
        await self.db.commit()
        await self.db.refresh(subscription)

        background_tasks.add_task(self.send_subscription_update_email, subscription, old_plan_id)

        return subscription

    async def send_subscription_update_email(self, subscription: Subscription, old_plan_id: str):
        """Sends a subscription update email to the user."""
        user_result = await self.db.execute(select(User).where(User.id == subscription.user_id))
        user = user_result.scalar_one_or_none()
        if not user:
            return

        context = {
            "customer_name": user.firstname,
            "service_name": "Banwee Subscription",
            "subscription_id": str(subscription.id),
            "new_plan_name": subscription.plan_id,
            "old_plan_name": old_plan_id,
            "subscription_status": subscription.status,
            "next_billing_date": subscription.end_date.strftime("%B %d, %Y") if subscription.end_date else "N/A",
            "next_billing_amount": "N/A", # Price not available in model
            "manage_subscription_url": f"{settings.FRONTEND_URL}/account/subscriptions",
            "company_name": "Banwee",
        }

        try:
            await send_email(
                to_email=user.email,
                mail_type='subscription_update',
                context=context
            )
            print(f"Subscription update email sent to {user.email} successfully.")
        except Exception as e:
            print(f"Failed to send subscription update email to {user.email}. Error: {e}")

    async def delete_subscription(self, subscription_id: UUID, user_id: UUID):
        subscription = await self.get_subscription_by_id(subscription_id, user_id)
        if not subscription:
            raise APIException(status_code=404, detail="Subscription not found")
        
        await self.db.delete(subscription)
        await self.db.commit()
