"""
Unit tests for payment service
"""
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from decimal import Decimal
from uuid import uuid4
from datetime import datetime

from services.payments import PaymentService
from models.payments import Payment, PaymentStatus
from models.orders import Order
from core.errors import APIException


class TestPaymentService:
    
    @pytest_asyncio.fixture
    async def payment_service(self, db_session, mock_stripe):
        with patch('services.payments.stripe', mock_stripe):
            return PaymentService(db_session)
    
    @pytest_asyncio.fixture
    async def test_order(self, db_session, test_user):
        """Create a test order"""
        order = Order(
            id=uuid4(),
            user_id=test_user.id,
            total_amount=Decimal("99.99"),
            status="pending",
            created_at=datetime.utcnow()
        )
        db_session.add(order)
        await db_session.commit()
        await db_session.refresh(order)
        return order
    
    @pytest.mark.asyncio
    async def test_create_payment_intent_success(self, payment_service, test_order):
        """Test successful payment intent creation"""
        amount = Decimal("99.99")
        currency = "usd"
        
        result = await payment_service.create_payment_intent(
            amount=amount,
            currency=currency,
            order_id=test_order.id
        )
        
        assert result["id"] == "pi_test_123"
        assert result["client_secret"] == "pi_test_123_secret_test"
        assert result["status"] == "requires_payment_method"
    
    @pytest.mark.asyncio
    async def test_create_payment_intent_invalid_amount(self, payment_service, test_order):
        """Test payment intent creation with invalid amount"""
        with pytest.raises(APIException) as exc_info:
            await payment_service.create_payment_intent(
                amount=Decimal("0"),
                currency="usd",
                order_id=test_order.id
            )
        
        assert exc_info.value.status_code == 400
        assert "amount" in str(exc_info.value.message).lower()
    
    @pytest.mark.asyncio
    async def test_confirm_payment_success(self, payment_service, test_order):
        """Test successful payment confirmation"""
        payment_intent_id = "pi_test_123"
        
        # Create a payment record first
        payment = Payment(
            id=uuid4(),
            order_id=test_order.id,
            amount=test_order.total_amount,
            currency="usd",
            payment_method="stripe",
            stripe_payment_intent_id=payment_intent_id,
            status=PaymentStatus.PENDING
        )
        payment_service.db.add(payment)
        await payment_service.db.commit()
        
        result = await payment_service.confirm_payment(payment_intent_id)
        
        assert result["id"] == payment_intent_id
        assert result["status"] == "succeeded"
        
        # Check payment status updated
        await payment_service.db.refresh(payment)
        assert payment.status == PaymentStatus.COMPLETED
    
    @pytest.mark.asyncio
    async def test_confirm_payment_not_found(self, payment_service):
        """Test payment confirmation with non-existent payment"""
        with pytest.raises(APIException) as exc_info:
            await payment_service.confirm_payment("pi_nonexistent")
        
        assert exc_info.value.status_code == 404
        assert "payment" in str(exc_info.value.message).lower()
    
    @pytest.mark.asyncio
    async def test_process_webhook_payment_succeeded(self, payment_service, test_order):
        """Test webhook processing for successful payment"""
        payment_intent_id = "pi_test_123"
        
        # Create a payment record
        payment = Payment(
            id=uuid4(),
            order_id=test_order.id,
            amount=test_order.total_amount,
            currency="usd",
            payment_method="stripe",
            stripe_payment_intent_id=payment_intent_id,
            status=PaymentStatus.PENDING
        )
        payment_service.db.add(payment)
        await payment_service.db.commit()
        
        webhook_data = {
            "type": "payment_intent.succeeded",
            "data": {
                "object": {
                    "id": payment_intent_id,
                    "status": "succeeded",
                    "amount": 9999,  # Stripe amounts are in cents
                    "currency": "usd"
                }
            }
        }
        
        await payment_service.process_webhook(webhook_data)
        
        # Check payment status updated
        await payment_service.db.refresh(payment)
        assert payment.status == PaymentStatus.COMPLETED
    
    @pytest.mark.asyncio
    async def test_process_webhook_payment_failed(self, payment_service, test_order):
        """Test webhook processing for failed payment"""
        payment_intent_id = "pi_test_123"
        
        # Create a payment record
        payment = Payment(
            id=uuid4(),
            order_id=test_order.id,
            amount=test_order.total_amount,
            currency="usd",
            payment_method="stripe",
            stripe_payment_intent_id=payment_intent_id,
            status=PaymentStatus.PENDING
        )
        payment_service.db.add(payment)
        await payment_service.db.commit()
        
        webhook_data = {
            "type": "payment_intent.payment_failed",
            "data": {
                "object": {
                    "id": payment_intent_id,
                    "status": "requires_payment_method",
                    "last_payment_error": {
                        "message": "Your card was declined."
                    }
                }
            }
        }
        
        await payment_service.process_webhook(webhook_data)
        
        # Check payment status updated
        await payment_service.db.refresh(payment)
        assert payment.status == PaymentStatus.FAILED
    
    @pytest.mark.asyncio
    async def test_refund_payment_success(self, payment_service, test_order):
        """Test successful payment refund"""
        payment_intent_id = "pi_test_123"
        
        # Create a completed payment
        payment = Payment(
            id=uuid4(),
            order_id=test_order.id,
            amount=test_order.total_amount,
            currency="usd",
            payment_method="stripe",
            stripe_payment_intent_id=payment_intent_id,
            status=PaymentStatus.COMPLETED
        )
        payment_service.db.add(payment)
        await payment_service.db.commit()
        
        # Mock Stripe refund
        with patch.object(payment_service, 'stripe') as mock_stripe:
            mock_stripe.Refund.create.return_value = MagicMock(
                id="re_test_123",
                status="succeeded",
                amount=9999
            )
            
            refund = await payment_service.refund_payment(
                payment.id,
                amount=Decimal("99.99"),
                reason="requested_by_customer"
            )
            
            assert refund["id"] == "re_test_123"
            assert refund["status"] == "succeeded"
            
            # Check payment status updated
            await payment_service.db.refresh(payment)
            assert payment.status == PaymentStatus.REFUNDED
    
    @pytest.mark.asyncio
    async def test_refund_payment_not_completed(self, payment_service, test_order):
        """Test refund attempt on non-completed payment"""
        payment = Payment(
            id=uuid4(),
            order_id=test_order.id,
            amount=test_order.total_amount,
            currency="usd",
            payment_method="stripe",
            stripe_payment_intent_id="pi_test_123",
            status=PaymentStatus.PENDING
        )
        payment_service.db.add(payment)
        await payment_service.db.commit()
        
        with pytest.raises(APIException) as exc_info:
            await payment_service.refund_payment(
                payment.id,
                amount=Decimal("99.99"),
                reason="requested_by_customer"
            )
        
        assert exc_info.value.status_code == 400
        assert "cannot be refunded" in str(exc_info.value.message).lower()
    
    @pytest.mark.asyncio
    async def test_get_payment_by_id(self, payment_service, test_order):
        """Test getting payment by ID"""
        payment = Payment(
            id=uuid4(),
            order_id=test_order.id,
            amount=test_order.total_amount,
            currency="usd",
            payment_method="stripe",
            stripe_payment_intent_id="pi_test_123",
            status=PaymentStatus.COMPLETED
        )
        payment_service.db.add(payment)
        await payment_service.db.commit()
        
        retrieved_payment = await payment_service.get_payment_by_id(payment.id)
        
        assert retrieved_payment.id == payment.id
        assert retrieved_payment.amount == payment.amount
        assert retrieved_payment.status == payment.status
    
    @pytest.mark.asyncio
    async def test_get_payments_by_order(self, payment_service, test_order):
        """Test getting payments by order ID"""
        payment1 = Payment(
            id=uuid4(),
            order_id=test_order.id,
            amount=Decimal("50.00"),
            currency="usd",
            payment_method="stripe",
            stripe_payment_intent_id="pi_test_123",
            status=PaymentStatus.COMPLETED
        )
        payment2 = Payment(
            id=uuid4(),
            order_id=test_order.id,
            amount=Decimal("49.99"),
            currency="usd",
            payment_method="stripe",
            stripe_payment_intent_id="pi_test_456",
            status=PaymentStatus.COMPLETED
        )
        payment_service.db.add_all([payment1, payment2])
        await payment_service.db.commit()
        
        payments = await payment_service.get_payments_by_order(test_order.id)
        
        assert len(payments) == 2
        assert all(p.order_id == test_order.id for p in payments)
    
    @pytest.mark.asyncio
    async def test_calculate_fees(self, payment_service):
        """Test payment fee calculation"""
        amount = Decimal("100.00")
        
        fees = payment_service.calculate_fees(amount, "stripe")
        
        # Stripe typically charges 2.9% + $0.30
        expected_fee = amount * Decimal("0.029") + Decimal("0.30")
        assert abs(fees - expected_fee) < Decimal("0.01")
    
    @pytest.mark.asyncio
    async def test_validate_payment_method(self, payment_service):
        """Test payment method validation"""
        # Valid payment methods
        assert payment_service.validate_payment_method("stripe")
        assert payment_service.validate_payment_method("paypal")
        
        # Invalid payment method
        assert not payment_service.validate_payment_method("invalid_method")
    
    @pytest.mark.asyncio
    async def test_retry_failed_payment(self, payment_service, test_order):
        """Test retrying a failed payment"""
        payment = Payment(
            id=uuid4(),
            order_id=test_order.id,
            amount=test_order.total_amount,
            currency="usd",
            payment_method="stripe",
            stripe_payment_intent_id="pi_test_123",
            status=PaymentStatus.FAILED,
            retry_count=0
        )
        payment_service.db.add(payment)
        await payment_service.db.commit()
        
        with patch.object(payment_service, 'create_payment_intent') as mock_create:
            mock_create.return_value = {
                "id": "pi_test_retry_123",
                "client_secret": "pi_test_retry_123_secret",
                "status": "requires_payment_method"
            }
            
            result = await payment_service.retry_payment(payment.id)
            
            assert result["id"] == "pi_test_retry_123"
            
            # Check retry count incremented
            await payment_service.db.refresh(payment)
            assert payment.retry_count == 1