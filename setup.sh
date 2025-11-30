#!/bin/bash

# Banwee E-commerce Platform Setup Script
# This script sets up the complete Docker environment

set -e

echo "🚀 Banwee E-commerce Platform Setup"
echo "===================================="
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

echo "✅ Docker and Docker Compose are installed"
echo ""

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from example..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your actual credentials before continuing!"
    echo "   Required: MAILGUN_API_KEY, MAILGUN_DOMAIN, SECRET_KEY, STRIPE keys"
    read -p "Press Enter after you've updated .env file..."
fi

# Create backend .env if it doesn't exist
if [ ! -f backend/.env ]; then
    echo "📝 Creating backend/.env file..."
    cp backend/.env.docker.example backend/.env
fi

# Create frontend .env if it doesn't exist
if [ ! -f frontend/.env ]; then
    echo "📝 Creating frontend/.env file..."
    cp frontend/.env.docker.example frontend/.env
fi

echo ""
echo "🐳 Starting Docker services..."
docker-compose up -d postgres redis

echo ""
echo "⏳ Waiting for PostgreSQL to be ready..."
sleep 10


echo ""
echo "🔧 Initializing PostgreSQL database..."
docker-compose run --rm backend python init_db.py

echo ""
echo "🚀 Starting all services..."
docker-compose up -d

echo ""
echo "⏳ Waiting for services to start..."
sleep 15

echo ""
echo "✅ Setup completed successfully!"
echo ""
echo "📋 Services Status:"
echo "==================="
docker-compose ps

echo ""
echo "🌐 Access Points:"
echo "================="
echo "Frontend:        http://localhost:5173"
echo "Backend API:     http://localhost:8000"
echo "API Docs:        http://localhost:8000/docs"
echo "PostgreSQL:      localhost:5432"
echo "Redis:           localhost:6379"
echo ""
echo "📝 Next Steps:"
echo "=============="
echo "1. Open http://localhost:5173 in your browser"
echo "2. Create an admin account"
echo "3. Start using Banwee!"
echo ""
echo "📊 View logs:"
echo "============="
echo "All services:    docker-compose logs -f"
echo "Backend only:    docker-compose logs -f backend"
echo "Frontend only:   docker-compose logs -f frontend"
echo "Celery worker:   docker-compose logs -f celery_worker"
echo ""
echo "🛑 Stop services:"
echo "================="
echo "docker-compose down"
echo ""
