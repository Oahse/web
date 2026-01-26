import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, patch, MagicMock
from core.utils.uuid_utils import uuid7
import aiohttp
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import directly to avoid circular imports
from services.tax import TaxService, TaxCalculationResult, TaxType


class TestTaxService:
    """Test suite for the enhanced TaxService with real API integration"""
    
    @pytest.fixture
    async def tax_service(self):
        """Create TaxService instance for testing"""
        mock_db = AsyncMock()
        service = TaxService(mock_db)
        yield service
        await service.close()
    
    @pytest.fixture
    def sample_address(self):
        """Create sample address for testing"""
        # Create a simple mock address object
        address = MagicMock()
        address.id = uuid7()
        address.street = "123 Main St"
        address.city = "San Francisco"
        address.state = "California"
        address.country = "United States"
        address.post_code = "94102"
        return address
    
    @pytest.mark.asyncio
    async def test_calculate_tax_with_address_id(self, tax_service, sample_address):
        """Test tax calculation using address ID"""
        # Mock database response
        tax_service.db.get = AsyncMock(return_value=sample_address)
        
        # Mock successful TaxJar API response
        with patch.object(tax_service, '_calculate_with_taxjar') as mock_taxjar:
            mock_result = TaxCalculationResult(
                tax_rate=0.0875,
                tax_amount=Decimal('8.75'),
                tax_type=TaxType.SALES_TAX,
                jurisdiction="CA, US",
                currency="USD"
            )
            mock_taxjar.return_value = mock_result
            
            result = await tax_service.calculate_tax(
                subtotal=Decimal('100.00'),
                shipping_address_id=sample_address.id
            )
            
            assert result.tax_rate == 0.0875
            assert result.tax_amount == Decimal('8.75')
            assert result.tax_type == TaxType.SALES_TAX
            assert result.jurisdiction == "CA, US"
            assert result.currency == "USD"
    
    @pytest.mark.asyncio
    async def test_calculate_tax_with_country_code(self, tax_service):
        """Test tax calculation using country code fallback"""
        with patch.object(tax_service, '_calculate_vat_with_api') as mock_vat:
            mock_result = TaxCalculationResult(
                tax_rate=0.20,
                tax_amount=Decimal('20.00'),
                tax_type=TaxType.VAT,
                jurisdiction="GB",
                currency="GBP"
            )
            mock_vat.return_value = mock_result
            
            result = await tax_service.calculate_tax(
                subtotal=Decimal('100.00'),
                country_code="GB",
                currency="GBP"
            )
            
            assert result.tax_rate == 0.20
            assert result.tax_amount == Decimal('20.00')
            assert result.tax_type == TaxType.VAT
            assert result.jurisdiction == "GB"
    
    @pytest.mark.asyncio
    async def test_calculate_tax_fallback_when_apis_fail(self, tax_service):
        """Test fallback to emergency rates when all APIs fail"""
        with patch.object(tax_service, '_calculate_with_real_services', return_value=None):
            result = await tax_service.calculate_tax(
                subtotal=Decimal('100.00'),
                country_code="US"
            )
            
            # Should use emergency fallback
            assert result.tax_rate == 0.08  # US emergency fallback rate
            assert result.tax_amount == Decimal('8.00')
            assert result.calculation_method == "emergency_fallback"
    
    @pytest.mark.asyncio
    async def test_calculate_vat_with_api_success(self, tax_service):
        """Test successful VAT calculation with API"""
        tax_service.vat_api_key = "test_key"
        
        # Mock successful API response
        mock_response_data = {
            "success": True,
            "standard_rate": 20.0,
            "country_code": "GB"
        }
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_response_data)
            mock_get.return_value.__aenter__.return_value = mock_response
            
            location_info = {"country_code": "GB"}
            result = await tax_service._calculate_vat_with_api(
                Decimal('100.00'), location_info, "GBP"
            )
            
            assert result is not None
            assert result.tax_rate == 0.20
            assert result.tax_amount == Decimal('20.00')
            assert result.tax_type == TaxType.VAT
            assert result.jurisdiction == "GB"
    
    @pytest.mark.asyncio
    async def test_calculate_with_taxjar_success(self, tax_service):
        """Test successful TaxJar API calculation"""
        tax_service.tax_api_key = "test_key"
        
        # Mock successful TaxJar response
        mock_response_data = {
            "tax": {
                "rate": 0.0875,
                "amount_to_collect": 8.75,
                "jurisdictions": {
                    "state": {
                        "tax_name": "CA State Sales Tax",
                        "tax_rate": 0.0625,
                        "tax_collectable": 6.25,
                        "jurisdiction_name": "California"
                    },
                    "county": {
                        "tax_name": "San Francisco County Tax",
                        "tax_rate": 0.025,
                        "tax_collectable": 2.50,
                        "jurisdiction_name": "San Francisco County"
                    }
                }
            }
        }
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_response_data)
            mock_post.return_value.__aenter__.return_value = mock_response
            
            location_info = {
                "country_code": "US",
                "state_code": "CA",
                "city": "San Francisco",
                "postal_code": "94102"
            }
            
            result = await tax_service._calculate_with_taxjar(
                Decimal('100.00'), location_info, "subscription", "USD"
            )
            
            assert result is not None
            assert result.tax_rate == 0.0875
            assert result.tax_amount == Decimal('8.75')
            assert result.tax_type == TaxType.SALES_TAX
            assert len(result.breakdown) == 2  # State and county taxes
    
    @pytest.mark.asyncio
    async def test_validate_tax_number_success(self, tax_service):
        """Test successful VAT number validation"""
        tax_service.vat_api_key = "test_key"
        
        mock_response_data = {
            "valid": True,
            "company_name": "Test Company Ltd",
            "company_address": "123 Test Street, London",
            "country_code": "GB",
            "vat_number": "GB123456789"
        }
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_response_data)
            mock_get.return_value.__aenter__.return_value = mock_response
            
            result = await tax_service.validate_tax_number("GB123456789", "GB")
            
            assert result["valid"] is True
            assert result["company_name"] == "Test Company Ltd"
            assert result["country_code"] == "GB"
    
    @pytest.mark.asyncio
    async def test_get_tax_rates_for_location_taxjar(self, tax_service):
        """Test getting tax rates for US location using TaxJar"""
        tax_service.tax_api_key = "test_key"
        
        mock_response_data = {
            "rate": {
                "combined_rate": 0.0875,
                "state_rate": 0.0625,
                "county_rate": 0.0125,
                "city_rate": 0.0125,
                "special_district_rate": 0.0
            }
        }
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_response_data)
            mock_get.return_value.__aenter__.return_value = mock_response
            
            result = await tax_service.get_tax_rates_for_location(
                country_code="US",
                state_code="CA",
                city="San Francisco",
                postal_code="94102"
            )
            
            assert result["combined_rate"] == 0.0875
            assert result["state_rate"] == 0.0625
            assert result["tax_type"] == "sales_tax"
            assert result["source"] == "taxjar_api"
    
    @pytest.mark.asyncio
    async def test_get_tax_rates_for_location_vat(self, tax_service):
        """Test getting VAT rates for EU location"""
        tax_service.vat_api_key = "test_key"
        
        mock_response_data = {
            "success": True,
            "standard_rate": 20.0,
            "reduced_rates": {
                "food": 5.0,
                "books": 0.0
            }
        }
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_response_data)
            mock_get.return_value.__aenter__.return_value = mock_response
            
            result = await tax_service.get_tax_rates_for_location(country_code="GB")
            
            assert result["standard_rate"] == 0.20  # Converted from percentage
            assert result["tax_type"] == "vat"
            assert result["source"] == "vat_api"
            assert "reduced_rates" in result
    
    def test_get_country_code_mapping(self, tax_service):
        """Test country name to code mapping"""
        assert tax_service._get_country_code("United States") == "US"
        assert tax_service._get_country_code("United Kingdom") == "GB"
        assert tax_service._get_country_code("Germany") == "DE"
        assert tax_service._get_country_code("Unknown Country") == "UN"
    
    def test_get_state_code_mapping(self, tax_service):
        """Test state name to code mapping"""
        assert tax_service._get_state_code("California") == "CA"
        assert tax_service._get_state_code("New York") == "NY"
        assert tax_service._get_state_code("Ontario") == "ON"
        assert tax_service._get_state_code("Unknown State") == "UN"
    
    def test_get_supported_currencies(self, tax_service):
        """Test supported currencies list"""
        currencies = tax_service.get_supported_currencies()
        
        assert "USD" in currencies
        assert "EUR" in currencies
        assert "GBP" in currencies
        assert currencies["USD"] == "$"
        assert currencies["EUR"] == "€"
        assert currencies["GBP"] == "£"
    
    def test_get_currency_for_country(self, tax_service):
        """Test currency mapping for countries"""
        assert tax_service.get_currency_for_country("US") == "USD"
        assert tax_service.get_currency_for_country("GB") == "GBP"
        assert tax_service.get_currency_for_country("DE") == "EUR"
        assert tax_service.get_currency_for_country("CA") == "CAD"
        assert tax_service.get_currency_for_country("XX") == "USD"  # Default
    
    def test_get_tax_type_for_country(self, tax_service):
        """Test tax type mapping for countries"""
        assert tax_service.get_tax_type_for_country("US") == TaxType.SALES_TAX
        assert tax_service.get_tax_type_for_country("CA") == TaxType.GST
        assert tax_service.get_tax_type_for_country("GB") == TaxType.VAT
        assert tax_service.get_tax_type_for_country("AU") == TaxType.GST
        assert tax_service.get_tax_type_for_country("DE") == TaxType.VAT
    
    def test_get_tax_code_for_product(self, tax_service):
        """Test product type to tax code mapping"""
        assert tax_service._get_tax_code_for_product("food") == "40030"
        assert tax_service._get_tax_code_for_product("clothing") == "20010"
        assert tax_service._get_tax_code_for_product("electronics") == "30070"
        assert tax_service._get_tax_code_for_product("subscription") == "31000"
        assert tax_service._get_tax_code_for_product("unknown") == "00000"
    
    @pytest.mark.asyncio
    async def test_error_handling_in_calculate_tax(self, tax_service):
        """Test error handling in tax calculation"""
        # Mock database error
        tax_service.db.get = AsyncMock(side_effect=Exception("Database error"))
        
        result = await tax_service.calculate_tax(
            subtotal=Decimal('100.00'),
            shipping_address_id=uuid7()
        )
        
        # Should return zero tax as ultimate fallback
        assert result.tax_rate == 0.0
        assert result.tax_amount == Decimal('0.00')
        assert result.calculation_method == "error_fallback"
    
    def test_tax_calculation_result_to_dict(self):
        """Test TaxCalculationResult serialization"""
        result = TaxCalculationResult(
            tax_rate=0.20,
            tax_amount=Decimal('20.00'),
            tax_type=TaxType.VAT,
            jurisdiction="GB",
            breakdown=[{"type": "VAT", "rate": 0.20, "amount": 20.00}],
            currency="GBP",
            calculation_method="vat_api"
        )
        
        data = result.to_dict()
        
        assert data["tax_rate"] == 0.20
        assert data["tax_amount"] == 20.00
        assert data["tax_type"] == "vat"
        assert data["jurisdiction"] == "GB"
        assert data["currency"] == "GBP"
        assert data["calculation_method"] == "vat_api"
        assert len(data["breakdown"]) == 1
        assert "calculated_at" in data


if __name__ == "__main__":
    pytest.main([__file__])