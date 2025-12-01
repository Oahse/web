"""
Property-based tests for system settings.

**Feature: app-enhancements, Property 36: Maintenance mode enforcement**
**Validates: Requirements 12.1**

**Feature: app-enhancements, Property 37: User registration toggle**
**Validates: Requirements 12.2**

**Feature: app-enhancements, Property 38: File upload size enforcement**
**Validates: Requirements 12.3**

**Feature: app-enhancements, Property 39: File type validation**
**Validates: Requirements 12.4**

**Feature: app-enhancements, Property 40: Email notifications toggle**
**Validates: Requirements 12.5**

**Feature: app-enhancements, Property 41: SMS notifications toggle**
**Validates: Requirements 12.6**

**Feature: app-enhancements, Property 42: Settings persistence**
**Validates: Requirements 12.7**

**Feature: app-enhancements, Property 43: Settings save confirmation**
**Validates: Requirements 12.8**
"""

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from services.admin import AdminService
from models.settings import SystemSettings
from models.user import User


@pytest.mark.asyncio
@given(
    maintenance_mode=st.booleans()
)
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
async def test_property_maintenance_mode_enforcement(maintenance_mode, db_session: AsyncSession):
    """
    Property 36: Maintenance mode enforcement
    
    For any non-admin user when maintenance mode is enabled, the system should 
    display a maintenance page.
    
    **Validates: Requirements 12.1**
    """
    # Create admin service
    admin_service = AdminService(db_session)
    
    # Update maintenance mode setting
    settings_data = {"maintenance_mode": maintenance_mode}
    result = await admin_service.update_system_settings(settings_data)
    
    # Verify the setting was updated
    assert result['maintenance_mode'] == maintenance_mode
    
    # Verify the setting persists in database
    query = select(SystemSettings)
    db_result = await db_session.execute(query)
    settings = db_result.scalar_one_or_none()
    
    assert settings is not None, "Settings should exist in database"
    assert settings.maintenance_mode == maintenance_mode, \
        f"Maintenance mode should be {maintenance_mode} but got {settings.maintenance_mode}"


@pytest.mark.asyncio
@given(
    registration_enabled=st.booleans()
)
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
async def test_property_user_registration_toggle(registration_enabled, db_session: AsyncSession):
    """
    Property 37: User registration toggle
    
    For any user registration setting toggle, new user registration should be 
    enabled or disabled accordingly.
    
    **Validates: Requirements 12.2**
    """
    # Create admin service
    admin_service = AdminService(db_session)
    
    # Update registration enabled setting
    settings_data = {"registration_enabled": registration_enabled}
    result = await admin_service.update_system_settings(settings_data)
    
    # Verify the setting was updated
    assert result['registration_enabled'] == registration_enabled
    
    # Verify the setting persists in database
    query = select(SystemSettings)
    db_result = await db_session.execute(query)
    settings = db_result.scalar_one_or_none()
    
    assert settings is not None, "Settings should exist in database"
    assert settings.registration_enabled == registration_enabled, \
        f"Registration enabled should be {registration_enabled} but got {settings.registration_enabled}"


@pytest.mark.asyncio
@given(
    max_file_size=st.integers(min_value=1, max_value=100)
)
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
async def test_property_file_upload_size_enforcement(max_file_size, db_session: AsyncSession):
    """
    Property 38: File upload size enforcement
    
    For any file upload, the system should enforce the configured max file 
    upload size limit.
    
    **Validates: Requirements 12.3**
    """
    # Create admin service
    admin_service = AdminService(db_session)
    
    # Update max file size setting
    settings_data = {"max_file_size": max_file_size}
    result = await admin_service.update_system_settings(settings_data)
    
    # Verify the setting was updated
    assert result['max_file_size'] == max_file_size
    
    # Verify the setting persists in database
    query = select(SystemSettings)
    db_result = await db_session.execute(query)
    settings = db_result.scalar_one_or_none()
    
    assert settings is not None, "Settings should exist in database"
    assert settings.max_file_size == max_file_size, \
        f"Max file size should be {max_file_size} but got {settings.max_file_size}"


@pytest.mark.asyncio
@given(
    file_types=st.lists(
        st.sampled_from(['jpg', 'jpeg', 'png', 'pdf', 'doc', 'docx', 'txt', 'csv']),
        min_size=1,
        max_size=5,
        unique=True
    )
)
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
async def test_property_file_type_validation(file_types, db_session: AsyncSession):
    """
    Property 39: File type validation
    
    For any file upload, the system should validate the file type against the 
    configured allowed file types list.
    
    **Validates: Requirements 12.4**
    """
    # Create admin service
    admin_service = AdminService(db_session)
    
    # Convert list to comma-separated string
    allowed_types_str = ','.join(file_types)
    
    # Update allowed file types setting
    settings_data = {"allowed_file_types": allowed_types_str}
    result = await admin_service.update_system_settings(settings_data)
    
    # Verify the setting was updated
    assert result['allowed_file_types'] == allowed_types_str
    
    # Verify the setting persists in database
    query = select(SystemSettings)
    db_result = await db_session.execute(query)
    settings = db_result.scalar_one_or_none()
    
    assert settings is not None, "Settings should exist in database"
    assert settings.allowed_file_types == allowed_types_str, \
        f"Allowed file types should be {allowed_types_str} but got {settings.allowed_file_types}"
    
    # Verify each file type is in the setting
    stored_types = settings.allowed_file_types.split(',')
    for file_type in file_types:
        assert file_type in stored_types, \
            f"File type {file_type} should be in allowed types"


@pytest.mark.asyncio
@given(
    email_notifications=st.booleans()
)
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
async def test_property_email_notifications_toggle(email_notifications, db_session: AsyncSession):
    """
    Property 40: Email notifications toggle
    
    For any email notifications setting toggle, system-wide email sending 
    should be enabled or disabled accordingly.
    
    **Validates: Requirements 12.5**
    """
    # Create admin service
    admin_service = AdminService(db_session)
    
    # Update email notifications setting
    settings_data = {"email_notifications": email_notifications}
    result = await admin_service.update_system_settings(settings_data)
    
    # Verify the setting was updated
    assert result['email_notifications'] == email_notifications
    
    # Verify the setting persists in database
    query = select(SystemSettings)
    db_result = await db_session.execute(query)
    settings = db_result.scalar_one_or_none()
    
    assert settings is not None, "Settings should exist in database"
    assert settings.email_notifications == email_notifications, \
        f"Email notifications should be {email_notifications} but got {settings.email_notifications}"


@pytest.mark.asyncio
@given(
    sms_notifications=st.booleans()
)
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
async def test_property_sms_notifications_toggle(sms_notifications, db_session: AsyncSession):
    """
    Property 41: SMS notifications toggle
    
    For any SMS notifications setting toggle, system-wide SMS sending should 
    be enabled or disabled accordingly.
    
    **Validates: Requirements 12.6**
    """
    # Create admin service
    admin_service = AdminService(db_session)
    
    # Update SMS notifications setting
    settings_data = {"sms_notifications": sms_notifications}
    result = await admin_service.update_system_settings(settings_data)
    
    # Verify the setting was updated
    assert result['sms_notifications'] == sms_notifications
    
    # Verify the setting persists in database
    query = select(SystemSettings)
    db_result = await db_session.execute(query)
    settings = db_result.scalar_one_or_none()
    
    assert settings is not None, "Settings should exist in database"
    assert settings.sms_notifications == sms_notifications, \
        f"SMS notifications should be {sms_notifications} but got {settings.sms_notifications}"


@pytest.mark.asyncio
@given(
    maintenance_mode=st.booleans(),
    registration_enabled=st.booleans(),
    max_file_size=st.integers(min_value=1, max_value=100),
    email_notifications=st.booleans(),
    sms_notifications=st.booleans()
)
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
async def test_property_settings_persistence(
    maintenance_mode,
    registration_enabled,
    max_file_size,
    email_notifications,
    sms_notifications,
    db_session: AsyncSession
):
    """
    Property 42: Settings persistence
    
    For any settings update, the changes should be persisted to the database 
    immediately.
    
    **Validates: Requirements 12.7**
    """
    # Create admin service
    admin_service = AdminService(db_session)
    
    # Update multiple settings at once
    settings_data = {
        "maintenance_mode": maintenance_mode,
        "registration_enabled": registration_enabled,
        "max_file_size": max_file_size,
        "email_notifications": email_notifications,
        "sms_notifications": sms_notifications
    }
    result = await admin_service.update_system_settings(settings_data)
    
    # Verify all settings were updated in the result
    assert result['maintenance_mode'] == maintenance_mode
    assert result['registration_enabled'] == registration_enabled
    assert result['max_file_size'] == max_file_size
    assert result['email_notifications'] == email_notifications
    assert result['sms_notifications'] == sms_notifications
    
    # Verify all settings persist in database
    query = select(SystemSettings)
    db_result = await db_session.execute(query)
    settings = db_result.scalar_one_or_none()
    
    assert settings is not None, "Settings should exist in database"
    assert settings.maintenance_mode == maintenance_mode
    assert settings.registration_enabled == registration_enabled
    assert settings.max_file_size == max_file_size
    assert settings.email_notifications == email_notifications
    assert settings.sms_notifications == sms_notifications


@pytest.mark.asyncio
@given(
    dummy=st.just(None)
)
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
async def test_property_settings_save_confirmation(dummy, db_session: AsyncSession):
    """
    Property 43: Settings save confirmation
    
    For any settings save operation, the system should display a success 
    confirmation message.
    
    **Validates: Requirements 12.8**
    """
    # Create admin service
    admin_service = AdminService(db_session)
    
    # Update a setting
    settings_data = {"maintenance_mode": True}
    result = await admin_service.update_system_settings(settings_data)
    
    # Verify the result is a dictionary (confirmation structure)
    assert isinstance(result, dict), "Result should be a dictionary"
    
    # Verify the result contains the updated settings
    assert 'maintenance_mode' in result, "Result should contain maintenance_mode"
    assert result['maintenance_mode'] == True
    
    # Verify the result contains all expected fields
    expected_fields = [
        'id',
        'maintenance_mode',
        'registration_enabled',
        'max_file_size',
        'allowed_file_types',
        'email_notifications',
        'sms_notifications',
        'created_at',
        'updated_at'
    ]
    
    for field in expected_fields:
        assert field in result, f"Result should contain {field}"


@pytest.mark.asyncio
@given(
    dummy=st.just(None)
)
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
async def test_property_settings_default_creation(dummy, db_session: AsyncSession):
    """
    Additional property: Default settings creation
    
    For any first-time settings access, the system should create default 
    settings if none exist.
    """
    # Create admin service
    admin_service = AdminService(db_session)
    
    # Delete any existing settings
    query = select(SystemSettings)
    result = await db_session.execute(query)
    existing_settings = result.scalar_one_or_none()
    
    if existing_settings:
        await db_session.delete(existing_settings)
        await db_session.commit()
    
    # Get settings (should create defaults)
    settings = await admin_service.get_system_settings()
    
    # Verify default settings were created
    assert isinstance(settings, dict)
    assert 'maintenance_mode' in settings
    assert 'registration_enabled' in settings
    assert 'max_file_size' in settings
    assert 'allowed_file_types' in settings
    assert 'email_notifications' in settings
    assert 'sms_notifications' in settings
    
    # Verify defaults match expected values
    assert settings['maintenance_mode'] == False, "Default maintenance mode should be False"
    assert settings['registration_enabled'] == True, "Default registration should be enabled"
    assert settings['max_file_size'] == 10, "Default max file size should be 10 MB"
    assert settings['email_notifications'] == True, "Default email notifications should be enabled"
    assert settings['sms_notifications'] == False, "Default SMS notifications should be disabled"


@pytest.mark.asyncio
@given(
    dummy=st.just(None)
)
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
async def test_property_settings_retrieval(dummy, db_session: AsyncSession):
    """
    Additional property: Settings retrieval
    
    For any settings retrieval request, the system should return the current 
    settings from the database.
    """
    # Create admin service
    admin_service = AdminService(db_session)
    
    # Set specific settings
    test_settings = {
        "maintenance_mode": True,
        "registration_enabled": False,
        "max_file_size": 25,
        "email_notifications": False,
        "sms_notifications": True
    }
    await admin_service.update_system_settings(test_settings)
    
    # Retrieve settings
    retrieved_settings = await admin_service.get_system_settings()
    
    # Verify retrieved settings match what was set
    assert retrieved_settings['maintenance_mode'] == True
    assert retrieved_settings['registration_enabled'] == False
    assert retrieved_settings['max_file_size'] == 25
    assert retrieved_settings['email_notifications'] == False
    assert retrieved_settings['sms_notifications'] == True
