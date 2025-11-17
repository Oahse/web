from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime, timedelta
from core.database import get_db
from core.utils.response import Response
from core.exceptions import APIException
from services.analytics import AnalyticsService
from models.user import User
from services.auth import AuthService

from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_auth_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> User:
    return await AuthService.get_current_user(token, db)

router = APIRouter(prefix="/api/v1/analytics", tags=["Analytics"])

@router.get("/dashboard")
async def get_dashboard_data(
    date_range: Optional[str] = Query("30d"), 
    current_user: User = Depends(get_current_auth_user),
    db: AsyncSession = Depends(get_db)
):
    """Get dashboard analytics data."""
    try:
        analytics_service = AnalyticsService(db)
        
        # Parse date range
        if date_range == "7d":
            start_date = datetime.now() - timedelta(days=7)
        elif date_range == "30d":
            start_date = datetime.now() - timedelta(days=30)
        elif date_range == "90d":
            start_date = datetime.now() - timedelta(days=90)
        else:
            start_date = datetime.now() - timedelta(days=30)
        
        data = await analytics_service.get_dashboard_data(
            user_id=str(current_user.id),
            user_role=current_user.role,
            start_date=start_date
        )
        return Response(success=True, data=data)
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Failed to fetch analytics dashboard data", # Added message
            detail=f"Failed to fetch analytics data: {e}" # Modified detail to include original exception
        )

@router.get("/sales-trend")
async def get_sales_trend(
    days: int = Query(30, ge=1, le=366),
    current_user: User = Depends(get_current_auth_user),
    db: AsyncSession = Depends(get_db)
):
    """Get sales trend data."""
    try:
        analytics_service = AnalyticsService(db)
        trend = await analytics_service.get_sales_trend(
            user_id=str(current_user.id),
            user_role=current_user.role,
            days=days
        )
        return Response(success=True, data=trend)
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Failed to fetch sales trend data", # Added message
            detail=f"Failed to fetch sales trend: {e}" # Modified detail
        )

@router.get("/top-products")
async def get_top_products(
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_auth_user),
    db: AsyncSession = Depends(get_db)
):
    """Get top performing products."""
    try:
        analytics_service = AnalyticsService(db)
        products = await analytics_service.get_top_products(
            user_id=str(current_user.id),
            user_role=current_user.role,
            limit=limit
        )
        return Response(success=True, data=products)
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Failed to fetch top products data", # Added message
            detail=f"Failed to fetch top products: {e}" # Modified detail
        )