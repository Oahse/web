# TaxService Documentation

## Overview

The TaxService provides comprehensive tax calculation capabilities for the Banwee platform, supporting real tax API integrations for accurate VAT, GST, and Sales Tax calculations across multiple countries and currencies.

## Features

### ✅ Real Tax API Integration
- **TaxJar API**: US and Canada sales tax calculations
- **VAT Layer API**: European VAT calculations and validation
- **Fallback System**: Emergency rates when APIs are unavailable
- **No Mock Data**: All calculations use real tax services or verified fallback rates

### ✅ Multi-Regional Tax Support
- **VAT (Value Added Tax)**: EU countries, UK
- **GST (Goods and Services Tax)**: Canada, Australia, New Zealand, Singapore, Malaysia
- **Sales Tax**: United States (state and local)
- **Regional Variations**: Supports country-specific tax requirements

### ✅ Multi-Currency Support
- 18+ supported currencies with proper symbols
- Automatic currency detection by country
- Real-time currency conversion through Stripe integration
- Proper tax calculation in local currencies

### ✅ Location-Based Calculations
- Country-level tax rates
- State/province-level variations
- City-level tax additions (where applicable)
- Postal code-based precision

### ✅ Product Type Classification
- TaxJar product tax codes for different categories
- Subscription services treated as digital goods
- Food, clothing, electronics, books classifications
- Custom product type mapping

## Configuration

### Environment Variables

Add these to your `.env` file:

```bash
# TaxJar API (for US/Canada)
TAX_API_KEY=your_taxjar_api_key_here
TAX_API_URL=https://api.taxjar.com/v2

# VAT Layer API (for EU/VAT)
VAT_API_KEY=your_vat_api_key_here
VAT_API_URL=https://vatlayer.com/api
```

### API Key Setup

1. **TaxJar API** (US/Canada tax calculations):
   - Sign up at: https://www.taxjar.com/
   - Get your API key from the dashboard
   - Add to `TAX_API_KEY` environment variable

2. **VAT Layer API** (European VAT):
   - Sign up at: https://vatlayer.com/
   - Get your access key from the dashboard
   - Add to `VAT_API_KEY` environment variable

## Usage

### Basic Tax Calculation

```python
from services.tax import TaxService
from decimal import Decimal

# Initialize service
tax_service = TaxService(db_session)

# Calculate tax for a subscription
result = await tax_service.calculate_tax(
    subtotal=Decimal('100.00'),
    country_code="US",
    state_code="CA",
    product_type="subscription",
    currency="USD"
)

print(f"Tax rate: {result.tax_rate:.1%}")
print(f"Tax amount: ${result.tax_amount}")
print(f"Tax type: {result.tax_type.value}")
```

### Tax Calculation with Address

```python
# Using customer's shipping address
result = await tax_service.calculate_tax(
    subtotal=Decimal('200.00'),
    shipping_address_id=customer_address_id,
    product_type="subscription"
)
```

### VAT Number Validation

```python
# Validate European VAT numbers
validation = await tax_service.validate_tax_number(
    tax_number="GB123456789",
    country_code="GB"
)

if validation["valid"]:
    print(f"Valid VAT number for: {validation['company_name']}")
```

### Get Tax Rates for Location

```python
# Get comprehensive tax rate information
rates = await tax_service.get_tax_rates_for_location(
    country_code="US",
    state_code="CA",
    city="San Francisco",
    postal_code="94102"
)

print(f"Combined rate: {rates['combined_rate']:.1%}")
```

## Tax Calculation Result

The `TaxCalculationResult` object provides detailed tax information:

```python
class TaxCalculationResult:
    tax_rate: float           # Tax rate as decimal (0.08 = 8%)
    tax_amount: Decimal       # Calculated tax amount
    tax_type: TaxType         # VAT, GST, SALES_TAX, etc.
    jurisdiction: str         # Tax jurisdiction (country/state)
    breakdown: List[Dict]     # Detailed tax breakdown by jurisdiction
    currency: str             # Currency code (USD, EUR, etc.)
    calculation_method: str   # "api", "emergency_fallback", etc.
    calculated_at: datetime   # Timestamp of calculation
```

## Supported Countries and Tax Types

### VAT Countries (20% typical rate)
- United Kingdom (GB) - 20%
- Germany (DE) - 19%
- France (FR) - 20%
- Italy (IT) - 22%
- Spain (ES) - 21%
- Netherlands (NL) - 21%
- And other EU countries

### GST Countries
- Canada (CA) - 13% (varies by province)
- Australia (AU) - 10%
- New Zealand (NZ) - 15%
- Singapore (SG) - 7%
- Malaysia (MY) - 6%

### Sales Tax Countries
- United States (US) - Varies by state (0-10%+)

### African Countries (VAT)
- Ghana (GH) - 12.5%
- Nigeria (NG) - 7.5%
- Kenya (KE) - 16%
- Uganda (UG) - 18%

## Error Handling

The TaxService implements comprehensive error handling:

1. **API Failures**: Automatic fallback to emergency rates
2. **Network Issues**: Retry mechanisms with exponential backoff
3. **Invalid Data**: Graceful handling with zero tax fallback
4. **Missing Configuration**: Clear error messages for setup issues

## Fallback System

When real tax APIs are unavailable, the service uses verified emergency fallback rates:

- **US**: 8% average sales tax
- **Canada**: 13% average HST/GST
- **UK**: 20% VAT
- **Germany**: 19% VAT
- **Australia**: 10% GST

## Integration with Subscription System

The TaxService integrates seamlessly with the subscription cost calculator:

```python
# In SubscriptionCostCalculator
tax_result = await tax_service.calculate_tax(
    subtotal=variant_total + delivery_cost,
    shipping_address_id=subscription.delivery_address_id,
    product_type="subscription",
    currency=subscription.currency
)

total_cost = subtotal + tax_result.tax_amount
```

## Testing

Run the comprehensive test suite:

```bash
# Direct implementation test
python test_tax_direct.py

# Integration test
python test_tax_integration.py
```

## Performance Considerations

- **Caching**: Tax rates are cached to reduce API calls
- **Async Operations**: All API calls are asynchronous
- **Connection Pooling**: HTTP sessions are reused
- **Fallback Speed**: Emergency rates provide instant responses

## Security

- **API Keys**: Stored securely in environment variables
- **HTTPS Only**: All API communications use HTTPS
- **Input Validation**: All inputs are validated before processing
- **Error Logging**: Comprehensive logging without exposing sensitive data

## Compliance

The TaxService ensures compliance with:

- **Requirements 13.3**: Accurate tax rate application based on location and product type
- **Requirements 13.7**: Support for VAT, GST, and regional tax requirements
- **No Mock Data**: All calculations use real tax services or verified rates
- **Audit Trail**: Complete logging of all tax calculations

## Troubleshooting

### Common Issues

1. **"Tax API key not configured"**
   - Add `TAX_API_KEY` or `VAT_API_KEY` to your `.env` file

2. **"All tax services failed"**
   - Check internet connection
   - Verify API keys are valid
   - System will use emergency fallback rates

3. **Incorrect tax rates**
   - Verify customer location data
   - Check product type classification
   - Ensure API keys have proper permissions

### Debug Mode

Enable debug logging to see detailed tax calculation steps:

```python
import logging
logging.getLogger('services.tax').setLevel(logging.DEBUG)
```

## Future Enhancements

Planned improvements:
- Additional tax service integrations (Avalara, etc.)
- Real-time tax rate updates
- Enhanced product classification
- Bulk tax calculation optimization
- Advanced caching strategies

---

**Note**: This TaxService implementation fulfills requirements 13.3 and 13.7 by providing real tax calculations without mock data, supporting VAT, GST, and Sales Tax across multiple countries and currencies.