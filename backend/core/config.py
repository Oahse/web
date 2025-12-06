import os
import re # NEW: For regex matching of file types
from typing import List, Literal, Dict, Any, Optional # NEW: Import Dict, Any, Optional
from dotenv import load_dotenv
import logging
from enum import Enum

# NEW: Imports for synchronous DB session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# Imports for async DB session
from sqlalchemy.ext.asyncio import AsyncSession
from models.settings import SystemSettings # NEW
from services.settings import SettingsService # NEW
from core.database import AsyncSessionDB # NEW: For async DB access in validator if needed


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
    # REDIS_URL for connecting to the Redis service (used for caching, Celery broker, etc.).
    # Defaults to 'redis://localhost:6379/0' for local development or Docker Compose.
    REDIS_URL: str = os.getenv('REDIS_URL', 'redis://redis:6379/0') # Corrected default to 'redis' service name
    
    # --- Frontend URL ---
    # FRONTEND_URL is the base URL of the frontend application, used for redirects, etc.
    FRONTEND_URL: str = os.getenv('FRONTEND_URL', 'http://localhost:5173')

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
        Used by Celery tasks and potentially by SecurityValidator for sync operations.
        """
        uri = self.SQLALCHEMY_DATABASE_URI
        # Replace asyncpg with psycopg2 for synchronous access
        return uri.replace('+asyncpg', '+psycopg2')


# Instantiate the settings object to be used throughout the application
settings = Settings()


class SecurityLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SecurityConfig:
    """
    Defines application-wide security configurations.
    These can be adjusted based on the deployment environment and security requirements.
    """
    def __init__(self):
        self.security_level = SecurityLevel.MEDIUM
        self.cors_allow_credentials = True
        self.cors_max_age_seconds = 600
        self.cors_strict_origins = False
        self.enable_input_sanitization = True
        self.enable_rate_limiting = True
        # File Upload Settings (will be overridden by SystemSettings from DB)
        self.max_file_size_mb = 10
        self.allowed_file_types = ["jpg", "jpeg", "png", "pdf"]


class SecurityValidator:
    """
    Performs various security validations.
    """
    def __init__(self, db_session: AsyncSession): # Accept AsyncSession via DI
        self._settings_service = SettingsService(db_session)

    async def validate_file_upload(self, filename: str, file_size: int) -> Dict[str, Any]:
        """
        Validates a file upload against configured max size and allowed types.
        file_size is expected in bytes. Max file size setting is in MB.
        """
        results = {"is_valid": True, "errors": [], "warnings": []}

        max_size_mb = await self._settings_service.get_setting_value("max_file_size", default=10) # Default to 10MB
        allowed_types_str = await self._settings_service.get_setting_value("allowed_file_types", default="jpg,jpeg,png,pdf")
        
        # Convert max_size_mb to bytes
        max_size_bytes = max_size_mb * 1024 * 1024

        # Validate file size
        if file_size > max_size_bytes:
            results["is_valid"] = False
            results["errors"].append(f"File size exceeds maximum limit of {max_size_mb} MB.")

        # Validate file type
        allowed_types = [ext.strip().lower() for ext in allowed_types_str.split(',') if ext.strip()]
        if not allowed_types:
            results["warnings"].append("No allowed file types configured. All types will be accepted.")
        else:
            file_extension = os.path.splitext(filename)[1].lstrip('.').lower()
            if file_extension not in allowed_types:
                results["is_valid"] = False
                results["errors"].append(f"File type '{file_extension}' is not allowed. Allowed types are: {allowed_types_str}.")

        return results


# Global instance of SecurityValidator is not ideal with async DB session.
# Will modify get_security_validator to be a dependency.
# _security_validator_instance: Optional[SecurityValidator] = None

# Modify get_security_validator to be an async dependency
async def get_security_validator(db_session: AsyncSession) -> SecurityValidator:
    """Provides an instance of the SecurityValidator with an AsyncSession."""
    return SecurityValidator(db_session)


def get_security_monitor():
    """Placeholder for a security monitoring instance."""
    return None
