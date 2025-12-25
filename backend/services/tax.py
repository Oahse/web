from typing import Dict, Optional, List, Any
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.user import Address
from uuid import UUID
import aiohttp
import logging
import os
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class TaxType(Enum):
    """Enumeration of supported tax types"""
    VAT = "vat"  # Value Added Tax (EU, UK, etc.)
    GST = "gst"  # Goods and Services Tax (Canada, Australia, etc.)
    SALES_TAX = "sales_tax"  # US State Sales Tax
    EXCISE = "excise"  # Excise tax
    CUSTOMS = "customs"  # Import/customs duties


class TaxCalculationResult:
    """Result of tax calculation with detailed breakdown"""
    
    def __init__(
        self,
        tax_rate: float,
        tax_amount: Decimal,
        tax_type: TaxType,
        jurisdiction: str,
        breakdown: List[Dict[str, Any]] = None,
        currency: str = "USD",
        calculation_method: str = "api"
    ):
        self.tax_rate = tax_rate
        self.tax_amount = tax_amount
        self.tax_type = tax_type
        self.jurisdiction = jurisdiction
        self.breakdown = breakdown or []
        self.currency = currency
        self.calculation_method = calculation_method
        self.calculated_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "tax_rate": self.tax_rate,
            "tax_amount": float(self.tax_amount),
            "tax_type": self.tax_type.value,
            "jurisdiction": self.jurisdiction,
            "breakdown": self.breakdown,
            "currency": self.currency,
            "calculation_method": self.calculation_method,
            "calculated_at": self.calculated_at.isoformat()
        }


class TaxService:
    """Enhanced service for calculating taxes using real tax APIs and services"""
    
    # Fallback tax rates for emergency use only (when all APIs fail)
    EMERGENCY_FALLBACK_RATES = {
        "US": {"default": 0.08, "type": TaxType.SALES_TAX},
        "CA": {"default": 0.13, "type": TaxType.GST},
        "GB": {"default": 0.20, "type": TaxType.VAT},
        "DE": {"default": 0.19, "type": TaxType.VAT},
        "FR": {"default": 0.20, "type": TaxType.VAT},
        "IT": {"default": 0.22, "type": TaxType.VAT},
        "ES": {"default": 0.21, "type": TaxType.VAT},
        "NL": {"default": 0.21, "type": TaxType.VAT},
        "BE": {"default": 0.21, "type": TaxType.VAT},
        "AT": {"default": 0.20, "type": TaxType.VAT},
        "IE": {"default": 0.23, "type": TaxType.VAT},
        "PT": {"default": 0.23, "type": TaxType.VAT},
        "FI": {"default": 0.24, "type": TaxType.VAT},
        "SE": {"default": 0.25, "type": TaxType.VAT},
        "DK": {"default": 0.25, "type": TaxType.VAT},
        "AU": {"default": 0.10, "type": TaxType.GST},
        "NZ": {"default": 0.15, "type": TaxType.GST},
        "GH": {"default": 0.125, "type": TaxType.VAT},
        "NG": {"default": 0.075, "type": TaxType.VAT},
        "KE": {"default": 0.16, "type": TaxType.VAT},
        "UG": {"default": 0.18, "type": TaxType.VAT}
    }
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.tax_api_key = os.getenv('TAX_API_KEY')  # For services like TaxJar, Avalara
        self.tax_api_url = os.getenv('TAX_API_URL', 'https://api.taxjar.com/v2')
        self.vat_api_url = os.getenv('VAT_API_URL', 'https://vatlayer.com/api')
        self.vat_api_key = os.getenv('VAT_API_KEY')
        self.session = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session"""
        if not self.session:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def calculate_tax(
        self, 
        subtotal: Decimal, 
        shipping_address_id: Optional[UUID] = None,
        country_code: Optional[str] = None,
        state_code: Optional[str] = None,
        product_type: Optional[str] = None,
        currency: str = "USD"
    ) -> TaxCalculationResult:
        """
        Calculate tax amount using real tax services with fallback mechanisms.
        
        Args:
            subtotal: The subtotal amount before tax
            shipping_address_id: ID of the shipping address
            country_code: ISO country code (fallback if no address)
            state_code: State/province code (fallback if no address)
            product_type: Type of product for tax classification
            currency: Currency code for the calculation
            
        Returns:
            TaxCalculationResult with detailed tax information
        """
        try:
            # Get location information
            location_info = await self._get_location_info(
                shipping_address_id, country_code, state_code
            )
            
            # Try real tax calculation services in order of preference
            tax_result = await self._calculate_with_real_services(
                subtotal, location_info, product_type, currency
            )
            
            if tax_result:
                return tax_result
            
            # Fallback to emergency rates if all services fail
            logger.warning("All tax services failed, using emergency fallback rates")
            return await self._calculate_with_fallback(
                subtotal, location_info, currency
            )
            
        except Exception as e:
            logger.error(f"Tax calculation error: {str(e)}")
            # Return zero tax as ultimate fallback
            return TaxCalculationResult(
                tax_rate=0.0,
                tax_amount=Decimal('0.00'),
                tax_type=TaxType.SALES_TAX,
                jurisdiction="unknown",
                currency=currency,
                calculation_method="error_fallback"
            )
    
    async def _get_location_info(
        self,
        shipping_address_id: Optional[UUID],
        country_code: Optional[str],
        state_code: Optional[str]
    ) -> Dict[str, Any]:
        """Get comprehensive location information for tax calculation"""
        location_info = {
            "country_code": country_code,
            "state_code": state_code,
            "city": None,
            "postal_code": None,
            "full_address": None
        }
        
        # Get detailed address if provided
        if shipping_address_id:
            address = await self.db.get(Address, shipping_address_id)
            if address:
                location_info.update({
                    "country_code": self._get_country_code(address.country),
                    "state_code": self._get_state_code(address.state),
                    "city": address.city,
                    "postal_code": address.post_code,
                    "full_address": f"{address.street}, {address.city}, {address.state}, {address.country}"
                })
        
        return location_info
    
    async def _calculate_with_real_services(
        self,
        subtotal: Decimal,
        location_info: Dict[str, Any],
        product_type: Optional[str],
        currency: str
    ) -> Optional[TaxCalculationResult]:
        """Try calculating tax with real tax services"""
        
        country_code = location_info.get("country_code")
        
        # Try VAT calculation for EU/UK countries
        if country_code in ["GB", "DE", "FR", "IT", "ES", "NL", "BE", "AT", "IE", "PT", "FI", "SE", "DK"]:
            vat_result = await self._calculate_vat_with_api(subtotal, location_info, currency)
            if vat_result:
                return vat_result
        
        # Try TaxJar or similar service for US/CA
        if country_code in ["US", "CA"]:
            taxjar_result = await self._calculate_with_taxjar(subtotal, location_info, product_type, currency)
            if taxjar_result:
                return taxjar_result
        
        # Try generic tax API for other countries
        generic_result = await self._calculate_with_generic_api(subtotal, location_info, currency)
        if generic_result:
            return generic_result
        
        return None
    
    async def _calculate_vat_with_api(
        self,
        subtotal: Decimal,
        location_info: Dict[str, Any],
        currency: str
    ) -> Optional[TaxCalculationResult]:
        """Calculate VAT using VAT API service"""
        if not self.vat_api_key:
            logger.warning("VAT API key not configured")
            return None
        
        try:
            session = await self._get_session()
            country_code = location_info.get("country_code")
            
            # Get VAT rate for country
            url = f"{self.vat_api_url}/rate"
            params = {
                "access_key": self.vat_api_key,
                "country_code": country_code,
                "amount": float(subtotal),
                "currency": currency
            }
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("success"):
                        vat_rate = data.get("standard_rate", 0) / 100  # Convert percentage to decimal
                        vat_amount = subtotal * Decimal(str(vat_rate))
                        
                        return TaxCalculationResult(
                            tax_rate=vat_rate,
                            tax_amount=vat_amount,
                            tax_type=TaxType.VAT,
                            jurisdiction=country_code,
                            breakdown=[{
                                "type": "VAT",
                                "rate": vat_rate,
                                "amount": float(vat_amount),
                                "jurisdiction": country_code
                            }],
                            currency=currency,
                            calculation_method="vat_api"
                        )
        
        except Exception as e:
            logger.error(f"VAT API calculation failed: {str(e)}")
        
        return None
    
    async def _calculate_with_taxjar(
        self,
        subtotal: Decimal,
        location_info: Dict[str, Any],
        product_type: Optional[str],
        currency: str
    ) -> Optional[TaxCalculationResult]:
        """Calculate tax using TaxJar API"""
        if not self.tax_api_key:
            logger.warning("TaxJar API key not configured")
            return None
        
        try:
            session = await self._get_session()
            
            # Prepare TaxJar request
            headers = {
                "Authorization": f"Token token=\"{self.tax_api_key}\"",
                "Content-Type": "application/json"
            }
            
            payload = {
                "amount": float(subtotal),
                "shipping": 0,  # Shipping handled separately
                "to_country": location_info.get("country_code"),
                "to_state": location_info.get("state_code"),
                "to_city": location_info.get("city"),
                "to_zip": location_info.get("postal_code")
            }
            
            # Add product category if provided
            if product_type:
                payload["product_tax_code"] = self._get_tax_code_for_product(product_type)
            
            url = f"{self.tax_api_url}/taxes"
            
            async with session.post(url, json=payload, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    tax_info = data.get("tax", {})
                    
                    tax_rate = tax_info.get("rate", 0)
                    tax_amount = Decimal(str(tax_info.get("amount_to_collect", 0)))
                    
                    # Determine tax type based on jurisdiction
                    tax_type = TaxType.GST if location_info.get("country_code") == "CA" else TaxType.SALES_TAX
                    
                    # Build breakdown from jurisdictions
                    breakdown = []
                    for jurisdiction in tax_info.get("jurisdictions", {}).values():
                        if jurisdiction.get("tax_collectable", 0) > 0:
                            breakdown.append({
                                "type": jurisdiction.get("tax_name", "Tax"),
                                "rate": jurisdiction.get("tax_rate", 0),
                                "amount": jurisdiction.get("tax_collectable", 0),
                                "jurisdiction": jurisdiction.get("jurisdiction_name", "Unknown")
                            })
                    
                    return TaxCalculationResult(
                        tax_rate=tax_rate,
                        tax_amount=tax_amount,
                        tax_type=tax_type,
                        jurisdiction=f"{location_info.get('state_code', '')}, {location_info.get('country_code', '')}",
                        breakdown=breakdown,
                        currency=currency,
                        calculation_method="taxjar_api"
                    )
        
        except Exception as e:
            logger.error(f"TaxJar API calculation failed: {str(e)}")
        
        return None
    
    async def _calculate_with_generic_api(
        self,
        subtotal: Decimal,
        location_info: Dict[str, Any],
        currency: str
    ) -> Optional[TaxCalculationResult]:
        """Calculate tax using a generic tax API service"""
        # This would integrate with other tax services like Avalara, etc.
        # For now, we'll implement a basic structure that can be extended
        
        try:
            # Example integration with a hypothetical generic tax API
            # This can be replaced with actual service integration
            country_code = location_info.get("country_code")
            
            # For demonstration, we'll use a simple lookup for known tax rates
            # In production, this would call a real API
            if country_code in ["AU", "NZ", "SG", "MY"]:
                # These countries typically use GST
                tax_rate = await self._get_gst_rate_for_country(country_code)
                if tax_rate:
                    tax_amount = subtotal * Decimal(str(tax_rate))
                    
                    return TaxCalculationResult(
                        tax_rate=tax_rate,
                        tax_amount=tax_amount,
                        tax_type=TaxType.GST,
                        jurisdiction=country_code,
                        breakdown=[{
                            "type": "GST",
                            "rate": tax_rate,
                            "amount": float(tax_amount),
                            "jurisdiction": country_code
                        }],
                        currency=currency,
                        calculation_method="generic_api"
                    )
            
            # Handle VAT countries when VAT API is not available
            elif country_code in ["GB", "DE", "FR", "IT", "ES", "NL", "BE", "AT", "IE", "PT", "FI", "SE", "DK"]:
                # Use fallback VAT rates when API is not available
                fallback_info = self.EMERGENCY_FALLBACK_RATES.get(country_code)
                if fallback_info and fallback_info["type"] == TaxType.VAT:
                    tax_rate = fallback_info["default"]
                    tax_amount = subtotal * Decimal(str(tax_rate))
                    
                    return TaxCalculationResult(
                        tax_rate=tax_rate,
                        tax_amount=tax_amount,
                        tax_type=TaxType.VAT,
                        jurisdiction=country_code,
                        breakdown=[{
                            "type": "VAT",
                            "rate": tax_rate,
                            "amount": float(tax_amount),
                            "jurisdiction": country_code,
                            "note": "Emergency fallback rate used"
                        }],
                        currency=currency,
                        calculation_method="emergency_fallback"
                    )
        
        except Exception as e:
            logger.error(f"Generic tax API calculation failed: {str(e)}")
        
        return None
    
    async def _get_gst_rate_for_country(self, country_code: str) -> Optional[float]:
        """Get GST rate for specific countries"""
        gst_rates = {
            "AU": 0.10,  # 10% GST in Australia
            "NZ": 0.15,  # 15% GST in New Zealand
            "SG": 0.07,  # 7% GST in Singapore
            "MY": 0.06   # 6% GST in Malaysia
        }
        return gst_rates.get(country_code)
    
    async def _calculate_with_fallback(
        self,
        subtotal: Decimal,
        location_info: Dict[str, Any],
        currency: str
    ) -> TaxCalculationResult:
        """Calculate tax using emergency fallback rates"""
        country_code = location_info.get("country_code", "US")
        
        fallback_info = self.EMERGENCY_FALLBACK_RATES.get(country_code, 
                                                         self.EMERGENCY_FALLBACK_RATES["US"])
        
        tax_rate = fallback_info["default"]
        tax_type = fallback_info["type"]
        tax_amount = subtotal * Decimal(str(tax_rate))
        
        return TaxCalculationResult(
            tax_rate=tax_rate,
            tax_amount=tax_amount,
            tax_type=tax_type,
            jurisdiction=country_code,
            breakdown=[{
                "type": tax_type.value.upper(),
                "rate": tax_rate,
                "amount": float(tax_amount),
                "jurisdiction": country_code,
                "note": "Emergency fallback rate used"
            }],
            currency=currency,
            calculation_method="emergency_fallback"
        )
    
    def _get_tax_code_for_product(self, product_type: str) -> str:
        """Map product types to tax codes for API services"""
        tax_code_mapping = {
            "food": "40030",  # TaxJar code for food
            "clothing": "20010",  # TaxJar code for clothing
            "electronics": "30070",  # TaxJar code for electronics
            "books": "81100",  # TaxJar code for books
            "digital": "31000",  # TaxJar code for digital goods
            "subscription": "31000"  # Treat subscriptions as digital goods
        }
        return tax_code_mapping.get(product_type.lower(), "00000")  # Default general merchandise
    
    async def validate_tax_number(
        self,
        tax_number: str,
        country_code: str
    ) -> Dict[str, Any]:
        """Validate VAT/tax numbers using real validation services"""
        try:
            if not self.vat_api_key:
                return {"valid": False, "error": "VAT validation service not configured"}
            
            session = await self._get_session()
            
            url = f"{self.vat_api_url}/validate"
            params = {
                "access_key": self.vat_api_key,
                "vat_number": tax_number,
                "country_code": country_code
            }
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "valid": data.get("valid", False),
                        "company_name": data.get("company_name"),
                        "company_address": data.get("company_address"),
                        "country_code": data.get("country_code"),
                        "vat_number": data.get("vat_number")
                    }
        
        except Exception as e:
            logger.error(f"VAT validation failed: {str(e)}")
        
        return {"valid": False, "error": "Validation service unavailable"}
    
    async def get_tax_rates_for_location(
        self,
        country_code: str,
        state_code: Optional[str] = None,
        city: Optional[str] = None,
        postal_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get comprehensive tax rate information for a location"""
        try:
            location_info = {
                "country_code": country_code,
                "state_code": state_code,
                "city": city,
                "postal_code": postal_code
            }
            
            # Try to get rates from real services
            if self.tax_api_key and country_code in ["US", "CA"]:
                return await self._get_taxjar_rates(location_info)
            
            elif self.vat_api_key and country_code in ["GB", "DE", "FR", "IT", "ES"]:
                return await self._get_vat_rates(location_info)
            
            # Fallback to emergency rates
            fallback_info = self.EMERGENCY_FALLBACK_RATES.get(country_code)
            if fallback_info:
                return {
                    "country_code": country_code,
                    "standard_rate": fallback_info["default"],
                    "tax_type": fallback_info["type"].value,
                    "source": "fallback"
                }
            
            return {"error": "No tax information available for this location"}
        
        except Exception as e:
            logger.error(f"Failed to get tax rates: {str(e)}")
            return {"error": str(e)}
    
    async def _get_taxjar_rates(self, location_info: Dict[str, Any]) -> Dict[str, Any]:
        """Get tax rates from TaxJar API"""
        try:
            session = await self._get_session()
            
            headers = {
                "Authorization": f"Token token=\"{self.tax_api_key}\"",
                "Content-Type": "application/json"
            }
            
            params = {
                "country": location_info.get("country_code"),
                "state": location_info.get("state_code"),
                "city": location_info.get("city"),
                "zip": location_info.get("postal_code")
            }
            
            url = f"{self.tax_api_url}/rates/{location_info.get('postal_code', '00000')}"
            
            async with session.get(url, params=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    rate_info = data.get("rate", {})
                    
                    return {
                        "country_code": location_info.get("country_code"),
                        "state_code": location_info.get("state_code"),
                        "combined_rate": rate_info.get("combined_rate", 0),
                        "state_rate": rate_info.get("state_rate", 0),
                        "county_rate": rate_info.get("county_rate", 0),
                        "city_rate": rate_info.get("city_rate", 0),
                        "special_rate": rate_info.get("special_district_rate", 0),
                        "tax_type": "sales_tax",
                        "source": "taxjar_api"
                    }
        
        except Exception as e:
            logger.error(f"TaxJar rates lookup failed: {str(e)}")
        
        return {"error": "Failed to retrieve tax rates"}
    
    async def _get_vat_rates(self, location_info: Dict[str, Any]) -> Dict[str, Any]:
        """Get VAT rates from VAT API"""
        try:
            session = await self._get_session()
            
            url = f"{self.vat_api_url}/rate"
            params = {
                "access_key": self.vat_api_key,
                "country_code": location_info.get("country_code")
            }
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("success"):
                        return {
                            "country_code": location_info.get("country_code"),
                            "standard_rate": data.get("standard_rate", 0) / 100,
                            "reduced_rates": data.get("reduced_rates", {}),
                            "tax_type": "vat",
                            "source": "vat_api"
                        }
        
        except Exception as e:
            logger.error(f"VAT rates lookup failed: {str(e)}")
        
        return {"error": "Failed to retrieve VAT rates"}
    
    def _get_country_code(self, country_name: str) -> str:
        """Convert country name to ISO code"""
        country_mapping = {
            "United States": "US",
            "USA": "US",
            "United States of America": "US",
            "Canada": "CA",
            "United Kingdom": "GB",
            "UK": "GB",
            "Great Britain": "GB",
            "Germany": "DE",
            "Deutschland": "DE",
            "France": "FR",
            "Ghana": "GH",
            "Nigeria": "NG",
            "Kenya": "KE",
            "Uganda": "UG",
            "Australia": "AU",
            "New Zealand": "NZ",
            "Singapore": "SG",
            "Malaysia": "MY",
            "Italy": "IT",
            "Spain": "ES",
            "Netherlands": "NL",
            "Belgium": "BE",
            "Austria": "AT",
            "Ireland": "IE",
            "Portugal": "PT",
            "Finland": "FI",
            "Sweden": "SE",
            "Denmark": "DK"
        }
        return country_mapping.get(country_name, country_name[:2].upper())
    
    def _get_state_code(self, state_name: str) -> str:
        """Convert state name to code"""
        state_mapping = {
            # US States
            "California": "CA",
            "New York": "NY",
            "Texas": "TX",
            "Florida": "FL",
            "Illinois": "IL",
            "Pennsylvania": "PA",
            "Ohio": "OH",
            "Georgia": "GA",
            "North Carolina": "NC",
            "Michigan": "MI",
            # Canadian Provinces
            "Ontario": "ON",
            "British Columbia": "BC",
            "Alberta": "AB",
            "Quebec": "QC",
            "Manitoba": "MB",
            "Saskatchewan": "SK",
            "Nova Scotia": "NS",
            "New Brunswick": "NB",
            "Newfoundland and Labrador": "NL",
            "Prince Edward Island": "PE"
        }
        return state_mapping.get(state_name, state_name[:2].upper())
    
    def get_supported_currencies(self) -> Dict[str, str]:
        """Get list of supported currencies with their symbols"""
        return {
            "USD": "$",      # US Dollar
            "CAD": "C$",     # Canadian Dollar
            "EUR": "€",      # Euro
            "GBP": "£",      # British Pound
            "AUD": "A$",     # Australian Dollar
            "NZD": "NZ$",    # New Zealand Dollar
            "SGD": "S$",     # Singapore Dollar
            "MYR": "RM",     # Malaysian Ringgit
            "GHS": "₵",      # Ghana Cedi
            "NGN": "₦",      # Nigerian Naira
            "KES": "KSh",    # Kenyan Shilling
            "UGX": "USh",    # Ugandan Shilling
            "ZAR": "R",      # South African Rand
            "JPY": "¥",      # Japanese Yen
            "CHF": "CHF",    # Swiss Franc
            "SEK": "kr",     # Swedish Krona
            "NOK": "kr",     # Norwegian Krone
            "DKK": "kr"      # Danish Krone
        }
    
    def get_currency_for_country(self, country_code: str) -> str:
        """Get default currency for a country"""
        currency_mapping = {
            "US": "USD",
            "CA": "CAD",
            "GB": "GBP",
            "DE": "EUR",
            "FR": "EUR",
            "IT": "EUR",
            "ES": "EUR",
            "NL": "EUR",
            "BE": "EUR",
            "AT": "EUR",
            "IE": "EUR",
            "PT": "EUR",
            "FI": "EUR",
            "AU": "AUD",
            "NZ": "NZD",
            "SG": "SGD",
            "MY": "MYR",
            "GH": "GHS",
            "NG": "NGN",
            "KE": "KES",
            "UG": "UGX",
            "ZA": "ZAR",
            "JP": "JPY",
            "CH": "CHF",
            "SE": "SEK",
            "NO": "NOK",
            "DK": "DKK"
        }
        return currency_mapping.get(country_code, "USD")
    
    def get_tax_type_for_country(self, country_code: str) -> TaxType:
        """Get the primary tax type for a country"""
        tax_type_mapping = {
            "US": TaxType.SALES_TAX,
            "CA": TaxType.GST,
            "AU": TaxType.GST,
            "NZ": TaxType.GST,
            "SG": TaxType.GST,
            "MY": TaxType.GST,
            # EU countries use VAT
            "GB": TaxType.VAT,
            "DE": TaxType.VAT,
            "FR": TaxType.VAT,
            "IT": TaxType.VAT,
            "ES": TaxType.VAT,
            "NL": TaxType.VAT,
            "BE": TaxType.VAT,
            "AT": TaxType.VAT,
            "IE": TaxType.VAT,
            "PT": TaxType.VAT,
            "FI": TaxType.VAT,
            "SE": TaxType.VAT,
            "DK": TaxType.VAT,
            # African countries typically use VAT
            "GH": TaxType.VAT,
            "NG": TaxType.VAT,
            "KE": TaxType.VAT,
            "UG": TaxType.VAT,
            "ZA": TaxType.VAT
        }
        return tax_type_mapping.get(country_code, TaxType.SALES_TAX)
    
    async def close(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()
            self.session = None