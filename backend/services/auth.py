from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from fastapi import HTTPException, Depends, status, BackgroundTasks
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
import secrets
from core.config import settings
from models.user import User
from schemas.auth import UserCreate, Token, UserResponse, AuthResponse
from services.user import UserService
from core.database import get_db
from core.utils.messages.email import send_email
from core.utils.encryption import PasswordManager

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.password_manager = PasswordManager()

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return self.password_manager.verify_password(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        """Hash a password."""
        return self.password_manager.hash_password(password)

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None):
        """Create a JWT access token."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(
            to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt

    def create_refresh_token(self, data: dict, expires_delta: Optional[timedelta] = None):
        """Create a JWT refresh token."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(days=7)  # Refresh tokens last 7 days
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(
            to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def _send_verification_email(self, email: str, verification_code: str):
        """Placeholder for sending a verification email."""
        print(
            f"Sending verification email to {email} with code {verification_code}")
        # In a real application, integrate with an email service here

    async def _send_welcome_sms(self, phone_number: str):
        """Placeholder for sending a welcome SMS."""
        print(f"Sending welcome SMS to {phone_number}")
        # In a real application, integrate with an SMS service here

    async def create_user(self, user_data: UserCreate, background_tasks: BackgroundTasks) -> UserResponse:
        """Create a new user."""
        # Check if user already exists
        existing_user = await self.get_user_by_email(user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        user_service = UserService(self.db)
        print(user_data, '---')
        new_user = await user_service.create_user(user_data, background_tasks)

        # --- Send Notification to Admin for New User Registration ---
        admin_user_query = select(User.id).where(User.role == "Admin")
        admin_user_id = (await self.db.execute(admin_user_query)).scalar_one_or_none()

        if admin_user_id:
            # Lazy import to avoid circular import
            from services.notifications import NotificationService
            notification_service = NotificationService(self.db)
            await notification_service.create_notification(
                user_id=str(admin_user_id),
                message=f"New user registered: {new_user.email} ({new_user.firstname} {new_user.lastname}).",
                type="info",
                related_id=str(new_user.id)
            )
        # --- End Notification ---

        return UserResponse.from_orm(new_user)

    async def authenticate_user(self, email: str, password: str, background_tasks: BackgroundTasks) -> AuthResponse:
        """Authenticate user and return token."""
        print(f"Attempting to authenticate user: {email}")
        user = await self.get_user_by_email(email)
        if not user:
            print(f"User {email} not found.")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        password_verified = self.verify_password(
            password, user.hashed_password)
        print(f"Password verification for {email}: {password_verified}")

        if not password_verified:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Update last_login timestamp
        user.last_login = func.now()
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)

        print(f"Password verified for {email}. Proceeding to token creation.")

        # Send login alert email
        context = {
            "customer_name": user.firstname,
            "login_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"),
            "company_name": "Banwee",
            "security_page_url": f"{settings.FRONTEND_URL}/account/security",
        }
        try:
            background_tasks.add_task(
                send_email,
                to_email=user.email,
                mail_type='login_alert',
                context=context
            )
            print(f"Login alert email task added for {user.email}.")
        except Exception as e:
            print(
                f"Failed to add login alert email task for {user.email}. Error: {e}")

        access_token_expires = timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        print(f"Access token expires in: {access_token_expires}")
        access_token = self.create_access_token(
            data={"sub": user.email}, expires_delta=access_token_expires
        )
        refresh_token = self.create_refresh_token(data={"sub": user.email})
        print(f"Generated access token: {access_token}")

        auth_response = AuthResponse(
            access_token=access_token,
            token_type="bearer",
            refresh_token=refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserResponse.from_orm(user)
        )
        print(f"Returning AuthResponse object: {auth_response}")
        return auth_response

    @staticmethod
    async def get_current_user(
        token: str = Depends(oauth2_scheme),
        db: AsyncSession = Depends(get_db)
    ) -> User:
        """Get current authenticated user."""
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

        try:
            payload = jwt.decode(token, settings.SECRET_KEY,
                                 algorithms=[settings.ALGORITHM])
            email: str = payload.get("sub")
            if email is None:
                raise credentials_exception
        except JWTError:
            raise credentials_exception

        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if user is None:
            raise credentials_exception
        return user

    async def send_password_reset(self, email: str, background_tasks: BackgroundTasks):
        """Send password reset email."""
        user = await self.get_user_by_email(email)
        if not user:
            # Don't reveal if email exists for security
            return

        # Generate reset token
        reset_token = self.create_access_token(
            data={"sub": user.email, "type": "password_reset"},
            expires_delta=timedelta(hours=1)  # Reset tokens expire in 1 hour
        )

        # Send reset email
        context = {
            "customer_name": user.firstname,
            "reset_link": f"{settings.FRONTEND_URL}/reset-password?token={reset_token}",
            "company_name": "Banwee",
        }

        try:
            background_tasks.add_task(
                send_email,
                to_email=user.email,
                mail_type='password_reset',
                context=context
            )
        except Exception as e:
            print(f"Failed to send password reset email: {e}")

    async def reset_password(self, token: str, new_password: str):
        """Reset password using reset token."""
        try:
            payload = jwt.decode(token, settings.SECRET_KEY,
                                 algorithms=[settings.ALGORITHM])
            email: str = payload.get("sub")
            token_type: str = payload.get("type")

            if email is None or token_type != "password_reset":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid reset token"
                )
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token"
            )

        # Get user and update password
        user = await self.get_user_by_email(email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User not found"
            )

        # Update password
        user_service = UserService(self.db)
        hashed_password = self.get_password_hash(new_password)
        await user_service.update_user(user.id, {"hashed_password": hashed_password})
