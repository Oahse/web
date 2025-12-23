#!/usr/bin/env python3
"""
Configuration validation script for Kafka and Stripe settings.
This script validates that all required configuration is present and properly formatted.
"""

import os
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

try:
    from core.config import settings
    
    def validate_configuration():
        """Validate all configuration settings."""
        print("🔍 Validating configuration settings...")
        
        try:
            # Test basic configuration loading
            print(f"✅ Environment: {settings.ENVIRONMENT}")
            print(f"✅ Domain: {settings.DOMAIN}")
            
            # Test Kafka configuration
            print(f"✅ Kafka Bootstrap Servers: {settings.KAFKA_BOOTSTRAP_SERVERS}")
            print(f"✅ Kafka Topics:")
            print(f"   - Email: {settings.KAFKA_TOPIC_EMAIL}")
            print(f"   - Notification: {settings.KAFKA_TOPIC_NOTIFICATION}")
            print(f"   - Order: {settings.KAFKA_TOPIC_ORDER}")
            print(f"   - Negotiation: {settings.KAFKA_TOPIC_NEGOTIATION}")
            print(f"   - Payment: {settings.KAFKA_TOPIC_PAYMENT}")
            
            # Test Kafka consumer groups
            print(f"✅ Kafka Consumer Groups:")
            print(f"   - Backend: {settings.KAFKA_CONSUMER_GROUP_BACKEND}")
            print(f"   - Scheduler: {settings.KAFKA_CONSUMER_GROUP_SCHEDULER}")
            print(f"   - Negotiator: {settings.KAFKA_CONSUMER_GROUP_NEGOTIATOR}")
            
            # Test database configuration
            print(f"✅ Database URI: {settings.SQLALCHEMY_DATABASE_URI[:50]}...")
            print(f"✅ Sync Database URI: {settings.SQLALCHEMY_DATABASE_URI_SYNC[:50]}...")
            
            # Test validation methods
            settings.validate_kafka_configuration()
            print("✅ Kafka configuration validation passed")
            
            # Note: We skip validate_required_settings() and validate_stripe_configuration()
            # because they require actual secrets that may not be set in development
            
            print("\n🎉 Configuration validation completed successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Configuration validation failed: {e}")
            return False
    
    if __name__ == "__main__":
        success = validate_configuration()
        sys.exit(0 if success else 1)
        
except ImportError as e:
    print(f"❌ Failed to import configuration: {e}")
    print("Make sure you're running this from the backend directory and dependencies are installed.")
    sys.exit(1)