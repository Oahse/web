# Database Migration Guide

This guide covers all database migration operations for the application, including initial setup, schema changes, and data migrations.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Initial Database Setup](#initial-database-setup)
- [Running Migrations](#running-migrations)
- [Creating New Migrations](#creating-new-migrations)
- [Migration Commands](#migration-commands)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Tools
- Python 3.11+
- PostgreSQL 14+
- Alembic (included in requirements.txt)
- SQLAlchemy 2.0+

### Environment Setup
Ensure your environment variables are configured:

```bash
# Copy environment template
cp backend/.env.example backend/.env

# Edit with your database credentials
POSTGRES_DB_URL=postgresql://username:password@localhost:5432/dbname
```

## Initial Database Setup

### 1. Create Database
```bash
# Connect to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE your_app_name;
CREATE USER your_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE your_app_name TO your_user;
\q
```

### 2. Initialize Alembic (First Time Only)
```bash
cd backend

# Initialize Alembic migrations
alembic init alembic

# This creates the alembic/ directory with configuration
```

### 3. Configure Alembic
Edit `backend/alembic.ini`:
```ini
# Set your database URL
sqlalchemy.url = postgresql://username:password@localhost:5432/dbname
```

Edit `backend/alembic/env.py`:
```python
# Import your models
from models import *
target_metadata = Base.metadata
```

## Running Migrations

### Apply All Pending Migrations
```bash
cd backend

# Run all pending migrations
alembic upgrade head

# Or use the migration script
./migrate.sh
```

### Apply Specific Migration
```bash
# Upgrade to specific revision
alembic upgrade <revision_id>

# Downgrade to specific revision
alembic downgrade <revision_id>

# Downgrade one step
alembic downgrade -1
```

### Check Migration Status
```bash
# Show current revision
alembic current

# Show migration history
alembic history

# Show pending migrations
alembic show head
```

## Creating New Migrations

### Auto-generate Migration from Model Changes
```bash
cd backend

# Generate migration automatically
alembic revision --autogenerate -m "Description of changes"

# Example: Add new table
alembic revision --autogenerate -m "Add user_preferences table"

# Example: Modify existing table
alembic revision --autogenerate -m "Add email_verified column to users"
```

### Create Empty Migration for Data Changes
```bash
# Create empty migration for custom SQL or data operations
alembic revision -m "Migrate user data to new format"
```

### Example Migration File
```python
"""Add user_preferences table

Revision ID: abc123def456
Revises: previous_revision
Create Date: 2024-01-15 10:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'abc123def456'
down_revision = 'previous_revision'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Create new table
    op.create_table('user_preferences',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email_notifications', sa.Boolean(), nullable=True),
        sa.Column('sms_notifications', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Add index
    op.create_index('ix_user_preferences_user_id', 'user_preferences', ['user_id'])

def downgrade() -> None:
    # Drop index
    op.drop_index('ix_user_preferences_user_id', table_name='user_preferences')
    
    # Drop table
    op.drop_table('user_preferences')
```

## Migration Commands

### Using Alembic Directly
```bash
# Basic commands
alembic upgrade head              # Apply all migrations
alembic downgrade base            # Rollback all migrations
alembic current                   # Show current revision
alembic history                   # Show migration history
alembic show head                 # Show latest migration

# Advanced commands
alembic upgrade +2                # Upgrade 2 steps forward
alembic downgrade -1              # Downgrade 1 step back
alembic upgrade abc123:def456     # Upgrade from abc123 to def456
alembic stamp head                # Mark database as up-to-date without running migrations
```

### Using Migration Scripts
```bash
# Run migration script
./backend/migrate.sh

# Run with specific environment
ENV=production ./backend/migrate.sh

# Run migration service
python backend/run_migration.py
```

### Using Python Migration Service
```python
from services.migration_service import MigrationService
import asyncio

async def run_migrations():
    migration_service = MigrationService()
    
    # Run all pending migrations
    result = await migration_service.run_migrations()
    print(f"Applied {result['applied_count']} migrations")
    
    # Check migration status
    status = await migration_service.get_migration_status()
    print(f"Current revision: {status['current_revision']}")

# Run migrations
asyncio.run(run_migrations())
```

## Data Migrations

### Example: Migrate User Data
```python
"""Migrate user roles to new format

Revision ID: def456ghi789
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column

def upgrade() -> None:
    # Define table structure for data migration
    users_table = table('users',
        column('id', sa.String),
        column('role', sa.String),
        column('permissions', sa.JSON)
    )
    
    # Update user roles
    connection = op.get_bind()
    
    # Migrate admin users
    connection.execute(
        users_table.update()
        .where(users_table.c.role == 'admin')
        .values(permissions={'admin': True, 'manage_users': True})
    )
    
    # Migrate regular users
    connection.execute(
        users_table.update()
        .where(users_table.c.role == 'user')
        .values(permissions={'admin': False, 'manage_users': False})
    )

def downgrade() -> None:
    # Reverse the migration
    users_table = table('users',
        column('id', sa.String),
        column('role', sa.String),
        column('permissions', sa.JSON)
    )
    
    connection = op.get_bind()
    
    # Restore original roles based on permissions
    connection.execute(
        users_table.update()
        .where(users_table.c.permissions['admin'].astext == 'true')
        .values(role='admin')
    )
    
    connection.execute(
        users_table.update()
        .where(users_table.c.permissions['admin'].astext == 'false')
        .values(role='user')
    )
```

## Docker Migrations

### Running Migrations in Docker
```bash
# Run migrations in Docker container
docker-compose exec backend alembic upgrade head

# Run migration script in Docker
docker-compose exec backend ./migrate.sh

# Run one-time migration container
docker-compose run --rm backend alembic upgrade head
```

### Docker Compose with Auto-Migration
```yaml
# In docker-compose.yml
services:
  backend:
    build: ./backend
    depends_on:
      postgres:
        condition: service_healthy
    command: >
      sh -c "
        alembic upgrade head &&
        python main.py
      "
```

## Troubleshooting

### Common Issues

#### 1. Migration Conflicts
```bash
# If you have conflicting migrations
alembic merge -m "Merge conflicting migrations" head1 head2

# Or resolve manually by editing migration files
```

#### 2. Database Out of Sync
```bash
# Mark database as current without running migrations
alembic stamp head

# Or reset to specific revision
alembic stamp <revision_id>
```

#### 3. Failed Migration
```bash
# Check what went wrong
alembic current
alembic history

# Manually fix the issue and continue
alembic upgrade head

# Or rollback and try again
alembic downgrade -1
# Fix the migration file
alembic upgrade head
```

#### 4. Missing Dependencies
```bash
# Install required packages
pip install -r requirements.txt

# Or install specific packages
pip install alembic sqlalchemy psycopg2-binary
```

### Migration Best Practices

1. **Always backup before migrations**
   ```bash
   pg_dump -U username dbname > backup_$(date +%Y%m%d_%H%M%S).sql
   ```

2. **Test migrations on development first**
   ```bash
   # Test on dev database
   alembic upgrade head
   
   # Test rollback
   alembic downgrade -1
   alembic upgrade head
   ```

3. **Review auto-generated migrations**
   - Check that all changes are captured
   - Verify foreign key constraints
   - Add custom data migrations if needed

4. **Use descriptive migration messages**
   ```bash
   # Good
   alembic revision --autogenerate -m "Add user_preferences table with notification settings"
   
   # Bad
   alembic revision --autogenerate -m "Update models"
   ```

5. **Handle data carefully**
   - Use transactions for data migrations
   - Test with production-like data volumes
   - Consider migration performance impact

## Environment-Specific Migrations

### Development
```bash
# Quick reset for development
alembic downgrade base
alembic upgrade head

# Or drop and recreate
dropdb devdb && createdb devdb
alembic upgrade head
```

### Staging
```bash
# Backup first
pg_dump staging_db > staging_backup.sql

# Run migrations
alembic upgrade head

# Verify
alembic current
```

### Production
```bash
# 1. Backup database
pg_dump production_db > prod_backup_$(date +%Y%m%d_%H%M%S).sql

# 2. Test migration on copy
createdb prod_test
pg_restore -d prod_test prod_backup.sql
alembic upgrade head

# 3. Run on production (during maintenance window)
alembic upgrade head

# 4. Verify
alembic current
```

## Monitoring Migrations

### Check Migration Status
```python
from services.migration_service import MigrationService

async def check_status():
    service = MigrationService()
    status = await service.get_migration_status()
    
    print(f"Current revision: {status['current_revision']}")
    print(f"Pending migrations: {len(status['pending_migrations'])}")
    
    if status['pending_migrations']:
        print("Pending migrations:")
        for migration in status['pending_migrations']:
            print(f"  - {migration['revision']}: {migration['description']}")
```

### Automated Migration Checks
```bash
#!/bin/bash
# check_migrations.sh

# Check if migrations are needed
CURRENT=$(alembic current)
HEAD=$(alembic show head)

if [ "$CURRENT" != "$HEAD" ]; then
    echo "⚠️  Database migrations are pending!"
    echo "Current: $CURRENT"
    echo "Latest: $HEAD"
    exit 1
else
    echo "✅ Database is up to date"
    exit 0
fi
```

This guide covers all aspects of database migrations. For specific issues or advanced scenarios, refer to the [Alembic documentation](https://alembic.sqlalchemy.org/) or check the application logs.
---

# Specific Migrations

## Enhanced Subscription Payment Models Migration

# Enhanced Subscription Payment Models Migration

This document provides instructions for safely migrating the database to support the enhanced subscription payment system with admin-configurable pricing, comprehensive cost tracking, Stripe integration, and loyalty features.

## Overview

This migration adds the following new database models and enhancements:

### New Tables Created
- `pricing_configs` - Admin-configurable pricing settings
- `subscription_cost_history` - Historical cost change tracking  
- `payment_intents` - Enhanced Stripe payment intent tracking
- `subscription_analytics` - Daily subscription metrics
- `payment_analytics` - Daily payment performance metrics
- `loyalty_accounts` - Customer loyalty accounts with points and tiers
- `points_transactions` - Individual loyalty points transactions

### Enhanced Existing Tables
- `subscriptions` - Added 14 new fields for variant tracking, cost breakdown, delivery management, and loyalty integration

## Safety Features

This migration includes comprehensive safety features as required by the specification:

- **Automatic Backup Creation** - Database backup created before any changes
- **Data Integrity Validation** - Foreign key constraints and data consistency checks
- **Automatic Rollback** - Restore from backup if migration or validation fails
- **Detailed Logging** - Complete audit trail of all migration steps

## Prerequisites

1. **Database Access** - Ensure you have admin access to the PostgreSQL database
2. **Backup Space** - Ensure sufficient disk space for database backup
3. **Dependencies** - Install required Python packages:
   ```bash
   pip install asyncpg psycopg2-binary alembic sqlalchemy
   ```
4. **PostgreSQL Tools** - Ensure `pg_dump` and `pg_restore` are available in PATH

## Migration Process

### Step 1: Prepare Environment

```bash
# Navigate to backend directory
cd backend

# Activate virtual environment
source .venv/bin/activate

# Verify database connection
python -c "import asyncpg; print('Dependencies OK')"
```

### Step 2: Create Pre-Migration Backup (Recommended)

```bash
# Create manual backup before starting
python migration_utils.py --database-url "postgresql://user:pass@host/db" backup --name "pre_migration_manual"
```

### Step 3: Run Migration with Safety Features

```bash
# Run migration with automatic backup and rollback
python run_migration.py --database-url "postgresql://user:pass@host/db"
```

#### Alternative: Dry Run (Backup Only)

```bash
# Create backup without running migration
python run_migration.py --database-url "postgresql://user:pass@host/db" --dry-run
```

### Step 4: Verify Migration Success

```bash
# Validate data integrity
python migration_utils.py --database-url "postgresql://user:pass@host/db" validate

# List available backups
python migration_utils.py --database-url "postgresql://user:pass@host/db" list
```

## Rollback Procedure

If you need to rollback the migration:

### Option 1: Automatic Rollback (if migration failed)
The migration script automatically restores from backup if the migration fails or validation fails.

### Option 2: Manual Rollback

```bash
# List available backups
python migration_utils.py --database-url "postgresql://user:pass@host/db" list

# Restore from specific backup
python migration_utils.py --database-url "postgresql://user:pass@host/db" restore /path/to/backup.sql
```

### Option 3: Alembic Downgrade

```bash
# Downgrade using alembic (removes new tables and columns)
source .venv/bin/activate
python -m alembic downgrade d6d022bcff3b
```

## Troubleshooting

### Common Issues

1. **Connection Failed**
   - Verify database URL format: `postgresql://user:password@host:port/database`
   - Ensure database server is running and accessible
   - Check firewall and network connectivity

2. **Permission Denied**
   - Ensure database user has CREATE, ALTER, and DROP privileges
   - Verify pg_dump and pg_restore permissions

3. **Backup Failed**
   - Check disk space in backup directory
   - Verify pg_dump is installed and in PATH
   - Ensure database user has SELECT privileges on all tables

4. **Migration Failed**
   - Check migration logs in `migration.log`
   - Verify all model imports are working
   - Ensure no conflicting table names exist

### Recovery Steps

If migration fails and automatic rollback doesn't work:

1. **Stop Application** - Stop all application processes using the database
2. **Manual Restore** - Use pg_restore to restore from backup
3. **Verify Restoration** - Run validation checks
4. **Investigate Issue** - Check logs and fix underlying problem
5. **Retry Migration** - Re-run migration after fixing issues

## Validation Checks

The migration performs these validation checks:

- **Foreign Key Constraints** - Ensures all foreign keys are valid
- **Data Constraints** - Verifies check constraints and unique constraints  
- **Index Integrity** - Checks index consistency
- **Table Statistics** - Validates table row counts and statistics

## Post-Migration Steps

After successful migration:

1. **Update Application Code** - Deploy updated models and services
2. **Initialize Default Data** - Create default pricing configuration
3. **Test Core Functionality** - Verify subscription and payment flows
4. **Monitor Performance** - Watch for any performance impacts
5. **Clean Old Backups** - Archive or remove old backup files as needed

## Migration Metadata

- **Migration ID**: 003
- **Previous Migration**: d6d022bcff3b (merge search and inventory heads)
- **Tables Added**: 7 new tables
- **Columns Added**: 14 new columns to subscriptions table
- **Estimated Downtime**: 2-5 minutes (depending on data size)

## Support

For issues with this migration:

1. Check the `migration.log` file for detailed error messages
2. Verify all prerequisites are met
3. Ensure database backup is available before attempting fixes
4. Contact the development team with log files and error details

## Files Created/Modified

- `backend/models/pricing_config.py` - New pricing configuration models
- `backend/models/payment_intent.py` - Enhanced payment intent model
- `backend/models/analytics.py` - Analytics models for reporting
- `backend/models/loyalty.py` - Customer loyalty system models
- `backend/models/subscription.py` - Enhanced subscription model
- `backend/models/user.py` - Added loyalty and payment intent relationships
- `backend/alembic/versions/003_add_enhanced_subscription_payment_models.py` - Migration script
- `backend/migration_utils.py` - Migration utilities with backup/rollback
- `backend/run_migration.py` - Safe migration runner script