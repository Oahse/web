"""
Tests for payments service
"""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4
from decimal import Decimal
from unittest.mock import patch, MagicMock
import stripe

from services.payments import PaymentService, PaymentFailureReason
from models.payments import PaymentMethod, PaymentIntent, Transaction
from models.user import User
from models.orders import Order


class TestPaymentService:
    """Test payment service."""
    
    @pytest.mark.asyncio
    async def test_create_payment_method_with_stripe_pm(self, db_session: AsyncSession, test_user: User, mock_stripe):
        """Test creating payment method with Stripe PaymentMethod."""
        payment_service = PaymentService(db_session)
        
        payment_method = await payment_service.create_payment_method(
            user_id=test_user.id,
            stripe_payment_method_id="pm_test_123",
            is_default=True
        )
        
        assert payment_method is not None
        assert payment_method.user_id == test_user.id
        assert payment_method.stripe_payment_method_id == "pm_test_123"
        assert payment_method.type == "card"
        assert payment_method.last_four == "4242"
        assert payment_method.brand == "visa"
        assert payment_method.is_default is True
        assert payment_method.is_active is True
        
        # Verify Stripe API was called
        mock_stripe["payment_method"].retrieve.assert_called_once_with("pm_test_123")
    
    @pytest.mark.asyncio
    async def test_create_payment_method_with_stripe_token(self, db_session: AsyncSession, test_user: User, mock_stripe):
        """Test creating payment method with legacy Stripe token."""
        payment_service = PaymentService(db_session)
        
        # Mock PaymentMethod.create for token conversion
        mock_stripe["payment_method"].create.return_value = MagicMock(
            id="pm_converted_123",
            type="card",
            card=MagicMock(
                last4="4242",
                brand="visa",
                exp_month=12,
                exp_year=2025
            )
        )
        
        payment_method = await payment_service.create_payment_method(
            user_id=test_user.id,
            stripe_token="tok_test_123",
            is_default=False
        )
        
        assert payment_method is not None
        assert payment_method.user_id == test_user.id
        assert payment_method.stripe_payment_method_id == "pm_converted_123"
        assert payment_method.type == "card"
        assert payment_method.is_default is False
        
        # Verify Stripe APIs were called
        mock_stripe["token"].retrieve.assert_called_once_with("tok_test_123")
        mock_stripe["payment_method"].create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_payment_method_set_default(self, db_session: AsyncSession, test_user: User, mock_stripe):
        """Test creating payment method and setting as default."""
        # Create existing default payment method
        existing_pm = PaymentMethod(
            id=uuid4(),
            user_id=test_user.id,
            type="card",
            provider="stripe",
            stripe_payment_method_id="pm_existing_123",
            last_four="1234",
            brand="mastercard",
            is_default=True,
            is_active=True
        )
        db_session.add(existing_pm)
        await db_session.commit()
        
        payment_service = PaymentService(db_session)
        
        new_pm = await payment_service.create_payment_method(
            user_id=test_user.id,
            stripe_payment_method_id="pm_test_123",
            is_default=True
        )
        
        assert new_pm.is_default is True
        
        # Verify existing default was unset
        await db_session.refresh(existing_pm)
        assert existing_pm.is_default is False
    
    @pytest.mark.asyncio
    async def test_create_payment_method_stripe_error(self, db_session: AsyncSession, test_user: User, mock_stripe):
        """Test creating payment method with Stripe error."""
        # Mock Stripe to raise an error
        mock_stripe["payment_method"].retrieve.side_effect = stripe.error.InvalidRequestError(
            "No such payment_method", "pm_invalid"
        )
        
        payment_service = PaymentService(db_session)
        
        with pytest.raises(Exception) as exc_info:
            await payment_service.create_payment_method(
                user_id=test_user.id,
                stripe_payment_method_id="pm_invalid",
                is_default=True
            )
        
        assert "invalid" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_get_user_payment_methods(self, db_session: AsyncSession, test_user: User):
        """Test getting user's payment methods."""
        # Create payment methods
        pm1 = PaymentMethod(
            id=uuid4(),
            user_id=test_user.id,
            type="card",
            provider="stripe",
            stripe_payment_method_id="pm_test_123",
            last_four="4242",
            brand="visa",
            is_default=True,
            is_active=True
        )
        pm2 = PaymentMethod(
            id=uuid4(),
            user_id=test_user.id,
            type="card",
            provider="stripe",
            stripe_payment_method_id="pm_test_456",
            last_four="1234",
            brand="mastercard",
            is_default=False,
            is_active=True
        )
        db_session.add_all([pm1, pm2])
        await db_session.commit()
        
        payment_service = PaymentService(db_session)
        
        payment_methods = await payment_service.get_user_payment_methods(test_user.id)
        
        assert len(payment_methods) == 2
        
        # Should be ordered by default first, then by creation date
        assert payment_methods[0].is_default is True
        assert payment_methods[0].id == pm1.id
    
    @pytest.mark.asyncio
    async def test_get_user_payment_methods_empty(self, db_session: AsyncSession, test_user: User):
        """Test getting payment methods when user has none."""
        payment_service = PaymentService(db_session)
        
        payment_methods = await payment_service.get_user_payment_methods(test_user.id)
        
        assert payment_methods == []
    
    @pytest.mark.asyncio
    async def test_delete_payment_method(self, db_session: AsyncSession, test_payment_method: PaymentMethod):
        """Test deleting payment method."""
        payment_service = PaymentService(db_session)
        
        result = await payment_service.delete_payment_method(
            test_payment_method.id,
            test_payment_method.user_id
        )
        
        assert result is True
        
        # Verify payment method is deleted
        deleted_pm = await payment_service.get_payment_method_by_id(
            test_payment_method.id,
            test_payment_method.user_id
        )
        assert deleted_pm is None
    
    @pytest.mark.asyncio
    async def test_delete_payment_method_not_found(self, db_session: AsyncSession, test_user: User):
        """Test deleting nonexistent payment method."""
        payment_service = PaymentService(db_session)
        
        result = await payment_service.delete_payment_method(uuid4(), test_user.id)
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_delete_payment_method_unauthorized(self, db_session: AsyncSession, test_payment_method: PaymentMethod):
        """Test deleting payment method by different user."""
        payment_service = PaymentService(db_session)
        other_user_id = uuid4()
        
        result = await payment_service.delete_payment_method(
            test_payment_method.id,
            other_user_id
        )
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_create_payment_intent(self, db_session: AsyncSession, test_user: User, test_payment_method: PaymentMethod, mock_stripe):
        """Test creating payment intent."""
        payment_service = PaymentService(db_session)
        
        payment_intent = await payment_service.create_payment_intent(
            user_id=test_user.id,
            amount=Decimal("100.00"),
            currency="usd",
            payment_method_id=test_payment_method.id,
            description="Test payment"
        )
        
        assert payment_intent is not None
        assert payment_intent.user_id == test_user.id
        assert payment_intent.amount == Decimal("100.00")
        assert payment_intent.currency == "usd"
        assert payment_intent.status == "requires_confirmation"
        assert payment_intent.stripe_payment_intent_id == "pi_test_123"
        
        # Verify Stripe API was called
        mock_stripe["payment_intent"].create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_payment_intent_invalid_payment_method(self, db_session: AsyncSession, test_user: User):
        """Test creating payment intent with invalid payment method."""
        payment_service = PaymentService(db_session)
        
        with pytest.raises(Exception) as exc_info:
            await payment_service.create_payment_intent(
                user_id=test_user.id,
                amount=Decimal("100.00"),
                currency="usd",
                payment_method_id=uuid4(),  # Invalid ID
                description="Test payment"
            )
        
        assert "payment method not found" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_confirm_payment_intent_success(self, db_session: AsyncSession, test_user: User, mock_stripe):
        """Test confirming payment intent successfully."""
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
            status="succeeded",
            charges=MagicMock(data=[MagicMock(id="ch_test_123")])
        ))
        
        payment_service = PaymentService(db_session)
        
        confirmed_intent = await payment_service.confirm_payment_intent(payment_intent.id)
        
        assert confirmed_intent is not None
        assert confirmed_intent.status == "succeeded"
        
        # Verify Stripe API was called
        mock_stripe["payment_intent"].confirm.assert_called_once_with("pi_test_123")
    
    @pytest.mark.asyncio
    async def test_confirm_payment_intent_failed(self, db_session: AsyncSession, test_user: User, mock_stripe):
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
            status="requires_payment_method",
            last_payment_error=MagicMock(
                code="card_declined",
                message="Your card was declined."
            )
        ))
        
        payment_service = PaymentService(db_session)
        
        confirmed_intent = await payment_service.confirm_payment_intent(payment_intent.id)
        
        assert confirmed_intent is not None
        assert confirmed_intent.status == "requires_payment_method"
    
    @pytest.mark.asyncio
    async def test_process_payment_success(self, db_session: AsyncSession, test_user: User, test_payment_method: PaymentMethod, mock_stripe):
        """Test processing payment successfully."""
        # Mock successful payment
        mock_stripe["payment_intent"].create.return_value = MagicMock(
            id="pi_test_123",
            status="succeeded",
            amount=10000,
            currency="usd",
            charges=MagicMock(data=[MagicMock(id="ch_test_123")])
        )
        
        payment_service = PaymentService(db_session)
        
        result = await payment_service.process_payment(
            user_id=test_user.id,
            amount=Decimal("100.00"),
            currency="usd",
            payment_method_id=test_payment_method.id,
            description="Test payment",
            idempotency_key=str(uuid4())
        )
        
        assert result["status"] == "succeeded"
        assert result["payment_intent_id"] == "pi_test_123"
        assert result["amount"] == Decimal("100.00")
        
        # Verify transaction was created
        assert "transaction_id" in result
    
    @pytest.mark.asyncio
    async def test_process_payment_failed(self, db_session: AsyncSession, test_user: User, test_payment_method: PaymentMethod, mock_stripe):
        """Test processing payment that fails."""
        # Mock failed payment
        mock_stripe["payment_intent"].create.return_value = MagicMock(
            id="pi_test_123",
            status="requires_payment_method",
            amount=10000,
            currency="usd",
            last_payment_error=MagicMock(
                code="card_declined",
                message="Your card was declined."
            )
        )
        
        payment_service = PaymentService(db_session)
        
        result = await payment_service.process_payment(
            user_id=test_user.id,
            amount=Decimal("100.00"),
            currency="usd",
            payment_method_id=test_payment_method.id,
            description="Test payment",
            idempotency_key=str(uuid4())
        )
        
        assert result["status"] == "requires_payment_method"
        assert result["payment_intent_id"] == "pi_test_123"
        assert "error" in result
        assert result["error"]["code"] == "card_declined"
    
    @pytest.mark.asyncio
    async def test_process_payment_idempotency(self, db_session: AsyncSession, test_user: User, test_payment_method: PaymentMethod, mock_stripe):
        """Test payment processing idempotency."""
        idempotency_key = str(uuid4())
        
        # Mock successful payment
        mock_stripe["payment_intent"].create.return_value = MagicMock(
            id="pi_test_123",
            status="succeeded",
            amount=10000,
            currency="usd",
            charges=MagicMock(data=[MagicMock(id="ch_test_123")])
        )
        
        payment_service = PaymentService(db_session)
        
        # First payment
        result1 = await payment_service.process_payment(
            user_id=test_user.id,
            amount=Decimal("100.00"),
            currency="usd",
            payment_method_id=test_payment_method.id,
            description="Test payment",
            idempotency_key=idempotency_key
        )
        
        # Second payment with same idempotency key
        result2 = await payment_service.process_payment(
            user_id=test_user.id,
            amount=Decimal("100.00"),
            currency="usd",
            payment_method_id=test_payment_method.id,
            description="Test payment",
            idempotency_key=idempotency_key
        )
        
        # Should return same result
        assert result1["payment_intent_id"] == result2["payment_intent_id"]
        assert result1["transaction_id"] == result2["transaction_id"]
    
    @pytest.mark.asyncio
    async def test_get_user_transactions(self, db_session: AsyncSession, test_user: User):
        """Test getting user's transactions."""
        # Create transactions
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
        
        payment_service = PaymentService(db_session)
        
        transactions = await payment_service.get_user_transactions(test_user.id)
        
        assert len(transactions) == 2
        
        # Should be ordered by creation date (newest first)
        assert transactions[0].created_at >= transactions[1].created_at
    
    @pytest.mark.asyncio
    async def test_get_user_transactions_with_filters(self, db_session: AsyncSession, test_user: User):
        """Test getting user's transactions with filters."""
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
        
        payment_service = PaymentService(db_session)
        
        # Filter by status
        succeeded_transactions = await payment_service.get_user_transactions(
            test_user.id,
            status="succeeded"
        )
        
        assert len(succeeded_transactions) == 1
        assert succeeded_transactions[0].status == "succeeded"
    
    @pytest.mark.asyncio
    async def test_create_refund(self, db_session: AsyncSession, test_user: User, mock_stripe):
        """Test creating refund."""
        # Create transaction to refund
        transaction = Transaction(
            id=uuid4(),
            user_id=test_user.id,
            stripe_payment_intent_id="pi_test_123",
            stripe_charge_id="ch_test_123",
            amount=Decimal("100.00"),
            currency="usd",
            status="succeeded",
            transaction_type="payment"
        )
        db_session.add(transaction)
        await db_session.commit()
        
        # Mock successful refund
        with patch('stripe.Refund.create') as mock_refund:
            mock_refund.return_value = MagicMock(
                id="re_test_123",
                status="succeeded",
                amount=5000,  # $50.00 in cents
                charge="ch_test_123"
            )
            
            payment_service = PaymentService(db_session)
            
            refund = await payment_service.create_refund(
                transaction_id=transaction.id,
                amount=Decimal("50.00"),
                reason="requested_by_customer"
            )
        
        assert refund is not None
        assert refund.amount == Decimal("50.00")
        assert refund.status == "succeeded"
        assert refund.stripe_refund_id == "re_test_123"
        
        # Verify Stripe API was called
        mock_refund.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_refund_excessive_amount(self, db_session: AsyncSession, test_user: User):
        """Test creating refund with amount exceeding transaction."""
        # Create transaction
        transaction = Transaction(
            id=uuid4(),
            user_id=test_user.id,
            stripe_payment_intent_id="pi_test_123",
            stripe_charge_id="ch_test_123",
            amount=Decimal("100.00"),
            currency="usd",
            status="succeeded",
            transaction_type="payment"
        )
        db_session.add(transaction)
        await db_session.commit()
        
        payment_service = PaymentService(db_session)
        
        with pytest.raises(Exception) as exc_info:
            await payment_service.create_refund(
                transaction_id=transaction.id,
                amount=Decimal("150.00"),  # More than transaction amount
                reason="requested_by_customer"
            )
        
        assert "exceeds" in str(exc_info.value).lower()


class TestPaymentFailureHandling:
    """Test payment failure handling."""
    
    @pytest.mark.asyncio
    async def test_categorize_payment_failure(self, db_session: AsyncSession):
        """Test payment failure categorization."""
        payment_service = PaymentService(db_session)
        
        # Test different failure codes
        test_cases = [
            ("insufficient_funds", PaymentFailureReason.INSUFFICIENT_FUNDS),
            ("card_declined", PaymentFailureReason.CARD_DECLINED),
            ("expired_card", PaymentFailureReason.EXPIRED_CARD),
            ("incorrect_cvc", PaymentFailureReason.INVALID_CARD),
            ("authentication_required", PaymentFailureReason.AUTHENTICATION_REQUIRED),
            ("processing_error", PaymentFailureReason.PROCESSING_ERROR),
            ("unknown_code", PaymentFailureReason.UNKNOWN)
        ]
        
        for stripe_code, expected_reason in test_cases:
            reason = payment_service.categorize_payment_failure(stripe_code)
            assert reason == expected_reason
    
    @pytest.mark.asyncio
    async def test_handle_payment_failure(self, db_session: AsyncSession, test_user: User):
        """Test payment failure handling."""
        # Create failed payment intent
        payment_intent = PaymentIntent(
            id=uuid4(),
            user_id=test_user.id,
            stripe_payment_intent_id="pi_test_123",
            amount=Decimal("100.00"),
            currency="usd",
            status="requires_payment_method"
        )
        db_session.add(payment_intent)
        await db_session.commit()
        
        payment_service = PaymentService(db_session)
        
        failure_info = {
            "code": "card_declined",
            "message": "Your card was declined.",
            "decline_code": "generic_decline"
        }
        
        await payment_service.handle_payment_failure(payment_intent.id, failure_info)
        
        # Verify failure was recorded
        await db_session.refresh(payment_intent)
        assert payment_intent.failure_reason == PaymentFailureReason.CARD_DECLINED
        assert payment_intent.failure_message == "Your card was declined."
    
    @pytest.mark.asyncio
    async def test_retry_failed_payment(self, db_session: AsyncSession, test_user: User, test_payment_method: PaymentMethod, mock_stripe):
        """Test retrying failed payment."""
        # Create failed payment intent
        payment_intent = PaymentIntent(
            id=uuid4(),
            user_id=test_user.id,
            stripe_payment_intent_id="pi_test_123",
            amount=Decimal("100.00"),
            currency="usd",
            status="requires_payment_method",
            failure_reason=PaymentFailureReason.CARD_DECLINED,
            retry_count=0
        )
        db_session.add(payment_intent)
        await db_session.commit()
        
        # Mock successful retry
        mock_stripe["payment_intent"].confirm = MagicMock(return_value=MagicMock(
            id="pi_test_123",
            status="succeeded",
            charges=MagicMock(data=[MagicMock(id="ch_test_123")])
        ))
        
        payment_service = PaymentService(db_session)
        
        result = await payment_service.retry_payment(
            payment_intent.id,
            test_payment_method.id
        )
        
        assert result["status"] == "succeeded"
        
        # Verify retry count was incremented
        await db_session.refresh(payment_intent)
        assert payment_intent.retry_count == 1
    
    @pytest.mark.asyncio
    async def test_retry_payment_max_attempts(self, db_session: AsyncSession, test_user: User, test_payment_method: PaymentMethod):
        """Test retrying payment that has reached max attempts."""
        # Create payment intent with max retries
        payment_intent = PaymentIntent(
            id=uuid4(),
            user_id=test_user.id,
            stripe_payment_intent_id="pi_test_123",
            amount=Decimal("100.00"),
            currency="usd",
            status="requires_payment_method",
            failure_reason=PaymentFailureReason.CARD_DECLINED,
            retry_count=3  # Max retries reached
        )
        db_session.add(payment_intent)
        await db_session.commit()
        
        payment_service = PaymentService(db_session)
        
        with pytest.raises(Exception) as exc_info:
            await payment_service.retry_payment(
                payment_intent.id,
                test_payment_method.id
            )
        
        assert "max retry attempts" in str(exc_info.value).lower()


class TestPaymentSecurity:
    """Test payment security features."""
    
    @pytest.mark.asyncio
    async def test_payment_amount_validation(self, db_session: AsyncSession, test_user: User, test_payment_method: PaymentMethod):
        """Test payment amount validation."""
        payment_service = PaymentService(db_session)
        
        # Test negative amount
        with pytest.raises(Exception) as exc_info:
            await payment_service.create_payment_intent(
                user_id=test_user.id,
                amount=Decimal("-10.00"),
                currency="usd",
                payment_method_id=test_payment_method.id,
                description="Test payment"
            )
        
        assert "amount must be positive" in str(exc_info.value).lower()
        
        # Test zero amount
        with pytest.raises(Exception) as exc_info:
            await payment_service.create_payment_intent(
                user_id=test_user.id,
                amount=Decimal("0.00"),
                currency="usd",
                payment_method_id=test_payment_method.id,
                description="Test payment"
            )
        
        assert "amount must be positive" in str(exc_info.value).lower()
        
        # Test excessive amount
        with pytest.raises(Exception) as exc_info:
            await payment_service.create_payment_intent(
                user_id=test_user.id,
                amount=Decimal("1000000.00"),  # $1M
                currency="usd",
                payment_method_id=test_payment_method.id,
                description="Test payment"
            )
        
        assert "amount exceeds limit" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_payment_method_ownership_validation(self, db_session: AsyncSession, test_user: User):
        """Test payment method ownership validation."""
        # Create payment method for different user
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
        
        other_pm = PaymentMethod(
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
        db_session.add(other_pm)
        await db_session.commit()
        
        payment_service = PaymentService(db_session)
        
        # Try to use other user's payment method
        with pytest.raises(Exception) as exc_info:
            await payment_service.create_payment_intent(
                user_id=test_user.id,
                amount=Decimal("100.00"),
                currency="usd",
                payment_method_id=other_pm.id,
                description="Test payment"
            )
        
        assert "payment method not found" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_transaction_integrity(self, db_session: AsyncSession, test_user: User, test_payment_method: PaymentMethod, mock_stripe):
        """Test transaction integrity and consistency."""
        payment_service = PaymentService(db_session)
        
        # Mock Stripe payment that succeeds
        mock_stripe["payment_intent"].create.return_value = MagicMock(
            id="pi_test_123",
            status="succeeded",
            amount=10000,
            currency="usd",
            charges=MagicMock(data=[MagicMock(id="ch_test_123")])
        )
        
        result = await payment_service.process_payment(
            user_id=test_user.id,
            amount=Decimal("100.00"),
            currency="usd",
            payment_method_id=test_payment_method.id,
            description="Test payment",
            idempotency_key=str(uuid4())
        )
        
        # Verify both PaymentIntent and Transaction were created
        payment_intent = await payment_service.get_payment_intent_by_stripe_id("pi_test_123")
        transaction = await payment_service.get_transaction_by_id(result["transaction_id"])
        
        assert payment_intent is not None
        assert transaction is not None
        assert payment_intent.amount == transaction.amount
        assert payment_intent.currency == transaction.currency
        assert payment_intent.status == transaction.status
    
    @pytest.mark.asyncio
    async def test_webhook_signature_validation(self, db_session: AsyncSession):
        """Test webhook signature validation."""
        payment_service = PaymentService(db_session)
        
        # Mock webhook payload and signature
        payload = '{"id": "evt_test_123", "type": "payment_intent.succeeded"}'
        valid_signature = "t=1234567890,v1=valid_signature"
        invalid_signature = "t=1234567890,v1=invalid_signature"
        
        with patch('stripe.Webhook.construct_event') as mock_construct:
            # Test valid signature
            mock_construct.return_value = {"id": "evt_test_123", "type": "payment_intent.succeeded"}
            
            is_valid = payment_service.validate_webhook_signature(payload, valid_signature)
            assert is_valid is True
            
            # Test invalid signature
            mock_construct.side_effect = stripe.error.SignatureVerificationError(
                "Invalid signature", valid_signature
            )
            
            is_valid = payment_service.validate_webhook_signature(payload, invalid_signature)
            assert is_valid is False