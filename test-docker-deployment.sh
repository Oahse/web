#!/bin/bash

# Docker Deployment Test Script
# This script tests all aspects of the Docker deployment

set -e  # Exit on error

echo "🧪 Testing Docker Deployment for Banwee Platform"
echo "=================================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# Function to print test result
print_result() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓ PASSED${NC}: $2"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}✗ FAILED${NC}: $2"
        ((TESTS_FAILED++))
    fi
}

# Function to check if Docker is running
check_docker() {
    echo "1. Checking Docker installation..."
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}Docker is not installed${NC}"
        exit 1
    fi
    print_result 0 "Docker is installed"
    
    if ! docker info &> /dev/null; then
        echo -e "${RED}Docker daemon is not running${NC}"
        exit 1
    fi
    print_result 0 "Docker daemon is running"
    echo ""
}

# Function to check if docker-compose is available
check_docker_compose() {
    echo "2. Checking Docker Compose..."
    if docker compose version &> /dev/null; then
        print_result 0 "Docker Compose is available"
    elif command -v docker-compose &> /dev/null; then
        print_result 0 "Docker Compose (standalone) is available"
    else
        echo -e "${RED}Docker Compose is not available${NC}"
        exit 1
    fi
    echo ""
}

# Function to start containers
start_containers() {
    echo "3. Starting Docker containers..."
    echo -e "${YELLOW}This may take a few minutes on first run...${NC}"
    
    if docker compose up -d --build; then
        print_result 0 "Containers started successfully"
    else
        print_result 1 "Failed to start containers"
        return 1
    fi
    
    echo "Waiting for services to be ready..."
    sleep 10
    echo ""
}

# Function to check if all containers are running
check_containers_running() {
    echo "4. Checking if all containers are running..."
    
    EXPECTED_CONTAINERS=("banwee_postgres" "banwee_redis" "banwee_backend" "banwee_frontend" "banwee_celery_worker" "banwee_celery_beat")
    
    for container in "${EXPECTED_CONTAINERS[@]}"; do
        if docker ps --format '{{.Names}}' | grep -q "^${container}$"; then
            print_result 0 "Container ${container} is running"
        else
            print_result 1 "Container ${container} is not running"
        fi
    done
    echo ""
}

# Function to check health status
check_health_status() {
    echo "5. Checking container health status..."
    
    # Wait for health checks to complete
    echo "Waiting for health checks to complete (30 seconds)..."
    sleep 30
    
    # Check postgres health
    if docker inspect --format='{{.State.Health.Status}}' banwee_postgres 2>/dev/null | grep -q "healthy"; then
        print_result 0 "PostgreSQL is healthy"
    else
        print_result 1 "PostgreSQL health check failed"
    fi
    
    # Check redis health
    if docker inspect --format='{{.State.Health.Status}}' banwee_redis 2>/dev/null | grep -q "healthy"; then
        print_result 0 "Redis is healthy"
    else
        print_result 1 "Redis health check failed"
    fi
    
    # Check backend health
    if docker inspect --format='{{.State.Health.Status}}' banwee_backend 2>/dev/null | grep -q "healthy"; then
        print_result 0 "Backend is healthy"
    else
        print_result 1 "Backend health check failed"
    fi
    
    # Check frontend health
    if docker inspect --format='{{.State.Health.Status}}' banwee_frontend 2>/dev/null | grep -q "healthy"; then
        print_result 0 "Frontend is healthy"
    else
        print_result 1 "Frontend health check failed"
    fi
    echo ""
}

# Function to test database connection
test_database_connection() {
    echo "6. Testing database connection from backend..."
    
    if docker exec banwee_backend python -c "
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from core.config import settings

async def test_db():
    engine = create_async_engine(settings.SQLALCHEMY_DATABASE_URI)
    try:
        async with engine.connect() as conn:
            result = await conn.execute('SELECT 1')
            await result.fetchone()
        await engine.dispose()
        return True
    except Exception as e:
        print(f'Error: {e}')
        await engine.dispose()
        return False

if asyncio.run(test_db()):
    print('Database connection successful')
    exit(0)
else:
    exit(1)
" 2>&1 | grep -q "Database connection successful"; then
        print_result 0 "Backend can connect to database"
    else
        print_result 1 "Backend cannot connect to database"
    fi
    echo ""
}

# Function to test API endpoints
test_api_endpoints() {
    echo "7. Testing API endpoints..."
    
    # Test root endpoint
    if curl -f -s http://localhost:8000/ > /dev/null; then
        print_result 0 "Backend root endpoint is accessible"
    else
        print_result 1 "Backend root endpoint is not accessible"
    fi
    
    # Test health endpoint
    if curl -f -s http://localhost:8000/health/live > /dev/null; then
        print_result 0 "Backend health endpoint is accessible"
    else
        print_result 1 "Backend health endpoint is not accessible"
    fi
    
    # Test API docs
    if curl -f -s http://localhost:8000/docs > /dev/null; then
        print_result 0 "API documentation is accessible"
    else
        print_result 1 "API documentation is not accessible"
    fi
    echo ""
}

# Function to test frontend
test_frontend() {
    echo "8. Testing frontend..."
    
    if curl -f -s http://localhost:5173 > /dev/null; then
        print_result 0 "Frontend is accessible"
    else
        print_result 1 "Frontend is not accessible"
    fi
    echo ""
}

# Function to test inter-container communication
test_inter_container_communication() {
    echo "9. Testing inter-container communication..."
    
    # Test backend to postgres
    if docker exec banwee_backend ping -c 1 postgres > /dev/null 2>&1; then
        print_result 0 "Backend can reach PostgreSQL container"
    else
        print_result 1 "Backend cannot reach PostgreSQL container"
    fi
    
    # Test backend to redis
    if docker exec banwee_backend ping -c 1 redis > /dev/null 2>&1; then
        print_result 0 "Backend can reach Redis container"
    else
        print_result 1 "Backend cannot reach Redis container"
    fi
    echo ""
}

# Function to test data persistence
test_data_persistence() {
    echo "10. Testing data persistence..."
    
    # Check if volumes exist
    if docker volume ls | grep -q "banwee_postgres_data"; then
        print_result 0 "PostgreSQL data volume exists"
    else
        print_result 1 "PostgreSQL data volume does not exist"
    fi
    
    if docker volume ls | grep -q "banwee_redis_data"; then
        print_result 0 "Redis data volume exists"
    else
        print_result 1 "Redis data volume does not exist"
    fi
    echo ""
}

# Function to check logs for errors
check_logs() {
    echo "11. Checking container logs for errors..."
    
    # Check backend logs
    if docker logs banwee_backend 2>&1 | grep -i "error" | grep -v "ERROR_HANDLING" | grep -v "test_error" > /dev/null; then
        print_result 1 "Backend logs contain errors (check with: docker logs banwee_backend)"
    else
        print_result 0 "Backend logs look clean"
    fi
    
    # Check frontend logs
    if docker logs banwee_frontend 2>&1 | grep -i "error" | grep -v "ERROR_HANDLING" > /dev/null; then
        print_result 1 "Frontend logs contain errors (check with: docker logs banwee_frontend)"
    else
        print_result 0 "Frontend logs look clean"
    fi
    echo ""
}

# Function to print summary
print_summary() {
    echo "=================================================="
    echo "Test Summary"
    echo "=================================================="
    echo -e "${GREEN}Tests Passed: ${TESTS_PASSED}${NC}"
    echo -e "${RED}Tests Failed: ${TESTS_FAILED}${NC}"
    echo ""
    
    if [ $TESTS_FAILED -eq 0 ]; then
        echo -e "${GREEN}✓ All tests passed! Docker deployment is working correctly.${NC}"
        echo ""
        echo "Access the application:"
        echo "  Frontend: http://localhost:5173"
        echo "  Backend API: http://localhost:8000"
        echo "  API Docs: http://localhost:8000/docs"
        echo ""
        echo "Default credentials:"
        echo "  Admin: admin@banwee.com / adminpass"
        echo "  Supplier: supplier@banwee.com / supplierpass"
        return 0
    else
        echo -e "${RED}✗ Some tests failed. Please check the output above for details.${NC}"
        echo ""
        echo "Useful commands for debugging:"
        echo "  docker compose logs backend"
        echo "  docker compose logs frontend"
        echo "  docker compose ps"
        echo "  docker compose down && docker compose up -d"
        return 1
    fi
}

# Main execution
main() {
    check_docker
    check_docker_compose
    start_containers
    check_containers_running
    check_health_status
    test_database_connection
    test_api_endpoints
    test_frontend
    test_inter_container_communication
    test_data_persistence
    check_logs
    print_summary
}

# Run main function
main
exit $?
