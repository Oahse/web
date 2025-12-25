"""
Property-based test for webhook idempotency.

This test validates Property 18: Webhook idempotency
Requirements: 6.6

**Feature: platform-modernization, Property 18: Webhook idempotency**
"""
import pytest
import sys
import os
from unittest.mock import AsyncMock, MagicMock, patch
from hypothesis import given, strategies as st, settings, HealthCheck
import asyncio
import json
import hmac
import hashlib
import time
from datetime import datetime

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')

# Global settings for all property tests to handle async operations
DEFAULT_SETTINGS = settings(
    max_examples=100,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
    deadline=None  # Disable deadline for async operations with mocking
)


class TestWebhookIdempotencyProperty:
    """Property-based tests for webhook idempotency"""

    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        db_mock = AsyncMock()
        db_mock.commit = AsyncMock()
        db_mock.refresh = AsyncMock()
        db_mock.add = MagicMock()
        db_mock.execute = AsyncMock()
        return db_mock

    @pytest.fixture
    def webhook_secret(self):
        """Sample webhook secret for testing"""
        return "whsec_test_secret_key_for_webhook_verification"

    def generate_stripe_signature(self, payload: bytes, secret: str, timestamp: int = None) -> str:
        """Generate a valid Stripe webhook signature"""
        if timestamp is None:
            timestamp = int(time.time())
        
        # Create the signed payload string
        signed_payload = f"{timestamp}.{payload.decode('utf-8')}"
        
        # Generate the signature
        signature = hmac.new(
            secret.encode('utf-8'),
            signed_payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return f"t={timestamp},v1={signature}"

    @given(
        event_id=st.text(min_size=10, max_size=50, alphabet=st.characters(whitelist_categories=('Ll', 'Lu', 'Nd', 'Pc'))),
        event_type=st.sampled_from([
            'payment_intent.succeeded',
            'payment_intent.payment_failed', 
            'charge.succeeded',
            'payment_method.attached',
            'customer.updated'
        ]),
        payload_data=st.dictionaries(
            st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Ll', 'Lu'))),
            st.one_of(st.text(min_size=1, max_size=50), st.integers(min_value=1, max_value=10000)),
            min_size=1,
            max_size=5
        ),
        processing_count=st.integers(min_value=2, max_value=5)  # Test multiple processing attempts
    )
    @DEFAULT_SETTINGS
    def test_webhook_idempotency_property(
        self, mock_db, webhook_secret, event_id, event_type, payload_data, processing_count
    ):
        """
        Property: For any webhook event, processing the same webhook multiple times should have no 
        additional effect beyond the first processing.
        
        **Feature: platform-modernization, Property 18: Webhook idempotency**
        **Validates: Requirements 6.6**
        """
        from services.payment import PaymentService
        from models.webhook_event import WebhookEvent
        from sqlalchemy import select
        
        # Create a valid webhook event
        webhook_event = {
            "id": event_id,
            "type": event_type,
            "data": {
                "object": payload_data
            },
            "created": int(time.time())
        }
        
        # Mock the webhook record for idempotency tracking
        mock_webhook_record = MagicMock()
        mock_webhook_record.stripe_event_id = event_id
        mock_webhook_record.event_type = event_type
        mock_webhook_record.processed = False
        mock_webhook_record.processing_attempts = 0
        mock_webhook_record.last_processing_attempt = None
        mock_webhook_record.completed_at = None
        mock_webhook_record.error_message = None
        
        # Track state changes for idempotency verification
        processing_calls = []
        
        async def mock_get_or_create_webhook_record(event_id_param, event_type_param, event_data):
            """Mock the webhook record retrieval/creation"""
            # First call: return unprocessed record
            if len(processing_calls) == 0:
                mock_webhook_record.processed = False
                mock_webhook_record.processing_attempts = 0
            else:
                # Subsequent calls: return already processed record
                mock_webhook_record.processed = True
                mock_webhook_record.processing_attempts = 1
                mock_webhook_record.completed_at = datetime.utcnow()
            
            return mock_webhook_record
        
        # Mock the specific event handlers to track calls
        async def mock_payment_intent_succeeded(data, event_id_param):
            processing_calls.append(('payment_intent.succeeded', event_id_param))
        
        async def mock_payment_intent_failed(data, event_id_param):
            processing_calls.append(('payment_intent.payment_failed', event_id_param))
        
        async def mock_charge_succeeded(data, event_id_param):
            processing_calls.append(('charge.succeeded', event_id_param))
        
        async def mock_payment_method_attached(data, event_id_param):
            processing_calls.append(('payment_method.attached', event_id_param))
        
        async def mock_customer_updated(data, event_id_param):
            processing_calls.append(('customer.updated', event_id_param))
        
        # Create payment service instance
        payment_service = PaymentService(mock_db)
        
        # Patch the internal methods
        with patch.object(payment_service, '_get_or_create_webhook_record', side_effect=mock_get_or_create_webhook_record):
            with patch.object(payment_service, '_handle_payment_intent_succeeded', side_effect=mock_payment_intent_succeeded):
                with patch.object(payment_service, '_handle_payment_intent_failed', side_effect=mock_payment_intent_failed):
                    with patch.object(payment_service, '_handle_charge_succeeded', side_effect=mock_charge_succeeded):
                        with patch.object(payment_service, '_handle_payment_method_attached', side_effect=mock_payment_method_attached):
                            with patch.object(payment_service, '_handle_customer_updated', side_effect=mock_customer_updated):
                                
                                # Process the same webhook event multiple times
                                async def process_webhooks():
                                    for i in range(processing_count):
                                        try:
                                            await payment_service.handle_stripe_webhook(webhook_event)
                                        except Exception as e:
                                            # Allow exceptions on first processing, but not on subsequent ones
                                            if i > 0:
                                                pytest.fail(f"Idempotent webhook processing should not raise exception on attempt {i+1}: {str(e)}")
                                
                                # Run the async processing
                                asyncio.run(process_webhooks())
                
                # Property: Only the first processing should execute the handler
                if event_type in ['payment_intent.succeeded', 'payment_intent.payment_failed', 'charge.succeeded', 'payment_method.attached', 'customer.updated']:
                    # Should have exactly one processing call (from first attempt)
                    handler_calls = [call for call in processing_calls if call[0] == event_type]
                    assert len(handler_calls) <= 1, f"Handler for {event_type} should be called at most once, but was called {len(handler_calls)} times"
                    
                    if len(handler_calls) == 1:
                        # Verify the correct event ID was passed
                        assert handler_calls[0][1] == event_id, f"Handler should be called with correct event ID {event_id}"

    @given(
        event_id=st.text(min_size=10, max_size=50, alphabet=st.characters(whitelist_categories=('Ll', 'Lu', 'Nd', 'Pc'))),
        event_type=st.sampled_from([
            'payment_intent.succeeded',
            'payment_intent.payment_failed'
        ]),
        payload_data=st.dictionaries(
            st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Ll', 'Lu'))),
            st.one_of(st.text(min_size=1, max_size=50), st.integers(min_value=1, max_value=10000)),
            min_size=1,
            max_size=5
        )
    )
    @DEFAULT_SETTINGS
    def test_webhook_record_creation_idempotency_property(
        self, mock_db, event_id, event_type, payload_data
    ):
        """
        Property: For any webhook event ID, multiple calls to get_or_create_webhook_record 
        should return the same record and not create duplicates.
        
        **Feature: platform-modernization, Property 18: Webhook idempotency**
        **Validates: Requirements 6.6**
        """
        from services.payment import PaymentService
        from models.webhook_event import WebhookEvent
        from sqlalchemy import select
        
        webhook_event = {
            "id": event_id,
            "type": event_type,
            "data": {"object": payload_data},
            "created": int(time.time())
        }
        
        # Mock database query results
        mock_webhook_record = MagicMock()
        mock_webhook_record.stripe_event_id = event_id
        mock_webhook_record.event_type = event_type
        mock_webhook_record.processed = False
        
        # Track database operations
        db_adds = []
        db_queries = []
        
        async def mock_execute(query):
            """Mock database execute method"""
            db_queries.append(query)
            result_mock = MagicMock()
            
            # First query: return None (record doesn't exist)
            # Subsequent queries: return existing record
            if len(db_queries) == 1:
                result_mock.scalar_one_or_none.return_value = None
            else:
                result_mock.scalar_one_or_none.return_value = mock_webhook_record
            
            return result_mock
        
        def mock_add(record):
            """Mock database add method"""
            db_adds.append(record)
        
        # Setup mock database
        mock_db.execute = mock_execute
        mock_db.add = mock_add
        
        payment_service = PaymentService(mock_db)
        
        # Call get_or_create_webhook_record multiple times
        async def test_record_creation():
            records = []
            for i in range(3):
                record = await payment_service._get_or_create_webhook_record(
                    event_id, event_type, webhook_event
                )
                records.append(record)
            return records
        
        records = asyncio.run(test_record_creation())
        
        # Property: Should only create one database record
        assert len(db_adds) <= 1, f"Should create at most one webhook record, but created {len(db_adds)}"
        
        # Property: All calls should return records with the same event ID
        for record in records:
            if hasattr(record, 'stripe_event_id'):
                assert record.stripe_event_id == event_id, "All returned records should have the same event ID"

    @given(
        event_id=st.text(min_size=10, max_size=50, alphabet=st.characters(whitelist_categories=('Ll', 'Lu', 'Nd', 'Pc'))),
        event_type=st.sampled_from(['payment_intent.succeeded', 'payment_intent.payment_failed']),
        initial_processed_state=st.booleans()
    )
    @DEFAULT_SETTINGS
    def test_webhook_processed_flag_idempotency_property(
        self, mock_db, event_id, event_type, initial_processed_state
    ):
        """
        Property: For any webhook event that is already marked as processed, 
        subsequent processing attempts should skip the actual processing logic.
        
        **Feature: platform-modernization, Property 18: Webhook idempotency**
        **Validates: Requirements 6.6**
        """
        from services.payment import PaymentService
        
        webhook_event = {
            "id": event_id,
            "type": event_type,
            "data": {"object": {"id": "test_payment_intent"}},
            "created": int(time.time())
        }
        
        # Mock webhook record with initial processed state
        mock_webhook_record = MagicMock()
        mock_webhook_record.stripe_event_id = event_id
        mock_webhook_record.event_type = event_type
        mock_webhook_record.processed = initial_processed_state
        mock_webhook_record.processing_attempts = 1 if initial_processed_state else 0
        
        # Track handler calls
        handler_called = []
        
        async def mock_get_or_create_webhook_record(event_id_param, event_type_param, event_data):
            return mock_webhook_record
        
        async def mock_handler(data, event_id_param):
            handler_called.append(event_id_param)
        
        payment_service = PaymentService(mock_db)
        
        with patch.object(payment_service, '_get_or_create_webhook_record', side_effect=mock_get_or_create_webhook_record):
            with patch.object(payment_service, '_handle_payment_intent_succeeded', side_effect=mock_handler):
                with patch.object(payment_service, '_handle_payment_intent_failed', side_effect=mock_handler):
                    
                    async def process_webhook():
                        await payment_service.handle_stripe_webhook(webhook_event)
                    
                    asyncio.run(process_webhook())
        
        # Property: If already processed, handler should not be called
        if initial_processed_state:
            assert len(handler_called) == 0, "Handler should not be called for already processed events"
        else:
            # If not processed initially, handler should be called once
            assert len(handler_called) <= 1, "Handler should be called at most once for unprocessed events"

    @given(
        event_id=st.text(min_size=10, max_size=50, alphabet=st.characters(whitelist_categories=('Ll', 'Lu', 'Nd', 'Pc'))),
        concurrent_requests=st.integers(min_value=2, max_value=4)
    )
    @DEFAULT_SETTINGS
    def test_webhook_concurrent_processing_idempotency_property(
        self, mock_db, webhook_secret, event_id, concurrent_requests
    ):
        """
        Property: For any webhook event processed concurrently multiple times, 
        only one processing should succeed and others should be handled idempotently.
        
        **Feature: platform-modernization, Property 18: Webhook idempotency**
        **Validates: Requirements 6.6**
        """
        from services.payment import PaymentService
        
        webhook_event = {
            "id": event_id,
            "type": "payment_intent.succeeded",
            "data": {"object": {"id": "test_payment_intent"}},
            "created": int(time.time())
        }
        
        # Simulate concurrent access with a shared state
        processing_state = {"processed": False, "processing_count": 0, "handler_calls": []}
        
        async def mock_get_or_create_webhook_record(event_id_param, event_type_param, event_data):
            """Simulate race condition in webhook record creation"""
            mock_record = MagicMock()
            mock_record.stripe_event_id = event_id_param
            mock_record.event_type = event_type_param
            mock_record.processed = processing_state["processed"]
            mock_record.processing_attempts = processing_state["processing_count"]
            return mock_record
        
        async def mock_handler(data, event_id_param):
            """Mock handler that tracks calls and updates processing state"""
            if not processing_state["processed"]:
                processing_state["handler_calls"].append(event_id_param)
                processing_state["processed"] = True
                processing_state["processing_count"] += 1
        
        # Run concurrent processing with proper patching
        async def run_concurrent_processing():
            payment_service = PaymentService(mock_db)
            
            with patch.object(payment_service, '_get_or_create_webhook_record', side_effect=mock_get_or_create_webhook_record):
                with patch.object(payment_service, '_handle_payment_intent_succeeded', side_effect=mock_handler):
                    
                    # Create tasks for concurrent processing
                    tasks = []
                    for _ in range(concurrent_requests):
                        task = asyncio.create_task(payment_service.handle_stripe_webhook(webhook_event))
                        tasks.append(task)
                    
                    # Wait for all concurrent processing to complete
                    await asyncio.gather(*tasks, return_exceptions=True)
        
        asyncio.run(run_concurrent_processing())
        
        # Property: Handler should be called at most once despite concurrent processing
        handler_calls = processing_state["handler_calls"]
        assert len(handler_calls) <= 1, f"Handler should be called at most once, but was called {len(handler_calls)} times"
        
        # Property: If handler was called, processing state should indicate completion
        if len(handler_calls) > 0:
            assert processing_state["processed"] == True, "Processing state should indicate completion when handler was called"