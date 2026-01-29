"""
Unit tests for authentication service
"""
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession

from services.auth import AuthService
from models.user import User
from core.errors import APIException
from schemas.auth import UserCreate, UserLogin


class TestAuthService:
    
    @pytest_asyncio.fixture
    async def auth_service(self, db_session):
        return AuthService(db_session)
    
    @pytest_asyncio.fixture
    async def user_data(self):
        return {
            "email": "test@example.com",
            "username": "testuser",
            "first_name": "Test",
            "last_name": "User",
            "password": "testpassword123"
        }
    
    @pytest.mark.asyncio
    async def test_register_user_success(self, auth_service, user_data):
        """Test successful user registration"""
        user_create = UserCreate(**user_data)
        
        with patch('services.auth.get_password_hash') as mock_hash:
            mock_hash.return_value = "hashed_password"
            
            user = await auth_service.register_user(user_create)
            
            assert user.email == user_data["email"]
            assert user.username == user_data["username"]
            assert user.first_name == user_data["first_name"]
            assert user.last_name == user_data["last_name"]
            assert user.hashed_password == "hashed_password"
            assert not user.is_verified
            assert user.is_active
    
    @pytest.mark.asyncio
    async def test_register_user_duplicate_email(self, auth_service, user_data, test_user):
        """Test registration with duplicate email"""
        user_data["email"] = test_user.email
        user_create = UserCreate(**user_data)
        
        with pytest.raises(APIException) as exc_info:
            await auth_service.register_user(user_create)
        
        assert exc_info.value.status_code == 400
        assert "already registered" in str(exc_info.value.message).lower()
    
    @pytest.mark.asyncio
    async def test_authenticate_user_success(self, auth_service, test_user):
        """Test successful user authentication"""
        with patch('services.auth.verify_password') as mock_verify:
            mock_verify.return_value = True
            
            user = await auth_service.authenticate_user(test_user.email, "password")
            
            assert user.id == test_user.id
            assert user.email == test_user.email
    
    @pytest.mark.asyncio
    async def test_authenticate_user_invalid_credentials(self, auth_service, test_user):
        """Test authentication with invalid credentials"""
        with patch('services.auth.verify_password') as mock_verify:
            mock_verify.return_value = False
            
            user = await auth_service.authenticate_user(test_user.email, "wrong_password")
            
            assert user is None
    
    @pytest.mark.asyncio
    async def test_authenticate_user_not_found(self, auth_service):
        """Test authentication with non-existent user"""
        user = await auth_service.authenticate_user("nonexistent@example.com", "password")
        assert user is None
    
    @pytest.mark.asyncio
    async def test_create_access_token(self, auth_service):
        """Test access token creation"""
        user_id = uuid4()
        
        with patch('services.auth.create_access_token') as mock_create:
            mock_create.return_value = "test_token"
            
            token = auth_service.create_access_token(user_id)
            
            assert token == "test_token"
            mock_create.assert_called_once_with(data={"sub": str(user_id)})
    
    @pytest.mark.asyncio
    async def test_verify_token_valid(self, auth_service):
        """Test token verification with valid token"""
        user_id = uuid4()
        
        with patch('services.auth.verify_token') as mock_verify:
            mock_verify.return_value = {"sub": str(user_id)}
            
            payload = auth_service.verify_token("valid_token")
            
            assert payload["sub"] == str(user_id)
    
    @pytest.mark.asyncio
    async def test_verify_token_invalid(self, auth_service):
        """Test token verification with invalid token"""
        with patch('services.auth.verify_token') as mock_verify:
            mock_verify.return_value = None
            
            payload = auth_service.verify_token("invalid_token")
            
            assert payload is None
    
    @pytest.mark.asyncio
    async def test_get_user_by_id(self, auth_service, test_user):
        """Test getting user by ID"""
        user = await auth_service.get_user_by_id(test_user.id)
        
        assert user.id == test_user.id
        assert user.email == test_user.email
    
    @pytest.mark.asyncio
    async def test_get_user_by_email(self, auth_service, test_user):
        """Test getting user by email"""
        user = await auth_service.get_user_by_email(test_user.email)
        
        assert user.id == test_user.id
        assert user.email == test_user.email
    
    @pytest.mark.asyncio
    async def test_update_user_password(self, auth_service, test_user):
        """Test updating user password"""
        new_password = "newpassword123"
        
        with patch('services.auth.get_password_hash') as mock_hash:
            mock_hash.return_value = "new_hashed_password"
            
            await auth_service.update_user_password(test_user.id, new_password)
            
            # Refresh user from database
            await auth_service.db.refresh(test_user)
            assert test_user.hashed_password == "new_hashed_password"
    
    @pytest.mark.asyncio
    async def test_verify_user_email(self, auth_service, test_user):
        """Test email verification"""
        # Initially user is not verified
        test_user.is_verified = False
        await auth_service.db.commit()
        
        await auth_service.verify_user_email(test_user.id)
        
        await auth_service.db.refresh(test_user)
        assert test_user.is_verified
    
    @pytest.mark.asyncio
    async def test_deactivate_user(self, auth_service, test_user):
        """Test user deactivation"""
        await auth_service.deactivate_user(test_user.id)
        
        await auth_service.db.refresh(test_user)
        assert not test_user.is_active
    
    @pytest.mark.asyncio
    async def test_reset_password_request(self, auth_service, test_user):
        """Test password reset request"""
        with patch('services.auth.generate_reset_token') as mock_token:
            mock_token.return_value = "reset_token_123"
            
            token = await auth_service.create_password_reset_token(test_user.email)
            
            assert token == "reset_token_123"
    
    @pytest.mark.asyncio
    async def test_reset_password_with_token(self, auth_service, test_user):
        """Test password reset with valid token"""
        reset_token = "valid_reset_token"
        new_password = "newpassword123"
        
        with patch('services.auth.verify_reset_token') as mock_verify:
            mock_verify.return_value = test_user.id
            
            with patch('services.auth.get_password_hash') as mock_hash:
                mock_hash.return_value = "new_hashed_password"
                
                success = await auth_service.reset_password_with_token(reset_token, new_password)
                
                assert success
                await auth_service.db.refresh(test_user)
                assert test_user.hashed_password == "new_hashed_password"
    
    @pytest.mark.asyncio
    async def test_reset_password_invalid_token(self, auth_service):
        """Test password reset with invalid token"""
        with patch('services.auth.verify_reset_token') as mock_verify:
            mock_verify.return_value = None
            
            success = await auth_service.reset_password_with_token("invalid_token", "newpassword")
            
            assert not success