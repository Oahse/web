#!/bin/bash

###############################################################################
# Banwee Docker Launch Script
# This script starts all Docker containers for the Banwee application
###############################################################################

set -e  # Exit on error

echo "🚀 Starting Banwee Application in Docker..."
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found!"
    echo "📝 Creating .env from .env.example..."
    cp .env.example .env
    echo "✅ .env file created. Please update it with your actual credentials."
    echo ""
fi

# Check if backend/.env exists
if [ ! -f backend/.env ]; then
    echo "⚠️  backend/.env file not found!"
    echo "📝 Creating backend/.env from backend/.env.example..."
    cp backend/.env.example backend/.env
    echo "✅ backend/.env file created."
    echo ""
fi

# Check if frontend/.env exists
if [ ! -f frontend/.env ]; then
    echo "⚠️  frontend/.env file not found!"
    echo "📝 Creating frontend/.env from frontend/.env.example..."
    cp frontend/.env.example frontend/.env
    echo "✅ frontend/.env file created."
    echo ""
fi

echo "🐳 Building and starting Docker containers..."
docker-compose up --build -d

echo ""
echo "⏳ Waiting for services to be healthy..."
sleep 10

# Check service health
echo ""
echo "🔍 Checking service status..."
docker-compose ps

echo ""
echo "✅ Banwee application is starting!"
echo ""
echo "📍 Service URLs:"
echo "   Frontend:  http://localhost:5173"
echo "   Backend:   http://localhost:8000"
echo "   API Docs:  http://localhost:8000/docs"
echo "   PostgreSQL: localhost:5432"
echo "   Redis:     localhost:6379"
echo ""
echo "📊 View logs with: docker-compose logs -f [service_name]"
echo "   Services: backend, frontend, postgres, redis, celery_worker, celery_beat"
echo ""
echo "🛑 Stop all services with: docker-compose down"
echo ""
echo "⚠️  IMPORTANT: Run './seed-database.sh' to populate the database with sample data"
echo ""
