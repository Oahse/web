# Banwee Environment Variables Documentation

This document describes all environment variables used across Banwee containers.
Each container has its own .env file with support for dev/prod overrides.

## Setup Instructions

1. Copy the appropriate `.env.example` file to `.env` in each container directory
2. Update the variables with your specific values
3. For production, ensure all sensitive variables are properly secured
4. The same .env file works for both development and production environments

## Environment-Specific Behavior

- **Development**: Uses localhost for service connections
- **Production**: Uses Docker service names for connections
- **Overrides**: Automatically applied based on ENVIRONMENT variable

## Security Notes

- Never commit .env files to version control
- Use strong, unique values for all SECRET_KEY variables
- Rotate API keys and passwords regularly
- Use environment-specific Stripe keys (test vs live)
