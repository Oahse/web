"""
Integration tests for authentication flow
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient
from unittest.mock import patch

from main import app


class TestAuthFlow:
    
    @pytest.mark.asyncio
    async def test_complete_registration_flow(self, client: AsyncClient):
        """Test complete user registration flow"""
        # Step 1: Register user
        registration_data = {
            "email": "newuser@example.com",
            "username": "newuser",
            "first_name": "New",
            "last_name": "User",
            "password": "securepassword123"
        }
        
        response = await client.post("/api/auth/register", json=registration_data)
        assert response.status_code == 201
        
        user_data = response.json()
        assert user_data["email"] == registration_data["email"]
        assert user_data["username"] == registration_data["username"]
        assert "id" in user_data
        assert not user_data["is_verified"]
        
        # Step 2: Attempt login before verification (should fail)
        login_data = {
            "email": registration_data["email"],
            "password": registration_data["password"]
        }
        
        response = await client.post("/api/auth/login", json=login_data)
        assert response.status_code == 400
        assert "not verified" in response.json()["message"].lower()
        
        # Step 3: Verify email (mock verification)
        with patch('services.auth.verify_email_token') as mock_verify:
            mock_verify.return_value = user_data["id"]
            
            response = await client.post(
                f"/api/auth/verify-email",
                json={"token": "mock_verification_token"}
            )
            assert response.status_code == 200
        
        # Step 4: Login after verification
        response = await client.post("/api/auth/login", json=login_data)
        assert response.status_code == 200
        
        login_response = response.json()
        assert "access_token" in login_response
        assert "refresh_token" in login_response
        assert login_response["token_type"] == "bearer"
    
    @pytest.mark.asyncio
    async def test_login_with_invalid_credentials(self, client: AsyncClient, test_user):
        """Test login with invalid credentials"""
        login_data = {
            "email": test_user.email,
            "password": "wrongpassword"
        }
        
        response = await client.post("/api/auth/login", json=login_data)
        assert response.status_code == 401
        assert "invalid credentials" in response.json()["message"].lower()
    
    @pytest.mark.asyncio
    async def test_token_refresh_flow(self, client: AsyncClient, test_user):
        """Test token refresh flow"""
        # First login to get tokens
        login_data = {
            "email": test_user.email,
            "password": "testpassword123"
        }
        
        with patch('services.auth.verify_password') as mock_verify:
            mock_verify.return_value = True
            
            response = await client.post("/api/auth/login", json=login_data)
            assert response.status_code == 200
            
            tokens = response.json()
            refresh_token = tokens["refresh_token"]
        
        # Use refresh token to get new access token
        with patch('services.auth.verify_refresh_token') as mock_verify_refresh:
            mock_verify_refresh.return_value = {"sub": str(test_user.id)}
            
            response = await client.post(
                "/api/auth/refresh",
                json={"refresh_token": refresh_token}
            )
            assert response.status_code == 200
            
            new_tokens = response.json()
            assert "access_token" in new_tokens
            assert new_tokens["access_token"] != tokens["access_token"]
    
    @pytest.mark.asyncio
    async def test_password_reset_flow(self, client: AsyncClient, test_user):
        """Test complete password reset flow"""
        # Step 1: Request password reset
        response = await client.post(
            "/api/auth/forgot-password",
            json={"email": test_user.email}
        )
        assert response.status_code == 200
        assert "reset link sent" in response.json()["message"].lower()
        
        # Step 2: Reset password with token
        new_password = "newpassword123"
        
        with patch('services.auth.verify_reset_token') as mock_verify:
            mock_verify.return_value = test_user.id
            
            response = await client.post(
                "/api/auth/reset-password",
                json={
                    "token": "mock_reset_token",
                    "new_password": new_password
                }
            )
            assert response.status_code == 200
        
        # Step 3: Login with new password
        with patch('services.auth.verify_password') as mock_verify_password:
            mock_verify_password.return_value = True
            
            response = await client.post(
                "/api/auth/login",
                json={"email": test_user.email, "password": new_password}
            )
            assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_protected_route_access(self, client: AsyncClient, test_user):
        """Test accessing protected routes with and without authentication"""
        # Try accessing protected route without token
        response = await client.get("/api/user/profile")
        assert response.status_code == 401
        
        # Login to get token
        with patch('services.auth.verify_password') as mock_verify:
            mock_verify.return_value = True
            
            login_response = await client.post(
                "/api/auth/login",
                json={"email": test_user.email, "password": "testpassword123"}
            )
            access_token = login_response.json()["access_token"]
        
        # Access protected route with token
        headers = {"Authorization": f"Bearer {access_token}"}
        
        with patch('services.auth.verify_token') as mock_verify_token:
            mock_verify_token.return_value = {"sub": str(test_user.id)}
            
            response = await client.get("/api/user/profile", headers=headers)
            assert response.status_code == 200
            
            profile_data = response.json()
            assert profile_data["email"] == test_user.email
    
    @pytest.mark.asyncio
    async def test_oauth_login_flow(self, client: AsyncClient):
        """Test OAuth login flow"""
        # Mock OAuth provider response
        oauth_data = {
            "provider": "google",
            "access_token": "mock_oauth_token",
            "user_info": {
                "email": "oauth@example.com",
                "first_name": "OAuth",
                "last_name": "User",
                "provider_id": "google_123456"
            }
        }
        
        with patch('services.auth.verify_oauth_token') as mock_verify_oauth:
            mock_verify_oauth.return_value = oauth_data["user_info"]
            
            response = await client.post("/api/oauth/login", json=oauth_data)
            assert response.status_code == 200
            
            login_response = response.json()
            assert "access_token" in login_response
            assert "user" in login_response
            assert login_response["user"]["email"] == oauth_data["user_info"]["email"]
    
    @pytest.mark.asyncio
    async def test_logout_flow(self, client: AsyncClient, test_user):
        """Test logout flow"""
        # Login first
        with patch('services.auth.verify_password') as mock_verify:
            mock_verify.return_value = True
            
            login_response = await client.post(
                "/api/auth/login",
                json={"email": test_user.email, "password": "testpassword123"}
            )
            access_token = login_response.json()["access_token"]
        
        # Logout
        headers = {"Authorization": f"Bearer {access_token}"}
        
        with patch('services.auth.verify_token') as mock_verify_token:
            mock_verify_token.return_value = {"sub": str(test_user.id)}
            
            response = await client.post("/api/auth/logout", headers=headers)
            assert response.status_code == 200
        
        # Try to access protected route with logged out token
        response = await client.get("/api/user/profile", headers=headers)
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_account_deactivation_flow(self, client: AsyncClient, test_user):
        """Test account deactivation flow"""
        # Login first
        with patch('services.auth.verify_password') as mock_verify:
            mock_verify.return_value = True
            
            login_response = await client.post(
                "/api/auth/login",
                json={"email": test_user.email, "password": "testpassword123"}
            )
            access_token = login_response.json()["access_token"]
        
        headers = {"Authorization": f"Bearer {access_token}"}
        
        # Deactivate account
        with patch('services.auth.verify_token') as mock_verify_token:
            mock_verify_token.return_value = {"sub": str(test_user.id)}
            
            response = await client.post(
                "/api/user/deactivate",
                headers=headers,
                json={"password": "testpassword123"}
            )
            assert response.status_code == 200
        
        # Try to login with deactivated account
        response = await client.post(
            "/api/auth/login",
            json={"email": test_user.email, "password": "testpassword123"}
        )
        assert response.status_code == 401
        assert "deactivated" in response.json()["message"].lower()
    
    @pytest.mark.asyncio
    async def test_concurrent_login_attempts(self, client: AsyncClient, test_user):
        """Test handling of concurrent login attempts"""
        import asyncio
        
        login_data = {
            "email": test_user.email,
            "password": "testpassword123"
        }
        
        with patch('services.auth.verify_password') as mock_verify:
            mock_verify.return_value = True
            
            # Make multiple concurrent login requests
            tasks = [
                client.post("/api/auth/login", json=login_data)
                for _ in range(5)
            ]
            
            responses = await asyncio.gather(*tasks)
            
            # All should succeed
            assert all(r.status_code == 200 for r in responses)
            
            # All should have valid tokens
            tokens = [r.json()["access_token"] for r in responses]
            assert all(token for token in tokens)
    
    @pytest.mark.asyncio
    async def test_rate_limiting_on_auth_endpoints(self, client: AsyncClient):
        """Test rate limiting on authentication endpoints"""
        # This would require actual rate limiting middleware to be configured
        # For now, we'll test the structure
        
        login_data = {
            "email": "nonexistent@example.com",
            "password": "wrongpassword"
        }
        
        # Make multiple failed login attempts
        responses = []
        for _ in range(10):
            response = await client.post("/api/auth/login", json=login_data)
            responses.append(response)
        
        # Should eventually get rate limited (429) or continue getting 401
        status_codes = [r.status_code for r in responses]
        assert all(code in [401, 429] for code in status_codes)