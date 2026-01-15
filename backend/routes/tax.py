"""
Tax calculation routes
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from typing import Optional, List
from uuid import UUID
from decimal import Decimal

from core.database import get_db
from core.dependencies import get_current_user, require_admin
from core.exceptions import APIException
from core.utils.response import Response
from models.user import User
from models.tax_rates import TaxRate
from services.tax import TaxService
from schemas.tax import (
    Currency,
    TaxCalculationRequest,
    TaxCalculationResponse,
    TaxRateCreate,
    TaxRateUpdate,
    TaxRateResponse,
)

router = APIRouter(prefix="/tax", tags=["tax"])


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

# ============================================================================
# ADMIN TAX RATES MANAGEMENT ROUTES
# ============================================================================


@router.get("/admin/tax-rates", response_model=List[TaxRateResponse])
async def list_tax_rates(
    country_code: Optional[str] = Query(None, description="Filter by country code"),
    province_code: Optional[str] = Query(None, description="Filter by province code"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search in country/province names"),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """List all tax rates with filtering and pagination (Admin only)"""
    try:
        # Build query
        query = select(TaxRate)
        
        # Apply filters
        conditions = []
        if country_code:
            conditions.append(TaxRate.country_code == country_code.upper())
        if province_code:
            conditions.append(TaxRate.province_code == province_code.upper())
        if is_active is not None:
            conditions.append(TaxRate.is_active == is_active)
        if search:
            search_term = f"%{search}%"
            conditions.append(
                or_(
                    TaxRate.country_name.ilike(search_term),
                    TaxRate.province_name.ilike(search_term)
                )
            )
        
        if conditions:
            query = query.where(and_(*conditions))
        
        # Order by country, then province
        query = query.order_by(TaxRate.country_code, TaxRate.province_code)
        
        # Apply pagination
        offset = (page - 1) * per_page
        query = query.offset(offset).limit(per_page)
        
        result = await db.execute(query)
        tax_rates = result.scalars().all()
        
        # Format response
        response_data = []
        for rate in tax_rates:
            response_data.append(TaxRateResponse(
                id=rate.id,
                country_code=rate.country_code,
                country_name=rate.country_name,
                province_code=rate.province_code,
                province_name=rate.province_name,
                tax_rate=rate.tax_rate,
                tax_percentage=rate.tax_rate * 100,
                tax_name=rate.tax_name,
                is_active=rate.is_active,
                created_at=rate.created_at.isoformat(),
                updated_at=rate.updated_at.isoformat() if rate.updated_at else None
            ))
        
        return response_data
        
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to list tax rates: {str(e)}"
        )


@router.get("/admin/tax-rates/countries", response_model=List[dict])
async def list_countries(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get list of unique countries with tax rates (Admin only)"""
    try:
        query = select(
            TaxRate.country_code,
            TaxRate.country_name,
            func.count(TaxRate.id).label('rate_count')
        ).group_by(
            TaxRate.country_code,
            TaxRate.country_name
        ).order_by(TaxRate.country_name)
        
        result = await db.execute(query)
        countries = result.all()
        
        return [
            {
                "country_code": row.country_code,
                "country_name": row.country_name,
                "rate_count": row.rate_count
            }
            for row in countries
        ]
        
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to list countries: {str(e)}"
        )


@router.get("/admin/tax-rates/{tax_rate_id}", response_model=TaxRateResponse)
async def get_tax_rate(
    tax_rate_id: UUID,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific tax rate by ID (Admin only)"""
    try:
        result = await db.execute(
            select(TaxRate).where(TaxRate.id == tax_rate_id)
        )
        tax_rate = result.scalar_one_or_none()
        
        if not tax_rate:
            raise APIException(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Tax rate not found"
            )
        
        return TaxRateResponse(
            id=tax_rate.id,
            country_code=tax_rate.country_code,
            country_name=tax_rate.country_name,
            province_code=tax_rate.province_code,
            province_name=tax_rate.province_name,
            tax_rate=tax_rate.tax_rate,
            tax_percentage=tax_rate.tax_rate * 100,
            tax_name=tax_rate.tax_name,
            is_active=tax_rate.is_active,
            created_at=tax_rate.created_at.isoformat(),
            updated_at=tax_rate.updated_at.isoformat() if tax_rate.updated_at else None
        )
        
    except APIException:
        raise
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to get tax rate: {str(e)}"
        )


@router.post("/admin/tax-rates", response_model=TaxRateResponse, status_code=status.HTTP_201_CREATED)
async def create_tax_rate(
    data: TaxRateCreate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Create a new tax rate (Admin only)"""
    try:
        # Check if tax rate already exists for this location
        existing_query = select(TaxRate).where(
            and_(
                TaxRate.country_code == data.country_code.upper(),
                TaxRate.province_code == (data.province_code.upper() if data.province_code else None)
            )
        )
        result = await db.execute(existing_query)
        existing = result.scalar_one_or_none()
        
        if existing:
            raise APIException(
                status_code=status.HTTP_400_BAD_REQUEST,
                message=f"Tax rate already exists for {data.country_code}" + 
                        (f"-{data.province_code}" if data.province_code else "")
            )
        
        # Create new tax rate
        tax_rate = TaxRate(
            country_code=data.country_code.upper(),
            country_name=data.country_name,
            province_code=data.province_code.upper() if data.province_code else None,
            province_name=data.province_name,
            tax_rate=data.tax_rate,
            tax_name=data.tax_name,
            is_active=data.is_active
        )
        
        db.add(tax_rate)
        await db.commit()
        await db.refresh(tax_rate)
        
        return TaxRateResponse(
            id=tax_rate.id,
            country_code=tax_rate.country_code,
            country_name=tax_rate.country_name,
            province_code=tax_rate.province_code,
            province_name=tax_rate.province_name,
            tax_rate=tax_rate.tax_rate,
            tax_percentage=tax_rate.tax_rate * 100,
            tax_name=tax_rate.tax_name,
            is_active=tax_rate.is_active,
            created_at=tax_rate.created_at.isoformat(),
            updated_at=tax_rate.updated_at.isoformat() if tax_rate.updated_at else None
        )
        
    except APIException:
        raise
    except Exception as e:
        await db.rollback()
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to create tax rate: {str(e)}"
        )


@router.put("/admin/tax-rates/{tax_rate_id}", response_model=TaxRateResponse)
async def update_tax_rate(
    tax_rate_id: UUID,
    data: TaxRateUpdate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Update an existing tax rate (Admin only)"""
    try:
        result = await db.execute(
            select(TaxRate).where(TaxRate.id == tax_rate_id)
        )
        tax_rate = result.scalar_one_or_none()
        
        if not tax_rate:
            raise APIException(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Tax rate not found"
            )
        
        # Update fields
        if data.country_name is not None:
            tax_rate.country_name = data.country_name
        if data.province_name is not None:
            tax_rate.province_name = data.province_name
        if data.tax_rate is not None:
            tax_rate.tax_rate = data.tax_rate
        if data.tax_name is not None:
            tax_rate.tax_name = data.tax_name
        if data.is_active is not None:
            tax_rate.is_active = data.is_active
        
        await db.commit()
        await db.refresh(tax_rate)
        
        return TaxRateResponse(
            id=tax_rate.id,
            country_code=tax_rate.country_code,
            country_name=tax_rate.country_name,
            province_code=tax_rate.province_code,
            province_name=tax_rate.province_name,
            tax_rate=tax_rate.tax_rate,
            tax_percentage=tax_rate.tax_rate * 100,
            tax_name=tax_rate.tax_name,
            is_active=tax_rate.is_active,
            created_at=tax_rate.created_at.isoformat(),
            updated_at=tax_rate.updated_at.isoformat() if tax_rate.updated_at else None
        )
        
    except APIException:
        raise
    except Exception as e:
        await db.rollback()
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to update tax rate: {str(e)}"
        )


@router.delete("/admin/tax-rates/{tax_rate_id}")
async def delete_tax_rate(
    tax_rate_id: UUID,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Delete a tax rate (Admin only)"""
    try:
        result = await db.execute(
            select(TaxRate).where(TaxRate.id == tax_rate_id)
        )
        tax_rate = result.scalar_one_or_none()
        
        if not tax_rate:
            raise APIException(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Tax rate not found"
            )
        
        await db.delete(tax_rate)
        await db.commit()
        
        return Response.success(message="Tax rate deleted successfully")
        
    except APIException:
        raise
    except Exception as e:
        await db.rollback()
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to delete tax rate: {str(e)}"
        )


@router.post("/admin/tax-rates/bulk-update")
async def bulk_update_tax_rates(
    updates: List[dict],
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Bulk update multiple tax rates (Admin only)"""
    try:
        updated_count = 0
        errors = []
        
        for update_data in updates:
            try:
                tax_rate_id = UUID(update_data.get("id"))
                result = await db.execute(
                    select(TaxRate).where(TaxRate.id == tax_rate_id)
                )
                tax_rate = result.scalar_one_or_none()
                
                if tax_rate:
                    if "tax_rate" in update_data:
                        tax_rate.tax_rate = float(update_data["tax_rate"])
                    if "is_active" in update_data:
                        tax_rate.is_active = bool(update_data["is_active"])
                    if "tax_name" in update_data:
                        tax_rate.tax_name = update_data["tax_name"]
                    
                    updated_count += 1
                else:
                    errors.append(f"Tax rate {tax_rate_id} not found")
                    
            except Exception as e:
                errors.append(f"Error updating {update_data.get('id')}: {str(e)}")
        
        await db.commit()
        
        return Response.success(
            data={
                "updated_count": updated_count,
                "errors": errors
            },
            message=f"Successfully updated {updated_count} tax rates"
        )
        
    except Exception as e:
        await db.rollback()
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to bulk update tax rates: {str(e)}"
        )
