"""
Container Environment Management Service

This service provides comprehensive environment variable management for Docker containers,
supporting single .env files per container with dev/prod overrides, validation,
and secure handling of sensitive variables.
"""

import os
import re
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import logging
from dotenv import load_dotenv
import json


logger = logging.getLogger(__name__)


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
    SECRET = "secret"  # Sensitive data like API keys, passwords
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
    invalid_variables: List[Tuple[str, str]] = field(default_factory=list)  # (name, error)
    warnings: List[str] = field(default_factory=list)
    error_message: Optional[str] = None


@dataclass
class ContainerConfig:
    """Configuration for a specific container"""
    container_name: str
    env_file_path: str
    required_variables: List[EnvironmentVariable]
    environment_type: EnvironmentType
    loaded_variables: Dict[str, str] = field(default_factory=dict)
    validation_result: Optional[ValidationResult] = None


class ContainerEnvironmentService:
    """
    Service for managing Docker container environment variables with support for:
    - Single .env file per container with dev/prod overrides
    - Comprehensive validation of required settings
    - Secure handling of sensitive variables
    - Clear error messages for missing or invalid variables
    """
    
    # Common environment variable definitions for different containers
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
            validation_pattern=r"^.{32,}$"  # At least 32 characters
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
            validation_pattern=r"^whsec_[a-zA-Z0-9_]{10,}$"  # More flexible pattern
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
    ]
    
    FRONTEND_VARIABLES = [
        EnvironmentVariable(
            name="VITE_API_BASE_URL",
            description="Backend API base URL",
            variable_type=VariableType.URL,
            required=True,
            default_value="http://localhost:8000/api/v1"
        ),
        EnvironmentVariable(
            name="VITE_STRIPE_PUBLIC_KEY",
            description="Stripe publishable key",
            variable_type=VariableType.STRING,
            required=True,
            validation_pattern=r"^pk_(test_|live_)[a-zA-Z0-9]{99}$"
        ),
        EnvironmentVariable(
            name="VITE_APP_NAME",
            description="Application name",
            variable_type=VariableType.STRING,
            required=True,
            default_value="Banwee"
        ),
        EnvironmentVariable(
            name="VITE_APP_URL",
            description="Application URL",
            variable_type=VariableType.URL,
            required=True,
            default_value="http://localhost:5173"
        ),
    ]

    @staticmethod
    def validate_environment_variables(
        required_vars: List[str],
        container_name: str
    ) -> ValidationResult:
        """
        Validate that all required environment variables are present and valid.
        
        Args:
            required_vars: List of required variable names
            container_name: Name of the container for context
            
        Returns:
            ValidationResult with validation status and details
        """
        try:
            # Get variable definitions for the container
            var_definitions = ContainerEnvironmentService._get_variable_definitions(container_name)
            var_dict = {var.name: var for var in var_definitions}
            
            missing_variables = []
            invalid_variables = []
            warnings = []
            
            # Check each required variable
            for var_name in required_vars:
                var_def = var_dict.get(var_name)
                if not var_def:
                    warnings.append(f"Variable {var_name} not found in definitions for {container_name}")
                    continue
                
                value = os.getenv(var_name)
                
                # Check if required variable is missing
                if var_def.required and not value:
                    if var_def.default_value:
                        warnings.append(f"Using default value for {var_name}")
                        os.environ[var_name] = var_def.default_value
                    else:
                        missing_variables.append(var_name)
                        continue
                
                # Validate variable if present
                if value:
                    validation_error = ContainerEnvironmentService._validate_variable_value(
                        var_def, value
                    )
                    if validation_error:
                        invalid_variables.append((var_name, validation_error))
            
            # Generate error message if validation failed
            error_message = None
            if missing_variables or invalid_variables:
                error_parts = []
                
                if missing_variables:
                    error_parts.append(
                        f"Missing required environment variables for {container_name}:\n" +
                        "\n".join(f"  - {var}: {var_dict.get(var, {}).description if var in var_dict else 'No description'}" 
                                 for var in missing_variables)
                    )
                
                if invalid_variables:
                    error_parts.append(
                        f"Invalid environment variables for {container_name}:\n" +
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
            
        except Exception as e:
            logger.error(f"Error validating environment variables for {container_name}: {e}")
            return ValidationResult(
                is_valid=False,
                error_message=f"Validation error for {container_name}: {str(e)}"
            )

    @staticmethod
    def load_container_config(
        env_file_path: str,
        environment: str  # "dev" or "prod"
    ) -> ContainerConfig:
        """
        Load container configuration from .env file with environment-specific overrides.
        
        Args:
            env_file_path: Path to the .env file
            environment: Environment type ("dev", "prod", "staging", "local")
            
        Returns:
            ContainerConfig with loaded variables and validation results
        """
        try:
            # Determine environment type
            env_type = EnvironmentType.DEVELOPMENT
            if environment.lower() in ["prod", "production"]:
                env_type = EnvironmentType.PRODUCTION
            elif environment.lower() == "staging":
                env_type = EnvironmentType.STAGING
            elif environment.lower() == "local":
                env_type = EnvironmentType.LOCAL
            
            # Extract container name from path
            container_name = ContainerEnvironmentService._extract_container_name(env_file_path)
            
            # Load environment variables from file
            if os.path.exists(env_file_path):
                load_dotenv(env_file_path, override=False)  # Don't override existing env vars
            else:
                logger.warning(f"Environment file not found: {env_file_path}")
            
            # Get variable definitions for this container
            var_definitions = ContainerEnvironmentService._get_variable_definitions(container_name)
            
            # Apply environment-specific overrides
            loaded_variables = {}
            for var_def in var_definitions:
                value = os.getenv(var_def.name)
                
                # Apply environment-specific overrides
                if env_type == EnvironmentType.DEVELOPMENT and var_def.dev_override:
                    value = var_def.dev_override
                    os.environ[var_def.name] = value
                elif env_type == EnvironmentType.PRODUCTION and var_def.prod_override:
                    value = var_def.prod_override
                    os.environ[var_def.name] = value
                
                # Use default if no value is set
                if not value and var_def.default_value:
                    value = var_def.default_value
                    os.environ[var_def.name] = value
                
                if value:
                    loaded_variables[var_def.name] = value
            
            # Validate the configuration
            required_vars = [var.name for var in var_definitions if var.required]
            validation_result = ContainerEnvironmentService.validate_environment_variables(
                required_vars, container_name
            )
            
            return ContainerConfig(
                container_name=container_name,
                env_file_path=env_file_path,
                required_variables=var_definitions,
                environment_type=env_type,
                loaded_variables=loaded_variables,
                validation_result=validation_result
            )
            
        except Exception as e:
            logger.error(f"Error loading container config from {env_file_path}: {e}")
            raise ValueError(f"Failed to load container configuration: {str(e)}")

    @staticmethod
    def generate_env_documentation(
        container_configs: Dict[str, ContainerConfig]
    ) -> str:
        """
        Generate comprehensive documentation for environment variables across all containers.
        
        Args:
            container_configs: Dictionary of container name to ContainerConfig
            
        Returns:
            Formatted documentation string
        """
        try:
            doc_lines = [
                "# Banwee Environment Variables Documentation",
                "",
                "This document describes all environment variables used across Banwee containers.",
                "Each container has its own .env file with support for dev/prod overrides.",
                "",
            ]
            
            for container_name, config in container_configs.items():
                doc_lines.extend([
                    f"## {container_name.title()} Container",
                    "",
                    f"**Environment File:** `{config.env_file_path}`",
                    f"**Environment Type:** {config.environment_type.value}",
                    "",
                ])
                
                # Group variables by category
                categories = {
                    "Database": [],
                    "Security": [],
                    "External Services": [],
                    "Application": [],
                    "Other": []
                }
                
                for var in config.required_variables:
                    category = ContainerEnvironmentService._categorize_variable(var.name)
                    categories[category].append(var)
                
                # Document each category
                for category, variables in categories.items():
                    if not variables:
                        continue
                        
                    doc_lines.extend([
                        f"### {category} Configuration",
                        "",
                    ])
                    
                    for var in variables:
                        doc_lines.extend([
                            f"**{var.name}**",
                            f"- Description: {var.description}",
                            f"- Type: {var.variable_type.value}",
                            f"- Required: {'Yes' if var.required else 'No'}",
                        ])
                        
                        if var.default_value:
                            doc_lines.append(f"- Default: `{var.default_value}`")
                        
                        if var.dev_override:
                            doc_lines.append(f"- Development Override: `{var.dev_override}`")
                        
                        if var.prod_override:
                            doc_lines.append(f"- Production Override: `{var.prod_override}`")
                        
                        if var.sensitive:
                            doc_lines.append("- **⚠️ SENSITIVE**: Handle securely, do not log or expose")
                        
                        if var.validation_pattern:
                            doc_lines.append(f"- Validation Pattern: `{var.validation_pattern}`")
                        
                        doc_lines.append("")
                
                doc_lines.append("---")
                doc_lines.append("")
            
            # Add setup instructions
            doc_lines.extend([
                "## Setup Instructions",
                "",
                "1. Copy the appropriate `.env.example` file to `.env` in each container directory",
                "2. Update the variables with your specific values",
                "3. For production, ensure all sensitive variables are properly secured",
                "4. The same .env file works for both development and production environments",
                "",
                "## Environment-Specific Behavior",
                "",
                "- **Development**: Uses localhost for service connections",
                "- **Production**: Uses Docker service names for connections",
                "- **Overrides**: Automatically applied based on ENVIRONMENT variable",
                "",
                "## Security Notes",
                "",
                "- Never commit .env files to version control",
                "- Use strong, unique values for all SECRET_KEY variables",
                "- Rotate API keys and passwords regularly",
                "- Use environment-specific Stripe keys (test vs live)",
                "",
            ])
            
            return "\n".join(doc_lines)
            
        except Exception as e:
            logger.error(f"Error generating environment documentation: {e}")
            return f"Error generating documentation: {str(e)}"

    @staticmethod
    def _get_variable_definitions(container_name: str) -> List[EnvironmentVariable]:
        """Get variable definitions for a specific container"""
        if container_name.lower() in ["backend", "api", "main"]:
            return ContainerEnvironmentService.BACKEND_VARIABLES
        elif container_name.lower() in ["frontend", "web", "ui"]:
            return ContainerEnvironmentService.FRONTEND_VARIABLES
        else:
            # Return common variables for unknown containers
            return [
                EnvironmentVariable(
                    name="ENVIRONMENT",
                    description="Application environment",
                    variable_type=VariableType.STRING,
                    required=True,
                    default_value="local"
                )
            ]

    @staticmethod
    def _extract_container_name(env_file_path: str) -> str:
        """Extract container name from environment file path"""
        path = Path(env_file_path)
        
        # If path contains 'backend', 'frontend', etc., use that
        parts = path.parts
        for part in parts:
            if part.lower() in ["backend", "frontend", "negotiator", "scheduler"]:
                return part.lower()
        
        # Default to parent directory name
        return path.parent.name.lower()

    @staticmethod
    def _validate_variable_value(var_def: EnvironmentVariable, value: str) -> Optional[str]:
        """
        Validate a single environment variable value.
        
        Returns:
            Error message if invalid, None if valid
        """
        try:
            # Type-specific validation
            if var_def.variable_type == VariableType.INTEGER:
                try:
                    int(value)
                except ValueError:
                    return f"Must be a valid integer, got: {value}"
            
            elif var_def.variable_type == VariableType.FLOAT:
                try:
                    float(value)
                except ValueError:
                    return f"Must be a valid float, got: {value}"
            
            elif var_def.variable_type == VariableType.BOOLEAN:
                if value.lower() not in ["true", "false", "1", "0", "yes", "no"]:
                    return f"Must be a boolean value (true/false), got: {value}"
            
            elif var_def.variable_type == VariableType.URL:
                if not value.startswith(("http://", "https://", "redis://", "postgresql://", "postgresql+asyncpg://")):
                    return f"Must be a valid URL, got: {value}"
            
            elif var_def.variable_type == VariableType.EMAIL:
                if "@" not in value or "." not in value.split("@")[-1]:
                    return f"Must be a valid email address, got: {value}"
            
            elif var_def.variable_type == VariableType.JSON:
                try:
                    json.loads(value)
                except json.JSONDecodeError:
                    return f"Must be valid JSON, got: {value}"
            
            # Pattern validation
            if var_def.validation_pattern:
                if not re.match(var_def.validation_pattern, value):
                    return f"Does not match required pattern: {var_def.validation_pattern}"
            
            # Sensitive variable checks
            if var_def.sensitive:
                if len(value) < 8:
                    return "Sensitive variables must be at least 8 characters long"
                
                # Check for common weak values
                weak_values = ["password", "secret", "key", "test", "admin", "default"]
                if value.lower() in weak_values:
                    return f"Sensitive variable cannot use common weak value: {value}"
            
            return None
            
        except Exception as e:
            return f"Validation error: {str(e)}"

    @staticmethod
    def _categorize_variable(var_name: str) -> str:
        """Categorize a variable for documentation purposes"""
        name_lower = var_name.lower()
        
        if any(db_term in name_lower for db_term in ["postgres", "redis", "kafka", "database", "db"]):
            return "Database"
        elif any(sec_term in name_lower for sec_term in ["secret", "key", "password", "token"]):
            return "Security"
        elif any(ext_term in name_lower for ext_term in ["stripe", "mailgun", "smtp", "api", "oauth"]):
            return "External Services"
        elif any(app_term in name_lower for app_term in ["environment", "domain", "url", "cors", "frontend"]):
            return "Application"
        else:
            return "Other"


# Convenience functions for common operations
def validate_backend_environment() -> ValidationResult:
    """Validate backend container environment variables"""
    required_vars = [var.name for var in ContainerEnvironmentService.BACKEND_VARIABLES if var.required]
    return ContainerEnvironmentService.validate_environment_variables(required_vars, "backend")


def validate_frontend_environment() -> ValidationResult:
    """Validate frontend container environment variables"""
    required_vars = [var.name for var in ContainerEnvironmentService.FRONTEND_VARIABLES if var.required]
    return ContainerEnvironmentService.validate_environment_variables(required_vars, "frontend")


def load_and_validate_all_containers() -> Dict[str, ContainerConfig]:
    """Load and validate all container configurations"""
    containers = {}
    
    # Backend container
    backend_env_path = os.path.join("backend", ".env")
    if os.path.exists(backend_env_path):
        containers["backend"] = ContainerEnvironmentService.load_container_config(
            backend_env_path, os.getenv("ENVIRONMENT", "local")
        )
    
    # Frontend container
    frontend_env_path = os.path.join("frontend", ".env")
    if os.path.exists(frontend_env_path):
        containers["frontend"] = ContainerEnvironmentService.load_container_config(
            frontend_env_path, os.getenv("ENVIRONMENT", "local")
        )
    
    return containers