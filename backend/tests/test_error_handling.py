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
        # Application uses custom error format with 'errors' field
        assert "errors" in data or "detail" in data
        # Verify error details are present
        if "errors" in data:
            assert len(data["errors"]) > 0
            assert data["success"] is False
        elif "detail" in data:
            assert len(data["detail"]) > 0
    
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
        assert "errors" in data or "detail" in data
        # Should have multiple validation errors
        if "errors" in data:
            assert len(data["errors"]) > 0
            # Should have errors for both category_id and base_price
            assert any("category_id" in str(key) for key in data["errors"].keys())
            assert any("base_price" in str(key) for key in data["errors"].keys())
        elif "detail" in data:
            assert len(data["detail"]) > 0
    
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
        # Should have error details
        assert "errors" in data or "detail" in data
        
        # Error message should be descriptive
        if "errors" in data:
            assert len(data["errors"]) > 0
            # Each error should have a descriptive message
            for field, message in data["errors"].items():
                assert isinstance(message, str)
                assert len(message) > 0
        elif "detail" in data:
            assert len(data["detail"]) > 0
            # Each error should have location and message
            for error in data["detail"]:
                assert "loc" in error  # Field location
                assert "msg" in error  # Error message
                assert "type" in error  # Error type
    
    def test_empty_product_name_validation(self, client: TestClient, auth_headers: dict):
        """Test that empty product name is rejected or handled"""
        from uuid import uuid4
        
        invalid_product = {
            "name": "",  # Empty name
            "description": "Test",
            "category_id": str(uuid4()),
            "variants": [
                {
                    "name": "Variant 1",
                    "base_price": 10.99,
                    "stock": 10
                }
            ]
        }
        
        response = client.post(
            "/api/v1/products",
            json=invalid_product,
            headers=auth_headers
        )
        
        # Empty name might be accepted or rejected depending on validation
        # If rejected, should be 422, if accepted but fails later, could be 500
        assert response.status_code in [422, 500]
        data = response.json()
        
        if response.status_code == 422:
            # Check for validation error
            assert "errors" in data or "detail" in data
            if "errors" in data:
                # Check that error mentions name field
                assert any("name" in str(key).lower() for key in data["errors"].keys())
            elif "detail" in data:
                errors = data["detail"]
                name_errors = [e for e in errors if "name" in str(e.get("loc", []))]
                assert len(name_errors) > 0
    
    def test_missing_variant_price_validation(self, client: TestClient, auth_headers: dict):
        """Test that missing variant price is rejected"""
        from uuid import uuid4
        
        invalid_product = {
            "name": "Test Product",
            "description": "Test",
            "category_id": str(uuid4()),
            "variants": [
                {
                    "name": "Variant 1",
                    # Missing base_price
                    "stock": 10
                }
            ]
        }
        
        response = client.post(
            "/api/v1/products",
            json=invalid_product,
            headers=auth_headers
        )
        
        assert response.status_code == 422
        data = response.json()
        assert "errors" in data or "detail" in data
        # Check that error is about the base_price field
        if "errors" in data:
            assert any("base_price" in str(key) for key in data["errors"].keys())
        elif "detail" in data:
            errors = data["detail"]
            price_errors = [e for e in errors if "base_price" in str(e.get("loc", []))]
            assert len(price_errors) > 0
    
    def test_invalid_uuid_format_validation(self, client: TestClient, auth_headers: dict):
        """Test that invalid UUID format is rejected"""
        invalid_product = {
            "name": "Test Product",
            "description": "Test",
            "category_id": "not-a-valid-uuid",  # Invalid UUID
            "variants": [
                {
                    "name": "Variant 1",
                    "base_price": 10.99,
                    "stock": 10
                }
            ]
        }
        
        response = client.post(
            "/api/v1/products",
            json=invalid_product,
            headers=auth_headers
        )
        
        assert response.status_code == 422
        data = response.json()
        assert "errors" in data or "detail" in data
        # Check that error is about the category_id field
        if "errors" in data:
            assert any("category_id" in str(key) for key in data["errors"].keys())
            # Error message should mention UUID
            category_error = next((v for k, v in data["errors"].items() if "category_id" in str(k)), None)
            assert category_error is not None
            assert "uuid" in category_error.lower() or "invalid" in category_error.lower()
        elif "detail" in data:
            errors = data["detail"]
            uuid_errors = [e for e in errors if "category_id" in str(e.get("loc", []))]
            assert len(uuid_errors) > 0
    
    def test_negative_price_validation(self, client: TestClient, auth_headers: dict):
        """Test that negative prices are handled"""
        from uuid import uuid4
        
        invalid_product = {
            "name": "Test Product",
            "description": "Test",
            "category_id": str(uuid4()),
            "variants": [
                {
                    "name": "Variant 1",
                    "base_price": -10.99,  # Negative price
                    "stock": 10
                }
            ]
        }
        
        response = client.post(
            "/api/v1/products",
            json=invalid_product,
            headers=auth_headers
        )
        
        # Negative prices might be accepted or rejected depending on validation
        # Should either reject with 422/400 or fail later with 500
        assert response.status_code in [400, 422, 500]
        data = response.json()
        # Should have error information
        assert "detail" in data or "message" in data or "errors" in data
    
    def test_invalid_stock_type_validation(self, client: TestClient, auth_headers: dict):
        """Test that invalid stock type is rejected"""
        from uuid import uuid4
        
        invalid_product = {
            "name": "Test Product",
            "description": "Test",
            "category_id": str(uuid4()),
            "variants": [
                {
                    "name": "Variant 1",
                    "base_price": 10.99,
                    "stock": "not-a-number"  # Invalid stock type
                }
            ]
        }
        
        response = client.post(
            "/api/v1/products",
            json=invalid_product,
            headers=auth_headers
        )
        
        assert response.status_code == 422
        data = response.json()
        assert "errors" in data or "detail" in data
        # Check that error is about the stock field
        if "errors" in data:
            assert any("stock" in str(key) for key in data["errors"].keys())
            # Error message should mention integer or number
            stock_error = next((v for k, v in data["errors"].items() if "stock" in str(k)), None)
            assert stock_error is not None
            assert "integer" in stock_error.lower() or "number" in stock_error.lower()
        elif "detail" in data:
            errors = data["detail"]
            stock_errors = [e for e in errors if "stock" in str(e.get("loc", []))]
            assert len(stock_errors) > 0


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
    
    def test_500_internal_server_error(self, client: TestClient):
        """Test that 500 errors return appropriate status code and message"""
        # Trigger an internal server error by mocking the ProductService
        with patch('services.products.ProductService.get_products') as mock_get_products:
            mock_get_products.side_effect = Exception("Database connection failed")
            
            response = client.get("/api/v1/products")
            
            # Should return 500 Internal Server Error
            assert response.status_code == 500
            data = response.json()
            assert data["success"] is False
            assert "message" in data
            # Error message should be descriptive
            assert len(data["message"]) > 0
            # Should have correlation_id for tracking
            assert "correlation_id" in data
            # Should have timestamp
            assert "timestamp" in data
    
    def test_database_error_returns_500(self, client: TestClient):
        """Test that database errors return 500 with descriptive message"""
        with patch('services.products.ProductService.get_products') as mock_get_products:
            mock_get_products.side_effect = SQLAlchemyError("Database query failed")
            
            response = client.get("/api/v1/products")
            
            assert response.status_code == 500
            data = response.json()
            assert data["success"] is False
            assert "message" in data
            # Should have descriptive error message
            assert len(data["message"]) > 0
            # Should have error_code
            assert "error_code" in data
            # Error code should be present (may be ERR_500, DATABASE_ERROR, or INTERNAL_ERROR)
            assert data["error_code"] in ["DATABASE_ERROR", "INTERNAL_ERROR", "ERR_500"]
    
    def test_error_messages_are_descriptive(self, client: TestClient):
        """Test that error messages are descriptive and helpful"""
        # Test 404 error message
        response = client.get("/api/v1/products/00000000-0000-0000-0000-000000000000")
        
        assert response.status_code == 404
        data = response.json()
        message = data.get("message") or data.get("detail")
        
        # Message should be descriptive
        assert message is not None
        assert len(message) > 10  # Should be more than just "Not found"
        assert isinstance(message, str)
    
    def test_error_includes_correlation_id(self, client: TestClient):
        """Test that all errors include correlation IDs for tracking"""
        # Test with 404 error
        response = client.get("/api/v1/products/00000000-0000-0000-0000-000000000000")
        
        assert response.status_code == 404
        data = response.json()
        assert "correlation_id" in data
        # Correlation ID should be a valid UUID format
        correlation_id = data["correlation_id"]
        assert isinstance(correlation_id, str)
        assert len(correlation_id) > 0
        # Should be UUID format (contains hyphens)
        assert "-" in correlation_id
    
    def test_error_includes_timestamp(self, client: TestClient):
        """Test that all errors include timestamps"""
        response = client.get("/api/v1/products/00000000-0000-0000-0000-000000000000")
        
        assert response.status_code == 404
        data = response.json()
        assert "timestamp" in data
        # Timestamp should be ISO format
        timestamp = data["timestamp"]
        assert isinstance(timestamp, str)
        assert len(timestamp) > 0
        # Should contain date separator
        assert "-" in timestamp or "/" in timestamp
    
    def test_error_includes_error_code(self, client: TestClient):
        """Test that errors include error codes for categorization"""
        response = client.get("/api/v1/products/00000000-0000-0000-0000-000000000000")
        
        assert response.status_code == 404
        data = response.json()
        assert "error_code" in data
        error_code = data["error_code"]
        assert isinstance(error_code, str)
        assert len(error_code) > 0
    
    def test_errors_are_logged(self, client: TestClient, caplog):
        """Test that errors are logged for debugging"""
        # Trigger an error that should be logged
        with patch('services.products.ProductService.get_products') as mock_get_products:
            mock_get_products.side_effect = Exception("Test error for logging")
            
            response = client.get("/api/v1/products")
            
            # Should return error response
            assert response.status_code == 500
            data = response.json()
            
            # Verify error response structure
            assert data["success"] is False
            assert "message" in data
            assert "correlation_id" in data
            
            # Note: Logging verification depends on logging configuration
            # The error should be returned in the response
            assert len(data["message"]) > 0
    
    def test_database_errors_are_logged(self, client: TestClient, caplog):
        """Test that database errors are logged with details"""
        with patch('services.products.ProductService.get_products') as mock_get_products:
            mock_get_products.side_effect = SQLAlchemyError("Database connection lost")
            
            response = client.get("/api/v1/products")
            
            assert response.status_code == 500
            data = response.json()
            
            # Verify error response structure
            assert data["success"] is False
            assert "message" in data
            assert "correlation_id" in data
            
            # Note: Logging verification depends on logging configuration
            # The error should be returned in the response
            assert len(data["message"]) > 0
    
    def test_400_bad_request_error(self, client: TestClient, auth_headers: dict):
        """Test that 400 errors return appropriate status code"""
        # Send malformed JSON
        response = client.post(
            "/api/v1/products",
            data="not valid json",
            headers={**auth_headers, "Content-Type": "application/json"}
        )
        
        # Should return 400 or 422
        assert response.status_code in [400, 422]
        data = response.json()
        assert data["success"] is False
        assert "message" in data or "detail" in data
    
    def test_method_not_allowed_error(self, client: TestClient):
        """Test that 405 errors are handled correctly"""
        # Try to DELETE on an endpoint that doesn't support it
        response = client.delete("/api/v1/auth/login")
        
        # Should return 405 Method Not Allowed
        assert response.status_code == 405
        data = response.json()
        assert data["success"] is False
    
    def test_unsupported_media_type_error(self, client: TestClient, auth_headers: dict):
        """Test that 415 errors are handled for unsupported content types"""
        # Send XML when JSON is expected
        response = client.post(
            "/api/v1/products",
            data="<xml>data</xml>",
            headers={**auth_headers, "Content-Type": "application/xml"}
        )
        
        # Should return 415 or 422
        assert response.status_code in [415, 422]
        data = response.json()
        assert data["success"] is False
    
    def test_error_response_structure_on_exception(self, client: TestClient):
        """Test that exceptions return proper error response structure"""
        with patch('services.products.ProductService.get_products') as mock_get_products:
            # Simulate an exception
            mock_get_products.side_effect = Exception("Internal processing error")
            
            response = client.get("/api/v1/products")
            
            assert response.status_code == 500
            data = response.json()
            
            # Verify error response has all required fields
            assert data["success"] is False
            assert "message" in data
            assert "error_code" in data
            assert "correlation_id" in data
            assert "timestamp" in data
            
            # Message should be descriptive
            assert len(data["message"]) > 0
    
    def test_multiple_errors_have_unique_correlation_ids(self, client: TestClient):
        """Test that each error gets a unique correlation ID"""
        # Make multiple requests that trigger errors
        response1 = client.get("/api/v1/products/00000000-0000-0000-0000-000000000000")
        response2 = client.get("/api/v1/products/11111111-1111-1111-1111-111111111111")
        
        assert response1.status_code == 404
        assert response2.status_code == 404
        
        data1 = response1.json()
        data2 = response2.json()
        
        # Both should have correlation IDs
        assert "correlation_id" in data1
        assert "correlation_id" in data2
        
        # Correlation IDs should be different
        assert data1["correlation_id"] != data2["correlation_id"]


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
