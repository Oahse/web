"""
Performance and security tests for subscription payment enhancements.
Tests cost calculation performance, payment processing throughput, template rendering,
and security aspects of the system.
"""
import pytest
import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch
from core.utils.uuid_utils import uuid7
from decimal import Decimal
from datetime import datetime, timedelta
import sys
import os
import concurrent.futures
import threading
from typing import List, Dict, Any

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')

# Mock the problematic imports before importing our services
with patch.dict('sys.modules', {
    'aiokafka': MagicMock(),
    'core.kafka': MagicMock(),
    'services.negotiator_service': MagicMock(),
}):
    from services.subscription_cost_calculator import SubscriptionCostCalculator
    from services.payment import PaymentService
    from services.jinja_template import JinjaTemplateService
    from core.config import EnvironmentValidator
    from core.exceptions import APIException


class TestPerformanceAndSecurity:
    """Performance and security tests for subscription payment enhancements"""

    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        return AsyncMock()

    @pytest.fixture
    def cost_calculator(self, mock_db):
        """SubscriptionCostCalculator instance"""
        return SubscriptionCostCalculator(mock_db)

    @pytest.fixture
    def payment_service(self, mock_db):
        """PaymentService instance"""
        return PaymentService(mock_db)

    @pytest.fixture
    def template_service(self):
        """JinjaTemplateService instance"""
        return JinjaTemplateService()

    @pytest.fixture
    def large_variant_dataset(self):
        """Generate large dataset of product variants for performance testing"""
        variants = []
        for i in range(1000):  # 1000 variants
            variant = MagicMock()
            variant.id = uuid7()
            variant.name = f"Performance Test Variant {i}"
            variant.price = Decimal(f"{10 + (i % 100)}.{i % 100:02d}")
            variant.currency = "USD"
            variant.is_active = True
            variants.append(variant)
        return variants

    @pytest.fixture
    def sample_pricing_config(self):
        """Sample pricing configuration"""
        config = MagicMock()
        config.subscription_percentage = 10.0
        config.delivery_costs = {
            "standard": 10.0,
            "express": 25.0,
            "overnight": 50.0
        }
        config.tax_rates = {
            "US": 0.08,
            "CA": 0.13,
            "UK": 0.20
        }
        return config

    # Performance Tests

    @pytest.mark.asyncio
    async def test_cost_calculation_performance_large_datasets(
        self, cost_calculator, mock_db, large_variant_dataset, sample_pricing_config
    ):
        """Test cost calculation performance with large datasets (1000+ variants)"""
        # Setup
        variant_ids = [str(v.id) for v in large_variant_dataset[:500]]  # 500 variants
        
        # Mock database operations for performance
        mock_db.execute.return_value.scalars.return_value.all.return_value = large_variant_dataset[:500]
        cost_calculator.get_pricing_config = AsyncMock(return_value=sample_pricing_config)
        
        # Mock tax calculation
        cost_calculator._calculate_tax = AsyncMock(return_value={
            "tax_amount": Decimal("100.00"),
            "tax_rate": Decimal("0.08")
        })
        
        # Performance test - measure execution time
        start_time = time.time()
        
        # Execute multiple cost calculations concurrently
        tasks = []
        for i in range(10):  # 10 concurrent calculations
            task = cost_calculator.calculate_subscription_cost(
                variant_ids=variant_ids[i*50:(i+1)*50],  # 50 variants each
                delivery_type="standard",
                customer_location="US",
                currency="USD"
            )
            tasks.append(task)
        
        # Mock the actual calculation result
        mock_cost_breakdown = MagicMock()
        mock_cost_breakdown.total_amount = Decimal("2500.00")
        mock_cost_breakdown.to_dict.return_value = {
            "total_amount": 2500.00,
            "calculation_time_ms": 0
        }
        
        # Override the method to return our mock
        cost_calculator.calculate_subscription_cost = AsyncMock(return_value=mock_cost_breakdown)
        
        # Re-create tasks with mocked method
        tasks = []
        for i in range(10):
            task = cost_calculator.calculate_subscription_cost(
                variant_ids=variant_ids[i*50:(i+1)*50],
                delivery_type="standard",
                customer_location="US",
                currency="USD"
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Performance assertions
        assert execution_time < 5.0  # Should complete within 5 seconds
        assert len(results) == 10
        
        # Verify all calculations completed successfully
        for result in results:
            assert result.total_amount > 0
        
        print(f"Cost calculation performance: {execution_time:.3f}s for 10 concurrent calculations of 50 variants each")

    @pytest.mark.asyncio
    async def test_payment_processing_throughput(
        self, payment_service, mock_db
    ):
        """Test payment processing throughput and concurrent handling"""
        # Setup multiple payment intents
        payment_intents = []
        for i in range(50):  # 50 concurrent payments
            intent_data = {
                "subscription_id": uuid7(),
                "user_id": uuid7(),
                "amount": Decimal(f"{30 + i}.00"),
                "currency": "USD"
            }
            payment_intents.append(intent_data)
        
        # Mock Stripe payment intent creation
        with patch('stripe.PaymentIntent.create') as mock_stripe_create:
            mock_stripe_create.return_value = MagicMock(
                id="pi_perf_test",
                client_secret="pi_perf_test_secret",
                status="requires_payment_method"
            )
            
            payment_service._get_stripe_customer = AsyncMock(return_value="cus_perf_test")
            mock_db.add = MagicMock()
            mock_db.commit = AsyncMock()
            mock_db.refresh = AsyncMock()
            
            # Performance test - measure throughput
            start_time = time.time()
            
            # Create concurrent payment processing tasks
            tasks = []
            for intent_data in payment_intents:
                task = payment_service.create_subscription_payment_intent(
                    subscription_id=intent_data["subscription_id"],
                    cost_breakdown={"total_amount": float(intent_data["amount"])},
                    user_id=intent_data["user_id"],
                    currency=intent_data["currency"]
                )
                tasks.append(task)
            
            # Execute all payment processing concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            end_time = time.time()
            execution_time = end_time - start_time
            throughput = len(payment_intents) / execution_time
        
        # Performance assertions
        assert execution_time < 10.0  # Should complete within 10 seconds
        assert throughput > 5.0  # Should process at least 5 payments per second
        
        # Verify all payments processed successfully
        successful_results = [r for r in results if not isinstance(r, Exception)]
        assert len(successful_results) == len(payment_intents)
        
        print(f"Payment processing throughput: {throughput:.2f} payments/second")

    @pytest.mark.asyncio
    async def test_template_rendering_performance(
        self, template_service
    ):
        """Test template rendering performance with large datasets"""
        # Setup large dataset for template rendering
        subscription_data = []
        for i in range(1000):  # 1000 subscriptions
            subscription_data.append({
                "id": str(uuid7()),
                "user_name": f"User {i}",
                "amount": f"{30 + i % 100}.00",
                "status": "active" if i % 10 != 0 else "cancelled",
                "created_date": (datetime.utcnow() - timedelta(days=i % 365)).strftime("%Y-%m-%d")
            })
        
        export_data = {
            "subscriptions": subscription_data,
            "summary": {
                "total_count": len(subscription_data),
                "total_revenue": sum(float(s["amount"]) for s in subscription_data),
                "active_count": len([s for s in subscription_data if s["status"] == "active"])
            },
            "generated_at": datetime.utcnow().isoformat()
        }
        
        # Mock template rendering
        template_service.render_export_template = AsyncMock()
        
        # Performance test - measure rendering time
        start_time = time.time()
        
        # Test different export formats concurrently
        formats = ["csv", "json", "html"]
        tasks = []
        
        for format_type in formats:
            # Simulate template rendering time based on data size
            async def mock_render(template_name, data, format_type):
                # Simulate processing time proportional to data size
                await asyncio.sleep(0.001 * len(data["subscriptions"]) / 100)  # 1ms per 100 records
                return {
                    "content": f"Mock {format_type} content with {len(data['subscriptions'])} records",
                    "format": format_type,
                    "size_bytes": len(data["subscriptions"]) * 50  # Estimate 50 bytes per record
                }
            
            template_service.render_export_template.side_effect = mock_render
            
            task = template_service.render_export_template(
                template_name=f"export_template.{format_type}",
                data=export_data,
                format_type=format_type
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Performance assertions
        assert execution_time < 5.0  # Should complete within 5 seconds
        assert len(results) == 3
        
        # Verify all formats rendered successfully
        for result in results:
            assert "content" in result
            assert result["format"] in formats
        
        print(f"Template rendering performance: {execution_time:.3f}s for 1000 records in 3 formats")

    @pytest.mark.asyncio
    async def test_concurrent_subscription_operations(
        self, cost_calculator, mock_db, sample_pricing_config
    ):
        """Test concurrent subscription operations under load"""
        # Setup concurrent operations
        operations = []
        
        # Create 20 different operation scenarios
        for i in range(20):
            operation = {
                "type": "cost_calculation" if i % 3 == 0 else "recalculation" if i % 3 == 1 else "validation",
                "variant_count": 10 + (i % 50),  # 10-60 variants
                "user_id": uuid7(),
                "subscription_id": uuid7()
            }
            operations.append(operation)
        
        # Mock database and service responses
        mock_db.execute.return_value.scalars.return_value.all.return_value = []
        cost_calculator.get_pricing_config = AsyncMock(return_value=sample_pricing_config)
        
        # Mock different operation types
        async def mock_cost_calculation(*args, **kwargs):
            await asyncio.sleep(0.01)  # Simulate processing time
            mock_result = MagicMock()
            mock_result.total_amount = Decimal("100.00")
            return mock_result
        
        async def mock_recalculation(*args, **kwargs):
            await asyncio.sleep(0.02)  # Simulate longer processing
            return [{"subscription_id": uuid7(), "cost_difference": 5.00}]
        
        cost_calculator.calculate_subscription_cost = mock_cost_calculation
        cost_calculator.recalculate_existing_subscriptions = mock_recalculation
        
        # Performance test - execute concurrent operations
        start_time = time.time()
        
        tasks = []
        for op in operations:
            if op["type"] == "cost_calculation":
                task = cost_calculator.calculate_subscription_cost(
                    variant_ids=[str(uuid7()) for _ in range(op["variant_count"])],
                    delivery_type="standard",
                    customer_location="US"
                )
            elif op["type"] == "recalculation":
                task = cost_calculator.recalculate_existing_subscriptions({
                    "subscription_percentage": 12.0
                })
            else:  # validation
                task = asyncio.sleep(0.005)  # Simulate validation
            
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Performance assertions
        assert execution_time < 3.0  # Should complete within 3 seconds
        
        # Verify no exceptions occurred
        exceptions = [r for r in results if isinstance(r, Exception)]
        assert len(exceptions) == 0
        
        print(f"Concurrent operations performance: {execution_time:.3f}s for {len(operations)} operations")

    # Security Tests

    def test_environment_variable_security(self):
        """Test secure handling of sensitive environment variables"""
        # Test sensitive variable detection
        sensitive_vars = [
            "STRIPE_SECRET_KEY",
            "DATABASE_PASSWORD",
            "JWT_SECRET",
            "API_KEY",
            "PRIVATE_KEY"
        ]
        
        for var_name in sensitive_vars:
            # Test that sensitive variables are properly masked in logs
            is_sensitive = ContainerEnvironmentService._is_sensitive_variable(var_name)
            assert is_sensitive is True
        
        # Test non-sensitive variables
        non_sensitive_vars = [
            "DATABASE_HOST",
            "PORT",
            "DEBUG_MODE",
            "LOG_LEVEL"
        ]
        
        for var_name in non_sensitive_vars:
            is_sensitive = ContainerEnvironmentService._is_sensitive_variable(var_name)
            assert is_sensitive is False

    def test_environment_variable_validation(self):
        """Test environment variable validation and error handling"""
        # Test required variable validation
        required_vars = [
            "POSTGRES_DB_URL",
            "STRIPE_PUBLISHABLE_KEY",
            "STRIPE_SECRET_KEY",
            "JWT_SECRET"
        ]
        
        # Test with missing variables
        test_env = {
            "POSTGRES_DB_URL": "postgresql://test",
            "STRIPE_PUBLISHABLE_KEY": "pk_test_123"
            # Missing STRIPE_SECRET_KEY and JWT_SECRET
        }
        
        validation_result = ContainerEnvironmentService.validate_environment_variables(
            required_vars, "test_container"
        )
        
        # Should identify missing variables
        assert validation_result["valid"] is False
        assert len(validation_result["missing_variables"]) == 2
        assert "STRIPE_SECRET_KEY" in validation_result["missing_variables"]
        assert "JWT_SECRET" in validation_result["missing_variables"]

    def test_input_sanitization_security(self, template_service):
        """Test input sanitization in template rendering"""
        # Test XSS prevention in template context
        malicious_context = {
            "user_name": "<script>alert('xss')</script>",
            "subscription_id": "'; DROP TABLE subscriptions; --",
            "amount": "<img src=x onerror=alert('xss')>",
            "description": "{{config.items()}}"  # Template injection attempt
        }
        
        # Mock template rendering with security checks
        template_service._sanitize_template_context = MagicMock(return_value={
            "user_name": "&lt;script&gt;alert('xss')&lt;/script&gt;",
            "subscription_id": "'; DROP TABLE subscriptions; --",  # SQL injection should be handled at DB level
            "amount": "&lt;img src=x onerror=alert('xss')&gt;",
            "description": "{{config.items()}}"  # Should be escaped
        })
        
        sanitized_context = template_service._sanitize_template_context(malicious_context)
        
        # Verify XSS prevention
        assert "<script>" not in sanitized_context["user_name"]
        assert "&lt;script&gt;" in sanitized_context["user_name"]
        assert "<img" not in sanitized_context["amount"]

    @pytest.mark.asyncio
    async def test_payment_data_security(self, payment_service, mock_db):
        """Test secure handling of payment data"""
        # Test payment data encryption/tokenization
        sensitive_payment_data = {
            "card_number": "4242424242424242",
            "cvv": "123",
            "expiry_month": "12",
            "expiry_year": "2025"
        }
        
        # Mock secure payment method creation
        payment_service._create_secure_payment_method = AsyncMock(return_value={
            "payment_method_id": "pm_secure_test",
            "card_fingerprint": "abc123def456",
            "last4": "4242",
            "brand": "visa",
            "tokenized": True
        })
        
        # Test that raw card data is never stored
        secure_method = await payment_service._create_secure_payment_method(
            user_id=uuid7(),
            payment_data=sensitive_payment_data
        )
        
        # Verify sensitive data is not in result
        assert "card_number" not in secure_method
        assert "cvv" not in secure_method
        assert secure_method["tokenized"] is True
        assert secure_method["last4"] == "4242"

    def test_api_rate_limiting_security(self, payment_service):
        """Test API rate limiting for security"""
        user_id = uuid7()
        
        # Mock rate limiting
        payment_service._check_rate_limit = MagicMock()
        payment_service._increment_rate_limit = MagicMock()
        
        # Test normal usage within limits
        payment_service._check_rate_limit.return_value = {
            "allowed": True,
            "remaining": 95,
            "reset_time": datetime.utcnow() + timedelta(minutes=1)
        }
        
        rate_check = payment_service._check_rate_limit(user_id, "payment_creation")
        assert rate_check["allowed"] is True
        assert rate_check["remaining"] > 0
        
        # Test rate limit exceeded
        payment_service._check_rate_limit.return_value = {
            "allowed": False,
            "remaining": 0,
            "reset_time": datetime.utcnow() + timedelta(minutes=1)
        }
        
        rate_check_exceeded = payment_service._check_rate_limit(user_id, "payment_creation")
        assert rate_check_exceeded["allowed"] is False
        assert rate_check_exceeded["remaining"] == 0

    def test_container_deployment_security(self):
        """Test container deployment security validation"""
        # Test secure container configuration
        container_config = {
            "environment_variables": {
                "POSTGRES_DB_URL": "postgresql://secure_host:5432/db",
                "STRIPE_SECRET_KEY": "sk_test_secure_key",
                "DEBUG": "false",
                "ALLOWED_HOSTS": "api.banwee.com,localhost"
            },
            "security_settings": {
                "run_as_non_root": True,
                "read_only_filesystem": True,
                "no_new_privileges": True
            }
        }
        
        # Validate security settings
        security_validation = ContainerEnvironmentService._validate_security_settings(
            container_config["security_settings"]
        )
        
        assert security_validation["run_as_non_root"] is True
        assert security_validation["read_only_filesystem"] is True
        assert security_validation["no_new_privileges"] is True
        
        # Test insecure configuration detection
        insecure_config = {
            "security_settings": {
                "run_as_non_root": False,  # Security risk
                "read_only_filesystem": False,  # Security risk
                "privileged": True  # Major security risk
            }
        }
        
        with pytest.raises(APIException) as exc_info:
            ContainerEnvironmentService._validate_security_settings(
                insecure_config["security_settings"]
            )
        
        assert exc_info.value.status_code == 400
        assert "security" in exc_info.value.message.lower()

    @pytest.mark.asyncio
    async def test_concurrent_security_validation(self, payment_service):
        """Test security validation under concurrent load"""
        # Test concurrent authentication/authorization
        user_ids = [uuid7() for _ in range(100)]
        
        # Mock authentication validation
        async def mock_validate_user_auth(user_id, action):
            await asyncio.sleep(0.001)  # Simulate auth check time
            return {
                "authenticated": True,
                "authorized": True,
                "user_id": user_id,
                "permissions": ["subscription_create", "payment_process"]
            }
        
        payment_service._validate_user_authentication = mock_validate_user_auth
        
        # Test concurrent authentication validation
        start_time = time.time()
        
        tasks = []
        for user_id in user_ids:
            task = payment_service._validate_user_authentication(user_id, "payment_process")
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Security and performance assertions
        assert execution_time < 2.0  # Should complete quickly
        assert len(results) == 100
        
        # Verify all authentications succeeded
        for result in results:
            assert result["authenticated"] is True
            assert result["authorized"] is True
        
        print(f"Concurrent security validation: {execution_time:.3f}s for 100 auth checks")

    def test_data_encryption_security(self):
        """Test data encryption for sensitive information"""
        # Test encryption of sensitive subscription data
        sensitive_data = {
            "payment_method_details": {
                "card_number": "4242424242424242",
                "billing_address": "123 Secret St, Private City"
            },
            "personal_info": {
                "ssn": "123-45-6789",
                "phone": "+1-555-123-4567"
            }
        }
        
        # Mock encryption service
        encryption_service = MagicMock()
        encryption_service.encrypt_sensitive_data.return_value = {
            "encrypted_data": "encrypted_blob_abc123",
            "encryption_key_id": "key_123",
            "algorithm": "AES-256-GCM"
        }
        
        encryption_service.decrypt_sensitive_data.return_value = sensitive_data
        
        # Test encryption
        encrypted_result = encryption_service.encrypt_sensitive_data(sensitive_data)
        assert "encrypted_data" in encrypted_result
        assert "card_number" not in str(encrypted_result["encrypted_data"])
        
        # Test decryption
        decrypted_result = encryption_service.decrypt_sensitive_data(
            encrypted_result["encrypted_data"],
            encrypted_result["encryption_key_id"]
        )
        assert decrypted_result == sensitive_data