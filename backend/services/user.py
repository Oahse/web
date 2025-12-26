from fastapi import BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, func
from sqlalchemy.orm import selectinload
from typing import List, Optional
from uuid import UUID, uuid4
from models.user import Address, User
from models.orders import Order
from core.exceptions import APIException
from schemas.user import UserCreate, UserUpdate
from datetime import datetime, timedelta
import secrets
from core.utils.messages.email import send_email
import httpx
from core.config import settings
from core.utils.encryption import PasswordManager


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.password_manager = PasswordManager()

    async def create_user(self, user_data: UserCreate, background_tasks: BackgroundTasks) -> User:
        hashed_password = self.password_manager.hash_password(
            user_data.password)
        verification_token = secrets.token_urlsafe(32)
        token_expiration = datetime.now() + timedelta(hours=24)  # Token valid for 24 hours

        new_user = User(
            id=uuid4(),
            email=user_data.email,
            firstname=user_data.firstname,
            lastname=user_data.lastname,
            hashed_password=hashed_password,
            role=user_data.role,
            verified=False,
            verification_token=verification_token,
            token_expiration=token_expiration
        )
        self.db.add(new_user)
        await self.db.commit()
        await self.db.refresh(new_user)

        # Send verification email in the background
        background_tasks.add_task(
            self.send_verification_email, new_user, verification_token)

        return new_user

    async def send_verification_email(self, user: User, token: str):
        """Sends a verification email using the send_email service."""
        if not settings.MAILGUN_API_KEY or not settings.MAILGUN_DOMAIN:
            print("Mailgun API key or domain not configured. Skipping email sending.")
            return

        verification_link = f"{settings.FRONTEND_URL}/verify-email?token={token}"

        context = {
            "customer_name": user.firstname,
            "verification_link": verification_link,
            "company_name": "Banwee",
            "expiry_time": "24 hours",
            "current_year": datetime.now().year,
        }

        try:
            await send_email(
                to_email=user.email,
                mail_type='activation',
                context=context
            )
            print(f"Verification email sent to {user.email} successfully.")
        except Exception as e:
            print(
                f"Failed to send verification email to {user.email}. Error: {e}")

    async def verify_email(self, token: str, background_tasks: BackgroundTasks):
        """Verify user email with token and send welcome email."""
        result = await self.db.execute(
            select(User).where(User.verification_token == token)
        )
        user = result.scalar_one_or_none()

        if not user or user.token_expiration < datetime.now():
            raise APIException(
                status_code=400,
                message="Invalid or expired verification token",
            )

        user.verified = True
        user.verification_token = None
        user.token_expiration = None
        await self.db.commit()

        # Send welcome email in the background
        background_tasks.add_task(self.send_welcome_email, user)

    async def send_welcome_email(self, user: User):
        """Sends a welcome email to a new user."""
        context = {
            "customer_name": user.firstname,
            "company_name": "Banwee",
        }
        try:
            await send_email(
                to_email=user.email,
                mail_type='welcome',
                context=context
            )
            print(f"Welcome email sent to {user.email} successfully.")
        except Exception as e:
            print(f"Failed to send welcome email to {user.email}. Error: {e}")


class AddressService:
    """Service layer for managing user addresses."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # -----------------------------------------------------------
    # CRUD OPERATIONS
    # -----------------------------------------------------------

    async def create_address(
        self,
        user_id: UUID,
        street: Optional[str] = None,
        city: Optional[str] = None,
        state: Optional[str] = None,
        country: Optional[str] = None,
        post_code: Optional[str] = None,
        kind: str = "Shipping",
    ) -> Address:
        """Create a new address for a user."""
        address = Address(
            user_id=user_id,
            street=street,
            city=city,
            state=state,
            country=country,
            post_code=post_code,
            kind=kind,
        )
        self.db.add(address)
        await self.db.commit()
        await self.db.refresh(address)
        return address

    async def get_address(self, address_id: UUID) -> Optional[Address]:
        """Retrieve an address by ID."""
        query = select(Address).where(Address.id == address_id)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_user_addresses(self, user_id: UUID) -> List[Address]:
        """Fetch all addresses for a given user."""
        query = (
            select(Address)
            .where(Address.user_id == user_id)
            .options(selectinload(Address.user))
            .order_by(Address.created_at.desc())
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def update_address(self, address_id: UUID, user_id: UUID, **kwargs) -> Optional[Address]:
        """Update address fields dynamically."""
        query = update(Address)
        query = query.where(and_(Address.id == address_id,
                            Address.user_id == user_id))
        query = query.values(**kwargs)
        query = query.execution_options(synchronize_session="fetch")

        await self.db.execute(query)
        await self.db.commit()
        return await self.get_address(address_id)

    async def delete_address(self, address_id: UUID, user_id: UUID = None) -> bool:
        """Delete an address by ID."""
        if user_id:
            result = await self.db.execute(delete(Address).where(and_(Address.id == address_id, Address.user_id == user_id)))
        else:
            result = await self.db.execute(delete(Address).where(Address.id == address_id))
        await self.db.commit()
        return result.rowcount > 0

    # -----------------------------------------------------------
    # CUSTOM LOGIC
    # -----------------------------------------------------------

    async def get_default_shipping(self, user_id: UUID) -> Optional[Address]:
        """Get a user's default shipping address."""
        # First, try to find an address marked as default
        query = select(Address).where(
            Address.user_id == user_id,
            Address.is_default == True,
            Address.kind == "Shipping"
        )
        result = await self.db.execute(query)
        address = result.scalars().first()

        if address:
            return address

        # If no default is set, return the most recent shipping address
        query = select(Address).where(
            Address.user_id == user_id,
            Address.kind == "Shipping"
        ).order_by(Address.created_at.desc())
        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_default_billing(self, user_id: UUID) -> Optional[Address]:
        """Get a user's default billing address."""
        query = select(Address).where(
            Address.user_id == user_id,
            Address.kind == "Billing"
        ).order_by(Address.created_at.desc())
        result = await self.db.execute(query)
        return result.scalars().first()

    # Add missing methods to UserService
    async def get_users(self, page: int = 1, limit: int = 10, role: Optional[str] = None) -> dict:
        """Get paginated list of users with order count"""
        offset = (page - 1) * limit

        # Build base query with order count using SQL aggregation
        query = (
            select(
                User,
                func.count(Order.id).label('order_count')
            )
            .outerjoin(Order, User.id == Order.user_id)
            .group_by(User.id)
        )

        # Apply role filter if provided
        if role:
            query = query.where(User.role == role)

        # Get total count
        count_query = select(func.count()).select_from(User)
        if role:
            count_query = count_query.where(User.role == role)
        count_result = await self.db.execute(count_query)
        total = count_result.scalar()

        # Apply pagination and ordering
        query = query.offset(offset).limit(limit).order_by(User.created_at.desc())
        result = await self.db.execute(query)
        rows = result.all()

        # Convert to list of dicts with user and order_count
        users_with_counts = []
        for row in rows:
            user = row[0]
            order_count = row[1]
            # Add order_count as an attribute to the user object
            user.order_count = order_count
            users_with_counts.append(user)

        return {
            "users": users_with_counts,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "pages": (total + limit - 1) // limit
            }
        }

    async def get_user(self, user_id: UUID) -> Optional[User]:
        """Get user by ID"""
        query = select(User).where(User.id == user_id).options(
            selectinload(User.addresses)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def update_user(self, user_id: UUID, user_data: UserUpdate) -> Optional[User]:
        """Update user"""
        query = select(User).where(User.id == user_id)
        result = await self.db.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            return None

        # Update fields
        for field, value in user_data.model_dump(exclude_unset=True).items():
            if hasattr(user, field):
                setattr(user, field, value)

        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def delete_user(self, user_id: UUID) -> bool:
        """Delete user"""
        query = select(User).where(User.id == user_id)
        result = await self.db.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            return False

        await self.db.delete(user)
        await self.db.commit()
        return True
