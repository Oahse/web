"""
Unit tests for subscription service
"""
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from decimal import Decimal
from uuid import uuid4
from datetime import datetime, timedelta

from services.subscriptions.subscription import SubscriptionService
from models.subscriptions import Subscription, SubscriptionStatus, SubscriptionItem
from models.product import ProductVariant
from core.errors import APIException


class TestSubscriptionService:
    
    @pytest_asyncio.fixture
    async def subscription_service(self, db_session):
        return SubscriptionService(db_session)
    
    @pytest.mark.asyncio
    async def test_create_subscription_success(self, subscription_service, test_user, test_product):
        """Test successful subscription creation"""
        product, variant = test_product
        
        subscription_data = {
            "user_id": test_user.id,
            "frequency": "monthly",
            "variant_ids": [variant.id],
            "quantities": [2]
        }
        
        subscription = await subscription_service.create_subscription(**subscription_data)
        
        assert subscription.user_id == test_user.id
        assert subscription.frequency == "monthly"
        assert subscription.status == SubscriptionStatus.ACTIVE
        assert subscription.next_billing_date is not None
        
        # Check subscription items
        assert len(subscription.items) == 1
        assert subscription.items[0].variant_id == variant.id
        assert subscription.items[0].quantity == 2
    
    @pytest.mark.asyncio
    async def test_create_subscription_invalid_variant(self, subscription_service, test_user):
        """Test subscription creation with invalid variant"""
        invalid_variant_id = uuid4()
        
        subscription_data = {
            "user_id": test_user.id,
            "frequency": "monthly",
            "variant_ids": [invalid_variant_id],
            "quantities": [1]
        }
        
        with pytest.raises(APIException) as exc_info:
            await subscription_service.create_subscription(**subscription_data)
        
        assert exc_info.value.status_code == 404
        assert "variant" in str(exc_info.value.message).lower()
    
    @pytest.mark.asyncio
    async def test_update_subscription_items(self, subscription_service, test_subscription, test_product):
        """Test updating subscription items"""
        product, variant = test_product
        
        # Add item to subscription
        new_items = [
            {"variant_id": variant.id, "quantity": 3}
        ]
        
        updated_subscription = await subscription_service.update_subscription_items(
            test_subscription.id,
            new_items
        )
        
        assert len(updated_subscription.items) == 1
        assert updated_subscription.items[0].variant_id == variant.id
        assert updated_subscription.items[0].quantity == 3
    
    @pytest.mark.asyncio
    async def test_pause_subscription(self, subscription_service, test_subscription):
        """Test pausing an active subscription"""
        # Ensure subscription is active
        test_subscription.status = SubscriptionStatus.ACTIVE
        await subscription_service.db.commit()
        
        paused_subscription = await subscription_service.pause_subscription(test_subscription.id)
        
        assert paused_subscription.status == SubscriptionStatus.PAUSED
        assert paused_subscription.paused_at is not None
    
    @pytest.mark.asyncio
    async def test_resume_subscription(self, subscription_service, test_subscription):
        """Test resuming a paused subscription"""
        # Set subscription as paused
        test_subscription.status = SubscriptionStatus.PAUSED
        test_subscription.paused_at = datetime.utcnow()
        await subscription_service.db.commit()
        
        resumed_subscription = await subscription_service.resume_subscription(test_subscription.id)
        
        assert resumed_subscription.status == SubscriptionStatus.ACTIVE
        assert resumed_subscription.paused_at is None
        assert resumed_subscription.next_billing_date > datetime.utcnow()
    
    @pytest.mark.asyncio
    async def test_cancel_subscription(self, subscription_service, test_subscription):
        """Test canceling a subscription"""
        canceled_subscription = await subscription_service.cancel_subscription(
            test_subscription.id,
            reason="customer_request"
        )
        
        assert canceled_subscription.status == SubscriptionStatus.CANCELED
        assert canceled_subscription.canceled_at is not None
        assert canceled_subscription.cancellation_reason == "customer_request"
    
    @pytest.mark.asyncio
    async def test_process_subscription_renewal(self, subscription_service, test_subscription, test_product):
        """Test processing subscription renewal"""
        product, variant = test_product
        
        # Add items to subscription
        item = SubscriptionItem(
            id=uuid4(),
            subscription_id=test_subscription.id,
            variant_id=variant.id,
            quantity=2,
            price=variant.price
        )
        subscription_service.db.add(item)
        await subscription_service.db.commit()
        
        # Set next billing date to past
        test_subscription.next_billing_date = datetime.utcnow() - timedelta(days=1)
        await subscription_service.db.commit()
        
        with patch('services.subscriptions.subscription.OrderService') as mock_order_service:
            mock_order_service.return_value.create_order.return_value = MagicMock(id=uuid4())
            
            renewed_subscription = await subscription_service.process_renewal(test_subscription.id)
            
            assert renewed_subscription.next_billing_date > datetime.utcnow()
            assert renewed_subscription.billing_cycle_count > 0
    
    @pytest.mark.asyncio
    async def test_calculate_subscription_total(self, subscription_service, test_subscription, test_product):
        """Test calculating subscription total"""
        product, variant = test_product
        
        # Add items to subscription
        item1 = SubscriptionItem(
            id=uuid4(),
            subscription_id=test_subscription.id,
            variant_id=variant.id,
            quantity=2,
            price=Decimal("50.00")
        )
        item2 = SubscriptionItem(
            id=uuid4(),
            subscription_id=test_subscription.id,
            variant_id=variant.id,
            quantity=1,
            price=Decimal("30.00")
        )
        subscription_service.db.add_all([item1, item2])
        await subscription_service.db.commit()
        
        total = await subscription_service.calculate_subscription_total(test_subscription.id)
        
        # (2 * 50.00) + (1 * 30.00) = 130.00
        assert total == Decimal("130.00")
    
    @pytest.mark.asyncio
    async def test_get_user_subscriptions(self, subscription_service, test_user, test_subscription):
        """Test getting user subscriptions"""
        subscriptions = await subscription_service.get_user_subscriptions(test_user.id)
        
        assert len(subscriptions) == 1
        assert subscriptions[0].id == test_subscription.id
        assert subscriptions[0].user_id == test_user.id
    
    @pytest.mark.asyncio
    async def test_get_subscription_by_id(self, subscription_service, test_subscription):
        """Test getting subscription by ID"""
        subscription = await subscription_service.get_subscription_by_id(test_subscription.id)
        
        assert subscription.id == test_subscription.id
        assert subscription.user_id == test_subscription.user_id
    
    @pytest.mark.asyncio
    async def test_get_subscription_not_found(self, subscription_service):
        """Test getting non-existent subscription"""
        with pytest.raises(APIException) as exc_info:
            await subscription_service.get_subscription_by_id(uuid4())
        
        assert exc_info.value.status_code == 404
        assert "subscription" in str(exc_info.value.message).lower()
    
    @pytest.mark.asyncio
    async def test_update_subscription_frequency(self, subscription_service, test_subscription):
        """Test updating subscription frequency"""
        new_frequency = "weekly"
        
        updated_subscription = await subscription_service.update_subscription_frequency(
            test_subscription.id,
            new_frequency
        )
        
        assert updated_subscription.frequency == new_frequency
        # Next billing date should be recalculated
        assert updated_subscription.next_billing_date != test_subscription.next_billing_date
    
    @pytest.mark.asyncio
    async def test_apply_discount_to_subscription(self, subscription_service, test_subscription):
        """Test applying discount to subscription"""
        discount_code = "SAVE20"
        discount_amount = Decimal("20.00")
        
        with patch('services.subscriptions.subscription.DiscountService') as mock_discount_service:
            mock_discount_service.return_value.validate_discount.return_value = {
                "valid": True,
                "discount_amount": discount_amount,
                "discount_type": "fixed"
            }
            
            updated_subscription = await subscription_service.apply_discount(
                test_subscription.id,
                discount_code
            )
            
            assert updated_subscription.discount_code == discount_code
            assert updated_subscription.discount_amount == discount_amount
    
    @pytest.mark.asyncio
    async def test_get_subscription_analytics(self, subscription_service, test_user, test_subscription):
        """Test getting subscription analytics"""
        analytics = await subscription_service.get_subscription_analytics(test_user.id)
        
        assert "total_subscriptions" in analytics
        assert "active_subscriptions" in analytics
        assert "total_spent" in analytics
        assert "average_order_value" in analytics
        
        assert analytics["total_subscriptions"] == 1
        assert analytics["active_subscriptions"] == 1
    
    @pytest.mark.asyncio
    async def test_get_due_renewals(self, subscription_service, test_subscription):
        """Test getting subscriptions due for renewal"""
        # Set subscription due for renewal
        test_subscription.next_billing_date = datetime.utcnow() - timedelta(hours=1)
        test_subscription.status = SubscriptionStatus.ACTIVE
        await subscription_service.db.commit()
        
        due_subscriptions = await subscription_service.get_due_renewals()
        
        assert len(due_subscriptions) == 1
        assert due_subscriptions[0].id == test_subscription.id
    
    @pytest.mark.asyncio
    async def test_subscription_status_transitions(self, subscription_service, test_subscription):
        """Test valid subscription status transitions"""
        # Active -> Paused
        test_subscription.status = SubscriptionStatus.ACTIVE
        await subscription_service.db.commit()
        
        paused = await subscription_service.pause_subscription(test_subscription.id)
        assert paused.status == SubscriptionStatus.PAUSED
        
        # Paused -> Active
        resumed = await subscription_service.resume_subscription(test_subscription.id)
        assert resumed.status == SubscriptionStatus.ACTIVE
        
        # Active -> Canceled
        canceled = await subscription_service.cancel_subscription(test_subscription.id)
        assert canceled.status == SubscriptionStatus.CANCELED
    
    @pytest.mark.asyncio
    async def test_invalid_status_transition(self, subscription_service, test_subscription):
        """Test invalid subscription status transitions"""
        # Set subscription as canceled
        test_subscription.status = SubscriptionStatus.CANCELED
        await subscription_service.db.commit()
        
        # Try to resume canceled subscription
        with pytest.raises(APIException) as exc_info:
            await subscription_service.resume_subscription(test_subscription.id)
        
        assert exc_info.value.status_code == 400
        assert "cannot resume" in str(exc_info.value.message).lower()
    
    @pytest.mark.asyncio
    async def test_subscription_item_price_tracking(self, subscription_service, test_subscription, test_product):
        """Test that subscription items track price at time of creation"""
        product, variant = test_product
        
        # Update variant price
        original_price = variant.price
        variant.price = Decimal("199.99")
        await subscription_service.db.commit()
        
        # Add item to subscription
        new_items = [
            {"variant_id": variant.id, "quantity": 1}
        ]
        
        updated_subscription = await subscription_service.update_subscription_items(
            test_subscription.id,
            new_items
        )
        
        # Item should have current price, not original
        assert updated_subscription.items[0].price == Decimal("199.99")
        assert updated_subscription.items[0].price != original_price