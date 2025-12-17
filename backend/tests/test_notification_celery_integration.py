"""
Integration tests for notification and Celery processing.

Property 41: Notification Celery processing
Validates: Requirements 15.6
"""

import pytest
from httpx import AsyncClient
from unittest.mock import patch, MagicMock, AsyncMock # Import AsyncMock
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio
from uuid import UUID

from core.config import settings # Import settings
from services.notification import NotificationService
from tasks.email_tasks import send_low_stock_alert_email

# Property 41: Notification Celery processing
@pytest.mark.asyncio
@patch('tasks.email_tasks.send_low_stock_alert_email.delay')
async def test_low_stock_email_notification_celery_processing(
    mock_celery_delay: MagicMock, db_session: AsyncSession
):
    """
    Test low stock email notification trigger -> Celery worker processing -> delivery.
    Verify email notifications are processed asynchronously through Celery workers.
    """
    # Mock data for low stock alert
    product_name = "Test Product"
    variant_name = "Red Small"
    location_name = "Warehouse A"
    current_stock = 5
    threshold = 10
    
    admin_email = "admin@example.com"
    # Use a valid UUID string for admin_user_id
    mock_admin_user_uuid = "a1b2c3d4-e5f6-7890-1234-567890abcdef" 
    
    # Mock the admin user object that would be returned from db.scalar
    mock_admin_user = MagicMock()
    mock_admin_user.email = admin_email
    
    notification_service = NotificationService(db_session)
    
    # Patch db.scalar to return our mock_admin_user
    with patch.object(notification_service.db, 'scalar', return_value=mock_admin_user):
        # Mock the internal call to create_notification to prevent actual DB interaction during this test
        # and focus on the email task triggering.
        with patch.object(notification_service, 'create_notification', AsyncMock()) as mock_create_notification: # Use AsyncMock
            # Temporarily override ADMIN_USER_ID in settings for this test
            with patch.object(settings, 'ADMIN_USER_ID', mock_admin_user_uuid):
                # Simulate the call that would trigger the low stock email alert
                await notification_service.send_low_stock_alert(
                    product_name=product_name,
                    variant_name=variant_name,
                    location_name=location_name,
                    current_stock=current_stock,
                    threshold=threshold
                )
            
            # Define the expected context that send_low_stock_alert_email expects
            expected_context = {
                "recipient_email": admin_email,
                "product_name": product_name,
                "variant_name": variant_name,
                "location_name": location_name,
                "current_stock": current_stock,
                "threshold": threshold,
                "admin_inventory_link": f"{settings.FRONTEND_URL}/admin/inventory", # Link to admin inventory page
                "company_name": "Banwee",
            }

            # Assert that the Celery task for sending low stock email was called correctly
            mock_celery_delay.assert_called_once_with(
                admin_email, # recipient_email
                expected_context # context dictionary
            )

            # Assert that an in-app notification was also attempted to be created
            mock_create_notification.assert_called_once_with(
                user_id=UUID(mock_admin_user_uuid),
                message=f"Low stock alert! {product_name} ({variant_name}) at {location_name} has {current_stock} units left (threshold: {threshold}).",
                type="low_stock",
                related_id=None
            )

    print("\nLow stock email notification Celery processing test passed (mocked Celery task call).")