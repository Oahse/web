"""
Tests for security middleware functionality
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from core.middleware.rate_limit import SecurityService, RateLimitService
from core.security.config import security_settings


class TestSecurityService:
    """Test security service functionality"""
    
    @pytest.fixture
    def security_service(self):
        """Create security service instance"""
        return SecurityService()
    
    @pytest.mark.asyncio
    async def test_coupon_abuse_detection_daily_limit(self, security_service):
        """Test coupon abuse detection for daily limit"""
        # Mock Redis client
        mock_redis = AsyncMock()
        security_service._get_redis = AsyncMock(return_value=mock_redis)
        
        # Simulate 3 previous attempts (at daily limit)
        mock_redis.zcard.return_value = 3
        
        result = await security_service.detect_coupon_abuse("user:123", "SAVE20")
        
        assert result["blocked"] is True
        assert result["reason"] == "coupon_abuse_daily_limit"
        assert "too many coupon attempts today" in result["message"].lower()
    
    @pytest.mark.asyncio
    async def test_coupon_abuse_detection_rapid_attempts(self, security_service):
        """Test coupon abuse detection for rapid attempts"""
        mock_redis = AsyncMock()
        security_service._get_redis = AsyncMock(return_value=mock_redis)
        
        # Simulate under daily limit but rapid attempts
        mock_redis.zcard.return_value = 1  # Under daily limit
        mock_redis.zcount.return_value = 2  # 2 attempts in 5 minutes
        
        result = await security_service.detect_coupon_abuse("user:123", "SAVE20")
        
        assert result["blocked"] is True
        assert result["reason"] == "coupon_abuse_rate_limit"
    
    @pytest.mark.asyncio
    async def test_price_tampering_detection(self, security_service):
        """Test price tampering detection"""
        mock_redis = AsyncMock()
        security_service._get_redis = AsyncMock(return_value=mock_redis)
        
        # Mock first tampering attempt
        mock_redis.zcard.return_value = 1
        
        submitted_prices = {"item1": 10.00, "item2": 15.50}
        actual_prices = {"item1": 12.00, "item2": 15.50}  # item1 tampered
        
        result = await security_service.detect_price_tampering(
            "user:123", submitted_prices, actual_prices
        )
        
        assert result["blocked"] is True
        assert result["reason"] == "price_validation_failed"
        assert len(result["tampered_items"]) == 1
        assert result["tampered_items"][0]["item_id"] == "item1"
    
    @pytest.mark.asyncio
    async def test_price_tampering_account_suspension(self, security_service):
        """Test account suspension after repeated price tampering"""
        mock_redis = AsyncMock()
        security_service._get_redis = AsyncMock(return_value=mock_redis)
        
        # Mock 3rd tampering attempt (suspension threshold)
        mock_redis.zcard.return_value = 3
        
        submitted_prices = {"item1": 10.00}
        actual_prices = {"item1": 12.00}
        
        result = await security_service.detect_price_tampering(
            "user:123", submitted_prices, actual_prices
        )
        
        assert result["blocked"] is True
        assert result["reason"] == "account_suspended"
        assert "suspended" in result["message"].lower()
    
    @pytest.mark.asyncio
    async def test_checkout_abuse_detection(self, security_service):
        """Test checkout abuse detection"""
        mock_redis = AsyncMock()
        security_service._get_redis = AsyncMock(return_value=mock_redis)
        
        # Simulate 5 checkout attempts in 10 minutes (at limit)
        mock_redis.zcard.return_value = 5
        
        result = await security_service.detect_checkout_abuse("user:123")
        
        assert result["blocked"] is True
        assert result["reason"] == "checkout_abuse"
        assert "too many checkout attempts" in result["message"].lower()


class TestRateLimitService:
    """Test rate limiting service"""
    
    @pytest.fixture
    def rate_limit_service(self):
        """Create rate limit service instance"""
        return RateLimitService()
    
    @pytest.mark.asyncio
    async def test_rate_limit_within_limit(self, rate_limit_service):
        """Test rate limiting when within limits"""
        mock_redis = AsyncMock()
        rate_limit_service._get_redis = AsyncMock(return_value=mock_redis)
        
        # Mock Redis responses for within limit
        mock_redis.zcard.return_value = 2  # 2 requests in window
        
        result = await rate_limit_service.check_rate_limit(
            "user:123", "auth_login", custom_limit=5
        )
        
        assert result["allowed"] is True
        assert result["limit"] == 5
        assert result["remaining"] == 2  # 5 - 2 - 1 = 2
    
    @pytest.mark.asyncio
    async def test_rate_limit_exceeded(self, rate_limit_service):
        """Test rate limiting when limit exceeded"""
        mock_redis = AsyncMock()
        rate_limit_service._get_redis = AsyncMock(return_value=mock_redis)
        
        # Mock Redis responses for exceeded limit
        mock_redis.zcard.return_value = 5  # At limit
        mock_redis.zrange.return_value = [(b"123456789", 1234567890)]
        
        result = await rate_limit_service.check_rate_limit(
            "user:123", "auth_login", custom_limit=5
        )
        
        assert result["allowed"] is False
        assert result["limit"] == 5
        assert result["remaining"] == 0
        assert result["retry_after"] > 0


class TestSecurityConfig:
    """Test security configuration"""
    
    def test_get_rate_limit(self):
        """Test getting rate limits from config"""
        assert security_settings.get_rate_limit("auth_login") == 5
        assert security_settings.get_rate_limit("checkout") == 3
        assert security_settings.get_rate_limit("unknown") == 100  # default
    
    def test_get_endpoint_category(self):
        """Test endpoint categorization"""
        assert security_settings.get_endpoint_category("/auth/login") == "auth_login"
        assert security_settings.get_endpoint_category("/cart/add") == "cart_operations"
        assert security_settings.get_endpoint_category("/unknown/path") == "api_general"
    
    def test_is_security_endpoint(self):
        """Test security endpoint detection"""
        assert security_settings.is_security_endpoint("/cart/promocode", "coupon_validation")
        assert security_settings.is_security_endpoint("/orders/checkout", "checkout")
        assert not security_settings.is_security_endpoint("/products/", "checkout")


if __name__ == "__main__":
    pytest.main([__file__])