"""
Enhanced Environment Validator

Provides comprehensive validation for environment variables across different
deployment scenarios (Docker, local development, production).
"""

import os
import sys
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import logging
from dataclasses import dataclass

from .container_environment import (
    ContainerEnvironmentService,
    ValidationResult,
    EnvironmentVariable,
    VariableType
)

logger = logging.getLogger(__name__)


@dataclass
class EnvironmentContext:
    """Context information about the current environment"""
    is_docker: bool
    is_production: bool
    is_development: bool
    container_name: str
    env_file_path: Optional[str]


class EnvironmentValidator:
    """Enhanced environment validator with context-aware validation"""
    
    def __init__(self):
        self.context = self._detect_environment_context()
    
    def _detect_environment_context(self) -> EnvironmentContext:
        """Detect the current environment context"""
        
        # Check if running in Docker
        is_docker = (
            os.path.exists('/.dockerenv') or
            os.getenv('DOCKER_CONTAINER') == 'true' or
            os.getenv('KUBERNETES_SERVICE_HOST') is not None
        )
        
        # Check environment type
        env_type = os.getenv('ENVIRONMENT', 'local').lower()
        is_production = env_type in ['production', 'prod']
        is_development = env_type in ['development', 'dev', 'local']
        
        # Determine container name
        container_name = self._detect_container_name()
        
        # Find .env file
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
        
        # Check for explicit container name
        container_name = os.getenv('CONTAINER_NAME')
        if container_name:
            return container_name.lower()
        
        # Check current working directory
        cwd = Path.cwd()
        if 'backend' in cwd.parts:
            return 'backend'
        elif 'frontend' in cwd.parts:
            return 'frontend'
        elif 'negotiator' in cwd.parts:
            return 'negotiator'
        elif 'scheduler' in cwd.parts:
            return 'scheduler'
        
        # Default to backend if uncertain
        return 'backend'
    
    def _find_env_file(self) -> Optional[str]:
        """Find the appropriate .env file"""
        
        # Check current directory first
        current_env = Path('.env')
        if current_env.exists():
            return str(current_env)
        
        # Check container-specific locations
        container_paths = [
            Path('backend/.env'),
            Path('frontend/.env'),
            Path('../.env'),
            Path(f'{self.context.container_name}/.env') if hasattr(self, 'context') else None
        ]
        
        for path in container_paths:
            if path and path.exists():
                return str(path)
        
        return None
    
    def validate_startup_environment(self) -> ValidationResult:
        """
        Perform comprehensive startup validation with context awareness
        """
        try:
            logger.info(f"Validating environment for {self.context.container_name} container")
            logger.info(f"Context: Docker={self.context.is_docker}, "
                       f"Production={self.context.is_production}, "
                       f"Development={self.context.is_development}")
            
            # Load environment file if available
            if self.context.env_file_path:
                from dotenv import load_dotenv
                load_dotenv(self.context.env_file_path)
                logger.info(f"Loaded environment from {self.context.env_file_path}")
            
            # Get appropriate validation rules
            validation_rules = self._get_validation_rules()
            
            # Perform validation
            result = self._validate_with_context(validation_rules)
            
            # Add context-specific warnings
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
            rules = ContainerEnvironmentService.BACKEND_VARIABLES.copy()
        elif self.context.container_name == 'frontend':
            rules = ContainerEnvironmentService.FRONTEND_VARIABLES.copy()
        else:
            # Generic rules for other containers
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
            # In development, some production-only variables are optional
            for rule in rules:
                if rule.name in ['MAILGUN_API_KEY', 'MAILGUN_DOMAIN', 'STRIPE_WEBHOOK_SECRET']:
                    rule.required = False
        
        if self.context.is_production:
            # In production, ensure all security variables are present
            for rule in rules:
                if rule.sensitive and rule.name in ['SECRET_KEY', 'STRIPE_SECRET_KEY']:
                    rule.required = True
        
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
                error = self._validate_variable_with_context(rule, value)
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
    
    def _validate_variable_with_context(
        self, 
        rule: EnvironmentVariable, 
        value: str
    ) -> Optional[str]:
        """Validate a variable with context-specific rules"""
        
        # Use base validation first
        base_error = ContainerEnvironmentService._validate_variable_value(rule, value)
        if base_error:
            return base_error
        
        # Context-specific validation
        if self.context.is_production and rule.sensitive:
            # Stricter validation for production sensitive variables
            if rule.name == 'SECRET_KEY' and len(value) < 32:
                return "SECRET_KEY must be at least 32 characters in production"
            
            if 'test' in value.lower() and rule.name.startswith('STRIPE'):
                return f"Production environment should not use test Stripe keys"
        
        if self.context.is_development and rule.name.startswith('STRIPE'):
            # Warn about live keys in development
            if 'live' in value and not self.context.is_production:
                return "Development environment should use test Stripe keys (sk_test_)"
        
        # Docker-specific validation
        if self.context.is_docker:
            if rule.name in ['POSTGRES_SERVER', 'REDIS_URL', 'KAFKA_BOOTSTRAP_SERVERS']:
                if 'localhost' in value and self.context.is_production:
                    return f"Docker production should use service names, not localhost"
        
        return None
    
    def _add_context_warnings(self, result: ValidationResult):
        """Add context-specific warnings to the validation result"""
        
        if self.context.is_development:
            result.warnings.append("Running in development mode")
            
            if not self.context.env_file_path:
                result.warnings.append("No .env file found - using environment variables only")
        
        if self.context.is_production:
            result.warnings.append("Running in production mode")
            
            # Check for development artifacts in production
            dev_indicators = ['localhost', 'test', 'dev', 'debug']
            for var_name, var_value in os.environ.items():
                if any(indicator in var_value.lower() for indicator in dev_indicators):
                    if var_name in ['POSTGRES_SERVER', 'REDIS_URL', 'FRONTEND_URL']:
                        result.warnings.append(
                            f"Production environment has development-like value for {var_name}: {var_value}"
                        )
        
        if self.context.is_docker:
            result.warnings.append("Running in Docker container")
        else:
            result.warnings.append("Running in local environment")
    
    def generate_setup_instructions(self) -> str:
        """Generate context-specific setup instructions"""
        
        instructions = [
            f"# Environment Setup Instructions for {self.context.container_name.title()}",
            "",
            f"**Current Context:**",
            f"- Container: {self.context.container_name}",
            f"- Docker: {'Yes' if self.context.is_docker else 'No'}",
            f"- Environment: {'Production' if self.context.is_production else 'Development'}",
            "",
        ]
        
        if not self.context.env_file_path:
            instructions.extend([
                "## Missing .env File",
                "",
                "1. Create a .env file in the appropriate location:",
                f"   ```bash",
                f"   cp {self.context.container_name}/.env.example {self.context.container_name}/.env",
                f"   ```",
                "",
                "2. Edit the .env file with your configuration values",
                "",
            ])
        
        if self.context.is_development:
            instructions.extend([
                "## Development Setup",
                "",
                "1. Use localhost for service connections",
                "2. Use Stripe test keys (sk_test_...)",
                "3. Generate a secure SECRET_KEY:",
                "   ```bash",
                "   openssl rand -hex 32",
                "   ```",
                "",
            ])
        
        if self.context.is_production:
            instructions.extend([
                "## Production Setup",
                "",
                "1. Use Docker service names for connections",
                "2. Use Stripe live keys (sk_live_...)",
                "3. Ensure all sensitive variables are secure",
                "4. Verify no development artifacts remain",
                "",
            ])
        
        return "\n".join(instructions)


# Convenience function for startup validation
def validate_startup_environment() -> ValidationResult:
    """Validate environment for application startup"""
    validator = EnvironmentValidator()
    return validator.validate_startup_environment()


# Convenience function for setup instructions
def get_setup_instructions() -> str:
    """Get context-specific setup instructions"""
    validator = EnvironmentValidator()
    return validator.generate_setup_instructions()