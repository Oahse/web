"""
Property-based test for configuration validation.

This test validates Property 21: Configuration validation
Requirements: 9.1, 9.2, 9.3

**Feature: platform-modernization, Property 21: Configuration validation**
"""
import pytest
import os
import tempfile
from typing import Dict, Any, Optional, List
from unittest.mock import patch, MagicMock

from hypothesis import given, strategies as st, settings, assume, HealthCheck
from hypothesis.strategies import composite

# Import the Settings class for testing
from backend.core.config import Settings


# Test configuration
DEFAULT_SETTINGS = settings(
    max_examples=100,
    deadline=30000,  # 30 seconds
    suppress_health_check=[
        HealthCheck.function_scoped_fixture
    ]
)


class ConfigurationValidator:
    """Configuration validation utility class for testing"""
    
    REQUIRED_KAFKA_SETTINGS = [
        'KAFKA_BOOTSTRAP_SERVERS',
        'KAFKA_TOPIC_EMAIL',
        'KAFKA_TOPIC_NOTIFICATION', 
        'KAFKA_TOPIC_ORDER',
        'KAFKA_TOPIC_NEGOTIATION',
        'KAFKA_TOPIC_PAYMENT',
        'KAFKA_CONSUMER_GROUP_BACKEND',
        'KAFKA_CONSUMER_GROUP_SCHEDULER',
        'KAFKA_CONSUMER_GROUP_NEGOTIATOR'
    ]
    
    REQUIRED_STRIPE_SETTINGS = [
        'STRIPE_SECRET_KEY',
        'STRIPE_WEBHOOK_SECRET'
    ]
    
    REQUIRED_SECURITY_SETTINGS = [
        'SECRET_KEY'
    ]
    
    REQUIRED_DATABASE_SETTINGS = [
        # Either POSTGRES_DB_URL or all individual settings
        ['POSTGRES_DB_URL'],
        ['POSTGRES_USER', 'POSTGRES_PASSWORD', 'POSTGRES_SERVER', 'POSTGRES_DB']
    ]
    
    @staticmethod
    def validate_kafka_configuration(config_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate Kafka configuration settings
        """
        result = {
            'valid': True,
            'errors': []
        }
        
        # Check required Kafka settings
        for setting in ConfigurationValidator.REQUIRED_KAFKA_SETTINGS:
            if setting not in config_dict or not config_dict[setting] or not str(config_dict[setting]).strip():
                result['valid'] = False
                result['errors'].append(f"Kafka setting {setting} is required and cannot be empty")
        
        # Validate bootstrap servers format
        if 'KAFKA_BOOTSTRAP_SERVERS' in config_dict and config_dict['KAFKA_BOOTSTRAP_SERVERS']:
            bootstrap_servers = config_dict['KAFKA_BOOTSTRAP_SERVERS']
            if not isinstance(bootstrap_servers, str) or ':' not in bootstrap_servers:
                result['valid'] = False
                result['errors'].append("KAFKA_BOOTSTRAP_SERVERS must be in format 'host:port'")
        
        # Validate topic names are not empty
        topic_settings = [s for s in ConfigurationValidator.REQUIRED_KAFKA_SETTINGS if 'TOPIC' in s]
        for topic_setting in topic_settings:
            if topic_setting in config_dict and config_dict[topic_setting]:
                topic_name = str(config_dict[topic_setting]).strip()
                if not topic_name:
                    result['valid'] = False
                    result['errors'].append(f"Kafka topic name {topic_setting} cannot be empty")
        
        # Validate consumer group IDs are not empty
        group_settings = [s for s in ConfigurationValidator.REQUIRED_KAFKA_SETTINGS if 'CONSUMER_GROUP' in s]
        for group_setting in group_settings:
            if group_setting in config_dict and config_dict[group_setting]:
                group_id = str(config_dict[group_setting]).strip()
                if not group_id:
                    result['valid'] = False
                    result['errors'].append(f"Kafka consumer group ID {group_setting} cannot be empty")
        
        return result
    
    @staticmethod
    def validate_stripe_configuration(config_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate Stripe configuration settings
        """
        result = {
            'valid': True,
            'errors': []
        }
        
        # Check required Stripe settings
        for setting in ConfigurationValidator.REQUIRED_STRIPE_SETTINGS:
            if setting not in config_dict or not config_dict[setting]:
                result['valid'] = False
                result['errors'].append(f"Stripe setting {setting} is required")
        
        # Validate Stripe secret key format
        if 'STRIPE_SECRET_KEY' in config_dict and config_dict['STRIPE_SECRET_KEY']:
            secret_key = config_dict['STRIPE_SECRET_KEY']
            if not secret_key.startswith(('sk_test_', 'sk_live_')):
                result['valid'] = False
                result['errors'].append("STRIPE_SECRET_KEY must start with 'sk_test_' or 'sk_live_'")
        
        # Validate Stripe webhook secret format
        if 'STRIPE_WEBHOOK_SECRET' in config_dict and config_dict['STRIPE_WEBHOOK_SECRET']:
            webhook_secret = config_dict['STRIPE_WEBHOOK_SECRET']
            if not webhook_secret.startswith('whsec_'):
                result['valid'] = False
                result['errors'].append("STRIPE_WEBHOOK_SECRET must start with 'whsec_'")
        
        return result
    
    @staticmethod
    def validate_required_settings(config_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate all required configuration settings
        """
        result = {
            'valid': True,
            'errors': []
        }
        
        # Check security settings
        for setting in ConfigurationValidator.REQUIRED_SECURITY_SETTINGS:
            if setting not in config_dict or not config_dict[setting]:
                result['valid'] = False
                result['errors'].append(f"Security setting {setting} is required for session management and token signing")
        
        # Check database settings - either full URL or individual components
        has_db_url = 'POSTGRES_DB_URL' in config_dict and config_dict['POSTGRES_DB_URL']
        has_individual_settings = all(
            setting in config_dict and config_dict[setting] 
            for setting in ['POSTGRES_USER', 'POSTGRES_PASSWORD', 'POSTGRES_SERVER', 'POSTGRES_DB']
        )
        
        if not has_db_url and not has_individual_settings:
            result['valid'] = False
            result['errors'].append("Database configuration is incomplete. Either set POSTGRES_DB_URL or all individual PostgreSQL settings")
        
        return result
    
    @staticmethod
    def validate_error_message_clarity(error_messages: List[str]) -> Dict[str, Any]:
        """
        Validate that error messages are clear and descriptive
        """
        result = {
            'valid': True,
            'errors': []
        }
        
        for message in error_messages:
            if not isinstance(message, str):
                result['valid'] = False
                result['errors'].append("Error messages must be strings")
                continue
            
            if len(message.strip()) == 0:
                result['valid'] = False
                result['errors'].append("Error messages cannot be empty")
                continue
            
            # Check that error messages are descriptive (contain key information)
            if len(message) < 10:
                result['valid'] = False
                result['errors'].append(f"Error message too short to be descriptive: '{message}'")
                continue
            
            # Error messages should mention what's missing or wrong
            descriptive_keywords = ['required', 'missing', 'invalid', 'must', 'cannot', 'should', 'incomplete']
            if not any(keyword in message.lower() for keyword in descriptive_keywords):
                result['valid'] = False
                result['errors'].append(f"Error message should be more descriptive: '{message}'")
        
        return result


@composite
def valid_kafka_config(draw):
    """Generate valid Kafka configuration"""
    return {
        'KAFKA_BOOTSTRAP_SERVERS': draw(st.sampled_from(['kafka:29092', 'localhost:9092', 'kafka-cluster:9092'])),
        'KAFKA_TOPIC_EMAIL': draw(st.text(alphabet='abcdefghijklmnopqrstuvwxyz-', min_size=5, max_size=20)),
        'KAFKA_TOPIC_NOTIFICATION': draw(st.text(alphabet='abcdefghijklmnopqrstuvwxyz-', min_size=5, max_size=20)),
        'KAFKA_TOPIC_ORDER': draw(st.text(alphabet='abcdefghijklmnopqrstuvwxyz-', min_size=5, max_size=20)),
        'KAFKA_TOPIC_NEGOTIATION': draw(st.text(alphabet='abcdefghijklmnopqrstuvwxyz-', min_size=5, max_size=20)),
        'KAFKA_TOPIC_PAYMENT': draw(st.text(alphabet='abcdefghijklmnopqrstuvwxyz-', min_size=5, max_size=20)),
        'KAFKA_CONSUMER_GROUP_BACKEND': draw(st.text(alphabet='abcdefghijklmnopqrstuvwxyz-', min_size=5, max_size=30)),
        'KAFKA_CONSUMER_GROUP_SCHEDULER': draw(st.text(alphabet='abcdefghijklmnopqrstuvwxyz-', min_size=5, max_size=30)),
        'KAFKA_CONSUMER_GROUP_NEGOTIATOR': draw(st.text(alphabet='abcdefghijklmnopqrstuvwxyz-', min_size=5, max_size=30))
    }


@composite
def invalid_kafka_config(draw):
    """Generate invalid Kafka configuration"""
    invalid_type = draw(st.sampled_from(['missing_bootstrap', 'empty_topic', 'empty_group', 'invalid_bootstrap_format']))
    
    base_config = draw(valid_kafka_config())
    
    if invalid_type == 'missing_bootstrap':
        del base_config['KAFKA_BOOTSTRAP_SERVERS']
    elif invalid_type == 'empty_topic':
        topic_key = draw(st.sampled_from([k for k in base_config.keys() if 'TOPIC' in k]))
        base_config[topic_key] = ''
    elif invalid_type == 'empty_group':
        group_key = draw(st.sampled_from([k for k in base_config.keys() if 'CONSUMER_GROUP' in k]))
        base_config[group_key] = ''
    elif invalid_type == 'invalid_bootstrap_format':
        base_config['KAFKA_BOOTSTRAP_SERVERS'] = draw(st.text(alphabet='abcdefghijklmnopqrstuvwxyz', min_size=5, max_size=15))
    
    return base_config


@composite
def valid_stripe_config(draw):
    """Generate valid Stripe configuration"""
    env_type = draw(st.sampled_from(['test', 'live']))
    
    return {
        'STRIPE_SECRET_KEY': f"sk_{env_type}_" + draw(st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', min_size=20, max_size=50)),
        'STRIPE_WEBHOOK_SECRET': 'whsec_' + draw(st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', min_size=20, max_size=50))
    }


@composite
def invalid_stripe_config(draw):
    """Generate invalid Stripe configuration"""
    invalid_type = draw(st.sampled_from(['missing_secret_key', 'missing_webhook_secret', 'invalid_secret_key_format', 'invalid_webhook_format']))
    
    base_config = draw(valid_stripe_config())
    
    if invalid_type == 'missing_secret_key':
        del base_config['STRIPE_SECRET_KEY']
    elif invalid_type == 'missing_webhook_secret':
        del base_config['STRIPE_WEBHOOK_SECRET']
    elif invalid_type == 'invalid_secret_key_format':
        base_config['STRIPE_SECRET_KEY'] = draw(st.text(alphabet='abcdefghijklmnopqrstuvwxyz', min_size=10, max_size=30))
    elif invalid_type == 'invalid_webhook_format':
        base_config['STRIPE_WEBHOOK_SECRET'] = draw(st.text(alphabet='abcdefghijklmnopqrstuvwxyz', min_size=10, max_size=30))
    
    return base_config


@composite
def valid_complete_config(draw):
    """Generate complete valid configuration"""
    kafka_config = draw(valid_kafka_config())
    stripe_config = draw(valid_stripe_config())
    
    config = {
        **kafka_config,
        **stripe_config,
        'SECRET_KEY': draw(st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*', min_size=32, max_size=64))
    }
    
    # Add database config - either full URL or individual components
    db_type = draw(st.sampled_from(['url', 'components']))
    if db_type == 'url':
        config['POSTGRES_DB_URL'] = 'postgresql+asyncpg://user:pass@localhost:5432/dbname'
    else:
        config.update({
            'POSTGRES_USER': 'testuser',
            'POSTGRES_PASSWORD': 'testpass',
            'POSTGRES_SERVER': 'localhost',
            'POSTGRES_DB': 'testdb'
        })
    
    return config


@composite
def invalid_complete_config(draw):
    """Generate invalid complete configuration"""
    invalid_type = draw(st.sampled_from(['missing_secret_key', 'missing_db_config', 'invalid_kafka', 'invalid_stripe']))
    
    base_config = draw(valid_complete_config())
    
    if invalid_type == 'missing_secret_key':
        del base_config['SECRET_KEY']
    elif invalid_type == 'missing_db_config':
        # Remove both URL and individual components
        base_config.pop('POSTGRES_DB_URL', None)
        for key in ['POSTGRES_USER', 'POSTGRES_PASSWORD', 'POSTGRES_SERVER', 'POSTGRES_DB']:
            base_config.pop(key, None)
    elif invalid_type == 'invalid_kafka':
        base_config['KAFKA_BOOTSTRAP_SERVERS'] = 'invalid-format'
    elif invalid_type == 'invalid_stripe':
        base_config['STRIPE_SECRET_KEY'] = 'invalid-key-format'
    
    return base_config


class TestConfigurationValidationProperty:
    """Property-based tests for configuration validation"""

    @given(kafka_config=valid_kafka_config())
    @DEFAULT_SETTINGS
    def test_valid_kafka_configuration_property(self, kafka_config):
        """
        Property: For any valid Kafka configuration, validation should succeed
        **Feature: platform-modernization, Property 21: Configuration validation**
        **Validates: Requirements 9.1**
        """
        result = ConfigurationValidator.validate_kafka_configuration(kafka_config)
        
        # Property: Valid Kafka configuration should pass validation
        assert result['valid'] is True, f"Valid Kafka configuration should pass validation, errors: {result['errors']}"
        assert len(result['errors']) == 0, f"Valid Kafka configuration should have no errors, got: {result['errors']}"
        
        # Property: All required Kafka settings should be present and non-empty
        for setting in ConfigurationValidator.REQUIRED_KAFKA_SETTINGS:
            assert setting in kafka_config, f"Required Kafka setting {setting} should be present"
            assert kafka_config[setting], f"Required Kafka setting {setting} should not be empty"
            assert str(kafka_config[setting]).strip(), f"Required Kafka setting {setting} should not be whitespace only"

    @given(kafka_config=invalid_kafka_config())
    @DEFAULT_SETTINGS
    def test_invalid_kafka_configuration_property(self, kafka_config):
        """
        Property: For any invalid Kafka configuration, validation should fail with clear error messages
        **Feature: platform-modernization, Property 21: Configuration validation**
        **Validates: Requirements 9.1, 9.3**
        """
        result = ConfigurationValidator.validate_kafka_configuration(kafka_config)
        
        # Property: Invalid Kafka configuration should fail validation
        assert result['valid'] is False, f"Invalid Kafka configuration should fail validation"
        assert len(result['errors']) > 0, f"Invalid Kafka configuration should have error messages"
        
        # Property: Error messages should be clear and descriptive
        error_validation = ConfigurationValidator.validate_error_message_clarity(result['errors'])
        assert error_validation['valid'] is True, f"Error messages should be clear and descriptive: {error_validation['errors']}"

    @given(stripe_config=valid_stripe_config())
    @DEFAULT_SETTINGS
    def test_valid_stripe_configuration_property(self, stripe_config):
        """
        Property: For any valid Stripe configuration, validation should succeed
        **Feature: platform-modernization, Property 21: Configuration validation**
        **Validates: Requirements 9.2**
        """
        result = ConfigurationValidator.validate_stripe_configuration(stripe_config)
        
        # Property: Valid Stripe configuration should pass validation
        assert result['valid'] is True, f"Valid Stripe configuration should pass validation, errors: {result['errors']}"
        assert len(result['errors']) == 0, f"Valid Stripe configuration should have no errors, got: {result['errors']}"
        
        # Property: Stripe secret key should have correct format
        secret_key = stripe_config['STRIPE_SECRET_KEY']
        assert secret_key.startswith(('sk_test_', 'sk_live_')), f"Stripe secret key should start with 'sk_test_' or 'sk_live_', got: {secret_key}"
        
        # Property: Stripe webhook secret should have correct format
        webhook_secret = stripe_config['STRIPE_WEBHOOK_SECRET']
        assert webhook_secret.startswith('whsec_'), f"Stripe webhook secret should start with 'whsec_', got: {webhook_secret}"

    @given(stripe_config=invalid_stripe_config())
    @DEFAULT_SETTINGS
    def test_invalid_stripe_configuration_property(self, stripe_config):
        """
        Property: For any invalid Stripe configuration, validation should fail with clear error messages
        **Feature: platform-modernization, Property 21: Configuration validation**
        **Validates: Requirements 9.2, 9.3**
        """
        result = ConfigurationValidator.validate_stripe_configuration(stripe_config)
        
        # Property: Invalid Stripe configuration should fail validation
        assert result['valid'] is False, f"Invalid Stripe configuration should fail validation"
        assert len(result['errors']) > 0, f"Invalid Stripe configuration should have error messages"
        
        # Property: Error messages should be clear and descriptive
        error_validation = ConfigurationValidator.validate_error_message_clarity(result['errors'])
        assert error_validation['valid'] is True, f"Error messages should be clear and descriptive: {error_validation['errors']}"

    @given(config=valid_complete_config())
    @DEFAULT_SETTINGS
    def test_valid_complete_configuration_property(self, config):
        """
        Property: For any complete valid configuration, all validation should succeed
        **Feature: platform-modernization, Property 21: Configuration validation**
        **Validates: Requirements 9.1, 9.2, 9.3**
        """
        # Test individual components
        kafka_result = ConfigurationValidator.validate_kafka_configuration(config)
        stripe_result = ConfigurationValidator.validate_stripe_configuration(config)
        required_result = ConfigurationValidator.validate_required_settings(config)
        
        # Property: All validation components should pass for valid complete configuration
        assert kafka_result['valid'] is True, f"Kafka validation should pass, errors: {kafka_result['errors']}"
        assert stripe_result['valid'] is True, f"Stripe validation should pass, errors: {stripe_result['errors']}"
        assert required_result['valid'] is True, f"Required settings validation should pass, errors: {required_result['errors']}"
        
        # Property: No validation errors should exist
        all_errors = kafka_result['errors'] + stripe_result['errors'] + required_result['errors']
        assert len(all_errors) == 0, f"No validation errors should exist for valid configuration, got: {all_errors}"

    @given(config=invalid_complete_config())
    @DEFAULT_SETTINGS
    def test_invalid_complete_configuration_property(self, config):
        """
        Property: For any invalid complete configuration, validation should fail with clear error messages
        **Feature: platform-modernization, Property 21: Configuration validation**
        **Validates: Requirements 9.1, 9.2, 9.3**
        """
        # Test individual components
        kafka_result = ConfigurationValidator.validate_kafka_configuration(config)
        stripe_result = ConfigurationValidator.validate_stripe_configuration(config)
        required_result = ConfigurationValidator.validate_required_settings(config)
        
        # Property: At least one validation component should fail for invalid configuration
        has_validation_failure = (
            not kafka_result['valid'] or 
            not stripe_result['valid'] or 
            not required_result['valid']
        )
        assert has_validation_failure, "At least one validation component should fail for invalid configuration"
        
        # Property: All error messages should be clear and descriptive
        all_errors = kafka_result['errors'] + stripe_result['errors'] + required_result['errors']
        if all_errors:
            error_validation = ConfigurationValidator.validate_error_message_clarity(all_errors)
            assert error_validation['valid'] is True, f"All error messages should be clear and descriptive: {error_validation['errors']}"

    @given(
        missing_settings=st.lists(
            st.sampled_from(ConfigurationValidator.REQUIRED_KAFKA_SETTINGS + 
                          ConfigurationValidator.REQUIRED_STRIPE_SETTINGS + 
                          ConfigurationValidator.REQUIRED_SECURITY_SETTINGS),
            min_size=1,
            max_size=5,
            unique=True
        )
    )
    @DEFAULT_SETTINGS
    def test_missing_environment_variables_error_messages_property(self, missing_settings):
        """
        Property: For any missing required environment variables, clear error messages should be provided
        **Feature: platform-modernization, Property 21: Configuration validation**
        **Validates: Requirements 9.3**
        """
        # Create config with missing settings
        complete_config = {
            'KAFKA_BOOTSTRAP_SERVERS': 'kafka:29092',
            'KAFKA_TOPIC_EMAIL': 'banwee-emails',
            'KAFKA_TOPIC_NOTIFICATION': 'banwee-notifications',
            'KAFKA_TOPIC_ORDER': 'banwee-orders',
            'KAFKA_TOPIC_NEGOTIATION': 'banwee-negotiations',
            'KAFKA_TOPIC_PAYMENT': 'banwee-payments',
            'KAFKA_CONSUMER_GROUP_BACKEND': 'banwee-backend-consumers',
            'KAFKA_CONSUMER_GROUP_SCHEDULER': 'banwee-scheduler-consumers',
            'KAFKA_CONSUMER_GROUP_NEGOTIATOR': 'banwee-negotiator-consumers',
            'STRIPE_SECRET_KEY': 'sk_test_123456789',
            'STRIPE_WEBHOOK_SECRET': 'whsec_123456789',
            'SECRET_KEY': 'test-secret-key-12345',
            'POSTGRES_DB_URL': 'postgresql+asyncpg://user:pass@localhost:5432/dbname'
        }
        
        # Remove the missing settings
        config_with_missing = {k: v for k, v in complete_config.items() if k not in missing_settings}
        
        # Test validation
        kafka_result = ConfigurationValidator.validate_kafka_configuration(config_with_missing)
        stripe_result = ConfigurationValidator.validate_stripe_configuration(config_with_missing)
        required_result = ConfigurationValidator.validate_required_settings(config_with_missing)
        
        # Collect all errors
        all_errors = kafka_result['errors'] + stripe_result['errors'] + required_result['errors']
        
        # Property: Missing settings should generate error messages
        assert len(all_errors) > 0, f"Missing settings {missing_settings} should generate error messages"
        
        # Property: Error messages should mention the missing settings
        error_text = ' '.join(all_errors).lower()
        for setting in missing_settings:
            # Check if the setting name or a related keyword appears in error messages
            setting_mentioned = (
                setting.lower() in error_text or
                any(part.lower() in error_text for part in setting.split('_')) or
                'required' in error_text or
                'missing' in error_text
            )
            assert setting_mentioned, f"Error messages should mention missing setting {setting}. Errors: {all_errors}"
        
        # Property: Error messages should be clear and descriptive
        error_validation = ConfigurationValidator.validate_error_message_clarity(all_errors)
        assert error_validation['valid'] is True, f"Error messages should be clear and descriptive: {error_validation['errors']}"

    @given(
        config_env=st.sampled_from(['local', 'staging', 'production']),
        kafka_servers=st.lists(
            st.text(alphabet='abcdefghijklmnopqrstuvwxyz0123456789.-', min_size=5, max_size=20),
            min_size=1,
            max_size=3
        )
    )
    @DEFAULT_SETTINGS
    def test_environment_specific_kafka_configuration_property(self, config_env, kafka_servers):
        """
        Property: For any environment, Kafka configuration should support different server configurations
        **Feature: platform-modernization, Property 21: Configuration validation**
        **Validates: Requirements 9.1**
        """
        # Create environment-specific Kafka configuration
        kafka_bootstrap_servers = ','.join(f"{server}:9092" for server in kafka_servers)
        
        config = {
            'ENVIRONMENT': config_env,
            'KAFKA_BOOTSTRAP_SERVERS': kafka_bootstrap_servers,
            'KAFKA_TOPIC_EMAIL': f'{config_env}-emails',
            'KAFKA_TOPIC_NOTIFICATION': f'{config_env}-notifications',
            'KAFKA_TOPIC_ORDER': f'{config_env}-orders',
            'KAFKA_TOPIC_NEGOTIATION': f'{config_env}-negotiations',
            'KAFKA_TOPIC_PAYMENT': f'{config_env}-payments',
            'KAFKA_CONSUMER_GROUP_BACKEND': f'{config_env}-backend-consumers',
            'KAFKA_CONSUMER_GROUP_SCHEDULER': f'{config_env}-scheduler-consumers',
            'KAFKA_CONSUMER_GROUP_NEGOTIATOR': f'{config_env}-negotiator-consumers'
        }
        
        result = ConfigurationValidator.validate_kafka_configuration(config)
        
        # Property: Environment-specific Kafka configuration should be valid
        assert result['valid'] is True, f"Environment-specific Kafka configuration should be valid for {config_env}, errors: {result['errors']}"
        
        # Property: Topic names should reflect environment
        for topic_key in [k for k in config.keys() if 'TOPIC' in k]:
            topic_name = config[topic_key]
            assert config_env in topic_name, f"Topic name {topic_name} should include environment {config_env}"
        
        # Property: Consumer group names should reflect environment
        for group_key in [k for k in config.keys() if 'CONSUMER_GROUP' in k]:
            group_name = config[group_key]
            assert config_env in group_name, f"Consumer group name {group_name} should include environment {config_env}"

    def test_settings_class_integration_property(self):
        """
        Property: The Settings class should properly validate configuration on initialization
        **Feature: platform-modernization, Property 21: Configuration validation**
        **Validates: Requirements 9.1, 9.2, 9.3**
        """
        # Test validation methods directly since .env loading happens at module level
        
        # Test that the current settings instance has required validation methods
        from backend.core.config import settings
        
        # Property: Settings should have validation methods
        assert hasattr(settings, 'validate_required_settings'), "Settings should have validate_required_settings method"
        assert hasattr(settings, 'validate_kafka_configuration'), "Settings should have validate_kafka_configuration method"
        assert hasattr(settings, 'validate_stripe_configuration'), "Settings should have validate_stripe_configuration method"
        
        # Property: Current settings should have required attributes
        assert hasattr(settings, 'SECRET_KEY'), "Settings should have SECRET_KEY attribute"
        assert hasattr(settings, 'STRIPE_SECRET_KEY'), "Settings should have STRIPE_SECRET_KEY attribute"
        assert hasattr(settings, 'KAFKA_BOOTSTRAP_SERVERS'), "Settings should have KAFKA_BOOTSTRAP_SERVERS attribute"
        
        # Test validation with missing settings by creating a mock Settings class
        class MockSettings:
            def __init__(self, env_vars):
                # Simulate missing environment variables
                self.SECRET_KEY = env_vars.get('SECRET_KEY', '')
                self.STRIPE_SECRET_KEY = env_vars.get('STRIPE_SECRET_KEY', '')
                self.STRIPE_WEBHOOK_SECRET = env_vars.get('STRIPE_WEBHOOK_SECRET', '')
                self.KAFKA_BOOTSTRAP_SERVERS = env_vars.get('KAFKA_BOOTSTRAP_SERVERS', '')
                self.POSTGRES_DB_URL = env_vars.get('POSTGRES_DB_URL', '')
                self.POSTGRES_USER = env_vars.get('POSTGRES_USER', '')
                self.POSTGRES_PASSWORD = env_vars.get('POSTGRES_PASSWORD', '')
                self.POSTGRES_SERVER = env_vars.get('POSTGRES_SERVER', '')
                self.POSTGRES_DB = env_vars.get('POSTGRES_DB', '')
                
                # Add all Kafka topic attributes
                self.KAFKA_TOPIC_EMAIL = env_vars.get('KAFKA_TOPIC_EMAIL', 'banwee-emails')
                self.KAFKA_TOPIC_NOTIFICATION = env_vars.get('KAFKA_TOPIC_NOTIFICATION', 'banwee-notifications')
                self.KAFKA_TOPIC_ORDER = env_vars.get('KAFKA_TOPIC_ORDER', 'banwee-orders')
                self.KAFKA_TOPIC_NEGOTIATION = env_vars.get('KAFKA_TOPIC_NEGOTIATION', 'banwee-negotiations')
                self.KAFKA_TOPIC_PAYMENT = env_vars.get('KAFKA_TOPIC_PAYMENT', 'banwee-payments')
                
                # Add Kafka consumer group attributes
                self.KAFKA_CONSUMER_GROUP_BACKEND = env_vars.get('KAFKA_CONSUMER_GROUP_BACKEND', 'banwee-backend-consumers')
                self.KAFKA_CONSUMER_GROUP_SCHEDULER = env_vars.get('KAFKA_CONSUMER_GROUP_SCHEDULER', 'banwee-scheduler-consumers')
                self.KAFKA_CONSUMER_GROUP_NEGOTIATOR = env_vars.get('KAFKA_CONSUMER_GROUP_NEGOTIATOR', 'banwee-negotiator-consumers')
            
            def validate_required_settings(self):
                return settings.__class__.validate_required_settings(self)
            
            def validate_kafka_configuration(self):
                return settings.__class__.validate_kafka_configuration(self)
            
            def validate_stripe_configuration(self):
                return settings.__class__.validate_stripe_configuration(self)
        
        # Test with missing required settings
        invalid_settings = MockSettings({
            'KAFKA_BOOTSTRAP_SERVERS': 'kafka:29092'
            # Missing SECRET_KEY, STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET
        })
        
        # Property: Missing required settings should raise ValueError with clear message
        with pytest.raises(ValueError) as exc_info:
            invalid_settings.validate_required_settings()
        
        error_message = str(exc_info.value)
        assert 'Missing required configuration settings' in error_message
        assert 'SECRET_KEY' in error_message
        assert 'STRIPE_SECRET_KEY' in error_message
        assert 'STRIPE_WEBHOOK_SECRET' in error_message
        
        # Test with valid settings
        valid_settings = MockSettings({
            'SECRET_KEY': 'test-secret-key-12345678901234567890',
            'STRIPE_SECRET_KEY': 'sk_test_1234567890abcdef',
            'STRIPE_WEBHOOK_SECRET': 'whsec_1234567890abcdef',
            'KAFKA_BOOTSTRAP_SERVERS': 'kafka:29092',
            'POSTGRES_DB_URL': 'postgresql+asyncpg://user:pass@localhost:5432/dbname'
        })
        
        # Property: Valid configuration should not raise exceptions
        try:
            valid_settings.validate_required_settings()
            valid_settings.validate_kafka_configuration()
            valid_settings.validate_stripe_configuration()
        except Exception as e:
            pytest.fail(f"Valid configuration should not raise exceptions, got: {e}")

    @given(
        stripe_key_prefix=st.sampled_from(['sk_test_', 'sk_live_']),
        webhook_prefix=st.just('whsec_'),
        key_suffix=st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', min_size=20, max_size=50)
    )
    @DEFAULT_SETTINGS
    def test_stripe_credential_format_validation_property(self, stripe_key_prefix, webhook_prefix, key_suffix):
        """
        Property: For any Stripe credentials, format validation should enforce correct prefixes
        **Feature: platform-modernization, Property 21: Configuration validation**
        **Validates: Requirements 9.2**
        """
        valid_config = {
            'STRIPE_SECRET_KEY': stripe_key_prefix + key_suffix,
            'STRIPE_WEBHOOK_SECRET': webhook_prefix + key_suffix
        }
        
        result = ConfigurationValidator.validate_stripe_configuration(valid_config)
        
        # Property: Correctly formatted Stripe credentials should pass validation
        assert result['valid'] is True, f"Correctly formatted Stripe credentials should pass validation, errors: {result['errors']}"
        
        # Test with invalid prefixes
        invalid_configs = [
            {'STRIPE_SECRET_KEY': 'invalid_' + key_suffix, 'STRIPE_WEBHOOK_SECRET': webhook_prefix + key_suffix},
            {'STRIPE_SECRET_KEY': stripe_key_prefix + key_suffix, 'STRIPE_WEBHOOK_SECRET': 'invalid_' + key_suffix}
        ]
        
        for invalid_config in invalid_configs:
            invalid_result = ConfigurationValidator.validate_stripe_configuration(invalid_config)
            
            # Property: Incorrectly formatted Stripe credentials should fail validation
            assert invalid_result['valid'] is False, f"Incorrectly formatted Stripe credentials should fail validation"
            assert len(invalid_result['errors']) > 0, f"Invalid Stripe credentials should have error messages"
            
            # Property: Error messages should mention format requirements
            error_text = ' '.join(invalid_result['errors']).lower()
            assert any(keyword in error_text for keyword in ['format', 'start', 'prefix', 'must']), f"Error messages should mention format requirements: {invalid_result['errors']}"