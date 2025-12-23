from typing import Dict, Optional
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.user import Address
from uuid import UUID


class TaxService:
    """Service for calculating taxes based on location and order details"""
    
    # Tax rates by country/state (simplified for demo - in production, use a tax service API)
    TAX_RATES = {
        "US": {
            "default": 0.08,  # 8% default US tax
            "CA": 0.10,       # California
            "NY": 0.08,       # New York
            "TX": 0.0625,     # Texas
            "FL": 0.06,       # Florida
        },
        "CA": {
            "default": 0.13,  # 13% HST/GST for Canada
            "ON": 0.13,       # Ontario
            "BC": 0.12,       # British Columbia
            "AB": 0.05,       # Alberta
        },
        "GB": {
            "default": 0.20,  # 20% VAT for UK
        },
        "DE": {
            "default": 0.19,  # 19% VAT for Germany
        },
        "FR": {
            "default": 0.20,  # 20% VAT for France
        },
        "GH": {
            "default": 0.125, # 12.5% VAT for Ghana
        },
        "NG": {
            "default": 0.075, # 7.5% VAT for Nigeria
        },
        "KE": {
            "default": 0.16,  # 16% VAT for Kenya
        },
        "UG": {
            "default": 0.18,  # 18% VAT for Uganda
        }
    }
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def calculate_tax(
        self, 
        subtotal: Decimal, 
        shipping_address_id: Optional[UUID] = None,
        country_code: Optional[str] = None,
        state_code: Optional[str] = None
    ) -> Dict[str, any]:
        """
        Calculate tax amount based on subtotal and location.
        
        Args:
            subtotal: The subtotal amount before tax
            shipping_address_id: ID of the shipping address
            country_code: ISO country code (fallback if no address)
            state_code: State/province code (fallback if no address)
            
        Returns:
            Dict containing tax_rate, tax_amount, and location info
        """
        tax_rate = 0.0
        location_info = {}
        
        # Get location from address if provided
        if shipping_address_id:
            address = await self.db.get(Address, shipping_address_id)
            if address:
                country_code = self._get_country_code(address.country)
                state_code = self._get_state_code(address.state)
                location_info = {
                    "country": address.country,
                    "state": address.state,
                    "city": address.city
                }
        
        # Calculate tax rate
        if country_code:
            country_rates = self.TAX_RATES.get(country_code, {})
            if state_code and state_code in country_rates:
                tax_rate = country_rates[state_code]
            else:
                tax_rate = country_rates.get("default", 0.0)
        
        # Calculate tax amount
        tax_amount = subtotal * Decimal(str(tax_rate))
        
        return {
            "tax_rate": tax_rate,
            "tax_amount": float(tax_amount),
            "location": location_info,
            "tax_inclusive": False  # Assuming tax-exclusive pricing
        }
    
    def _get_country_code(self, country_name: str) -> str:
        """Convert country name to ISO code"""
        country_mapping = {
            "United States": "US",
            "USA": "US",
            "Canada": "CA",
            "United Kingdom": "GB",
            "UK": "GB",
            "Germany": "DE",
            "France": "FR",
            "Ghana": "GH",
            "Nigeria": "NG",
            "Kenya": "KE",
            "Uganda": "UG"
        }
        return country_mapping.get(country_name, country_name[:2].upper())
    
    def _get_state_code(self, state_name: str) -> str:
        """Convert state name to code"""
        state_mapping = {
            "California": "CA",
            "New York": "NY",
            "Texas": "TX",
            "Florida": "FL",
            "Ontario": "ON",
            "British Columbia": "BC",
            "Alberta": "AB"
        }
        return state_mapping.get(state_name, state_name[:2].upper())
    
    def get_supported_currencies(self) -> Dict[str, str]:
        """Get list of supported currencies with their symbols"""
        return {
            "USD": "$",
            "CAD": "C$",
            "EUR": "€",
            "GBP": "£",
            "GHS": "₵",  # Ghana Cedi
            "NGN": "₦",  # Nigerian Naira
            "KES": "KSh", # Kenyan Shilling
            "UGX": "USh"  # Ugandan Shilling
        }
    
    def get_currency_for_country(self, country_code: str) -> str:
        """Get default currency for a country"""
        currency_mapping = {
            "US": "USD",
            "CA": "CAD",
            "GB": "GBP",
            "DE": "EUR",
            "FR": "EUR",
            "GH": "GHS",
            "NG": "NGN",
            "KE": "KES",
            "UG": "UGX"
        }
        return currency_mapping.get(country_code, "USD")