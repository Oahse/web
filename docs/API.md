# API Usage Guide

Complete guide for using the application APIs, including authentication, endpoints, and examples.

## Table of Contents
- [Getting Started](#getting-started)
- [Authentication](#authentication)
- [Core APIs](#core-apis)
- [Admin APIs](#admin-apis)
- [Error Handling](#error-handling)
- [Rate Limiting](#rate-limiting)
- [Examples](#examples)

## Getting Started

### Base URL
```
Development: http://localhost:8000
Production: https://your-domain.com
```

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
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## Authentication

### Register User
```http
POST /v1/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword123",
  "firstname": "John",
  "lastname": "Doe"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "user": {
      "id": "uuid-here",
      "email": "user@example.com",
      "firstname": "John",
      "lastname": "Doe",
      "role": "Customer"
    },
    "access_token": "jwt-token-here",
    "token_type": "bearer"
  },
  "message": "User registered successfully"
}
```

### Login
```http
POST /v1/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

### Using Authentication Token
Include the token in the Authorization header:
```http
Authorization: Bearer your-jwt-token-here
```

## Core APIs

### User Management

#### Get Current User Profile
```http
GET /v1/users/me
Authorization: Bearer your-token
```

#### Update User Profile
```http
PUT /v1/users/me
Authorization: Bearer your-token
Content-Type: application/json

{
  "firstname": "Jane",
  "lastname": "Smith",
  "phone": "+1234567890"
}
```

#### Add User Address
```http
POST /v1/users/me/addresses
Authorization: Bearer your-token
Content-Type: application/json

{
  "street": "123 Main St",
  "city": "New York",
  "state": "NY",
  "country": "USA",
  "post_code": "10001",
  "is_default": true
}
```

### Product Management

#### Get All Products
```http
GET /v1/products?page=1&limit=20&category=electronics
```

**Query Parameters:**
- `page`: Page number (default: 1)
- `limit`: Items per page (default: 20, max: 100)
- `category`: Filter by category
- `search`: Search term
- `min_price`: Minimum price filter
- `max_price`: Maximum price filter

#### Get Product Details
```http
GET /v1/products/{product_id}
```

#### Get Product Variants
```http
GET /v1/products/{product_id}/variants
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

#### Remove Cart Item
```http
DELETE /v1/cart/items/{item_id}
Authorization: Bearer your-token
```

### Order Management

#### Create Order
```http
POST /v1/orders
Authorization: Bearer your-token
Content-Type: application/json

{
  "items": [
    {
      "variant_id": "variant-uuid",
      "quantity": 2
    }
  ],
  "shipping_address": {
    "street": "123 Main St",
    "city": "New York",
    "state": "NY",
    "country": "USA",
    "post_code": "10001"
  },
  "payment_method": "credit_card",
  "notes": "Please handle with care"
}
```

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

#### Get Order Details
```http
GET /v1/orders/{order_id}
Authorization: Bearer your-token
```

#### Cancel Order
```http
PUT /v1/orders/{order_id}/cancel
Authorization: Bearer your-token
```

#### Track Order
```http
GET /v1/orders/{order_id}/tracking
Authorization: Bearer your-token
```

#### Public Order Tracking (No Auth Required)
```http
GET /v1/orders/track/{order_id}
```

### Subscription Management

#### Create Subscription
```http
POST /v1/subscriptions
Authorization: Bearer your-token
Content-Type: application/json

{
  "plan_id": "monthly-plan",
  "status": "active",
  "price": 29.99,
  "currency": "USD",
  "billing_cycle": "monthly",
  "auto_renew": true
}
```

#### Get User Subscriptions
```http
GET /v1/subscriptions?page=1&limit=10
Authorization: Bearer your-token
```

#### Update Subscription
```http
PUT /v1/subscriptions/{subscription_id}
Authorization: Bearer your-token
Content-Type: application/json

{
  "auto_renew": false,
  "status": "paused"
}
```

#### Cancel Subscription
```http
DELETE /v1/subscriptions/{subscription_id}
Authorization: Bearer your-token
```

### Payment Management

#### Get Payment Methods
```http
GET /v1/users/me/payment-methods
Authorization: Bearer your-token
```

#### Add Payment Method
```http
POST /v1/users/{user_id}/payment-methods
Authorization: Bearer your-token
Content-Type: application/json

{
  "stripe_token": "tok_visa",
  "is_default": true
}
```

#### Create Payment Intent
```http
POST /v1/payments/create-payment-intent
Authorization: Bearer your-token
Content-Type: application/json

{
  "order_id": "order-uuid",
  "subtotal": 99.99,
  "currency": "USD",
  "shipping_address_id": "address-uuid",
  "payment_method_id": "payment-uuid",
  "expires_in_minutes": 30
}
```

#### Process Payment
```http
POST /v1/payments/process
Authorization: Bearer your-token
Content-Type: application/json

{
  "amount": 99.99,
  "payment_method_id": "payment-uuid",
  "order_id": "order-uuid",
  "currency": "USD"
}
```

#### Confirm Payment
```http
POST /v1/payments/confirm
Authorization: Bearer your-token
Content-Type: application/json

{
  "payment_intent_id": "pi_stripe_id",
  "handle_3d_secure": true
}
```

## Admin APIs

### Admin Authentication
Admin APIs require admin role. Include admin token in Authorization header.

### User Management

#### Get All Users
```http
GET /v1/admin/users?page=1&limit=20&role=Customer&search=john
Authorization: Bearer admin-token
```

#### Create User (Admin)
```http
POST /v1/admin/users
Authorization: Bearer admin-token
Content-Type: application/json

{
  "email": "newuser@example.com",
  "password": "temppassword",
  "firstname": "New",
  "lastname": "User",
  "role": "Customer"
}
```

#### Update User Status
```http
PUT /v1/admin/users/{user_id}/status
Authorization: Bearer admin-token
Content-Type: application/json

{
  "is_active": false
}
```

#### Delete User
```http
DELETE /v1/admin/users/{user_id}
Authorization: Bearer admin-token
```

### Order Management

#### Get All Orders
```http
GET /v1/admin/orders?page=1&limit=20&status=pending&date_from=2024-01-01
Authorization: Bearer admin-token
```

#### Update Order Status
```http
PUT /v1/admin/orders/{order_id}/status
Authorization: Bearer admin-token
Content-Type: application/json

{
  "status": "shipped",
  "tracking_number": "1Z999AA1234567890",
  "carrier_name": "UPS",
  "location": "Distribution Center",
  "description": "Package shipped"
}
```

#### Ship Order
```http
PUT /v1/admin/orders/{order_id}/ship
Authorization: Bearer admin-token
Content-Type: application/json

{
  "tracking_number": "1Z999AA1234567890",
  "carrier_name": "UPS"
}
```

### Analytics

#### Get Admin Stats
```http
GET /v1/admin/stats
Authorization: Bearer admin-token
```

#### Get Platform Overview
```http
GET /v1/admin/overview
Authorization: Bearer admin-token
```

#### Export Orders
```http
GET /v1/admin/orders/export?format=csv&status=completed&date_from=2024-01-01
Authorization: Bearer admin-token
```

### System Settings

#### Get System Settings
```http
GET /v1/admin/system/settings
Authorization: Bearer admin-token
```

#### Update System Settings
```http
PUT /v1/admin/system/settings
Authorization: Bearer admin-token
Content-Type: application/json

[
  {
    "key": "maintenance_mode",
    "value": "false",
    "value_type": "boolean"
  },
  {
    "key": "max_cart_items",
    "value": "50",
    "value_type": "integer"
  }
]
```

### Inventory Management

#### Get All Inventory Items
```http
GET /v1/inventory?page=1&limit=20&low_stock=true
Authorization: Bearer admin-token
```

#### Create Inventory Item
```http
POST /v1/inventory
Authorization: Bearer admin-token
Content-Type: application/json

{
  "variant_id": "variant-uuid",
  "location_id": "location-uuid",
  "quantity": 100,
  "low_stock_threshold": 10
}
```

#### Adjust Stock
```http
POST /v1/inventory/adjustments
Authorization: Bearer admin-token
Content-Type: application/json

{
  "variant_id": "variant-uuid",
  "location_id": "location-uuid",
  "quantity_change": -5,
  "reason": "Damaged items removed",
  "notes": "Items damaged during inspection"
}
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
  "timestamp": "2024-01-15T10:30:00Z"
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

#### Python/Requests
```python
import requests

def api_call(url, method='GET', data=None, token=None):
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    
    response = requests.request(method, url, json=data, headers=headers)
    result = response.json()
    
    if not result.get('success'):
        raise Exception(result.get('error', {}).get('message', 'API Error'))
    
    return result.get('data')
```

## Rate Limiting

### Rate Limits
- **General APIs**: 1000 requests per hour per user
- **Auth APIs**: 10 requests per minute per IP
- **Admin APIs**: 5000 requests per hour per admin

### Rate Limit Headers
```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1642248000
```

### Handling Rate Limits
```javascript
function handleRateLimit(response) {
  if (response.status === 429) {
    const resetTime = response.headers.get('X-RateLimit-Reset');
    const waitTime = (resetTime * 1000) - Date.now();
    
    console.log(`Rate limited. Retry after ${waitTime}ms`);
    
    setTimeout(() => {
      // Retry the request
    }, waitTime);
  }
}
```

## Examples

### Complete Order Flow
```javascript
// 1. Add items to cart
await fetch('/v1/cart/items', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({
    variant_id: 'variant-uuid',
    quantity: 2
  })
});

// 2. Create payment intent
const paymentIntent = await fetch('/v1/payments/create-payment-intent', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({
    order_id: 'order-uuid',
    subtotal: 99.99,
    currency: 'USD'
  })
});

// 3. Checkout
const order = await fetch('/v1/orders/checkout', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({
    shipping_address_id: 'address-uuid',
    shipping_method_id: 'method-uuid',
    payment_method_id: 'payment-uuid'
  })
});

// 4. Confirm payment
await fetch('/v1/payments/confirm', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({
    payment_intent_id: paymentIntent.data.id,
    handle_3d_secure: true
  })
});
```

### Subscription Management
```python
import requests

# Create subscription
subscription = requests.post('/v1/subscriptions', 
  headers={'Authorization': f'Bearer {token}'},
  json={
    'plan_id': 'monthly-plan',
    'status': 'active',
    'price': 29.99,
    'auto_renew': True
  }
)

# Update subscription
requests.put(f'/v1/subscriptions/{subscription_id}',
  headers={'Authorization': f'Bearer {token}'},
  json={'auto_renew': False}
)

# Cancel subscription
requests.delete(f'/v1/subscriptions/{subscription_id}',
  headers={'Authorization': f'Bearer {token}'}
)
```

### Admin Operations
```bash
# Get all users with curl
curl -X GET "http://localhost:8000/v1/admin/users?page=1&limit=20" \
  -H "Authorization: Bearer admin-token" \
  -H "Content-Type: application/json"

# Update order status
curl -X PUT "http://localhost:8000/v1/admin/orders/order-uuid/status" \
  -H "Authorization: Bearer admin-token" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "shipped",
    "tracking_number": "1Z999AA1234567890",
    "carrier_name": "UPS"
  }'

# Export orders
curl -X GET "http://localhost:8000/v1/admin/orders/export?format=csv" \
  -H "Authorization: Bearer admin-token" \
  --output orders_export.csv
```

## Testing APIs

### Using curl
```bash
# Test authentication
curl -X POST "http://localhost:8000/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "password"}'

# Test with authentication
curl -X GET "http://localhost:8000/v1/users/me" \
  -H "Authorization: Bearer your-token"
```

### Using Postman
1. Import the API collection (if available)
2. Set up environment variables for base URL and tokens
3. Use the collection runner for automated testing

### Using Python
```python
import requests

# Base configuration
BASE_URL = "http://localhost:8000/v1"
token = "your-jwt-token"

# Test user profile
response = requests.get(f"{BASE_URL}/users/me", 
  headers={"Authorization": f"Bearer {token}"}
)
print(response.json())
```

This guide covers the main API endpoints and usage patterns. For detailed schema information, refer to the OpenAPI documentation at `/docs` when the server is running.
---

# Endpoint Reference

# API Documentation

This document provides a detailed overview of the Banwee E-commerce Platform API endpoints.

# API Documentation

This document provides a detailed overview of the Banwee E-commerce Platform API endpoints.

## Authentication

The API uses JWT for authentication. Include the token in the `Authorization` header as a Bearer token.

`Authorization: Bearer <your_jwt_token>`

## Image Upload & CDN Delivery

The platform uses GitHub as an image storage backend with jsDelivr CDN for fast global delivery.

### How It Works

1. **Upload**: Product images are uploaded to a GitHub repository via the GitHub API
2. **Storage**: Images are organized in category folders (e.g., `food/product.jpg`)
3. **Delivery**: Images are served via jsDelivr CDN for optimal performance
4. **URL Format**: `https://cdn.jsdelivr.net/gh/{owner}/{repo}@{branch}/{path}`

### Image Upload Flow

When creating or updating products:

1. Admin selects images in the product form
2. Frontend uploads images to GitHub using `uploadSingleFile()` or `uploadMultipleFiles()`
3. GitHub API returns the file path
4. Frontend generates jsDelivr CDN URL
5. CDN URL is sent to backend and stored in database
6. Images are loaded from CDN when displaying products

### Security

- GitHub Personal Access Token is encrypted using AES encryption
- Token should be stored in environment variables in production
- Only authenticated admin/supplier users can upload images

### Configuration

See `frontend/src/lib/github.tsx` for GitHub integration configuration:
- Repository owner, name, and branch
- Encrypted token (should be moved to environment variables)
- Upload and delete functions

### Authentication Endpoints

- **POST /v1/auth/register**
  - **Description**: Register a new user.
  - **Request Body**:
    ```json
    {
      "email": "user@example.com",
      "password": "password",
      "firstname": "Test",
      "lastname": "User"
    }
    ```
  - **Response Body**:
    ```json
    {
      "success": true,
      "data": {
        "id": "...",
        "email": "user@example.com",
        "firstname": "Test",
        "lastname": "User"
      },
      "message": "User registered successfully"
    }
    ```

- **POST /v1/auth/login**
  - **Description**: Login user and return access token.
  - **Request Body**:
    ```json
    {
      "email": "user@example.com",
      "password": "password"
    }
    ```
  - **Response Body**:
    ```json
    {
      "success": true,
      "data": {
        "access_token": "...",
        "token_type": "bearer"
      },
      "message": "Login successful"
    }
    ```

- **POST /v1/auth/logout**
  - **Description**: Logout user.
  - **Response Body**:
    ```json
    {
      "success": true,
      "message": "Logged out successfully"
    }
    ```

- **GET /v1/auth/profile**
  - **Description**: Get current user profile.
  - **Response Body**:
    ```json
    {
      "success": true,
      "data": {
        "id": "...",
        "email": "...",
        "firstname": "...",
        "lastname": "..."
      }
    }
    ```

- **PUT /v1/auth/profile**
  - **Description**: Update user profile.
  - **Request Body**:
    ```json
    {
      "firstname": "New",
      "lastname": "Name"
    }
    ```
  - **Response Body**:
    ```json
    {
      "success": true,
      "data": {
        "id": "...",
        "email": "...",
        "firstname": "New",
        "lastname": "Name"
      },
      "message": "Profile updated successfully"
    }
    ```

- **PUT /v1/auth/change-password**
  - **Description**: Change user password.
  - **Request Body**:
    ```json
    {
      "current_password": "...",
      "new_password": "..."
    }
    ```
  - **Response Body**:
    ```json
    {
      "success": true,
      "message": "Password changed successfully"
    }
    ```

- **POST /v1/auth/forgot-password**
  - **Description**: Send password reset email.
  - **Request Body**:
    ```json
    {
      "email": "user@example.com"
    }
    ```
  - **Response Body**:
    ```json
    {
      "success": true,
      "message": "If the email exists, a reset link has been sent"
    }
    ```

- **POST /v1/auth/reset-password**
  - **Description**: Reset password with token.
  - **Request Body**:
    ```json
    {
      "token": "...",
      "new_password": "..."
    }
    ```
  - **Response Body**:
    ```json
    {
      "success": true,
      "message": "Password reset successfully"
    }
    ```

- **GET /v1/auth/verify-email**
  - **Description**: Verify user email with token.
  - **Query Parameters**:
    - `token` (required, string): The verification token sent to the user's email.
  - **Response Body**:
    ```json
    {
      "success": true,
      "message": "Email verified successfully"
    }
    ```

- **POST /v1/auth/refresh**
  - **Description**: Refresh access token using refresh token.
  - **Request Body**:
    ```json
    {
      "refresh_token": "..."
    }
    ```
  - **Response Body**:
    ```json
    {
      "success": true,
      "data": {
        "access_token": "...",
        "token_type": "bearer"
      },
      "message": "Token refreshed successfully"
    }
    ```

- **GET /v1/auth/addresses**
  - **Description**: Get all addresses for the current user.
  - **Response Body**:
    ```json
    {
      "success": true,
      "data": [
        {
          "id": "...",
          "street": "...",
          "city": "...",
          "state": "...",
          "country": "...",
          "post_code": "..."
        }
      ]
    }
    ```

- **POST /v1/auth/addresses**
  - **Description**: Create a new address for the current user.
  - **Request Body**:
    ```json
    {
      "street": "...",
      "city": "...",
      "state": "...",
      "country": "...",
      "post_code": "..."
    }
    ```
  - **Response Body**:
    ```json
    {
      "success": true,
      "data": {
        "id": "...",
        "street": "...",
        "city": "...",
        "state": "...",
        "country": "...",
        "post_code": "..."
      },
      "message": "Address created successfully"
    }
    ```

- **PUT /v1/auth/addresses/{address_id}**
  - **Description**: Update an existing address for the current user.
  - **Request Body**:
    ```json
    {
      "street": "...",
      "city": "..."
    }
    ```
  - **Response Body**:
    ```json
    {
      "success": true,
      "data": {
        "id": "...",
        "street": "...",
        "city": "..."
      },
      "message": "Address updated successfully"
    }
    ```

- **DELETE /v1/auth/addresses/{address_id}**
  - **Description**: Delete an address for the current user.
  - **Response Body**:
    ```json
    {
      "success": true,
      "message": "Address deleted successfully"
    }
    ```

---

## Endpoints

### Admin

- **GET /v1/admin/stats**
  - **Description**: Get admin dashboard statistics, such as total revenue, total orders, total users, and total products.
  - **Response Body**:
    ```json
    {
      "success": true,
      "data": {
        "total_revenue": 1000.00,
        "total_orders": 100,
        "total_users": 50,
        "total_products": 200
      }
    }
    ```

- **GET /v1/admin/overview**
  - **Description**: Get a platform overview, including recent orders, new users, and top products.
  - **Response Body**:
    ```json
    {
      "success": true,
      "data": {
        "recent_orders": [
          {
            "id": "...",
            "status": "...",
            "total_amount": "..."
          }
        ],
        "new_users": [
          {
            "id": "...",
            "firstname": "...",
            "lastname": "..."
          }
        ],
        "top_products": [
          {
            "id": "...",
            "name": "...",
            "total_sales": "..."
          }
        ]
      }
    }
    ```

- **GET /v1/admin/orders**
  - **Description**: Get all orders (admin only).
  - **Query Parameters**:
    - `page` (optional, integer): The page number to retrieve.
    - `limit` (optional, integer): The number of items to retrieve per page.
    - `status` (optional, string): Filter by order status.
    - `q` (optional, string): Search query.
    - `date_from` (optional, string): Filter by creation date (from).
    - `date_to` (optional, string): Filter by creation date (to).
    - `min_price` (optional, float): Filter by minimum price.
    - `max_price` (optional, float): Filter by maximum price.
  - **Response Body**:
    ```json
    {
      "success": true,
      "data": {
        "data": [
          {
            "id": "...",
            "status": "...",
            "total_amount": "..."
          }
        ],
        "total": 100,
        "page": 1,
        "per_page": 10,
        "total_pages": 10
      }
    }
    ```

- **GET /v1/admin/users**
  - **Description**: Get all users (admin only).
  - **Query Parameters**:
    - `page` (optional, integer): The page number to retrieve.
    - `limit` (optional, integer): The number of items to retrieve per page.
    - `role_filter` (optional, string): Filter by user role.
    - `search` (optional, string): Search query.
    - `status` (optional, string): Filter by user status.
    - `verified` (optional, boolean): Filter by verified status.
  - **Response Body**:
    ```json
    {
      "success": true,
      "data": {
        "data": [
          {
            "id": "...",
            "firstname": "...",
            "lastname": "...",
            "email": "..."
          }
        ],
        "total": 50,
        "page": 1,
        "per_page": 10,
        "total_pages": 5
      }
    }
    ```

- **POST /v1/admin/users**
  - **Description**: Create a new user (admin only).
  - **Request Body**:
    ```json
    {
      "email": "user@example.com",
      "password": "password",
      "firstname": "Test",
      "lastname": "User"
    }
    ```
  - **Response Body**:
    ```json
    {
      "success": true,
      "data": {
        "id": "...",
        "email": "user@example.com",
        "firstname": "Test",
        "lastname": "User"
      },
      "message": "User created successfully"
    }
    ```

- **GET /v1/admin/users/{user_id}**
  - **Description**: Get a single user by ID (admin only).
  - **Response Body**:
    ```json
    {
      "success": true,
      "data": {
        "id": "...",
        "email": "user@example.com",
        "firstname": "Test",
        "lastname": "User"
      }
    }
    ```

- **GET /v1/admin/products**
  - **Description**: Get all products (admin only).
  - **Query Parameters**:
    - `page` (optional, integer): The page number to retrieve.
    - `limit` (optional, integer): The number of items to retrieve per page.
    - `search` (optional, string): Search query.
    - `category` (optional, string): Filter by category.
    - `status` (optional, string): Filter by product status.
    - `supplier` (optional, string): Filter by supplier.
  - **Response Body**:
    ```json
    {
      "success": true,
      "data": {
        "data": [
          {
            "id": "...",
            "name": "...",
            "price": "..."
          }
        ],
        "total": 200,
        "page": 1,
        "per_page": 10,
        "total_pages": 20
      }
    }
    ```

- **GET /v1/admin/variants**
  - **Description**: Get all variants (admin only).
  - **Query Parameters**:
    - `page` (optional, integer): The page number to retrieve.
    - `limit` (optional, integer): The number of items to retrieve per page.
    - `search` (optional, string): Search query.
    - `product_id` (optional, string): Filter by product ID.
  - **Response Body**:
    ```json
    {
      "success": true,
      "data": {
        "data": [
          {
            "id": "...",
            "name": "...",
            "price": "..."
          }
        ],
        "total": 50,
        "page": 1,
        "per_page": 10,
        "total_pages": 5
      }
    }
    ```

- **PUT /v1/admin/users/{user_id}/status**
  - **Description**: Update user status (admin only).
  - **Request Body**:
    ```json
    {
      "is_active": true
    }
    ```
  - **Response Body**:
    ```json
    {
      "success": true,
      "data": {
        "id": "...",
        "is_active": true
      },
      "message": "User status updated"
    }
    ```

- **DELETE /v1/admin/users/{user_id}**
  - **Description**: Delete user (admin only).
  - **Response Body**:
    ```json
    {
      "success": true,
      "message": "User deleted successfully"
    }
    ```

- **GET /v1/admin/orders/{order_id}**
  - **Description**: Get a single order by ID (admin only).
  - **Response Body**:
    ```json
    {
      "success": true,
      "data": {
        "id": "...",
        "status": "...",
        "total_amount": "..."
      }
    }
    ```

- **PUT /v1/admin/orders/{order_id}/ship**
  - **Description**: Update an order with shipping information (admin only).
  - **Request Body**:
    ```json
    {
      "tracking_number": "...",
      "carrier_name": "..."
    }
    ```
  - **Response Body**:
    ```json
    {
      "success": true,
      "data": {
        "id": "...",
        "status": "shipped"
      },
      "message": "Order status updated to shipped."
    }
    ```

- **PUT /v1/admin/orders/{order_id}/status**
  - **Description**: Update order status (admin only).
  - **Request Body**:
    ```json
    {
      "status": "confirmed"
    }
    ```
  - **Response Body**:
    ```json
    {
      "success": true,
      "data": {
        "id": "...",
        "status": "confirmed"
      },
      "message": "Order status updated to confirmed"
    }
    ```

- **GET /v1/admin/system/settings**
  - **Description**: Get system settings (admin only).
  - **Response Body**:
    ```json
    {
      "success": true,
      "data": {
        "maintenance_mode": false,
        "registration_enabled": true
      }
    }
    ```

- **PUT /v1/admin/system/settings**
  - **Description**: Update system settings (admin only).
  - **Request Body**:
    ```json
    {
      "maintenance_mode": true,
      "registration_enabled": false
    }
    ```
  - **Response Body**:
    ```json
    {
      "success": true,
      "data": {
        "maintenance_mode": true,
        "registration_enabled": false
      },
      "message": "System settings updated successfully"
    }
    ```

### Analytics

- **GET /v1/analytics/dashboard**
  - **Description**: Get dashboard analytics data.
  - **Query Parameters**:
    - `date_range` (optional, string): The date range for the data. Can be `7d`, `30d`, or `90d`. Defaults to `30d`.
  - **Response Body**:
    ```json
    {
      "success": true,
      "data": {
        "total_sales": "...",
        "total_orders": "...",
        "new_customers": "...",
        "top_products": [
          {
            "name": "...",
            "total_sales": "..."
          }
        ]
      }
    }
    ```

- **GET /v1/analytics/sales-trend**
  - **Description**: Get sales trend data.
  - **Query Parameters**:
    - `days` (optional, integer): The number of days to get the sales trend for. Defaults to `30`.
  - **Response Body**:
    ```json
    {
      "success": true,
      "data": [
        {
          "date": "...",
          "total_sales": "..."
        }
      ]
    }
    ```

- **GET /v1/analytics/top-products**
  - **Description**: Get top performing products.
  - **Query Parameters**:
    - `limit` (optional, integer): The number of products to retrieve. Defaults to `10`.
  - **Response Body**:
    ```json
    {
      "success": true,
      "data": [
        {
          "name": "...",
          "total_sales": "..."
        }
      ]
    }
    ```

### Authentication

- **POST /v1/auth/register**: Register a new user.
- **POST /v1/auth/login**: Login user and return access token.
- **POST /v1/auth/logout**: Logout user.
- **GET /v1/auth/profile**: Get current user profile.
- **GET /v1/auth/addresses**: Get all addresses for the current user.
- **POST /v1/auth/addresses**: Create a new address for the current user.
- **PUT /v1/auth/addresses/{address_id}**: Update an existing address for the current user.
- **DELETE /v1/auth/addresses/{address_id}**: Delete an address for the current user.
- **GET /v1/auth/verify-email**: Verify user email with token.
- **POST /v1/auth/forgot-password**: Send password reset email.
- **POST /v1/auth/reset-password**: Reset password with token.
- **PUT /v1/auth/profile**: Update user profile.
- **PUT /v1/auth/change-password**: Change user password.
- **POST /v1/auth/refresh**: Refresh access token using refresh token.

### Cart

- **GET /v1/cart/**
  - **Description**: Get the current user's cart.
  - **Response Body**:
    ```json
    {
      "success": true,
      "data": {
        "id": "...",
        "items": [
          {
            "id": "...",
            "variant_id": "...",
            "quantity": 1,
            "product": {
              "id": "...",
              "name": "...",
              "price": "..."
            }
          }
        ],
        "subtotal": "...",
        "tax": "...",
        "shipping": "...",
        "total": "..."
      }
    }
    ```

- **POST /v1/cart/add**
  - **Description**: Add an item to the cart.
  - **Request Body**:
    ```json
    {
      "variant_id": "...",
      "quantity": 1
    }
    ```
  - **Response Body**:
    ```json
    {
      "success": true,
      "data": {
        "id": "...",
        "items": [
          {
            "id": "...",
            "variant_id": "...",
            "quantity": 1,
            "product": {
              "id": "...",
              "name": "...",
              "price": "..."
            }
          }
        ]
      },
      "message": "Item added to cart"
    }
    ```

- **PUT /v1/cart/update/{item_id}**
  - **Description**: Update the quantity of a cart item.
  - **Request Body**:
    ```json
    {
      "quantity": 2
    }
    ```
  - **Response Body**:
    ```json
    {
      "success": true,
      "data": {
        "id": "...",
        "items": [
          {
            "id": "...",
            "variant_id": "...",
            "quantity": 2,
            "product": {
              "id": "...",
              "name": "...",
              "price": "..."
            }
          }
        ]
      },
      "message": "Cart item quantity updated"
    }
    ```

- **DELETE /v1/cart/remove/{item_id}**
  - **Description**: Remove an item from the cart.
  - **Response Body**:
    ```json
    {
      "success": true,
      "data": {
        "id": "...",
        "items": []
      },
      "message": "Item removed from cart"
    }
    ```

- **POST /v1/cart/promocode**
  - **Description**: Apply a promocode to the cart.
  - **Request Body**:
    ```json
    {
      "code": "..."
    }
    ```
  - **Response Body**:
    ```json
    {
      "success": true,
      "data": {
        "id": "...",
        "discount_amount": "..."
      }
    }
    ```

- **DELETE /v1/cart/promocode**
  - **Description**: Remove a promocode from the cart.
  - **Response Body**:
    ```json
    {
      "success": true,
      "data": {
        "id": "...",
        "discount_amount": 0
      }
    }
    ```

- **GET /v1/cart/count**
  - **Description**: Get the number of items in the cart.
  - **Response Body**:
    ```json
    {
      "success": true,
      "data": 5
    }
    ```

- **POST /v1/cart/validate**
  - **Description**: Validate the cart.
  - **Response Body**:
    ```json
    {
      "success": true,
      "data": {
        "is_valid": true
      }
    }
    ```

- **POST /v1/cart/shipping-options**
  - **Description**: Get shipping options for the cart.
  - **Request Body**:
    ```json
    {
      "address": {
        "street": "...",
        "city": "...",
        "state": "...",
        "country": "...",
        "post_code": "..."
      }
    }
    ```
  - **Response Body**:
    ```json
    {
      "success": true,
      "data": [
        {
          "id": "...",
          "name": "...",
          "price": "..."
        }
      ]
    }
    ```

- **POST /v1/cart/calculate**
  - **Description**: Calculate the totals for the cart.
  - **Request Body**:
    ```json
    {
      "shipping_method_id": "..."
    }
    ```
  - **Response Body**:
    ```json
    {
      "success": true,
      "data": {
        "subtotal": "...",
        "tax": "...",
        "shipping": "...",
        "total": "..."
      }
    }
    ```

- **POST /v1/cart/items/{item_id}/save-for-later**
  - **Description**: Save an item for later.
  - **Response Body**:
    ```json
    {
      "success": true,
      "data": {
        "id": "...",
        "saved_for_later": true
      }
    }
    ```

- **POST /v1/cart/items/{item_id}/move-to-cart**
  - **Description**: Move a saved item to the cart.
  - **Response Body**:
    ```json
    {
      "success": true,
      "data": {
        "id": "...",
        "saved_for_later": false
      }
    }
    ```

- **GET /v1/cart/saved-items**
  - **Description**: Get all saved items.
  - **Response Body**:
    ```json
    {
      "success": true,
      "data": [
        {
          "id": "...",
          "variant_id": "...",
          "quantity": 1,
          "product": {
            "id": "...",
            "name": "...",
            "price": "..."
          }
        }
      ]
    }
    ```

- **POST /v1/cart/clear**
  - **Description**: Clear the cart.
  - **Response Body**:
    ```json
    {
      "success": true,
      "data": {
        "id": "...",
        "items": []
      },
      "message": "Cart cleared successfully"
    }
    ```

- **DELETE /v1/cart/clear**
  - **Description**: Clear the cart.
  - **Response Body**:
    ```json
    {
      "success": true,
      "data": {
        "id": "...",
        "items": []
      },
      "message": "Cart cleared successfully"
    }
    ```

- **POST /v1/cart/merge**
  - **Description**: Merge the cart with a list of items.
  - **Request Body**:
    ```json
    {
      "items": [
        {
          "variant_id": "...",
          "quantity": 1
        }
      ]
    }
    ```
  - **Response Body**:
    ```json
    {
      "success": true,
      "data": {
        "id": "...",
        "items": [
          {
            "id": "...",
            "variant_id": "...",
            "quantity": 1,
            "product": {
              "id": "...",
              "name": "...",
              "price": "..."
            }
          }
        ]
      }
    }
    ```

- **GET /v1/cart/checkout-summary**
  - **Description**: Get a summary of the cart for checkout.
  - **Response Body**:
    ```json
    {
      "success": true,
      "data": {
        "cart": {
          "id": "...",
          "items": [
            {
              "id": "...",
              "variant_id": "...",
              "quantity": 1,
              "product": {
                "id": "...",
                "name": "...",
                "price": "..."
              }
            }
          ],
          "subtotal": "...",
          "tax": "...",
          "shipping": "...",
          "total": "..."
        },
        "available_payment_methods": [
          {
            "id": "...",
            "type": "...",
            "last_four": "..."
          }
        ],
        "available_shipping_methods": [
          {
            "id": "...",
            "name": "...",
            "price": "..."
          }
        ],
        "tax_info": {
          "rate": "..."
        }
      }
    }
    ```

### Health

- **GET /health/live**
  - **Description**: Liveness check. Returns a 200 OK response if the service is running.
  - **Response Body**:
    ```json
    {
      "status": "alive",
      "timestamp": "..."
    }
    ```

- **GET /health/ready**
  - **Description**: Readiness check. Returns a 200 OK response if the service is ready to handle traffic. Checks critical dependencies like database connectivity.
  - **Response Body**:
    ```json
    {
      "status": "healthy",
      "timestamp": "...",
      "checks": [
        {
          "name": "database",
          "status": "healthy",
          "response_time": "..."
        }
      ]
    }
    ```

- **GET /health/detailed**
  - **Description**: Comprehensive health check with detailed component status.
  - **Response Body**:
    ```json
    {
      "status": "healthy",
      "timestamp": "...",
      "checks": [
        {
          "name": "database",
          "status": "healthy",
          "response_time": "..."
        },
        {
          "name": "system_resources",
          "status": "healthy",
          "details": {
            "cpu_percent": "...",
            "memory_percent": "..."
          }
        }
      ]
    }
    ```

- **GET /health/dependencies**
  - **Description**: Dependencies health check.
  - **Response Body**:
    ```json
    {
      "status": "healthy",
      "timestamp": "...",
      "checks": [
        {
          "name": "stripe",
          "status": "healthy",
          "response_time": "..."
        }
      ]
    }
    ```

- **GET /health/api-endpoints**
  - **Description**: API endpoints health check.
  - **Response Body**:
    ```json
    {
      "status": "healthy",
      "timestamp": "...",
      "checks": [
        {
          "name": "endpoint_/v1/products",
          "status": "healthy",
          "response_time": "..."
        }
      ]
    }
    ```

- **GET /health/metrics**
  - **Description**: Performance metrics.
  - **Response Body**:
    ```json
    {
      "timestamp": "...",
      "metrics": {
        "database": {
          "connection_pool_size": "...",
          "active_connections": "..."
        },
        "system": {
          "cpu_usage": "...",
          "memory_usage": "..."
        }
      }
    }
    ```

### Orders

- **POST /v1/orders/**
  - **Description**: Create a new order.
  - **Request Body**:
    ```json
    {
      "items": [
        {
          "variant_id": "...",
          "quantity": 1
        }
      ],
      "shipping_address_id": "...",
      "shipping_method_id": "...",
      "payment_method_id": "..."
    }
    ```
  - **Response Body**:
    ```json
    {
      "success": true,
      "data": {
        "id": "...",
        "status": "pending",
        "total_amount": "..."
      },
      "message": "Order created successfully"
    }
    ```

- **POST /v1/orders/checkout**
  - **Description**: Place an order from the current cart.
  - **Request Body**:
    ```json
    {
      "shipping_address_id": "...",
      "shipping_method_id": "...",
      "payment_method_id": "..."
    }
    ```
  - **Response Body**:
    ```json
    {
      "success": true,
      "data": {
        "id": "...",
        "status": "pending",
        "total_amount": "..."
      },
      "message": "Order placed successfully"
    }
    ```

- **GET /v1/orders/**
  - **Description**: Get user's orders.
  - **Query Parameters**:
    - `page` (optional, integer): The page number to retrieve.
    - `limit` (optional, integer): The number of items to retrieve per page.
    - `status` (optional, string): Filter by order status.
  - **Response Body**:
    ```json
    {
      "success": true,
      "data": {
        "orders": [
          {
            "id": "...",
            "status": "...",
            "total_amount": "..."
          }
        ],
        "total": 1,
        "page": 1,
        "per_page": 10,
        "total_pages": 1
      }
    }
    ```

- **GET /v1/orders/{order_id}**
  - **Description**: Get a specific order.
  - **Response Body**:
    ```json
    {
      "success": true,
      "data": {
        "id": "...",
        "status": "...",
        "total_amount": "..."
      }
    }
    ```

- **PUT /v1/orders/{order_id}/cancel**
  - **Description**: Cancel an order.
  - **Response Body**:
    ```json
    {
      "success": true,
      "data": {
        "id": "...",
        "status": "cancelled"
      },
      "message": "Order cancelled successfully"
    }
    ```

- **GET /v1/orders/{order_id}/tracking**
  - **Description**: Get order tracking information.
  - **Response Body**:
    ```json
    {
      "success": true,
      "data": {
        "tracking_number": "...",
        "carrier_name": "...",
        "tracking_events": [
          {
            "status": "...",
            "location": "...",
            "timestamp": "..."
          }
        ]
      }
    }
    ```

- **POST /v1/orders/{order_id}/refund**
  - **Description**: Request order refund.
  - **Request Body**:
    ```json
    {
      "reason": "..."
    }
    ```
  - **Response Body**:
    ```json
    {
      "success": true,
      "data": {
        "refund_request_id": "..."
      },
      "message": "Refund request submitted"
    }
    ```

- **POST /v1/orders/{order_id}/reorder**
  - **Description**: Create new order from existing order.
  - **Response Body**:
    ```json
    {
      "success": true,
      "data": {
        "id": "...",
        "status": "pending",
        "total_amount": "..."
      },
      "message": "Order recreated successfully"
    }
    ```

- **GET /v1/orders/{order_id}/invoice**
  - **Description**: Get order invoice.
  - **Response Body**:
    ```json
    {
      "success": true,
      "data": {
        "invoice_url": "..."
      }
    }
    ```

- **POST /v1/orders/{order_id}/notes**
  - **Description**: Add note to order.
  - **Request Body**:
    ```json
    {
      "note": "..."
    }
    ```
  - **Response Body**:
    ```json
    {
      "success": true,
      "data": {
        "id": "...",
        "note": "..."
      },
      "message": "Note added successfully"
    }
    ```

- **GET /v1/orders/{order_id}/notes**
  - **Description**: Get order notes.
  - **Response Body**:
    ```json
    {
      "success": true,
      "data": [
        {
          "id": "...",
          "note": "..."
        }
      ]
    }
    ```

### Payments

- **GET /v1/users/me/payment-methods**
  - **Description**: Get all payment methods for the current user.
  - **Response Body**:
    ```json
    {
      "success": true,
      "data": [
        {
          "id": "...",
          "type": "credit_card",
          "last_four": "4242"
        }
      ]
    }
    ```

- **GET /v1/users/{user_id}/payment-methods**
  - **Description**: Get all payment methods for a user.
  - **Response Body**:
    ```json
    {
      "success": true,
      "data": [
        {
          "id": "...",
          "type": "credit_card",
          "last_four": "4242"
        }
      ]
    }
    ```

- **POST /v1/users/{user_id}/payment-methods**
  - **Description**: Add a new payment method for a user.
  - **Request Body**:
    ```json
    {
      "type": "credit_card",
      "provider": "stripe",
      "last_four": "4242",
      "expiry_month": 12,
      "expiry_year": 2025
    }
    ```
  - **Response Body**:
    ```json
    {
      "success": true,
      "data": {
        "id": "...",
        "type": "credit_card",
        "last_four": "4242"
      }
    }
    ```

- **PUT /v1/users/{user_id}/payment-methods/{method_id}**
  - **Description**: Update a payment method.
  - **Request Body**:
    ```json
    {
      "expiry_month": 1,
      "expiry_year": 2026
    }
    ```
  - **Response Body**:
    ```json
    {
      "success": true,
      "data": {
        "id": "...",
        "expiry_month": 1,
        "expiry_year": 2026
      }
    }
    ```

- **DELETE /v1/users/{user_id}/payment-methods/{method_id}**
  - **Description**: Delete a payment method.
  - **Response Body**:
    ```json
    {
      "success": true,
      "message": "Payment method deleted successfully"
    }
    ```

- **PUT /v1/users/{user_id}/payment-methods/{method_id}/default**
  - **Description**: Set a payment method as default.
  - **Response Body**:
    ```json
    {
      "success": true,
      "data": {
        "id": "...",
        "is_default": true
      }
    }
    ```

- **POST /v1/payments/create-payment-intent**
  - **Description**: Create a Stripe Payment Intent.
  - **Request Body**:
    ```json
    {
      "order_id": "...",
      "amount": 100.00,
      "currency": "usd"
    }
    ```
  - **Response Body**:
    ```json
    {
      "client_secret": "..."
    }
    ```

- **POST /v1/payments/process**
  - **Description**: Process a payment.
  - **Request Body**:
    ```json
    {
      "amount": 100.00,
      "payment_method_id": "...",
      "order_id": "..."
    }
    ```
  - **Response Body**:
    ```json
    {
      "success": true,
      "data": {
        "status": "succeeded"
      },
      "message": "Payment processed successfully"
    }
    ```

- **POST /v1/payments/stripe-webhook**
  - **Description**: Handle Stripe webhook events.
  - **Response Body**:
    ```json
    {
      "status": "success"
    }
    ```

### Products

- **GET /v1/products/home**
  - **Description**: Get all data needed for the home page in one request.
  - **Response Body**:
    ```json
    {
      "success": true,
      "data": {
        "categories": [
          {
            "id": "...",
            "name": "..."
          }
        ],
        "featured": [
          {
            "id": "...",
            "name": "...",
            "price": "..."
          }
        ],
        "popular": [
          {
            "id": "...",
            "name": "...",
            "price": "..."
          }
        ],
        "deals": [
          {
            "id": "...",
            "name": "...",
            "price": "..."
          }
        ]
      }
    }
    ```

- **GET /v1/products/**
  - **Description**: Get products with optional filtering and pagination.
  - **Query Parameters**:
    - `page` (optional, integer): The page number to retrieve.
    - `limit` (optional, integer): The number of items to retrieve per page.
    - `category` (optional, string): Filter by category.
    - `q` (optional, string): Search query.
    - `min_price` (optional, float): Filter by minimum price.
    - `max_price` (optional, float): Filter by maximum price.
    - `min_rating` (optional, integer): Filter by minimum rating.
    - `max_rating` (optional, integer): Filter by maximum rating.
    - `sort_by` (optional, string): Sort by `created_at`, `price`, or `rating`.
    - `sort_order` (optional, string): Sort order (`asc` or `desc`).
    - `availability` (optional, boolean): Filter by availability.
    - `featured` (optional, boolean): Filter by featured products.
    - `popular` (optional, boolean): Filter by popular products.
    - `sale` (optional, boolean): Filter by products on sale.
  - **Response Body**:
    ```json
    {
      "success": true,
      "data": {
        "data": [
          {
            "id": "...",
            "name": "...",
            "price": "..."
          }
        ],
        "total": 1,
        "page": 1,
        "per_page": 10,
        "total_pages": 1
      }
    }
    ```

- **GET /v1/products/categories**
  - **Description**: Get all product categories.
  - **Response Body**:
    ```json
    {
      "success": true,
      "data": [
        {
          "id": "...",
          "name": "..."
        }
      ]
    }
    ```

- **GET /v1/products/{product_id}/recommendations**
  - **Description**: Get recommended products based on a product.
  - **Query Parameters**:
    - `limit` (optional, integer): The number of recommendations to retrieve.
  - **Response Body**:
    ```json
    {
      "success": true,
      "data": [
        {
          "id": "...",
          "name": "...",
          "price": "..."
        }
      ]
    }
    ```

- **GET /v1/products/{product_id}/variants**
  - **Description**: Get all variants for a product.
  - **Response Body**:
    ```json
    {
      "success": true,
      "data": [
        {
          "id": "...",
          "name": "...",
          "price": "..."
        }
      ]
    }
    ```

- **GET /v1/products/variants/{variant_id}**
  - **Description**: Get a specific product variant by ID.
  - **Response Body**:
    ```json
    {
      "success": true,
      "data": {
        "id": "...",
        "name": "...",
        "price": "..."
      }
    }
    ```

- **GET /v1/products/variants/{variant_id}/qrcode**
  - **Description**: Get QR code for a product variant.
  - **Response Body**:
    ```json
    {
      "success": true,
      "data": {
        "qr_code_url": "..."
      }
    }
    ```

- **GET /v1/products/variants/{variant_id}/barcode**
  - **Description**: Get barcode for a product variant.
  - **Response Body**:
    ```json
    {
      "success": true,
      "data": {
        "barcode_url": "..."
      }
    }
    ```

- **GET /v1/products/{product_id}**
  - **Description**: Get a specific product by ID.
  - **Response Body**:
    ```json
    {
      "success": true,
      "data": {
        "id": "...",
        "name": "...",
        "price": "..."
      }
    }
    ```

- **GET /v1/products/categories/{category_id}**
  - **Description**: Get a specific category by ID.
  - **Response Body**:
    ```json
    {
      "success": true,
      "data": {
        "id": "...",
        "name": "..."
      }
    }
    ```

- **POST /v1/products/**
  - **Description**: Create a new product (suppliers only).
  - **Request Body**:
    ```json
    {
      "name": "...",
      "description": "...",
      "category_id": "...",
      "variants": [
        {
          "name": "...",
          "price": "...",
          "stock": "..."
        }
      ]
    }
    ```
  - **Response Body**:
    ```json
    {
      "success": true,
      "data": {
        "id": "...",
        "name": "...",
        "price": "..."
      },
      "message": "Product created successfully"
    }
    ```

- **PUT /v1/products/{product_id}**
  - **Description**: Update a product (suppliers only).
  - **Request Body**:
    ```json
    {
      "name": "..."
    }
    ```
  - **Response Body**:
    ```json
    {
      "success": true,
      "data": {
        "id": "...",
        "name": "..."
      },
      "message": "Product updated successfully"
    }
    ```

- **DELETE /v1/products/{product_id}**
  - **Description**: Delete a product (suppliers only).
  - **Response Body**:
    ```json
    {
      "success": true,
      "message": "Product deleted successfully"
    }
    ```

### Reviews

- **POST /v1/reviews/**
  - **Description**: Create a new review for a product.
  - **Request Body**:
    ```json
    {
      "product_id": "...",
      "rating": 5,
      "comment": "This is a great product!"
    }
    ```
  - **Response Body**:
    ```json
    {
      "success": true,
      "data": {
        "id": "...",
        "product_id": "...",
        "rating": 5,
        "comment": "This is a great product!"
      },
      "message": "Review created successfully"
    }
    ```

- **GET /v1/reviews/{review_id}**
  - **Description**: Get a specific review by ID.
  - **Response Body**:
    ```json
    {
      "success": true,
      "data": {
        "id": "...",
        "product_id": "...",
        "rating": 5,
        "comment": "This is a great product!"
      }
    }
    ```

- **GET /v1/reviews/product/{product_id}**
  - **Description**: Get all reviews for a specific product.
  - **Query Parameters**:
    - `page` (optional, integer): The page number to retrieve.
    - `limit` (optional, integer): The number of items to retrieve per page.
    - `min_rating` (optional, integer): Filter by minimum rating.
    - `max_rating` (optional, integer): Filter by maximum rating.
    - `sort_by` (optional, string): Sort by `created_at` or `rating`.
  - **Response Body**:
    ```json
    {
      "success": true,
      "data": {
        "data": [
          {
            "id": "...",
            "rating": 5,
            "comment": "..."
          }
        ],
        "total": 1,
        "page": 1,
        "per_page": 10,
        "total_pages": 1
      }
    }
    ```

- **PUT /v1/reviews/{review_id}**
  - **Description**: Update an existing review.
  - **Request Body**:
    ```json
    {
      "rating": 4,
      "comment": "This is an updated review."
    }
    ```
  - **Response Body**:
    ```json
    {
      "success": true,
      "data": {
        "id": "...",
        "rating": 4,
        "comment": "This is an updated review."
      },
      "message": "Review updated successfully"
    }
    ```

- **DELETE /v1/reviews/{review_id}**
  - **Description**: Delete a review.
  - **Response Body**:
    ```json
    {
      "success": true,
      "message": "Review deleted successfully"
    }
    ```

### Security

- **GET /security/status**
  - **Description**: Get current security status and threat indicators.
  - **Response Body**:
    ```json
    {
      "success": true,
      "data": {
        "total_events": 0,
        "threat_indicators": {
          "sql_injection_attempts": 0,
          "xss_attempts": 0,
          "brute_force_attempts": 0
        },
        "recent_events": [],
        "security_level": "medium"
      },
      "message": "Security status retrieved successfully"
    }
    ```

- **GET /security/config**
  - **Description**: Get current security configuration.
  - **Response Body**:
    ```json
    {
      "success": true,
      "data": {
        "security_level": "medium",
        "rate_limiting_enabled": true,
        "input_sanitization_enabled": true
      },
      "message": "Security configuration retrieved successfully"
    }
    ```

- **POST /security/test**
  - **Description**: Test security features.
  - **Request Body**:
    ```json
    {
      "test_type": "input_validation",
      "test_data": {
        "input": "<script>alert('xss')</script>"
      }
    }
    ```
  - **Response Body**:
    ```json
    {
      "success": true,
      "data": {
        "input": "<script>alert('xss')</script>",
        "is_safe": false,
        "security_issues": [
          "Potential XSS attack detected"
        ],
        "warnings": [],
        "sanitized_value": ""
      },
      "message": "Security test 'input_validation' completed successfully"
    }
    ```

- **POST /security/events/{event_type}**
  - **Description**: Record a security event.
  - **Request Body**:
    ```json
    {
      "details": {
        "ip_address": "127.0.0.1"
      }
    }
    ```
  - **Response Body**:
    ```json
    {
      "success": true,
      "data": {
        "event_type": "login_failed",
        "recorded": true
      },
      "message": "Security event recorded successfully"
    }
    ```

- **GET /security/events**
  - **Description**: Get security events.
  - **Query Parameters**:
    - `limit` (optional, integer): The number of events to retrieve.
    - `event_type` (optional, string): Filter by event type.
    - `severity` (optional, string): Filter by severity.
  - **Response Body**:
    ```json
    {
      "success": true,
      "data": {
        "events": [
          {
            "timestamp": "...",
            "type": "login_failed",
            "details": {
              "ip_address": "127.0.0.1"
            },
            "severity": "medium"
          }
        ],
        "total_events": 1,
        "filters_applied": {
          "event_type": null,
          "severity": null,
          "limit": 50
        }
      },
      "message": "Security events retrieved successfully"
    }
    ```

- **DELETE /security/events**
  - **Description**: Clear security events.
  - **Query Parameters**:
    - `confirm` (required, boolean): Must be `true` to clear events.
  - **Response Body**:
    ```json
    {
      "success": true,
      "data": {
        "events_cleared": true
      },
      "message": "Security events cleared successfully"
    }
    ```

### Social Auth

- **GET /auth/facebook/callback**
  - **Description**: Facebook authentication callback.
  - **Query Parameters**:
    - `code` (required, string): The authorization code from Facebook.
  - **Response Body**:
    ```json
    {
      "message": "Facebook authentication successful",
      "user": {
        "id": "...",
        "name": "...",
        "email": "..."
      }
    }
    ```

- **GET /auth/tiktok/callback**
  - **Description**: TikTok authentication callback.
  - **Query Parameters**:
    - `code` (required, string): The authorization code from TikTok.
  - **Response Body**:
    ```json
    {
      "message": "TikTok authentication successful",
      "user": {
        "open_id": "...",
        "union_id": "...",
        "avatar_url": "...",
        "display_name": "..."
      }
    }
    ```

### Subscriptions

- **POST /v1/subscriptions/**
  - **Description**: Create a new subscription.
  - **Request Body**:
    ```json
    {
      "plan_id": "...",
      "payment_method_id": "..."
    }
    ```
  - **Response Body**:
    ```json
    {
      "success": true,
      "data": {
        "id": "...",
        "plan_id": "...",
        "status": "active"
      },
      "message": "Subscription created successfully"
    }
    ```

- **GET /v1/subscriptions/**
  - **Description**: Get user's subscriptions.
  - **Query Parameters**:
    - `page` (optional, integer): The page number to retrieve.
    - `limit` (optional, integer): The number of items to retrieve per page.
  - **Response Body**:
    ```json
    {
      "success": true,
      "data": {
        "data": [
          {
            "id": "...",
            "plan_id": "...",
            "status": "active"
          }
        ],
        "total": 1,
        "page": 1,
        "per_page": 10,
        "total_pages": 1
      }
    }
    ```

- **GET /v1/subscriptions/{subscription_id}**
  - **Description**: Get a specific subscription.
  - **Response Body**:
    ```json
    {
      "success": true,
      "data": {
        "id": "...",
        "plan_id": "...",
        "status": "active"
      }
    }
    ```

- **PUT /v1/subscriptions/{subscription_id}**
  - **Description**: Update a subscription.
  - **Request Body**:
    ```json
    {
      "plan_id": "..."
    }
    ```
  - **Response Body**:
    ```json
    {
      "success": true,
      "data": {
        "id": "...",
        "plan_id": "..."
      },
      "message": "Subscription updated successfully"
    }
    ```

- **DELETE /v1/subscriptions/{subscription_id}**
  - **Description**: Delete a subscription.
  - **Response Body**:
    ```json
    {
      "success": true,
      "message": "Subscription deleted successfully"
    }
    ```

### Users & Addresses

- **GET /v1/users/**: List users.
- **GET /v1/users/{user_id}**: Get user.
- **POST /v1/users/**: Create user.
- **PUT /v1/users/{user_id}**: Update user.
- **DELETE /v1/users/{user_id}**: Delete user.
- **GET /v1/users/me/addresses**: List my addresses.
- **GET /v1/users/{user_id}/addresses**: List addresses.
- **GET /v1/users/addresses/{address_id}**: Get address.
- **POST /v1/users/{user_id}/addresses**: Create address.
- **PUT /v1/users/addresses/{address_id}**: Update address.
- **POST /v1/users/addresses**: Create user address.
- **PUT /v1/users/addresses/{address_id}**: Update user address.
- **DELETE /v1/users/addresses/{address_id}**: Delete user address.

### Wishlists

- **POST /v1/users/{user_id}/wishlists/default**: Create a default wishlist for the user if none exists.
- **GET /v1/users/{user_id}/wishlists**: Get wishlists for a user.
- **POST /v1/users/{user_id}/wishlists**: Create a wishlist for a user.
- **GET /v1/users/{user_id}/wishlists/{wishlist_id}**: Get a specific wishlist by ID.
- **PUT /v1/users/{user_id}/wishlists/{wishlist_id}**: Update a wishlist.
- **DELETE /v1/users/{user_id}/wishlists/{wishlist_id}**: Delete a wishlist.
- **POST /v1/users/{user_id}/wishlists/{wishlist_id}/items**: Add an item to a wishlist.
- **DELETE /v1/users/{user_id}/wishlists/{wishlist_id}/items/{item_id}**: Remove an item from a wishlist.
- **PUT /v1/users/{user_id}/wishlists/{wishlist_id}/default**: Set a wishlist as default.
