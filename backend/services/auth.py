from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from fastapi import HTTPException, Depends, status, BackgroundTasks
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import secrets
import uuid
from core.config import settings
from models.user import User
from schemas.auth import UserCreate, Token, UserResponse, AuthResponse
from services.user import UserService
from core.database import get_db
from core.redis import RedisService, RedisKeyManager
from core.utils.messages.email import send_email
from core.utils.encryption import PasswordManager

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/v1/auth/token")


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.password_manager = PasswordManager()
        self.redis_service = RedisService() # Initialize RedisService

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return self.password_manager.verify_password(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        """Hash a password."""
        return self.password_manager.hash_password(password)

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access",
            "jti": str(uuid.uuid4())  # JWT ID for token tracking
        })
        
        encoded_jwt = jwt.encode(
            to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt

    async def create_refresh_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT refresh token."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh",
            "jti": str(uuid.uuid4())  # JWT ID for token tracking
        })
        
        encoded_jwt = jwt.encode(
            to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        
        # Store refresh token in Redis
        if settings.REDIS_RATELIMIT_ENABLED: # Use this flag for now, need a specific one for auth
            await self._store_refresh_token_in_redis(to_encode["jti"], str(data["sub"]), to_encode["exp"])
            
        return encoded_jwt

    async def _store_refresh_token_in_redis(self, jti: str, user_id: str, expiration_timestamp: int) -> bool:
        """Stores a refresh token's JTI and user_id in Redis."""
        key = RedisKeyManager.session_key(f"refresh:{jti}")
        data = {
            "user_id": user_id,
            "exp": expiration_timestamp
        }
        # TTL should be based on the token's expiration
        ttl = expiration_timestamp - int(datetime.utcnow().timestamp())
        if ttl > 0:
            return await self.redis_service.set_with_expiry(key, data, ttl, data_type="json")
        return False
        
    async def _get_refresh_token_from_redis(self, jti: str) -> Optional[Dict[str, Any]]:
        """Retrieves a refresh token's data from Redis."""
        key = RedisKeyManager.session_key(f"refresh:{jti}")
        return await self.redis_service.get_data(key, data_type="json")

    async def _blacklist_token_in_redis(self, jti: str, expiration_timestamp: int) -> bool:
        """Blacklists a JWT (access or refresh) by its JTI in Redis."""
        key = RedisKeyManager.session_key(f"blacklist:{jti}")
        # Store a dummy value, expiration is what matters
        ttl = expiration_timestamp - int(datetime.utcnow().timestamp())
        if ttl > 0:
            return await self.redis_service.set_with_expiry(key, {"blacklisted": True}, ttl, data_type="json")
        return False
        
    async def _is_token_blacklisted(self, jti: str) -> bool:
        """Checks if a JWT's JTI is in the Redis blacklist."""
        key = RedisKeyManager.session_key(f"blacklist:{jti}")
        return await self.redis_service.exists(key)

    def verify_token(self, token: str, token_type: str = "access") -> Dict[str, Any]:
        """Verify and decode JWT token."""
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            
            # Check token type
            if payload.get("type") != token_type:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Invalid token type. Expected {token_type}",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            # Check expiration
            exp = payload.get("exp")
            if exp is None or datetime.utcnow() > datetime.fromtimestamp(exp):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has expired",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            return payload
            
        except JWTError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

    async def refresh_access_token(self, refresh_token: str) -> Dict[str, str]:
        """Generate new access token using refresh token."""
        try:
            # Verify refresh token
            payload = self.verify_token(refresh_token, "refresh")
            jti = payload.get("jti")
            user_id_from_token = payload.get("sub")

            if not jti or not user_id_from_token:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid refresh token payload"
                )
            
            # Check if refresh token is blacklisted
            if await self._is_token_blacklisted(jti):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Refresh token has been blacklisted"
                )
            
            # Check if refresh token exists in Redis
            redis_token_data = await self._get_refresh_token_from_redis(jti)
            if not redis_token_data or str(redis_token_data.get("user_id")) != user_id_from_token:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Refresh token not found or invalid"
                )
            
            # Get user from token
            user = await self.get_user_by_id(user_id_from_token)
            if not user or not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found or inactive"
                )
            
            # Create new access token
            access_token_data = {
                "sub": str(user.id),
                "email": user.email,
                "role": user.role,
                "is_active": user.is_active
            }
            
            new_access_token = self.create_access_token(access_token_data)
            
            return {
                "access_token": new_access_token,
                "token_type": "bearer"
            }
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not refresh token"
            )

    async def revoke_refresh_token(self, refresh_token: str) -> bool:
        """Revoke a refresh token (add to blacklist)."""
        try:
            payload = self.verify_token(refresh_token, "refresh")
            jti = payload.get("jti")
            
            if jti:
                expiration_timestamp = payload.get("exp")
                if expiration_timestamp:
                    # Blacklist the refresh token's JTI in Redis
                    return await self._blacklist_token_in_redis(jti, expiration_timestamp)
                # If expiration_timestamp is None, implicitly return False by falling through
            # If jti is None, implicitly return False by falling through
            return False # Moved this return here, explicitly handles cases where jti or expiration_timestamp is None
            
        except HTTPException:
            return False
        except Exception as e:
            # Log the error
            print(f"Error revoking refresh token: {e}")
            return False

    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def _send_verification_email(self, email: str, verification_code: str):
        """Placeholder for sending a verification email."""
        print(f"Sending verification email to {email} with code {verification_code}")
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
        admin_user_query = select(User.id).where(User.role == "Admin").limit(1)
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
        """Authenticate user and return JWT tokens."""
        print(f"Attempting to authenticate user: {email}")
        user = await self.get_user_by_email(email)
        if not user:
            print(f"User {email} not found.")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        password_verified = self.verify_password(password, user.hashed_password)
        print(f"Password verification for {email}: {password_verified}")

        if not password_verified:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Check if user is active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is deactivated",
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
            print(f"Failed to add login alert email task for {user.email}. Error: {e}")

        # Create token data
        token_data = {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role,
            "is_active": user.is_active
        }

        # Create access and refresh tokens
        access_token = self.create_access_token(token_data)
        refresh_token = await self.create_refresh_token(token_data)
        
        print(f"Generated tokens for user {user.email}")

        auth_response = AuthResponse(
            access_token=access_token,
            token_type="bearer",
            refresh_token=refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserResponse(
                id=user.id,
                email=user.email,
                firstname=user.firstname,
                lastname=user.lastname,
                phone=user.phone,
                role=user.role,
                verified=user.verified,
                is_active=user.is_active,
                created_at=user.created_at
            )
        )
        
        return auth_response

    async def get_current_user(
        self,
        token: str
    ) -> User:
        """Get current authenticated user using enhanced JWT verification."""
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

        try:
            # Decode and verify token
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            
            # Check token type
            token_type = payload.get("type")
            if token_type != "access":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token type",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            # Get JTI from payload
            jti: str = payload.get("jti")
            if jti and await self._is_token_blacklisted(jti):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has been blacklisted",
                    headers={"WWW-Authenticate": "Bearer"},
                )
                
            # Get user ID from token
            user_id: str = payload.get("sub")
            if user_id is None:
                raise credentials_exception
                
            # Check token expiration
            exp = payload.get("exp")
            if exp is None or datetime.utcnow() > datetime.fromtimestamp(exp):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has expired",
                    headers={"WWW-Authenticate": "Bearer"},
                )
                
        except JWTError:
            raise credentials_exception

        # Get user from database
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if user is None:
            raise credentials_exception
            
        # Check if user is still active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is deactivated",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        return user

    async def extend_session(self, token: str) -> Dict[str, Any]:
        """Extend user session by issuing a new access token."""
        try:
            # Verify current token
            payload = self.verify_token(token, "access")
            user_id = payload.get("sub")
            
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token payload"
                )
            
            # Get user to ensure they're still active
            user = await self.get_user_by_id(user_id)
            if not user or not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found or inactive"
                )
            
            # Create new access token with extended expiration
            token_data = {
                "sub": str(user.id),
                "email": user.email,
                "role": user.role,
                "is_active": user.is_active
            }
            
            # Extend by the standard access token duration
            new_access_token = self.create_access_token(token_data)
            
            return {
                "access_token": new_access_token,
                "token_type": "bearer",
                "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                "message": "Session extended successfully"
            }
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not extend session"
            )

    async def get_session_info(self, token: str) -> Dict[str, Any]:
        """Get session information for the current token."""
        try:
            payload = self.verify_token(token, "access")
            
            issued_at = payload.get("iat")
            expires_at = payload.get("exp")
            
            if not issued_at or not expires_at:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token timestamps"
                )
            
            current_time = datetime.utcnow().timestamp()
            time_until_expiry = expires_at - current_time
            
            return {
                "issued_at": issued_at,
                "expires_at": expires_at,
                "time_until_expiry": max(0, int(time_until_expiry)),
                "is_valid": time_until_expiry > 0,
                "user_id": payload.get("sub"),
                "email": payload.get("email"),
                "role": payload.get("role")
            }
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not get session info"
            )
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
