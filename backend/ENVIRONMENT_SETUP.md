# Environment Setup Instructions for Backend

**Current Context:**
- Container: backend
- Docker: No
- Environment: Development

## Development Setup

1. Use localhost for service connections
2. Use Stripe test keys (sk_test_...)
3. Generate a secure SECRET_KEY:
   ```bash
   openssl rand -hex 32
   ```
