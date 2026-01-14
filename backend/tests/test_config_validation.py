"""
Tests for configuration validation using Pydantic models

Feature: application-error-fixes
Tests configuration validation implementation from task 5.1
"""

import os
import pytest
from pydantic import ValidationError
from core.config import (
    DatabaseConfig,
    RedisConfig,
    KafkaConfig,
    SecurityConfig,
    ApplicationConfig,
    PydanticConfigValidator
)


class TestDatabaseConfig:
    """Test database configuration validation"""
    
    def test_valid_database_config(self, monkeypatch):
        """Test that valid database configuration passes validation"""
        monkeypatch.setenv('POSTGRES_USER', 'testuser')
        monkeypatch.setenv('POSTGRES_PASSWORD', 'testpassword123')
        monkeypatch.setenv('POSTGRES_SERVER', 'localhost')
        monkeypatch.setenv('POSTGRES_PORT', '5432')
        monkeypatch.setenv('POSTGRES_DB', 'testdb')
        
        config = DatabaseConfig()
        assert config.POSTGRES_USER == 'testuser'
        assert config.POSTGRES_PASSWORD == 'testpassword123'
    
    def test_password_too_short(self, monkeypatch):
        """Test that short passwords are rejected"""
        monkeypatch.setenv('POSTGRES_USER', 'testuser')
        monkeypatch.setenv('POSTGRES_PASSWORD', 'short')
        
        with pytest.raises(ValidationError) as exc_info:
            DatabaseConfig()
        
        assert 'at least 8 characters' in str(exc_info.value)
    
    def test_invalid_db_url_format(self, monkeypatch):
        """Test that invalid database URL format is rejected"""
        monkeypatch.setenv('POSTGRES_PASSWORD', 'testpassword123')
        monkeypatch.setenv('POSTGRES_DB_URL', 'mysql://invalid')
        
        with pytest.raises(ValidationError) as exc_info:
            DatabaseConfig()
        
        assert 'postgresql' in str(exc_info.value).lower()
    
    def test_invalid_port_range(self, monkeypatch):
        """Test that invalid port numbers are rejected"""
        monkeypatch.setenv('POSTGRES_PASSWORD', 'testpassword123')
        monkeypatch.setenv('POSTGRES_PORT', '99999')
        
        with pytest.raises(ValidationError) as exc_info:
            DatabaseConfig()
        
        assert 'less than or equal to 65535' in str(exc_info.value)


class TestRedisConfig:
    """Test Redis configuration validation"""
    
    def test_valid_redis_config(self, monkeypatch):
        """Test that valid Redis configuration passes validation"""
        monkeypatch.setenv('REDIS_URL', 'redis://localhost:6379/0')
        
        config = RedisConfig()
        assert config.REDIS_URL == 'redis://localhost:6379/0'
        assert config.REDIS_CACHE_ENABLED is True
    
    def test_invalid_redis_url(self, monkeypatch):
        """Test that invalid Redis URL is rejected"""
        monkeypatch.setenv('REDIS_URL', 'http://localhost:6379')
        
        with pytest.raises(ValidationError) as exc_info:
            RedisConfig()
        
        assert 'redis://' in str(exc_info.value)
    
    def test_cache_ttl_too_low(self, monkeypatch):
        """Test that cache TTL below minimum is rejected"""
        monkeypatch.setenv('REDIS_CACHE_TTL', '30')
        
        with pytest.raises(ValidationError) as exc_info:
            RedisConfig()
        
        assert 'greater than or equal to 60' in str(exc_info.value)


class TestKafkaConfig:
    """Test Kafka configuration validation"""
    
    def test_valid_kafka_config(self, monkeypatch):
        """Test that valid Kafka configuration passes validation"""
        monkeypatch.setenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
        
        config = KafkaConfig()
        assert config.KAFKA_BOOTSTRAP_SERVERS == 'localhost:9092'
        assert config.KAFKA_TOPIC_EMAIL == 'banwee-email-notifications'
    
    def test_empty_bootstrap_servers(self, monkeypatch):
        """Test that empty bootstrap servers are rejected"""
        monkeypatch.setenv('KAFKA_BOOTSTRAP_SERVERS', '')
        
        with pytest.raises(ValidationError) as exc_info:
            KafkaConfig()
        
        assert 'cannot be empty' in str(exc_info.value)
    
    def test_invalid_poll_records(self, monkeypatch):
        """Test that invalid poll records value is rejected"""
        monkeypatch.setenv('KAFKA_MAX_POLL_RECORDS', '0')
        
        with pytest.raises(ValidationError) as exc_info:
            KafkaConfig()
        
        assert 'greater than or equal to 1' in str(exc_info.value)


class TestSecurityConfig:
    """Test security configuration validation"""
    
    def test_valid_security_config(self, monkeypatch):
        """Test that valid security configuration passes validation"""
        monkeypatch.setenv('SECRET_KEY', 'a' * 32)
        monkeypatch.setenv('STRIPE_SECRET_KEY', 'sk_test_' + 'a' * 99)
        monkeypatch.setenv('STRIPE_WEBHOOK_SECRET', 'whsec_test123456')
        
        config = SecurityConfig()
        assert len(config.SECRET_KEY) >= 32
        assert config.STRIPE_SECRET_KEY.startswith('sk_test_')
    
    def test_secret_key_too_short(self, monkeypatch):
        """Test that short secret key is rejected"""
        monkeypatch.setenv('SECRET_KEY', 'short')
        monkeypatch.setenv('STRIPE_SECRET_KEY', 'sk_test_' + 'a' * 99)
        monkeypatch.setenv('STRIPE_WEBHOOK_SECRET', 'whsec_test')
        
        with pytest.raises(ValidationError) as exc_info:
            SecurityConfig()
        
        assert 'at least 32 characters' in str(exc_info.value)
    
    def test_invalid_stripe_key_format(self, monkeypatch):
        """Test that invalid Stripe key format is rejected"""
        monkeypatch.setenv('SECRET_KEY', 'a' * 32)
        monkeypatch.setenv('STRIPE_SECRET_KEY', 'invalid_key')
        monkeypatch.setenv('STRIPE_WEBHOOK_SECRET', 'whsec_test')
        
        with pytest.raises(ValidationError) as exc_info:
            SecurityConfig()
        
        assert 'sk_test_' in str(exc_info.value) or 'sk_live_' in str(exc_info.value)
    
    def test_invalid_webhook_secret_format(self, monkeypatch):
        """Test that invalid webhook secret format is rejected"""
        monkeypatch.setenv('SECRET_KEY', 'a' * 32)
        monkeypatch.setenv('STRIPE_SECRET_KEY', 'sk_test_' + 'a' * 99)
        monkeypatch.setenv('STRIPE_WEBHOOK_SECRET', 'invalid')
        
        with pytest.raises(ValidationError) as exc_info:
            SecurityConfig()
        
        assert 'whsec_' in str(exc_info.value)
    
    def test_production_requires_live_stripe_keys(self, monkeypatch):
        """Test that production environment requires live Stripe keys"""
        monkeypatch.setenv('ENVIRONMENT', 'production')
        monkeypatch.setenv('SECRET_KEY', 'a' * 64)
        monkeypatch.setenv('STRIPE_SECRET_KEY', 'sk_test_' + 'a' * 99)
        monkeypatch.setenv('STRIPE_WEBHOOK_SECRET', 'whsec_test')
        
        with pytest.raises(ValidationError) as exc_info:
            SecurityConfig()
        
        assert 'live' in str(exc_info.value).lower()


class TestApplicationConfig:
    """Test application configuration validation"""
    
    def test_valid_application_config(self, monkeypatch):
        """Test that valid application configuration passes validation"""
        monkeypatch.setenv('ENVIRONMENT', 'local')
        monkeypatch.setenv('FRONTEND_URL', 'http://localhost:5173')
        monkeypatch.setenv('BACKEND_URL', 'http://localhost:8000')
        
        config = ApplicationConfig()
        assert config.ENVIRONMENT == 'local'
        assert config.FRONTEND_URL == 'http://localhost:5173'
    
    def test_invalid_url_format(self, monkeypatch):
        """Test that invalid URL format is rejected"""
        monkeypatch.setenv('FRONTEND_URL', 'invalid-url')
        
        with pytest.raises(ValidationError) as exc_info:
            ApplicationConfig()
        
        assert 'http://' in str(exc_info.value) or 'https://' in str(exc_info.value)
    
    def test_invalid_environment_type(self, monkeypatch):
        """Test that invalid environment type is rejected"""
        monkeypatch.setenv('ENVIRONMENT', 'invalid')
        
        with pytest.raises(ValidationError) as exc_info:
            ApplicationConfig()
        
        assert 'local' in str(exc_info.value) or 'staging' in str(exc_info.value)


class TestPydanticConfigValidator:
    """Test the comprehensive Pydantic configuration validator"""
    
    def test_validator_with_valid_config(self, monkeypatch):
        """Test that validator passes with valid configuration"""
        # Set all required environment variables
        monkeypatch.setenv('POSTGRES_PASSWORD', 'testpassword123')
        monkeypatch.setenv('REDIS_URL', 'redis://localhost:6379/0')
        monkeypatch.setenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
        monkeypatch.setenv('SECRET_KEY', 'a' * 32)
        monkeypatch.setenv('STRIPE_SECRET_KEY', 'sk_test_' + 'a' * 99)
        monkeypatch.setenv('STRIPE_WEBHOOK_SECRET', 'whsec_test123456')
        monkeypatch.setenv('FRONTEND_URL', 'http://localhost:5173')
        monkeypatch.setenv('BACKEND_URL', 'http://localhost:8000')
        
        validator = PydanticConfigValidator()
        result = validator.validate_all()
        
        assert result.is_valid is True
        assert len(result.errors) == 0
    
    def test_validator_with_missing_required_fields(self, monkeypatch):
        """Test that validator fails with missing required fields"""
        # Don't set required fields
        monkeypatch.delenv('SECRET_KEY', raising=False)
        monkeypatch.delenv('STRIPE_SECRET_KEY', raising=False)
        
        validator = PydanticConfigValidator()
        result = validator.validate_all()
        
        assert result.is_valid is False
        assert len(result.errors) > 0
    
    def test_validator_collects_multiple_errors(self, monkeypatch):
        """Test that validator collects multiple validation errors"""
        monkeypatch.setenv('SECRET_KEY', 'short')  # Too short
        monkeypatch.setenv('STRIPE_SECRET_KEY', 'invalid')  # Invalid format
        monkeypatch.setenv('POSTGRES_PASSWORD', 'short')  # Too short
        
        validator = PydanticConfigValidator()
        result = validator.validate_all()
        
        assert result.is_valid is False
        assert len(result.errors) >= 3  # At least 3 errors


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
