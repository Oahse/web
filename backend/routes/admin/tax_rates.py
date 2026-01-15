"""
Admin routes for managing tax rates
"""
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from typing import Optional, List
from uuid import UUID

from core.database import get_db
from core.dependencies import require_admin
from core.exceptions import APIException
from core.utils.response import Response
from models.user import User
from models.tax_rates import TaxRate
from pydantic import BaseModel, Field


# Schemas
class TaxRateCreate(BaseModel):
    country_code: str = Field(..., min_length=2, max_length=2, description="ISO 3166-1 alpha-2 country code")
    country_name: str = Field(..., min_length=1, max_length=100)
    province_code: Optional[str] = Field(None, max_length=10, description="State/Province code")
    province_name: Optional[str] = Field(None, max_length=100)
    tax_rate: float = Field(..., ge=0, le=1, description="Tax rate as decimal (e.g., 0.0725 for 7.25%)")
    tax_name: Optional[str] = Field(None, max_length=50, description="e.g., GST, VAT, Sales Tax")
    is_active: bool = True


class TaxRateUpdate(BaseModel):
    country_name: Optional[str] = Field(None, min_length=1, max_length=100)
    province_name: Optional[str] = Field(None, max_length=100)
    tax_rate: Optional[float] = Field(None, ge=0, le=1)
    tax_name: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = None


class TaxRateResponse(BaseModel):
    id: UUID
    country_code: str
    country_name: str
    province_code: Optional[str]
    province_name: Optional[str]
    tax_rate: float
    tax_percentage: float  # Computed: tax_rate * 100
    tax_name: Optional[str]
    is_active: bool
    created_at: str
    updated_at: Optional[str]

    class Config:
        from_attributes = True


router = APIRouter(prefix="/tax-rates", tags=["Admin - Tax Rates"])


@router.get("/", response_model=List[TaxRateResponse])
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
    """List all tax rates with filtering and pagination"""
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


@router.get("/countries", response_model=List[dict])
async def list_countries(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get list of unique countries with tax rates"""
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


@router.get("/{tax_rate_id}", response_model=TaxRateResponse)
async def get_tax_rate(
    tax_rate_id: UUID,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific tax rate by ID"""
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


@router.post("/", response_model=TaxRateResponse, status_code=status.HTTP_201_CREATED)
async def create_tax_rate(
    data: TaxRateCreate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Create a new tax rate"""
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


@router.put("/{tax_rate_id}", response_model=TaxRateResponse)
async def update_tax_rate(
    tax_rate_id: UUID,
    data: TaxRateUpdate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Update an existing tax rate"""
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


@router.delete("/{tax_rate_id}")
async def delete_tax_rate(
    tax_rate_id: UUID,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Delete a tax rate"""
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
        
        return Response(
            success=True,
            message="Tax rate deleted successfully"
        )
        
    except APIException:
        raise
    except Exception as e:
        await db.rollback()
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to delete tax rate: {str(e)}"
        )


@router.post("/bulk-update")
async def bulk_update_tax_rates(
    updates: List[dict],
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Bulk update multiple tax rates"""
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
        
        return Response(
            success=True,
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
