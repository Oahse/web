also# Banwee Backend Test Suite

This directory contains comprehensive tests for the Banwee e-commerce backend API and services.

## Test Structure

```
tests/
├── conftest.py                    # Test configuration and fixtures
├── test_api_auth.py              # Authentication API tests
├── test_api_cart.py              # Cart API tests
├── test_api_inventory.py         # Inventory API tests
├── test_api_orders.py            # Orders API tests
├── test_api_payments.py          # Payments API tests
├── test_api_products.py          # Products API tests
├── test_services_auth.py         # Authentication service tests
├── test_services_cart.py         # Cart service tests
├── test_services_orders.py       # Orders service tests
├── test_services_payments.py     # Payments service tests
├── test_models.py                # Database model tests
├── test_integration.py           # Integration tests
├── run_tests.py                  # Test runner script
└── README.md                     # This file
```

## Test Categories

### API Tests (`test_api_*.py`)
- **Authentication**: User registration, login, password reset, email verification
- **Products**: Product CRUD, search, categories, variants, recommendations
- **Cart**: Add/remove items, quantity updates, validation, pricing
- **Orders**: Order creation, checkout validation, order management, tracking
- **Payments**: Payment methods, payment processing, refunds, transactions
- **Inventory**: Stock management, warehouse operations, adjustments

### Service Tests (`test_services_*.py`)
- **Authentication Service**: Password hashing, JWT tokens, user management
- **Cart Service**: Cart operations, validation, pricing calculations
- **Orders Service**: Order processing, pricing validation, checkout logic
- **Payments Service**: Payment processing, failure handling, refunds

### Model Tests (`test_models.py`)
- Database model creation and validation
- Constraint testing (unique, foreign key, check constraints)
- Model relationships and cascading operations

### Integration Tests (`test_integration.py`)
- Complete user workflows (registration → shopping → checkout)
- End-to-end order processing
- Cross-service interactions
- Error handling across the application

## Test Features

### Comprehensive Coverage
- **API Endpoints**: All 50+ API endpoints tested
- **Service Functions**: All business logic functions tested
- **Database Models**: All 21+ models with relationships tested
- **Authentication**: JWT tokens, role-based access, security features
- **Payment Processing**: Stripe integration, failure handling, refunds
- **Inventory Management**: Stock tracking, adjustments, low stock alerts
- **Order Processing**: Complete checkout flow, pricing validation

### Security Testing
- Authentication and authorization
- Input validation and sanitization
- SQL injection prevention
- Price tampering detection
- Rate limiting and abuse prevention

### Performance Testing
- Bulk operations
- Pagination efficiency
- Database query optimization
- Caching mechanisms

### Error Handling
- API error responses
- Service layer exceptions
- Database constraint violations
- External service failures (Stripe, email)

## Running Tests

### Prerequisites
```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx pytest-cov

# Ensure you're in the backend directory
cd backend
```

### Quick Start
```bash
# Run all tests
python tests/run_tests.py

# Run with coverage
python tests/run_tests.py --coverage

# Run specific test categories
python tests/run_tests.py --api        # API tests only
python tests/run_tests.py --services   # Service tests only
python tests/run_tests.py --models     # Model tests only
```

### Advanced Usage
```bash
# Run specific test file
python tests/run_tests.py --file test_api_auth.py

# Run specific test function
python tests/run_tests.py --test test_login_success

# Run with verbose output
python tests/run_tests.py --verbose

# Skip slow tests
python tests/run_tests.py --fast

# Run integration tests only
python tests/run_tests.py --integration
```

### Direct pytest Usage
```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=. --cov-report=html

# Run specific markers
pytest tests/ -m "api"           # API tests
pytest tests/ -m "service"       # Service tests
pytest tests/ -m "integration"   # Integration tests
pytest tests/ -m "not slow"      # Skip slow tests

# Run specific test file
pytest tests/test_api_auth.py -v

# Run specific test function
pytest tests/test_api_auth.py::TestAuthAPI::test_login_success -v
```

## Test Configuration

### Environment Setup
Tests use an in-memory SQLite database and mock external services:
- **Database**: SQLite in-memory for fast, isolated tests
- **Redis**: Mocked for caching and session management
- **Stripe**: Mocked for payment processing
- **Email**: Mocked for email notifications

### Fixtures
The test suite includes comprehensive fixtures:
- **Database**: Automatic setup/teardown with transactions
- **Users**: Test users with different roles (customer, admin, supplier)
- **Products**: Categories, products, variants with inventory
- **Authentication**: JWT tokens for different user types
- **External Services**: Mocked Stripe, Redis, email services

### Test Data Factory
Use the `TestDataFactory` for creating test data:
```python
def test_example(test_data_factory):
    user_data = test_data_factory.user_data(email="custom@example.com")
    product_data = test_data_factory.product_data(name="Custom Product")
```

## Test Markers

Tests are organized with pytest markers:
- `@pytest.mark.api` - API endpoint tests
- `@pytest.mark.service` - Service layer tests
- `@pytest.mark.model` - Database model tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.slow` - Slow-running tests
- `@pytest.mark.unit` - Unit tests

## Coverage Goals

Target coverage levels:
- **Overall**: 90%+
- **API Endpoints**: 95%+
- **Service Functions**: 95%+
- **Critical Business Logic**: 100%

## Continuous Integration

Tests are designed to run in CI/CD pipelines:
- Fast execution (< 2 minutes for full suite)
- No external dependencies
- Deterministic results
- Comprehensive error reporting

## Writing New Tests

### API Test Template
```python
@pytest.mark.asyncio
async def test_new_endpoint(self, async_client: AsyncClient, auth_headers: dict):
    """Test description."""
    response = await async_client.get("/new-endpoint", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
```

### Service Test Template
```python
@pytest.mark.asyncio
async def test_new_service_function(self, db_session: AsyncSession):
    """Test description."""
    service = NewService(db_session)
    
    result = await service.new_function(param1, param2)
    
    assert result is not None
    assert result.property == expected_value
```

### Best Practices
1. **Descriptive Names**: Test names should clearly describe what is being tested
2. **Arrange-Act-Assert**: Structure tests with clear setup, execution, and verification
3. **Independent Tests**: Each test should be independent and not rely on others
4. **Mock External Services**: Always mock external APIs and services
5. **Test Edge Cases**: Include tests for error conditions and edge cases
6. **Use Fixtures**: Leverage fixtures for common test data and setup

## Troubleshooting

### Common Issues

**Database Connection Errors**:
```bash
# Ensure test database is properly configured
export DATABASE_URL="sqlite+aiosqlite:///:memory:"
```

**Import Errors**:
```bash
# Ensure you're in the backend directory
cd backend
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

**Async Test Issues**:
```bash
# Ensure pytest-asyncio is installed and configured
pip install pytest-asyncio
```

### Debug Mode
```bash
# Run tests with debug output
pytest tests/ -v -s --tb=long

# Run single test with debugging
pytest tests/test_api_auth.py::TestAuthAPI::test_login_success -v -s --pdb
```

## Contributing

When adding new features:
1. Write tests first (TDD approach)
2. Ensure all existing tests pass
3. Add tests for new API endpoints
4. Add tests for new service functions
5. Update integration tests if needed
6. Maintain test coverage above 90%

## Performance Benchmarks

Test suite performance targets:
- **Unit Tests**: < 30 seconds
- **Integration Tests**: < 60 seconds
- **Full Suite**: < 2 minutes
- **Coverage Report**: < 30 seconds additional

## Security Testing

The test suite includes security-focused tests:
- Authentication bypass attempts
- Authorization boundary testing
- Input validation and sanitization
- SQL injection prevention
- XSS prevention
- CSRF protection
- Rate limiting validation

## Monitoring and Reporting

Test results and coverage reports are generated in:
- `htmlcov/` - HTML coverage reports
- `pytest-report.html` - Test execution report
- Console output with detailed results

For questions or issues with the test suite, please refer to the main project documentation or create an issue in the project repository.