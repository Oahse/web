#!/usr/bin/env python3
"""
Environment Validation Script

This script validates all required environment variables for Banwee containers.
It provides context-aware validation and setup instructions.
"""

import sys
import os
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from core.environment_validator import EnvironmentValidator, validate_startup_environment
from core.container_environment import ContainerEnvironmentService, load_and_validate_all_containers
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main validation function with enhanced context awareness"""
    try:
        logger.info("Starting comprehensive environment validation for Banwee...")
        
        # Create validator instance
        validator = EnvironmentValidator()
        
        logger.info(f"Detected context:")
        logger.info(f"  - Container: {validator.context.container_name}")
        logger.info(f"  - Docker: {validator.context.is_docker}")
        logger.info(f"  - Production: {validator.context.is_production}")
        logger.info(f"  - Development: {validator.context.is_development}")
        logger.info(f"  - Env file: {validator.context.env_file_path}")
        
        # Perform validation
        validation_result = validate_startup_environment()
        
        if validation_result.is_valid:
            logger.info("✅ All required environment variables are valid!")
            
            # Print warnings if any
            if validation_result.warnings:
                logger.warning("Warnings:")
                for warning in validation_result.warnings:
                    logger.warning(f"  - {warning}")
            
            # Generate documentation if possible
            try:
                containers = load_and_validate_all_containers()
                documentation = ContainerEnvironmentService.generate_env_documentation(containers)
                
                doc_file = backend_dir / "ENVIRONMENT_VARIABLES.md"
                with open(doc_file, 'w') as f:
                    f.write(documentation)
                logger.info(f"Generated environment documentation: {doc_file}")
                
            except Exception as e:
                logger.warning(f"Could not generate documentation: {e}")
            
            # Generate setup instructions
            try:
                instructions = validator.generate_setup_instructions()
                instructions_file = backend_dir / "ENVIRONMENT_SETUP.md"
                with open(instructions_file, 'w') as f:
                    f.write(instructions)
                logger.info(f"Generated setup instructions: {instructions_file}")
                
            except Exception as e:
                logger.warning(f"Could not generate setup instructions: {e}")
            
            return 0
            
        else:
            logger.error("❌ Environment validation failed!")
            
            if validation_result.error_message:
                logger.error(validation_result.error_message)
            
            # Print specific issues
            if validation_result.missing_variables:
                logger.error("Missing required variables:")
                for var in validation_result.missing_variables:
                    logger.error(f"  - {var}")
            
            if validation_result.invalid_variables:
                logger.error("Invalid variables:")
                for var, error in validation_result.invalid_variables:
                    logger.error(f"  - {var}: {error}")
            
            # Print context-specific setup instructions
            logger.error("\n" + "="*60)
            logger.error("SETUP INSTRUCTIONS:")
            logger.error("="*60)
            
            try:
                instructions = validator.generate_setup_instructions()
                logger.error(instructions)
            except Exception as e:
                logger.error(f"Could not generate setup instructions: {e}")
                # Fallback instructions
                logger.error("1. Copy .env.example to .env in the appropriate directory")
                logger.error("2. Update the variables with your specific values")
                logger.error("3. Ensure all required variables are set")
                logger.error("4. For production, use secure values for sensitive variables")
            
            logger.error("="*60)
            
            return 1
            
    except Exception as e:
        logger.error(f"Validation script failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)