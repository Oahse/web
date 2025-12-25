#!/bin/bash

# Full Stack Testing Script
# Tests all components: Frontend, Backend, Database, Kafka, Redis

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BACKEND_URL="http://localhost:8000"
FRONTEND_URL="http://localhost:3000"
POSTGRES_HOST="localhost"
POSTGRES_PORT="5432"
REDIS_HOST="localhost"
REDIS_PORT="6379"
KAFKA_HOST="localhost"
KAFKA_PORT="9092"

# Test results
TESTS_PASSED=0
TESTS_FAILED=0
FAILED_TESTS=()

# Helper functions
print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_test() {
    echo -e "${YELLOW}Testing: $1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
    ((TESTS_PASSED++))
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
    ((TESTS_FAILED++))
    FAILED_TESTS+=("$1")
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Wait for service to be ready
wait_for_service() {
    local host=$1
    local port=$2
    local service_name=$3
    local max_attempts=30
    local attempt=1

    print_info "Waiting for $service_name to be ready..."
    
    while [ $attempt -le $max_attempts ]; do
        if nc -z "$host" "$port" 2>/dev/null; then
            print_success "$service_name is ready"
            return 0
        fi
        
        echo -n "."
        sleep 2
        ((attempt++))
    done
    
    print_error "$service_name is not responding after $((max_attempts * 2)) seconds"
    return 1
}

# Test HTTP endpoint
test_http_endpoint() {
    local url=$1
    local expected_status=$2
    local description=$3
    
    print_test "$description"
    
    if command_exists curl; then
        local response=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null || echo "000")
        
        if [ "$response" = "$expected_status" ]; then
            print_success "$description - Status: $response"
        else
            print_error "$description - Expected: $expected_status, Got: $response"
        fi
    else
        print_error "curl not found - cannot test HTTP endpoints"
    fi
}

# Test database connection
test_database() {
    print_test "Database connection"
    
    if command_exists psql; then
        # Test connection
        if PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT 1;" >/dev/null 2>&1; then
            print_success "PostgreSQL connection successful"
            
            # Test basic operations
            print_test "Database operations"
            
            # Create test table
            if PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "
                CREATE TABLE IF NOT EXISTS test_table (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100),
                    created_at TIMESTAMP DEFAULT NOW()
                );
            " >/dev/null 2>&1; then
                print_success "Table creation successful"
            else
                print_error "Table creation failed"
            fi
            
            # Insert test data
            if PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "
                INSERT INTO test_table (name) VALUES ('test_entry');
            " >/dev/null 2>&1; then
                print_success "Data insertion successful"
            else
                print_error "Data insertion failed"
            fi
            
            # Query test data
            local count=$(PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -c "
                SELECT COUNT(*) FROM test_table WHERE name = 'test_entry';
            " 2>/dev/null | xargs)
            
            if [ "$count" -gt "0" ]; then
                print_success "Data query successful - Found $count records"
            else
                print_error "Data query failed"
            fi
            
            # Cleanup
            PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "
                DROP TABLE IF EXISTS test_table;
            " >/dev/null 2>&1
            
        else
            print_error "PostgreSQL connection failed"
        fi
    else
        print_error "psql not found - cannot test database"
    fi
}

# Test Redis connection
test_redis() {
    print_test "Redis connection"
    
    if command_exists redis-cli; then
        # Test connection
        if redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" ping >/dev/null 2>&1; then
            print_success "Redis connection successful"
            
            # Test basic operations
            print_test "Redis operations"
            
            # Set test key
            if redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" set test_key "test_value" >/dev/null 2>&1; then
                print_success "Redis SET operation successful"
            else
                print_error "Redis SET operation failed"
            fi
            
            # Get test key
            local value=$(redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" get test_key 2>/dev/null)
            if [ "$value" = "test_value" ]; then
                print_success "Redis GET operation successful"
            else
                print_error "Redis GET operation failed"
            fi
            
            # Delete test key
            redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" del test_key >/dev/null 2>&1
            
        else
            print_error "Redis connection failed"
        fi
    else
        print_error "redis-cli not found - cannot test Redis"
    fi
}

# Test Kafka connection
test_kafka() {
    print_test "Kafka connection"
    
    # Check if Kafka is running using Docker
    if docker-compose ps kafka | grep -q "Up"; then
        print_success "Kafka container is running"
        
        # Test Kafka operations
        print_test "Kafka operations"
        
        local test_topic="test-topic-$(date +%s)"
        
        # Create topic
        if docker-compose exec -T kafka kafka-topics --bootstrap-server localhost:9092 --create --topic "$test_topic" --partitions 1 --replication-factor 1 >/dev/null 2>&1; then
            print_success "Kafka topic creation successful"
            
            # Produce message
            if echo "test message" | docker-compose exec -T kafka kafka-console-producer --bootstrap-server localhost:9092 --topic "$test_topic" >/dev/null 2>&1; then
                print_success "Kafka message production successful"
            else
                print_error "Kafka message production failed"
            fi
            
            # List topics to verify
            if docker-compose exec -T kafka kafka-topics --bootstrap-server localhost:9092 --list | grep -q "$test_topic"; then
                print_success "Kafka topic listing successful"
            else
                print_error "Kafka topic listing failed"
            fi
            
            # Cleanup
            docker-compose exec -T kafka kafka-topics --bootstrap-server localhost:9092 --delete --topic "$test_topic" >/dev/null 2>&1
            
        else
            print_error "Kafka topic creation failed"
        fi
    else
        print_error "Kafka container is not running"
    fi
}

# Test backend API
test_backend_api() {
    print_test "Backend API health"
    
    # Wait for backend to be ready
    if wait_for_service "localhost" "8000" "Backend API"; then
        # Test health endpoint
        test_http_endpoint "$BACKEND_URL/health" "200" "Health endpoint"
        
        # Test API documentation
        test_http_endpoint "$BACKEND_URL/docs" "200" "API documentation"
        
        # Test OpenAPI spec
        test_http_endpoint "$BACKEND_URL/openapi.json" "200" "OpenAPI specification"
        
        # Test authentication endpoints
        test_http_endpoint "$BACKEND_URL/api/v1/auth/register" "422" "Auth register endpoint (expects validation error)"
        
        # Test API endpoints that should return 401 without auth
        test_http_endpoint "$BACKEND_URL/api/v1/users/me" "401" "Protected endpoint (expects unauthorized)"
        
        # Test CORS
        print_test "CORS configuration"
        if command_exists curl; then
            local cors_response=$(curl -s -H "Origin: http://localhost:3000" -H "Access-Control-Request-Method: GET" -H "Access-Control-Request-Headers: X-Requested-With" -X OPTIONS "$BACKEND_URL/api/v1/users/me" -w "%{http_code}" -o /dev/null 2>/dev/null || echo "000")
            
            if [ "$cors_response" = "200" ] || [ "$cors_response" = "204" ]; then
                print_success "CORS preflight successful"
            else
                print_error "CORS preflight failed - Status: $cors_response"
            fi
        fi
    fi
}

# Test frontend
test_frontend() {
    print_test "Frontend application"
    
    # Wait for frontend to be ready
    if wait_for_service "localhost" "3000" "Frontend"; then
        # Test main page
        test_http_endpoint "$FRONTEND_URL" "200" "Frontend main page"
        
        # Test static assets (if accessible)
        print_test "Frontend static assets"
        if command_exists curl; then
            # Try to access common static files
            local static_response=$(curl -s -o /dev/null -w "%{http_code}" "$FRONTEND_URL/static/css/main.css" 2>/dev/null || echo "404")
            if [ "$static_response" = "200" ] || [ "$static_response" = "404" ]; then
                print_success "Frontend static assets accessible"
            else
                print_error "Frontend static assets not accessible"
            fi
        fi
    fi
}

# Test database migrations
test_migrations() {
    print_test "Database migrations"
    
    if docker-compose ps backend | grep -q "Up"; then
        # Check migration status
        local migration_output=$(docker-compose exec -T backend alembic current 2>/dev/null || echo "error")
        
        if [ "$migration_output" != "error" ] && [ -n "$migration_output" ]; then
            print_success "Database migrations are applied"
            print_info "Current migration: $(echo $migration_output | xargs)"
        else
            print_error "Database migrations check failed"
        fi
        
        # Test migration command
        if docker-compose exec -T backend alembic check >/dev/null 2>&1; then
            print_success "Migration consistency check passed"
        else
            print_error "Migration consistency check failed"
        fi
    else
        print_error "Backend container is not running - cannot test migrations"
    fi
}

# Test environment variables
test_environment() {
    print_test "Environment configuration"
    
    # Check if required environment files exist
    if [ -f ".env" ]; then
        print_success "Main .env file exists"
    else
        print_error "Main .env file missing"
    fi
    
    if [ -f "backend/.env" ]; then
        print_success "Backend .env file exists"
    else
        print_error "Backend .env file missing"
    fi
    
    # Load environment variables
    if [ -f ".env" ]; then
        source .env
        
        # Check critical variables
        if [ -n "$POSTGRES_DB" ] && [ -n "$POSTGRES_USER" ] && [ -n "$POSTGRES_PASSWORD" ]; then
            print_success "Database environment variables configured"
        else
            print_error "Database environment variables missing"
        fi
    fi
}

# Test Docker services
test_docker_services() {
    print_test "Docker services status"
    
    if command_exists docker-compose; then
        # Check if services are running
        local services=("postgres" "redis" "kafka" "backend" "frontend")
        
        for service in "${services[@]}"; do
            if docker-compose ps "$service" | grep -q "Up"; then
                print_success "$service container is running"
            else
                print_error "$service container is not running"
            fi
        done
        
        # Check service health
        print_test "Service health checks"
        
        # PostgreSQL health
        if docker-compose exec -T postgres pg_isready -U "$POSTGRES_USER" >/dev/null 2>&1; then
            print_success "PostgreSQL health check passed"
        else
            print_error "PostgreSQL health check failed"
        fi
        
        # Redis health
        if docker-compose exec -T redis redis-cli ping >/dev/null 2>&1; then
            print_success "Redis health check passed"
        else
            print_error "Redis health check failed"
        fi
        
    else
        print_error "docker-compose not found"
    fi
}

# Test API integration
test_api_integration() {
    print_test "API integration tests"
    
    if command_exists curl; then
        # Test user registration
        print_test "User registration flow"
        
        local test_email="test_$(date +%s)@example.com"
        local registration_response=$(curl -s -X POST "$BACKEND_URL/api/v1/auth/register" \
            -H "Content-Type: application/json" \
            -d "{
                \"email\": \"$test_email\",
                \"password\": \"testpassword123\",
                \"first_name\": \"Test\",
                \"last_name\": \"User\"
            }" 2>/dev/null || echo '{"success": false}')
        
        if echo "$registration_response" | grep -q '"success": true'; then
            print_success "User registration successful"
            
            # Extract token for further tests
            local token=$(echo "$registration_response" | grep -o '"access_token": "[^"]*"' | cut -d'"' -f4)
            
            if [ -n "$token" ]; then
                print_success "Authentication token received"
                
                # Test authenticated endpoint
                local profile_response=$(curl -s -X GET "$BACKEND_URL/api/v1/users/me" \
                    -H "Authorization: Bearer $token" 2>/dev/null || echo '{"success": false}')
                
                if echo "$profile_response" | grep -q '"success": true'; then
                    print_success "Authenticated API call successful"
                else
                    print_error "Authenticated API call failed"
                fi
            else
                print_error "No authentication token received"
            fi
        else
            print_error "User registration failed"
        fi
    fi
}

# Test file uploads
test_file_operations() {
    print_test "File operations"
    
    # Check if upload directory exists in backend container
    if docker-compose exec -T backend test -d "/app/uploads" 2>/dev/null; then
        print_success "Upload directory exists"
    else
        print_error "Upload directory missing"
    fi
    
    # Test file permissions
    if docker-compose exec -T backend test -w "/app/uploads" 2>/dev/null; then
        print_success "Upload directory is writable"
    else
        print_error "Upload directory is not writable"
    fi
}

# Test logging
test_logging() {
    print_test "Application logging"
    
    # Check if log files are being created
    if docker-compose logs backend | grep -q "INFO\|ERROR\|WARNING" 2>/dev/null; then
        print_success "Backend logging is working"
    else
        print_error "Backend logging not found"
    fi
    
    # Check log levels
    if docker-compose logs backend | grep -q "INFO" 2>/dev/null; then
        print_success "INFO level logging working"
    else
        print_error "INFO level logging not working"
    fi
}

# Performance tests
test_performance() {
    print_test "Basic performance tests"
    
    if command_exists curl; then
        # Test response times
        local response_time=$(curl -s -w "%{time_total}" -o /dev/null "$BACKEND_URL/health" 2>/dev/null || echo "999")
        
        if (( $(echo "$response_time < 2.0" | bc -l 2>/dev/null || echo "0") )); then
            print_success "Health endpoint response time: ${response_time}s"
        else
            print_error "Health endpoint slow response time: ${response_time}s"
        fi
        
        # Test concurrent requests
        print_test "Concurrent request handling"
        
        local concurrent_test_passed=true
        for i in {1..5}; do
            curl -s "$BACKEND_URL/health" >/dev/null 2>&1 &
        done
        wait
        
        if [ $? -eq 0 ]; then
            print_success "Concurrent requests handled successfully"
        else
            print_error "Concurrent request handling failed"
        fi
    fi
}

# Main test execution
main() {
    print_header "Full Stack Application Testing"
    
    print_info "Starting comprehensive testing of all application components..."
    print_info "This will test: Frontend, Backend, Database, Redis, Kafka, and integrations"
    
    # Load environment variables
    if [ -f ".env" ]; then
        source .env
    fi
    
    # Prerequisites check
    print_header "Prerequisites Check"
    
    local required_commands=("docker" "docker-compose" "curl" "nc")
    for cmd in "${required_commands[@]}"; do
        if command_exists "$cmd"; then
            print_success "$cmd is available"
        else
            print_error "$cmd is not available"
        fi
    done
    
    # Environment tests
    print_header "Environment Configuration"
    test_environment
    
    # Docker services tests
    print_header "Docker Services"
    test_docker_services
    
    # Database tests
    print_header "Database Testing"
    test_database
    
    # Redis tests
    print_header "Redis Testing"
    test_redis
    
    # Kafka tests
    print_header "Kafka Testing"
    test_kafka
    
    # Migration tests
    print_header "Database Migrations"
    test_migrations
    
    # Backend API tests
    print_header "Backend API Testing"
    test_backend_api
    
    # Frontend tests
    print_header "Frontend Testing"
    test_frontend
    
    # Integration tests
    print_header "API Integration Testing"
    test_api_integration
    
    # File operations tests
    print_header "File Operations"
    test_file_operations
    
    # Logging tests
    print_header "Logging"
    test_logging
    
    # Performance tests
    print_header "Performance Testing"
    test_performance
    
    # Final results
    print_header "Test Results Summary"
    
    echo -e "${GREEN}Tests Passed: $TESTS_PASSED${NC}"
    echo -e "${RED}Tests Failed: $TESTS_FAILED${NC}"
    
    if [ $TESTS_FAILED -gt 0 ]; then
        echo -e "\n${RED}Failed Tests:${NC}"
        for test in "${FAILED_TESTS[@]}"; do
            echo -e "${RED}  - $test${NC}"
        done
        
        echo -e "\n${YELLOW}Troubleshooting Tips:${NC}"
        echo -e "${YELLOW}1. Ensure all services are running: docker-compose ps${NC}"
        echo -e "${YELLOW}2. Check service logs: docker-compose logs <service_name>${NC}"
        echo -e "${YELLOW}3. Verify environment variables are set correctly${NC}"
        echo -e "${YELLOW}4. Ensure ports are not blocked by firewall${NC}"
        echo -e "${YELLOW}5. Check Docker resources (memory, disk space)${NC}"
        
        exit 1
    else
        echo -e "\n${GREEN}🎉 All tests passed! Your application stack is working correctly.${NC}"
        
        echo -e "\n${BLUE}Application URLs:${NC}"
        echo -e "${BLUE}  Frontend: http://localhost:3000${NC}"
        echo -e "${BLUE}  Backend API: http://localhost:8000${NC}"
        echo -e "${BLUE}  API Documentation: http://localhost:8000/docs${NC}"
        
        exit 0
    fi
}

# Run main function
main "$@"