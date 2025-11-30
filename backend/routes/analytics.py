from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime, timedelta
from core.database import get_db
from core.utils.response import Response
from core.exceptions import APIException
from services.analytics import AnalyticsService
from models.user import User
from services.auth import AuthService
import io

from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


async def get_current_auth_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> User:
    return await AuthService.get_current_user(token, db)

router = APIRouter(prefix="/api/v1/analytics", tags=["Analytics"])


@router.get("/dashboard")
async def get_dashboard_data(
    date_range: Optional[str] = Query("30d"),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    product: Optional[str] = Query(None),
    userSegment: Optional[str] = Query(None),
    orderStatus: Optional[str] = Query(None),
    current_user: User = Depends(get_current_auth_user),
    db: AsyncSession = Depends(get_db)
):
    """Get dashboard analytics data with filters."""
    try:
        analytics_service = AnalyticsService(db)

        # Parse date range
        if date_from and date_to:
            # Custom date range
            start_date = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
            end_date = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
        elif date_range == "7d":
            start_date = datetime.now() - timedelta(days=7)
            end_date = datetime.now()
        elif date_range == "30d":
            start_date = datetime.now() - timedelta(days=30)
            end_date = datetime.now()
        elif date_range == "3m":
            start_date = datetime.now() - timedelta(days=90)
            end_date = datetime.now()
        elif date_range == "12m":
            start_date = datetime.now() - timedelta(days=365)
            end_date = datetime.now()
        else:
            start_date = datetime.now() - timedelta(days=30)
            end_date = datetime.now()

        # Build filters dict
        filters = {
            'category': category,
            'product': product,
            'user_segment': userSegment,
            'order_status': orderStatus
        }

        data = await analytics_service.get_dashboard_data(
            user_id=str(current_user.id),
            user_role=current_user.role,
            start_date=start_date,
            end_date=end_date,
            filters=filters
        )
        return Response(success=True, data=data)
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            # Modified detail to include original exception
            message=f"Failed to fetch analytics data: {e}"
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
        return Response(success=True, data={"sales_trend": trend})
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to fetch sales trend: {e}"  # Modified detail
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
            message=f"Failed to fetch top products: {e}"  # Modified detail
        )


@router.get("/export")
async def export_analytics(
    type: str = Query("dashboard"),
    format: str = Query("csv"),
    date_range: Optional[str] = Query("30d"),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    product: Optional[str] = Query(None),
    userSegment: Optional[str] = Query(None),
    orderStatus: Optional[str] = Query(None),
    current_user: User = Depends(get_current_auth_user),
    db: AsyncSession = Depends(get_db)
):
    """Export analytics data as CSV or Excel."""
    try:
        analytics_service = AnalyticsService(db)

        # Parse date range
        if date_from and date_to:
            start_date = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
            end_date = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
        elif date_range == "7d":
            start_date = datetime.now() - timedelta(days=7)
            end_date = datetime.now()
        elif date_range == "30d":
            start_date = datetime.now() - timedelta(days=30)
            end_date = datetime.now()
        elif date_range == "3m":
            start_date = datetime.now() - timedelta(days=90)
            end_date = datetime.now()
        elif date_range == "12m":
            start_date = datetime.now() - timedelta(days=365)
            end_date = datetime.now()
        else:
            start_date = datetime.now() - timedelta(days=30)
            end_date = datetime.now()

        # Build filters dict
        filters = {
            'category': category,
            'product': product,
            'user_segment': userSegment,
            'order_status': orderStatus
        }

        # Get the data
        data = await analytics_service.get_dashboard_data(
            user_id=str(current_user.id),
            user_role=current_user.role,
            start_date=start_date,
            end_date=end_date,
            filters=filters
        )

        # Export the data
        file_content, content_type, filename = await analytics_service.export_data(
            data=data,
            format=format,
            export_type=type
        )

        return StreamingResponse(
            io.BytesIO(file_content),
            media_type=content_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to export analytics data: {e}"
        )


@router.get("/recent-activity")
async def get_recent_activity(
    limit: int = Query(100, ge=1, le=500),
    since: Optional[str] = Query(None),
    current_user: User = Depends(get_current_auth_user),
    db: AsyncSession = Depends(get_db)
):
    """Get recent activity logs."""
    try:
        analytics_service = AnalyticsService(db)
        
        # Parse since parameter if provided
        since_date = None
        if since:
            since_date = datetime.fromisoformat(since.replace('Z', '+00:00'))
        
        activities = await analytics_service.get_recent_activity(
            limit=limit,
            since=since_date
        )
        
        return Response(success=True, data=activities)
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to fetch recent activity: {e}"
        )
