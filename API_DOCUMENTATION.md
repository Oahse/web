# API Documentation

This document provides a detailed overview of the Banwee E-commerce Platform API endpoints.

# API Documentation

This document provides a detailed overview of the Banwee E-commerce Platform API endpoints.

## Authentication

The API uses JWT for authentication. Include the token in the `Authorization` header as a Bearer token.

`Authorization: Bearer <your_jwt_token>`

### Authentication Endpoints

- **POST /api/v1/auth/register**
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

- **POST /api/v1/auth/login**
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

- **POST /api/v1/auth/logout**
  - **Description**: Logout user.
  - **Response Body**:
    ```json
    {
      "success": true,
      "message": "Logged out successfully"
    }
    ```

- **GET /api/v1/auth/profile**
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

- **PUT /api/v1/auth/profile**
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

- **PUT /api/v1/auth/change-password**
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

- **POST /api/v1/auth/forgot-password**
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

- **POST /api/v1/auth/reset-password**
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

- **GET /api/v1/auth/verify-email**
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

- **POST /api/v1/auth/refresh**
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

- **GET /api/v1/auth/addresses**
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

- **POST /api/v1/auth/addresses**
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

- **PUT /api/v1/auth/addresses/{address_id}**
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

- **DELETE /api/v1/auth/addresses/{address_id}**
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

- **GET /api/v1/admin/stats**
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

- **GET /api/v1/admin/overview**
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

- **GET /api/v1/admin/orders**
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

- **GET /api/v1/admin/users**
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

- **POST /api/v1/admin/users**
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

- **GET /api/v1/admin/users/{user_id}**
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

- **GET /api/v1/admin/products**
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

- **GET /api/v1/admin/variants**
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

- **PUT /api/v1/admin/users/{user_id}/status**
  - **Description**: Update user status (admin only).
  - **Request Body**:
    ```json
    {
      "active": true
    }
    ```
  - **Response Body**:
    ```json
    {
      "success": true,
      "data": {
        "id": "...",
        "active": true
      },
      "message": "User status updated"
    }
    ```

- **DELETE /api/v1/admin/users/{user_id}**
  - **Description**: Delete user (admin only).
  - **Response Body**:
    ```json
    {
      "success": true,
      "message": "User deleted successfully"
    }
    ```

- **GET /api/v1/admin/orders/{order_id}**
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

- **PUT /api/v1/admin/orders/{order_id}/ship**
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
      "message": "Order status updated to shipped and notification sent."
    }
    ```

- **PUT /api/v1/admin/orders/{order_id}/status**
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

- **GET /api/v1/admin/system/settings**
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

- **PUT /api/v1/admin/system/settings**
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

- **GET /api/v1/analytics/dashboard**
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

- **GET /api/v1/analytics/sales-trend**
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

- **GET /api/v1/analytics/top-products**
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

- **POST /api/v1/auth/register**: Register a new user.
- **POST /api/v1/auth/login**: Login user and return access token.
- **POST /api/v1/auth/logout**: Logout user.
- **GET /api/v1/auth/profile**: Get current user profile.
- **GET /api/v1/auth/addresses**: Get all addresses for the current user.
- **POST /api/v1/auth/addresses**: Create a new address for the current user.
- **PUT /api/v1/auth/addresses/{address_id}**: Update an existing address for the current user.
- **DELETE /api/v1/auth/addresses/{address_id}**: Delete an address for the current user.
- **GET /api/v1/auth/verify-email**: Verify user email with token.
- **POST /api/v1/auth/forgot-password**: Send password reset email.
- **POST /api/v1/auth/reset-password**: Reset password with token.
- **PUT /api/v1/auth/profile**: Update user profile.
- **PUT /api/v1/auth/change-password**: Change user password.
- **POST /api/v1/auth/refresh**: Refresh access token using refresh token.

### Blog

- **POST /api/v1/blog/**
  - **Description**: Create a new blog post (admin only).
  - **Request Body**:
    ```json
    {
      "title": "My First Blog Post",
      "content": "This is the content of my first blog post.",
      "is_published": true
    }
    ```
  - **Response Body**:
    ```json
    {
      "success": true,
      "data": {
        "id": "...",
        "title": "My First Blog Post",
        "content": "This is the content of my first blog post.",
        "is_published": true
      },
      "message": "Blog post created successfully"
    }
    ```

- **GET /api/v1/blog/**
  - **Description**: Get all blog posts.
  - **Query Parameters**:
    - `page` (optional, integer): The page number to retrieve.
    - `limit` (optional, integer): The number of items to retrieve per page.
    - `is_published` (optional, boolean): Filter by published status.
    - `search` (optional, string): Search query.
  - **Response Body**:
    ```json
    {
      "success": true,
      "data": {
        "data": [
          {
            "id": "...",
            "title": "...",
            "excerpt": "..."
          }
        ],
        "total": 1,
        "page": 1,
        "per_page": 10,
        "total_pages": 1
      }
    }
    ```

- **GET /api/v1/blog/{post_id}**
  - **Description**: Get a specific blog post by ID.
  - **Response Body**:
    ```json
    {
      "success": true,
      "data": {
        "id": "...",
        "title": "...",
        "content": "..."
      }
    }
    ```

- **PUT /api/v1/blog/{post_id}**
  - **Description**: Update a blog post (admin only).
  - **Request Body**:
    ```json
    {
      "title": "My Updated Blog Post",
      "content": "This is the updated content of my blog post."
    }
    ```
  - **Response Body**:
    ```json
    {
      "success": true,
      "data": {
        "id": "...",
        "title": "My Updated Blog Post",
        "content": "This is the updated content of my blog post."
      },
      "message": "Blog post updated successfully"
    }
    ```

- **DELETE /api/v1/blog/{post_id}**
  - **Description**: Delete a blog post (admin only).
  - **Response Body**:
    ```json
    {
      "success": true,
      "message": "Blog post deleted successfully"
    }
    ```

### Cart

- **GET /api/v1/cart/**
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

- **POST /api/v1/cart/add**
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

- **PUT /api/v1/cart/update/{item_id}**
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

- **DELETE /api/v1/cart/remove/{item_id}**
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

- **POST /api/v1/cart/promocode**
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

- **DELETE /api/v1/cart/promocode**
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

- **GET /api/v1/cart/count**
  - **Description**: Get the number of items in the cart.
  - **Response Body**:
    ```json
    {
      "success": true,
      "data": 5
    }
    ```

- **POST /api/v1/cart/validate**
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

- **POST /api/v1/cart/shipping-options**
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

- **POST /api/v1/cart/calculate**
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

- **POST /api/v1/cart/items/{item_id}/save-for-later**
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

- **POST /api/v1/cart/items/{item_id}/move-to-cart**
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

- **GET /api/v1/cart/saved-items**
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

- **POST /api/v1/cart/clear**
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

- **DELETE /api/v1/cart/clear**
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

- **POST /api/v1/cart/merge**
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

- **GET /api/v1/cart/checkout-summary**
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

- **GET /health/websockets**
  - **Description**: WebSocket health check.
  - **Response Body**:
    ```json
    {
      "status": "healthy",
      "timestamp": "...",
      "details": {
        "active_connections": 0,
        "total_messages_sent": 0,
        "total_messages_received": 0
      }
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
          "name": "endpoint_/api/v1/products",
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

### Notifications

- **GET /api/v1/notifications/**
  - **Description**: Get notifications for the current user.
  - **Query Parameters**:
    - `page` (optional, integer): The page number to retrieve.
    - `limit` (optional, integer): The number of items to retrieve per page.
    - `read` (optional, boolean): Filter by read status.
  - **Response Body**:
    ```json
    {
      "success": true,
      "data": {
        "data": [
          {
            "id": "...",
            "message": "...",
            "read": false
          }
        ],
        "total": 1,
        "page": 1,
        "per_page": 10,
        "total_pages": 1
      }
    }
    ```

- **PUT /api/v1/notifications/{notification_id}/read**
  - **Description**: Mark a notification as read.
  - **Response Body**:
    ```json
    {
      "success": true,
      "data": {
        "id": "...",
        "read": true
      },
      "message": "Notification marked as read"
    }
    ```

- **PUT /api/v1/notifications/mark-all-read**
  - **Description**: Mark all notifications as read.
  - **Response Body**:
    ```json
    {
      "success": true,
      "data": {
        "message": "All notifications marked as read"
      }
    }
    ```

- **DELETE /api/v1/notifications/{notification_id}**
  - **Description**: Delete a notification.
  - **Response Body**:
    ```json
    {
      "success": true,
      "message": "Notification deleted successfully"
    }
    ```

### Orders

- **POST /api/v1/orders/**
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

- **POST /api/v1/orders/checkout**
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

- **GET /api/v1/orders/**
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

- **GET /api/v1/orders/{order_id}**
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

- **PUT /api/v1/orders/{order_id}/cancel**
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

- **GET /api/v1/orders/{order_id}/tracking**
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

- **POST /api/v1/orders/{order_id}/refund**
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

- **POST /api/v1/orders/{order_id}/reorder**
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

- **GET /api/v1/orders/{order_id}/invoice**
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

- **POST /api/v1/orders/{order_id}/notes**
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

- **GET /api/v1/orders/{order_id}/notes**
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

- **GET /api/v1/users/me/payment-methods**
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

- **GET /api/v1/users/{user_id}/payment-methods**
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

- **POST /api/v1/users/{user_id}/payment-methods**
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

- **PUT /api/v1/users/{user_id}/payment-methods/{method_id}**
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

- **DELETE /api/v1/users/{user_id}/payment-methods/{method_id}**
  - **Description**: Delete a payment method.
  - **Response Body**:
    ```json
    {
      "success": true,
      "message": "Payment method deleted successfully"
    }
    ```

- **PUT /api/v1/users/{user_id}/payment-methods/{method_id}/default**
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

- **POST /api/v1/payments/create-payment-intent**
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

- **POST /api/v1/payments/process**
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

- **POST /api/v1/payments/stripe-webhook**
  - **Description**: Handle Stripe webhook events.
  - **Response Body**:
    ```json
    {
      "status": "success"
    }
    ```

### Products

- **GET /api/v1/products/home**
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

- **GET /api/v1/products/**
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

- **GET /api/v1/products/categories**
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

- **GET /api/v1/products/{product_id}/recommendations**
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

- **GET /api/v1/products/{product_id}/variants**
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

- **GET /api/v1/products/variants/{variant_id}**
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

- **GET /api/v1/products/variants/{variant_id}/qrcode**
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

- **GET /api/v1/products/variants/{variant_id}/barcode**
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

- **GET /api/v1/products/{product_id}**
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

- **GET /api/v1/products/categories/{category_id}**
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

- **POST /api/v1/products/**
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

- **PUT /api/v1/products/{product_id}**
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

- **DELETE /api/v1/products/{product_id}**
  - **Description**: Delete a product (suppliers only).
  - **Response Body**:
    ```json
    {
      "success": true,
      "message": "Product deleted successfully"
    }
    ```

### Reviews

- **POST /api/v1/reviews/**
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

- **GET /api/v1/reviews/{review_id}**
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

- **GET /api/v1/reviews/product/{product_id}**
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

- **PUT /api/v1/reviews/{review_id}**
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

- **DELETE /api/v1/reviews/{review_id}**
  - **Description**: Delete a review.
  - **Response Body**:
    ```json
    {
      "success": true,
      "message": "Review deleted successfully"
    }
    ```

### Security

- **GET /api/security/status**
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

- **GET /api/security/config**
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

- **POST /api/security/test**
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

- **POST /api/security/events/{event_type}**
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

- **GET /api/security/events**
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

- **DELETE /api/security/events**
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

- **POST /api/v1/subscriptions/**
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

- **GET /api/v1/subscriptions/**
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

- **GET /api/v1/subscriptions/{subscription_id}**
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

- **PUT /api/v1/subscriptions/{subscription_id}**
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

- **DELETE /api/v1/subscriptions/{subscription_id}**
  - **Description**: Delete a subscription.
  - **Response Body**:
    ```json
    {
      "success": true,
      "message": "Subscription deleted successfully"
    }
    ```

### Users & Addresses

- **GET /api/v1/users/**: List users.
- **GET /api/v1/users/{user_id}**: Get user.
- **POST /api/v1/users/**: Create user.
- **PUT /api/v1/users/{user_id}**: Update user.
- **DELETE /api/v1/users/{user_id}**: Delete user.
- **GET /api/v1/users/me/addresses**: List my addresses.
- **GET /api/v1/users/{user_id}/addresses**: List addresses.
- **GET /api/v1/users/addresses/{address_id}**: Get address.
- **POST /api/v1/users/{user_id}/addresses**: Create address.
- **PUT /api/v1/users/addresses/{address_id}**: Update address.
- **POST /api/v1/users/addresses**: Create user address.
- **PUT /api/v1/users/addresses/{address_id}**: Update user address.
- **DELETE /api/v1/users/addresses/{address_id}**: Delete user address.

### WebSockets

- **WS /ws**: General WebSocket endpoint.
- **WS /ws/notifications/{user_id}**: WebSocket endpoint for user-specific notifications.
- **GET /ws/stats**: Get WebSocket connection statistics.
- **GET /ws/connections/{user_id}**: Get all connections for a specific user.
- **POST /ws/cleanup**: Manually trigger cleanup of dead connections.
- **POST /ws/broadcast**: Broadcast a message to all connections (admin only).

### Wishlists

- **POST /api/v1/users/{user_id}/wishlists/default**: Create a default wishlist for the user if none exists.
- **GET /api/v1/users/{user_id}/wishlists**: Get wishlists for a user.
- **POST /api/v1/users/{user_id}/wishlists**: Create a wishlist for a user.
- **GET /api/v1/users/{user_id}/wishlists/{wishlist_id}**: Get a specific wishlist by ID.
- **PUT /api/v1/users/{user_id}/wishlists/{wishlist_id}**: Update a wishlist.
- **DELETE /api/v1/users/{user_id}/wishlists/{wishlist_id}**: Delete a wishlist.
- **POST /api/v1/users/{user_id}/wishlists/{wishlist_id}/items**: Add an item to a wishlist.
- **DELETE /api/v1/users/{user_id}/wishlists/{wishlist_id}/items/{item_id}**: Remove an item from a wishlist.
- **PUT /api/v1/users/{user_id}/wishlists/{wishlist_id}/default**: Set a wishlist as default.
