import os
import re # For regex matching of file types
from typing import List, Literal, Dict, Any, Optional # Import Dict, Any, Optional
from dotenv import load_dotenv
import logging
from enum import Enum

# Imports for synchronous DB session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# Imports for async DB session
from sqlalchemy.ext.asyncio import AsyncSession


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file located in the parent directory
# This ensures that variables set in a local .env file are loaded.
# Environment variables explicitly set (e.g., by Docker Compose) will take precedence.
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
ENV_PATH = os.path.join(BASE_DIR, '.env')
load_dotenv(ENV_PATH)


def parse_cors(value: str) -> List[str]:
    """
    Parses CORS origins. Accepts comma-separated string or list-like string.
    Example: "http://localhost,http://127.0.0.1" → ["http://localhost", "http://127.0.0.1"]
    If the value is empty, a default list of common development origins is provided.
    """
    if not value:
        # Default CORS origins for local development
        return [
            "http://localhost:5173",  # Vite dev server
            "http://0.0.0.0:5173",  # Vite dev server when binding to all interfaces
            "http://127.0.0.1:5173",
            "http://localhost:3000",  # optional if you also use CRA
        ]
    if isinstance(value, str):
        value = value.strip()
        if value.startswith("[") and value.endswith("]"):
            # Handles list-like string format (e.g., "['http://a.com', 'http://b.com']")
            parsed_list = [i.strip().strip('"') for i in value[1:-1].split(",")]
            return parsed_list
        # Handles comma-separated string format (e.g., "http://a.com,http://b.com")
        parsed_list = [i.strip() for i in value.split(",")]
        return parsed_list
    raise ValueError("Invalid CORS format")


class Settings:
    # --- General Environment Settings ---
    # DOMAIN for API endpoint generation and general application context. Defaults to 'localhost' for local dev.
    DOMAIN: str = os.getenv('DOMAIN', 'localhost')
    # ENVIRONMENT determines application behavior (e.g., logging level, debug modes).
    ENVIRONMENT: Literal["local", "staging",
                         "production"] = os.getenv('ENVIRONMENT', 'local')


    # --- External Service Integrations (Uncomment and configure as needed) ---
    # SMS_API_KEY: Optional[str] = os.getenv('SMS_API_KEY')
    # SMS_API_URL: Optional[str] = os.getenv('SMS_API_URL')
    # FIREBASE_CREDENTIALS_JSON: Optional[str] = os.getenv('FIREBASE_CREDENTIALS_JSON','')

    # --- PostgreSQL Database Configuration ---
    # Individual PostgreSQL connection parameters.
    # Defaults are set for local Docker Compose setup.
    POSTGRES_USER: str = os.getenv('POSTGRES_USER', 'banwee') # Default user for Docker
    POSTGRES_PASSWORD: str = os.getenv(
        'POSTGRES_PASSWORD', 'banwee_password') # Default password for Docker
    POSTGRES_SERVER: str = os.getenv(
        'POSTGRES_SERVER', 'postgres') # Default to 'postgres' service name for Docker
    POSTGRES_PORT: int = int(os.getenv('POSTGRES_PORT', 5432))
    POSTGRES_DB: str = os.getenv('POSTGRES_DB', 'banwee_db') # Default database name for Docker

    # Full PostgreSQL Database URL.
    # This variable takes precedence if set, simplifying connection string management.
    # Default is an empty string, allowing the URL to be constructed from components or
    # to be provided by Docker Compose environment variables.
    POSTGRES_DB_URL: str = os.getenv('POSTGRES_DB_URL', "")


    # SQLite (fallback if needed for testing or specific local environments)
    SQLITE_DB_PATH: str = os.getenv('SQLITE_DB_PATH', 'db1.db')

    # --- Security Settings ---
    # SECRET_KEY is crucial for session management, token signing, and cryptographic operations.
    SECRET_KEY: str = os.getenv('SECRET_KEY')
    # STRIPE_SECRET_KEY for Stripe API authentication.
    STRIPE_SECRET_KEY: str = os.getenv('STRIPE_SECRET_KEY')
    # STRIPE_WEBHOOK_SECRET for verifying Stripe webhook events.
    STRIPE_WEBHOOK_SECRET: str = os.getenv('STRIPE_WEBHOOK_SECRET')
    # ALGORITHM for JWT token encoding.
    ALGORITHM: str = os.getenv('ALGORITHM', "HS256")
    # ACCESS_TOKEN_EXPIRE_MINUTES defines the validity period for access tokens.
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES', 30))
    # REFRESH_TOKEN_EXPIRE_DAYS defines the validity period for refresh tokens.
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(
        os.getenv('REFRESH_TOKEN_EXPIRE_DAYS', 7))

    # --- Mailgun Configuration ---
    # MAILGUN_API_KEY for Mailgun API authentication (used for sending emails).
    MAILGUN_API_KEY: str = os.getenv('MAILGUN_API_KEY', '')
    # MAILGUN_DOMAIN configured with Mailgun for sending emails.
    MAILGUN_DOMAIN: str = os.getenv('MAILGUN_DOMAIN', '')
    # MAILGUN_FROM_EMAIL is the sender email address for system notifications.
    MAILGUN_FROM_EMAIL: str = os.getenv('MAILGUN_FROM_EMAIL', 'Banwee <noreply@banwee.com>')
    
    # --- Redis Configuration ---
    # REDIS_URL for connecting to the Redis service (used for caching and session management).
    # Defaults to 'redis://localhost:6379/0' for local development or Docker Compose.
    REDIS_URL: str = os.getenv('REDIS_URL', 'redis://redis:6379/0') # Corrected default to 'redis' service name
    
    # --- Kafka Configuration ---
    # Kafka bootstrap servers for connecting to the Kafka cluster
    KAFKA_BOOTSTRAP_SERVERS: str = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka:29092')
    
    # Kafka topic names for different message types
    KAFKA_TOPIC_EMAIL: str = os.getenv('KAFKA_TOPIC_EMAIL', 'banwee-emails')
    KAFKA_TOPIC_NOTIFICATION: str = os.getenv('KAFKA_TOPIC_NOTIFICATION', 'banwee-notifications')
    KAFKA_TOPIC_ORDER: str = os.getenv('KAFKA_TOPIC_ORDER', 'banwee-orders')
    KAFKA_TOPIC_NEGOTIATION: str = os.getenv('KAFKA_TOPIC_NEGOTIATION', 'banwee-negotiations')
    KAFKA_TOPIC_PAYMENT: str = os.getenv('KAFKA_TOPIC_PAYMENT', 'banwee-payments')
    
    # Kafka consumer group IDs
    KAFKA_CONSUMER_GROUP_BACKEND: str = os.getenv('KAFKA_CONSUMER_GROUP_BACKEND', 'banwee-backend-consumers')
    KAFKA_CONSUMER_GROUP_SCHEDULER: str = os.getenv('KAFKA_CONSUMER_GROUP_SCHEDULER', 'banwee-scheduler-consumers')
    KAFKA_CONSUMER_GROUP_NEGOTIATOR: str = os.getenv('KAFKA_CONSUMER_GROUP_NEGOTIATOR', 'banwee-negotiator-consumers')
    
    # Kafka configuration settings
    KAFKA_AUTO_OFFSET_RESET: str = os.getenv('KAFKA_AUTO_OFFSET_RESET', 'earliest')
    KAFKA_ENABLE_AUTO_COMMIT: bool = os.getenv('KAFKA_ENABLE_AUTO_COMMIT', 'true').lower() == 'true'
    KAFKA_MAX_POLL_RECORDS: int = int(os.getenv('KAFKA_MAX_POLL_RECORDS', '500'))
    KAFKA_SESSION_TIMEOUT_MS: int = int(os.getenv('KAFKA_SESSION_TIMEOUT_MS', '30000'))
    KAFKA_HEARTBEAT_INTERVAL_MS: int = int(os.getenv('KAFKA_HEARTBEAT_INTERVAL_MS', '10000'))
    
    # Kafka retry and error handling
    KAFKA_RETRY_BACKOFF_MS: int = int(os.getenv('KAFKA_RETRY_BACKOFF_MS', '1000'))
    KAFKA_MAX_RETRIES: int = int(os.getenv('KAFKA_MAX_RETRIES', '3'))
    KAFKA_REQUEST_TIMEOUT_MS: int = int(os.getenv('KAFKA_REQUEST_TIMEOUT_MS', '30000'))
    
    # --- Frontend URL ---
    # FRONTEND_URL is the base URL of the frontend application, used for redirects, etc.
    FRONTEND_URL: str = os.getenv('FRONTEND_URL', 'http://localhost:5173')

    # --- Admin User ID (for notifications, etc.) ---
    ADMIN_USER_ID: str = os.getenv('ADMIN_USER_ID', 'your_admin_uuid_here') # NEW

    # --- Notification Cleanup Settings ---
    # NOTIFICATION_CLEANUP_DAYS specifies how old notifications must be before deletion.
    NOTIFICATION_CLEANUP_DAYS: int = int(
        os.getenv('NOTIFICATION_CLEANUP_DAYS', 30))
    # NOTIFICATION_CLEANUP_INTERVAL_SECONDS defines how often the cleanup task runs.
    NOTIFICATION_CLEANUP_INTERVAL_SECONDS: int = int(
        os.getenv('NOTIFICATION_CLEANUP_INTERVAL_SECONDS', 86400))  # 24 hours

    # --- CORS Configuration ---
    # RAW_CORS_ORIGINS is a comma-separated string of allowed origins for Cross-Origin Resource Sharing.
    RAW_CORS_ORIGINS: str = os.getenv('BACKEND_CORS_ORIGINS', '')
    # BACKEND_CORS_ORIGINS is the parsed list of allowed origins, used by FastAPI's CORSMiddleware.
    BACKEND_CORS_ORIGINS: List[str] = parse_cors(RAW_CORS_ORIGINS)

    # --- SMTP Configuration (for general email sending) ---
    SMTP_HOSTNAME: str = os.getenv('SMTP_HOSTNAME', '')
    SMTP_USER: str = os.getenv('SMTP_USER', '')
    SMTP_PASSWORD: str = os.getenv('SMTP_PASSWORD', '')

    # --- Social Media Integration Credentials ---
    TELEGRAM_BOT_TOKEN: str = os.getenv('TELEGRAM_BOT_TOKEN', '')
    WHATSAPP_ACCESS_TOKEN: str = os.getenv('WHATSAPP_ACCESS_TOKEN', '')
    PHONE_NUMBER_ID: str = os.getenv('PHONE_NUMBER_ID', '')

    FACEBOOK_APP_ID: str = os.getenv('FACEBOOK_APP_ID')
    FACEBOOK_APP_SECRET: str = os.getenv('FACEBOOK_APP_SECRET')

    TIKTOK_CLIENT_KEY: str = os.getenv('TIKTOK_CLIENT_KEY')
    TIKTOK_CLIENT_SECRET: str = os.getenv('TIKTOK_CLIENT_SECRET')

    @property
    def server_host(self) -> str:
        """Determines the server host URL based on the environment."""
        return f"http://{self.DOMAIN}" if self.ENVIRONMENT == "local" else f"https://{self.DOMAIN}"

    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        """
        Constructs the SQLAlchemy database URI.
        Prioritizes a full URL (POSTGRES_DB_URL or DATABASE_URL) over individual components.
        Ensures async PostgreSQL driver is specified.
        """
        # Always use PostgreSQL with async support
        # Priority: POSTGRES_DB_URL (specific full URL) > build from individual components
        if self.POSTGRES_DB_URL:
            return self.POSTGRES_DB_URL
        
        # Build PostgreSQL URL from individual components if no full URL is provided
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def SQLALCHEMY_DATABASE_URI_SYNC(self) -> str:
        """
        Constructs the SQLAlchemy database URI for synchronous access.
        Used by services that require synchronous database operations.
        """
        uri = self.SQLALCHEMY_DATABASE_URI
        # Replace asyncpg with psycopg2 for synchronous access
        return uri.replace('+asyncpg', '+psycopg2')

    def validate_required_settings(self) -> None:
        """
        Validates that all required configuration settings are present.
        Raises ValueError with clear error messages for missing settings.
        """
        missing_settings = []
        
        # Check required security settings
        if not self.SECRET_KEY:
            missing_settings.append("SECRET_KEY is required for session management and token signing")
        
        # Check required Stripe settings
        if not self.STRIPE_SECRET_KEY:
            missing_settings.append("STRIPE_SECRET_KEY is required for Stripe API authentication")
        
        if not self.STRIPE_WEBHOOK_SECRET:
            missing_settings.append("STRIPE_WEBHOOK_SECRET is required for webhook signature verification")
        
        # Check Kafka settings
        if not self.KAFKA_BOOTSTRAP_SERVERS:
            missing_settings.append("KAFKA_BOOTSTRAP_SERVERS is required for Kafka connection")
        
        # Check database settings
        if not self.POSTGRES_DB_URL and not all([
            self.POSTGRES_USER, self.POSTGRES_PASSWORD, 
            self.POSTGRES_SERVER, self.POSTGRES_DB
        ]):
            missing_settings.append("Database configuration is incomplete. Either set POSTGRES_DB_URL or all individual PostgreSQL settings")
        
        if missing_settings:
            error_message = "Missing required configuration settings:\n" + "\n".join(f"- {setting}" for setting in missing_settings)
            raise ValueError(error_message)

    def validate_kafka_configuration(self) -> None:
        """
        Validates Kafka-specific configuration settings.
        """
        # Validate topic names are not empty
        topics = [
            self.KAFKA_TOPIC_EMAIL,
            self.KAFKA_TOPIC_NOTIFICATION,
            self.KAFKA_TOPIC_ORDER,
            self.KAFKA_TOPIC_NEGOTIATION,
            self.KAFKA_TOPIC_PAYMENT
        ]
        
        for topic in topics:
            if not topic or not topic.strip():
                raise ValueError(f"Kafka topic name cannot be empty")
        
        # Validate consumer group IDs
        consumer_groups = [
            self.KAFKA_CONSUMER_GROUP_BACKEND,
            self.KAFKA_CONSUMER_GROUP_SCHEDULER,
            self.KAFKA_CONSUMER_GROUP_NEGOTIATOR
        ]
        
        for group in consumer_groups:
            if not group or not group.strip():
                raise ValueError(f"Kafka consumer group ID cannot be empty")

    def validate_stripe_configuration(self) -> None:
        """
        Validates Stripe-specific configuration settings.
        """
        if self.STRIPE_SECRET_KEY and not self.STRIPE_SECRET_KEY.startswith(('sk_test_', 'sk_live_')):
            raise ValueError("STRIPE_SECRET_KEY must start with 'sk_test_' or 'sk_live_'")
        
        if self.STRIPE_WEBHOOK_SECRET and not self.STRIPE_WEBHOOK_SECRET.startswith('whsec_'):
            raise ValueError("STRIPE_WEBHOOK_SECRET must start with 'whsec_'")


# Instantiate the settings object to be used throughout the application
settings = Settings()