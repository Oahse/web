"""
Application Configuration and Environment Management

This module provides:
- Environment variable management and validation
- Application settings with context-aware defaults
- Environment validation and setup utilities
"""

import os
import re
import logging
from typing import List, Dict, Any, Optional, Tuple, Literal
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS AND DATA CLASSES
# =============================================================================

class EnvironmentType(Enum):
    """Supported environment types"""
    DEVELOPMENT = "dev"
    PRODUCTION = "prod" 
    STAGING = "staging"
    LOCAL = "local"


class VariableType(Enum):
    """Types of environment variables for validation"""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    URL = "url"
    EMAIL = "email"
    SECRET = "secret"
    JSON = "json"


@dataclass
class EnvironmentVariable:
    """Definition of an environment variable with validation rules"""
    name: str
    description: str
    variable_type: VariableType
    required: bool = True
    default_value: Optional[str] = None
    validation_pattern: Optional[str] = None
    sensitive: bool = False
    dev_override: Optional[str] = None
    prod_override: Optional[str] = None


@dataclass
class ValidationResult:
    """Result of environment variable validation"""
    is_valid: bool
    missing_variables: List[str] = field(default_factory=list)
    invalid_variables: List[Tuple[str, str]] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    error_message: Optional[str] = None


@dataclass
class EnvironmentContext:
    """Context information about the current environment"""
    is_docker: bool
    is_production: bool
    is_development: bool
    container_name: str
    env_file_path: Optional[str]


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def parse_cors(value: str) -> List[str]:
    """
    Parses CORS origins. Accepts comma-separated string or list-like string.
    """
    if not value:
        return [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://0.0.0.0:5173",
            "http://localhost:3000",
            "http://www.banwee.com",
            "https://www.banwee.com",
            "https://www.banwee.ca",
            "https://www.banwee.co.uk",
            "https://www.banwee.ng",
            "https://banwee.com"
        ]
    
    if isinstance(value, str):
        value = value.strip()
        if value.startswith("[") and value.endswith("]"):
            return [i.strip().strip('"') for i in value[1:-1].split(",")]
        return [i.strip() for i in value.split(",")]
    
    raise ValueError("Invalid CORS format")


# =============================================================================
# ENVIRONMENT VARIABLE DEFINITIONS
# =============================================================================

class VariableDefinitions:
    """Centralized environment variable definitions for all containers"""
    
    BACKEND_VARIABLES = [
        # Database Configuration
        EnvironmentVariable(
            name="POSTGRES_USER",
            description="PostgreSQL database username",
            variable_type=VariableType.STRING,
            required=True,
            default_value="banwee"
        ),
        EnvironmentVariable(
            name="POSTGRES_PASSWORD", 
            description="PostgreSQL database password",
            variable_type=VariableType.SECRET,
            required=True,
            sensitive=True,
            default_value="banwee_password"
        ),
        EnvironmentVariable(
            name="POSTGRES_SERVER",
            description="PostgreSQL server hostname",
            variable_type=VariableType.STRING,
            required=True,
            default_value="postgres",
            dev_override="localhost",
            prod_override="postgres"
        ),
        EnvironmentVariable(
            name="POSTGRES_PORT",
            description="PostgreSQL server port", 
            variable_type=VariableType.INTEGER,
            required=True,
            default_value="5432",
            validation_pattern=r"^\d{1,5}$"
        ),
        EnvironmentVariable(
            name="POSTGRES_DB",
            description="PostgreSQL database name",
            variable_type=VariableType.STRING,
            required=True,
            default_value="banwee_db"
        ),
        EnvironmentVariable(
            name="POSTGRES_DB_URL",
            description="Complete PostgreSQL connection URL",
            variable_type=VariableType.URL,
            required=False,
            validation_pattern=r"^postgresql\+asyncpg://.*"
        ),
        
        # Redis Configuration
        EnvironmentVariable(
            name="REDIS_URL",
            description="Redis connection URL",
            variable_type=VariableType.URL,
            required=True,
            default_value="redis://redis:6379/0",
            dev_override="redis://localhost:6379/0",
            prod_override="redis://redis:6379/0"
        ),
        
        # Kafka Configuration
        EnvironmentVariable(
            name="KAFKA_BOOTSTRAP_SERVERS",
            description="Kafka bootstrap servers",
            variable_type=VariableType.STRING,
            required=True,
            default_value="kafka:29092",
            dev_override="localhost:9092",
            prod_override="kafka:29092"
        ),
        
        # Security Configuration
        EnvironmentVariable(
            name="SECRET_KEY",
            description="Application secret key for JWT and encryption",
            variable_type=VariableType.SECRET,
            required=True,
            sensitive=True,
            validation_pattern=r"^.{32,}$"
        ),
        EnvironmentVariable(
            name="STRIPE_SECRET_KEY",
            description="Stripe API secret key",
            variable_type=VariableType.SECRET,
            required=True,
            sensitive=True,
            validation_pattern=r"^sk_(test_|live_)[a-zA-Z0-9]{99}$"
        ),
        EnvironmentVariable(
            name="STRIPE_WEBHOOK_SECRET",
            description="Stripe webhook endpoint secret",
            variable_type=VariableType.SECRET,
            required=True,
            sensitive=True,
            validation_pattern=r"^whsec_[a-zA-Z0-9_]{10,}$"
        ),
        
        # Application Settings
        EnvironmentVariable(
            name="ENVIRONMENT",
            description="Application environment (local, staging, production)",
            variable_type=VariableType.STRING,
            required=True,
            default_value="local",
            validation_pattern=r"^(local|staging|production)$"
        ),
        EnvironmentVariable(
            name="FRONTEND_URL",
            description="Frontend application URL",
            variable_type=VariableType.URL,
            required=True,
            default_value="http://localhost:5173"
        ),
        EnvironmentVariable(
            name="BACKEND_URL",
            description="Backend application URL",
            variable_type=VariableType.URL,
            required=True,
            default_value="http://localhost:8000"
        ),
        
        # Email Configuration
        EnvironmentVariable(
            name="MAILGUN_API_KEY",
            description="Mailgun API key for email sending",
            variable_type=VariableType.SECRET,
            required=False,
            sensitive=True
        ),
        EnvironmentVariable(
            name="MAILGUN_DOMAIN",
            description="Mailgun domain for email sending",
            variable_type=VariableType.STRING,
            required=False
        ),
    ]


# =============================================================================
# MAIN SETTINGS CLASS
# =============================================================================

class Settings:
    """
    Application settings with environment validation and context awareness
    """
    
    def __init__(self):
        self._load_environment()
        self._initialize_settings()
        self._validate_configuration()
    
    def _load_environment(self):
        """Load environment variables from .env file"""
        ENVIRONMENT = os.getenv('ENVIRONMENT', 'local')
        env_file = '.dev.env' if ENVIRONMENT in ['local', 'dev'] else '.prod.env'
        
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        ENV_PATH = os.path.join(BASE_DIR, env_file)
        
        if os.path.exists(ENV_PATH):
            load_dotenv(ENV_PATH)
        else:
            # Fallback to .env for backward compatibility or other setups
            fallback_path = os.path.join(BASE_DIR, '.env')
            if os.path.exists(fallback_path):
                load_dotenv(fallback_path)

    def _initialize_settings(self):
        """Initialize all configuration settings."""
        
        # --- General Environment Settings ---
        self.DOMAIN: str = os.getenv('DOMAIN', 'localhost')
        self.ENVIRONMENT: Literal["local", "staging", "production"] = os.getenv('ENVIRONMENT', 'local')
        
        # --- URLs ---
        self.FRONTEND_URL: str = os.getenv('FRONTEND_URL', 'http://localhost:5173')
        self.BACKEND_URL: str = os.getenv('BACKEND_URL', 'http://localhost:8000')
        cors_origins = os.getenv('BACKEND_CORS_ORIGINS', 'http://localhost:5173,http://127.0.0.1:5173,http://0.0.0.0:5173')
        
        # --- PostgreSQL Database Configuration ---
        self.POSTGRES_USER: str = os.getenv('POSTGRES_USER', 'banwee')
        self.POSTGRES_PASSWORD: str = os.getenv('POSTGRES_PASSWORD', 'banwee_password')
        self.POSTGRES_SERVER: str = os.getenv('POSTGRES_SERVER')
        self.POSTGRES_PORT: int = int(os.getenv('POSTGRES_PORT', 5432))
        self.POSTGRES_DB: str = os.getenv('POSTGRES_DB', 'banwee_db')
        self.POSTGRES_DB_URL: str = os.getenv('POSTGRES_DB_URL')
        
        # Database connection pool settings
        self.DB_POOL_SIZE: int = int(os.getenv('DB_POOL_SIZE', 20))
        self.DB_MAX_OVERFLOW: int = int(os.getenv('DB_MAX_OVERFLOW', 30))
        self.DB_POOL_TIMEOUT: int = int(os.getenv('DB_POOL_TIMEOUT', 30))
        self.DB_POOL_RECYCLE: int = int(os.getenv('DB_POOL_RECYCLE', 3600))
        
        # --- Security Settings ---
        self.SECRET_KEY: str = os.getenv('SECRET_KEY')
        self.STRIPE_SECRET_KEY: str = os.getenv('STRIPE_SECRET_KEY')
        self.STRIPE_WEBHOOK_SECRET: str = os.getenv('STRIPE_WEBHOOK_SECRET')
        self.ALGORITHM: str = os.getenv('ALGORITHM', "HS256")
        
        # Session and Token Configuration
        self.ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES', 30))
        self.REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv('REFRESH_TOKEN_EXPIRE_DAYS', 7))
        self.SESSION_WARNING_THRESHOLD_MINUTES: int = int(os.getenv('SESSION_WARNING_THRESHOLD_MINUTES', 5))
        self.SESSION_EXTENSION_MINUTES: int = int(os.getenv('SESSION_EXTENSION_MINUTES', 30))
        
        # Remember Me Configuration
        self.REMEMBER_ME_TOKEN_EXPIRE_DAYS: int = int(os.getenv('REMEMBER_ME_TOKEN_EXPIRE_DAYS', 30))
        
        # Session Security
        self.MAX_CONCURRENT_SESSIONS: int = int(os.getenv('MAX_CONCURRENT_SESSIONS', 5))
        self.FORCE_LOGOUT_ON_PASSWORD_CHANGE: bool = os.getenv('FORCE_LOGOUT_ON_PASSWORD_CHANGE', 'true').lower() == 'true'
        
        # --- Redis Configuration ---
        self.REDIS_URL: str = os.getenv('REDIS_URL')
        self.REDIS_CACHE_ENABLED: bool = os.getenv('REDIS_CACHE_ENABLED', 'true').lower() == 'true'
        self.REDIS_RATELIMIT_ENABLED: bool = os.getenv('REDIS_RATELIMIT_ENABLED', 'true').lower() == 'true'
        self.REDIS_CACHE_TTL: int = int(os.getenv('REDIS_CACHE_TTL', '3600'))
        
        # --- Kafka Configuration ---
        self.KAFKA_BOOTSTRAP_SERVERS: str = os.getenv('KAFKA_BOOTSTRAP_SERVERS')
        
        # Kafka Topics
        self.KAFKA_TOPIC_EMAIL: str = os.getenv('KAFKA_TOPIC_EMAIL', 'banwee-email-notifications')
        self.KAFKA_TOPIC_NOTIFICATION: str = os.getenv('KAFKA_TOPIC_NOTIFICATION', 'banwee-user-notifications')
        self.KAFKA_TOPIC_ORDER: str = os.getenv('KAFKA_TOPIC_ORDER', 'banwee-order-events')
        self.KAFKA_TOPIC_NEGOTIATION: str = os.getenv('KAFKA_TOPIC_NEGOTIATION', 'banwee-negotiation-events')
        self.KAFKA_TOPIC_PAYMENT: str = os.getenv('KAFKA_TOPIC_PAYMENT', 'banwee-payment-events')
        self.KAFKA_TOPIC_CART: str = os.getenv('KAFKA_TOPIC_CART', 'banwee-cart-events')
        self.KAFKA_TOPIC_INVENTORY: str = os.getenv('KAFKA_TOPIC_INVENTORY', 'banwee-inventory-events')
        self.KAFKA_TOPIC_WEBSOCKET: str = os.getenv('KAFKA_TOPIC_WEBSOCKET', 'banwee-websocket-events')
        self.KAFKA_TOPIC_REAL_TIME: str = os.getenv('KAFKA_TOPIC_REAL_TIME', 'banwee-real-time-notifications')
        
        # Kafka Consumer Groups
        self.KAFKA_CONSUMER_GROUP_BACKEND: str = os.getenv('KAFKA_CONSUMER_GROUP_BACKEND', 'banwee-backend-consumers')
        self.KAFKA_CONSUMER_GROUP_SCHEDULER: str = os.getenv('KAFKA_CONSUMER_GROUP_SCHEDULER', 'banwee-scheduler-consumers')
        self.KAFKA_CONSUMER_GROUP_NEGOTIATOR: str = os.getenv('KAFKA_CONSUMER_GROUP_NEGOTIATOR', 'banwee-negotiator-consumers')
        self.KAFKA_CONSUMER_GROUP_WEBSOCKET: str = os.getenv('KAFKA_CONSUMER_GROUP_WEBSOCKET', 'banwee-websocket-consumers')
        
        # Kafka Performance Settings
        self.KAFKA_AUTO_OFFSET_RESET: str = os.getenv('KAFKA_AUTO_OFFSET_RESET', 'earliest')
        self.KAFKA_ENABLE_AUTO_COMMIT: bool = os.getenv('KAFKA_ENABLE_AUTO_COMMIT', 'true').lower() == 'true'
        self.KAFKA_MAX_POLL_RECORDS: int = int(os.getenv('KAFKA_MAX_POLL_RECORDS', 500))
        self.KAFKA_SESSION_TIMEOUT_MS: int = int(os.getenv('KAFKA_SESSION_TIMEOUT_MS', 30000))
        self.KAFKA_HEARTBEAT_INTERVAL_MS: int = int(os.getenv('KAFKA_HEARTBEAT_INTERVAL_MS', 10000))
        self.KAFKA_RETRY_BACKOFF_MS: int = int(os.getenv('KAFKA_RETRY_BACKOFF_MS', 1000))
        self.KAFKA_MAX_RETRIES: int = int(os.getenv('KAFKA_MAX_RETRIES', 3))
        self.KAFKA_REQUEST_TIMEOUT_MS: int = int(os.getenv('KAFKA_REQUEST_TIMEOUT_MS', 30000))
        self.KAFKA_DELIVERY_TIMEOUT_MS: int = int(os.getenv('KAFKA_DELIVERY_TIMEOUT_MS', 120000))
        self.KAFKA_BATCH_SIZE: int = int(os.getenv('KAFKA_BATCH_SIZE', 16384))
        self.KAFKA_LINGER_MS: int = int(os.getenv('KAFKA_LINGER_MS', 5))
        self.KAFKA_COMPRESSION_TYPE: str = os.getenv('KAFKA_COMPRESSION_TYPE', 'snappy')
        self.KAFKA_ACKS: str = os.getenv('KAFKA_ACKS', 'all')
        
        # --- CORS Configuration ---
        self.BACKEND_CORS_ORIGINS: List[str] = parse_cors(cors_origins)
        
        # ... (rest of the settings)
        self.MAILGUN_API_KEY: str = os.getenv('MAILGUN_API_KEY', '')
        self.MAILGUN_DOMAIN: str = os.getenv('MAILGUN_DOMAIN', '')
        self.MAILGUN_FROM_EMAIL: str = os.getenv('MAILGUN_FROM_EMAIL', 'Banwee <noreply@banwee.com>')
        self.TELEGRAM_BOT_TOKEN: str = os.getenv('TELEGRAM_BOT_TOKEN', '')
        self.WHATSAPP_ACCESS_TOKEN: str = os.getenv('WHATSAPP_ACCESS_TOKEN', '')
        self.PHONE_NUMBER_ID: str = os.getenv('PHONE_NUMBER_ID', '')
        self.FACEBOOK_APP_ID: str = os.getenv('FACEBOOK_APP_ID')
        self.FACEBOOK_APP_SECRET: str = os.getenv('FACEBOOK_APP_SECRET')
        self.TIKTOK_CLIENT_KEY: str = os.getenv('TIKTOK_CLIENT_KEY')
        self.TIKTOK_CLIENT_SECRET: str = os.getenv('TIKTOK_CLIENT_SECRET')
        self.TAX_API_KEY: str = os.getenv('TAX_API_KEY', '')
        self.TAX_API_URL: str = os.getenv('TAX_API_URL', 'https://api.taxjar.com/v2')
        self.VAT_API_KEY: str = os.getenv('VAT_API_KEY', '')
        self.VAT_API_URL: str = os.getenv('VAT_API_URL', 'https://vatlayer.com/api')
        self.ADMIN_USER_ID: str = os.getenv('ADMIN_USER_ID', 'your_admin_uuid_here')
        self.NOTIFICATION_CLEANUP_DAYS: int = int(os.getenv('NOTIFICATION_CLEANUP_DAYS', 30))
        self.NOTIFICATION_CLEANUP_INTERVAL_SECONDS: int = int(os.getenv('NOTIFICATION_CLEANUP_INTERVAL_SECONDS', 86400))
    
    @property
    def server_host(self) -> str:
        """Determines the server host URL based on the environment."""
        return f"http://{self.DOMAIN}" if self.ENVIRONMENT == "local" else f"https://{self.DOMAIN}"
    
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        """Constructs the SQLAlchemy database URI for async operations."""
        if self.POSTGRES_DB_URL:
            return self.POSTGRES_DB_URL
        
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )
    
    @property
    def SQLALCHEMY_DATABASE_URI_SYNC(self) -> str:
        """Constructs the SQLAlchemy database URI for synchronous operations."""
        uri = self.SQLALCHEMY_DATABASE_URI
        return uri.replace('+asyncpg', '+psycopg2')
    
    def _validate_configuration(self):
        """Validate all configuration settings"""
        self.validate_required_settings()
        self.validate_kafka_configuration()
        self.validate_stripe_configuration()
    
    def validate_required_settings(self) -> None:
        """Validates that all required configuration settings are present."""
        missing_settings = []
        
        if not self.SECRET_KEY:
            missing_settings.append("SECRET_KEY is required for session management and token signing")
        
        if not self.STRIPE_SECRET_KEY:
            missing_settings.append("STRIPE_SECRET_KEY is required for Stripe API authentication")
        
        if not self.STRIPE_WEBHOOK_SECRET:
            missing_settings.append("STRIPE_WEBHOOK_SECRET is required for webhook signature verification")
        
        if not self.KAFKA_BOOTSTRAP_SERVERS:
            missing_settings.append("KAFKA_BOOTSTRAP_SERVERS is required for Kafka connection")
        
        if not self.POSTGRES_DB_URL and not all([
            self.POSTGRES_USER, self.POSTGRES_PASSWORD, 
            self.POSTGRES_SERVER, self.POSTGRES_DB
        ]):
            missing_settings.append("Database configuration is incomplete")
        
        if missing_settings:
            error_message = "Missing required configuration settings:\n" + "\n".join(f"- {setting}" for setting in missing_settings)
            raise ValueError(error_message)
    
    def validate_kafka_configuration(self) -> None:
        """Validates Kafka-specific configuration settings."""
        topics = [
            self.KAFKA_TOPIC_EMAIL,
            self.KAFKA_TOPIC_NOTIFICATION,
            self.KAFKA_TOPIC_ORDER,
            # self.KAFKA_TOPIC_NEGOTIATION,  # Disabled - not using negotiator for now
            self.KAFKA_TOPIC_PAYMENT
        ]
        
        for topic in topics:
            if not topic or not topic.strip():
                raise ValueError(f"Kafka topic name cannot be empty")
    
    def validate_stripe_configuration(self) -> None:
        """Validates Stripe-specific configuration settings."""
        if self.STRIPE_SECRET_KEY and not self.STRIPE_SECRET_KEY.startswith(('sk_test_', 'sk_live_')):
            raise ValueError("STRIPE_SECRET_KEY must start with 'sk_test_' or 'sk_live_'")
        
        if self.STRIPE_WEBHOOK_SECRET and not self.STRIPE_WEBHOOK_SECRET.startswith('whsec_'):
            raise ValueError("STRIPE_WEBHOOK_SECRET must start with 'whsec_'")


# =============================================================================
# ENVIRONMENT VALIDATOR
# =============================================================================

class EnvironmentValidator:
    """Enhanced environment validator with context-aware validation"""
    
    def __init__(self):
        self.context = self._detect_environment_context()
    
    def _detect_environment_context(self) -> EnvironmentContext:
        """Detect the current environment context"""
        
        is_docker = (
            os.path.exists('/.dockerenv') or
            os.getenv('DOCKER_CONTAINER') == 'true' or
            os.getenv('KUBERNETES_SERVICE_HOST') is not None
        )
        
        env_type = os.getenv('ENVIRONMENT', 'local').lower()
        is_production = env_type in ['production', 'prod']
        is_development = env_type in ['development', 'dev', 'local']
        
        container_name = self._detect_container_name()
        env_file_path = self._find_env_file()
        
        return EnvironmentContext(
            is_docker=is_docker,
            is_production=is_production,
            is_development=is_development,
            container_name=container_name,
            env_file_path=env_file_path
        )
    
    def _detect_container_name(self) -> str:
        """Detect the current container name"""
        container_name = os.getenv('CONTAINER_NAME')
        if container_name:
            return container_name.lower()
        
        cwd = Path.cwd()
        if 'backend' in cwd.parts:
            return 'backend'
        elif 'frontend' in cwd.parts:
            return 'frontend'
        elif 'negotiator' in cwd.parts:
            return 'negotiator'
        elif 'scheduler' in cwd.parts:
            return 'scheduler'
        
        return 'backend'
    
    def _find_env_file(self) -> Optional[str]:
        """Find the appropriate .env file"""
        current_env = Path('.env')
        if current_env.exists():
            return str(current_env)
        
        container_paths = [
            Path('backend/.env'),
            Path('frontend/.env'),
            Path('../.env'),
        ]
        
        for path in container_paths:
            if path.exists():
                return str(path)
        
        return None
    
    def validate_startup_environment(self) -> ValidationResult:
        """Perform comprehensive startup validation with context awareness"""
        try:
            logger.info(f"Validating environment for {self.context.container_name} container")
            
            if self.context.env_file_path:
                load_dotenv(self.context.env_file_path)
                logger.info(f"Loaded environment from {self.context.env_file_path}")
            
            validation_rules = self._get_validation_rules()
            result = self._validate_with_context(validation_rules)
            self._add_context_warnings(result)
            
            return result
            
        except Exception as e:
            logger.error(f"Startup validation failed: {e}")
            return ValidationResult(
                is_valid=False,
                error_message=f"Validation error: {str(e)}"
            )
    
    def _get_validation_rules(self) -> List[EnvironmentVariable]:
        """Get validation rules appropriate for the current context"""
        if self.context.container_name == 'backend':
            rules = VariableDefinitions.BACKEND_VARIABLES.copy()
        else:
            rules = [
                EnvironmentVariable(
                    name="ENVIRONMENT",
                    description="Application environment",
                    variable_type=VariableType.STRING,
                    required=True,
                    default_value="local"
                )
            ]
        
        # Adjust rules based on context
        if self.context.is_development:
            for rule in rules:
                if rule.name in ['MAILGUN_API_KEY', 'MAILGUN_DOMAIN']:
                    rule.required = False
        
        return rules
    
    def _validate_with_context(self, rules: List[EnvironmentVariable]) -> ValidationResult:
        """Validate environment variables with context awareness"""
        missing_variables = []
        invalid_variables = []
        warnings = []
        
        for rule in rules:
            value = os.getenv(rule.name)
            
            # Apply environment-specific overrides
            if self.context.is_development and rule.dev_override:
                if not value or value == rule.default_value:
                    value = rule.dev_override
                    os.environ[rule.name] = value
                    warnings.append(f"Applied development override for {rule.name}")
            
            elif self.context.is_production and rule.prod_override:
                if not value or value == rule.default_value:
                    value = rule.prod_override
                    os.environ[rule.name] = value
                    warnings.append(f"Applied production override for {rule.name}")
            
            # Check required variables
            if rule.required and not value:
                if rule.default_value:
                    os.environ[rule.name] = rule.default_value
                    warnings.append(f"Using default value for {rule.name}")
                else:
                    missing_variables.append(rule.name)
                    continue
            
            # Validate variable if present
            if value:
                error = self._validate_variable_value(rule, value)
                if error:
                    invalid_variables.append((rule.name, error))
        
        # Generate error message
        error_message = None
        if missing_variables or invalid_variables:
            error_parts = []
            
            if missing_variables:
                error_parts.append(
                    f"Missing required variables for {self.context.container_name}:\n" +
                    "\n".join(f"  - {var}" for var in missing_variables)
                )
            
            if invalid_variables:
                error_parts.append(
                    f"Invalid variables for {self.context.container_name}:\n" +
                    "\n".join(f"  - {var}: {error}" for var, error in invalid_variables)
                )
            
            error_message = "\n\n".join(error_parts)
        
        return ValidationResult(
            is_valid=len(missing_variables) == 0 and len(invalid_variables) == 0,
            missing_variables=missing_variables,
            invalid_variables=invalid_variables,
            warnings=warnings,
            error_message=error_message
        )
    
    def _validate_variable_value(self, rule: EnvironmentVariable, value: str) -> Optional[str]:
        """Validate a single environment variable value"""
        try:
            # Type-specific validation
            if rule.variable_type == VariableType.INTEGER:
                try:
                    int(value)
                except ValueError:
                    return f"Must be a valid integer, got: {value}"
            
            elif rule.variable_type == VariableType.URL:
                if not value.startswith(("http://", "https://", "redis://", "postgresql://", "postgresql+asyncpg://")):
                    return f"Must be a valid URL, got: {value}"
            
            # Pattern validation
            if rule.validation_pattern:
                if not re.match(rule.validation_pattern, value):
                    return f"Does not match required pattern: {rule.validation_pattern}"
            
            # Context-specific validation
            if self.context.is_production and rule.sensitive:
                if rule.name == 'SECRET_KEY' and len(value) < 32:
                    return "SECRET_KEY must be at least 32 characters in production"
                
                if 'test' in value.lower() and rule.name.startswith('STRIPE'):
                    return f"Production environment should not use test Stripe keys"
            
            return None
            
        except Exception as e:
            return f"Validation error: {str(e)}"
    
    def _add_context_warnings(self, result: ValidationResult):
        """Add context-specific warnings to the validation result"""
        if self.context.is_development:
            result.warnings.append("Running in development mode")
        
        if self.context.is_production:
            result.warnings.append("Running in production mode")
        
        if self.context.is_docker:
            result.warnings.append("Running in Docker container")


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def validate_startup_environment() -> ValidationResult:
    """Validate environment for application startup"""
    validator = EnvironmentValidator()
    return validator.validate_startup_environment()


def get_setup_instructions() -> str:
    """Get context-specific setup instructions"""
    validator = EnvironmentValidator()
    instructions = [
        f"# Environment Setup Instructions for {validator.context.container_name.title()}",
        "",
        f"**Current Context:**",
        f"- Container: {validator.context.container_name}",
        f"- Docker: {'Yes' if validator.context.is_docker else 'No'}",
        f"- Environment: {'Production' if validator.context.is_production else 'Development'}",
        "",
    ]
    
    if not validator.context.env_file_path:
        instructions.extend([
            "## Missing .env File",
            "",
            "1. Create a .env file in the appropriate location",
            "2. Edit the .env file with your configuration values",
            "",
        ])
    
    return "\n".join(instructions)


# =============================================================================
# MAIN SETTINGS INSTANCE
# =============================================================================

# Instantiate the settings object to be used throughout the application
settings = Settings()