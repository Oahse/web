"""
Business Analytics Service
Tracks and calculates key e-commerce metrics including conversion rates,
cart abandonment, time to first purchase, refund rates, and repeat customers
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc, asc, text
from sqlalchemy.orm import selectinload
from fastapi import HTTPException

from models.analytics import (
    UserSession, AnalyticsEvent, ConversionFunnel, CustomerLifecycleMetrics,
    EventType, TrafficSource 
)
from models.orders import Order
from models.user import User
from models.refunds import Refund
from core.config import settings

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Comprehensive business analytics service"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def track_event(
        self,
        session_id: str,
        event_type: EventType,
        user_id: Optional[UUID] = None,
        event_data: Optional[Dict[str, Any]] = None,
        page_url: Optional[str] = None,
        page_title: Optional[str] = None,
        order_id: Optional[UUID] = None,
        product_id: Optional[UUID] = None,
        revenue: Optional[float] = None
    ) -> AnalyticsEvent:
        """Track an analytics event"""
        try:
            event = AnalyticsEvent(
                session_id=session_id,
                user_id=user_id,
                event_type=event_type,
                page_url=page_url,
                page_title=page_title,
                event_data=event_data or {},
                order_id=order_id,
                product_id=product_id,
                revenue=revenue
            )
            
            self.db.add(event)
            
            # Update session metrics
            await self._update_session_metrics(session_id)
            
            # Update conversion funnel
            if user_id:
                await self._update_conversion_funnel(session_id, user_id, event_type)
            
            await self.db.commit()
            return event
            
        except Exception as e:
            logger.error(f"Failed to track event: {e}")
            await self.db.rollback()
            raise
    
    async def get_conversion_metrics(
        self,
        start_date: datetime,
        end_date: datetime,
        traffic_source: Optional[TrafficSource] = None
    ) -> Dict[str, Any]:
        """Get conversion rate metrics"""
        try:
            # Base query for sessions in date range
            base_query = select(UserSession).where(
                and_(
                    UserSession.started_at >= start_date,
                    UserSession.started_at <= end_date
                )
            )
            
            if traffic_source:
                base_query = base_query.where(UserSession.traffic_source == traffic_source)
            
            # Total sessions
            total_sessions_result = await self.db.execute(
                select(func.count(UserSession.id)).select_from(base_query.subquery())
            )
            total_sessions = total_sessions_result.scalar() or 0
            
            # Converted sessions
            converted_sessions_result = await self.db.execute(
                select(func.count(UserSession.id)).select_from(
                    base_query.where(UserSession.converted == True).subquery()
                )
            )
            converted_sessions = converted_sessions_result.scalar() or 0
            
            # Conversion rate
            conversion_rate = (converted_sessions / total_sessions * 100) if total_sessions > 0 else 0
            
            # Revenue metrics
            revenue_result = await self.db.execute(
                select(
                    func.sum(UserSession.conversion_value),
                    func.avg(UserSession.conversion_value)
                ).select_from(
                    base_query.where(UserSession.converted == True).subquery()
                )
            )
            total_revenue, avg_order_value = revenue_result.first() or (0, 0)
            
            # Conversion by traffic source
            source_conversion = await self.db.execute(
                select(
                    UserSession.traffic_source,
                    func.count(UserSession.id).label('total_sessions'),
                    func.sum(func.cast(UserSession.converted, Integer)).label('converted_sessions'),
                    func.sum(UserSession.conversion_value).label('revenue')
                ).where(
                    and_(
                        UserSession.started_at >= start_date,
                        UserSession.started_at <= end_date
                    )
                ).group_by(UserSession.traffic_source)
            )
            
            source_breakdown = []
            for row in source_conversion:
                source_total = row.total_sessions or 0
                source_converted = row.converted_sessions or 0
                source_rate = (source_converted / source_total * 100) if source_total > 0 else 0
                
                source_breakdown.append({
                    "traffic_source": row.traffic_source.value if row.traffic_source else "unknown",
                    "total_sessions": source_total,
                    "converted_sessions": source_converted,
                    "conversion_rate": round(source_rate, 2),
                    "revenue": float(row.revenue or 0)
                })
            
            return {
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                "overall": {
                    "total_sessions": total_sessions,
                    "converted_sessions": converted_sessions,
                    "conversion_rate": round(conversion_rate, 2),
                    "total_revenue": float(total_revenue or 0),
                    "average_order_value": float(avg_order_value or 0)
                },
                "by_traffic_source": source_breakdown
            }
            
        except Exception as e:
            logger.error(f"Failed to get conversion metrics: {e}")
            raise HTTPException(status_code=500, detail="Failed to retrieve conversion metrics")
    
    async def get_cart_abandonment_metrics(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Get cart abandonment metrics"""
        try:
            # Sessions that added items to cart
            cart_sessions = await self.db.execute(
                select(func.count(func.distinct(AnalyticsEvent.session_id))).where(
                    and_(
                        AnalyticsEvent.event_type == EventType.CART_ADD,
                        AnalyticsEvent.timestamp >= start_date,
                        AnalyticsEvent.timestamp <= end_date
                    )
                )
            )
            total_cart_sessions = cart_sessions.scalar() or 0
            
            # Sessions that started checkout
            checkout_sessions = await self.db.execute(
                select(func.count(func.distinct(AnalyticsEvent.session_id))).where(
                    and_(
                        AnalyticsEvent.event_type == EventType.CHECKOUT_START,
                        AnalyticsEvent.timestamp >= start_date,
                        AnalyticsEvent.timestamp <= end_date
                    )
                )
            )
            total_checkout_sessions = checkout_sessions.scalar() or 0
            
            # Sessions that completed purchase
            purchase_sessions = await self.db.execute(
                select(func.count(func.distinct(AnalyticsEvent.session_id))).where(
                    and_(
                        AnalyticsEvent.event_type == EventType.PURCHASE,
                        AnalyticsEvent.timestamp >= start_date,
                        AnalyticsEvent.timestamp <= end_date
                    )
                )
            )
            total_purchase_sessions = purchase_sessions.scalar() or 0
            
            # Calculate abandonment rates
            cart_abandonment_rate = ((total_cart_sessions - total_checkout_sessions) / total_cart_sessions * 100) if total_cart_sessions > 0 else 0
            checkout_abandonment_rate = ((total_checkout_sessions - total_purchase_sessions) / total_checkout_sessions * 100) if total_checkout_sessions > 0 else 0
            overall_abandonment_rate = ((total_cart_sessions - total_purchase_sessions) / total_cart_sessions * 100) if total_cart_sessions > 0 else 0
            
            # Funnel analysis
            funnel_data = await self.db.execute(
                select(
                    ConversionFunnel.current_step,
                    func.count(ConversionFunnel.id).label('count')
                ).where(
                    and_(
                        ConversionFunnel.created_at >= start_date,
                        ConversionFunnel.created_at <= end_date
                    )
                ).group_by(ConversionFunnel.current_step).order_by(ConversionFunnel.current_step)
            )
            
            funnel_steps = []
            step_names = ["Landing", "Product View", "Add to Cart", "Checkout Start", "Purchase"]
            
            for row in funnel_data:
                step_index = row.current_step
                if 0 <= step_index < len(step_names):
                    funnel_steps.append({
                        "step": step_index,
                        "step_name": step_names[step_index],
                        "count": row.count
                    })
            
            return {
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                "abandonment_rates": {
                    "cart_abandonment_rate": round(cart_abandonment_rate, 2),
                    "checkout_abandonment_rate": round(checkout_abandonment_rate, 2),
                    "overall_abandonment_rate": round(overall_abandonment_rate, 2)
                },
                "funnel_metrics": {
                    "total_cart_sessions": total_cart_sessions,
                    "total_checkout_sessions": total_checkout_sessions,
                    "total_purchase_sessions": total_purchase_sessions
                },
                "conversion_funnel": funnel_steps
            }
            
        except Exception as e:
            logger.error(f"Failed to get cart abandonment metrics: {e}")
            raise HTTPException(status_code=500, detail="Failed to retrieve cart abandonment metrics")
    
    async def get_time_to_purchase_metrics(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Get time to first purchase metrics"""
        try:
            # Get customers who made their first purchase in the period
            first_purchase_metrics = await self.db.execute(
                select(
                    CustomerLifecycleMetrics.time_to_first_purchase_hours,
                    CustomerLifecycleMetrics.registered_at,
                    CustomerLifecycleMetrics.first_purchase_at
                ).where(
                    and_(
                        CustomerLifecycleMetrics.first_purchase_at >= start_date,
                        CustomerLifecycleMetrics.first_purchase_at <= end_date,
                        CustomerLifecycleMetrics.time_to_first_purchase_hours.isnot(None)
                    )
                )
            )
            
            times_to_purchase = []
            for row in first_purchase_metrics:
                if row.time_to_first_purchase_hours is not None:
                    times_to_purchase.append(row.time_to_first_purchase_hours)
            
            if not times_to_purchase:
                return {
                    "period": {
                        "start_date": start_date.isoformat(),
                        "end_date": end_date.isoformat()
                    },
                    "metrics": {
                        "total_first_purchases": 0,
                        "average_hours": 0,
                        "median_hours": 0,
                        "min_hours": 0,
                        "max_hours": 0
                    },
                    "distribution": []
                }
            
            # Calculate statistics
            times_to_purchase.sort()
            total_customers = len(times_to_purchase)
            average_hours = sum(times_to_purchase) / total_customers
            median_hours = times_to_purchase[total_customers // 2]
            min_hours = min(times_to_purchase)
            max_hours = max(times_to_purchase)
            
            # Create distribution buckets
            distribution = [
                {"range": "0-1 hours", "count": sum(1 for t in times_to_purchase if t <= 1)},
                {"range": "1-24 hours", "count": sum(1 for t in times_to_purchase if 1 < t <= 24)},
                {"range": "1-7 days", "count": sum(1 for t in times_to_purchase if 24 < t <= 168)},
                {"range": "1-4 weeks", "count": sum(1 for t in times_to_purchase if 168 < t <= 672)},
                {"range": "1+ months", "count": sum(1 for t in times_to_purchase if t > 672)}
            ]
            
            return {
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                "metrics": {
                    "total_first_purchases": total_customers,
                    "average_hours": round(average_hours, 2),
                    "median_hours": round(median_hours, 2),
                    "min_hours": round(min_hours, 2),
                    "max_hours": round(max_hours, 2),
                    "average_days": round(average_hours / 24, 2)
                },
                "distribution": distribution
            }
            
        except Exception as e:
            logger.error(f"Failed to get time to purchase metrics: {e}")
            raise HTTPException(status_code=500, detail="Failed to retrieve time to purchase metrics")
    
    async def get_refund_rate_metrics(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Get refund rate metrics"""
        try:
            # Orders in the period
            orders_result = await self.db.execute(
                select(
                    func.count(Order.id).label('total_orders'),
                    func.sum(Order.total_amount).label('total_revenue')
                ).where(
                    and_(
                        Order.created_at >= start_date,
                        Order.created_at <= end_date,
                        Order.order_status.in_(['confirmed', 'shipped', 'delivered'])
                    )
                )
            )
            order_stats = orders_result.first()
            total_orders = order_stats.total_orders or 0
            total_revenue = order_stats.total_revenue or 0
            
            # Refunds in the period
            refunds_result = await self.db.execute(
                select(
                    func.count(Refund.id).label('total_refunds'),
                    func.sum(Refund.processed_amount).label('total_refund_amount')
                ).join(Order, Refund.order_id == Order.id).where(
                    and_(
                        Order.created_at >= start_date,
                        Order.created_at <= end_date,
                        Refund.status.in_(['completed', 'processing'])
                    )
                )
            )
            refund_stats = refunds_result.first()
            total_refunds = refund_stats.total_refunds or 0
            total_refund_amount = refund_stats.total_refund_amount or 0
            
            # Calculate rates
            refund_rate = (total_refunds / total_orders * 100) if total_orders > 0 else 0
            refund_amount_rate = (total_refund_amount / total_revenue * 100) if total_revenue > 0 else 0
            
            # Refund reasons breakdown
            refund_reasons = await self.db.execute(
                select(
                    Refund.reason,
                    func.count(Refund.id).label('count'),
                    func.sum(Refund.processed_amount).label('amount')
                ).join(Order, Refund.order_id == Order.id).where(
                    and_(
                        Order.created_at >= start_date,
                        Order.created_at <= end_date,
                        Refund.status.in_(['completed', 'processing'])
                    )
                ).group_by(Refund.reason)
            )
            
            reason_breakdown = []
            for row in refund_reasons:
                reason_breakdown.append({
                    "reason": row.reason.value if row.reason else "unknown",
                    "count": row.count,
                    "amount": float(row.amount or 0),
                    "percentage": round((row.count / total_refunds * 100) if total_refunds > 0 else 0, 2)
                })
            
            return {
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                "overall": {
                    "total_orders": total_orders,
                    "total_refunds": total_refunds,
                    "refund_rate": round(refund_rate, 2),
                    "total_revenue": float(total_revenue),
                    "total_refund_amount": float(total_refund_amount),
                    "refund_amount_rate": round(refund_amount_rate, 2)
                },
                "by_reason": reason_breakdown
            }
            
        except Exception as e:
            logger.error(f"Failed to get refund rate metrics: {e}")
            raise HTTPException(status_code=500, detail="Failed to retrieve refund rate metrics")
    
    async def get_repeat_customer_metrics(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Get repeat customer metrics"""
        try:
            # Customer segments
            segments_result = await self.db.execute(
                select(
                    CustomerLifecycleMetrics.customer_segment,
                    func.count(CustomerLifecycleMetrics.user_id).label('count'),
                    func.avg(CustomerLifecycleMetrics.total_orders).label('avg_orders'),
                    func.avg(CustomerLifecycleMetrics.lifetime_value).label('avg_ltv')
                ).where(
                    CustomerLifecycleMetrics.metrics_updated_at >= start_date
                ).group_by(CustomerLifecycleMetrics.customer_segment)
            )
            
            segment_breakdown = []
            total_customers = 0
            
            for row in segments_result:
                segment_breakdown.append({
                    "segment": row.customer_segment or "unknown",
                    "count": row.count,
                    "average_orders": round(float(row.avg_orders or 0), 2),
                    "average_ltv": round(float(row.avg_ltv or 0), 2)
                })
                total_customers += row.count
            
            # Repeat purchase rate
            repeat_customers = await self.db.execute(
                select(func.count(CustomerLifecycleMetrics.user_id)).where(
                    and_(
                        CustomerLifecycleMetrics.total_orders > 1,
                        CustomerLifecycleMetrics.metrics_updated_at >= start_date
                    )
                )
            )
            repeat_customer_count = repeat_customers.scalar() or 0
            
            repeat_rate = (repeat_customer_count / total_customers * 100) if total_customers > 0 else 0
            
            # Purchase frequency distribution
            frequency_distribution = await self.db.execute(
                select(
                    CustomerLifecycleMetrics.total_orders,
                    func.count(CustomerLifecycleMetrics.user_id).label('customer_count')
                ).where(
                    CustomerLifecycleMetrics.metrics_updated_at >= start_date
                ).group_by(CustomerLifecycleMetrics.total_orders).order_by(CustomerLifecycleMetrics.total_orders)
            )
            
            frequency_data = []
            for row in frequency_distribution:
                frequency_data.append({
                    "order_count": row.total_orders,
                    "customer_count": row.customer_count
                })
            
            # Average days between orders for repeat customers
            avg_days_between = await self.db.execute(
                select(func.avg(CustomerLifecycleMetrics.average_days_between_orders)).where(
                    and_(
                        CustomerLifecycleMetrics.total_orders > 1,
                        CustomerLifecycleMetrics.average_days_between_orders.isnot(None),
                        CustomerLifecycleMetrics.metrics_updated_at >= start_date
                    )
                )
            )
            average_days_between_orders = avg_days_between.scalar() or 0
            
            return {
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                "overall": {
                    "total_customers": total_customers,
                    "repeat_customers": repeat_customer_count,
                    "repeat_rate": round(repeat_rate, 2),
                    "average_days_between_orders": round(float(average_days_between_orders), 2)
                },
                "by_segment": segment_breakdown,
                "frequency_distribution": frequency_data
            }
            
        except Exception as e:
            logger.error(f"Failed to get repeat customer metrics: {e}")
            raise HTTPException(status_code=500, detail="Failed to retrieve repeat customer metrics")
    
    async def get_comprehensive_dashboard_data(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Get comprehensive dashboard data with all key metrics"""
        try:
            # Get all metrics in parallel
            conversion_metrics = await self.get_conversion_metrics(start_date, end_date)
            cart_metrics = await self.get_cart_abandonment_metrics(start_date, end_date)
            purchase_metrics = await self.get_time_to_purchase_metrics(start_date, end_date)
            refund_metrics = await self.get_refund_rate_metrics(start_date, end_date)
            repeat_metrics = await self.get_repeat_customer_metrics(start_date, end_date)
            
            return {
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                "conversion": conversion_metrics,
                "cart_abandonment": cart_metrics,
                "time_to_purchase": purchase_metrics,
                "refunds": refund_metrics,
                "repeat_customers": repeat_metrics,
                "generated_at": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get comprehensive dashboard data: {e}")
            raise HTTPException(status_code=500, detail="Failed to retrieve dashboard data")
    
    async def _update_session_metrics(self, session_id: str):
        """Update session metrics when events are tracked"""
        try:
            # Get session
            session_result = await self.db.execute(
                select(UserSession).where(UserSession.session_id == session_id)
            )
            session = session_result.scalar_one_or_none()
            
            if session:
                # Count events
                events_count = await self.db.execute(
                    select(func.count(AnalyticsEvent.id)).where(
                        AnalyticsEvent.session_id == session_id
                    )
                )
                session.events_count = events_count.scalar() or 0
                
                # Check for conversion
                purchase_event = await self.db.execute(
                    select(AnalyticsEvent).where(
                        and_(
                            AnalyticsEvent.session_id == session_id,
                            AnalyticsEvent.event_type == EventType.PURCHASE
                        )
                    ).limit(1)
                )
                
                if purchase_event.scalar_one_or_none():
                    session.converted = True
                    # Get conversion value
                    revenue_sum = await self.db.execute(
                        select(func.sum(AnalyticsEvent.revenue)).where(
                            and_(
                                AnalyticsEvent.session_id == session_id,
                                AnalyticsEvent.event_type == EventType.PURCHASE
                            )
                        )
                    )
                    session.conversion_value = revenue_sum.scalar() or 0
                
        except Exception as e:
            logger.error(f"Failed to update session metrics: {e}")
    
    async def _update_conversion_funnel(self, session_id: str, user_id: UUID, event_type: EventType):
        """Update conversion funnel tracking"""
        try:
            # Get or create funnel record
            funnel_result = await self.db.execute(
                select(ConversionFunnel).where(
                    ConversionFunnel.session_id == session_id
                )
            )
            funnel = funnel_result.scalar_one_or_none()
            
            if not funnel:
                funnel = ConversionFunnel(
                    session_id=session_id,
                    user_id=user_id
                )
                self.db.add(funnel)
            
            # Update funnel step based on event type
            now = datetime.now(timezone.utc)
            
            if event_type == EventType.PAGE_VIEW and not funnel.landing_at:
                funnel.landing_at = now
                funnel.current_step = max(funnel.current_step, 0)
                funnel.max_step_reached = max(funnel.max_step_reached, 0)
            elif event_type == EventType.CART_ADD:
                funnel.cart_add_at = now
                funnel.current_step = max(funnel.current_step, 2)
                funnel.max_step_reached = max(funnel.max_step_reached, 2)
            elif event_type == EventType.CHECKOUT_START:
                funnel.checkout_start_at = now
                funnel.current_step = max(funnel.current_step, 3)
                funnel.max_step_reached = max(funnel.max_step_reached, 3)
            elif event_type == EventType.PURCHASE:
                funnel.purchase_at = now
                funnel.current_step = 4
                funnel.max_step_reached = 4
                funnel.completed = True
                
        except Exception as e:
            logger.error(f"Failed to update conversion funnel: {e}")

    async def get_sales_trend_data(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Get sales trend data over the specified period"""
        try:
            # Get daily sales data
            daily_sales = await self.db.execute(
                select(
                    func.date(Order.created_at).label('date'),
                    func.count(Order.id).label('order_count'),
                    func.sum(Order.total_amount).label('revenue'),
                    func.avg(Order.total_amount).label('avg_order_value')
                ).where(
                    and_(
                        Order.created_at >= start_date,
                        Order.created_at <= end_date,
                        Order.status.in_(['confirmed', 'shipped', 'delivered', 'completed'])
                    )
                ).group_by(func.date(Order.created_at)).order_by(func.date(Order.created_at))
            )
            
            trend_data = []
            total_revenue = 0
            total_orders = 0
            
            for row in daily_sales:
                daily_revenue = float(row.revenue or 0)
                daily_orders = row.order_count or 0
                
                trend_data.append({
                    "date": row.date.isoformat() if row.date else None,
                    "order_count": daily_orders,
                    "revenue": daily_revenue,
                    "avg_order_value": float(row.avg_order_value or 0)
                })
                
                total_revenue += daily_revenue
                total_orders += daily_orders
            
            # Calculate growth rate if we have data
            growth_rate = 0.0
            if len(trend_data) > 1:
                first_day_revenue = trend_data[0]["revenue"]
                last_day_revenue = trend_data[-1]["revenue"]
                if first_day_revenue > 0:
                    growth_rate = ((last_day_revenue - first_day_revenue) / first_day_revenue) * 100
            
            return {
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "days": len(trend_data)
                },
                "summary": {
                    "total_revenue": total_revenue,
                    "total_orders": total_orders,
                    "avg_daily_revenue": total_revenue / len(trend_data) if trend_data else 0,
                    "avg_daily_orders": total_orders / len(trend_data) if trend_data else 0,
                    "growth_rate": round(growth_rate, 2)
                },
                "daily_data": trend_data
            }
            
        except Exception as e:
            logger.error(f"Failed to get sales trend data: {e}")
            raise HTTPException(status_code=500, detail="Failed to retrieve sales trend data")