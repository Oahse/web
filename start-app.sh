#!/bin/bash

# Banwee Application Startup Script
# This script initializes the database, seeds data, and starts both backend and frontend

set -e  # Exit on any error

echo "🚀 Starting Banwee Application..."
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Check if .env file exists
if [ ! -f ".env" ]; then
    print_error ".env file not found!"
    print_error "Please create a .env file with your Neon PostgreSQL and Upstash Redis URLs"
    exit 1
fi

# Load environment variables
source .env

# Verify required environment variables
print_step "Verifying environment configuration..."

if [ -z "$POSTGRES_DB_URL" ]; then
    print_error "POSTGRES_DB_URL is not set in .env file"
    exit 1
fi

if [ -z "$REDIS_URL" ]; then
    print_error "REDIS_URL is not set in .env file"
    exit 1
fi

print_status "Environment variables loaded successfully"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    print_error "Node.js is not installed. Please install Node.js 16 or higher."
    exit 1
fi

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    print_error "npm is not installed. Please install npm."
    exit 1
fi

print_status "All required tools are installed"

# Setup Python virtual environment for backend
print_step "Setting up Python virtual environment..."
cd backend

if [ ! -d ".venv" ]; then
    print_status "Creating Python virtual environment..."
    python3 -m venv .venv
fi

print_status "Activating virtual environment..."
source .venv/bin/activate

# Install Python dependencies
print_step "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Initialize and seed database
print_step "Initializing database..."
print_status "Creating tables and seeding data..."
# python init_db.py --seed --products 50 --users 25
python init_db.py --users 25

if [ $? -eq 0 ]; then
    print_status "Database initialized successfully!"
else
    print_error "Database initialization failed!"
    exit 1
fi

# Start backend server in background
print_step "Starting backend server..."
print_status "Backend will be available at http://localhost:8000"
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 3

# Check if backend started successfully
if ps -p $BACKEND_PID > /dev/null; then
    print_status "Backend server started successfully (PID: $BACKEND_PID)"
else
    print_error "Backend server failed to start"
    exit 1
fi

# Go back to root directory
cd ..

# Setup frontend
print_step "Setting up frontend..."
cd frontend

# Install Node.js dependencies
print_step "Installing Node.js dependencies..."
npm install
npm install axios

# Start frontend server in background
print_step "Starting frontend server..."
print_status "Frontend will be available at http://localhost:5173"
npm run dev &
FRONTEND_PID=$!

# Wait a moment for frontend to start
sleep 3

# Check if frontend started successfully
if ps -p $FRONTEND_PID > /dev/null; then
    print_status "Frontend server started successfully (PID: $FRONTEND_PID)"
else
    print_error "Frontend server failed to start"
    kill $BACKEND_PID 2>/dev/null || true
    exit 1
fi

# Go back to root directory
cd ..

echo ""
echo "🎉 Banwee Application Started Successfully!"
echo "=========================================="
echo ""
echo "📱 Frontend: http://localhost:5173"
echo "🔧 Backend API: http://localhost:8000"
echo "📚 API Documentation: http://localhost:8000/docs"
echo ""
echo "🔐 Default Login Credentials:"
echo "   Admin: admin@banwee.com / admin123"
echo "   Customer: customer1@example.com / customer1123"
echo ""
echo "🛑 To stop the application, press Ctrl+C"
echo ""

# Create a function to cleanup on exit
cleanup() {
    print_warning "Shutting down application..."
    kill $BACKEND_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    print_status "Application stopped"
    exit 0
}

# Set trap to cleanup on script exit
trap cleanup SIGINT SIGTERM

# Wait for user to stop the application
while true; do
    sleep 1
    # Check if processes are still running
    if ! ps -p $BACKEND_PID > /dev/null; then
        print_error "Backend server stopped unexpectedly"
        kill $FRONTEND_PID 2>/dev/null || true
        exit 1
    fi
    if ! ps -p $FRONTEND_PID > /dev/null; then
        print_error "Frontend server stopped unexpectedly"
        kill $BACKEND_PID 2>/dev/null || true
        exit 1
    fi
done