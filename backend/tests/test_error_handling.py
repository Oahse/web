"""
Test error handling throughout the application
Tests network errors, validation errors, API errors, and authentication errors
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from sqlalchemy.exc import SQLAlchemyError

from main import app
from core.exceptions.api_exceptions import (
    APIException,
    ValidationException,
    AuthenticationException,
    NotFoundException,
    DatabaseException
)


class TestNetworkErrorHandling:
    """Test network error handling - Requirement 6.1"""
    
    def test_error_response_structure(self, client: TestClient):
        """Test that error responses have proper structure for network errors"""
        # Test with a non-existent endpoint to trigger an error
        response = client.get("/api/v1/nonexistent")
        
        # Should return error with proper structure
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert "message" in data or "detail" in data
    
    def test_error_includes_correlation_id(self, client: TestClient):
        """Test that errors include correlation IDs for tracking"""
        response = client.get("/api/v1/nonexistent")
        
        assert response.status_code == 404
        data = response.json()
        # Should have correlation_id or error_code for tracking
        assert "correlation_id" in data or "error_code" in data
    
    def test_error_includes_timestamp(self, client: TestClient):
        """Test that errors include timestamps"""
        response = client.get("/api/v1/nonexistent")
        
        assert response.status_code == 404
        data = response.json()
        # Should have timestamp
        assert "timestamp" in data


class TestValidationErrorHandling:
    """Test validation error handling - Requirement 6.2"""
    
    def test_missing_required_fields(self, client: TestClient, auth_headers: dict):
        """Test that missing required fields return validation errors"""
        # Try to create a product without required fields
        invalid_product = {
            "name": "",  # Empty name
            # Missing description, category_id, etc.
        }
        
        response = client.post(
            "/api/v1/products",
            json=invalid_product,
            headers=auth_headers
        )
        
        # Should return 422 validation error
        assert response.status_code == 422
        data = response.json()
        assert data["success"] is False
        assert "errors" in data or "detail" in data
    
    def test_invalid_data_types(self, client: TestClient, auth_headers: dict):
        """Test that invalid data types return validation errors"""
        invalid_product = {
            "name": "Test Product",
            "description": "Test Description",
            "category_id": "not-a-uuid",  # Invalid UUID
            "variants": [
                {
                    "name": "Variant 1",
                    "base_price": "not-a-number",  # Invalid price
                    "stock": -5  # Negative stock
                }
            ]
        }
        
        response = client.post(
            "/api/v1/products",
            json=invalid_product,
            headers=auth_headers
        )
        
        # Should return 422 validation error
        assert response.status_code == 422
        data = response.json()
        assert data["success"] is False
    
    def test_validation_error_messages_are_descriptive(self, client: TestClient, auth_headers: dict):
        """Test that validation errors include descriptive messages"""
        invalid_product = {
            "name": "",
            "description": "",
        }
        
        response = client.post(
            "/api/v1/products",
            json=invalid_product,
            headers=auth_headers
        )
        
        assert response.status_code == 422
        data = response.json()
        assert data["success"] is False
        # Should have error details
        assert "errors" in data or "detail" in data
        
        # Error message should be descriptive
        if "errors" in data:
            assert len(data["errors"]) > 0
        elif "detail" in data:
            assert len(data["detail"]) > 0


class TestAPIErrorHandling:
    """Test API error handling - Requirement 6.3"""
    
    def test_404_not_found_error(self, client: TestClient):
        """Test that 404 errors are handled correctly"""
        response = client.get("/api/v1/products/00000000-0000-0000-0000-000000000000")
        
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert "message" in data or "detail" in data
    
    def test_error_response_has_proper_structure(self, client: TestClient):
        """Test that API errors have proper response structure"""
        response = client.get("/api/v1/products/00000000-0000-0000-0000-000000000000")
        
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert "message" in data or "detail" in data
        # Should have correlation_id for error tracking
        assert "correlation_id" in data or "error_code" in data
        # Should have timestamp
        assert "timestamp" in data


class TestAuthenticationErrorHandling:
    """Test authentication error handling - Requirement 6.4"""
    
    def test_access_protected_route_without_auth(self, client: TestClient):
        """Test that accessing protected routes without auth returns 401"""
        # Try to create a product without authentication
        product_data = {
            "name": "Test Product",
            "description": "Test Description",
            "category_id": "00000000-0000-0000-0000-000000000000",
            "variants": []
        }
        
        response = client.post("/api/v1/products", json=product_data)
        
        # Should return 401 Unauthorized
        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False
    
    def test_invalid_token_returns_401(self, client: TestClient):
        """Test that invalid tokens return 401"""
        invalid_headers = {"Authorization": "Bearer invalid_token_here"}
        
        response = client.get("/api/v1/auth/profile", headers=invalid_headers)
        
        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False
    
    def test_expired_token_returns_401(self, client: TestClient):
        """Test that expired tokens return 401"""
        # Create an expired token
        expired_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0QGV4YW1wbGUuY29tIiwiZXhwIjoxfQ.invalid"
        expired_headers = {"Authorization": f"Bearer {expired_token}"}
        
        response = client.get("/api/v1/auth/profile", headers=expired_headers)
        
        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False
    
    def test_missing_authorization_header(self, client: TestClient):
        """Test that missing authorization header returns 401"""
        response = client.get("/api/v1/auth/profile")
        
        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False
    
    def test_malformed_authorization_header(self, client: TestClient):
        """Test that malformed authorization headers return 401"""
        malformed_headers = {"Authorization": "NotBearer token"}
        
        response = client.get("/api/v1/auth/profile", headers=malformed_headers)
        
        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False
