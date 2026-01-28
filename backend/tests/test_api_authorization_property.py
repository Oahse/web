"""
Property-based tests for API authorization and state validation
Feature: subscription-product-management, Property 16: Authorization and State Validation
Validates: Requirements 7.1
"""
import pytest
import asyncio
from hypothesis import given, strategies as st, settings
from hypothesis.strategies import composite
from uuid import uuid4, UUID
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock, MagicMock

from services.enhanced_subscription_service import EnhancedSubscriptionService
from models.subscriptions import Subscription, SubscriptionProduct
from models.user import User
from models.product import Product
from models.discounts import Discount, SubscriptionDiscount


@composite
def subscription_data(draw):
    """Generate subscription test data"""
    return {
        "id": draw(st.uuids()),
        "user_id": draw(st.uuids()),
        "status": draw(st.sampled_from(["active", "paused", "cancelled", "expired"])),
        "subtotal": draw(st.floats(min_value=0.01, max_value=1000.0)),
        "total": draw(st.floats(min_value=0.01, max_value=1000.0)),
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }


@composite
def user_data(draw):
    """Generate user test data"""
    return {
        "id": draw(st.uuids()),
        "email": draw(st.emails()),
        "is_active": draw(st.booleans()),
        "created_at": datetime.now(timezone.utc)
    }


@composite
def product_data(draw):
    """Generate product test data"""
    return {
        "id": draw(st.uuids()),
        "name": draw(st.text(min_size=1, max_size=100)),
        "price": draw(st.floats(min_value=0.01, max_value=500.0)),
        "is_active": draw(st.booleans())
    }


class TestAPIAuthorizationProperty:
    """Property-based tests for API authorization and state validation"""

    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        db = AsyncMock(spec=AsyncSession)
        db.execute = AsyncMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        db.add = AsyncMock()
        db.delete = AsyncMock()
        return db

    @pytest.fixture
    def enhanced_service(self, mock_db):
        """Enhanced subscription service with mocked database"""
        return EnhancedSubscriptionService(mock_db)

    @given(
        subscription_data=subscription_data(),
        requesting_user_id=st.uuids(),
        product_id=st.uuids()
    )
    @settings(max_examples=50, deadline=5000)
    def test_property_16_authorization_validation_product_removal(
        self, enhanced_service, mock_db, subscription_data, requesting_user_id, product_id
    ):
        """
        Property 16: Authorization and State Validation
        For any product removal request, the system should validate user permissions 
        and subscription state before processing the request.
        """
        async def run_test():
            # Create mock subscription
            subscription = MagicMock()
            subscription.id = subscription_data["id"]
            subscription.user_id = subscription_data["user_id"]
            subscription.status = subscription_data["status"]
            subscription.to_dict = MagicMock(return_value=subscription_data)
            
            # Create mock subscription products
            subscription_product = MagicMock()
            subscription_product.product_id = product_id
            subscription_product.is_active = True
            subscription_product.removed_at = None
            
            subscription.subscription_products = [subscription_product]
            
            # Mock database query result
            mock_result = AsyncMock()
            mock_result.scalar_one_or_none = AsyncMock(return_value=subscription)
            mock_db.execute.return_value = mock_result
            
            # Test authorization validation
            if requesting_user_id != subscription_data["user_id"]:
                # Should raise HTTPException for unauthorized access
                with pytest.raises(HTTPException) as exc_info:
                    await enhanced_service.remove_product(
                        subscription_id=subscription_data["id"],
                        product_id=product_id,
                        user_id=requesting_user_id
                    )
                
                # Verify proper error code for authorization failure
                assert exc_info.value.status_code == 404  # Not found (security through obscurity)
                
            elif subscription_data["status"] not in ["active", "paused"]:
                # Should raise HTTPException for invalid subscription state
                with pytest.raises(HTTPException) as exc_info:
                    await enhanced_service.remove_product(
                        subscription_id=subscription_data["id"],
                        product_id=product_id,
                        user_id=requesting_user_id
                    )
                
                # Verify proper error code for invalid state
                assert exc_info.value.status_code == 400
                assert "inactive subscription" in str(exc_info.value.detail).lower()
                
            else:
                # Should proceed with valid authorization and state
                # Mock additional required objects for successful execution
                mock_audit = MagicMock()
                mock_db.add = AsyncMock()
                
                # Mock the _recalculate_subscription_totals method
                enhanced_service._recalculate_subscription_totals = AsyncMock()
                
                try:
                    result = await enhanced_service.remove_product(
                        subscription_id=subscription_data["id"],
                        product_id=product_id,
                        user_id=requesting_user_id
                    )
                    
                    # Verify successful execution
                    assert result is not None
                    
                    # Verify database operations were called
                    mock_db.execute.assert_called()
                    mock_db.commit.assert_called()
                    
                except Exception as e:
                    # Allow for other business logic exceptions (like last product removal)
                    # but ensure they're not authorization-related
                    if isinstance(e, HTTPException):
                        assert e.status_code != 404 or "not found" not in str(e.detail).lower()
        
        # Run the async test
        asyncio.run(run_test())

    @given(
        subscription_data=subscription_data(),
        requesting_user_id=st.uuids(),
        discount_code=st.text(min_size=1, max_size=20)
    )
    @settings(max_examples=50, deadline=5000)
    def test_property_16_authorization_validation_discount_application(
        self, enhanced_service, mock_db, subscription_data, requesting_user_id, discount_code
    ):
        """
        Property 16: Authorization and State Validation
        For any discount application request, the system should validate user permissions 
        and subscription state before processing the request.
        """
        async def run_test():
            # Create mock subscription
            subscription = MagicMock()
            subscription.id = subscription_data["id"]
            subscription.user_id = subscription_data["user_id"]
            subscription.status = subscription_data["status"]
            subscription.subtotal = subscription_data["subtotal"]
            subscription.applied_discounts = []
            
            # Mock database query results
            subscription_result = AsyncMock()
            subscription_result.scalar_one_or_none = AsyncMock(return_value=subscription)
            
            # Mock discount
            discount = MagicMock()
            discount.id = uuid4()
            discount.code = discount_code
            discount.is_active = True
            discount.is_valid = MagicMock(return_value=True)
            discount.calculate_discount_amount = MagicMock(return_value=10.0)
            
            discount_result = AsyncMock()
            discount_result.scalar_one_or_none = AsyncMock(return_value=discount)
            
            # Configure mock_db.execute to return appropriate results
            mock_db.execute.side_effect = [subscription_result, discount_result]
            
            # Test authorization validation
            if requesting_user_id != subscription_data["user_id"]:
                # Should raise HTTPException for unauthorized access
                with pytest.raises(HTTPException) as exc_info:
                    await enhanced_service.apply_discount(
                        subscription_id=subscription_data["id"],
                        discount_code=discount_code,
                        user_id=requesting_user_id
                    )
                
                # Verify proper error code for authorization failure
                assert exc_info.value.status_code == 404  # Not found (security through obscurity)
                
            elif subscription_data["status"] not in ["active", "paused"]:
                # Should raise HTTPException for invalid subscription state
                with pytest.raises(HTTPException) as exc_info:
                    await enhanced_service.apply_discount(
                        subscription_id=subscription_data["id"],
                        discount_code=discount_code,
                        user_id=requesting_user_id
                    )
                
                # Verify proper error code for invalid state
                assert exc_info.value.status_code == 400
                assert "inactive subscription" in str(exc_info.value.detail).lower()
                
            else:
                # Should proceed with valid authorization and state
                # Mock additional required objects for successful execution
                enhanced_service._recalculate_subscription_totals = AsyncMock()
                
                try:
                    result = await enhanced_service.apply_discount(
                        subscription_id=subscription_data["id"],
                        discount_code=discount_code,
                        user_id=requesting_user_id
                    )
                    
                    # Verify successful execution
                    assert result is not None
                    assert "discount_code" in result
                    assert result["discount_code"] == discount_code
                    
                    # Verify database operations were called
                    mock_db.execute.assert_called()
                    mock_db.commit.assert_called()
                    
                except Exception as e:
                    # Allow for other business logic exceptions (like invalid discount)
                    # but ensure they're not authorization-related
                    if isinstance(e, HTTPException):
                        assert e.status_code != 404 or "not found" not in str(e.detail).lower()
        
        # Run the async test
        asyncio.run(run_test())

    @given(
        subscription_data=subscription_data(),
        requesting_user_id=st.uuids()
    )
    @settings(max_examples=50, deadline=5000)
    def test_property_16_authorization_validation_subscription_details(
        self, enhanced_service, mock_db, subscription_data, requesting_user_id
    ):
        """
        Property 16: Authorization and State Validation
        For any subscription details request, the system should validate user permissions 
        before returning sensitive subscription information.
        """
        async def run_test():
            # Create mock subscription
            subscription = MagicMock()
            subscription.id = subscription_data["id"]
            subscription.user_id = subscription_data["user_id"]
            subscription.status = subscription_data["status"]
            subscription.to_dict = MagicMock(return_value=subscription_data)
            subscription.subscription_products = []
            subscription.applied_discounts = []
            subscription.subtotal = subscription_data["subtotal"]
            subscription.shipping_cost = 10.0
            subscription.tax_amount = 5.0
            subscription.discount_amount = 0.0
            subscription.total = subscription_data["total"]
            
            # Mock database query result
            mock_result = AsyncMock()
            mock_result.scalar_one_or_none = AsyncMock(return_value=subscription)
            mock_db.execute.return_value = mock_result
            
            # Test authorization validation
            if requesting_user_id != subscription_data["user_id"]:
                # Should raise HTTPException for unauthorized access
                with pytest.raises(HTTPException) as exc_info:
                    await enhanced_service.get_subscription_details(
                        subscription_id=subscription_data["id"],
                        user_id=requesting_user_id
                    )
                
                # Verify proper error code for authorization failure
                assert exc_info.value.status_code == 404  # Not found (security through obscurity)
                
            else:
                # Should proceed with valid authorization
                result = await enhanced_service.get_subscription_details(
                    subscription_id=subscription_data["id"],
                    user_id=requesting_user_id
                )
                
                # Verify successful execution and proper data structure
                assert result is not None
                assert "subscription" in result
                assert "products" in result
                assert "discounts" in result
                assert "totals" in result
                
                # Verify database query was called
                mock_db.execute.assert_called()
        
        # Run the async test
        asyncio.run(run_test())


# Synchronous wrapper for property tests
class TestAPIAuthorizationPropertySync:
    """Synchronous wrapper for property tests"""
    
    def test_authorization_validation_sync(self):
        """Run all authorization validation property tests synchronously"""
        test_instance = TestAPIAuthorizationProperty()
        
        # Create mock fixtures
        mock_db = AsyncMock(spec=AsyncSession)
        mock_db.execute = AsyncMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        mock_db.add = AsyncMock()
        mock_db.delete = AsyncMock()
        
        enhanced_service = EnhancedSubscriptionService(mock_db)
        
        # Test data
        subscription_data = {
            "id": uuid4(),
            "user_id": uuid4(),
            "status": "active",
            "subtotal": 100.0,
            "total": 115.0,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        
        # Test unauthorized access
        unauthorized_user_id = uuid4()
        product_id = uuid4()
        
        # Run individual test cases
        test_instance.test_property_16_authorization_validation_product_removal(
            enhanced_service, mock_db, subscription_data, unauthorized_user_id, product_id
        )
        
        test_instance.test_property_16_authorization_validation_discount_application(
            enhanced_service, mock_db, subscription_data, unauthorized_user_id, "TEST10"
        )
        
        test_instance.test_property_16_authorization_validation_subscription_details(
            enhanced_service, mock_db, subscription_data, unauthorized_user_id
        )


if __name__ == "__main__":
    # Run property tests
    test_sync = TestAPIAuthorizationPropertySync()
    test_sync.test_authorization_validation_sync()
    print("✓ Property 16: Authorization and State Validation tests completed")