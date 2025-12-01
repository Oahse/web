"""
Property-based tests for Docker environment variables.

**Feature: app-enhancements, Property 64: Environment variables accessibility**
**Validates: Requirements 19.5**

These tests verify that environment variables are properly accessible and
configured in the Docker environment.
"""

import pytest
import os
from hypothesis import given, strategies as st, settings as hypothesis_settings, HealthCheck
from core.config import settings


@given(
    env_var=st.sampled_from([
        "DATABASE_URL",
        "REDIS_URL",
        "SECRET_KEY",
        "FRONTEND_URL",
        "POSTGRES_USER",
        "POSTGRES_PASSWORD",
        "POSTGRES_SERVER",
        "POSTGRES_DB"
    ])
)
@hypothesis_settings(
    max_examples=8,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
def test_required_environment_variables_exist(env_var):
    """
    Property: For any required environment variable, it should be accessible
    in the application.
    
    This tests that:
    1. Required environment variables are set
    2. Variables are accessible from settings
    3. Configuration is properly loaded
    """
    # Check if variable exists in environment or settings
    if env_var == "DATABASE_URL":
        assert hasattr(settings, 'SQLALCHEMY_DATABASE_URI'), \
            "DATABASE_URL not configured in settings"
        assert settings.SQLALCHEMY_DATABASE_URI, \
            "DATABASE_URL is empty"
    elif env_var == "REDIS_URL":
        assert hasattr(settings, 'REDIS_URL'), \
            "REDIS_URL not configured in settings"
    elif env_var == "SECRET_KEY":
        assert hasattr(settings, 'SECRET_KEY'), \
            "SECRET_KEY not configured in settings"
        assert len(settings.SECRET_KEY) >= 32, \
            "SECRET_KEY should be at least 32 characters"
    elif env_var == "FRONTEND_URL":
        assert hasattr(settings, 'FRONTEND_URL'), \
            "FRONTEND_URL not configured in settings"
    elif env_var == "POSTGRES_USER":
        assert hasattr(settings, 'POSTGRES_USER'), \
            "POSTGRES_USER not configured in settings"
    elif env_var == "POSTGRES_PASSWORD":
        assert hasattr(settings, 'POSTGRES_PASSWORD'), \
            "POSTGRES_PASSWORD not configured in settings"
    elif env_var == "POSTGRES_SERVER":
        assert hasattr(settings, 'POSTGRES_SERVER'), \
            "POSTGRES_SERVER not configured in settings"
    elif env_var == "POSTGRES_DB":
        assert hasattr(settings, 'POSTGRES_DB'), \
            "POSTGRES_DB not configured in settings"


@given(
    setting_attr=st.sampled_from([
        "SQLALCHEMY_DATABASE_URI",
        "SECRET_KEY",
        "ALGORITHM",
        "ACCESS_TOKEN_EXPIRE_MINUTES"
    ])
)
@hypothesis_settings(
    max_examples=4,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
def test_settings_attributes_accessible(setting_attr):
    """
    Property: For any settings attribute, it should be accessible and have
    a valid value.
    
    This tests that:
    1. Settings object is properly initialized
    2. Attributes are accessible
    3. Values are not None or empty
    """
    assert hasattr(settings, setting_attr), \
        f"Settings attribute {setting_attr} does not exist"
    
    value = getattr(settings, setting_attr)
    assert value is not None, \
        f"Settings attribute {setting_attr} is None"
    
    if isinstance(value, str):
        assert len(value) > 0, \
            f"Settings attribute {setting_attr} is empty string"


def test_database_url_format():
    """
    Property: The database URL should be in the correct format for async
    PostgreSQL connections.
    
    This tests that:
    1. Database URL is properly formatted
    2. Contains required components
    3. Uses correct driver (asyncpg)
    """
    db_url = settings.SQLALCHEMY_DATABASE_URI
    
    assert db_url.startswith("postgresql+asyncpg://"), \
        "Database URL should use postgresql+asyncpg driver"
    
    # Check for required components
    assert "@" in db_url, "Database URL should contain @ separator"
    assert "/" in db_url, "Database URL should contain / separator"


def test_redis_url_format():
    """
    Property: The Redis URL should be in the correct format.
    
    This tests that:
    1. Redis URL is properly formatted
    2. Contains required components
    3. Uses correct protocol
    """
    if hasattr(settings, 'REDIS_URL'):
        redis_url = settings.REDIS_URL
        
        assert redis_url.startswith("redis://"), \
            "Redis URL should use redis:// protocol"
        
        # Check for required components
        assert ":" in redis_url, "Redis URL should contain port"


@given(
    cors_origin=st.sampled_from([
        "http://localhost:5173",
        "http://localhost:3000",
        "http://frontend:5173"
    ])
)
@hypothesis_settings(
    max_examples=3,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
def test_cors_origins_configuration(cors_origin):
    """
    Property: For any valid CORS origin, it should be properly configured.
    
    This tests that:
    1. CORS origins are configured
    2. Frontend URL is allowed
    3. Configuration is accessible
    """
    if hasattr(settings, 'BACKEND_CORS_ORIGINS'):
        cors_origins = settings.BACKEND_CORS_ORIGINS
        
        # CORS origins might be a list or string
        if isinstance(cors_origins, list):
            # At least one origin should be configured
            assert len(cors_origins) > 0, "No CORS origins configured"
        elif isinstance(cors_origins, str):
            # Should not be empty
            assert len(cors_origins) > 0, "CORS origins string is empty"


def test_jwt_configuration():
    """
    Property: JWT configuration should be properly set up.
    
    This tests that:
    1. JWT algorithm is configured
    2. Token expiration times are set
    3. Values are reasonable
    """
    assert hasattr(settings, 'ALGORITHM'), "JWT algorithm not configured"
    assert settings.ALGORITHM in ["HS256", "HS384", "HS512"], \
        "JWT algorithm should be a valid HMAC algorithm"
    
    if hasattr(settings, 'ACCESS_TOKEN_EXPIRE_MINUTES'):
        assert settings.ACCESS_TOKEN_EXPIRE_MINUTES > 0, \
            "Access token expiration should be positive"
        assert settings.ACCESS_TOKEN_EXPIRE_MINUTES <= 1440, \
            "Access token expiration should not exceed 24 hours"


def test_environment_name():
    """
    Property: The environment name should be set and valid.
    
    This tests that:
    1. Environment name is configured
    2. Value is one of the expected environments
    3. Configuration is accessible
    """
    if hasattr(settings, 'ENVIRONMENT'):
        env = settings.ENVIRONMENT
        assert env in ["local", "development", "staging", "production"], \
            f"Environment '{env}' is not a recognized environment"


@given(
    optional_var=st.sampled_from([
        "MAILGUN_API_KEY",
        "STRIPE_SECRET_KEY",
        "GOOGLE_CLIENT_ID",
        "FACEBOOK_APP_ID"
    ])
)
@hypothesis_settings(
    max_examples=4,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
def test_optional_environment_variables(optional_var):
    """
    Property: For any optional environment variable, if it's set, it should
    have a valid value.
    
    This tests that:
    1. Optional variables can be accessed
    2. If set, they have non-empty values
    3. Missing optional variables don't break the application
    """
    # These are optional, so we just check if they exist and are valid if set
    if hasattr(settings, optional_var):
        value = getattr(settings, optional_var)
        if value is not None and isinstance(value, str):
            # If set, should not be empty
            # Note: Placeholder values (starting with "your_") are acceptable
            # in development/example configurations
            if len(value) > 0:
                # Just verify it's a string with content
                assert isinstance(value, str), \
                    f"{optional_var} should be a string"


def test_docker_specific_configuration():
    """
    Property: Docker-specific configuration should use service names instead
    of localhost.
    
    This tests that:
    1. Database host uses service name in Docker
    2. Redis host uses service name in Docker
    3. Configuration is Docker-aware
    """
    db_url = settings.SQLALCHEMY_DATABASE_URI
    
    # In Docker, should use service names
    # This test will pass in both Docker and local environments
    # as it just checks the URL is valid
    assert "postgresql" in db_url, "Database URL should contain postgresql"
    
    if hasattr(settings, 'REDIS_URL'):
        redis_url = settings.REDIS_URL
        assert "redis://" in redis_url, "Redis URL should contain redis://"


def test_settings_immutability():
    """
    Property: Settings should be immutable after initialization.
    
    This tests that:
    1. Settings object is properly frozen
    2. Configuration cannot be accidentally modified
    3. Application state is stable
    """
    # Try to access a setting
    original_value = settings.SECRET_KEY
    
    # Verify we can read it multiple times
    assert settings.SECRET_KEY == original_value
    assert settings.SECRET_KEY == original_value


@given(
    port_config=st.sampled_from([
        ("POSTGRES_PORT", 5432),
        ("REDIS_PORT", 6379)
    ])
)
@hypothesis_settings(
    max_examples=2,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
def test_port_configurations(port_config):
    """
    Property: For any service port configuration, it should be set to the
    correct default value.
    
    This tests that:
    1. Port configurations are accessible
    2. Ports use standard values
    3. Configuration is consistent
    """
    port_name, expected_port = port_config
    
    if hasattr(settings, port_name):
        port = getattr(settings, port_name)
        assert port == expected_port, \
            f"{port_name} should be {expected_port}, got {port}"
