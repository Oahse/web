#!/bin/sh
# Migration script for Docker container startup with Alembic auto-initialization

echo "🔄 Running database migrations..."

# Initialize Alembic if not already configured
if [ ! -f "alembic.ini" ]; then
    echo "📝 Alembic not configured, initializing..."
    python -m alembic init alembic
    
    # Update alembic.ini to use environment variables
    sed -i 's|sqlalchemy.url = driver://user:pass@localhost/dbname|# sqlalchemy.url = driver://user:pass@localhost/dbname\n# Database URL will be set from environment variables in env.py|' alembic.ini
    
    # Create proper env.py for async operations
    cat > alembic/env.py << 'EOF'
import asyncio
import os
import sys
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# Add the parent directory to sys.path to import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import your models and database configuration
from core.database import Base, GUID
from core.config import settings

# Import all models to ensure they're registered with Base.metadata
from models import *

# this is the Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set the database URL from environment variables
config.set_main_option("sqlalchemy.url", settings.SQLALCHEMY_DATABASE_URI)

# add your model's MetaData object here for 'autogenerate' support
target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,
    )

    with context.begin_transaction():
        context.run_migrations()

def do_run_migrations(connection: Connection) -> None:
    """Run migrations with the given connection."""
    context.configure(
        connection=connection, 
        target_metadata=target_metadata,
        render_as_batch=True,
    )

    with context.begin_transaction():
        context.run_migrations()

async def run_async_migrations() -> None:
    """Run migrations in async mode."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()

def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    asyncio.run(run_async_migrations())

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
EOF

    # Update the script template to properly import custom types
    cat > alembic/script.py.mako << 'EOF'
"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from core.database import GUID
${imports if imports else ""}

# revision identifiers, used by Alembic.
revision: str = ${repr(up_revision)}
down_revision: Union[str, None] = ${repr(down_revision)}
branch_labels: Union[str, Sequence[str], None] = ${repr(branch_labels)}
depends_on: Union[str, Sequence[str], None] = ${repr(depends_on)}


def upgrade() -> None:
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    ${downgrades if downgrades else "pass"}
EOF
    
    echo "✅ Alembic initialized successfully"
fi

# Wait for database to be ready
echo "⏳ Waiting for database to be ready..."
python -c "
import asyncio
import sys
from sqlalchemy.ext.asyncio import create_async_engine
from core.config import settings

async def wait_for_db():
    engine = create_async_engine(settings.SQLALCHEMY_DATABASE_URI)
    max_retries = 30
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            from sqlalchemy import text
            async with engine.connect() as conn:
                await conn.execute(text('SELECT 1'))
            print('✅ Database is ready!')
            await engine.dispose()
            return True
        except Exception as e:
            retry_count += 1
            print(f'⏳ Waiting for database... ({retry_count}/{max_retries})')
            await asyncio.sleep(2)
    
    print('❌ Database connection failed after maximum retries')
    await engine.dispose()
    return False

if not asyncio.run(wait_for_db()):
    sys.exit(1)
"

if [ $? -ne 0 ]; then
    echo "❌ Database connection failed"
    exit 1
fi

# Remove any existing problematic migration files
if [ -d "alembic/versions" ] && [ "$(ls -A alembic/versions 2>/dev/null)" ]; then
    echo "🧹 Cleaning up existing migration files..."
    rm -f alembic/versions/*.py
fi

# Create initial migration if no migrations exist
if [ ! "$(ls -A alembic/versions 2>/dev/null)" ]; then
    echo "📝 No migrations found, creating initial migration..."
    python -m alembic revision --autogenerate -m "Initial migration"
    if [ $? -eq 0 ]; then
        echo "✅ Initial migration created successfully"
    else
        echo "⚠️  Could not create initial migration, creating empty one..."
        python -m alembic revision -m "Initial empty migration"
    fi
fi

# Run Alembic migrations
echo "🔄 Applying database migrations..."
python -m alembic upgrade head

if [ $? -eq 0 ]; then
    echo "✅ Migrations completed successfully"
else
    echo "❌ Migration failed"
    exit 1
fi
