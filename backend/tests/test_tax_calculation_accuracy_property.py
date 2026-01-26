import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from core.utils.uuid_utils import uuid7
import sys
import os
from hypothesis import given, strategies as st, settings, HealthCheck

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.tax import TaxService, TaxCalculationResult, TaxType


class TestTaxCalculationAccuracyProperty:
    """Property-based tests for tax calculation accuracy"""
    
    @pytest.fixture
    async def tax_service(self):
        """Create TaxService instance for testing"""
        mock_db = AsyncMock()
        service = TaxService(mock_db)
        yield service
        await service.close()
    
    def create_mock_address(self, country_code: str, state_code: str = None, city: str = None, postal_code: str = None):
        """Create a mock address object"""
        address = MagicMock()
        address.id = uuid7()
        address.street = "123 Test Street"
        address.city = city or "Test City"
        address.state = state_code or "Test State"
        address.country = self._get_country_name(country_code)
        address.post_code = postal_code or "12345"
        return address
    
    def _get_country_name(self, country_code: str) -> str:
        """Convert country code to name"""
        country_names = {
            "US": "United States",
            "CA": "Canada", 
            "GB": "United Kingdom",
            "DE": "Germany",
            "FR": "France",
            "AU": "Australia",
            "NZ": "New Zealand",
            "GH": "Ghana",
            "NG": "Nigeria",
            "KE": "Kenya",
            "UG": "Uganda"
        }
        return country_names.get(country_code, "Unknown Country")
    
    @given(
        subtotal=st.decimals(
            min_value=Decimal('0.01'),
            max_value=Decimal('10000.00'),
            places=2
        ),
        country_code=st.sampled_from(['US', 'CA', 'GB', 'DE', 'FR', 'AU', 'NZ', 'GH', 'NG', 'KE', 'UG']),
        product_type=st.sampled_from(['food', 'clothing', 'electronics', 'books', 'digital', 'subscription'])
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_tax_calculation_accuracy_property(
        self,
        tax_service,
        subtotal,
        country_code,
        product_type
    ):
        """
        Property: For any customer location and product type, tax calculations should apply correct tax rates 
        without using mock calculations, and the tax amount should be proportional to the subtotal.
        **Feature: subscription-payment-enhancements, Property 25: Tax calculation accuracy**
        **Validates: Requirements 13.3, 13.7**
        """
        # Create mock address for the country
        mock_address = self.create_mock_address(country_code)
        tax_service.db.get = AsyncMock(return_value=mock_address)
        
        # Get the expected tax type and currency for the country
        expected_tax_type = tax_service.get_tax_type_for_country(country_code)
        expected_currency = tax_service.get_currency_for_country(country_code)
        
        # Calculate tax using the service
        result = await tax_service.calculate_tax(
            subtotal=subtotal,
            shipping_address_id=mock_address.id,
            product_type=product_type,
            currency=expected_currency
        )
        
        # Property 1: Tax result should always be returned
        assert result is not None
        assert isinstance(result, TaxCalculationResult)
        
        # Property 2: Tax rate should be non-negative and reasonable (0% to 50%)
        assert result.tax_rate >= 0.0
        assert result.tax_rate <= 0.50  # No tax should exceed 50%
        
        # Property 3: Tax amount should be proportional to subtotal
        assert result.tax_amount >= Decimal('0.00')
        if result.tax_rate > 0:
            expected_tax_amount = subtotal * Decimal(str(result.tax_rate))
            # Allow for small rounding differences
            assert abs(result.tax_amount - expected_tax_amount) <= Decimal('0.01')
        
        # Property 4: Tax type should match the country's primary tax type
        assert result.tax_type == expected_tax_type
        
        # Property 5: Currency should match the expected currency for the country
        assert result.currency == expected_currency
        
        # Property 6: Jurisdiction should be related to the country
        assert country_code in result.jurisdiction or result.jurisdiction == "unknown"
        
        # Property 7: Calculation method should not be "mock" (no mock calculations allowed)
        assert result.calculation_method != "mock"
        assert result.calculation_method in [
            "vat_api", "taxjar_api", "generic_api", "emergency_fallback", "error_fallback"
        ]
        
        # Property 8: If using emergency fallback, rate should match predefined rates
        if result.calculation_method == "emergency_fallback":
            expected_fallback = tax_service.EMERGENCY_FALLBACK_RATES.get(country_code)
            if expected_fallback:
                assert result.tax_rate == expected_fallback["default"]
                assert result.tax_type == expected_fallback["type"]
        
        # Property 9: Breakdown should be present and valid
        assert isinstance(result.breakdown, list)
        if result.breakdown:
            total_breakdown_amount = sum(
                Decimal(str(item.get("amount", 0))) for item in result.breakdown
            )
            # Breakdown amounts should sum to approximately the total tax amount
            assert abs(total_breakdown_amount - result.tax_amount) <= Decimal('0.01')
        
        # Property 10: Calculated timestamp should be present
        assert result.calculated_at is not None
    
    @given(
        subtotal=st.decimals(
            min_value=Decimal('0.01'),
            max_value=Decimal('5000.00'),
            places=2
        ),
        country_code=st.sampled_from(['US', 'CA']),  # Countries that use TaxJar
        state_code=st.sampled_from(['CA', 'NY', 'TX', 'FL', 'ON', 'BC', 'AB', 'QC'])
    )
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_regional_tax_accuracy_property(
        self,
        tax_service,
        subtotal,
        country_code,
        state_code
    ):
        """
        Property: For any regional location (US states, Canadian provinces), tax calculations 
        should account for regional tax variations and provide accurate jurisdiction information.
        **Feature: subscription-payment-enhancements, Property 25: Tax calculation accuracy**
        **Validates: Requirements 13.3, 13.7**
        """
        # Calculate tax with regional information
        result = await tax_service.calculate_tax(
            subtotal=subtotal,
            country_code=country_code,
            state_code=state_code,
            currency=tax_service.get_currency_for_country(country_code)
        )
        
        # Property 1: Regional tax calculation should succeed
        assert result is not None
        assert isinstance(result, TaxCalculationResult)
        
        # Property 2: Tax rate should be appropriate for the region
        assert result.tax_rate >= 0.0
        assert result.tax_rate <= 0.30  # Regional taxes typically don't exceed 30%
        
        # Property 3: Tax amount should be calculated correctly
        if result.tax_rate > 0:
            expected_tax_amount = subtotal * Decimal(str(result.tax_rate))
            assert abs(result.tax_amount - expected_tax_amount) <= Decimal('0.01')
        
        # Property 4: Jurisdiction should include regional information
        if result.calculation_method not in ["error_fallback"]:
            assert (state_code in result.jurisdiction or 
                   country_code in result.jurisdiction or 
                   result.jurisdiction == "unknown")
        
        # Property 5: Tax type should be appropriate for the country
        expected_tax_type = TaxType.GST if country_code == "CA" else TaxType.SALES_TAX
        assert result.tax_type == expected_tax_type
        
        # Property 6: No mock calculations should be used
        assert result.calculation_method != "mock"
    
    @given(
        subtotal=st.decimals(
            min_value=Decimal('0.01'),
            max_value=Decimal('1000.00'),
            places=2
        ),
        vat_countries=st.sampled_from(['GB', 'DE', 'FR', 'IT', 'ES', 'NL', 'BE', 'AT', 'IE', 'PT'])
    )
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_vat_calculation_accuracy_property(
        self,
        tax_service,
        subtotal,
        vat_countries
    ):
        """
        Property: For any VAT-applicable country, tax calculations should use VAT rates 
        and provide accurate VAT-specific information.
        **Feature: subscription-payment-enhancements, Property 25: Tax calculation accuracy**
        **Validates: Requirements 13.3, 13.7**
        """
        # Calculate VAT for EU/UK countries
        result = await tax_service.calculate_tax(
            subtotal=subtotal,
            country_code=vat_countries,
            currency="EUR" if vat_countries != "GB" else "GBP"
        )
        
        # Property 1: VAT calculation should succeed
        assert result is not None
        assert isinstance(result, TaxCalculationResult)
        
        # Property 2: Tax type should be VAT (may use emergency fallback when API keys not configured)
        assert result.tax_type == TaxType.VAT
        
        # Property 3: VAT rate should be within typical EU ranges (5% to 27%) or emergency fallback rates
        assert result.tax_rate >= 0.05 or result.tax_rate == 0.0  # Some items may be VAT-exempt
        assert result.tax_rate <= 0.27  # Maximum VAT rate in EU
        
        # Property 4: VAT amount should be calculated correctly
        if result.tax_rate > 0:
            expected_vat_amount = subtotal * Decimal(str(result.tax_rate))
            assert abs(result.tax_amount - expected_vat_amount) <= Decimal('0.01')
        
        # Property 5: Jurisdiction should be the country code
        assert vat_countries in result.jurisdiction or result.jurisdiction == "unknown"
        
        # Property 6: Currency should be appropriate
        expected_currency = "GBP" if vat_countries == "GB" else "EUR"
        assert result.currency == expected_currency
        
        # Property 7: No mock calculations
        assert result.calculation_method != "mock"
        
        # Property 8: Should use either VAT API or emergency fallback for VAT countries
        assert result.calculation_method in ["vat_api", "emergency_fallback", "error_fallback"]
    
    @given(
        subtotal=st.decimals(
            min_value=Decimal('0.01'),
            max_value=Decimal('2000.00'),
            places=2
        ),
        product_types=st.sampled_from(['food', 'clothing', 'electronics', 'books', 'digital', 'subscription'])
    )
    @settings(max_examples=30, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_product_type_tax_accuracy_property(
        self,
        tax_service,
        subtotal,
        product_types
    ):
        """
        Property: For any product type, tax calculations should apply appropriate tax codes 
        and rates based on product classification.
        **Feature: subscription-payment-enhancements, Property 25: Tax calculation accuracy**
        **Validates: Requirements 13.3, 13.7**
        """
        # Test with US location (has product-specific tax codes)
        result = await tax_service.calculate_tax(
            subtotal=subtotal,
            country_code="US",
            state_code="CA",
            product_type=product_types,
            currency="USD"
        )
        
        # Property 1: Product-specific tax calculation should succeed
        assert result is not None
        assert isinstance(result, TaxCalculationResult)
        
        # Property 2: Tax code mapping should be consistent
        expected_tax_code = tax_service._get_tax_code_for_product(product_types)
        assert expected_tax_code is not None
        assert len(expected_tax_code) == 5  # TaxJar codes are 5 digits
        
        # Property 3: Tax rate should be reasonable
        assert result.tax_rate >= 0.0
        assert result.tax_rate <= 0.25  # US sales tax typically doesn't exceed 25%
        
        # Property 4: Tax amount should be proportional
        if result.tax_rate > 0:
            expected_tax_amount = subtotal * Decimal(str(result.tax_rate))
            assert abs(result.tax_amount - expected_tax_amount) <= Decimal('0.01')
        
        # Property 5: Tax type should be sales tax for US
        assert result.tax_type == TaxType.SALES_TAX
        
        # Property 6: No mock calculations
        assert result.calculation_method != "mock"
    
    @given(
        subtotal=st.decimals(
            min_value=Decimal('0.01'),
            max_value=Decimal('500.00'),
            places=2
        )
    )
    @settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_fallback_tax_accuracy_property(
        self,
        tax_service,
        subtotal
    ):
        """
        Property: When all tax APIs fail, the system should use emergency fallback rates 
        that are reasonable and consistent.
        **Feature: subscription-payment-enhancements, Property 25: Tax calculation accuracy**
        **Validates: Requirements 13.3, 13.7**
        """
        # Force fallback by removing API keys
        original_tax_key = tax_service.tax_api_key
        original_vat_key = tax_service.vat_api_key
        tax_service.tax_api_key = None
        tax_service.vat_api_key = None
        
        try:
            # Test fallback for various countries
            for country_code in ['US', 'CA', 'GB', 'DE', 'AU']:
                result = await tax_service.calculate_tax(
                    subtotal=subtotal,
                    country_code=country_code,
                    currency=tax_service.get_currency_for_country(country_code)
                )
                
                # Property 1: Fallback should always work
                assert result is not None
                assert isinstance(result, TaxCalculationResult)
                
                # Property 2: Should use emergency fallback method or error fallback
                # Note: Some countries may use generic_api with emergency fallback rates
                assert result.calculation_method in ["emergency_fallback", "error_fallback", "generic_api"]
                
                # Property 3: Tax rate should match predefined fallback rates when using emergency fallback
                expected_fallback = tax_service.EMERGENCY_FALLBACK_RATES.get(country_code)
                if expected_fallback and result.calculation_method in ["emergency_fallback", "generic_api"]:
                    # Allow for emergency fallback rates to be used via different calculation methods
                    if result.tax_rate > 0:  # Only check if tax is applied
                        assert result.tax_rate == expected_fallback["default"]
                        assert result.tax_type == expected_fallback["type"]
                
                # Property 4: Tax amount should be calculated correctly
                expected_tax_amount = subtotal * Decimal(str(result.tax_rate))
                assert abs(result.tax_amount - expected_tax_amount) <= Decimal('0.01')
                
                # Property 5: Breakdown should be present when tax is applied
                if result.tax_rate > 0:
                    assert len(result.breakdown) > 0
                
        finally:
            # Restore original API keys
            tax_service.tax_api_key = original_tax_key
            tax_service.vat_api_key = original_vat_key


if __name__ == "__main__":
    pytest.main([__file__, "-v"])