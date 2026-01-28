"""
Tests for payments API endpoints
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4
from decimal import Decimal
from unittest.mock import patch, MagicMock

from models.payments import PaymentMethod, PaymentIntent, Transaction
from models.user import User


class TestPaymentsAPI:
    """Test payments API endpoints."""
    
    @pytest.mark.asyncio
    async def test_get_payment_methods_success(self, async_client: AsyncClient, auth_headers: dict, test_payment_method: PaymentMethod):
        """Test getting user's payment methods."""
        response = await async_client.get("/payments/methods", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) >= 1
        
        method_data = data["data"][0]
        assert method_data["id"] == str(test_payment_method.id)
        assert method_data["type"] == test_payment_method.type
        assert method_data["last_four"] == test_payment_method.last_four
        assert method_data["is_default"] == test_payment_method.is_default
    
    @pytest.mark.asyncio
    async def test_get_payment_methods_empty(self, async_client: AsyncClient, auth_headers: dict):
        """Test getting payment methods when user has none."""
        response = await async_client.get("/payments/methods", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"] == []
    
    @pytest.mark.asyncio
    async def test_get_payment_methods_unauthorized(self, async_client: AsyncClient):
        """Test getting payment methods without authentication."""
        response = await async_client.get("/payments/methods")
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_create_payment_method_success(self, async_client: AsyncClient, auth_headers: dict, mock_stripe):
        """Test creating payment method with Stripe."""
        payment_data = {
            "stripe_payment_method_id": "pm_test_123",
            "is_default": True
        }
        
        response = await async_client.post("/payments/methods", json=payment_data, headers=auth_headers)
        
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["type"] == "card"
        assert data["data"]["last_four"] == "4242"
        assert data["data"]["brand"] == "visa"
        assert data["data"]["is_default"] is True
        
        # Verify Stripe API was called
        mock_stripe["payment_method"].retrieve.assert_called_once_with("pm_test_123")
    
    @pytest.mark.asyncio
    async def test_create_payment_method_legacy_token(self, async_client: AsyncClient, auth_headers: dict, mock_stripe):
        """Test creating payment method with legacy Stripe token."""
        payment_data = {
            "stripe_token": "tok_test_123",
            "is_default": False
        }
        
        response = await async_client.post("/payments/methods", json=payment_data, headers=auth_headers)
        
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["type"] == "card"
        assert data["data"]["is_default"] is False
        
        # Verify Stripe API was called
        mock_stripe["token"].retrieve.assert_called_once_with("tok_test_123")
    
    @pytest.mark.asyncio
    async def test_create_payment_method_invalid_stripe_id(self, async_client: AsyncClient, auth_headers: dict, mock_stripe):
        """Test creating payment method with invalid Stripe ID."""
        # Mock Stripe to raise an error
        mock_stripe["payment_method"].retrieve.side_effect = Exception("Invalid payment method")
        
        payment_data = {
            "stripe_payment_method_id": "pm_invalid",
            "is_default": True
        }
        
        response = await async_client.post("/payments/methods", json=payment_data, headers=auth_headers)
        
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert "invalid" in data["message"].lower()
    
    @pytest.mark.asyncio
    async def test_create_payment_method_missing_data(self, async_client: AsyncClient, auth_headers: dict):
        """Test creating payment method with missing data."""
        payment_data = {
            "is_default": True
            # Missing stripe_payment_method_id or stripe_token
        }
        
        response = await async_client.post("/payments/methods", json=payment_data, headers=auth_headers)
        
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
    
    @pytest.mark.asyncio
    async def test_delete_payment_method_success(self, async_client: AsyncClient, auth_headers: dict, test_payment_method: PaymentMethod):
        """Test deleting payment method."""
        response = await async_client.delete(f"/payments/methods/{test_payment_method.id}", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "Payment method deleted successfully"
    
    @pytest.mark.asyncio
    async def test_delete_payment_method_not_found(self, async_client: AsyncClient, auth_headers: dict):
        """Test deleting nonexistent payment method."""
        fake_id = uuid4()
        response = await async_client.delete(f"/payments/methods/{fake_id}", headers=auth_headers)
        
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert "not found" in data["message"].lower()
    
    @pytest.mark.asyncio
    async def test_delete_other_user_payment_method(self, async_client: AsyncClient, auth_headers: dict, db_session: AsyncSession):
        """Test deleting another user's payment method."""
        # Create another user and their payment method
        other_user = User(
            id=uuid4(),
            email="other@example.com",
            firstname="Other",
            lastname="User",
            hashed_password="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
            role="customer",
            verified=True,
            is_active=True
        )
        db_session.add(other_user)
        
        other_payment_method = PaymentMethod(
            id=uuid4(),
            user_id=other_user.id,
            type="card",
            provider="stripe",
            stripe_payment_method_id="pm_other_123",
            last_four="1234",
            brand="mastercard",
            is_default=True,
            is_active=True
        )
        db_session.add(other_payment_method)
        await db_session.commit()
        
        response = await async_client.delete(f"/payments/methods/{other_payment_method.id}", headers=auth_headers)
        
        assert response.status_code == 404  # Should not find method (security)


class TestPaymentIntentsAPI:
    """Test payment intents API endpoints."""
    
    @pytest.mark.asyncio
    async def test_create_payment_intent_success(self, async_client: AsyncClient, auth_headers: dict, test_payment_method: PaymentMethod, mock_stripe):
        """Test creating payment intent."""
        intent_data = {
            "amount": "100.00",
            "currency": "usd",
            "payment_method_id": str(test_payment_method.id),
            "description": "Test payment"
        }
        
        response = await async_client.post("/payments/intents", json=intent_data, headers=auth_headers)
        
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["amount"] == 10000  # Stripe uses cents
        assert data["data"]["currency"] == "usd"
        assert data["data"]["status"] == "requires_confirmation"
        
        # Verify Stripe API was called
        mock_stripe["payment_intent"].create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_payment_intent_invalid_amount(self, async_client: AsyncClient, auth_headers: dict, test_payment_method: PaymentMethod):
        """Test creating payment intent with invalid amount."""
        intent_data = {
            "amount": "-10.00",  # Negative amount
            "currency": "usd",
            "payment_method_id": str(test_payment_method.id),
            "description": "Test payment"
        }
        
        response = await async_client.post("/payments/intents", json=intent_data, headers=auth_headers)
        
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_create_payment_intent_invalid_payment_method(self, async_client: AsyncClient, auth_headers: dict):
        """Test creating payment intent with invalid payment method."""
        intent_data = {
            "amount": "100.00",
            "currency": "usd",
            "payment_method_id": str(uuid4()),  # Invalid ID
            "description": "Test payment"
        }
        
        response = await async_client.post("/payments/intents", json=intent_data, headers=auth_headers)
        
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert "payment method not found" in data["message"].lower()
    
    @pytest.mark.asyncio
    async def test_confirm_payment_intent_success(self, async_client: AsyncClient, auth_headers: dict, db_session: AsyncSession, test_user: User, mock_stripe):
        """Test confirming payment intent."""
        # Create payment intent
        payment_intent = PaymentIntent(
            id=uuid4(),
            user_id=test_user.id,
            stripe_payment_intent_id="pi_test_123",
            amount=Decimal("100.00"),
            currency="usd",
            status="requires_confirmation"
        )
        db_session.add(payment_intent)
        await db_session.commit()
        
        # Mock successful confirmation
        mock_stripe["payment_intent"].confirm = MagicMock(return_value=MagicMock(
            id="pi_test_123",
            status="succeeded"
        ))
        
        response = await async_client.post(f"/payments/intents/{payment_intent.id}/confirm", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["status"] == "succeeded"
    
    @pytest.mark.asyncio
    async def test_confirm_payment_intent_failed(self, async_client: AsyncClient, auth_headers: dict, db_session: AsyncSession, test_user: User, mock_stripe):
        """Test confirming payment intent that fails."""
        # Create payment intent
        payment_intent = PaymentIntent(
            id=uuid4(),
            user_id=test_user.id,
            stripe_payment_intent_id="pi_test_123",
            amount=Decimal("100.00"),
            currency="usd",
            status="requires_confirmation"
        )
        db_session.add(payment_intent)
        await db_session.commit()
        
        # Mock failed confirmation
        mock_stripe["payment_intent"].confirm = MagicMock(return_value=MagicMock(
            id="pi_test_123",
            status="requires_payment_method"
        ))
        
        response = await async_client.post(f"/payments/intents/{payment_intent.id}/confirm", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["status"] == "requires_payment_method"


class TestTransactionsAPI:
    """Test transactions API endpoints."""
    
    @pytest.mark.asyncio
    async def test_get_transactions_success(self, async_client: AsyncClient, auth_headers: dict, db_session: AsyncSession, test_user: User):
        """Test getting user's transactions."""
        # Create test transaction
        transaction = Transaction(
            id=uuid4(),
            user_id=test_user.id,
            stripe_payment_intent_id="pi_test_123",
            amount=Decimal("100.00"),
            currency="usd",
            status="succeeded",
            transaction_type="payment"
        )
        db_session.add(transaction)
        await db_session.commit()
        
        response = await async_client.get("/payments/transactions", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) >= 1
        
        transaction_data = data["data"][0]
        assert transaction_data["id"] == str(transaction.id)
        assert transaction_data["amount"] == str(transaction.amount)
        assert transaction_data["status"] == transaction.status
    
    @pytest.mark.asyncio
    async def test_get_transactions_with_filters(self, async_client: AsyncClient, auth_headers: dict, db_session: AsyncSession, test_user: User):
        """Test getting transactions with filters."""
        # Create transactions with different statuses
        transaction1 = Transaction(
            id=uuid4(),
            user_id=test_user.id,
            stripe_payment_intent_id="pi_test_123",
            amount=Decimal("100.00"),
            currency="usd",
            status="succeeded",
            transaction_type="payment"
        )
        transaction2 = Transaction(
            id=uuid4(),
            user_id=test_user.id,
            stripe_payment_intent_id="pi_test_456",
            amount=Decimal("50.00"),
            currency="usd",
            status="failed",
            transaction_type="payment"
        )
        db_session.add_all([transaction1, transaction2])
        await db_session.commit()
        
        response = await async_client.get("/payments/transactions?status=succeeded", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        
        # Should only return succeeded transactions
        for transaction_data in data["data"]:
            assert transaction_data["status"] == "succeeded"
    
    @pytest.mark.asyncio
    async def test_get_transactions_pagination(self, async_client: AsyncClient, auth_headers: dict):
        """Test transactions pagination."""
        response = await async_client.get("/payments/transactions?page=1&limit=10", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "pagination" in data
        assert data["pagination"]["page"] == 1
        assert data["pagination"]["limit"] == 10


class TestPaymentProcessing:
    """Test payment processing endpoints."""
    
    @pytest.mark.asyncio
    async def test_process_payment_success(self, async_client: AsyncClient, auth_headers: dict, test_payment_method: PaymentMethod, mock_stripe):
        """Test processing payment."""
        payment_data = {
            "amount": "100.00",
            "currency": "usd",
            "payment_method_id": str(test_payment_method.id),
            "description": "Test payment",
            "idempotency_key": str(uuid4())
        }
        
        # Mock successful payment
        mock_stripe["payment_intent"].create.return_value = MagicMock(
            id="pi_test_123",
            status="succeeded",
            amount=10000,
            currency="usd"
        )
        
        response = await async_client.post("/payments/process", json=payment_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["status"] == "succeeded"
    
    @pytest.mark.asyncio
    async def test_process_payment_failed(self, async_client: AsyncClient, auth_headers: dict, test_payment_method: PaymentMethod, mock_stripe):
        """Test processing failed payment."""
        payment_data = {
            "amount": "100.00",
            "currency": "usd",
            "payment_method_id": str(test_payment_method.id),
            "description": "Test payment",
            "idempotency_key": str(uuid4())
        }
        
        # Mock failed payment
        mock_stripe["payment_intent"].create.return_value = MagicMock(
            id="pi_test_123",
            status="requires_payment_method",
            amount=10000,
            currency="usd"
        )
        
        response = await async_client.post("/payments/process", json=payment_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["status"] == "requires_payment_method"
    
    @pytest.mark.asyncio
    async def test_process_payment_idempotency(self, async_client: AsyncClient, auth_headers: dict, test_payment_method: PaymentMethod, mock_stripe):
        """Test payment idempotency."""
        idempotency_key = str(uuid4())
        payment_data = {
            "amount": "100.00",
            "currency": "usd",
            "payment_method_id": str(test_payment_method.id),
            "description": "Test payment",
            "idempotency_key": idempotency_key
        }
        
        # Mock successful payment
        mock_stripe["payment_intent"].create.return_value = MagicMock(
            id="pi_test_123",
            status="succeeded",
            amount=10000,
            currency="usd"
        )
        
        # First request
        response1 = await async_client.post("/payments/process", json=payment_data, headers=auth_headers)
        assert response1.status_code == 200
        
        # Second request with same idempotency key
        response2 = await async_client.post("/payments/process", json=payment_data, headers=auth_headers)
        assert response2.status_code == 200
        
        # Should return same result
        assert response1.json()["data"]["id"] == response2.json()["data"]["id"]


class TestRefundsAPI:
    """Test refunds API endpoints."""
    
    @pytest.mark.asyncio
    async def test_create_refund_success(self, async_client: AsyncClient, auth_headers: dict, db_session: AsyncSession, test_user: User, mock_stripe):
        """Test creating refund."""
        # Create transaction to refund
        transaction = Transaction(
            id=uuid4(),
            user_id=test_user.id,
            stripe_payment_intent_id="pi_test_123",
            amount=Decimal("100.00"),
            currency="usd",
            status="succeeded",
            transaction_type="payment"
        )
        db_session.add(transaction)
        await db_session.commit()
        
        refund_data = {
            "amount": "50.00",
            "reason": "requested_by_customer"
        }
        
        # Mock successful refund
        with patch('stripe.Refund.create') as mock_refund:
            mock_refund.return_value = MagicMock(
                id="re_test_123",
                status="succeeded",
                amount=5000
            )
            
            response = await async_client.post(f"/payments/refunds/{transaction.id}", json=refund_data, headers=auth_headers)
        
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["amount"] == "50.00"
        assert data["data"]["status"] == "succeeded"
    
    @pytest.mark.asyncio
    async def test_create_refund_invalid_transaction(self, async_client: AsyncClient, auth_headers: dict):
        """Test creating refund for invalid transaction."""
        refund_data = {
            "amount": "50.00",
            "reason": "requested_by_customer"
        }
        
        response = await async_client.post(f"/payments/refunds/{uuid4()}", json=refund_data, headers=auth_headers)
        
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert "transaction not found" in data["message"].lower()
    
    @pytest.mark.asyncio
    async def test_create_refund_excessive_amount(self, async_client: AsyncClient, auth_headers: dict, db_session: AsyncSession, test_user: User):
        """Test creating refund with amount exceeding transaction."""
        # Create transaction
        transaction = Transaction(
            id=uuid4(),
            user_id=test_user.id,
            stripe_payment_intent_id="pi_test_123",
            amount=Decimal("100.00"),
            currency="usd",
            status="succeeded",
            transaction_type="payment"
        )
        db_session.add(transaction)
        await db_session.commit()
        
        refund_data = {
            "amount": "150.00",  # More than transaction amount
            "reason": "requested_by_customer"
        }
        
        response = await async_client.post(f"/payments/refunds/{transaction.id}", json=refund_data, headers=auth_headers)
        
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert "exceeds" in data["message"].lower()


class TestPaymentValidation:
    """Test payment validation and edge cases."""
    
    @pytest.mark.asyncio
    async def test_create_payment_method_invalid_data(self, async_client: AsyncClient, auth_headers: dict):
        """Test creating payment method with invalid data."""
        payment_data = {
            "invalid_field": "invalid_value"
        }
        
        response = await async_client.post("/payments/methods", json=payment_data, headers=auth_headers)
        
        assert response.status_code == 400
    
    @pytest.mark.asyncio
    async def test_process_payment_zero_amount(self, async_client: AsyncClient, auth_headers: dict, test_payment_method: PaymentMethod):
        """Test processing payment with zero amount."""
        payment_data = {
            "amount": "0.00",
            "currency": "usd",
            "payment_method_id": str(test_payment_method.id),
            "description": "Test payment"
        }
        
        response = await async_client.post("/payments/process", json=payment_data, headers=auth_headers)
        
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_process_payment_invalid_currency(self, async_client: AsyncClient, auth_headers: dict, test_payment_method: PaymentMethod):
        """Test processing payment with invalid currency."""
        payment_data = {
            "amount": "100.00",
            "currency": "invalid",
            "payment_method_id": str(test_payment_method.id),
            "description": "Test payment"
        }
        
        response = await async_client.post("/payments/process", json=payment_data, headers=auth_headers)
        
        assert response.status_code == 422