from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, Query, status, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Dict, Any, List
from core.database import get_db
from core.utils.response import Response
from core.exceptions import APIException
from services.admin_pricing import AdminPricingService
from services.analytics import AnalyticsService
from services.enhanced_export import EnhancedExportService
from models.user import User
from services.auth import AuthService

from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_auth_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> User:
    return await AuthService.get_current_user(token, db)

router = APIRouter(prefix="/api/v1/admin/pricing", tags=["Admin Pricing"])

def require_admin(current_user: User = Depends(get_current_auth_user)):
    """Require admin role."""
    if current_user.role not in ["Admin", "SuperAdmin"]:
        raise APIException(
            status_code=status.HTTP_403_FORBIDDEN,
            message="Admin access required"
        )
    return current_user

# Request/Response Models
class UpdateSubscriptionPercentageRequest(BaseModel):
    percentage: float
    change_reason: Optional[str] = None

class UpdateDeliveryCostsRequest(BaseModel):
    delivery_costs: Dict[str, float]
    change_reason: Optional[str] = None

class PricingImpactPreviewRequest(BaseModel):
    proposed_changes: Dict[str, Any]

class BulkPricingUpdateRequest(BaseModel):
    subscription_percentage: Optional[float] = None
    delivery_costs: Optional[Dict[str, float]] = None
    tax_rates: Optional[Dict[str, float]] = None
    change_reason: Optional[str] = None
    confirm_bulk_update: bool = False

# Cost Management Interface Routes

@router.get("/dashboard-summary")
async def get_dashboard_summary(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get comprehensive dashboard summary for cost management interface."""
    try:
        analytics_service = AnalyticsService(db)
        admin_pricing_service = AdminPricingService(db)
        
        # Get current date range (last 30 days)
        from datetime import datetime, timedelta
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        from services.analytics import DateRange, AnalyticsFilters
        date_range = DateRange(start_date=start_date, end_date=end_date)
        filters = AnalyticsFilters()
        
        # Get current pricing configuration
        current_config = await admin_pricing_service.get_pricing_config()
        
        # Get subscription metrics
        subscription_metrics = await analytics_service.get_subscription_metrics(
            date_range, filters
        )
        
        # Get payment analytics
        payment_analytics = await analytics_service.get_payment_success_analytics(
            date_range, ["payment_method", "country"]
        )
        
        # Get live metrics
        live_metrics = await analytics_service.get_live_metrics_display()
        
        # Calculate key performance indicators
        admin_fee_percentage = current_config.subscription_percentage if current_config else 10.0
        estimated_admin_revenue = subscription_metrics.total_revenue * (admin_fee_percentage / 100)
        
        # Get recent pricing changes
        recent_audit = await admin_pricing_service.get_pricing_audit_log(page=1, limit=5)
        
        dashboard_summary = {
            "overview": {
                "total_active_subscriptions": subscription_metrics.total_active_subscriptions,
                "monthly_recurring_revenue": float(subscription_metrics.monthly_recurring_revenue),
                "total_revenue_30_days": float(subscription_metrics.total_revenue),
                "estimated_admin_revenue": float(estimated_admin_revenue),
                "admin_fee_percentage": admin_fee_percentage,
                "average_subscription_value": float(subscription_metrics.average_subscription_value),
                "churn_rate": subscription_metrics.churn_rate,
                "conversion_rate": subscription_metrics.conversion_rate
            },
            "live_metrics": live_metrics["live_metrics"],
            "performance_indicators": live_metrics["performance_indicators"],
            "payment_health": {
                "total_payments": payment_analytics.total_payments,
                "success_rate": payment_analytics.success_rate,
                "failed_payments": payment_analytics.failed_payments,
                "total_volume": float(payment_analytics.total_volume),
                "average_payment_amount": float(payment_analytics.average_payment_amount)
            },
            "current_pricing_config": {
                "subscription_percentage": current_config.subscription_percentage if current_config else 10.0,
                "delivery_costs": current_config.delivery_costs if current_config else {},
                "last_updated": current_config.updated_at.isoformat() if current_config and current_config.updated_at else None,
                "version": current_config.version if current_config else "1.0"
            },
            "recent_changes": {
                "audit_entries": recent_audit["audit_entries"][:3],  # Last 3 changes
                "total_changes_30_days": len([
                    entry for entry in recent_audit["audit_entries"] 
                    if datetime.fromisoformat(entry["created_at"].replace('Z', '+00:00')) >= start_date
                ])
            },
            "alerts": [],  # Will be populated with any pricing alerts
            "quick_actions": {
                "can_update_percentage": True,
                "can_update_delivery_costs": True,
                "can_bulk_update": True,
                "can_export_data": True
            },
            "timestamp": datetime.now().isoformat()
        }
        
        # Add alerts based on performance indicators
        if live_metrics["performance_indicators"]["payment_health"] == "critical":
            dashboard_summary["alerts"].append({
                "type": "critical",
                "message": "Payment success rate is critically low",
                "action": "Review payment processing settings immediately"
            })
        elif live_metrics["performance_indicators"]["payment_health"] == "warning":
            dashboard_summary["alerts"].append({
                "type": "warning", 
                "message": "Payment success rate below optimal",
                "action": "Monitor payment patterns and consider adjustments"
            })
        
        if subscription_metrics.churn_rate > 10:
            dashboard_summary["alerts"].append({
                "type": "warning",
                "message": f"High churn rate detected: {subscription_metrics.churn_rate:.1f}%",
                "action": "Review pricing strategy and customer satisfaction"
            })
        
        return Response(
            success=True,
            data=dashboard_summary,
            message="Dashboard summary retrieved successfully"
        )
    except APIException:
        raise
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to get dashboard summary: {str(e)}"
        )

@router.get("/config")
async def get_pricing_config(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get current pricing configuration."""
    try:
        admin_pricing_service = AdminPricingService(db)
        config = await admin_pricing_service.get_pricing_config()
        
        if not config:
            raise APIException(
                status_code=404,
                message="No pricing configuration found"
            )
        
        return Response(
            success=True, 
            data=config.to_dict(),
            message="Pricing configuration retrieved successfully"
        )
    except APIException:
        raise
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to get pricing configuration: {str(e)}"
        )

@router.get("/revenue-metrics")
async def get_real_time_revenue_metrics(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Display real-time subscription revenue metrics."""
    try:
        analytics_service = AnalyticsService(db)
        
        # Get current date range
        from datetime import datetime, timedelta
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Get subscription metrics
        from services.analytics import DateRange, AnalyticsFilters
        date_range = DateRange(start_date=start_date, end_date=end_date)
        filters = AnalyticsFilters()
        
        subscription_metrics = await analytics_service.get_subscription_metrics(
            date_range, filters
        )
        
        # Get revenue breakdown by variants and delivery types
        revenue_breakdown = await analytics_service.get_revenue_breakdown_by_variant_and_delivery(
            date_range
        )
        
        # Calculate admin fee revenue
        admin_pricing_service = AdminPricingService(db)
        config = await admin_pricing_service.get_pricing_config()
        
        admin_fee_percentage = config.subscription_percentage if config else 10.0
        estimated_admin_revenue = subscription_metrics.total_revenue * (admin_fee_percentage / 100)
        
        # Get live metrics for real-time display
        live_metrics = await analytics_service.get_live_metrics_display()
        
        # Calculate growth trends
        yesterday_start = start_date - timedelta(days=days)
        yesterday_end = start_date
        yesterday_range = DateRange(start_date=yesterday_start, end_date=yesterday_end)
        
        previous_metrics = await analytics_service.get_subscription_metrics(
            yesterday_range, filters
        )
        
        revenue_growth = (
            ((subscription_metrics.total_revenue - previous_metrics.total_revenue) / 
             previous_metrics.total_revenue * 100) 
            if previous_metrics.total_revenue > 0 else 0.0
        )
        
        subscription_growth = (
            ((subscription_metrics.total_active_subscriptions - previous_metrics.total_active_subscriptions) / 
             previous_metrics.total_active_subscriptions * 100) 
            if previous_metrics.total_active_subscriptions > 0 else 0.0
        )
        
        metrics = {
            "total_revenue": float(subscription_metrics.total_revenue),
            "active_subscriptions": subscription_metrics.total_active_subscriptions,
            "new_subscriptions": subscription_metrics.new_subscriptions,
            "canceled_subscriptions": subscription_metrics.canceled_subscriptions,
            "paused_subscriptions": subscription_metrics.paused_subscriptions,
            "average_subscription_value": float(subscription_metrics.average_subscription_value),
            "monthly_recurring_revenue": float(subscription_metrics.monthly_recurring_revenue),
            "churn_rate": subscription_metrics.churn_rate,
            "conversion_rate": subscription_metrics.conversion_rate,
            "retention_rate": subscription_metrics.retention_rate,
            "admin_fee_percentage": admin_fee_percentage,
            "estimated_admin_revenue": float(estimated_admin_revenue),
            "revenue_breakdown": revenue_breakdown,
            "live_metrics": live_metrics["live_metrics"],
            "performance_indicators": live_metrics["performance_indicators"],
            "growth_metrics": {
                "revenue_growth_percent": float(revenue_growth),
                "subscription_growth_percent": float(subscription_growth),
                "comparison_period_days": days
            },
            "date_range": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": days
            }
        }
        
        return Response(
            success=True,
            data=metrics,
            message="Real-time revenue metrics retrieved successfully"
        )
    except APIException:
        raise
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to get revenue metrics: {str(e)}"
        )

@router.post("/preview-impact")
async def preview_pricing_impact(
    request: PricingImpactPreviewRequest,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Implement impact analysis for percentage changes."""
    try:
        admin_pricing_service = AdminPricingService(db)
        
        impact_analysis = await admin_pricing_service.preview_pricing_impact(
            proposed_changes=request.proposed_changes,
            admin_user_id=current_user.id
        )
        
        return Response(
            success=True,
            data=impact_analysis,
            message="Pricing impact analysis completed successfully"
        )
    except APIException:
        raise
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to preview pricing impact: {str(e)}"
        )

@router.get("/cost-comparison")
async def get_cost_comparison_tools(
    subscription_id: Optional[str] = Query(None),
    sample_variant_ids: Optional[List[str]] = Query(None),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Add cost comparison tools and affected subscription counts."""
    try:
        admin_pricing_service = AdminPricingService(db)
        
        # Convert string IDs to UUIDs if provided
        subscription_uuid = UUID(subscription_id) if subscription_id else None
        variant_uuids = [UUID(vid) for vid in sample_variant_ids] if sample_variant_ids else None
        
        comparison_data = await admin_pricing_service.get_cost_comparison_tools(
            subscription_id=subscription_uuid,
            sample_variants=variant_uuids
        )
        
        return Response(
            success=True,
            data=comparison_data,
            message="Cost comparison tools retrieved successfully"
        )
    except APIException:
        raise
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to get cost comparison tools: {str(e)}"
        )

@router.put("/subscription-percentage")
async def update_subscription_percentage(
    request: UpdateSubscriptionPercentageRequest,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Update subscription percentage with validation."""
    try:
        admin_pricing_service = AdminPricingService(db)
        
        updated_config = await admin_pricing_service.update_subscription_percentage(
            percentage=request.percentage,
            admin_user_id=current_user.id,
            change_reason=request.change_reason
        )
        
        return Response(
            success=True,
            data=updated_config.to_dict(),
            message=f"Subscription percentage updated to {request.percentage}% successfully"
        )
    except APIException:
        raise
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to update subscription percentage: {str(e)}"
        )

@router.put("/delivery-costs")
async def update_delivery_costs(
    request: UpdateDeliveryCostsRequest,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Update delivery costs with validation."""
    try:
        admin_pricing_service = AdminPricingService(db)
        
        updated_config = await admin_pricing_service.update_delivery_costs(
            delivery_costs=request.delivery_costs,
            admin_user_id=current_user.id,
            change_reason=request.change_reason
        )
        
        return Response(
            success=True,
            data=updated_config.to_dict(),
            message="Delivery costs updated successfully"
        )
    except APIException:
        raise
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to update delivery costs: {str(e)}"
        )

@router.post("/bulk-update")
async def bulk_pricing_update(
    request: BulkPricingUpdateRequest,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Create bulk pricing update functionality with confirmation workflows."""
    try:
        admin_pricing_service = AdminPricingService(db)
        
        # If not confirmed, return preview of changes
        if not request.confirm_bulk_update:
            proposed_changes = {}
            if request.subscription_percentage is not None:
                proposed_changes["subscription_percentage"] = request.subscription_percentage
            if request.delivery_costs is not None:
                proposed_changes["delivery_costs"] = request.delivery_costs
            if request.tax_rates is not None:
                proposed_changes["tax_rates"] = request.tax_rates
            
            impact_analysis = await admin_pricing_service.preview_pricing_impact(
                proposed_changes=proposed_changes,
                admin_user_id=current_user.id
            )
            
            return Response(
                success=True,
                data={
                    "preview": True,
                    "impact_analysis": impact_analysis,
                    "confirmation_required": True,
                    "message": "Review the impact analysis and confirm to proceed with bulk update"
                },
                message="Bulk pricing update preview generated. Confirmation required to proceed."
            )
        
        # Perform bulk update with confirmation
        results = []
        
        # Update subscription percentage if provided
        if request.subscription_percentage is not None:
            config = await admin_pricing_service.update_subscription_percentage(
                percentage=request.subscription_percentage,
                admin_user_id=current_user.id,
                change_reason=request.change_reason or "Bulk pricing update"
            )
            results.append({
                "type": "subscription_percentage",
                "old_value": None,  # Would need to track previous value
                "new_value": request.subscription_percentage,
                "config_id": str(config.id)
            })
        
        # Update delivery costs if provided
        if request.delivery_costs is not None:
            config = await admin_pricing_service.update_delivery_costs(
                delivery_costs=request.delivery_costs,
                admin_user_id=current_user.id,
                change_reason=request.change_reason or "Bulk pricing update"
            )
            results.append({
                "type": "delivery_costs",
                "old_value": None,  # Would need to track previous value
                "new_value": request.delivery_costs,
                "config_id": str(config.id)
            })
        
        return Response(
            success=True,
            data={
                "bulk_update_completed": True,
                "updates_applied": results,
                "total_updates": len(results)
            },
            message=f"Bulk pricing update completed successfully. {len(results)} updates applied."
        )
        
    except APIException:
        raise
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to perform bulk pricing update: {str(e)}"
        )

@router.get("/audit-log")
async def get_pricing_audit_log(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    admin_user_id: Optional[str] = Query(None),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get pricing configuration audit log."""
    try:
        admin_pricing_service = AdminPricingService(db)
        
        admin_uuid = UUID(admin_user_id) if admin_user_id else None
        
        audit_log = await admin_pricing_service.get_pricing_audit_log(
            page=page,
            limit=limit,
            admin_user_id=admin_uuid
        )
        
        return Response(
            success=True,
            data=audit_log,
            message="Pricing audit log retrieved successfully"
        )
    except APIException:
        raise
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to get pricing audit log: {str(e)}"
        )

@router.get("/affected-subscriptions")
async def get_affected_subscriptions_count(
    proposed_percentage: Optional[float] = Query(None),
    proposed_delivery_costs: Optional[str] = Query(None),  # JSON string
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get count of subscriptions that would be affected by pricing changes."""
    try:
        admin_pricing_service = AdminPricingService(db)
        
        # Build proposed changes
        proposed_changes = {}
        if proposed_percentage is not None:
            proposed_changes["subscription_percentage"] = proposed_percentage
        
        if proposed_delivery_costs:
            import json
            try:
                delivery_costs_dict = json.loads(proposed_delivery_costs)
                proposed_changes["delivery_costs"] = delivery_costs_dict
            except json.JSONDecodeError:
                raise APIException(
                    status_code=400,
                    message="Invalid JSON format for proposed_delivery_costs"
                )
        
        if not proposed_changes:
            raise APIException(
                status_code=400,
                message="At least one proposed change must be provided"
            )
        
        # Get impact analysis
        impact_analysis = await admin_pricing_service.preview_pricing_impact(
            proposed_changes=proposed_changes,
            admin_user_id=current_user.id
        )
        
        # Extract affected subscription counts
        affected_data = {
            "total_affected_subscriptions": impact_analysis["affected_subscriptions_count"],
            "increased_cost_count": impact_analysis["summary"]["increased_cost_count"],
            "decreased_cost_count": impact_analysis["summary"]["decreased_cost_count"],
            "no_change_count": impact_analysis["summary"]["no_change_count"],
            "total_revenue_impact": impact_analysis["total_revenue_impact"],
            "average_cost_change": impact_analysis["summary"]["average_cost_change"],
            "max_cost_increase": impact_analysis["summary"]["max_cost_increase"],
            "max_cost_decrease": impact_analysis["summary"]["max_cost_decrease"],
            "proposed_changes": proposed_changes
        }
        
        return Response(
            success=True,
            data=affected_data,
            message="Affected subscriptions count retrieved successfully"
        )
    except APIException:
        raise
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to get affected subscriptions count: {str(e)}"
        )

# Payment Analytics Routes

@router.get("/payment-analytics-dashboard")
async def get_payment_analytics_dashboard(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get comprehensive payment analytics for admin dashboard display."""
    try:
        analytics_service = AnalyticsService(db)
        
        # Calculate date range
        from datetime import datetime, timedelta
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        from services.analytics import DateRange
        date_range = DateRange(start_date=start_date, end_date=end_date)
        
        # Get comprehensive payment analytics
        payment_analytics = await analytics_service.get_payment_success_analytics(
            date_range=date_range,
            breakdown_by=["payment_method", "country", "failure_reason"]
        )
        
        # Get payment failure patterns and alerts
        failure_patterns = await analytics_service.monitor_payment_success_rate_and_failures(
            monitoring_window_hours=24
        )
        
        # Get payment trends for visualization
        daily_trends = []
        current_date = start_date
        while current_date <= end_date:
            day_start = current_date.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1)
            
            day_range = DateRange(start_date=day_start, end_date=day_end)
            day_analytics = await analytics_service.get_payment_success_analytics(
                date_range=day_range,
                breakdown_by=[]
            )
            
            daily_trends.append({
                "date": current_date.date().isoformat(),
                "total_payments": day_analytics.total_payments,
                "successful_payments": day_analytics.successful_payments,
                "failed_payments": day_analytics.failed_payments,
                "success_rate": day_analytics.success_rate,
                "total_volume": float(day_analytics.total_volume),
                "average_amount": float(day_analytics.average_payment_amount)
            })
            
            current_date += timedelta(days=1)
        
        # Calculate performance metrics
        previous_period_start = start_date - timedelta(days=days)
        previous_period_end = start_date
        previous_range = DateRange(start_date=previous_period_start, end_date=previous_period_end)
        
        previous_analytics = await analytics_service.get_payment_success_analytics(
            date_range=previous_range,
            breakdown_by=[]
        )
        
        # Calculate growth metrics
        volume_growth = (
            ((payment_analytics.total_volume - previous_analytics.total_volume) / 
             previous_analytics.total_volume * 100) 
            if previous_analytics.total_volume > 0 else 0.0
        )
        
        success_rate_change = payment_analytics.success_rate - previous_analytics.success_rate
        
        # Identify top failure reasons
        top_failure_reasons = sorted(
            payment_analytics.failure_analysis.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        # Calculate method performance rankings
        method_rankings = []
        for method, stats in payment_analytics.breakdown_by_method.items():
            method_rankings.append({
                "payment_method": method,
                "success_rate": stats.get("success_rate", 0),
                "total_payments": stats.get("total_payments", 0),
                "volume": stats.get("volume", 0),
                "rank": 0  # Will be set after sorting
            })
        
        method_rankings.sort(key=lambda x: x["success_rate"], reverse=True)
        for i, method in enumerate(method_rankings):
            method["rank"] = i + 1
        
        dashboard_data = {
            "summary": {
                "total_payments": payment_analytics.total_payments,
                "successful_payments": payment_analytics.successful_payments,
                "failed_payments": payment_analytics.failed_payments,
                "success_rate": payment_analytics.success_rate,
                "total_volume": float(payment_analytics.total_volume),
                "average_payment_amount": float(payment_analytics.average_payment_amount),
                "volume_growth_percent": float(volume_growth),
                "success_rate_change": float(success_rate_change)
            },
            "trends": {
                "daily_trends": daily_trends,
                "period_comparison": {
                    "current_period": {
                        "start_date": start_date.isoformat(),
                        "end_date": end_date.isoformat(),
                        "total_volume": float(payment_analytics.total_volume),
                        "success_rate": payment_analytics.success_rate
                    },
                    "previous_period": {
                        "start_date": previous_period_start.isoformat(),
                        "end_date": previous_period_end.isoformat(),
                        "total_volume": float(previous_analytics.total_volume),
                        "success_rate": previous_analytics.success_rate
                    }
                }
            },
            "breakdowns": {
                "by_payment_method": payment_analytics.breakdown_by_method,
                "by_country": payment_analytics.breakdown_by_country,
                "method_rankings": method_rankings
            },
            "failure_analysis": {
                "top_failure_reasons": [
                    {"reason": reason, "count": count, "percentage": round(count / payment_analytics.failed_payments * 100, 2)}
                    for reason, count in top_failure_reasons
                ] if payment_analytics.failed_payments > 0 else [],
                "failure_patterns": failure_patterns["failure_analysis"],
                "alerts": failure_patterns["alerts"],
                "recommendations": failure_patterns["recommendations"]
            },
            "real_time_monitoring": {
                "last_24_hours": failure_patterns["overall_metrics"],
                "hourly_breakdown": failure_patterns["hourly_breakdown"][-12:],  # Last 12 hours
                "current_health_status": "good" if payment_analytics.success_rate > 95 else "warning" if payment_analytics.success_rate > 85 else "critical"
            },
            "export_options": {
                "available_formats": ["csv", "json", "excel"],
                "date_range": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "days": days
                }
            }
        }
        
        return Response(
            success=True,
            data=dashboard_data,
            message="Payment analytics dashboard data retrieved successfully"
        )
    except APIException:
        raise
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to get payment analytics dashboard: {str(e)}"
        )

@router.get("/payment-analytics")
async def get_payment_analytics(
    days: int = Query(30, ge=1, le=365),
    breakdown_by: List[str] = Query(["payment_method", "country"]),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Display payment success rates and failure analysis."""
    try:
        analytics_service = AnalyticsService(db)
        
        # Calculate date range
        from datetime import datetime, timedelta
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        from services.analytics import DateRange
        date_range = DateRange(start_date=start_date, end_date=end_date)
        
        # Get payment analytics
        payment_analytics = await analytics_service.get_payment_success_analytics(
            date_range=date_range,
            breakdown_by=breakdown_by
        )
        
        # Format response
        analytics_data = {
            "summary": {
                "total_payments": payment_analytics.total_payments,
                "successful_payments": payment_analytics.successful_payments,
                "failed_payments": payment_analytics.failed_payments,
                "success_rate": payment_analytics.success_rate,
                "total_volume": float(payment_analytics.total_volume),
                "average_payment_amount": float(payment_analytics.average_payment_amount)
            },
            "breakdown_by_method": payment_analytics.breakdown_by_method,
            "breakdown_by_country": payment_analytics.breakdown_by_country,
            "failure_analysis": payment_analytics.failure_analysis,
            "date_range": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": days
            }
        }
        
        return Response(
            success=True,
            data=analytics_data,
            message="Payment analytics retrieved successfully"
        )
    except APIException:
        raise
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to get payment analytics: {str(e)}"
        )

@router.get("/payment-failure-patterns")
async def get_payment_failure_patterns(
    days: int = Query(30, ge=1, le=365),
    min_failure_count: int = Query(5, ge=1),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Create alerts for unusual payment patterns and high failure rates."""
    try:
        analytics_service = AnalyticsService(db)
        
        # Calculate date range
        from datetime import datetime, timedelta
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        from services.analytics import DateRange
        date_range = DateRange(start_date=start_date, end_date=end_date)
        
        # Get payment analytics for failure analysis
        payment_analytics = await analytics_service.get_payment_success_analytics(
            date_range=date_range,
            breakdown_by=["payment_method", "country", "failure_reason"]
        )
        
        # Analyze failure patterns
        failure_patterns = []
        alerts = []
        
        # Check for high failure rates by payment method
        for method, stats in payment_analytics.breakdown_by_method.items():
            failure_rate = (stats.get('failed_payments', 0) / max(stats.get('total_payments', 1), 1)) * 100
            if failure_rate > 20 and stats.get('failed_payments', 0) >= min_failure_count:  # Alert if >20% failure rate
                alerts.append({
                    "type": "high_failure_rate_by_method",
                    "payment_method": method,
                    "failure_rate": round(failure_rate, 2),
                    "failed_payments": stats.get('failed_payments', 0),
                    "total_payments": stats.get('total_payments', 0),
                    "severity": "high" if failure_rate > 50 else "medium"
                })
        
        # Check for high failure rates by country
        for country, stats in payment_analytics.breakdown_by_country.items():
            failure_rate = (stats.get('failed_payments', 0) / max(stats.get('total_payments', 1), 1)) * 100
            if failure_rate > 30 and stats.get('failed_payments', 0) >= min_failure_count:  # Alert if >30% failure rate
                alerts.append({
                    "type": "high_failure_rate_by_country",
                    "country": country,
                    "failure_rate": round(failure_rate, 2),
                    "failed_payments": stats.get('failed_payments', 0),
                    "total_payments": stats.get('total_payments', 0),
                    "severity": "high" if failure_rate > 60 else "medium"
                })
        
        # Analyze failure reasons
        failure_reasons = payment_analytics.failure_analysis
        for reason, count in failure_reasons.items():
            if count >= min_failure_count:
                failure_patterns.append({
                    "failure_reason": reason,
                    "count": count,
                    "percentage": round((count / max(payment_analytics.failed_payments, 1)) * 100, 2)
                })
        
        # Sort patterns by count
        failure_patterns.sort(key=lambda x: x['count'], reverse=True)
        
        # Check for unusual patterns (sudden spikes)
        if payment_analytics.failed_payments > payment_analytics.successful_payments * 0.5:  # More than 50% failures
            alerts.append({
                "type": "unusual_failure_spike",
                "description": "Unusually high failure rate detected",
                "failure_rate": round((payment_analytics.failed_payments / max(payment_analytics.total_payments, 1)) * 100, 2),
                "severity": "critical"
            })
        
        patterns_data = {
            "alerts": alerts,
            "failure_patterns": failure_patterns,
            "summary": {
                "total_alerts": len(alerts),
                "critical_alerts": len([a for a in alerts if a.get('severity') == 'critical']),
                "high_alerts": len([a for a in alerts if a.get('severity') == 'high']),
                "medium_alerts": len([a for a in alerts if a.get('severity') == 'medium'])
            },
            "analysis_period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": days
            }
        }
        
        return Response(
            success=True,
            data=patterns_data,
            message="Payment failure patterns analyzed successfully"
        )
    except APIException:
        raise
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to analyze payment failure patterns: {str(e)}"
        )

@router.get("/export/comprehensive-analytics")
async def export_comprehensive_analytics(
    format: str = Query("csv", regex="^(csv|json|excel)$"),
    days: int = Query(30, ge=1, le=365),
    include_cost_data: bool = Query(True),
    include_payment_data: bool = Query(True),
    include_subscription_data: bool = Query(True),
    include_failure_analysis: bool = Query(True),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Export comprehensive analytics data including costs, payments, and failure analysis."""
    try:
        from fastapi.responses import StreamingResponse
        import io
        import json as json_lib
        from datetime import datetime, timedelta
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        export_data = {}
        
        # Get cost data if requested
        if include_cost_data:
            admin_pricing_service = AdminPricingService(db)
            
            # Get current pricing config
            pricing_config = await admin_pricing_service.get_pricing_config()
            export_data["pricing_config"] = pricing_config.to_dict() if pricing_config else {}
            
            # Get pricing audit log
            audit_log = await admin_pricing_service.get_pricing_audit_log(page=1, limit=1000)
            export_data["pricing_audit_log"] = audit_log["audit_entries"]
            
            # Get cost comparison data
            comparison_data = await admin_pricing_service.get_cost_comparison_tools()
            export_data["cost_comparison"] = comparison_data
        
        # Get payment data if requested
        if include_payment_data:
            analytics_service = AnalyticsService(db)
            
            from services.analytics import DateRange
            date_range = DateRange(start_date=start_date, end_date=end_date)
            
            # Get comprehensive payment analytics
            payment_analytics = await analytics_service.get_payment_success_analytics(
                date_range=date_range,
                breakdown_by=["payment_method", "country", "failure_reason"]
            )
            
            export_data["payment_analytics"] = {
                "summary": {
                    "total_payments": payment_analytics.total_payments,
                    "successful_payments": payment_analytics.successful_payments,
                    "failed_payments": payment_analytics.failed_payments,
                    "success_rate": payment_analytics.success_rate,
                    "total_volume": float(payment_analytics.total_volume),
                    "average_payment_amount": float(payment_analytics.average_payment_amount)
                },
                "breakdown_by_method": payment_analytics.breakdown_by_method,
                "breakdown_by_country": payment_analytics.breakdown_by_country,
                "failure_analysis": payment_analytics.failure_analysis
            }
        
        # Get subscription data if requested
        if include_subscription_data:
            if 'analytics_service' not in locals():
                analytics_service = AnalyticsService(db)
                date_range = DateRange(start_date=start_date, end_date=end_date)
            
            from services.analytics import AnalyticsFilters
            filters = AnalyticsFilters()
            
            subscription_metrics = await analytics_service.get_subscription_metrics(
                date_range, filters
            )
            
            export_data["subscription_metrics"] = {
                "total_active_subscriptions": subscription_metrics.total_active_subscriptions,
                "new_subscriptions": subscription_metrics.new_subscriptions,
                "canceled_subscriptions": subscription_metrics.canceled_subscriptions,
                "paused_subscriptions": subscription_metrics.paused_subscriptions,
                "total_revenue": float(subscription_metrics.total_revenue),
                "average_subscription_value": float(subscription_metrics.average_subscription_value),
                "monthly_recurring_revenue": float(subscription_metrics.monthly_recurring_revenue),
                "churn_rate": subscription_metrics.churn_rate,
                "conversion_rate": subscription_metrics.conversion_rate,
                "retention_rate": subscription_metrics.retention_rate,
                "plan_breakdown": subscription_metrics.plan_breakdown,
                "geographic_breakdown": subscription_metrics.geographic_breakdown
            }
        
        # Get failure analysis if requested
        if include_failure_analysis:
            if 'analytics_service' not in locals():
                analytics_service = AnalyticsService(db)
            
            failure_patterns = await analytics_service.monitor_payment_success_rate_and_failures(
                monitoring_window_hours=24
            )
            
            export_data["failure_analysis"] = {
                "alerts": failure_patterns["alerts"],
                "failure_breakdown": failure_patterns["failure_analysis"],
                "hourly_breakdown": failure_patterns["hourly_breakdown"],
                "recommendations": failure_patterns["recommendations"]
            }
        
        # Add metadata
        export_data["export_metadata"] = {
            "exported_at": datetime.now().isoformat(),
            "exported_by": str(current_user.id),
            "export_type": "comprehensive_analytics",
            "date_range": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": days
            },
            "includes_cost_data": include_cost_data,
            "includes_payment_data": include_payment_data,
            "includes_subscription_data": include_subscription_data,
            "includes_failure_analysis": include_failure_analysis
        }
        
        # Generate export based on format
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if format == "json":
            output = io.StringIO()
            json_lib.dump(export_data, output, indent=2, default=str)
            content = output.getvalue().encode('utf-8')
            
            return StreamingResponse(
                io.BytesIO(content),
                media_type="application/json",
                headers={
                    "Content-Disposition": f"attachment; filename=comprehensive_analytics_{timestamp}.json"
                }
            )
        
        elif format == "csv":
            output = io.StringIO()
            
            # Write comprehensive analytics to CSV
            output.write("COMPREHENSIVE ANALYTICS EXPORT\n")
            output.write(f"Generated: {datetime.now().isoformat()}\n")
            output.write(f"Date Range: {start_date.date()} to {end_date.date()}\n\n")
            
            # Write subscription metrics
            if include_subscription_data and "subscription_metrics" in export_data:
                output.write("SUBSCRIPTION METRICS\n")
                metrics = export_data["subscription_metrics"]
                output.write("Metric,Value\n")
                for key, value in metrics.items():
                    if not isinstance(value, dict):
                        output.write(f"{key},{value}\n")
                output.write("\n")
            
            # Write payment analytics summary
            if include_payment_data and "payment_analytics" in export_data:
                output.write("PAYMENT ANALYTICS SUMMARY\n")
                summary = export_data["payment_analytics"]["summary"]
                output.write("Metric,Value\n")
                for key, value in summary.items():
                    output.write(f"{key},{value}\n")
                output.write("\n")
                
                # Write payment method breakdown
                output.write("PAYMENT METHOD BREAKDOWN\n")
                output.write("Method,Total Payments,Successful Payments,Success Rate,Volume\n")
                for method, stats in export_data["payment_analytics"]["breakdown_by_method"].items():
                    output.write(f"{method},{stats.get('total_payments', 0)},{stats.get('successful_payments', 0)},{stats.get('success_rate', 0)},{stats.get('volume', 0)}\n")
                output.write("\n")
            
            # Write failure analysis
            if include_failure_analysis and "failure_analysis" in export_data:
                output.write("FAILURE ANALYSIS\n")
                output.write("Failure Reason,Count\n")
                for failure in export_data["failure_analysis"]["failure_breakdown"]:
                    output.write(f"{failure.get('failure_reason', 'unknown')},{failure.get('count', 0)}\n")
                output.write("\n")
            
            # Write pricing audit log
            if include_cost_data and "pricing_audit_log" in export_data:
                output.write("PRICING AUDIT LOG\n")
                output.write("ID,Subscription Percentage,Updated By,Version,Active,Change Reason,Created At\n")
                for entry in export_data["pricing_audit_log"]:
                    output.write(f"{entry.get('id', '')},{entry.get('subscription_percentage', '')},{entry.get('updated_by', '')},{entry.get('version', '')},{entry.get('is_active', '')},{entry.get('change_reason', '')},{entry.get('created_at', '')}\n")
                output.write("\n")
            
            content = output.getvalue().encode('utf-8')
            
            return StreamingResponse(
                io.BytesIO(content),
                media_type="text/csv",
                headers={
                    "Content-Disposition": f"attachment; filename=comprehensive_analytics_{timestamp}.csv"
                }
            )
        
        elif format == "excel":
            # For Excel format, return structured data that can be processed by frontend
            output = io.StringIO()
            output.write("Comprehensive Analytics Export\n")
            output.write(f"Generated: {datetime.now().isoformat()}\n")
            output.write(f"Date Range: {start_date.date()} to {end_date.date()}\n\n")
            
            if include_subscription_data:
                output.write("SUBSCRIPTION DATA INCLUDED\n")
            if include_payment_data:
                output.write("PAYMENT DATA INCLUDED\n")
            if include_cost_data:
                output.write("COST DATA INCLUDED\n")
            if include_failure_analysis:
                output.write("FAILURE ANALYSIS INCLUDED\n")
            
            output.write(f"\nFull structured data available in JSON format.\n")
            content = output.getvalue().encode('utf-8')
            
            return StreamingResponse(
                io.BytesIO(content),
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={
                    "Content-Disposition": f"attachment; filename=comprehensive_analytics_{timestamp}.xlsx"
                }
            )
        
    except APIException:
        raise
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to export comprehensive analytics: {str(e)}"
        )

@router.get("/export/cost-payment-data")
async def export_cost_payment_data(
    format: str = Query("csv", regex="^(csv|json|excel)$"),
    days: int = Query(30, ge=1, le=365),
    include_cost_data: bool = Query(True),
    include_payment_data: bool = Query(True),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Implement export functionality for all cost and payment data."""
    try:
        from fastapi.responses import StreamingResponse
        import io
        import json as json_lib
        from datetime import datetime, timedelta
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        export_data = {}
        
        # Get cost data if requested
        if include_cost_data:
            admin_pricing_service = AdminPricingService(db)
            
            # Get current pricing config
            pricing_config = await admin_pricing_service.get_pricing_config()
            export_data["pricing_config"] = pricing_config.to_dict() if pricing_config else {}
            
            # Get pricing audit log
            audit_log = await admin_pricing_service.get_pricing_audit_log(page=1, limit=1000)
            export_data["pricing_audit_log"] = audit_log["audit_entries"]
            
            # Get cost comparison data
            comparison_data = await admin_pricing_service.get_cost_comparison_tools()
            export_data["cost_comparison"] = comparison_data
        
        # Get payment data if requested
        if include_payment_data:
            analytics_service = AnalyticsService(db)
            
            from services.analytics import DateRange
            date_range = DateRange(start_date=start_date, end_date=end_date)
            
            # Get payment analytics
            payment_analytics = await analytics_service.get_payment_success_analytics(
                date_range=date_range,
                breakdown_by=["payment_method", "country", "failure_reason"]
            )
            
            export_data["payment_analytics"] = {
                "summary": {
                    "total_payments": payment_analytics.total_payments,
                    "successful_payments": payment_analytics.successful_payments,
                    "failed_payments": payment_analytics.failed_payments,
                    "success_rate": payment_analytics.success_rate,
                    "total_volume": float(payment_analytics.total_volume),
                    "average_payment_amount": float(payment_analytics.average_payment_amount)
                },
                "breakdown_by_method": payment_analytics.breakdown_by_method,
                "breakdown_by_country": payment_analytics.breakdown_by_country,
                "failure_analysis": payment_analytics.failure_analysis
            }
        
        # Add metadata
        export_data["export_metadata"] = {
            "exported_at": datetime.now().isoformat(),
            "exported_by": str(current_user.id),
            "date_range": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": days
            },
            "includes_cost_data": include_cost_data,
            "includes_payment_data": include_payment_data
        }
        
        # Generate export based on format
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if format == "json":
            output = io.StringIO()
            json_lib.dump(export_data, output, indent=2, default=str)
            content = output.getvalue().encode('utf-8')
            
            return StreamingResponse(
                io.BytesIO(content),
                media_type="application/json",
                headers={
                    "Content-Disposition": f"attachment; filename=cost_payment_export_{timestamp}.json"
                }
            )
        
        elif format == "csv":
            output = io.StringIO()
            
            # Write cost data to CSV
            if include_cost_data and "pricing_audit_log" in export_data:
                output.write("PRICING AUDIT LOG\n")
                output.write("ID,Subscription Percentage,Updated By,Version,Active,Change Reason,Created At\n")
                for entry in export_data["pricing_audit_log"]:
                    output.write(f"{entry.get('id', '')},{entry.get('subscription_percentage', '')},{entry.get('updated_by', '')},{entry.get('version', '')},{entry.get('is_active', '')},{entry.get('change_reason', '')},{entry.get('created_at', '')}\n")
                output.write("\n")
            
            # Write payment data to CSV
            if include_payment_data and "payment_analytics" in export_data:
                output.write("PAYMENT ANALYTICS SUMMARY\n")
                summary = export_data["payment_analytics"]["summary"]
                output.write("Metric,Value\n")
                for key, value in summary.items():
                    output.write(f"{key},{value}\n")
                output.write("\n")
            
            content = output.getvalue().encode('utf-8')
            
            return StreamingResponse(
                io.BytesIO(content),
                media_type="text/csv",
                headers={
                    "Content-Disposition": f"attachment; filename=cost_payment_export_{timestamp}.csv"
                }
            )
        
        elif format == "excel":
            # For Excel format, we'll use a simplified approach
            # In a real implementation, you'd use openpyxl or xlsxwriter
            output = io.StringIO()
            output.write("Cost and Payment Data Export\n")
            output.write(f"Generated: {datetime.now().isoformat()}\n")
            output.write(f"Date Range: {start_date.date()} to {end_date.date()}\n\n")
            
            if include_cost_data:
                output.write("COST DATA INCLUDED\n")
            if include_payment_data:
                output.write("PAYMENT DATA INCLUDED\n")
            
            output.write(f"\nFull data available in JSON format.\n")
            content = output.getvalue().encode('utf-8')
            
            return StreamingResponse(
                io.BytesIO(content),
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={
                    "Content-Disposition": f"attachment; filename=cost_payment_export_{timestamp}.xlsx"
                }
            )
        
    except APIException:
        raise
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to export cost and payment data: {str(e)}"
        )

@router.get("/alerts/payment-monitoring")
async def get_payment_monitoring_alerts(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get real-time payment monitoring alerts for unusual patterns and high failure rates."""
    try:
        analytics_service = AnalyticsService(db)
        
        # Get current monitoring data
        monitoring_data = await analytics_service.monitor_payment_success_rate_and_failures(
            monitoring_window_hours=24
        )
        
        # Get additional context for alerts
        from datetime import datetime, timedelta
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)  # Last 7 days for context
        
        from services.analytics import DateRange
        date_range = DateRange(start_date=start_date, end_date=end_date)
        
        weekly_analytics = await analytics_service.get_payment_success_analytics(
            date_range=date_range,
            breakdown_by=["payment_method", "country"]
        )
        
        # Enhanced alert analysis
        enhanced_alerts = []
        
        # Process existing alerts and add context
        for alert in monitoring_data["alerts"]:
            enhanced_alert = alert.copy()
            
            if alert["type"] == "critical" and "success rate" in alert["message"].lower():
                enhanced_alert["context"] = {
                    "weekly_average": weekly_analytics.success_rate,
                    "trend": "declining" if monitoring_data["overall_metrics"]["success_rate"] < weekly_analytics.success_rate else "stable",
                    "impact_level": "high"
                }
                enhanced_alert["suggested_actions"] = [
                    "Check payment processor status",
                    "Review recent configuration changes",
                    "Contact payment provider support",
                    "Implement emergency fallback payment methods"
                ]
            
            elif alert["type"] == "warning":
                enhanced_alert["context"] = {
                    "weekly_average": weekly_analytics.success_rate,
                    "trend": "declining" if monitoring_data["overall_metrics"]["success_rate"] < weekly_analytics.success_rate else "stable",
                    "impact_level": "medium"
                }
                enhanced_alert["suggested_actions"] = [
                    "Monitor payment patterns closely",
                    "Review failure reasons",
                    "Consider adjusting fraud detection settings",
                    "Prepare customer communication if needed"
                ]
            
            enhanced_alerts.append(enhanced_alert)
        
        # Add custom business logic alerts
        
        # Check for unusual failure spikes by payment method
        for method, stats in weekly_analytics.breakdown_by_method.items():
            method_failure_rate = ((stats.get('total_payments', 0) - stats.get('successful_payments', 0)) / 
                                 max(stats.get('total_payments', 1), 1)) * 100
            
            if method_failure_rate > 15 and stats.get('total_payments', 0) > 10:  # More than 15% failure rate
                enhanced_alerts.append({
                    "type": "warning",
                    "message": f"High failure rate for {method}: {method_failure_rate:.1f}%",
                    "threshold": 15,
                    "current_value": method_failure_rate,
                    "context": {
                        "payment_method": method,
                        "total_payments": stats.get('total_payments', 0),
                        "impact_level": "medium"
                    },
                    "suggested_actions": [
                        f"Review {method} payment processing",
                        "Check with payment provider for issues",
                        "Consider temporarily promoting alternative payment methods"
                    ]
                })
        
        # Check for geographic payment issues
        for country, stats in weekly_analytics.breakdown_by_country.items():
            country_failure_rate = ((stats.get('total_payments', 0) - stats.get('successful_payments', 0)) / 
                                  max(stats.get('total_payments', 1), 1)) * 100
            
            if country_failure_rate > 20 and stats.get('total_payments', 0) > 5:  # More than 20% failure rate
                enhanced_alerts.append({
                    "type": "warning",
                    "message": f"High failure rate in {country}: {country_failure_rate:.1f}%",
                    "threshold": 20,
                    "current_value": country_failure_rate,
                    "context": {
                        "country": country,
                        "total_payments": stats.get('total_payments', 0),
                        "impact_level": "medium"
                    },
                    "suggested_actions": [
                        f"Review payment processing for {country}",
                        "Check local payment regulations",
                        "Consider region-specific payment methods"
                    ]
                })
        
        # Check for volume anomalies
        current_hour_volume = sum(
            h.get("total_payments", 0) for h in monitoring_data["hourly_breakdown"][-1:]
        )
        average_hourly_volume = sum(
            h.get("total_payments", 0) for h in monitoring_data["hourly_breakdown"]
        ) / len(monitoring_data["hourly_breakdown"]) if monitoring_data["hourly_breakdown"] else 0
        
        if current_hour_volume < average_hourly_volume * 0.3 and average_hourly_volume > 5:  # 70% drop
            enhanced_alerts.append({
                "type": "warning",
                "message": f"Significant drop in payment volume: {current_hour_volume} vs avg {average_hourly_volume:.1f}",
                "threshold": average_hourly_volume * 0.7,
                "current_value": current_hour_volume,
                "context": {
                    "volume_drop_percent": ((average_hourly_volume - current_hour_volume) / average_hourly_volume * 100),
                    "impact_level": "medium"
                },
                "suggested_actions": [
                    "Check for system outages",
                    "Review website performance",
                    "Verify payment form functionality",
                    "Check for marketing campaign issues"
                ]
            })
        
        # Sort alerts by severity
        alert_priority = {"critical": 3, "warning": 2, "info": 1}
        enhanced_alerts.sort(key=lambda x: alert_priority.get(x["type"], 0), reverse=True)
        
        alert_summary = {
            "total_alerts": len(enhanced_alerts),
            "critical_count": len([a for a in enhanced_alerts if a["type"] == "critical"]),
            "warning_count": len([a for a in enhanced_alerts if a["type"] == "warning"]),
            "info_count": len([a for a in enhanced_alerts if a["type"] == "info"]),
            "overall_health_status": (
                "critical" if any(a["type"] == "critical" for a in enhanced_alerts)
                else "warning" if any(a["type"] == "warning" for a in enhanced_alerts)
                else "good"
            )
        }
        
        response_data = {
            "alert_summary": alert_summary,
            "alerts": enhanced_alerts,
            "monitoring_data": {
                "current_success_rate": monitoring_data["overall_metrics"]["success_rate"],
                "total_payments_24h": monitoring_data["overall_metrics"]["total_payments"],
                "failed_payments_24h": monitoring_data["overall_metrics"]["failed_payments"],
                "monitoring_window_hours": 24
            },
            "context_data": {
                "weekly_success_rate": weekly_analytics.success_rate,
                "weekly_total_payments": weekly_analytics.total_payments,
                "weekly_volume": float(weekly_analytics.total_volume)
            },
            "last_updated": datetime.now().isoformat(),
            "auto_refresh_recommended": True,
            "refresh_interval_seconds": 300  # 5 minutes
        }
        
        return Response(
            success=True,
            data=response_data,
            message="Payment monitoring alerts retrieved successfully"
        )
    except APIException:
        raise
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to get payment monitoring alerts: {str(e)}"
        )

@router.get("/payment-trends")
async def get_payment_trends(
    days: int = Query(30, ge=7, le=365),
    granularity: str = Query("daily", regex="^(daily|weekly|monthly)$"),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get payment trends over time for dashboard visualization."""
    try:
        analytics_service = AnalyticsService(db)
        
        # Calculate date range
        from datetime import datetime, timedelta
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Get payment trends (this would need to be implemented in analytics service)
        # For now, we'll create a simplified version
        trends_data = {
            "payment_volume_trend": [],
            "success_rate_trend": [],
            "failure_count_trend": [],
            "average_amount_trend": []
        }
        
        # Generate sample trend data (in real implementation, query actual data)
        current_date = start_date
        while current_date <= end_date:
            # This is simplified - real implementation would query actual payment data
            trends_data["payment_volume_trend"].append({
                "date": current_date.date().isoformat(),
                "total_payments": 100,  # Would be actual count
                "total_volume": 10000.0  # Would be actual volume
            })
            
            trends_data["success_rate_trend"].append({
                "date": current_date.date().isoformat(),
                "success_rate": 95.5  # Would be calculated from actual data
            })
            
            trends_data["failure_count_trend"].append({
                "date": current_date.date().isoformat(),
                "failed_payments": 5  # Would be actual count
            })
            
            trends_data["average_amount_trend"].append({
                "date": current_date.date().isoformat(),
                "average_amount": 100.0  # Would be calculated from actual data
            })
            
            # Increment date based on granularity
            if granularity == "daily":
                current_date += timedelta(days=1)
            elif granularity == "weekly":
                current_date += timedelta(weeks=1)
            elif granularity == "monthly":
                current_date += timedelta(days=30)
        
        return Response(
            success=True,
            data={
                "trends": trends_data,
                "metadata": {
                    "date_range": {
                        "start_date": start_date.isoformat(),
                        "end_date": end_date.isoformat()
                    },
                    "granularity": granularity,
                    "days": days
                }
            },
            message="Payment trends retrieved successfully"
        )
    except APIException:
        raise
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to get payment trends: {str(e)}"
        )