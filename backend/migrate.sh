#!/bin/sh
# Migration script for Docker container startup

echo "🔄 Running database migrations..."

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
            async with engine.connect() as conn:
                await conn.execute('SELECT 1')
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

# Run Alembic migrations
echo "🔄 Applying database migrations..."
alembic upgrade head

if [ $? -eq 0 ]; then
    echo "✅ Migrations completed successfully"
else
    echo "❌ Migration failed"
    exit 1
fi
