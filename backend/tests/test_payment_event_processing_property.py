"""
Property-based test for payment event processing.

This test validates Property 17: Payment event processing
Requirements: 6.2, 6.3

**Feature: platform-modernization, Property 17: Payment event processing**
"""
import pytest
import sys
import os
from unittest.mock import AsyncMock, MagicMock, patch
from hypothesis import given, strategies as st, settings, HealthCheck
import asyncio
from datetime import datetime
from decimal import Decimal
import uuid

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')

# Global settings for all property tests to handle async operations
DEFAULT_SETTINGS = settings(
    max_examples=100,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
    deadline=None  # Disable deadline for async operations with mocking
)


class TestPaymentEventProcessingProperty:
    """Property-based tests for payment event processing"""

    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        db = AsyncMock()
        db.execute = AsyncMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        return db

    @pytest.fixture
    def payment_service(self, mock_db):
        """Create PaymentService instance with mocked dependencies"""
        from services.payment import PaymentService
        return PaymentService(mock_db)

    @pytest.fixture
    def sample_transaction(self):
        """Create a sample transaction for testing"""
        from models.transaction import Transaction
        return Transaction(
            id=uuid7(),
            user_id=uuid7(),
            order_id=uuid7(),
            stripe_payment_intent_id="pi_test_123456789",
            amount=Decimal("99.99"),
            currency="USD",
            status="pending",
            transaction_type="payment",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

    @given(
        payment_intent_id=st.text(min_size=10, max_size=50, alphabet=st.characters(whitelist_categories=('Ll', 'Lu', 'Nd', 'Pc'))),
        amount_received=st.integers(min_value=100, max_value=100000),  # Amount in cents
        event_id=st.text(min_size=10, max_size=50, alphabet=st.characters(whitelist_categories=('Ll', 'Lu', 'Nd', 'Pc')))
    )
    @DEFAULT_SETTINGS
    def test_payment_intent_succeeded_processing_property(
        self, payment_service, mock_db, sample_transaction, payment_intent_id, amount_received, event_id
    ):
        """
        Property: For any Stripe payment_intent.succeeded event, the corresponding transaction status
        should be updated to 'succeeded' and appropriate follow-up actions should be triggered.
        
        **Feature: platform-modernization, Property 17: Payment event processing**
        **Validates: Requirements 6.2**
        """
        # Setup the payment intent data
        payment_data = {
            "id": payment_intent_id,
            "status": "succeeded",
            "amount_received": amount_received
        }
        
        # Mock database query result for finding the transaction
        mock_result = MagicMock()
        mock_result.rowcount = 1  # Simulate successful update
        
        # Mock transaction retrieval for follow-up processing
        mock_transaction_result = MagicMock()
        sample_transaction.stripe_payment_intent_id = payment_intent_id
        sample_transaction.status = "succeeded"
        mock_transaction_result.scalar_one_or_none.return_value = sample_transaction
        
        # Configure mock to return different results for update vs select queries
        mock_db.execute.side_effect = [mock_result, mock_transaction_result]
        
        # Mock the email sending and activity logging
        with patch.object(payment_service, 'send_payment_receipt_email', new_callable=AsyncMock) as mock_email:
            with patch('services.activity.ActivityService') as mock_activity_service:
                mock_activity_instance = AsyncMock()
                mock_activity_service.return_value = mock_activity_instance
                
                # Execute the payment success handler
                result = asyncio.run(
                    payment_service._handle_payment_intent_succeeded(payment_data, event_id)
                )
                
                # Property: Transaction status should be updated
                assert mock_db.execute.called, "Database execute should be called to update transaction"
                assert mock_db.commit.called, "Database commit should be called after update"
                
                # Property: Follow-up actions should be triggered for existing transactions
                if mock_result.rowcount > 0:
                    mock_email.assert_called_once_with(sample_transaction), "Payment receipt email should be sent"
                    mock_activity_instance.log_activity.assert_called_once(), "Activity should be logged"
                    
                    # Verify activity log contains correct information
                    activity_call = mock_activity_instance.log_activity.call_args
                    assert activity_call[1]["action_type"] == "payment_success", "Activity type should be payment_success"
                    assert payment_intent_id in str(activity_call[1]["metadata"]), "Payment intent ID should be in metadata"

    @given(
        payment_intent_id=st.text(min_size=10, max_size=50, alphabet=st.characters(whitelist_categories=('Ll', 'Lu', 'Nd', 'Pc'))),
        failure_reason=st.text(min_size=5, max_size=100, alphabet=st.characters(whitelist_categories=('Ll', 'Lu', 'Nd', 'Pc', 'Zs'))),
        failure_code=st.sampled_from(['card_declined', 'insufficient_funds', 'expired_card', 'processing_error', 'authentication_required']),
        event_id=st.text(min_size=10, max_size=50, alphabet=st.characters(whitelist_categories=('Ll', 'Lu', 'Nd', 'Pc')))
    )
    @DEFAULT_SETTINGS
    def test_payment_intent_failed_processing_property(
        self, payment_service, mock_db, sample_transaction, payment_intent_id, failure_reason, failure_code, event_id
    ):
        """
        Property: For any Stripe payment_intent.payment_failed event, the corresponding transaction status
        should be updated to 'failed' with failure details and appropriate follow-up actions should be triggered.
        
        **Feature: platform-modernization, Property 17: Payment event processing**
        **Validates: Requirements 6.3**
        """
        # Setup the payment intent failure data
        payment_data = {
            "id": payment_intent_id,
            "status": "failed",
            "last_payment_error": {
                "message": failure_reason,
                "code": failure_code
            }
        }
        
        # Mock database query result for finding the transaction
        mock_result = MagicMock()
        mock_result.rowcount = 1  # Simulate successful update
        
        # Mock transaction retrieval for follow-up processing
        mock_transaction_result = MagicMock()
        sample_transaction.stripe_payment_intent_id = payment_intent_id
        sample_transaction.status = "failed"
        sample_transaction.failure_reason = failure_reason
        mock_transaction_result.scalar_one_or_none.return_value = sample_transaction
        
        # Configure mock to return different results for update vs select queries
        mock_db.execute.side_effect = [mock_result, mock_transaction_result]
        
        # Mock the email sending and activity logging
        with patch.object(payment_service, 'send_payment_failed_email', new_callable=AsyncMock) as mock_email:
            with patch('services.activity.ActivityService') as mock_activity_service:
                mock_activity_instance = AsyncMock()
                mock_activity_service.return_value = mock_activity_instance
                
                # Execute the payment failure handler
                result = asyncio.run(
                    payment_service._handle_payment_intent_failed(payment_data, event_id)
                )
                
                # Property: Transaction status should be updated with failure details
                assert mock_db.execute.called, "Database execute should be called to update transaction"
                assert mock_db.commit.called, "Database commit should be called after update"
                
                # Property: Follow-up actions should be triggered for existing transactions
                if mock_result.rowcount > 0:
                    mock_email.assert_called_once_with(sample_transaction, failure_reason), "Payment failure email should be sent"
                    mock_activity_instance.log_activity.assert_called_once(), "Activity should be logged"
                    
                    # Verify activity log contains correct failure information
                    activity_call = mock_activity_instance.log_activity.call_args
                    assert activity_call[1]["action_type"] == "payment_failure", "Activity type should be payment_failure"
                    assert failure_reason in activity_call[1]["description"], "Failure reason should be in description"
                    assert payment_intent_id in str(activity_call[1]["metadata"]), "Payment intent ID should be in metadata"
                    assert failure_code in str(activity_call[1]["metadata"]), "Failure code should be in metadata"

    @given(
        payment_intent_id=st.text(min_size=10, max_size=50, alphabet=st.characters(whitelist_categories=('Ll', 'Lu', 'Nd', 'Pc'))),
        event_type=st.sampled_from(['payment_intent.succeeded', 'payment_intent.payment_failed']),
        event_id=st.text(min_size=10, max_size=50, alphabet=st.characters(whitelist_categories=('Ll', 'Lu', 'Nd', 'Pc')))
    )
    @DEFAULT_SETTINGS
    def test_payment_event_nonexistent_transaction_property(
        self, payment_service, mock_db, payment_intent_id, event_type, event_id
    ):
        """
        Property: For any Stripe payment event referencing a non-existent transaction,
        the system should handle it gracefully without errors and log appropriate warnings.
        
        **Feature: platform-modernization, Property 17: Payment event processing**
        **Validates: Requirements 6.2, 6.3**
        """
        # Setup payment data based on event type
        if event_type == 'payment_intent.succeeded':
            payment_data = {
                "id": payment_intent_id,
                "status": "succeeded",
                "amount_received": 5000
            }
        else:  # payment_intent.payment_failed
            payment_data = {
                "id": payment_intent_id,
                "status": "failed",
                "last_payment_error": {
                    "message": "Card was declined",
                    "code": "card_declined"
                }
            }
        
        # Mock database query result for non-existent transaction
        mock_result = MagicMock()
        mock_result.rowcount = 0  # Simulate no transaction found
        mock_db.execute.return_value = mock_result
        
        # Mock logging to capture warnings
        with patch('logging.getLogger') as mock_logger:
            mock_logger_instance = MagicMock()
            mock_logger.return_value = mock_logger_instance
            
            # Execute the appropriate handler based on event type
            if event_type == 'payment_intent.succeeded':
                result = asyncio.run(
                    payment_service._handle_payment_intent_succeeded(payment_data, event_id)
                )
            else:
                result = asyncio.run(
                    payment_service._handle_payment_intent_failed(payment_data, event_id)
                )
            
            # Property: System should handle non-existent transactions gracefully
            assert mock_db.execute.called, "Database execute should be called to attempt update"
            
            # Property: Warning should be logged for non-existent transactions
            mock_logger_instance.warning.assert_called_once(), "Warning should be logged for non-existent transaction"
            warning_call = mock_logger_instance.warning.call_args[0][0]
            assert payment_intent_id in warning_call, "Warning should contain the payment intent ID"
            assert "No transaction found" in warning_call, "Warning should indicate no transaction was found"
            
            # Property: Commit should NOT be called when no transaction is found (early return)
            assert not mock_db.commit.called, "Database commit should NOT be called when no transaction is found"

    @given(
        payment_intent_id=st.text(min_size=10, max_size=50, alphabet=st.characters(whitelist_categories=('Ll', 'Lu', 'Nd', 'Pc'))),
        event_type=st.sampled_from(['payment_intent.succeeded', 'payment_intent.payment_failed']),
        event_id=st.text(min_size=10, max_size=50, alphabet=st.characters(whitelist_categories=('Ll', 'Lu', 'Nd', 'Pc')))
    )
    @DEFAULT_SETTINGS
    def test_payment_event_database_error_handling_property(
        self, payment_service, mock_db, payment_intent_id, event_type, event_id
    ):
        """
        Property: For any Stripe payment event where database operations fail,
        the system should propagate the error appropriately for retry mechanisms.
        
        **Feature: platform-modernization, Property 17: Payment event processing**
        **Validates: Requirements 6.2, 6.3**
        """
        # Setup payment data based on event type
        if event_type == 'payment_intent.succeeded':
            payment_data = {
                "id": payment_intent_id,
                "status": "succeeded",
                "amount_received": 5000
            }
        else:  # payment_intent.payment_failed
            payment_data = {
                "id": payment_intent_id,
                "status": "failed",
                "last_payment_error": {
                    "message": "Card was declined",
                    "code": "card_declined"
                }
            }
        
        # Mock database to raise an exception
        mock_db.execute.side_effect = Exception("Database connection error")
        
        # Property: Database errors should be propagated (not silently caught)
        with pytest.raises(Exception) as exc_info:
            if event_type == 'payment_intent.succeeded':
                asyncio.run(
                    payment_service._handle_payment_intent_succeeded(payment_data, event_id)
                )
            else:
                asyncio.run(
                    payment_service._handle_payment_intent_failed(payment_data, event_id)
                )
        
        # Property: The original database error should be preserved
        assert "Database connection error" in str(exc_info.value), "Original database error should be preserved"
        assert mock_db.execute.called, "Database execute should have been attempted"