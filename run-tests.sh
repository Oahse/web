#!/bin/bash

# Comprehensive test runner for integration and chaos tests
# Usage: ./run-tests.sh [integration|chaos|frontend|all]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default test type
TEST_TYPE=${1:-all}

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
    print_success "Docker is running"
}

# Function to check if required tools are installed
check_dependencies() {
    print_status "Checking dependencies..."
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed"
        exit 1
    fi
    
    # Check Node.js (for frontend tests)
    if ! command -v node &> /dev/null; then
        print_warning "Node.js is not installed - frontend tests will be skipped"
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed"
        exit 1
    fi
    
    print_success "All dependencies are available"
}

# Function to setup test environment
setup_test_environment() {
    print_status "Setting up test environment..."
    
    # Stop any existing test containers
    docker-compose -f docker-compose.yml down -v --remove-orphans 2>/dev/null || true
    
    # Start test infrastructure
    print_status "Starting test infrastructure..."
    docker-compose -f docker-compose.yml up -d test-postgres test-redis test-kafka
    
    # Wait for services to be healthy
    print_status "Waiting for services to be ready..."
    
    # Wait for PostgreSQL
    print_status "Waiting for PostgreSQL..."
    timeout=60
    while ! docker-compose -f docker-compose.yml exec -T test-postgres pg_isready -U test_user -d test_banwee_db > /dev/null 2>&1; do
        sleep 2
        timeout=$((timeout - 2))
        if [ $timeout -le 0 ]; then
            print_error "PostgreSQL failed to start within timeout"
            exit 1
        fi
    done
    print_success "PostgreSQL is ready"
    
    # Wait for Redis
    print_status "Waiting for Redis..."
    timeout=30
    while ! docker-compose -f docker-compose.yml exec -T test-redis redis-cli ping > /dev/null 2>&1; do
        sleep 1
        timeout=$((timeout - 1))
        if [ $timeout -le 0 ]; then
            print_error "Redis failed to start within timeout"
            exit 1
        fi
    done
    print_success "Redis is ready"
    
    # Wait for Kafka
    print_status "Waiting for Kafka..."
    timeout=120
    while ! docker-compose -f docker-compose.yml exec -T test-kafka kafka-broker-api-versions --bootstrap-server localhost:9092 > /dev/null 2>&1; do
        sleep 3
        timeout=$((timeout - 3))
        if [ $timeout -le 0 ]; then
            print_error "Kafka failed to start within timeout"
            exit 1
        fi
    done
    print_success "Kafka is ready"
    
    print_success "Test environment is ready"
}

# Function to run backend integration tests
run_integration_tests() {
    print_status "Running backend integration tests..."
    
    cd backend
    
    # Set test environment variables
    export DATABASE_URL="postgresql://test_user:test_password@localhost:5433/test_banwee_db"
    export REDIS_URL="redis://localhost:6380"
    export KAFKA_BOOTSTRAP_SERVERS="localhost:9093"
    export TESTING="true"
    export LOG_LEVEL="INFO"
    
    # Install Python dependencies if needed
    if [ ! -d ".venv" ]; then
        print_status "Creating Python virtual environment..."
        python3 -m venv .venv
    fi
    
    source .venv/bin/activate
    pip install -r requirements.txt > /dev/null 2>&1 || true
    pip install pytest pytest-asyncio pytest-timeout > /dev/null 2>&1 || true
    
    # Run integration tests
    python -m pytest tests/integration/ -v --tb=short --durations=10 \
        --junitxml=../test_results_integration.xml \
        --timeout=300 || {
        print_error "Integration tests failed"
        cd ..
        return 1
    }
    
    cd ..
    print_success "Integration tests completed"
}

# Function to run chaos tests
run_chaos_tests() {
    print_status "Running Kafka consumer chaos tests..."
    
    cd backend
    
    # Set test environment variables
    export DATABASE_URL="postgresql://test_user:test_password@localhost:5433/test_banwee_db"
    export REDIS_URL="redis://localhost:6380"
    export KAFKA_BOOTSTRAP_SERVERS="localhost:9093"
    export TESTING="true"
    export LOG_LEVEL="INFO"
    
    source .venv/bin/activate 2>/dev/null || true
    
    # Run chaos tests with special configuration
    python -m pytest tests/chaos/ -v --tb=short --durations=10 \
        --junitxml=../test_results_chaos.xml \
        --timeout=600 \
        --maxfail=5 \
        -m "chaos" || {
        print_error "Chaos tests failed"
        cd ..
        return 1
    }
    
    cd ..
    print_success "Chaos tests completed"
}

# Function to run frontend tests
run_frontend_tests() {
    print_status "Running frontend integration tests..."
    
    if [ ! -d "frontend" ]; then
        print_warning "Frontend directory not found - skipping frontend tests"
        return 0
    fi
    
    cd frontend
    
    # Install Node.js dependencies if needed
    if [ ! -d "node_modules" ]; then
        print_status "Installing Node.js dependencies..."
        npm install > /dev/null 2>&1 || {
            print_error "Failed to install Node.js dependencies"
            cd ..
            return 1
        }
    fi
    
    # Run frontend integration tests
    npm run test:integration || {
        print_error "Frontend tests failed"
        cd ..
        return 1
    }
    
    cd ..
    print_success "Frontend tests completed"
}

# Function to cleanup test environment
cleanup_test_environment() {
    print_status "Cleaning up test environment..."
    docker-compose -f docker-compose.yml down -v --remove-orphans 2>/dev/null || true
    print_success "Test environment cleaned up"
}

# Function to generate test report
generate_test_report() {
    print_status "Generating test report..."
    
    report_file="test_report_$(date +%Y%m%d_%H%M%S).txt"
    
    {
        echo "=== INTEGRATION AND CHAOS TEST REPORT ==="
        echo "Generated: $(date)"
        echo "Test Type: $TEST_TYPE"
        echo ""
        
        if [ -f "test_results_integration.xml" ]; then
            echo "Integration Tests:"
            grep -o 'tests="[^"]*"' test_results_integration.xml | head -1
            grep -o 'failures="[^"]*"' test_results_integration.xml | head -1
            grep -o 'errors="[^"]*"' test_results_integration.xml | head -1
            echo ""
        fi
        
        if [ -f "test_results_chaos.xml" ]; then
            echo "Chaos Tests:"
            grep -o 'tests="[^"]*"' test_results_chaos.xml | head -1
            grep -o 'failures="[^"]*"' test_results_chaos.xml | head -1
            grep -o 'errors="[^"]*"' test_results_chaos.xml | head -1
            echo ""
        fi
        
        echo "=== END REPORT ==="
    } > "$report_file"
    
    print_success "Test report generated: $report_file"
}

# Main execution
main() {
    print_status "Starting comprehensive test suite..."
    print_status "Test type: $TEST_TYPE"
    
    # Check prerequisites
    check_docker
    check_dependencies
    
    # Setup test environment
    setup_test_environment
    
    # Trap to ensure cleanup on exit
    trap cleanup_test_environment EXIT
    
    # Run tests based on type
    case $TEST_TYPE in
        "integration")
            run_integration_tests
            ;;
        "chaos")
            run_chaos_tests
            ;;
        "frontend")
            run_frontend_tests
            ;;
        "all")
            run_integration_tests
            run_chaos_tests
            run_frontend_tests
            ;;
        *)
            print_error "Invalid test type: $TEST_TYPE"
            print_error "Valid options: integration, chaos, frontend, all"
            exit 1
            ;;
    esac
    
    # Generate report
    generate_test_report
    
    print_success "All tests completed successfully!"
}

# Show usage if help is requested
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "Usage: $0 [integration|chaos|frontend|all]"
    echo ""
    echo "Test types:"
    echo "  integration  - Run backend integration tests for checkout flow"
    echo "  chaos        - Run Kafka consumer chaos tests"
    echo "  frontend     - Run frontend integration tests"
    echo "  all          - Run all test types (default)"
    echo ""
    echo "Examples:"
    echo "  $0                    # Run all tests"
    echo "  $0 integration        # Run only integration tests"
    echo "  $0 chaos             # Run only chaos tests"
    exit 0
fi

# Run main function
main