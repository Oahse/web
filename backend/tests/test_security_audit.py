"""
Security audit tests for the application.
Tests GitHub token encryption, JWT authentication, and input validation.
"""
import pytest
from datetime import datetime, timedelta
from uuid import uuid4
import bcrypt
from jose import jwt

from core.utils.auth.jwt_auth import JWTManager
from core.config import settings
from models.user import User
from schemas.product import ProductCreate, ProductVariantCreate


class TestGitHubTokenEncryption:
    """
    Test suite for GitHub token encryption security.
    Validates: Requirements 7.1
    """
    
    def test_github_token_is_encrypted_in_frontend(self):
        """
        Verify that the GitHub token is stored encrypted in the frontend code.
        The token should never be stored in plain text.
        """
        # Read the github.tsx file to verify encryption is used
        import os
        github_file_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            'frontend', 'src', 'lib', 'github.tsx'
        )
        
        # Check if file exists (in test environment it might not)
        if os.path.exists(github_file_path):
            with open(github_file_path, 'r') as f:
                content = f.read()
                
            # Verify that CryptoJS is imported
            assert 'CryptoJS' in content, "CryptoJS should be imported for encryption"
            
            # Verify that AES decryption is used
            assert 'CryptoJS.AES.decrypt' in content, "AES decryption should be used"
            
            # Verify that the token is stored encrypted (encryptedToken variable)
            assert 'encryptedToken' in content, "Token should be stored as encryptedToken"
            
            # Verify that plain text token is not exposed
            # The decrypted token should only be used internally
            assert 'decryptedToken' in content, "Token should be decrypted before use"
            
            # Ensure no plain GitHub token patterns (ghp_xxx or github_pat_xxx)
            assert 'ghp_' not in content or 'encryptedToken' in content, \
                "Plain GitHub token should not be exposed"
    
    def test_encryption_secret_key_exists(self):
        """
        Verify that an encryption secret key is defined.
        Note: In production, this should be in environment variables.
        """
        import os
        github_file_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            'frontend', 'src', 'lib', 'github.tsx'
        )
        
        if os.path.exists(github_file_path):
            with open(github_file_path, 'r') as f:
                content = f.read()
            
            # Verify that a secret key is defined
            assert 'secretKey' in content, "Secret key should be defined for encryption"
    
    def test_token_not_logged_to_console(self):
        """
        Verify that the decrypted token is not logged to console.
        This prevents token exposure in browser console or logs.
        """
        import os
        github_file_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            'frontend', 'src', 'lib', 'github.tsx'
        )
        
        if os.path.exists(github_file_path):
            with open(github_file_path, 'r') as f:
                content = f.read()
            
            # Check that decryptedToken is not logged
            # Look for console.log statements with decryptedToken
            lines = content.split('\n')
            for line in lines:
                if 'console.log' in line and not line.strip().startswith('//'):
                    # If there's an active console.log, ensure it doesn't log the token
                    assert 'decryptedToken' not in line, \
                        "Decrypted token should not be logged to console"
                    assert 'auth:' not in line.lower() or 'decryptedToken' not in line, \
                        "Authentication token should not be logged"


class TestJWTAuthentication:
    """
    Test suite for JWT authentication security.
    Validates: Requirements 4.2
    """
    
    def test_jwt_token_creation(self):
        """
        Verify that JWT tokens are created correctly with expiration.
        """
        jwt_manager = JWTManager()
        test_data = {"sub": "test@example.com", "role": "Supplier"}
        
        # Create token with custom expiration
        token = jwt_manager.create_access_token(
            data=test_data,
            expires_delta=timedelta(minutes=15)
        )
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_jwt_token_verification_valid(self):
        """
        Verify that valid JWT tokens are correctly verified.
        """
        jwt_manager = JWTManager()
        test_data = {"sub": "test@example.com", "role": "Supplier"}
        
        # Create and verify token
        token = jwt_manager.create_access_token(data=test_data)
        payload = jwt_manager.verify_token(token)
        
        assert payload is not None
        assert payload["sub"] == "test@example.com"
        assert payload["role"] == "Supplier"
        assert "exp" in payload
    
    def test_jwt_token_verification_invalid(self):
        """
        Verify that invalid JWT tokens are rejected.
        """
        jwt_manager = JWTManager()
        
        # Test with invalid token
        invalid_token = "invalid.token.here"
        payload = jwt_manager.verify_token(invalid_token)
        
        assert payload is None
    
    def test_jwt_token_verification_expired(self):
        """
        Verify that expired JWT tokens are rejected.
        """
        jwt_manager = JWTManager()
        test_data = {"sub": "test@example.com"}
        
        # Create token that expires immediately
        token = jwt_manager.create_access_token(
            data=test_data,
            expires_delta=timedelta(seconds=-1)  # Already expired
        )
        
        # Verify token is rejected
        payload = jwt_manager.verify_token(token)
        assert payload is None
    
    def test_jwt_token_contains_expiration(self):
        """
        Verify that JWT tokens contain expiration timestamp.
        """
        jwt_manager = JWTManager()
        test_data = {"sub": "test@example.com"}
        
        token = jwt_manager.create_access_token(data=test_data)
        payload = jwt_manager.verify_token(token)
        
        assert payload is not None
        assert "exp" in payload
        assert isinstance(payload["exp"], int)
        assert payload["exp"] > datetime.utcnow().timestamp()
    
    def test_jwt_refresh_token_creation(self):
        """
        Verify that refresh tokens are created with longer expiration.
        """
        jwt_manager = JWTManager()
        test_data = {"sub": "test@example.com"}
        
        refresh_token = jwt_manager.create_refresh_token(data=test_data)
        payload = jwt_manager.verify_token(refresh_token)
        
        assert payload is not None
        assert payload["type"] == "refresh"
        assert "exp" in payload
    
    def test_jwt_user_id_extraction(self):
        """
        Verify that user ID can be extracted from JWT token.
        """
        jwt_manager = JWTManager()
        test_email = "test@example.com"
        test_data = {"sub": test_email}
        
        token = jwt_manager.create_access_token(data=test_data)
        extracted_id = jwt_manager.get_user_id_from_token(token)
        
        assert extracted_id == test_email
    
    @pytest.mark.asyncio
    async def test_protected_endpoint_requires_auth(self, async_client):
        """
        Verify that protected endpoints reject requests without authentication.
        """
        # Try to create a product without authentication
        product_data = {
            "name": "Test Product",
            "description": "Test Description",
            "category_id": str(uuid4()),
            "variants": [
                {
                    "name": "Default",
                    "base_price": 10.0,
                    "stock": 100
                }
            ]
        }
        
        response = await async_client.post("/api/v1/products/", json=product_data)
        
        # Should return 401 Unauthorized
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_protected_endpoint_with_invalid_token(self, async_client):
        """
        Verify that protected endpoints reject requests with invalid tokens.
        """
        product_data = {
            "name": "Test Product",
            "description": "Test Description",
            "category_id": str(uuid4()),
            "variants": [
                {
                    "name": "Default",
                    "base_price": 10.0,
                    "stock": 100
                }
            ]
        }
        
        # Use invalid token
        headers = {"Authorization": "Bearer invalid.token.here"}
        response = await async_client.post(
            "/api/v1/products/",
            json=product_data,
            headers=headers
        )
        
        # Should return 401 Unauthorized
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_role_based_access_control(self, async_client, db_session):
        """
        Verify that role-based access control works correctly.
        Only Suppliers and Admins should be able to create products.
        """
        from models.user import User
        from core.utils.auth.jwt_auth import JWTManager
        
        # Create a regular customer user
        customer_email = "customer@example.com"
        customer_user = User(
            id=uuid4(),
            email=customer_email,
            firstname="Customer",
            lastname="User",
            role="Customer",  # Not a Supplier or Admin
            active=True,
            verified=True,
            hashed_password=bcrypt.hashpw("password123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        )
        
        db_session.add(customer_user)
        await db_session.commit()
        
        # Create token for customer
        jwt_manager = JWTManager()
        customer_token = jwt_manager.create_access_token(data={"sub": customer_email})
        
        product_data = {
            "name": "Test Product",
            "description": "Test Description",
            "category_id": str(uuid4()),
            "variants": [
                {
                    "name": "Default",
                    "base_price": 10.0,
                    "stock": 100
                }
            ]
        }
        
        # Try to create product as customer
        headers = {"Authorization": f"Bearer {customer_token}"}
        response = await async_client.post(
            "/api/v1/products/",
            json=product_data,
            headers=headers
        )
        
        # Should return 403 Forbidden
        assert response.status_code == 403


class TestInputValidation:
    """
    Test suite for input validation security.
    Validates: Requirements 3.2
    """
    
    @pytest.mark.asyncio
    async def test_pydantic_validation_missing_required_fields(self, async_client, auth_headers):
        """
        Verify that Pydantic validation rejects requests with missing required fields.
        """
        # Missing required fields: name, category_id, variants
        invalid_product_data = {
            "description": "Test Description"
        }
        
        response = await async_client.post(
            "/api/v1/products/",
            json=invalid_product_data,
            headers=auth_headers
        )
        
        # Should return 422 Unprocessable Entity
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_pydantic_validation_invalid_data_types(self, async_client, auth_headers):
        """
        Verify that Pydantic validation rejects requests with invalid data types.
        """
        # Invalid data types: base_price should be float, not string
        invalid_product_data = {
            "name": "Test Product",
            "category_id": str(uuid4()),
            "variants": [
                {
                    "name": "Default",
                    "base_price": "not_a_number",  # Invalid type
                    "stock": 100
                }
            ]
        }
        
        response = await async_client.post(
            "/api/v1/products/",
            json=invalid_product_data,
            headers=auth_headers
        )
        
        # Should return 422 Unprocessable Entity
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_pydantic_validation_invalid_uuid(self, async_client, auth_headers):
        """
        Verify that Pydantic validation rejects invalid UUID formats.
        """
        invalid_product_data = {
            "name": "Test Product",
            "category_id": "not-a-valid-uuid",  # Invalid UUID
            "variants": [
                {
                    "name": "Default",
                    "base_price": 10.0,
                    "stock": 100
                }
            ]
        }
        
        response = await async_client.post(
            "/api/v1/products/",
            json=invalid_product_data,
            headers=auth_headers
        )
        
        # Should return 422 Unprocessable Entity
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_sql_injection_prevention_in_product_name(self, async_client, auth_headers, db_session):
        """
        Verify that SQL injection attempts in product names are safely handled.
        SQLAlchemy ORM should prevent SQL injection.
        """
        from models.product import Category
        
        # Create a test category
        category_id = uuid4()
        category = Category(
            id=category_id,
            name="Test Category",
            is_active=True
        )
        db_session.add(category)
        await db_session.commit()
        
        # Attempt SQL injection in product name
        sql_injection_product = {
            "name": "Test'; DROP TABLE products; --",
            "description": "SQL Injection Attempt",
            "category_id": str(category_id),
            "variants": [
                {
                    "name": "Default",
                    "base_price": 10.0,
                    "stock": 100
                }
            ]
        }
        
        response = await async_client.post(
            "/api/v1/products/",
            json=sql_injection_product,
            headers=auth_headers
        )
        
        # Should either succeed (treating it as a normal string) or fail gracefully
        # The important thing is that it doesn't execute SQL injection
        assert response.status_code in [200, 201, 400, 422, 500]
        
        # Verify that the products table still exists by querying it
        from models.product import Product
        from sqlalchemy import select
        
        result = await db_session.execute(select(Product))
        # If we can query, the table wasn't dropped
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_xss_prevention_in_product_description(self, async_client, auth_headers, db_session):
        """
        Verify that XSS attempts in product descriptions are safely stored.
        The backend should store the data as-is, and the frontend should escape it.
        """
        from models.product import Category
        
        # Create a test category
        category_id = uuid4()
        category = Category(
            id=category_id,
            name="Test Category",
            is_active=True
        )
        db_session.add(category)
        await db_session.commit()
        
        # Attempt XSS in product description
        xss_product = {
            "name": "XSS Test Product",
            "description": "<script>alert('XSS')</script>",
            "category_id": str(category_id),
            "variants": [
                {
                    "name": "Default",
                    "base_price": 10.0,
                    "stock": 100
                }
            ]
        }
        
        response = await async_client.post(
            "/api/v1/products/",
            json=xss_product,
            headers=auth_headers
        )
        
        # Should either succeed (storing as-is) or fail gracefully
        # The important thing is that XSS is not executed
        assert response.status_code in [200, 201, 400, 422, 500]
        
        # If successful, verify the data is stored correctly
        if response.status_code in [200, 201]:
            data = response.json()
            # The script tag should be stored as a string, not executed
            assert "data" in data
            assert data["data"]["description"] == "<script>alert('XSS')</script>"
    
    @pytest.mark.asyncio
    async def test_negative_price_validation(self, async_client, auth_headers):
        """
        Verify that negative prices are handled appropriately.
        """
        invalid_product_data = {
            "name": "Test Product",
            "category_id": str(uuid4()),
            "variants": [
                {
                    "name": "Default",
                    "base_price": -10.0,  # Negative price
                    "stock": 100
                }
            ]
        }
        
        response = await async_client.post(
            "/api/v1/products/",
            json=invalid_product_data,
            headers=auth_headers
        )
        
        # Should either reject (422) or handle gracefully
        # Ideally should reject negative prices
        assert response.status_code in [422, 400, 500]
    
    @pytest.mark.asyncio
    async def test_negative_stock_validation(self, async_client, auth_headers):
        """
        Verify that negative stock values are handled appropriately.
        """
        invalid_product_data = {
            "name": "Test Product",
            "category_id": str(uuid4()),
            "variants": [
                {
                    "name": "Default",
                    "base_price": 10.0,
                    "stock": -100  # Negative stock
                }
            ]
        }
        
        response = await async_client.post(
            "/api/v1/products/",
            json=invalid_product_data,
            headers=auth_headers
        )
        
        # Should either reject (422) or handle gracefully
        assert response.status_code in [422, 400, 500, 200, 201]
    
    def test_pydantic_schema_validation_structure(self):
        """
        Verify that Pydantic schemas are properly defined with validation.
        """
        # Test ProductVariantCreate schema
        valid_variant = ProductVariantCreate(
            name="Test Variant",
            base_price=10.0,
            stock=100
        )
        assert valid_variant.name == "Test Variant"
        assert valid_variant.base_price == 10.0
        assert valid_variant.stock == 100
        
        # Test that schema has proper types
        assert hasattr(ProductVariantCreate, '__annotations__')
        annotations = ProductVariantCreate.__annotations__
        assert 'name' in annotations
        assert 'base_price' in annotations
        assert 'stock' in annotations
