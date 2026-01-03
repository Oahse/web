"""
Tax calculation routes
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from uuid import UUID
from decimal import Decimal
from enum import Enum

from core.database import get_db
from core.dependencies import get_current_user
from core.utils.response import Response
from models.user import User
from services.tax import TaxService
from pydantic import BaseModel

router = APIRouter(prefix="/tax", tags=["tax"])


class Currency(str, Enum):
    # Major currencies
    USD = "USD"  # US Dollar
    EUR = "EUR"  # Euro
    GBP = "GBP"  # British Pound
    JPY = "JPY"  # Japanese Yen
    CHF = "CHF"  # Swiss Franc
    CAD = "CAD"  # Canadian Dollar
    AUD = "AUD"  # Australian Dollar
    NZD = "NZD"  # New Zealand Dollar
    
    # Asian currencies
    CNY = "CNY"  # Chinese Yuan
    HKD = "HKD"  # Hong Kong Dollar
    SGD = "SGD"  # Singapore Dollar
    KRW = "KRW"  # South Korean Won
    INR = "INR"  # Indian Rupee
    THB = "THB"  # Thai Baht
    MYR = "MYR"  # Malaysian Ringgit
    PHP = "PHP"  # Philippine Peso
    IDR = "IDR"  # Indonesian Rupiah
    VND = "VND"  # Vietnamese Dong
    TWD = "TWD"  # Taiwan Dollar
    BDT = "BDT"  # Bangladeshi Taka
    PKR = "PKR"  # Pakistani Rupee
    LKR = "LKR"  # Sri Lankan Rupee
    NPR = "NPR"  # Nepalese Rupee
    BTN = "BTN"  # Bhutanese Ngultrum
    MVR = "MVR"  # Maldivian Rufiyaa
    AFN = "AFN"  # Afghan Afghani
    MMK = "MMK"  # Myanmar Kyat
    KHR = "KHR"  # Cambodian Riel
    LAK = "LAK"  # Lao Kip
    BND = "BND"  # Brunei Dollar
    MNT = "MNT"  # Mongolian Tugrik
    
    # European currencies
    SEK = "SEK"  # Swedish Krona
    NOK = "NOK"  # Norwegian Krone
    DKK = "DKK"  # Danish Krone
    PLN = "PLN"  # Polish Zloty
    CZK = "CZK"  # Czech Koruna
    HUF = "HUF"  # Hungarian Forint
    RON = "RON"  # Romanian Leu
    BGN = "BGN"  # Bulgarian Lev
    HRK = "HRK"  # Croatian Kuna
    RSD = "RSD"  # Serbian Dinar
    BAM = "BAM"  # Bosnia and Herzegovina Convertible Mark
    MKD = "MKD"  # Macedonian Denar
    ALL = "ALL"  # Albanian Lek
    MDL = "MDL"  # Moldovan Leu
    ISK = "ISK"  # Icelandic Krona
    
    # Middle Eastern currencies
    AED = "AED"  # UAE Dirham
    SAR = "SAR"  # Saudi Riyal
    QAR = "QAR"  # Qatari Riyal
    KWD = "KWD"  # Kuwaiti Dinar
    BHD = "BHD"  # Bahraini Dinar
    OMR = "OMR"  # Omani Rial
    JOD = "JOD"  # Jordanian Dinar
    ILS = "ILS"  # Israeli Shekel
    TRY = "TRY"  # Turkish Lira
    IRR = "IRR"  # Iranian Rial
    IQD = "IQD"  # Iraqi Dinar
    SYP = "SYP"  # Syrian Pound
    LBP = "LBP"  # Lebanese Pound
    YER = "YER"  # Yemeni Rial
    
    # African currencies
    ZAR = "ZAR"  # South African Rand
    EGP = "EGP"  # Egyptian Pound
    NGN = "NGN"  # Nigerian Naira
    KES = "KES"  # Kenyan Shilling
    GHS = "GHS"  # Ghanaian Cedi
    MAD = "MAD"  # Moroccan Dirham
    TND = "TND"  # Tunisian Dinar
    DZD = "DZD"  # Algerian Dinar
    LYD = "LYD"  # Libyan Dinar
    SDG = "SDG"  # Sudanese Pound
    ETB = "ETB"  # Ethiopian Birr
    UGX = "UGX"  # Ugandan Shilling
    TZS = "TZS"  # Tanzanian Shilling
    RWF = "RWF"  # Rwandan Franc
    BIF = "BIF"  # Burundian Franc
    DJF = "DJF"  # Djiboutian Franc
    SOS = "SOS"  # Somali Shilling
    ERN = "ERN"  # Eritrean Nakfa
    MWK = "MWK"  # Malawian Kwacha
    ZMW = "ZMW"  # Zambian Kwacha
    BWP = "BWP"  # Botswanan Pula
    NAD = "NAD"  # Namibian Dollar
    SZL = "SZL"  # Swazi Lilangeni
    LSL = "LSL"  # Lesotho Loti
    MGA = "MGA"  # Malagasy Ariary
    MUR = "MUR"  # Mauritian Rupee
    SCR = "SCR"  # Seychellois Rupee
    KMF = "KMF"  # Comorian Franc
    AOA = "AOA"  # Angolan Kwanza
    MZN = "MZN"  # Mozambican Metical
    SLL = "SLL"  # Sierra Leonean Leone
    LRD = "LRD"  # Liberian Dollar
    GNF = "GNF"  # Guinean Franc
    CDF = "CDF"  # Congolese Franc
    XAF = "XAF"  # Central African CFA Franc
    XOF = "XOF"  # West African CFA Franc
    
    # Latin American currencies
    BRL = "BRL"  # Brazilian Real
    MXN = "MXN"  # Mexican Peso
    ARS = "ARS"  # Argentine Peso
    CLP = "CLP"  # Chilean Peso
    COP = "COP"  # Colombian Peso
    PEN = "PEN"  # Peruvian Sol
    UYU = "UYU"  # Uruguayan Peso
    PYG = "PYG"  # Paraguayan Guarani
    BOB = "BOB"  # Bolivian Boliviano
    VES = "VES"  # Venezuelan Bolívar
    GYD = "GYD"  # Guyanese Dollar
    SRD = "SRD"  # Surinamese Dollar
    TTD = "TTD"  # Trinidad and Tobago Dollar
    JMD = "JMD"  # Jamaican Dollar
    BBD = "BBD"  # Barbadian Dollar
    BZD = "BZD"  # Belize Dollar
    XCD = "XCD"  # East Caribbean Dollar
    HTG = "HTG"  # Haitian Gourde
    DOP = "DOP"  # Dominican Peso
    CUP = "CUP"  # Cuban Peso
    GTQ = "GTQ"  # Guatemalan Quetzal
    HNL = "HNL"  # Honduran Lempira
    NIO = "NIO"  # Nicaraguan Córdoba
    CRC = "CRC"  # Costa Rican Colón
    PAB = "PAB"  # Panamanian Balboa
    
    # North American currencies
    AWG = "AWG"  # Aruban Florin
    ANG = "ANG"  # Netherlands Antillean Guilder
    
    # Oceania currencies
    FJD = "FJD"  # Fijian Dollar
    PGK = "PGK"  # Papua New Guinean Kina
    SBD = "SBD"  # Solomon Islands Dollar
    VUV = "VUV"  # Vanuatu Vatu
    WST = "WST"  # Samoan Tala
    TOP = "TOP"  # Tongan Paʻanga
    
    # Eastern European and Central Asian currencies
    RUB = "RUB"  # Russian Ruble
    UAH = "UAH"  # Ukrainian Hryvnia
    BYN = "BYN"  # Belarusian Ruble
    KZT = "KZT"  # Kazakhstani Tenge
    UZS = "UZS"  # Uzbekistani Som
    KGS = "KGS"  # Kyrgyzstani Som
    TJS = "TJS"  # Tajikistani Somoni
    TMT = "TMT"  # Turkmenistani Manat
    AZN = "AZN"  # Azerbaijani Manat
    AMD = "AMD"  # Armenian Dram
    GEL = "GEL"  # Georgian Lari
    
    # Special drawing rights and other
    XDR = "XDR"  # Special Drawing Rights
    XAU = "XAU"  # Gold (troy ounce)
    XAG = "XAG"  # Silver (troy ounce)
    XPT = "XPT"  # Platinum (troy ounce)
    XPD = "XPD"  # Palladium (troy ounce)
    
    # Cryptocurrencies (if supported)
    BTC = "BTC"  # Bitcoin
    ETH = "ETH"  # Ethereum
    USDT = "USDT"  # Tether
    USDC = "USDC"  # USD Coin
    BNB = "BNB"  # Binance Coin
    ADA = "ADA"  # Cardano
    SOL = "SOL"  # Solana
    DOT = "DOT"  # Polkadot
    MATIC = "MATIC"  # Polygon
    AVAX = "AVAX"  # Avalanche


class TaxCalculationRequest(BaseModel):
    subtotal: float
    shipping: float = 0.0
    shipping_address_id: Optional[UUID] = None
    country_code: Optional[str] = None
    state_code: Optional[str] = None
    product_type: Optional[str] = None
    currency: Currency = Currency.USD


class TaxCalculationResponse(BaseModel):
    tax_amount: float
    tax_rate: float
    tax_type: str
    jurisdiction: str
    currency: Currency
    breakdown: list = []


@router.post("/calculate")
async def calculate_tax(
    request: TaxCalculationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Calculate tax amount based on subtotal, shipping, and location
    """
    try:
        async with TaxService(db) as tax_service:
            result = await tax_service.calculate_tax(
                subtotal=Decimal(str(request.subtotal)),
                shipping_address_id=request.shipping_address_id,
                country_code=request.country_code,
                state_code=request.state_code,
                product_type=request.product_type,
                currency=request.currency
            )
            
            tax_response = TaxCalculationResponse(
                tax_amount=float(result.tax_amount),
                tax_rate=result.tax_rate,
                tax_type=result.tax_type.value,
                jurisdiction=result.jurisdiction,
                currency=Currency(result.currency),
                breakdown=result.breakdown
            )
            
            return Response.success(data=tax_response)
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Tax calculation failed: {str(e)}"
        )