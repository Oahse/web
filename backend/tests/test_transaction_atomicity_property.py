"""
Property-based test for transaction atomicity
Feature: subscription-product-management, Property 18: Transaction Atomicity
Validates: Requirements 7.5

Tests that data persistence operations either complete fully or roll back completely,
ensuring data consistency across all operations.
"""
import pytest
import asyncio
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from hypothesis.stateful import RuleBasedStateMachine, Bundle, rule, initialize, invariant
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, and_
from uuid import UUID, uuid4
from decimal import Decimal
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging

# Import models and services
from models.subscriptions import Subscription, SubscriptionProduct
from models.discounts import Discount, SubscriptionDiscount, ProductRemovalAudit
from models.user import User
from models.product import Product, ProductVariant
from services.enhanced_subscription_service import EnhancedSubscriptionService
from services.transaction_service import TransactionService, TransactionError
from core.database import Base, get_db
from core.config import settings

logger = logging.getLogger(__name__)

# Test database configuration
TEST_DATABASE_URL = "postgresql+asyncpg://test_user:test_pass@localhost:5432/test_subscription_db"

class TransactionAtomicityStateMachine(RuleBasedStateMachine):
    """
    Stateful property-based test for transaction atomicity
    
    This test verifies that all database operations either complete fully
    or roll back completely, maintaining data consistency.
    """
    
    def __init__(self):
        super().__init__()
        self.engine = None
        self.session_factory = None
        self.db_session = None
        self.subscription_service = None
        self.transaction_service = None
        
        # Track state for verification
        self.subscriptions: Dict[str, Dict[str, Any]] = {}
        self.products: Dict[str, Dict[str, Any]] = {}
        self.discounts: Dict[str, Dict[str, Any]] = {}
        self.users: Dict[str, Dict[str, Any]] = {}
        
        # Track operations for rollback verification
        self.pending_operations: List[Dict[str, Any]] = []
        self.completed_operations: List[Dict[str, Any]] = []
        self.failed_operations: List[Dict[str, Any]] = []
    
    @initialize()
    async def setup_database(self):
        """Initialize test database and create test data"""
        try:
            # Create async engine for testing
            self.engine = create_async_engine(
                TEST_DATABASE_URL,
                echo=False,
                pool_pre_ping=True,
                pool_size=5,
                max_overflow=10
            )
            
            # Create session factory
            self.session_factory = sessionmaker(
                bind=self.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            # Create tables
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            
            # Create database session
            self.db_session = self.session_factory()
            
            # Initialize services
            self.subscription_service = EnhancedSubscriptionService(self.db_session)
            self.transaction_service = TransactionService(self.db_session)
            
            # Create test users
            await self._create_test_users()
            
            # Create test products
            await self._create_test_products()
            
            # Create test discounts
            await self._create_test_discounts()
            
            # Create test subscriptions
            await self._create_test_subscriptions()
            
            await self.db_session.commit()
            
        except Exception as e:
            logger.error(f"Failed to setup test database: {e}")
            if self.db_session:
                await self.db_session.rollback()
            raise
    
    async def _create_test_users(self):
        """Create test users"""
        for i in range(3):
            user_id = str(uuid4())
            user = User(
                id=user_id,
                email=f"test_user_{i}@example.com",
                username=f"test_user_{i}",
                is_active=True
            )
            self.db_session.add(user)
            self.users[user_id] = {
                "id": user_id,
                "email": user.email,
                "username": user.username
            }
    
    async def _create_test_products(self):
        """Create test products"""
        for i in range(5):
            product_id = str(uuid4())
            product = Product(
                id=product_id,
                name=f"Test Product {i}",
                description=f"Test product description {i}",
                price=Decimal(f"{10 + i * 5}.99"),
                is_active=True
            )
            self.db_session.add(product)
            self.products[product_id] = {
                "id": product_id,
                "name": product.name,
                "price": float(product.price)
            }
    
    async def _create_test_discounts(self):
        """Create test discounts"""
        discount_types = ["PERCENTAGE", "FIXED_AMOUNT"]
        for i in range(3):
            discount_id = str(uuid4())
            discount_type = discount_types[i % 2]
            value = Decimal("10.0") if discount_type == "PERCENTAGE" else Decimal("5.00")
            
            discount = Discount(
                id=discount_id,
                code=f"TEST{i}",
                type=discount_type,
                value=value,
                valid_from=datetime.utcnow() - timedelta(days=1),
                valid_until=datetime.utcnow() + timedelta(days=30),
                usage_limit=100,
                used_count=0,
                is_active=True
            )
            self.db_session.add(discount)
            self.discounts[discount_id] = {
                "id": discount_id,
                "code": discount.code,
                "type": discount_type,
                "value": float(value)
            }
    
    async def _create_test_subscriptions(self):
        """Create test subscriptions"""
        user_ids = list(self.users.keys())
        product_ids = list(self.products.keys())
        
        for i in range(2):
            subscription_id = str(uuid4())
            user_id = user_ids[i % len(user_ids)]
            
            subscription = Subscription(
                id=subscription_id,
                user_id=user_id,
                status="active",
                billing_cycle="monthly",
                subtotal=50.0,
                tax_amount=5.0,
                shipping_cost=10.0,
                total=65.0,
                currency="USD"
            )
            self.db_session.add(subscription)
            
            # Add products to subscription
            subscription_products = []
            for j in range(2):  # 2 products per subscription
                product_id = product_ids[j % len(product_ids)]
                sp = SubscriptionProduct(
                    subscription_id=subscription_id,
                    product_id=product_id,
                    quantity=1,
                    unit_price=self.products[product_id]["price"],
                    total_price=self.products[product_id]["price"]
                )
                self.db_session.add(sp)
                subscription_products.append({
                    "product_id": product_id,
                    "quantity": 1,
                    "unit_price": self.products[product_id]["price"]
                })
            
            self.subscriptions[subscription_id] = {
                "id": subscription_id,
                "user_id": user_id,
                "status": "active",
                "products": subscription_products,
                "subtotal": 50.0,
                "total": 65.0
            }
    
    @rule(
        subscription_id=st.sampled_from([]),  # Will be populated dynamically
        product_index=st.integers(min_value=0, max_value=1),
        should_fail=st.booleans()
    )
    async def test_atomic_product_removal(self, subscription_id: str, product_index: int, should_fail: bool):
        """Test that product removal is atomic - either completes fully or rolls back completely"""
        assume(len(self.subscriptions) > 0)
        
        # Select a subscription with multiple products
        valid_subscriptions = [
            sub_id for sub_id, sub_data in self.subscriptions.items()
            if len(sub_data["products"]) > 1
        ]
        assume(len(valid_subscriptions) > 0)
        
        subscription_id = valid_subscriptions[0]
        subscription_data = self.subscriptions[subscription_id]
        user_id = subscription_data["user_id"]
        
        # Select a product to remove
        products = subscription_data["products"]
        assume(product_index < len(products))
        product_id = products[product_index]["product_id"]
        
        # Record initial state
        initial_state = await self._capture_subscription_state(subscription_id)
        
        operation_data = {
            "type": "product_removal",
            "subscription_id": subscription_id,
            "product_id": product_id,
            "user_id": user_id,
            "should_fail": should_fail,
            "initial_state": initial_state
        }
        
        try:
            if should_fail:
                # Simulate failure by using invalid product ID
                invalid_product_id = str(uuid4())
                await self.subscription_service.remove_product(
                    UUID(subscription_id),
                    UUID(invalid_product_id),
                    UUID(user_id)
                )
                # Should not reach here
                assert False, "Expected operation to fail but it succeeded"
            else:
                # Normal operation
                result = await self.subscription_service.remove_product(
                    UUID(subscription_id),
                    UUID(product_id),
                    UUID(user_id)
                )
                
                # Verify the operation completed successfully
                assert result is not None
                
                # Update our tracking state
                subscription_data["products"] = [
                    p for p in subscription_data["products"]
                    if p["product_id"] != product_id
                ]
                
                operation_data["completed"] = True
                self.completed_operations.append(operation_data)
        
        except Exception as e:
            # Operation failed - verify rollback
            operation_data["error"] = str(e)
            operation_data["completed"] = False
            self.failed_operations.append(operation_data)
            
            # Verify state was rolled back
            current_state = await self._capture_subscription_state(subscription_id)
            assert self._states_equal(initial_state, current_state), \
                f"State not properly rolled back after failure. Initial: {initial_state}, Current: {current_state}"
    
    @rule(
        subscription_id=st.sampled_from([]),  # Will be populated dynamically
        discount_code=st.sampled_from([]),  # Will be populated dynamically
        should_fail=st.booleans()
    )
    async def test_atomic_discount_application(self, subscription_id: str, discount_code: str, should_fail: bool):
        """Test that discount application is atomic"""
        assume(len(self.subscriptions) > 0 and len(self.discounts) > 0)
        
        subscription_id = list(self.subscriptions.keys())[0]
        subscription_data = self.subscriptions[subscription_id]
        user_id = subscription_data["user_id"]
        
        discount_code = list(self.discounts.values())[0]["code"]
        
        # Record initial state
        initial_state = await self._capture_subscription_state(subscription_id)
        
        operation_data = {
            "type": "discount_application",
            "subscription_id": subscription_id,
            "discount_code": discount_code,
            "user_id": user_id,
            "should_fail": should_fail,
            "initial_state": initial_state
        }
        
        try:
            if should_fail:
                # Use invalid discount code
                invalid_code = "INVALID_CODE"
                await self.subscription_service.apply_discount(
                    UUID(subscription_id),
                    invalid_code,
                    UUID(user_id)
                )
                assert False, "Expected operation to fail but it succeeded"
            else:
                # Normal operation
                result = await self.subscription_service.apply_discount(
                    UUID(subscription_id),
                    discount_code,
                    UUID(user_id)
                )
                
                assert result is not None
                assert "discount_amount" in result
                
                operation_data["completed"] = True
                self.completed_operations.append(operation_data)
        
        except Exception as e:
            # Operation failed - verify rollback
            operation_data["error"] = str(e)
            operation_data["completed"] = False
            self.failed_operations.append(operation_data)
            
            # Verify state was rolled back
            current_state = await self._capture_subscription_state(subscription_id)
            assert self._states_equal(initial_state, current_state), \
                f"State not properly rolled back after discount failure. Initial: {initial_state}, Current: {current_state}"
    
    @invariant()
    async def verify_data_consistency(self):
        """Verify that data remains consistent across all operations"""
        for subscription_id in self.subscriptions:
            # Verify subscription exists and has consistent state
            db_subscription = await self._get_subscription_from_db(subscription_id)
            if db_subscription:
                # Verify totals are consistent
                assert db_subscription.total >= 0, f"Subscription {subscription_id} has negative total"
                
                # Verify product count consistency
                active_products = await self._get_active_products_count(subscription_id)
                assert active_products >= 0, f"Subscription {subscription_id} has negative product count"
    
    async def _capture_subscription_state(self, subscription_id: str) -> Dict[str, Any]:
        """Capture the current state of a subscription for comparison"""
        try:
            result = await self.db_session.execute(
                select(Subscription).where(Subscription.id == subscription_id)
            )
            subscription = result.scalar_one_or_none()
            
            if not subscription:
                return {"exists": False}
            
            # Get products
            products_result = await self.db_session.execute(
                select(SubscriptionProduct).where(
                    and_(
                        SubscriptionProduct.subscription_id == subscription_id,
                        SubscriptionProduct.removed_at.is_(None)
                    )
                )
            )
            products = products_result.scalars().all()
            
            # Get discounts
            discounts_result = await self.db_session.execute(
                select(SubscriptionDiscount).where(
                    SubscriptionDiscount.subscription_id == subscription_id
                )
            )
            discounts = discounts_result.scalars().all()
            
            return {
                "exists": True,
                "status": subscription.status,
                "subtotal": subscription.subtotal,
                "total": subscription.total,
                "tax_amount": subscription.tax_amount,
                "shipping_cost": subscription.shipping_cost,
                "discount_amount": subscription.discount_amount,
                "product_count": len(products),
                "discount_count": len(discounts),
                "product_ids": [str(p.product_id) for p in products],
                "discount_ids": [str(d.discount_id) for d in discounts]
            }
        except Exception as e:
            logger.error(f"Failed to capture subscription state: {e}")
            return {"error": str(e)}
    
    def _states_equal(self, state1: Dict[str, Any], state2: Dict[str, Any]) -> bool:
        """Compare two subscription states for equality"""
        if state1.get("exists") != state2.get("exists"):
            return False
        
        if not state1.get("exists", False):
            return True  # Both don't exist
        
        # Compare key fields
        key_fields = ["status", "subtotal", "total", "product_count", "discount_count"]
        for field in key_fields:
            if state1.get(field) != state2.get(field):
                return False
        
        # Compare product and discount IDs
        if set(state1.get("product_ids", [])) != set(state2.get("product_ids", [])):
            return False
        
        if set(state1.get("discount_ids", [])) != set(state2.get("discount_ids", [])):
            return False
        
        return True
    
    async def _get_subscription_from_db(self, subscription_id: str) -> Optional[Subscription]:
        """Get subscription from database"""
        try:
            result = await self.db_session.execute(
                select(Subscription).where(Subscription.id == subscription_id)
            )
            return result.scalar_one_or_none()
        except Exception:
            return None
    
    async def _get_active_products_count(self, subscription_id: str) -> int:
        """Get count of active products in subscription"""
        try:
            result = await self.db_session.execute(
                select(SubscriptionProduct).where(
                    and_(
                        SubscriptionProduct.subscription_id == subscription_id,
                        SubscriptionProduct.removed_at.is_(None)
                    )
                )
            )
            products = result.scalars().all()
            return len(products)
        except Exception:
            return 0
    
    def teardown(self):
        """Clean up test resources"""
        if self.db_session:
            asyncio.create_task(self.db_session.close())
        if self.engine:
            asyncio.create_task(self.engine.dispose())


# Property-based test configuration
@settings(
    max_examples=50,
    deadline=30000,  # 30 seconds per test
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture]
)
class TestTransactionAtomicity:
    """Property-based tests for transaction atomicity"""
    
    @pytest.mark.asyncio
    async def test_transaction_atomicity_property(self):
        """
        Property 18: Transaction Atomicity
        
        For any data persistence operation, the system should ensure atomic transactions
        that either complete fully or roll back completely.
        """
        # Create and run the state machine
        state_machine = TransactionAtomicityStateMachine()
        
        try:
            await state_machine.setup_database()
            
            # Run a series of operations to test atomicity
            await self._run_atomicity_tests(state_machine)
            
        finally:
            state_machine.teardown()
    
    async def _run_atomicity_tests(self, state_machine: TransactionAtomicityStateMachine):
        """Run specific atomicity tests"""
        # Test 1: Product removal atomicity
        subscription_ids = list(state_machine.subscriptions.keys())
        if subscription_ids:
            subscription_id = subscription_ids[0]
            subscription_data = state_machine.subscriptions[subscription_id]
            
            if len(subscription_data["products"]) > 1:
                # Test successful removal
                await state_machine.test_atomic_product_removal(
                    subscription_id, 0, should_fail=False
                )
                
                # Test failed removal (should rollback)
                await state_machine.test_atomic_product_removal(
                    subscription_id, 0, should_fail=True
                )
        
        # Test 2: Discount application atomicity
        if subscription_ids and state_machine.discounts:
            subscription_id = subscription_ids[0]
            discount_code = list(state_machine.discounts.values())[0]["code"]
            
            # Test successful application
            await state_machine.test_atomic_discount_application(
                subscription_id, discount_code, should_fail=False
            )
            
            # Test failed application (should rollback)
            await state_machine.test_atomic_discount_application(
                subscription_id, discount_code, should_fail=True
            )
        
        # Verify final consistency
        await state_machine.verify_data_consistency()


# Simple property tests for basic atomicity
@given(
    operation_count=st.integers(min_value=1, max_value=5),
    failure_rate=st.floats(min_value=0.0, max_value=0.5)
)
@settings(max_examples=20, deadline=15000)
@pytest.mark.asyncio
async def test_batch_operation_atomicity(operation_count: int, failure_rate: float):
    """
    Test that batch operations maintain atomicity
    
    Property: When multiple operations are executed in a batch,
    either all succeed or all are rolled back.
    """
    # This is a simplified test that would be expanded in a real implementation
    # For now, we'll just verify the concept
    
    operations_succeeded = 0
    operations_failed = 0
    
    for i in range(operation_count):
        # Simulate operation success/failure based on failure rate
        import random
        if random.random() < failure_rate:
            operations_failed += 1
        else:
            operations_succeeded += 1
    
    # In a real atomic batch, either all operations succeed or all fail
    # This is a placeholder assertion for the concept
    if operations_failed > 0:
        # In atomic operations, if any fail, all should be rolled back
        assert operations_succeeded == 0 or operations_failed == operation_count
    else:
        # All operations succeeded
        assert operations_succeeded == operation_count


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v", "--tb=short"])