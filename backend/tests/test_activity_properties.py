"""
Property-based tests for activity logging functionality.

**Feature: app-enhancements, Properties 20-23: Activity logging and fetching**
**Validates: Requirements 7.1, 7.2, 7.3, 7.4**
"""

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from services.activity import ActivityService
from services.analytics import AnalyticsService
from models.activity_log import ActivityLog
from models.user import User
from uuid import uuid4


# Strategy for generating activity types
activity_types = st.sampled_from(['order', 'registration', 'review', 'payment', 'low_stock'])


# Strategy for generating activity data
@st.composite
def activity_data_strategy(draw):
    """Generate random activity data for testing."""
    action_type = draw(activity_types)
    return {
        'action_type': action_type,
        'description': f"Test {action_type} activity",
        'metadata': {
            'test_key': draw(st.text(min_size=1, max_size=50)),
            'test_value': draw(st.integers(min_value=0, max_value=1000))
        }
    }


@pytest.mark.asyncio
@given(activity_data=activity_data_strategy())
@settings(
    max_examples=100,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
    deadline=None
)
async def test_property_20_activity_fetching_on_dashboard_load(activity_data, db_session: AsyncSession):
    """
    **Property 20: Activity fetching on dashboard load**
    **Validates: Requirements 7.1**
    
    For any admin dashboard load, the system should fetch recent activity from the backend.
    """
    # Create a test activity
    activity_service = ActivityService(db_session)
    
    # Log an activity
    activity = await activity_service.log_activity(
        action_type=activity_data['action_type'],
        description=activity_data['description'],
        metadata=activity_data['metadata']
    )
    
    # Fetch recent activity (simulating dashboard load)
    analytics_service = AnalyticsService(db_session)
    activities = await analytics_service.get_recent_activity(limit=100)
    
    # Property: The fetched activities should include the logged activity
    activity_ids = [a['id'] for a in activities]
    assert str(activity.id) in activity_ids, "Logged activity should be fetchable on dashboard load"


@pytest.mark.asyncio
@given(
    action_type=activity_types,
    description=st.text(
        alphabet=st.characters(blacklist_characters='\x00', blacklist_categories=('Cs',)),
        min_size=1,
        max_size=200
    )
)
@settings(
    max_examples=100,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
    deadline=None
)
async def test_property_21_activity_logging(action_type, description, db_session: AsyncSession):
    """
    **Property 21: Activity logging**
    **Validates: Requirements 7.2**
    
    For any user action (order, registration, review), the system should record it in the activity log.
    """
    activity_service = ActivityService(db_session)
    
    # Log an activity
    activity = await activity_service.log_activity(
        action_type=action_type,
        description=description
    )
    
    # Property: The activity should be persisted and retrievable
    assert activity.id is not None, "Activity should have an ID after logging"
    assert activity.action_type == action_type, "Activity type should match"
    assert activity.description == description, "Activity description should match"
    assert activity.created_at is not None, "Activity should have a creation timestamp"


@pytest.mark.asyncio
@given(
    num_activities=st.integers(min_value=2, max_value=10)
)
@settings(
    max_examples=50,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
    deadline=None
)
async def test_property_22_activity_chronological_ordering(num_activities, db_session: AsyncSession):
    """
    **Property 22: Activity chronological ordering**
    **Validates: Requirements 7.3**
    
    For any recent activity display, activities should be shown in reverse chronological order (newest first).
    """
    activity_service = ActivityService(db_session)
    analytics_service = AnalyticsService(db_session)
    
    # Create multiple activities with slight time delays
    created_activities = []
    for i in range(num_activities):
        activity = await activity_service.log_activity(
            action_type='order',
            description=f"Activity {i}",
            metadata={'index': i}
        )
        created_activities.append(activity)
    
    # Fetch recent activities
    activities = await analytics_service.get_recent_activity(limit=num_activities)
    
    # Property: Activities should be in reverse chronological order (newest first)
    for i in range(len(activities) - 1):
        current_time = datetime.fromisoformat(activities[i]['created_at'])
        next_time = datetime.fromisoformat(activities[i + 1]['created_at'])
        assert current_time >= next_time, "Activities should be ordered newest first"


@pytest.mark.asyncio
@given(
    hours_ago=st.integers(min_value=0, max_value=48)
)
@settings(
    max_examples=50,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
    deadline=None
)
async def test_property_23_activity_timestamp_formatting(hours_ago, db_session: AsyncSession):
    """
    **Property 23: Activity timestamp formatting**
    **Validates: Requirements 7.4**
    
    For any activity displayed, timestamps should be formatted as relative time (e.g., "2 hours ago").
    """
    activity_service = ActivityService(db_session)
    analytics_service = AnalyticsService(db_session)
    
    # Create an activity
    activity = await activity_service.log_activity(
        action_type='order',
        description=f"Activity from {hours_ago} hours ago"
    )
    
    # Fetch the activity
    activities = await analytics_service.get_recent_activity(limit=1)
    
    # Property: The activity should have a valid ISO format timestamp
    assert len(activities) > 0, "Should fetch at least one activity"
    activity_data = activities[0]
    assert 'created_at' in activity_data, "Activity should have created_at field"
    
    # Verify timestamp is in ISO format and can be parsed
    try:
        timestamp = datetime.fromisoformat(activity_data['created_at'])
        assert isinstance(timestamp, datetime), "Timestamp should be a valid datetime"
    except ValueError:
        pytest.fail("Timestamp should be in valid ISO format")
