# Docker Compose Environment Setup

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
