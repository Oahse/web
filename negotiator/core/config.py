import os
from typing import Literal
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file located in the parent directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(BASE_DIR, '.env')
load_dotenv(ENV_PATH)

class Settings:
    # --- General Environment Settings ---
    ENVIRONMENT: Literal["local", "staging", "production"] = os.getenv('ENVIRONMENT', 'local')

    # --- PostgreSQL Database Configuration ---
    POSTGRES_USER: str = os.getenv('POSTGRES_USER', 'banwee')
    POSTGRES_PASSWORD: str = os.getenv('POSTGRES_PASSWORD', 'banwee_password')
    POSTGRES_SERVER: str = os.getenv('POSTGRES_SERVER', 'postgres')
    POSTGRES_PORT: int = int(os.getenv('POSTGRES_PORT', 5432))
    POSTGRES_DB: str = os.getenv('POSTGRES_DB', 'banwee_db')
    POSTGRES_DB_URL: str = os.getenv('POSTGRES_DB_URL', "")

    # --- Kafka Configuration ---
    KAFKA_BOOTSTRAP_SERVERS: str = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka:29092')
    KAFKA_TOPIC_NEGOTIATION: str = os.getenv('KAFKA_TOPIC_NEGOTIATION', 'banwee-negotiations')
    
    KAFKA_CONSUMER_GROUP_NEGOTIATOR: str = os.getenv('KAFKA_CONSUMER_GROUP_NEGOTIATOR', 'banwee-negotiator-consumers')
    
    KAFKA_AUTO_OFFSET_RESET: str = os.getenv('KAFKA_AUTO_OFFSET_RESET', 'earliest')
    KAFKA_ENABLE_AUTO_COMMIT: bool = os.getenv('KAFKA_ENABLE_AUTO_COMMIT', 'true').lower() == 'true'
    KAFKA_MAX_POLL_RECORDS: int = int(os.getenv('KAFKA_MAX_POLL_RECORDS', '500'))
    KAFKA_SESSION_TIMEOUT_MS: int = int(os.getenv('KAFKA_SESSION_TIMEOUT_MS', '30000'))
    KAFKA_HEARTBEAT_INTERVAL_MS: int = int(os.getenv('KAFKA_HEARTBEAT_INTERVAL_MS', '10000'))
    
    KAFKA_RETRY_BACKOFF_MS: int = int(os.getenv('KAFKA_RETRY_BACKOFF_MS', '1000'))
    KAFKA_MAX_RETRIES: int = int(os.getenv('KAFKA_MAX_RETRIES', '3'))
    KAFKA_REQUEST_TIMEOUT_MS: int = int(os.getenv('KAFKA_REQUEST_TIMEOUT_MS', '30000'))
    
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        if self.POSTGRES_DB_URL:
            return self.POSTGRES_DB_URL
        
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

settings = Settings()
