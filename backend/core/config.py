import os
from typing import List, Literal
from dotenv import load_dotenv
import logging
from enum import Enum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file located in the parent directory
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
ENV_PATH = os.path.join(BASE_DIR, '.env')
load_dotenv(ENV_PATH)


def parse_cors(value: str) -> List[str]:
    """
    Parses CORS origins. Accepts comma-separated string or list-like string.
    Example: "http://localhost,http://127.0.0.1" → ["http://localhost", "http://127.0.0.1"]
    """
    if not value:
        return [
            "http://localhost:5173",  # Vite dev server
            "http://127.0.0.1:5173",
            "http://localhost:3000",  # optional if you also use CRA
        ]
    if isinstance(value, str):
        value = value.strip()
        if value.startswith("[") and value.endswith("]"):
            return [i.strip().strip("'\"") for i in value[1:-1].split(",")]
        return [i.strip() for i in value.split(",")]
    raise ValueError("Invalid CORS format")


class Settings:
    # Environment
    DOMAIN: str = os.getenv('DOMAIN', 'localhost')
    ENVIRONMENT: Literal["local", "staging",
                         "production"] = os.getenv('ENVIRONMENT', 'local')


    # SMS
    # SMS_API_KEY: Optional[str] = os.getenv('SMS_API_KEY')
    # SMS_API_URL: Optional[str] = os.getenv('SMS_API_URL')

    # Push Notifications
    # FIREBASE_CREDENTIALS_JSON: Optional[str] = os.getenv('FIREBASE_CREDENTIALS_JSON','')

    # PostgreSQL
    POSTGRES_USER: str = os.getenv('POSTGRES_USER', 'postgres')
    POSTGRES_PASSWORD: str = os.getenv(
        'POSTGRES_PASSWORD', '0ZTftS7B0Bsf3tlzddQs')
    POSTGRES_SERVER: str = os.getenv(
        'POSTGRES_SERVER', 'banwee-db.c2po20oyum9p.us-east-1.rds.amazonaws.com')
    POSTGRES_PORT: int = int(os.getenv('POSTGRES_PORT', 5432))
    POSTGRES_DB: str = os.getenv('POSTGRES_DB', 'banwee_db')
    POSTGRES_DB_URL: str = os.getenv(
        'POSTGRES_DB_URL', "postgresql+asyncpg://postgres:0ZTftS7B0Bsf3tlzddQs@banwee-db.c2po20oyum9p.us-east-1.rds.amazonaws.com:5432/banwee_db")

    # SQLite (fallback if needed)
    SQLITE_DB_PATH: str = os.getenv('SQLITE_DB_PATH', 'db1.db')

    # Security
    SECRET_KEY: str = os.getenv('SECRET_KEY')
    STRIPE_SECRET_KEY: str = os.getenv('STRIPE_SECRET_KEY')
    STRIPE_WEBHOOK_SECRET: str = os.getenv('STRIPE_WEBHOOK_SECRET')
    ALGORITHM: str = os.getenv('ALGORITHM', "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES', 30))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(
        os.getenv('REFRESH_TOKEN_EXPIRE_DAYS', 7))
    RESEND_API_KEY: str = os.getenv('RESEND_API_KEY')

    MAILGUN_API_KEY: str = os.getenv('MAILGUN_API_KEY', '')
    MAILGUN_DOMAIN: str = os.getenv('MAILGUN_DOMAIN', '')
    MAILGUN_SENDER_EMAIL: str = os.getenv('MAILGUN_SENDER_EMAIL', '')

    # Frontend URL
    FRONTEND_URL: str = os.getenv('FRONTEND_URL', 'http://localhost:5173')

    # Notification Cleanup
    NOTIFICATION_CLEANUP_DAYS: int = int(
        os.getenv('NOTIFICATION_CLEANUP_DAYS', 30))
    NOTIFICATION_CLEANUP_INTERVAL_SECONDS: int = int(
        os.getenv('NOTIFICATION_CLEANUP_INTERVAL_SECONDS', 86400))  # 24 hours

    # CORS
    RAW_CORS_ORIGINS: str = os.getenv('BACKEND_CORS_ORIGINS', '')
    BACKEND_CORS_ORIGINS: List[str] = parse_cors(RAW_CORS_ORIGINS)

    SMTP_HOSTNAME: str = os.getenv('SMTP_HOSTNAME', '')
    SMTP_USER: str = os.getenv('SMTP_USER', '')
    SMTP_PASSWORD: str = os.getenv('SMTP_PASSWORD', '')

    TELEGRAM_BOT_TOKEN: str = os.getenv('TELEGRAM_BOT_TOKEN', '')
    WHATSAPP_ACCESS_TOKEN: str = os.getenv('WHATSAPP_ACCESS_TOKEN', '')
    PHONE_NUMBER_ID: str = os.getenv('PHONE_NUMBER_ID', '')

    FACEBOOK_APP_ID: str = os.getenv('FACEBOOK_APP_ID')
    FACEBOOK_APP_SECRET: str = os.getenv('FACEBOOK_APP_SECRET')

    TIKTOK_CLIENT_KEY: str = os.getenv('TIKTOK_CLIENT_KEY')
    TIKTOK_CLIENT_SECRET: str = os.getenv('TIKTOK_CLIENT_SECRET')

    @property
    def server_host(self) -> str:
        return f"http://{self.DOMAIN}" if self.ENVIRONMENT == "local" else f"https://{self.DOMAIN}"

    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        if self.ENVIRONMENT in ["local"]:
            # Use SQLite for local development with PostgreSQL-compatible schema
            return f"sqlite+aiosqlite:///{self.SQLITE_DB_PATH}"
        elif self.ENVIRONMENT in ["staging", "production"]:
            # Use PostgreSQL for staging and production
            if self.POSTGRES_DB_URL:
                return self.POSTGRES_DB_URL
            return (
                f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
                f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
            )
        else:
            raise ValueError("Invalid ENVIRONMENT for database connection")


# Instantiate the settings object
settings = Settings()


class SecurityLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SecurityConfig:
    def __init__(self):
        self.security_level = SecurityLevel.MEDIUM
        self.cors_allow_credentials = True
        self.cors_max_age_seconds = 600
        self.cors_strict_origins = False
        self.enable_input_sanitization = True
        self.enable_rate_limiting = True


def get_security_config() -> SecurityConfig:
    """Get security configuration"""
    return SecurityConfig()


def get_security_monitor():
    """Get security monitor (placeholder)"""
    return None


def get_security_validator():
    """Get security validator (placeholder)"""
    return None
