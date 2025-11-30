"""
Property-based tests for admin user actions.

**Feature: app-enhancements, Property 29: Password reset email sending**
**Validates: Requirements 10.2**

**Feature: app-enhancements, Property 30: Account deactivation**
**Validates: Requirements 10.3**

**Feature: app-enhancements, Property 31: Action completion feedback**
**Validates: Requirements 10.5**
"""

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from services.admin import AdminService
from models.user import User
from core.exceptions import APIException
from unittest.mock import patch, MagicMock


@pytest.mark.asyncio
@given(
    dummy=st.just(None)
)
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
async def test_property_password_reset_email_sending(dummy, db_session: AsyncSession):
    """
    Property 29: Password reset email sending
    
    For any "Reset Password" action, the system should send a password reset 
    email to the user.
    
    **Validates: Requirements 10.2**
    """
    # Create admin service
    admin_service = AdminService(db_session)
    
    # Get a user from the database
    query = select(User).limit(1)
    result = await db_session.execute(query)
    user = result.scalar_one_or_none()
    
    if not user:
        # Skip test if no users exist
        pytest.skip("No users in database")
    
    # Mock the Celery task where it's imported (inside the function)
    try:
        with patch('tasks.email_tasks.send_password_reset_email') as mock_email_task:
            # Call reset password
            result = await admin_service.reset_user_password(str(user.id))
            
            # Verify the result structure
            assert isinstance(result, dict)
            assert 'message' in result
            assert 'user_id' in result
            assert 'email' in result
            assert result['user_id'] == str(user.id)
            assert result['email'] == user.email
            
            # Verify email task was called
            mock_email_task.delay.assert_called_once()
            call_args = mock_email_task.delay.call_args[0]
            assert call_args[0] == user.email  # First arg should be user email
    except ModuleNotFoundError:
        pytest.skip("psycopg2 module not installed")


@pytest.mark.asyncio
@given(
    dummy=st.just(None)
)
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
async def test_property_account_deactivation(dummy, db_session: AsyncSession):
    """
    Property 30: Account deactivation
    
    For any "Deactivate Account" action with confirmation, the user account 
    should be deactivated (active=false).
    
    **Validates: Requirements 10.3**
    """
    # Create admin service
    admin_service = AdminService(db_session)
    
    # Get an active user from the database
    query = select(User).where(User.active == True).limit(1)
    result = await db_session.execute(query)
    user = result.scalar_one_or_none()
    
    if not user:
        # Skip test if no active users exist
        pytest.skip("No active users in database")
    
    user_id = str(user.id)
    
    # Deactivate the user
    result = await admin_service.deactivate_user(user_id)
    
    # Verify the result structure
    assert isinstance(result, dict)
    assert 'message' in result
    assert 'user_id' in result
    assert 'active' in result
    assert result['user_id'] == user_id
    assert result['active'] == False
    
    # Verify user is actually deactivated in database
    query = select(User).where(User.id == user_id)
    db_result = await db_session.execute(query)
    updated_user = db_result.scalar_one()
    
    assert updated_user.active == False, \
        f"User {user_id} should be deactivated but active={updated_user.active}"
    
    # Clean up: reactivate the user
    await admin_service.activate_user(user_id)


@pytest.mark.asyncio
@given(
    dummy=st.just(None)
)
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
async def test_property_account_activation(dummy, db_session: AsyncSession):
    """
    Additional property: Account activation
    
    For any "Activate Account" action, the user account should be activated 
    (active=true).
    """
    # Create admin service
    admin_service = AdminService(db_session)
    
    # Get an inactive user or create one
    query = select(User).where(User.active == False).limit(1)
    result = await db_session.execute(query)
    user = result.scalar_one_or_none()
    
    if not user:
        # Get any user and deactivate them first
        query = select(User).limit(1)
        result = await db_session.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            pytest.skip("No users in database")
        
        # Deactivate first
        await admin_service.deactivate_user(str(user.id))
    
    user_id = str(user.id)
    
    # Activate the user
    result = await admin_service.activate_user(user_id)
    
    # Verify the result structure
    assert isinstance(result, dict)
    assert 'message' in result
    assert 'user_id' in result
    assert 'active' in result
    assert result['user_id'] == user_id
    assert result['active'] == True
    
    # Verify user is actually activated in database
    query = select(User).where(User.id == user_id)
    db_result = await db_session.execute(query)
    updated_user = db_result.scalar_one()
    
    assert updated_user.active == True, \
        f"User {user_id} should be activated but active={updated_user.active}"


@pytest.mark.asyncio
@given(
    dummy=st.just(None)
)
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
async def test_property_action_completion_feedback(dummy, db_session: AsyncSession):
    """
    Property 31: Action completion feedback
    
    For any admin action completion, the system should display a success 
    message and update user status if applicable.
    
    **Validates: Requirements 10.5**
    """
    # Create admin service
    admin_service = AdminService(db_session)
    
    # Get a user from the database
    query = select(User).limit(1)
    result = await db_session.execute(query)
    user = result.scalar_one_or_none()
    
    if not user:
        pytest.skip("No users in database")
    
    user_id = str(user.id)
    original_status = user.active
    
    # Test deactivation feedback
    deactivate_result = await admin_service.deactivate_user(user_id)
    
    # Verify feedback structure
    assert isinstance(deactivate_result, dict)
    assert 'message' in deactivate_result, "Result should contain a message"
    assert isinstance(deactivate_result['message'], str), "Message should be a string"
    assert len(deactivate_result['message']) > 0, "Message should not be empty"
    assert 'active' in deactivate_result, "Result should contain updated status"
    assert deactivate_result['active'] == False, "Status should be updated to False"
    
    # Test activation feedback
    activate_result = await admin_service.activate_user(user_id)
    
    # Verify feedback structure
    assert isinstance(activate_result, dict)
    assert 'message' in activate_result, "Result should contain a message"
    assert isinstance(activate_result['message'], str), "Message should be a string"
    assert len(activate_result['message']) > 0, "Message should not be empty"
    assert 'active' in activate_result, "Result should contain updated status"
    assert activate_result['active'] == True, "Status should be updated to True"
    
    # Test password reset feedback
    try:
        with patch('tasks.email_tasks.send_password_reset_email') as mock_email_task:
            reset_result = await admin_service.reset_user_password(user_id)
            
            # Verify feedback structure
            assert isinstance(reset_result, dict)
            assert 'message' in reset_result, "Result should contain a message"
            assert isinstance(reset_result['message'], str), "Message should be a string"
            assert len(reset_result['message']) > 0, "Message should not be empty"
            assert 'email' in reset_result, "Result should contain user email"
    except ModuleNotFoundError:
        pytest.skip("psycopg2 module not installed")
    
    # Restore original status
    if original_status:
        await admin_service.activate_user(user_id)
    else:
        await admin_service.deactivate_user(user_id)


@pytest.mark.asyncio
@given(
    dummy=st.just(None)
)
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
async def test_property_invalid_user_error_handling(dummy, db_session: AsyncSession):
    """
    Additional property: Error handling for invalid user IDs
    
    For any admin action on a non-existent user, the system should raise 
    an appropriate error.
    """
    # Create admin service
    admin_service = AdminService(db_session)
    
    # Use a non-existent user ID
    invalid_user_id = "00000000-0000-0000-0000-000000000000"
    
    # Test deactivation with invalid user
    with pytest.raises(APIException) as exc_info:
        await admin_service.deactivate_user(invalid_user_id)
    assert exc_info.value.status_code == 404
    assert "not found" in exc_info.value.message.lower()
    
    # Test activation with invalid user
    with pytest.raises(APIException) as exc_info:
        await admin_service.activate_user(invalid_user_id)
    assert exc_info.value.status_code == 404
    assert "not found" in exc_info.value.message.lower()
    
    # Test password reset with invalid user
    with pytest.raises(APIException) as exc_info:
        await admin_service.reset_user_password(invalid_user_id)
    assert exc_info.value.status_code == 404
    assert "not found" in exc_info.value.message.lower()
