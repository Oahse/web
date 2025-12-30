#!/bin/sh
# Script to reset and regenerate Alembic migrations

echo "🧹 Resetting Alembic migrations..."

# Remove existing alembic configuration
if [ -d "alembic" ]; then
    echo "📁 Removing existing alembic directory..."
    rm -rf alembic
fi

if [ -f "alembic.ini" ]; then
    echo "📄 Removing existing alembic.ini..."
    rm -f alembic.ini
fi

echo "✅ Cleanup completed"
echo "🔄 Run ./migrate.sh to reinitialize Alembic"