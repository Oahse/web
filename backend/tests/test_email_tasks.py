import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from fastapi import BackgroundTasks

from tasks.email_tasks import (
    send_order_confirmation_email,
    send_shipping_update_email,
    send_welcome_email,
    send_password_reset_email,
    send_email_verification,
    send_email_change_confirmation,
    send_order_delivered_email,
    send_return_process_email,
    send_referral_request_email,
    send_low_stock_alert_email,
    EmailTaskService
)


class TestEmailTasks:
    """Test cases for email tasks"""

    @pytest.fixture
    def background_tasks(self):
        """Mock background tasks"""
        return MagicMock(spec=BackgroundTasks)

    @pytest.fixture
    def email_task_service(self):
        """Create EmailTaskService instance"""
        return EmailTaskService()

    def test_send_order_confirmation_email(self, background_tasks):
        """Test order confirmation email task"""
        send_order_confirmation_email(
            background_tasks=background_tasks,
            to_email="test@example.com",
            customer_name="John Doe",
            order_number="ORD-12345",
            order_date=datetime.now(),
            total_amount=99.99,
            items=[{"name": "Test Product", "quantity": 1, "price": 99.99}],
            shipping_address={"street": "123 Main St", "city": "Test City", "state": "TS", "zip_code": "12345", "country": "US"}
        )
        
        # Verify background task was added
        background_tasks.add_task.assert_called_once()
        
        # Get the task arguments
        args, kwargs = background_tasks.add_task.call_args
        task_func = args[0]
        email_data = args[1]
        
        # Verify email data structure
        assert email_data["to_email"] == "test@example.com"
        assert email_data["mail_type"] == "order_confirmation"
        assert email_data["context"]["customer_name"] == "John Doe"
        assert email_data["context"]["order_number"] == "ORD-12345"
        assert email_data["context"]["total_amount"] == 99.99

    def test_send_shipping_update_email(self, background_tasks):
        """Test shipping update email task"""
        send_shipping_update_email(
            background_tasks=background_tasks,
            to_email="test@example.com",
            customer_name="Jane Doe",
            order_number="ORD-67890",
            tracking_number="TRK-12345",
            carrier="UPS",
            estimated_delivery=datetime.now(),
            tracking_url="https://ups.com/track/TRK-12345"
        )
        
        background_tasks.add_task.assert_called_once()
        
        args, kwargs = background_tasks.add_task.call_args
        email_data = args[1]
        
        assert email_data["to_email"] == "test@example.com"
        assert email_data["mail_type"] == "shipping_update"
        assert email_data["context"]["customer_name"] == "Jane Doe"
        assert email_data["context"]["tracking_number"] == "TRK-12345"
        assert email_data["context"]["carrier"] == "UPS"

    def test_send_welcome_email(self, background_tasks):
        """Test welcome email task"""
        send_welcome_email(
            background_tasks=background_tasks,
            to_email="newuser@example.com",
            customer_name="New User",
            verification_required=True,
            verification_url="https://banwee.com/verify?token=abc123"
        )
        
        background_tasks.add_task.assert_called_once()
        
        args, kwargs = background_tasks.add_task.call_args
        email_data = args[1]
        
        assert email_data["to_email"] == "newuser@example.com"
        assert email_data["mail_type"] == "welcome"
        assert email_data["context"]["customer_name"] == "New User"
        assert email_data["context"]["verification_required"] == True
        assert email_data["context"]["verification_url"] == "https://banwee.com/verify?token=abc123"

    def test_send_password_reset_email(self, background_tasks):
        """Test password reset email task"""
        send_password_reset_email(
            background_tasks=background_tasks,
            to_email="user@example.com",
            customer_name="Test User",
            reset_link="https://banwee.com/reset?token=xyz789"
        )
        
        background_tasks.add_task.assert_called_once()
        
        args, kwargs = background_tasks.add_task.call_args
        email_data = args[1]
        
        assert email_data["to_email"] == "user@example.com"
        assert email_data["mail_type"] == "password_reset"
        assert email_data["context"]["customer_name"] == "Test User"
        assert email_data["context"]["reset_link"] == "https://banwee.com/reset?token=xyz789"

    def test_send_low_stock_alert_email(self, background_tasks):
        """Test low stock alert email task"""
        low_stock_products = [
            {
                "name": "Test Product 1",
                "sku": "TEST-001",
                "current_stock": 5,
                "min_threshold": 10,
                "supplier": "Test Supplier"
            },
            {
                "name": "Test Product 2", 
                "sku": "TEST-002",
                "current_stock": 2,
                "min_threshold": 15
            }
        ]
        
        send_low_stock_alert_email(
            background_tasks=background_tasks,
            to_email="admin@example.com",
            recipient_name="Admin User",
            low_stock_products=low_stock_products,
            alert_date=datetime.now()
        )
        
        background_tasks.add_task.assert_called_once()
        
        args, kwargs = background_tasks.add_task.call_args
        email_data = args[1]
        
        assert email_data["to_email"] == "admin@example.com"
        assert email_data["mail_type"] == "low_stock_alert"
        assert email_data["context"]["recipient_name"] == "Admin User"
        assert len(email_data["context"]["low_stock_products"]) == 2
        assert email_data["context"]["low_stock_products"][0]["sku"] == "TEST-001"

    @pytest.mark.asyncio
    async def test_email_task_service_kafka_integration(self, email_task_service):
        """Test EmailTaskService Kafka integration"""
        email_data = {
            "to_email": "test@example.com",
            "mail_type": "test_email",
            "context": {"test": "data"}
        }
        
        # Create a mock producer with async send_message method
        mock_producer = AsyncMock()
        mock_producer.send_message = AsyncMock()
        
        # Mock the async get_kafka_producer_service function
        async def mock_get_producer():
            return mock_producer
        
        with patch('tasks.email_tasks.get_kafka_producer_service', side_effect=mock_get_producer) as mock_kafka:
            await email_task_service._send_email_via_kafka(email_data)
            
            # Verify the producer service was called
            mock_kafka.assert_called_once()
            # Verify send_message was called with correct parameters
            mock_producer.send_message.assert_called_once_with(
                email_task_service.kafka_topic,
                email_data
            )

    @pytest.mark.asyncio
    async def test_email_task_service_direct_fallback(self, email_task_service):
        """Test EmailTaskService direct email fallback when Kafka fails"""
        email_data = {
            "to_email": "test@example.com",
            "mail_type": "test_email",
            "context": {"test": "data"}
        }
        
        with patch('tasks.email_tasks.get_kafka_producer_service') as mock_kafka, \
             patch('tasks.email_tasks.send_email') as mock_send_email:
            
            # Make Kafka fail
            mock_kafka.side_effect = Exception("Kafka unavailable")
            mock_send_email.return_value = AsyncMock()
            
            await email_task_service._send_email_via_kafka(email_data)
            
            # Should fallback to direct email
            mock_send_email.assert_called_once_with(
                to_email="test@example.com",
                mail_type="test_email",
                context={"test": "data"}
            )

    def test_email_task_service_add_task(self, email_task_service, background_tasks):
        """Test adding email task to background tasks"""
        email_data = {
            "to_email": "test@example.com",
            "mail_type": "test_email",
            "context": {"test": "data"}
        }
        
        email_task_service.add_email_task(background_tasks, email_data)
        
        background_tasks.add_task.assert_called_once()
        args, kwargs = background_tasks.add_task.call_args
        assert args[1] == email_data


if __name__ == "__main__":
    pytest.main([__file__])