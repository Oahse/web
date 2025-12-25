# Database Migrations

This document describes the simplified database migration process using Alembic directly.

## Overview

The application uses Alembic for database migrations with a simple, straightforward approach:

- Migrations run automatically when the backend container starts
- No complex backup/restore utilities - use standard database backup tools if needed
- Direct Alembic commands for all migration operations

## Automatic Migrations

When you start the application with `./docker-start.sh`, migrations are applied automatically:

1. The backend container starts
2. The `migrate.sh` script runs inside the container
3. Alembic applies any pending migrations with `alembic upgrade head`
4. The application starts normally

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
```

### Creating New Migrations

```bash
# Enter the backend container
docker-compose exec backend sh

# Generate a new migration
alembic revision --autogenerate -m "Description of changes"

# Create empty migration file
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