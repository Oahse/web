# Database Migrations

This document describes the simple database migration process using Alembic directly in Docker startup.

## Overview

The application uses Alembic for database migrations with a straightforward approach:

- Migrations run automatically when the backend container starts via Docker
- No migration utilities or complex tools - just Alembic
- Direct Alembic commands for all migration operations
- Simple, reliable, and integrated with Docker startup

## Automatic Migrations on Docker Start

When you start the application with `./docker-start.sh`, migrations are applied automatically:

1. The backend container starts
2. The `migrate.sh` script runs as part of container startup
3. Database connection is verified
4. Alembic applies any pending migrations with `alembic upgrade head`
5. The FastAPI application starts normally

This ensures your database is always up-to-date when the application starts.

## Manual Migration Commands

### Inside Docker Container

```bash
# Enter the backend container
docker-compose exec backend sh

# Check current migration status
alembic current

# Apply all pending migrations
alembic upgrade head

# Downgrade to previous migration
alembic downgrade -1

# Show migration history
alembic history

# View specific migration details
alembic show <revision_id>
```

### Creating New Migrations

```bash
# Enter the backend container
docker-compose exec backend sh

# Generate a new migration (auto-detects model changes)
alembic revision --autogenerate -m "Description of changes"

# Create empty migration file for manual changes
alembic revision -m "Manual migration description"
```

## Migration Files

Migration files are located in `backend/alembic/versions/` and follow Alembic's standard format.

## Database Backups

For production environments, use standard PostgreSQL backup tools:

```bash
# Create backup
pg_dump -h localhost -U banwee -d banwee_db > backup.sql

# Restore backup
psql -h localhost -U banwee -d banwee_db < backup.sql
```

## Troubleshooting

### Migration Fails

1. Check the container logs: `docker-compose logs backend`
2. Verify database connectivity
3. Check migration file syntax
4. Use `alembic downgrade` to revert if needed

### Container Won't Start

1. Check if migrations are failing in the logs
2. Temporarily comment out migration in `migrate.sh` to start container
3. Fix migration issues manually
4. Re-enable automatic migrations