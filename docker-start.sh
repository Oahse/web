#!/bin/bash

###############################################################################
# Banwee Docker Launch Script
# This script starts all Docker containers for the Banwee application
###############################################################################

set -e  # Exit on error

# Default to 'dev' if no environment is specified
ENV=${1:-dev}

echo "🚀 Starting Banwee Application in Docker ($ENV mode)..."
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found!"
    echo "📝 Creating .env from .env.example..."
    cp .env.example .env
    echo "✅ .env file created. Please update it with your actual credentials."
    echo ""
fi

if [ "$ENV" = "prod" ]; then
    # Production environment
    if [ ! -f docker-compose.prod.yml ]; then
        echo "❌ Error: docker-compose.prod.yml not found for production environment."
        exit 1
    fi
    echo "🐳 Building and starting production containers..."
    docker-compose -f docker-compose.prod.yml up --build -d
else
    # Development environment
    echo "🐳 Building and starting development containers..."
    docker-compose up --build -d
fi

echo ""
echo "⏳ Waiting for services to be healthy..."
sleep 20 # Increased sleep time to allow services to start

# Check service health
echo ""
echo "🔍 Checking service status..."
if [ "$ENV" = "prod" ]; then
    docker-compose -f docker-compose.prod.yml ps
else
    docker-compose ps
fi

echo ""
echo "⚙️  Database migrations are handled automatically during backend container startup."
echo ""

if [ "$ENV" = "dev" ]; then
    echo "🌱 Seeding database with sample data for development..."
    ./seed-database.sh
    echo "✅ Database seeded successfully."
    echo ""
fi

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
echo "   Services: backend, frontend, postgres, redis, kafka"
echo ""
echo "🛑 Stop all services with: docker-compose down"
echo ""

if [ "$ENV" = "dev" ]; then
    echo "🔐 Default Admin Account:"
    echo "   Email:    admin@banwee.com"
    echo "   Password: adminpass"
    echo ""
fi