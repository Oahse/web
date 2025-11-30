"""
Property-based tests for analytics filters.

**Feature: app-enhancements, Property 13: Analytics date range filtering**
**Validates: Requirements 5.1**
"""

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from services.analytics import AnalyticsService
from models.order import Order
from models.user import User
from models.product import Product


# Strategy for generating valid date ranges
@st.composite
def date_range_strategy(draw):
    """Generate a valid date range for testing."""
    # Generate a start date within the last year
    days_ago = draw(st.integers(min_value=1, max_value=365))
    start_date = datetime.now() - timedelta(days=days_ago)
    
    # Generate an end date after start date
    days_duration = draw(st.integers(min_value=1, max_value=days_ago))
    end_date = start_date + timedelta(days=days_duration)
    
    return start_date, end_date


@pytest.mark.asyncio
@given(date_range=date_range_strategy())
@settings(
    max_examples=100, 
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
async def test_property_date_range_filtering(date_range, db_session: AsyncSession):
    """
    Property 13: Analytics date range filtering
    
    For any custom date range selected, all analytics data (sales, orders, users) 
    should be filtered to that range.
    
    **Validates: Requirements 5.1**
    """
    start_date, end_date = date_range
    
    # Create analytics service
    analytics_service = AnalyticsService(db_session)
    
    # Get dashboard data with date range filter
    result = await analytics_service.get_dashboard_data(
        user_id="test_admin",
        user_role="Admin",
        start_date=start_date,
        end_date=end_date,
        filters={}
    )
    
    # Verify all orders in the result are within the date range
    # Query orders directly to verify
    orders_query = select(Order).where(
        Order.created_at >= start_date,
        Order.created_at <= end_date
    )
    orders_result = await db_session.execute(orders_query)
    expected_orders = orders_result.scalars().all()
    
    # The total_orders in result should match orders within date range
    assert result['total_orders'] == len(expected_orders), \
        f"Expected {len(expected_orders)} orders, got {result['total_orders']}"
    
    # Verify sales trend data is within date range
    for trend_point in result.get('sales_trend', []):
        trend_date = datetime.strptime(trend_point['date'], "%Y-%m-%d")
        assert start_date.date() <= trend_date.date() <= end_date.date(), \
            f"Trend date {trend_date} is outside range [{start_date}, {end_date}]"






@pytest.mark.asyncio
@given(
    category=st.one_of(st.none(), st.sampled_from(['supplements', 'herbs', 'oils', 'teas'])),
    order_status=st.one_of(st.none(), st.sampled_from(['pending', 'processing', 'confirmed', 'shipped', 'delivered', 'cancelled']))
)
@settings(
    max_examples=100, 
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
async def test_property_general_filters_application(category, order_status, db_session: AsyncSession):
    """
    Property 14: Analytics general filters application
    
    For any general filter applied (category, product, user segment), 
    all charts and metrics should reflect the filter.
    
    **Validates: Requirements 5.2**
    """
    # Create analytics service
    analytics_service = AnalyticsService(db_session)
    
    # Build filters
    filters = {}
    if category:
        filters['category'] = category
    if order_status:
        filters['order_status'] = order_status
    
    # Get dashboard data with filters
    start_date = datetime.now() - timedelta(days=30)
    end_date = datetime.now()
    
    result = await analytics_service.get_dashboard_data(
        user_id="test_admin",
        user_role="Admin",
        start_date=start_date,
        end_date=end_date,
        filters=filters
    )
    
    # Verify the result is valid
    assert isinstance(result, dict)
    assert 'total_orders' in result
    assert 'total_sales' in result
    
    # If order_status filter is applied, verify order status distribution
    if order_status and result.get('order_status_distribution'):
        # All orders should match the filtered status or be empty
        for status, count in result['order_status_distribution'].items():
            if count > 0:
                # If there are orders, they should match the filter
                assert status == order_status or order_status is None, \
                    f"Found orders with status {status} when filtering for {order_status}"
    
    # Verify sales trend data exists and is properly formatted
    assert 'sales_trend' in result
    assert isinstance(result['sales_trend'], list)
    for trend_point in result['sales_trend']:
        assert 'date' in trend_point
        assert 'sales' in trend_point
        assert 'orders' in trend_point






@pytest.mark.asyncio
@given(
    category=st.one_of(st.none(), st.sampled_from(['supplements', 'herbs', 'oils', 'teas'])),
    order_status=st.one_of(st.none(), st.sampled_from(['pending', 'processing', 'confirmed', 'shipped', 'delivered'])),
    user_segment=st.one_of(st.none(), st.sampled_from(['new', 'returning', 'vip']))
)
@settings(
    max_examples=100, 
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
async def test_property_multiple_filters_combination(category, order_status, user_segment, db_session: AsyncSession):
    """
    Property 15: Multiple filters combination
    
    For any multiple filters applied simultaneously, the system should 
    combine them with AND logic.
    
    **Validates: Requirements 5.3**
    """
    # Create analytics service
    analytics_service = AnalyticsService(db_session)
    
    # Build filters with multiple criteria
    filters = {}
    if category:
        filters['category'] = category
    if order_status:
        filters['order_status'] = order_status
    if user_segment:
        filters['user_segment'] = user_segment
    
    # Get dashboard data with multiple filters
    start_date = datetime.now() - timedelta(days=30)
    end_date = datetime.now()
    
    result = await analytics_service.get_dashboard_data(
        user_id="test_admin",
        user_role="Admin",
        start_date=start_date,
        end_date=end_date,
        filters=filters
    )
    
    # Verify the result is valid
    assert isinstance(result, dict)
    assert 'total_orders' in result
    assert 'total_sales' in result
    assert 'total_users' in result
    
    # When multiple filters are applied, results should be more restrictive
    # Get unfiltered results for comparison
    unfiltered_result = await analytics_service.get_dashboard_data(
        user_id="test_admin",
        user_role="Admin",
        start_date=start_date,
        end_date=end_date,
        filters={}
    )
    
    # Filtered results should have equal or fewer orders than unfiltered
    # (unless no filters were applied)
    if filters:
        assert result['total_orders'] <= unfiltered_result['total_orders'], \
            f"Filtered orders ({result['total_orders']}) should not exceed unfiltered ({unfiltered_result['total_orders']})"
        assert result['total_sales'] <= unfiltered_result['total_sales'], \
            f"Filtered sales ({result['total_sales']}) should not exceed unfiltered ({unfiltered_result['total_sales']})"






@pytest.mark.asyncio
@given(
    category=st.one_of(st.none(), st.sampled_from(['supplements', 'herbs', 'oils', 'teas'])),
    order_status=st.one_of(st.none(), st.sampled_from(['pending', 'processing', 'confirmed', 'shipped', 'delivered']))
)
@settings(
    max_examples=100, 
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
async def test_property_filter_reset(category, order_status, db_session: AsyncSession):
    """
    Property 16: Filter reset behavior
    
    For any filter clear action, the system should reset to showing all data 
    without filters.
    
    **Validates: Requirements 5.4**
    """
    # Create analytics service
    analytics_service = AnalyticsService(db_session)
    
    start_date = datetime.now() - timedelta(days=30)
    end_date = datetime.now()
    
    # Get data with filters applied
    filters = {}
    if category:
        filters['category'] = category
    if order_status:
        filters['order_status'] = order_status
    
    filtered_result = await analytics_service.get_dashboard_data(
        user_id="test_admin",
        user_role="Admin",
        start_date=start_date,
        end_date=end_date,
        filters=filters
    )
    
    # Get data with no filters (reset state)
    reset_result = await analytics_service.get_dashboard_data(
        user_id="test_admin",
        user_role="Admin",
        start_date=start_date,
        end_date=end_date,
        filters={}
    )
    
    # Verify reset result structure
    assert isinstance(reset_result, dict)
    assert 'total_orders' in reset_result
    assert 'total_sales' in reset_result
    
    # Reset should show all data (equal or more than filtered)
    if filters:
        assert reset_result['total_orders'] >= filtered_result['total_orders'], \
            f"Reset should show all data: {reset_result['total_orders']} >= {filtered_result['total_orders']}"
        assert reset_result['total_sales'] >= filtered_result['total_sales'], \
            f"Reset should show all sales: {reset_result['total_sales']} >= {filtered_result['total_sales']}"
    else:
        # If no filters were applied, results should be identical
        assert reset_result['total_orders'] == filtered_result['total_orders']
        assert reset_result['total_sales'] == filtered_result['total_sales']



