#!/usr/bin/env python3
"""
Environment Documentation Generator

This script generates comprehensive documentation for all environment variables
used across Banwee containers, including setup instructions and examples.
"""

import sys
import os
from pathlib import Path
from typing import Dict, List

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from core.container_environment import (
    ContainerEnvironmentService,
    ContainerConfig,
    EnvironmentType,
    EnvironmentVariable,
    VariableType
)
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def generate_env_example_files():
    """Generate .env.example files for each container with proper documentation"""
    
    # Backend .env.example
    backend_example = generate_backend_env_example()
    backend_example_path = backend_dir / ".env.example"
    
    with open(backend_example_path, 'w') as f:
        f.write(backend_example)
    logger.info(f"Generated {backend_example_path}")
    
    # Frontend .env.example
    frontend_example = generate_frontend_env_example()
    frontend_example_path = backend_dir.parent / "frontend" / ".env.example"
    
    if frontend_example_path.parent.exists():
        with open(frontend_example_path, 'w') as f:
            f.write(frontend_example)
        logger.info(f"Generated {frontend_example_path}")


def generate_backend_env_example() -> str:
    """Generate backend .env.example content with comprehensive documentation"""
    
    lines = [
        "# ============================================",
        "# BANWEE BACKEND CONFIGURATION",
        "# ============================================",
        "# This file works for both local development and Docker environments",
        "# Copy this file to .env and update the values for your environment",
        "",
        "# IMPORTANT: Never commit the actual .env file to version control!",
        "# The .env file should contain your actual secrets and configuration.",
        "",
    ]
    
    # Get backend variable definitions
    variables = ContainerEnvironmentService.BACKEND_VARIABLES
    
    # Group variables by category
    categories = {}
    for var in variables:
        category = ContainerEnvironmentService._categorize_variable(var.name)
        if category not in categories:
            categories[category] = []
        categories[category].append(var)
    
    # Generate documentation for each category
    for category, vars_in_category in categories.items():
        lines.extend([
            f"# {category} Configuration",
            f"# {'=' * (len(category) + 14)}",
        ])
        
        for var in vars_in_category:
            lines.append("")
            lines.append(f"# {var.description}")
            
            if var.required:
                lines.append("# REQUIRED")
            else:
                lines.append("# OPTIONAL")
            
            if var.sensitive:
                lines.append("# ⚠️  SENSITIVE: Keep this value secure!")
            
            if var.validation_pattern:
                lines.append(f"# Pattern: {var.validation_pattern}")
            
            if var.dev_override or var.prod_override:
                lines.append("# Environment-specific overrides:")
                if var.dev_override:
                    lines.append(f"#   Development: {var.dev_override}")
                if var.prod_override:
                    lines.append(f"#   Production: {var.prod_override}")
            
            # Add the variable with example value
            example_value = var.default_value or _get_example_value(var)
            if var.sensitive and example_value:
                example_value = _mask_sensitive_value(example_value)
            
            lines.append(f"{var.name}={example_value}")
        
        lines.append("")
    
    # Add setup instructions
    lines.extend([
        "",
        "# ============================================",
        "# SETUP INSTRUCTIONS",
        "# ============================================",
        "",
        "# 1. Copy this file to .env:",
        "#    cp .env.example .env",
        "",
        "# 2. Update the values above with your actual configuration",
        "",
        "# 3. For local development:",
        "#    - Use localhost for database/redis connections",
        "#    - Use test Stripe keys (sk_test_...)",
        "#    - Generate a secure SECRET_KEY: openssl rand -hex 32",
        "",
        "# 4. For production:",
        "#    - Use Docker service names for connections",
        "#    - Use live Stripe keys (sk_live_...)",
        "#    - Use strong, unique passwords and secrets",
        "",
        "# 5. Environment-specific behavior:",
        "#    - Set ENVIRONMENT=local for development",
        "#    - Set ENVIRONMENT=production for production",
        "#    - Overrides are applied automatically based on ENVIRONMENT",
        "",
    ])
    
    return "\n".join(lines)


def generate_frontend_env_example() -> str:
    """Generate frontend .env.example content"""
    
    lines = [
        "# ============================================",
        "# BANWEE FRONTEND CONFIGURATION",
        "# ============================================",
        "# This file works for both local development and Docker environments",
        "# Copy this file to .env and update the values for your environment",
        "",
    ]
    
    variables = ContainerEnvironmentService.FRONTEND_VARIABLES
    
    for var in variables:
        lines.append("")
        lines.append(f"# {var.description}")
        
        if var.required:
            lines.append("# REQUIRED")
        else:
            lines.append("# OPTIONAL")
        
        if var.validation_pattern:
            lines.append(f"# Pattern: {var.validation_pattern}")
        
        example_value = var.default_value or _get_example_value(var)
        lines.append(f"{var.name}={example_value}")
    
    return "\n".join(lines)


def _get_example_value(var: EnvironmentVariable) -> str:
    """Get an example value for a variable based on its type and name"""
    
    if var.variable_type == VariableType.SECRET:
        if "stripe" in var.name.lower():
            if "webhook" in var.name.lower():
                return "whsec_your_stripe_webhook_secret_here"
            else:
                return "sk_test_your_stripe_secret_key_here"
        elif "secret_key" in var.name.lower():
            return "your-super-secret-key-change-in-production-min-32-chars"
        elif "mailgun" in var.name.lower():
            return "your_mailgun_api_key_here"
        else:
            return "your_secret_value_here"
    
    elif var.variable_type == VariableType.URL:
        if "postgres" in var.name.lower():
            return "postgresql+asyncpg://user:password@host:5432/database"
        elif "redis" in var.name.lower():
            return "redis://localhost:6379/0"
        elif "api" in var.name.lower():
            return "http://localhost:8000/api/v1"
        else:
            return "http://localhost:3000"
    
    elif var.variable_type == VariableType.INTEGER:
        if "port" in var.name.lower():
            return "5432"
        else:
            return "30"
    
    elif var.variable_type == VariableType.BOOLEAN:
        return "true"
    
    elif var.variable_type == VariableType.EMAIL:
        return "noreply@yourdomain.com"
    
    else:
        # String type
        if "domain" in var.name.lower():
            return "yourdomain.com"
        elif "environment" in var.name.lower():
            return "local"
        elif "name" in var.name.lower():
            return "Banwee"
        else:
            return "your_value_here"


def _mask_sensitive_value(value: str) -> str:
    """Mask sensitive values for example files"""
    if len(value) <= 8:
        return "your_secret_here"
    
    # Show first 4 and last 4 characters with asterisks in between
    return f"{value[:4]}{'*' * (len(value) - 8)}{value[-4:]}"


def generate_docker_compose_env_docs():
    """Generate documentation for Docker Compose environment setup"""
    
    content = """# Docker Compose Environment Setup

This document explains how to configure environment variables for Docker Compose deployment.

## File Structure

```
banwee/
├── docker-compose.yml
├── backend/
│   ├── .env              # Backend environment variables
│   └── .env.example      # Backend example configuration
└── frontend/
    ├── .env              # Frontend environment variables
    └── .env.example      # Frontend example configuration
```

## Setup Process

1. **Copy example files:**
   ```bash
   cp backend/.env.example backend/.env
   cp frontend/.env.example frontend/.env
   ```

2. **Update configuration:**
   - Edit `backend/.env` with your actual values
   - Edit `frontend/.env` with your actual values

3. **Environment-specific settings:**
   - Set `ENVIRONMENT=local` for development
   - Set `ENVIRONMENT=production` for production
   - Automatic overrides are applied based on this setting

## Service Connections

### Development (ENVIRONMENT=local)
- Database: `localhost:5432`
- Redis: `localhost:6379`
- Kafka: `localhost:9092`

### Production (ENVIRONMENT=production)
- Database: `postgres:5432` (Docker service name)
- Redis: `redis:6379` (Docker service name)
- Kafka: `kafka:29092` (Docker service name)

## Security Considerations

1. **Never commit .env files** to version control
2. **Use strong secrets** for production
3. **Rotate API keys** regularly
4. **Use test Stripe keys** for development
5. **Use live Stripe keys** for production

## Validation

The application automatically validates environment variables on startup:

```bash
# Manual validation
python backend/validate_environment.py

# Docker validation (automatic)
docker-compose up
```

## Troubleshooting

### Common Issues

1. **Missing variables:** Check the error message and add missing variables to .env
2. **Invalid format:** Ensure URLs start with http:// or https://
3. **Stripe keys:** Ensure test keys start with sk_test_ and live keys with sk_live_
4. **Database connection:** Verify PostgreSQL is running and accessible

### Getting Help

1. Check the generated `ENVIRONMENT_VARIABLES.md` for detailed documentation
2. Run `python backend/validate_environment.py` for specific error messages
3. Ensure all required services are running (PostgreSQL, Redis, Kafka)
"""
    
    doc_path = backend_dir.parent / "DOCKER_ENVIRONMENT_SETUP.md"
    with open(doc_path, 'w') as f:
        f.write(content)
    
    logger.info(f"Generated Docker environment documentation: {doc_path}")


def main():
    """Main function to generate all documentation"""
    try:
        logger.info("Generating environment documentation...")
        
        # Generate .env.example files
        generate_env_example_files()
        
        # Generate Docker Compose documentation
        generate_docker_compose_env_docs()
        
        # Generate comprehensive variable documentation
        try:
            from core.container_environment import load_and_validate_all_containers
            containers = load_and_validate_all_containers()
            documentation = ContainerEnvironmentService.generate_env_documentation(containers)
            
            doc_file = backend_dir.parent / "ENVIRONMENT_VARIABLES.md"
            with open(doc_file, 'w') as f:
                f.write(documentation)
            logger.info(f"Generated comprehensive documentation: {doc_file}")
            
        except Exception as e:
            logger.warning(f"Could not generate comprehensive documentation: {e}")
        
        logger.info("✅ Documentation generation completed successfully!")
        return 0
        
    except Exception as e:
        logger.error(f"Documentation generation failed: {e}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)