"""
Tests for enhanced PaymentService with subscription-specific features.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from decimal import Decimal
from datetime import datetime, timedelta
from core.utils.uuid_utils import uuid7

from services.payment import PaymentService
from models.user import User
from models.subscription import Subscription
from models.payment_intent import PaymentIntent
from models.payment import PaymentMethod


class TestEnhancedPaymentService:
    """Test enhanced payment service functionality"""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        db = AsyncMock()
        return db
    
    @pytest.fixture
    def payment_service(self, mock_db):
        """Create PaymentService instance with mocked database"""
        return PaymentService(mock_db)
    
    @pytest.fixture
    def sample_user(self):
        """Sample user for testing"""
        return User(
            id=uuid7(),
            email="test@example.com",
            firstname="Test",
            lastname="User",
            full_name="Test User",
            stripe_customer_id="cus_test123"
        )
    
    @pytest.fixture
    def sample_subscription(self):
        """Sample subscription for testing"""
        return Subscription(
            id=uuid7(),
            user_id=uuid7(),
            plan_id="premium",
            status="active",
            billing_cycle="monthly",
            currency="USD",
            variant_ids=["var1", "var2"],
            delivery_type="standard"
        )
    
    @pytest.fixture
    def sample_cost_breakdown(self):
        """Sample cost breakdown for testing"""
        return {
            "variant_costs": [
                {"variant_id": "var1", "price": 10.00},
                {"variant_id": "var2", "price": 15.00}
            ],
            "subtotal": 25.00,
            "admin_percentage": 5.0,
            "admin_fee": 1.25,
            "delivery_cost": 5.00,
            "tax_amount": 2.48,
            "total_amount": 33.73,
            "currency": "USD"
        }

    @pytest.mark.asyncio
    async def test_create_subscription_payment_intent_basic(
        self, payment_service, mock_db, sample_user, sample_subscription, sample_cost_breakdown
    ):
        """Test basic subscription payment intent creation"""
        # Mock database responses
        mock_db.get.side_effect = [sample_user, sample_subscription]
        mock_db.add = Mock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        
        # Mock Stripe payment intent creation
        with patch('stripe.PaymentIntent.create') as mock_stripe_create:
            mock_stripe_create.return_value = Mock(
                id="pi_test123",
                client_secret="pi_test123_secret",
                status="requires_payment_method",
                next_action=None
            )
            
            # Mock _get_stripe_customer method
            with patch.object(payment_service, '_get_stripe_customer', return_value="cus_test123"):
                result = await payment_service.create_subscription_payment_intent(
                    subscription_id=sample_subscription.id,
                    cost_breakdown=sample_cost_breakdown,
                    user_id=sample_user.id,
                    currency="USD"
                )
        
        # Verify result structure
        assert result["payment_intent_id"] == "pi_test123"
        assert result["client_secret"] == "pi_test123_secret"
        assert result["status"] == "requires_payment_method"
        assert result["amount_breakdown"] == sample_cost_breakdown
        assert result["currency"] == "USD"
        assert "subscription_details" in result
        assert result["subscription_details"]["subscription_id"] == str(sample_subscription.id)
        
        # Verify Stripe was called with correct parameters
        mock_stripe_create.assert_called_once()
        call_args = mock_stripe_create.call_args[1]
        assert call_args["amount"] == 3373  # 33.73 * 100 cents
        assert call_args["currency"] == "usd"
        assert call_args["customer"] == "cus_test123"

    @pytest.mark.asyncio
    async def test_verify_stripe_dashboard_transaction_success(
        self, payment_service, mock_db
    ):
        """Test successful Stripe dashboard transaction verification"""
        payment_intent_id = "pi_test123"
        
        # Mock Stripe payment intent retrieval
        with patch('stripe.PaymentIntent.retrieve') as mock_stripe_retrieve:
            mock_stripe_retrieve.return_value = Mock(
                id=payment_intent_id,
                status="succeeded",
                amount=3373,
                currency="usd",
                customer="cus_test123",
                charges=Mock(data=[
                    Mock(
                        id="ch_test123",
                        status="succeeded",
                        amount=3373,
                        currency="usd",
                        payment_method_details=Mock(type="card")
                    )
                ])
            )
            
            # Mock local payment intent record
            mock_local_record = Mock()
            mock_local_record.user_id = uuid7()
            mock_db.execute.return_value.scalar_one_or_none.return_value = mock_local_record
            mock_db.get.return_value = Mock(stripe_customer_id="cus_test123")
            mock_db.commit = AsyncMock()
            
            result = await payment_service.verify_stripe_dashboard_transaction(
                payment_intent_id=payment_intent_id,
                expected_amount=Decimal("33.73"),
                expected_currency="USD"
            )
        
        # Verify verification results
        assert result["verification_passed"] is True
        assert result["payment_intent_found"] is True
        assert result["stripe_status"] == "succeeded"
        assert result["amount_matches"] is True
        assert result["currency_matches"] is True
        assert result["charges_present"] is True
        assert "stripe_dashboard_url" in result

    @pytest.mark.asyncio
    async def test_handle_recurring_billing_success(
        self, payment_service, mock_db, sample_user, sample_subscription
    ):
        """Test successful recurring billing"""
        # Setup subscription as active
        sample_subscription.status = "active"
        
        # Mock database responses
        mock_db.get.side_effect = [sample_subscription, sample_user]
        
        # Mock default payment method
        mock_payment_method = Mock()
        mock_payment_method.id = uuid7()
        mock_payment_method.stripe_payment_method_id = "pm_test123"
        
        with patch.object(payment_service, 'get_default_payment_method', return_value=mock_payment_method):
            with patch.object(payment_service, 'create_subscription_payment_intent') as mock_create_intent:
                mock_create_intent.return_value = {
                    "payment_intent_id": "pi_test123",
                    "status": "succeeded",
                    "requires_action": False
                }
                
                with patch.object(payment_service, '_update_subscription_after_successful_billing') as mock_update:
                    result = await payment_service.handle_recurring_billing(
                        subscription_id=sample_subscription.id,
                        billing_cycle="monthly"
                    )
        
        # Verify successful billing result
        assert result["status"] == "succeeded"
        assert result["message"] == "Recurring billing completed successfully"
        assert result["subscription_status"] == "active"
        assert result["payment_intent_id"] == "pi_test123"
        
        # Verify subscription was updated
        mock_update.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_3d_secure_authentication(
        self, payment_service, mock_db
    ):
        """Test 3D Secure authentication handling"""
        payment_intent_id = "pi_test123"
        
        # Mock Stripe payment intent with 3D Secure requirement
        with patch('stripe.PaymentIntent.retrieve') as mock_stripe_retrieve:
            mock_stripe_retrieve.return_value = Mock(
                id=payment_intent_id,
                status="requires_action",
                client_secret="pi_test123_secret",
                next_action=Mock(
                    type="use_stripe_sdk",
                    redirect_to_url=Mock(
                        url="https://hooks.stripe.com/redirect/authenticate/src_123",
                        return_url="https://example.com/return"
                    )
                )
            )
            
            # Mock local payment intent record
            mock_local_record = Mock()
            mock_local_record.user_id = uuid7()
            mock_local_record.payment_metadata = {}
            mock_db.execute.return_value.scalar_one_or_none.return_value = mock_local_record
            mock_db.commit = AsyncMock()
            
            result = await payment_service.handle_3d_secure_authentication(
                payment_intent_id=payment_intent_id
            )
        
        # Verify 3D Secure handling result
        assert result["status"] == "requires_action"
        assert result["message"] == "3D Secure authentication required"
        assert result["client_secret"] == "pi_test123_secret"
        assert "next_action" in result

    @pytest.mark.asyncio
    async def test_process_multi_currency_payment(
        self, payment_service, mock_db, sample_user
    ):
        """Test multi-currency payment processing"""
        # Mock database responses
        mock_db.get.return_value = sample_user
        
        # Mock currency conversion
        with patch.object(payment_service, 'get_supported_currencies') as mock_currencies:
            mock_currencies.return_value = [
                {"code": "USD"}, {"code": "EUR"}, {"code": "GBP"}
            ]
            
            with patch.object(payment_service, 'convert_currency_via_stripe') as mock_convert:
                mock_convert.return_value = {
                    "converted_amount": Decimal("28.50"),
                    "exchange_rate": Decimal("0.85")
                }
                
                with patch.object(payment_service, '_calculate_international_tax') as mock_tax:
                    mock_tax.return_value = {
                        "tax_amount": Decimal("5.70"),
                        "tax_rate": Decimal("0.20")
                    }
                    
                    with patch('stripe.PaymentIntent.create') as mock_stripe_create:
                        mock_stripe_create.return_value = Mock(
                            id="pi_multi123",
                            client_secret="pi_multi123_secret",
                            status="requires_payment_method",
                            next_action=None
                        )
                        
                        with patch.object(payment_service, '_get_stripe_customer', return_value="cus_test123"):
                            mock_db.add = Mock()
                            mock_db.commit = AsyncMock()
                            mock_db.refresh = AsyncMock()
                            
                            result = await payment_service.process_multi_currency_payment(
                                amount=Decimal("33.50"),
                                from_currency="USD",
                                to_currency="EUR",
                                user_id=sample_user.id
                            )
        
        # Verify multi-currency result
        assert result["payment_intent_id"] == "pi_multi123"
        assert result["currency_conversion"]["original_amount"] == 33.50
        assert result["currency_conversion"]["converted_amount"] == 28.50
        assert result["currency_conversion"]["exchange_rate"] == 0.85
        assert result["currency_conversion"]["original_currency"] == "USD"
        assert result["currency_conversion"]["target_currency"] == "EUR"

    @pytest.mark.asyncio
    async def test_detect_user_currency(
        self, payment_service, mock_db
    ):
        """Test user currency detection"""
        user_id = uuid7()
        
        # Mock user with address
        mock_user = Mock()
        mock_user.preferred_currency = None
        mock_user.default_address = Mock()
        mock_user.default_address.country = "GB"
        
        mock_db.get.return_value = mock_user
        
        result = await payment_service.detect_user_currency(
            user_id=user_id,
            country_code="GB"
        )
        
        # Should detect GBP for Great Britain
        assert result == "GBP"

    @pytest.mark.asyncio
    async def test_log_payment_attempt(
        self, payment_service, mock_db
    ):
        """Test payment attempt logging"""
        user_id = uuid7()
        payment_intent_id = "pi_test123"
        amount = Decimal("25.00")
        
        # Mock payment intent record
        mock_payment_intent = Mock()
        mock_payment_intent.payment_metadata = {}
        mock_db.execute.return_value.scalar_one_or_none.return_value = mock_payment_intent
        mock_db.commit = AsyncMock()
        
        result = await payment_service.log_payment_attempt(
            user_id=user_id,
            payment_intent_id=payment_intent_id,
            amount=amount,
            currency="USD",
            payment_method_type="card"
        )
        
        # Verify logging result
        assert result["status"] == "success"
        assert result["message"] == "Payment attempt logged successfully"
        assert result["payment_intent_id"] == payment_intent_id

    def test_get_supported_currencies(self, payment_service):
        """Test getting supported currencies list"""
        currencies = payment_service.get_supported_currencies()
        
        # Verify currency list structure
        assert isinstance(currencies, list)
        assert len(currencies) > 0
        
        # Check for common currencies
        currency_codes = [c["code"] for c in currencies]
        assert "USD" in currency_codes
        assert "EUR" in currency_codes
        assert "GBP" in currency_codes
        
        # Verify currency structure
        usd_currency = next(c for c in currencies if c["code"] == "USD")
        assert "name" in usd_currency
        assert "symbol" in usd_currency
        assert "decimal_places" in usd_currency

    def test_currency_for_country_mapping(self, payment_service):
        """Test country to currency mapping"""
        # Test common country mappings
        assert payment_service._get_currency_for_country("US") == "USD"
        assert payment_service._get_currency_for_country("GB") == "GBP"
        assert payment_service._get_currency_for_country("DE") == "EUR"
        assert payment_service._get_currency_for_country("CA") == "CAD"
        assert payment_service._get_currency_for_country("AU") == "AUD"
        assert payment_service._get_currency_for_country("JP") == "JPY"
        
        # Test unknown country fallback
        assert payment_service._get_currency_for_country("XX") == "USD"

    def test_tax_rate_for_country(self, payment_service):
        """Test tax rate calculation for different countries"""
        # Test VAT countries
        uk_tax = payment_service._get_tax_rate_for_country("GB", "GBP")
        assert uk_tax["rate"] == Decimal('0.20')
        assert uk_tax["type"] == "vat"
        
        # Test US sales tax
        us_tax = payment_service._get_tax_rate_for_country("US", "USD")
        assert us_tax["rate"] == Decimal('0.08')
        assert uk_tax["type"] == "vat"
        
        # Test unknown country
        unknown_tax = payment_service._get_tax_rate_for_country("XX", "USD")
        assert unknown_tax["rate"] == Decimal('0')
        assert unknown_tax["type"] == "none"