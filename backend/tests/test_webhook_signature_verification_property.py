"""
Property-based test for webhook signature verification.

This test validates Property 16: Webhook signature verification
Requirements: 6.1

**Feature: platform-modernization, Property 16: Webhook signature verification**
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

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')

# Global settings for all property tests to handle async operations
DEFAULT_SETTINGS = settings(
    max_examples=100,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
    deadline=None  # Disable deadline for async operations with mocking
)


class TestWebhookSignatureVerificationProperty:
    """Property-based tests for webhook signature verification"""

    @pytest.fixture
    def mock_stripe(self):
        """Mock Stripe module"""
        stripe_mock = MagicMock()
        stripe_mock.Webhook = MagicMock()
        stripe_mock.SignatureVerificationError = Exception
        return stripe_mock

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

    def generate_invalid_signature(self, payload: bytes, secret: str) -> str:
        """Generate an invalid Stripe webhook signature"""
        timestamp = int(time.time())
        # Use wrong secret to generate invalid signature
        wrong_secret = secret + "_wrong"
        return self.generate_stripe_signature(payload, wrong_secret, timestamp)

    @given(
        event_type=st.sampled_from([
            'payment_intent.succeeded',
            'payment_intent.payment_failed', 
            'charge.succeeded',
            'payment_method.attached',
            'customer.updated'
        ]),
        event_id=st.text(min_size=10, max_size=50, alphabet=st.characters(whitelist_categories=('Ll', 'Lu', 'Nd', 'Pc'))),
        payload_data=st.dictionaries(
            st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Ll', 'Lu'))),
            st.one_of(st.text(min_size=1, max_size=50), st.integers(min_value=1, max_value=10000)),
            min_size=1,
            max_size=5
        )
    )
    @DEFAULT_SETTINGS
    def test_webhook_signature_verification_property(
        self, mock_stripe, webhook_secret, event_type, event_id, payload_data
    ):
        """
        Property: For any incoming Stripe webhook, webhooks with invalid signatures should be rejected,
        and valid webhooks should be processed correctly.
        
        **Feature: platform-modernization, Property 16: Webhook signature verification**
        **Validates: Requirements 6.1**
        """
        from fastapi import HTTPException, Request
        from fastapi.testclient import TestClient
        from unittest.mock import AsyncMock
        
        # Create a valid webhook payload
        webhook_payload = {
            "id": event_id,
            "type": event_type,
            "data": {
                "object": payload_data
            },
            "created": int(time.time())
        }
        
        payload_bytes = json.dumps(webhook_payload).encode('utf-8')
        
        # Test 1: Valid signature should be accepted
        valid_signature = self.generate_stripe_signature(payload_bytes, webhook_secret)
        
        with patch('stripe.Webhook.construct_event') as mock_construct:
            mock_construct.return_value = webhook_payload
            
            # Mock the request and dependencies
            mock_request = MagicMock()
            mock_request.body = AsyncMock(return_value=payload_bytes)
            mock_request.headers = {'stripe-signature': valid_signature}
            
            mock_db = AsyncMock()
            mock_background_tasks = MagicMock()
            
            # Import and test the webhook endpoint
            with patch('core.config.settings') as mock_settings:
                mock_settings.STRIPE_WEBHOOK_SECRET = webhook_secret
                
                from routes.payment import stripe_webhook
                
                # Property: Valid signature should not raise an exception
                try:
                    result = asyncio.run(stripe_webhook(
                        request=mock_request,
                        background_tasks=mock_background_tasks,
                        db=mock_db
                    ))
                    
                    # Property: Valid webhook should return success status
                    assert result["status"] == "success", "Valid webhook should return success status"
                    assert "event_id" in result, "Valid webhook should return event ID"
                    
                    # Property: construct_event should be called with correct parameters
                    mock_construct.assert_called_once_with(
                        payload_bytes, valid_signature, webhook_secret
                    )
                    
                except Exception as e:
                    pytest.fail(f"Valid webhook signature should not raise exception: {str(e)}")
        
        # Test 2: Invalid signature should be rejected
        invalid_signature = self.generate_invalid_signature(payload_bytes, webhook_secret)
        
        with patch('stripe.Webhook.construct_event') as mock_construct:
            # Mock Stripe to raise SignatureVerificationError for invalid signature
            import stripe
            mock_construct.side_effect = stripe.SignatureVerificationError("Invalid signature", "sig_header")
            
            mock_request = MagicMock()
            mock_request.body = AsyncMock(return_value=payload_bytes)
            mock_request.headers = {'stripe-signature': invalid_signature}
            
            mock_db = AsyncMock()
            mock_background_tasks = MagicMock()
            
            with patch('core.config.settings') as mock_settings:
                mock_settings.STRIPE_WEBHOOK_SECRET = webhook_secret
                
                from routes.payment import stripe_webhook
                
                # Property: Invalid signature should raise HTTPException
                with pytest.raises(HTTPException) as exc_info:
                    asyncio.run(stripe_webhook(
                        request=mock_request,
                        background_tasks=mock_background_tasks,
                        db=mock_db
                    ))
                
                # Property: Exception should have correct status code and message
                assert exc_info.value.status_code == 400, "Invalid signature should return 400 status code"
                assert "Invalid webhook signature" in str(exc_info.value.detail), "Error message should indicate invalid signature"

    @given(
        payload_content=st.one_of(
            st.just(b""),  # Empty payload
            st.text(min_size=1, max_size=100).map(lambda x: x.encode('utf-8')),  # Non-JSON payload
            st.just(b"invalid json content"),  # Invalid JSON
        )
    )
    @DEFAULT_SETTINGS
    def test_webhook_invalid_payload_handling_property(
        self, mock_stripe, webhook_secret, payload_content
    ):
        """
        Property: For any invalid webhook payload (empty, non-JSON, malformed),
        the webhook handler should reject it with appropriate error messages.
        
        **Feature: platform-modernization, Property 16: Webhook signature verification**
        **Validates: Requirements 6.1**
        """
        from fastapi import HTTPException
        from unittest.mock import AsyncMock
        
        # Generate signature for the payload (even if invalid)
        signature = self.generate_stripe_signature(payload_content, webhook_secret) if payload_content else "t=123,v1=invalid"
        
        with patch('stripe.Webhook.construct_event') as mock_construct:
            # Mock Stripe to raise ValueError for invalid payload
            mock_construct.side_effect = ValueError("Invalid payload format")
            
            mock_request = MagicMock()
            mock_request.body = AsyncMock(return_value=payload_content)
            mock_request.headers = {'stripe-signature': signature} if signature else {}
            
            mock_db = AsyncMock()
            mock_background_tasks = MagicMock()
            
            with patch('core.config.settings') as mock_settings:
                mock_settings.STRIPE_WEBHOOK_SECRET = webhook_secret
                
                from routes.payment import stripe_webhook
                
                # Property: Invalid payload should raise HTTPException
                with pytest.raises(HTTPException) as exc_info:
                    asyncio.run(stripe_webhook(
                        request=mock_request,
                        background_tasks=mock_background_tasks,
                        db=mock_db
                    ))
                
                # Property: Exception should have appropriate status code
                expected_status = 400
                assert exc_info.value.status_code == expected_status, f"Invalid payload should return {expected_status} status code"

    @given(
        missing_webhook_secret=st.booleans(),
        missing_signature_header=st.booleans()
    )
    @DEFAULT_SETTINGS
    def test_webhook_missing_requirements_property(
        self, mock_stripe, webhook_secret, missing_webhook_secret, missing_signature_header
    ):
        """
        Property: For any webhook request missing required components (signature header or webhook secret),
        the handler should reject it with appropriate error messages.
        
        **Feature: platform-modernization, Property 16: Webhook signature verification**
        **Validates: Requirements 6.1**
        """
        from fastapi import HTTPException
        from unittest.mock import AsyncMock
        
        # Skip test case where both requirements are present (should succeed)
        if not missing_webhook_secret and not missing_signature_header:
            return
        
        payload = b'{"id": "evt_test", "type": "payment_intent.succeeded"}'
        signature = self.generate_stripe_signature(payload, webhook_secret) if not missing_signature_header else None
        
        mock_request = MagicMock()
        mock_request.body = AsyncMock(return_value=payload)
        mock_request.headers = {'stripe-signature': signature} if signature else {}
        
        mock_db = AsyncMock()
        mock_background_tasks = MagicMock()
        
        with patch('core.config.settings') as mock_settings:
            # Create a mock settings object with the webhook secret attribute
            mock_settings.STRIPE_WEBHOOK_SECRET = None if missing_webhook_secret else webhook_secret
            
            # Also patch the settings import in the payment route
            with patch('routes.payment.settings') as mock_route_settings:
                mock_route_settings.STRIPE_WEBHOOK_SECRET = None if missing_webhook_secret else webhook_secret
                
                from routes.payment import stripe_webhook
            
                # Property: Missing requirements should raise HTTPException
                with pytest.raises(HTTPException) as exc_info:
                    asyncio.run(stripe_webhook(
                        request=mock_request,
                        background_tasks=mock_background_tasks,
                        db=mock_db
                    ))
            
                # Property: Exception should have appropriate status code and message
                # The webhook endpoint checks webhook secret first, then signature header
                if missing_webhook_secret:
                    # Missing webhook secret is checked first and returns 500
                    assert exc_info.value.status_code == 500, "Missing webhook secret should return 500 status code"
                    assert "webhook secret not configured" in str(exc_info.value.detail).lower(), "Error should indicate missing webhook secret"
                elif missing_signature_header:
                    # Missing signature header (when webhook secret is present) returns 400
                    assert exc_info.value.status_code == 400, "Missing signature header should return 400 status code"
                    assert "signature header" in str(exc_info.value.detail).lower(), "Error should indicate missing signature header"