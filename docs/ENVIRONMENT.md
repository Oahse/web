# Environment Configuration Guide

This guide explains how to configure environment variables for the Banwee application across different environments.

## Quick Start

### Development Setup

1. Copy the example environment file:
   ```bash
   cp .env.example .dev.env
   ```

2. Update the following required variables in `.dev.env`:
   ```bash
   SECRET_KEY=<generate-with-openssl-rand-hex-32>
   STRIPE_SECRET_KEY=sk_test_<your-test-key>
   STRIPE_WEBHOOK_SECRET=whsec_<your-webhook-secret>
   POSTGRES_PASSWORD=<strong-password>
   ```

3. Start the application:
   ```bash
   docker-compose up -d
   ```

### Production Setup

1. Copy the example environment file:
   ```bash
   cp .env.example .prod.env
   ```

2. Update ALL required variables in `.prod.env` (see Production Checklist below)

3. Deploy using production configuration:
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

## Environment Files

The application uses different environment files based on the `ENVIRONMENT` variable:

- **`.dev.env`**: Development environment (ENVIRONMENT=local or dev)
- **`.prod.env`**: Production environment (ENVIRONMENT=production)
- **`.env.example`**: Template with all available variables and documentation

## Configuration Validation

The application validates all configuration at startup using Pydantic models. If validation fails, you'll see detailed error messages indicating which variables are missing or invalid.

### Validation Features

- **Type checking**: Ensures variables are the correct type (string, integer, URL, etc.)
- **Format validation**: Validates URLs, secrets, and other formatted values
- **Required field checking**: Ensures all required variables are present
- **Production-specific validation**: Stricter rules for production environments
- **Default values**: Provides sensible defaults where appropriate

## Required Variables

### Critical (Must be set in all environments)

| Variable | Description | Example |
|----------|-------------|---------|
| `SECRET_KEY` | JWT signing key (32+ chars, 64+ for prod) | `openssl rand -hex 32` |
| `STRIPE_SECRET_KEY` | Stripe API key | `sk_test_...` or `sk_live_...` |
| `STRIPE_WEBHOOK_SECRET` | Stripe webhook secret | `whsec_...` |
| `POSTGRES_PASSWORD` | Database password (8+ chars, 16+ for prod) | Strong password |
| `KAFKA_BOOTSTRAP_SERVERS` | Kafka connection | `kafka:29092` |

### Production-Only Required

| Variable | Description | Example |
|----------|-------------|---------|
| `MAILGUN_API_KEY` | Email sending API key | Your Mailgun key |
| `MAILGUN_DOMAIN` | Email domain | `mg.yourdomain.com` |

## Variable Categories

### 1. General Settings

```bash
ENVIRONMENT=local              # local, staging, or production
DOMAIN=localhost               # Application domain
```

### 2. URLs

```bash
FRONTEND_URL=http://localhost:5173
BACKEND_URL=http://localhost:8000
BACKEND_CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

### 3. Database (PostgreSQL)

```bash
POSTGRES_USER=banwee
POSTGRES_PASSWORD=banwee_password
POSTGRES_SERVER=postgres       # Use 'localhost' for local development
POSTGRES_PORT=5432
POSTGRES_DB=banwee_db
```

**Connection Pool Settings:**
```bash
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=30
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600
```

### 4. Redis

```bash
REDIS_URL=redis://redis:6379/0  # Use 'localhost' for local development
REDIS_CACHE_ENABLED=true
REDIS_RATELIMIT_ENABLED=true
REDIS_CACHE_TTL=3600
```

### 5. Kafka

```bash
KAFKA_BOOTSTRAP_SERVERS=kafka:29092  # Use 'localhost:9092' for local
KAFKA_TOPIC_EMAIL=banwee-email-notifications
KAFKA_TOPIC_NOTIFICATION=banwee-user-notifications
# ... (see .env.example for all topics)
```

### 6. Security

```bash
SECRET_KEY=<64-character-random-string>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
```

### 7. Payment (Stripe)

```bash
STRIPE_SECRET_KEY=sk_test_...        # Use sk_live_ in production
STRIPE_WEBHOOK_SECRET=whsec_...
VITE_STRIPE_PUBLIC_KEY=pk_test_...   # Use pk_live_ in production
```

### 8. Email (Mailgun)

```bash
MAILGUN_API_KEY=your_api_key
MAILGUN_DOMAIN=mg.yourdomain.com
MAILGUN_FROM_EMAIL=Banwee <noreply@yourdomain.com>
```

## Environment-Specific Configuration

### Development (Docker)

Use service names for inter-container communication:

```bash
POSTGRES_SERVER=postgres
REDIS_URL=redis://redis:6379/0
KAFKA_BOOTSTRAP_SERVERS=kafka:29092
```

### Development (Local)

Use localhost for local services:

```bash
POSTGRES_SERVER=localhost
REDIS_URL=redis://localhost:6379/0
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
```

### Production

Use production values and stricter security:

```bash
ENVIRONMENT=production
DOMAIN=api.banwee.com
FRONTEND_URL=https://www.banwee.com
BACKEND_URL=https://api.banwee.com

# Use production Stripe keys
STRIPE_SECRET_KEY=sk_live_...
VITE_STRIPE_PUBLIC_KEY=pk_live_...

# Strong secrets (64+ characters)
SECRET_KEY=<64-character-random-string>
POSTGRES_PASSWORD=<16-character-strong-password>
```

## Production Checklist

Before deploying to production, ensure:

- [ ] `ENVIRONMENT=production`
- [ ] `SECRET_KEY` is 64+ characters and randomly generated
- [ ] `POSTGRES_PASSWORD` is 16+ characters and strong
- [ ] `STRIPE_SECRET_KEY` starts with `sk_live_`
- [ ] `STRIPE_WEBHOOK_SECRET` is configured
- [ ] `MAILGUN_API_KEY` and `MAILGUN_DOMAIN` are set
- [ ] All URLs use HTTPS
- [ ] CORS origins are restricted to your domains
- [ ] Database credentials are secure
- [ ] All default values are changed
- [ ] Secrets are not committed to version control

## Generating Secure Values

### SECRET_KEY

Generate a secure random key:

```bash
# 32-byte (64-character) hex string
openssl rand -hex 32

# Or 64-byte (128-character) hex string for extra security
openssl rand -hex 64
```

### POSTGRES_PASSWORD

Generate a strong password:

```bash
# 24-character random password
openssl rand -base64 24
```

## Validation Errors

If you see validation errors at startup, check:

1. **Missing required variables**: Add them to your .env file
2. **Invalid format**: Check the format matches requirements (e.g., URLs start with http://)
3. **Production-specific errors**: Ensure production values meet stricter requirements
4. **Type errors**: Ensure numeric values are valid integers

### Common Validation Errors

**"SECRET_KEY must be at least 32 characters"**
- Generate a longer key: `openssl rand -hex 32`

**"STRIPE_SECRET_KEY must start with 'sk_test_' or 'sk_live_'"**
- Check your Stripe key format

**"Production environment should use live Stripe keys"**
- Change `sk_test_` to `sk_live_` in production

**"Database URL must start with postgresql://"**
- Check your `POSTGRES_DB_URL` format

## Docker Compose Configuration

The `docker-compose.yml` file automatically loads environment variables from `.dev.env` or `.prod.env` based on the `ENVIRONMENT` variable.

### Volume Configuration

Frontend volumes are configured to:
- Mount source files for hot reload
- Exclude `node_modules` to prevent conflicts
- Exclude `dist` to prevent build artifacts conflicts

```yaml
volumes:
  - ./frontend/src:/app/src:ro
  - ./frontend/public:/app/public:ro
  # ... other specific files
  - /app/node_modules  # Excluded
  - /app/dist          # Excluded
```

## Troubleshooting

### Application won't start

1. Check validation errors in logs
2. Verify all required variables are set
3. Ensure database/Redis/Kafka are running
4. Check service connectivity (use service names in Docker)

### Database connection fails

1. Verify `POSTGRES_SERVER` matches your setup (postgres for Docker, localhost for local)
2. Check `POSTGRES_PASSWORD` is correct
3. Ensure PostgreSQL is running and healthy

### Stripe webhooks fail

1. Verify `STRIPE_WEBHOOK_SECRET` is correct
2. Check webhook endpoint is configured in Stripe dashboard
3. Ensure webhook secret matches the endpoint

## Best Practices

1. **Never commit .env files**: Add `.dev.env` and `.prod.env` to `.gitignore`
2. **Use strong secrets**: Generate random values, don't use defaults
3. **Separate environments**: Use different values for dev/staging/prod
4. **Document changes**: Update `.env.example` when adding new variables
5. **Validate early**: Run validation before deployment
6. **Rotate secrets**: Regularly update production secrets
7. **Use secret management**: Consider using AWS Secrets Manager or similar for production

## Additional Resources

- [Pydantic Settings Documentation](https://docs.pydantic.dev/latest/usage/settings/)
- [FastAPI Configuration](https://fastapi.tiangolo.com/advanced/settings/)
- [Docker Compose Environment Variables](https://docs.docker.com/compose/environment-variables/)
- [Stripe API Keys](https://stripe.com/docs/keys)
