"""
Tests for authentication service
"""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from jose import jwt

from services.auth import AuthService
from models.user import User, UserRole
from schemas.auth import UserCreate
from core.config import settings


class TestAuthService:
    """Test authentication service."""
    
    @pytest.mark.asyncio
    async def test_create_user_success(self, db_session: AsyncSession, mock_email):
        """Test successful user creation."""
        auth_service = AuthService(db_session)
        user_data = UserCreate(
            email="newuser@example.com",
            firstname="New",
            lastname="User",
            password="TestPassword123!",
            phone="+1234567890",
            country="US"
        )
        
        user = await auth_service.create_user(user_data, MagicMock())
        
        assert user.email == user_data.email
        assert user.firstname == user_data.firstname
        assert user.lastname == user_data.lastname
        assert user.role == UserRole.CUSTOMER
        assert user.verified is False
        assert user.is_active is True
        assert user.hashed_password != user_data.password  # Should be hashed
        mock_email.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_user_duplicate_email(self, db_session: AsyncSession, test_user: User):
        """Test creating user with duplicate email."""
        auth_service = AuthService(db_session)
        user_data = UserCreate(
            email=test_user.email,  # Duplicate email
            firstname="Duplicate",
            lastname="User",
            password="TestPassword123!",
            phone="+1234567891",
            country="US"
        )
        
        with pytest.raises(Exception) as exc_info:
            await auth_service.create_user(user_data, MagicMock())
        
        assert "already exists" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_authenticate_user_success(self, db_session: AsyncSession, test_user: User):
        """Test successful user authentication."""
        auth_service = AuthService(db_session)
        
        authenticated_user = await auth_service.authenticate_user(test_user.email, "secret")
        
        assert authenticated_user is not None
        assert authenticated_user.id == test_user.id
        assert authenticated_user.email == test_user.email
    
    @pytest.mark.asyncio
    async def test_authenticate_user_wrong_password(self, db_session: AsyncSession, test_user: User):
        """Test authentication with wrong password."""
        auth_service = AuthService(db_session)
        
        authenticated_user = await auth_service.authenticate_user(test_user.email, "wrongpassword")
        
        assert authenticated_user is None
    
    @pytest.mark.asyncio
    async def test_authenticate_user_nonexistent(self, db_session: AsyncSession):
        """Test authentication with nonexistent user."""
        auth_service = AuthService(db_session)
        
        authenticated_user = await auth_service.authenticate_user("nonexistent@example.com", "password")
        
        assert authenticated_user is None
    
    @pytest.mark.asyncio
    async def test_authenticate_user_inactive(self, db_session: AsyncSession):
        """Test authentication with inactive user."""
        # Create inactive user
        inactive_user = User(
            email="inactive@example.com",
            firstname="Inactive",
            lastname="User",
            hashed_password="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
            role=UserRole.CUSTOMER,
            verified=True,
            is_active=False
        )
        db_session.add(inactive_user)
        await db_session.commit()
        
        auth_service = AuthService(db_session)
        
        authenticated_user = await auth_service.authenticate_user(inactive_user.email, "secret")
        
        assert authenticated_user is None
    
    def test_verify_password_success(self, db_session: AsyncSession):
        """Test password verification."""
        auth_service = AuthService(db_session)
        plain_password = "TestPassword123!"
        hashed_password = auth_service.get_password_hash(plain_password)
        
        is_valid = auth_service.verify_password(plain_password, hashed_password)
        
        assert is_valid is True
    
    def test_verify_password_failure(self, db_session: AsyncSession):
        """Test password verification with wrong password."""
        auth_service = AuthService(db_session)
        plain_password = "TestPassword123!"
        wrong_password = "WrongPassword123!"
        hashed_password = auth_service.get_password_hash(plain_password)
        
        is_valid = auth_service.verify_password(wrong_password, hashed_password)
        
        assert is_valid is False
    
    def test_get_password_hash(self, db_session: AsyncSession):
        """Test password hashing."""
        auth_service = AuthService(db_session)
        password = "TestPassword123!"
        
        hashed = auth_service.get_password_hash(password)
        
        assert hashed != password
        assert len(hashed) > 50  # Bcrypt hashes are long
        assert hashed.startswith("$2b$")  # Bcrypt prefix
    
    def test_create_access_token(self, db_session: AsyncSession):
        """Test access token creation."""
        auth_service = AuthService(db_session)
        user_data = {"sub": "user123", "role": "customer"}
        
        token = auth_service.create_access_token(data=user_data)
        
        assert isinstance(token, str)
        assert len(token) > 100  # JWT tokens are long
        
        # Decode and verify token
        decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert decoded["sub"] == "user123"
        assert decoded["role"] == "customer"
        assert "exp" in decoded
        assert "iat" in decoded
        assert "jti" in decoded
    
    def test_create_access_token_with_expiry(self, db_session: AsyncSession):
        """Test access token creation with custom expiry."""
        auth_service = AuthService(db_session)
        user_data = {"sub": "user123"}
        expires_delta = timedelta(minutes=30)
        
        token = auth_service.create_access_token(data=user_data, expires_delta=expires_delta)
        
        decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        exp_time = datetime.fromtimestamp(decoded["exp"])
        expected_exp = datetime.utcnow() + expires_delta
        
        # Allow 1 minute tolerance
        assert abs((exp_time - expected_exp).total_seconds()) < 60
    
    def test_create_refresh_token(self, db_session: AsyncSession):
        """Test refresh token creation."""
        auth_service = AuthService(db_session)
        user_data = {"sub": "user123"}
        
        token = auth_service.create_refresh_token(data=user_data)
        
        assert isinstance(token, str)
        assert len(token) > 100
        
        # Decode and verify token
        decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert decoded["sub"] == "user123"
        assert decoded["type"] == "refresh"
        assert "exp" in decoded
    
    @pytest.mark.asyncio
    async def test_get_current_user_success(self, db_session: AsyncSession, test_user: User):
        """Test getting current user from token."""
        auth_service = AuthService(db_session)
        token = auth_service.create_access_token(data={"sub": str(test_user.id)})
        
        current_user = await auth_service.get_current_user(token)
        
        assert current_user is not None
        assert current_user.id == test_user.id
        assert current_user.email == test_user.email
    
    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self, db_session: AsyncSession):
        """Test getting current user with invalid token."""
        auth_service = AuthService(db_session)
        
        with pytest.raises(Exception):
            await auth_service.get_current_user("invalid_token")
    
    @pytest.mark.asyncio
    async def test_get_current_user_expired_token(self, db_session: AsyncSession, test_user: User):
        """Test getting current user with expired token."""
        auth_service = AuthService(db_session)
        # Create expired token
        token = auth_service.create_access_token(
            data={"sub": str(test_user.id)},
            expires_delta=timedelta(seconds=-1)
        )
        
        with pytest.raises(Exception):
            await auth_service.get_current_user(token)
    
    @pytest.mark.asyncio
    async def test_get_current_user_nonexistent_user(self, db_session: AsyncSession):
        """Test getting current user with token for nonexistent user."""
        auth_service = AuthService(db_session)
        fake_user_id = "00000000-0000-0000-0000-000000000000"
        token = auth_service.create_access_token(data={"sub": fake_user_id})
        
        with pytest.raises(Exception):
            await auth_service.get_current_user(token)
    
    def test_create_email_verification_token(self, db_session: AsyncSession):
        """Test email verification token creation."""
        auth_service = AuthService(db_session)
        email = "test@example.com"
        
        token = auth_service.create_email_verification_token(email)
        
        assert isinstance(token, str)
        assert len(token) > 100
        
        # Decode and verify token
        decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert decoded["sub"] == email
        assert decoded["type"] == "email_verification"
    
    @pytest.mark.asyncio
    async def test_verify_email_success(self, db_session: AsyncSession):
        """Test email verification."""
        # Create unverified user
        unverified_user = User(
            email="unverified@example.com",
            firstname="Unverified",
            lastname="User",
            hashed_password="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
            role=UserRole.CUSTOMER,
            verified=False,
            is_active=True
        )
        db_session.add(unverified_user)
        await db_session.commit()
        
        auth_service = AuthService(db_session)
        token = auth_service.create_email_verification_token(unverified_user.email)
        
        result = await auth_service.verify_email(token)
        
        assert result is True
        await db_session.refresh(unverified_user)
        assert unverified_user.verified is True
    
    @pytest.mark.asyncio
    async def test_verify_email_invalid_token(self, db_session: AsyncSession):
        """Test email verification with invalid token."""
        auth_service = AuthService(db_session)
        
        with pytest.raises(Exception):
            await auth_service.verify_email("invalid_token")
    
    def test_create_password_reset_token(self, db_session: AsyncSession):
        """Test password reset token creation."""
        auth_service = AuthService(db_session)
        email = "test@example.com"
        
        token = auth_service.create_password_reset_token(email)
        
        assert isinstance(token, str)
        assert len(token) > 100
        
        # Decode and verify token
        decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert decoded["sub"] == email
        assert decoded["type"] == "password_reset"
    
    @pytest.mark.asyncio
    async def test_reset_password_success(self, db_session: AsyncSession, test_user: User):
        """Test password reset."""
        auth_service = AuthService(db_session)
        token = auth_service.create_password_reset_token(test_user.email)
        new_password = "NewPassword123!"
        old_hash = test_user.hashed_password
        
        result = await auth_service.reset_password(token, new_password)
        
        assert result is True
        await db_session.refresh(test_user)
        assert test_user.hashed_password != old_hash
        
        # Verify new password works
        assert auth_service.verify_password(new_password, test_user.hashed_password)
    
    @pytest.mark.asyncio
    async def test_reset_password_invalid_token(self, db_session: AsyncSession):
        """Test password reset with invalid token."""
        auth_service = AuthService(db_session)
        
        with pytest.raises(Exception):
            await auth_service.reset_password("invalid_token", "NewPassword123!")
    
    @pytest.mark.asyncio
    async def test_change_password_success(self, db_session: AsyncSession, test_user: User):
        """Test password change."""
        auth_service = AuthService(db_session)
        current_password = "secret"
        new_password = "NewPassword123!"
        old_hash = test_user.hashed_password
        
        result = await auth_service.change_password(test_user.id, current_password, new_password)
        
        assert result is True
        await db_session.refresh(test_user)
        assert test_user.hashed_password != old_hash
        
        # Verify new password works
        assert auth_service.verify_password(new_password, test_user.hashed_password)
    
    @pytest.mark.asyncio
    async def test_change_password_wrong_current(self, db_session: AsyncSession, test_user: User):
        """Test password change with wrong current password."""
        auth_service = AuthService(db_session)
        wrong_current = "wrongpassword"
        new_password = "NewPassword123!"
        
        with pytest.raises(Exception) as exc_info:
            await auth_service.change_password(test_user.id, wrong_current, new_password)
        
        assert "current password" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_update_last_login(self, db_session: AsyncSession, test_user: User):
        """Test updating last login timestamp."""
        auth_service = AuthService(db_session)
        old_last_login = test_user.last_login
        
        await auth_service.update_last_login(test_user.id)
        
        await db_session.refresh(test_user)
        assert test_user.last_login != old_last_login
        assert test_user.last_login is not None


class TestAuthServiceValidation:
    """Test authentication service validation."""
    
    @pytest.mark.asyncio
    async def test_create_user_weak_password(self, db_session: AsyncSession):
        """Test creating user with weak password."""
        auth_service = AuthService(db_session)
        user_data = UserCreate(
            email="test@example.com",
            firstname="Test",
            lastname="User",
            password="weak",  # Too weak
            phone="+1234567890",
            country="US"
        )
        
        with pytest.raises(Exception) as exc_info:
            await auth_service.create_user(user_data, MagicMock())
        
        assert "password" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_create_user_invalid_email(self, db_session: AsyncSession):
        """Test creating user with invalid email."""
        auth_service = AuthService(db_session)
        user_data = UserCreate(
            email="invalid-email",  # Invalid format
            firstname="Test",
            lastname="User",
            password="TestPassword123!",
            phone="+1234567890",
            country="US"
        )
        
        with pytest.raises(Exception):
            await auth_service.create_user(user_data, MagicMock())
    
    def test_password_strength_validation(self, db_session: AsyncSession):
        """Test password strength validation."""
        auth_service = AuthService(db_session)
        
        # Test various password strengths
        weak_passwords = [
            "123456",
            "password",
            "abc123",
            "short",
            "NOLOWER123!",
            "noupper123!",
            "NoNumbers!",
            "NoSpecialChars123"
        ]
        
        for password in weak_passwords:
            is_strong = auth_service.validate_password_strength(password)
            assert is_strong is False, f"Password '{password}' should be considered weak"
        
        # Test strong password
        strong_password = "StrongPassword123!"
        is_strong = auth_service.validate_password_strength(strong_password)
        assert is_strong is True


class TestAuthServiceSecurity:
    """Test authentication service security features."""
    
    @pytest.mark.asyncio
    async def test_rate_limiting_login_attempts(self, db_session: AsyncSession, test_user: User, mock_redis):
        """Test rate limiting for login attempts."""
        auth_service = AuthService(db_session)
        
        # Mock Redis to simulate rate limiting
        mock_redis.get.return_value = b"5"  # 5 attempts
        
        with pytest.raises(Exception) as exc_info:
            await auth_service.authenticate_user(test_user.email, "wrongpassword")
        
        assert "rate limit" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_account_lockout(self, db_session: AsyncSession, test_user: User):
        """Test account lockout after multiple failed attempts."""
        auth_service = AuthService(db_session)
        
        # Simulate multiple failed attempts
        for _ in range(6):  # Exceed limit
            await auth_service.authenticate_user(test_user.email, "wrongpassword")
        
        # Account should be locked
        await db_session.refresh(test_user)
        assert test_user.account_status == "locked"
    
    def test_token_blacklisting(self, db_session: AsyncSession, test_user: User, mock_redis):
        """Test token blacklisting."""
        auth_service = AuthService(db_session)
        token = auth_service.create_access_token(data={"sub": str(test_user.id)})
        
        # Blacklist token
        auth_service.blacklist_token(token)
        
        # Verify token is blacklisted
        mock_redis.set.assert_called()
        
        # Mock Redis to return blacklisted token
        mock_redis.get.return_value = b"blacklisted"
        
        is_blacklisted = auth_service.is_token_blacklisted(token)
        assert is_blacklisted is True
    
    def test_secure_token_generation(self, db_session: AsyncSession):
        """Test secure token generation."""
        auth_service = AuthService(db_session)
        
        # Generate multiple tokens and ensure they're unique
        tokens = set()
        for _ in range(100):
            token = auth_service.create_access_token(data={"sub": "test"})
            tokens.add(token)
        
        # All tokens should be unique
        assert len(tokens) == 100
    
    @pytest.mark.asyncio
    async def test_session_management(self, db_session: AsyncSession, test_user: User, mock_redis):
        """Test session management."""
        auth_service = AuthService(db_session)
        
        # Create session
        session_id = await auth_service.create_session(test_user.id)
        assert session_id is not None
        
        # Verify session exists
        mock_redis.get.return_value = str(test_user.id).encode()
        is_valid = await auth_service.validate_session(session_id)
        assert is_valid is True
        
        # Invalidate session
        await auth_service.invalidate_session(session_id)
        mock_redis.delete.assert_called()
    
    def test_csrf_token_generation(self, db_session: AsyncSession):
        """Test CSRF token generation."""
        auth_service = AuthService(db_session)
        
        csrf_token = auth_service.generate_csrf_token()
        
        assert isinstance(csrf_token, str)
        assert len(csrf_token) >= 32  # Should be sufficiently long
        
        # Verify token is valid
        is_valid = auth_service.validate_csrf_token(csrf_token)
        assert is_valid is True
        
        # Invalid token should fail
        is_valid = auth_service.validate_csrf_token("invalid_token")
        assert is_valid is False