# Banwee API - Comprehensive Guide

Complete documentation for the Banwee E-commerce Platform API, including authentication, endpoints, logging, and best practices.

## Table of Contents
- [Getting Started](#getting-started)
- [Authentication](#authentication)
- [API Endpoints](#api-endpoints)
- [Checkout Validation](#checkout-validation)
- [Logging System](#logging-system)
- [Error Handling](#error-handling)
- [Environment Configuration](#environment-configuration)
- [Testing](#testing)
- [Best Practices](#best-practices)

## Getting Started

### Base URLs
- **Development**: `http://localhost:8000`
- **Production**: `https://api.banwee.com`

### API Versioning
All APIs are versioned and prefixed with `/v1/`

### Content Type
All requests should use `Content-Type: application/json`

### Response Format
All responses follow this structure:
```json
{
  "success": true,
  "data": {},
  "message": "Operation completed successfully",
  "timestamp": "2026-01-26T15:30:00Z"
}
```

## Authentication

### JWT Token Authentication
The API uses JWT tokens for authentication. Include the token in the Authorization header:

```http
Authorization: Bearer your-jwt-token-here
```

### Authentication Endpoints

#### Register User
```http
POST /v1/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword123",
  "first_name": "John",
  "last_name": "Doe"
}
```

#### Login
```http
POST /v1/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

#### Get Current User
```http
GET /v1/auth/me
Authorization: Bearer your-token
```

## API Endpoints

### Products

#### Get All Products
```http
GET /v1/products?page=1&limit=20&category=electronics&search=phone
```

**Query Parameters:**
- `page`: Page number (default: 1)
- `limit`: Items per page (default: 20, max: 100)
- `category`: Filter by category
- `search`: Search term
- `min_price`: Minimum price filter
- `max_price`: Maximum price filter
- `sort_by`: Sort field (created_at, price, name)
- `sort_order`: Sort direction (asc, desc)

#### Get Product Details
```http
GET /v1/products/{product_id}
```

### Cart Management

#### Get User Cart
```http
GET /v1/cart
Authorization: Bearer your-token
```

#### Add Item to Cart
```http
POST /v1/cart/items
Authorization: Bearer your-token
Content-Type: application/json

{
  "variant_id": "variant-uuid",
  "quantity": 2
}
```

#### Update Cart Item
```http
PUT /v1/cart/items/{item_id}
Authorization: Bearer your-token
Content-Type: application/json

{
  "quantity": 3
}
```

### Order Management

#### Checkout from Cart
```http
POST /v1/orders/checkout
Authorization: Bearer your-token
Content-Type: application/json

{
  "shipping_address_id": "address-uuid",
  "shipping_method_id": "method-uuid",
  "payment_method_id": "payment-uuid",
  "notes": "Delivery instructions"
}
```

#### Get User Orders
```http
GET /v1/orders?page=1&limit=10&status=active
Authorization: Bearer your-token
```

#### Track Order
```http
GET /v1/orders/{order_id}/tracking
Authorization: Bearer your-token
```

### Admin Endpoints

#### Get Admin Stats
```http
GET /v1/admin/stats
Authorization: Bearer admin-token
```

#### Get All Users (Admin)
```http
GET /v1/admin/users?page=1&limit=20&role=Customer&search=john
Authorization: Bearer admin-token
```

#### Update Order Status (Admin)
```http
PUT /v1/admin/orders/{order_id}/status
Authorization: Bearer admin-token
Content-Type: application/json

{
  "status": "shipped",
  "tracking_number": "1Z999AA1234567890",
  "carrier_name": "UPS"
}
```

## Checkout Validation

The checkout process includes comprehensive validation to ensure data integrity and prevent errors.

### Validation Process

1. **Cart Validation**: Verify cart items exist and are available
2. **Price Validation**: Recalculate prices to prevent tampering
3. **Inventory Check**: Ensure sufficient stock for all items
4. **Address Validation**: Verify shipping address is complete
5. **Payment Validation**: Confirm payment method is valid

### Checkout Request
```json
{
  "shipping_address_id": "uuid",
  "shipping_method_id": "uuid", 
  "payment_method_id": "uuid",
  "notes": "Special delivery instructions",
  "promo_code": "DISCOUNT10"
}
```

### Validation Response
```json
{
  "success": true,
  "data": {
    "order_id": "uuid",
    "total_amount": 99.99,
    "validated_items": [
      {
        "variant_id": "uuid",
        "quantity": 2,
        "unit_price": 29.99,
        "total_price": 59.98
      }
    ],
    "shipping_cost": 9.99,
    "tax_amount": 8.00,
    "discount_amount": 5.00
  }
}
```

### Validation Errors
```json
{
  "success": false,
  "error": {
    "code": "CHECKOUT_VALIDATION_ERROR",
    "message": "Checkout validation failed",
    "details": {
      "price_discrepancies": [
        {
          "variant_id": "uuid",
          "expected_price": 29.99,
          "provided_price": 25.99
        }
      ],
      "insufficient_stock": [
        {
          "variant_id": "uuid",
          "requested": 5,
          "available": 2
        }
      ]
    }
  }
}
```

## Logging System

The application uses an enhanced structured logging system with JSON output and contextual information.

### Features
- **Structured JSON Logging**: All logs in JSON format for easy parsing
- **File Rotation**: Automatic log file rotation (size and time-based)
- **Contextual Information**: Rich context including user IDs, request IDs, endpoints
- **Multiple Log Levels**: Debug, Info, Warning, Error, Critical
- **Specialized Methods**: HTTP requests, database operations, business events

### Log Format
```json
{
  "timestamp": "2026-01-26T15:30:07.256092",
  "level": "INFO",
  "message": "User logged in",
  "service": "banwee-api",
  "logger": "auth_service",
  "user_id": "user123",
  "endpoint": "/auth/login",
  "request_id": "req_456",
  "metadata": {
    "login_method": "email",
    "session_id": "sess_789"
  }
}
```

### Using the Logger

#### Basic Logging
```python
from core.logging import get_structured_logger

logger = get_structured_logger(__name__)

logger.info(
    "User action performed",
    user_id="user123",
    endpoint="/api/orders",
    metadata={"action": "create_order", "amount": 99.99}
)
```

#### HTTP Request Logging
```python
logger.log_request(
    method="POST",
    endpoint="/api/orders",
    user_id="user123",
    duration_ms=150.5,
    status_code=201
)
```

#### Business Event Logging
```python
logger.log_business_event(
    "order_created",
    {
        "order_id": "ord_789",
        "amount": 99.99,
        "items_count": 3
    },
    user_id="user123"
)
```

## Error Handling

### Error Response Format
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": {
      "field": "email",
      "issue": "Invalid email format"
    }
  },
  "timestamp": "2026-01-26T15:30:00Z"
}
```

### Common Error Codes

| Code | Status | Description |
|------|--------|-------------|
| `VALIDATION_ERROR` | 400 | Invalid input data |
| `UNAUTHORIZED` | 401 | Authentication required |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `CONFLICT` | 409 | Resource conflict |
| `CHECKOUT_VALIDATION_ERROR` | 400 | Checkout validation failed |
| `INSUFFICIENT_STOCK` | 400 | Not enough inventory |
| `PAYMENT_ERROR` | 400 | Payment processing failed |
| `RATE_LIMITED` | 429 | Too many requests |
| `INTERNAL_ERROR` | 500 | Server error |

### Error Handling Examples

#### JavaScript/Fetch
```javascript
async function apiCall(url, options) {
  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
        ...options.headers
      }
    });
    
    const data = await response.json();
    
    if (!data.success) {
      throw new Error(data.error.message);
    }
    
    return data.data;
  } catch (error) {
    console.error('API Error:', error.message);
    throw error;
  }
}
```

## Environment Configuration

### Required Variables

#### Critical (All Environments)
```bash
SECRET_KEY=<64-character-random-string>
STRIPE_SECRET_KEY=sk_test_... # or sk_live_ for production
STRIPE_WEBHOOK_SECRET=whsec_...
POSTGRES_DB_URL=postgresql+asyncpg://user:pass@host:port/db
```

#### Production Only
```bash
MAILGUN_API_KEY=your_mailgun_api_key
MAILGUN_DOMAIN=mg.yourdomain.com
```

### Environment Files
- **`.dev.env`**: Development configuration
- **`.prod.env`**: Production configuration
- **`.env.example`**: Template with documentation

### Configuration Validation
The application validates all configuration at startup using Pydantic models:

- Type checking and format validation
- Required field verification
- Production-specific stricter rules
- Detailed error messages for invalid configuration

## Testing

### Health Check
```bash
curl http://localhost:8000/v1/health/live
```

### Authentication Test
```bash
# Login
curl -X POST "http://localhost:8000/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "password"}'

# Use token
curl -X GET "http://localhost:8000/v1/auth/me" \
  -H "Authorization: Bearer your-token"
```

### Checkout Validation Test
```bash
curl -X POST "http://localhost:8000/v1/orders/checkout" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-token" \
  -d '{
    "shipping_address_id": "uuid",
    "shipping_method_id": "uuid",
    "payment_method_id": "uuid"
  }'
```

### Using Python
```python
import requests

BASE_URL = "http://localhost:8000/v1"

# Test login
response = requests.post(f"{BASE_URL}/auth/login", json={
    "email": "test@example.com",
    "password": "password"
})

token = response.json()["data"]["access_token"]

# Test authenticated endpoint
response = requests.get(f"{BASE_URL}/auth/me", 
    headers={"Authorization": f"Bearer {token}"}
)
```

## Best Practices

### API Usage
1. **Always include proper headers**: Content-Type and Authorization
2. **Handle errors gracefully**: Check success field and handle error responses
3. **Use pagination**: Don't fetch all data at once
4. **Implement retry logic**: For transient failures
5. **Cache responses**: Where appropriate to reduce API calls

### Security
1. **Store tokens securely**: Use secure storage mechanisms
2. **Implement token refresh**: Handle token expiration
3. **Validate input**: Always validate data on client side too
4. **Use HTTPS**: In production environments
5. **Rate limiting**: Respect rate limits and implement backoff

### Logging
1. **Include context**: Always provide user_id, request_id when available
2. **Use appropriate levels**: Debug for development, Info for normal flow
3. **Log business events**: Important for analytics and debugging
4. **Don't log sensitive data**: Passwords, tokens, personal information
5. **Use structured logging**: Easier to parse and analyze

### Performance
1. **Use appropriate page sizes**: Balance between performance and data needs
2. **Implement caching**: Cache frequently accessed data
3. **Optimize queries**: Use filters and search parameters effectively
4. **Monitor response times**: Track API performance
5. **Use compression**: Enable gzip compression for responses

### Development
1. **Use environment variables**: Never hardcode configuration
2. **Test thoroughly**: Include edge cases and error scenarios
3. **Document changes**: Update API documentation when making changes
4. **Version APIs**: Use versioning for breaking changes
5. **Monitor logs**: Regularly check application logs for issues

## Migration and Deployment

### Database Migrations
- Automatic migrations on Docker startup
- Use Alembic for schema changes
- Backup database before major migrations

### Environment Setup
1. Copy `.env.example` to `.dev.env` or `.prod.env`
2. Update all required variables
3. Validate configuration before deployment
4. Use Docker Compose for consistent environments

### Production Checklist
- [ ] All environment variables configured
- [ ] Database migrations applied
- [ ] SSL certificates configured
- [ ] Monitoring and logging enabled
- [ ] Backup procedures in place
- [ ] Security headers configured
- [ ] Rate limiting enabled

This comprehensive guide covers all aspects of using the Banwee API effectively. For specific implementation details, refer to the individual endpoint documentation and code examples provided.