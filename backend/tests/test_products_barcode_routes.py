import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch
from core.utils.uuid_utils import uuid7
from main import app
from models.user import User


class TestProductsBarcodeRoutes:
    """Test cases for products barcode/QR code routes"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)

    @pytest.fixture
    def sample_variant_id(self):
        """Sample variant ID for testing"""
        return str(uuid7())

    @pytest.fixture
    def mock_admin_user(self):
        """Mock admin user"""
        user = MagicMock(spec=User)
        user.id = uuid7()
        user.email = "admin@test.com"
        user.role = "Admin"
        return user

    @pytest.fixture
    def mock_supplier_user(self):
        """Mock supplier user"""
        user = MagicMock(spec=User)
        user.id = uuid7()
        user.email = "supplier@test.com"
        user.role = "Supplier"
        return user

    @pytest.fixture
    def mock_customer_user(self):
        """Mock customer user"""
        user = MagicMock(spec=User)
        user.id = uuid7()
        user.email = "customer@test.com"
        user.role = "Customer"
        return user

    @pytest.fixture
    def auth_headers(self):
        """Mock authentication headers"""
        return {"Authorization": "Bearer mock_token"}

    def test_get_variant_qr_code_success(self, client, sample_variant_id):
        """Test successful QR code retrieval"""
        with patch('routes.products.ProductService') as mock_service:
            mock_instance = mock_service.return_value
            mock_instance.generate_qr_code = AsyncMock(return_value="data:image/png;base64,qr_code_data")

            response = client.get(f"/v1/products/variants/{sample_variant_id}/qrcode")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "qr_code_url" in data["data"]

    def test_get_variant_qr_code_not_found(self, client, sample_variant_id):
        """Test QR code retrieval for non-existent variant"""
        with patch('routes.products.ProductService') as mock_service:
            mock_instance = mock_service.return_value
            mock_instance.generate_qr_code = AsyncMock(return_value=None)

            response = client.get(f"/v1/products/variants/{sample_variant_id}/qrcode")
            
            assert response.status_code == 404
            data = response.json()
            assert "Product variant not found" in data["message"]

    def test_get_variant_barcode_success(self, client, sample_variant_id):
        """Test successful barcode retrieval"""
        with patch('routes.products.ProductService') as mock_service:
            mock_instance = mock_service.return_value
            mock_instance.generate_barcode = AsyncMock(return_value="data:image/png;base64,barcode_data")

            response = client.get(f"/v1/products/variants/{sample_variant_id}/barcode")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "barcode_url" in data["data"]

    def test_get_variant_barcode_not_found(self, client, sample_variant_id):
        """Test barcode retrieval for non-existent variant"""
        with patch('routes.products.ProductService') as mock_service:
            mock_instance = mock_service.return_value
            mock_instance.generate_barcode = AsyncMock(return_value=None)

            response = client.get(f"/v1/products/variants/{sample_variant_id}/barcode")
            
            assert response.status_code == 404
            data = response.json()
            assert "Product variant not found" in data["message"]

    def test_generate_variant_codes_admin_success(self, client, sample_variant_id, auth_headers, mock_admin_user):
        """Test successful code generation by admin"""
        with patch('routes.products.get_current_auth_user', return_value=mock_admin_user), \
             patch('routes.products.ProductService') as mock_service:
            
            mock_instance = mock_service.return_value
            mock_instance.generate_variant_codes = AsyncMock(return_value={
                "barcode": "data:image/png;base64,barcode_data",
                "qr_code": "data:image/png;base64,qr_code_data"
            })

            response = client.post(
                f"/v1/products/variants/{sample_variant_id}/codes/generate",
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "barcode" in data["data"]
            assert "qr_code" in data["data"]
            assert data["message"] == "Codes generated successfully"

    def test_generate_variant_codes_supplier_success(self, client, sample_variant_id, auth_headers, mock_supplier_user):
        """Test successful code generation by supplier"""
        with patch('routes.products.get_current_auth_user', return_value=mock_supplier_user), \
             patch('routes.products.ProductService') as mock_service:
            
            mock_instance = mock_service.return_value
            mock_instance.generate_variant_codes = AsyncMock(return_value={
                "barcode": "data:image/png;base64,barcode_data",
                "qr_code": "data:image/png;base64,qr_code_data"
            })

            response = client.post(
                f"/v1/products/variants/{sample_variant_id}/codes/generate",
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True

    def test_generate_variant_codes_customer_forbidden(self, client, sample_variant_id, auth_headers, mock_customer_user):
        """Test code generation forbidden for customer"""
        with patch('routes.products.get_current_auth_user', return_value=mock_customer_user):
            response = client.post(
                f"/v1/products/variants/{sample_variant_id}/codes/generate",
                headers=auth_headers
            )
            
            assert response.status_code == 403
            data = response.json()
            assert "Only suppliers and admins can generate codes" in data["message"]

    def test_generate_variant_codes_unauthenticated(self, client, sample_variant_id):
        """Test code generation without authentication"""
        response = client.post(f"/v1/products/variants/{sample_variant_id}/codes/generate")
        
        assert response.status_code == 401

    def test_update_variant_codes_success(self, client, sample_variant_id, auth_headers, mock_admin_user):
        """Test successful code update"""
        update_data = {
            "barcode": "data:image/png;base64,new_barcode_data",
            "qr_code": "data:image/png;base64,new_qr_code_data"
        }

        with patch('routes.products.get_current_auth_user', return_value=mock_admin_user), \
             patch('routes.products.ProductService') as mock_service:
            
            mock_instance = mock_service.return_value
            mock_instance.update_variant_codes = AsyncMock(return_value=update_data)

            response = client.put(
                f"/v1/products/variants/{sample_variant_id}/codes",
                json=update_data,
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["barcode"] == update_data["barcode"]
            assert data["data"]["qr_code"] == update_data["qr_code"]
            assert data["message"] == "Codes updated successfully"

    def test_update_variant_codes_partial_update(self, client, sample_variant_id, auth_headers, mock_admin_user):
        """Test partial code update (only barcode)"""
        update_data = {
            "barcode": "data:image/png;base64,new_barcode_data"
        }

        with patch('routes.products.get_current_auth_user', return_value=mock_admin_user), \
             patch('routes.products.ProductService') as mock_service:
            
            mock_instance = mock_service.return_value
            mock_instance.update_variant_codes = AsyncMock(return_value={
                "barcode": update_data["barcode"],
                "qr_code": "existing_qr_code"
            })

            response = client.put(
                f"/v1/products/variants/{sample_variant_id}/codes",
                json=update_data,
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["barcode"] == update_data["barcode"]

    def test_update_variant_codes_customer_forbidden(self, client, sample_variant_id, auth_headers, mock_customer_user):
        """Test code update forbidden for customer"""
        update_data = {"barcode": "new_barcode"}

        with patch('routes.products.get_current_auth_user', return_value=mock_customer_user):
            response = client.put(
                f"/v1/products/variants/{sample_variant_id}/codes",
                json=update_data,
                headers=auth_headers
            )
            
            assert response.status_code == 403
            data = response.json()
            assert "Only suppliers and admins can update codes" in data["message"]

    def test_update_variant_codes_empty_payload(self, client, sample_variant_id, auth_headers, mock_admin_user):
        """Test code update with empty payload"""
        with patch('routes.products.get_current_auth_user', return_value=mock_admin_user), \
             patch('routes.products.ProductService') as mock_service:
            
            mock_instance = mock_service.return_value
            mock_instance.update_variant_codes = AsyncMock(return_value={
                "barcode": None,
                "qr_code": None
            })

            response = client.put(
                f"/v1/products/variants/{sample_variant_id}/codes",
                json={},
                headers=auth_headers
            )
            
            assert response.status_code == 200

    def test_generate_variant_codes_service_error(self, client, sample_variant_id, auth_headers, mock_admin_user):
        """Test code generation with service error"""
        with patch('routes.products.get_current_auth_user', return_value=mock_admin_user), \
             patch('routes.products.ProductService') as mock_service:
            
            mock_instance = mock_service.return_value
            mock_instance.generate_variant_codes = AsyncMock(side_effect=Exception("Service error"))

            response = client.post(
                f"/v1/products/variants/{sample_variant_id}/codes/generate",
                headers=auth_headers
            )
            
            assert response.status_code == 500
            data = response.json()
            assert "Failed to generate codes" in data["message"]

    def test_update_variant_codes_service_error(self, client, sample_variant_id, auth_headers, mock_admin_user):
        """Test code update with service error"""
        update_data = {"barcode": "new_barcode"}

        with patch('routes.products.get_current_auth_user', return_value=mock_admin_user), \
             patch('routes.products.ProductService') as mock_service:
            
            mock_instance = mock_service.return_value
            mock_instance.update_variant_codes = AsyncMock(side_effect=Exception("Service error"))

            response = client.put(
                f"/v1/products/variants/{sample_variant_id}/codes",
                json=update_data,
                headers=auth_headers
            )
            
            assert response.status_code == 500
            data = response.json()
            assert "Failed to update codes" in data["message"]

    def test_invalid_variant_id_format(self, client, auth_headers, mock_admin_user):
        """Test with invalid UUID format"""
        invalid_id = "invalid-uuid"

        with patch('routes.products.get_current_auth_user', return_value=mock_admin_user):
            response = client.post(
                f"/v1/products/variants/{invalid_id}/codes/generate",
                headers=auth_headers
            )
            
            # Should return 422 for invalid UUID format
            assert response.status_code == 422


class TestProductsBarcodeRoutesIntegration:
    """Integration tests for barcode routes"""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_full_barcode_workflow(self, client, mock_admin_user):
        """Test complete barcode workflow: generate -> retrieve -> update"""
        variant_id = str(uuid7())
        auth_headers = {"Authorization": "Bearer mock_token"}

        with patch('routes.products.get_current_auth_user', return_value=mock_admin_user), \
             patch('routes.products.ProductService') as mock_service:
            
            mock_instance = mock_service.return_value
            
            # Step 1: Generate codes
            mock_instance.generate_variant_codes = AsyncMock(return_value={
                "barcode": "data:image/png;base64,generated_barcode",
                "qr_code": "data:image/png;base64,generated_qr_code"
            })

            generate_response = client.post(
                f"/v1/products/variants/{variant_id}/codes/generate",
                headers=auth_headers
            )
            assert generate_response.status_code == 200

            # Step 2: Retrieve QR code
            mock_instance.generate_qr_code = AsyncMock(return_value="data:image/png;base64,generated_qr_code")
            
            qr_response = client.get(f"/v1/products/variants/{variant_id}/qrcode")
            assert qr_response.status_code == 200

            # Step 3: Retrieve barcode
            mock_instance.generate_barcode = AsyncMock(return_value="data:image/png;base64,generated_barcode")
            
            barcode_response = client.get(f"/v1/products/variants/{variant_id}/barcode")
            assert barcode_response.status_code == 200

            # Step 4: Update codes
            mock_instance.update_variant_codes = AsyncMock(return_value={
                "barcode": "data:image/png;base64,updated_barcode",
                "qr_code": "data:image/png;base64,updated_qr_code"
            })

            update_response = client.put(
                f"/v1/products/variants/{variant_id}/codes",
                json={
                    "barcode": "data:image/png;base64,updated_barcode",
                    "qr_code": "data:image/png;base64,updated_qr_code"
                },
                headers=auth_headers
            )
            assert update_response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__])