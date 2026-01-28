# E-Commerce Platform

A comprehensive full-stack e-commerce platform built with FastAPI (Python) backend and React (TypeScript) frontend.

## 🚀 Features

### Core Features
- **User Authentication & Authorization** - JWT-based auth with OAuth support
- **Product Management** - Products, variants, categories, inventory tracking
- **Shopping Cart** - Persistent cart with real-time updates
- **Checkout & Payments** - Stripe integration with multiple payment methods
- **Order Management** - Order tracking, fulfillment, refunds
- **Subscription System** - Recurring orders with flexible scheduling
- **Admin Dashboard** - Comprehensive admin panel with analytics
- **Search & Filtering** - Advanced product search and filtering
- **Reviews & Ratings** - Product reviews and rating system
- **Wishlist** - Save products for later
- **Inventory Management** - Multi-warehouse inventory tracking
- **Discount System** - Coupons, promotions, and bulk discounts
- **Analytics** - Sales analytics and reporting
- **Email Notifications** - Automated email system
- **Mobile Responsive** - Fully responsive design

### Technical Features
- **Async/Await** - Full async support for high performance
- **Background Jobs** - ARQ for background task processing
- **Caching** - Redis caching for improved performance
- **Database** - PostgreSQL with SQLAlchemy ORM
- **API Documentation** - Auto-generated OpenAPI/Swagger docs
- **Testing** - Comprehensive test suite with 80%+ coverage
- **Docker Support** - Full containerization with Docker Compose
- **CI/CD Pipeline** - GitHub Actions for automated testing and deployment
- **Security** - CORS, rate limiting, input validation, SQL injection protection
- **Monitoring** - Health checks and error tracking

## 🛠️ Tech Stack

### Backend
- **FastAPI** - Modern, fast web framework for building APIs
- **Python 3.11** - Latest Python with async/await support
- **PostgreSQL** - Robust relational database
- **SQLAlchemy** - Python SQL toolkit and ORM
- **Redis** - In-memory data structure store for caching
- **ARQ** - Async task queue for background jobs
- **Stripe** - Payment processing
- **Pydantic** - Data validation using Python type annotations
- **Alembic** - Database migration tool
- **Pytest** - Testing framework

### Frontend
- **React 18** - Modern React with hooks and concurrent features
- **TypeScript** - Type-safe JavaScript
- **Vite** - Fast build tool and dev server
- **Tailwind CSS** - Utility-first CSS framework
- **React Router** - Client-side routing
- **React Hook Form** - Performant forms with easy validation
- **Axios** - HTTP client for API requests
- **Stripe Elements** - Secure payment forms
- **React Query** - Data fetching and caching
- **Vitest** - Fast unit testing framework
- **React Testing Library** - Testing utilities

### DevOps & Tools
- **Docker** - Containerization
- **Docker Compose** - Multi-container orchestration
- **GitHub Actions** - CI/CD pipeline
- **Nginx** - Reverse proxy and load balancer
- **ESLint** - JavaScript/TypeScript linting
- **Prettier** - Code formatting

## 📋 Prerequisites

- **Python 3.11+**
- **Node.js 18+**
- **PostgreSQL 15+**
- **Redis 7+**
- **Docker & Docker Compose** (optional)

## 🚀 Quick Start

### Using Docker (Recommended)

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd ecommerce-platform
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   cp backend/.env.example backend/.env
   cp frontend/.env.example frontend/.env
   # Edit .env files with your configuration
   ```

3. **Start the application**
   ```bash
   docker-compose up -d
   ```

4. **Run database migrations**
   ```bash
   docker-compose exec backend alembic upgrade head
   ```

5. **Access the application**
   - Frontend: http://localhost
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### Manual Setup

#### Backend Setup

1. **Navigate to backend directory**
   ```bash
   cd backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your database and Redis URLs
   ```

5. **Set up PostgreSQL database**
   ```bash
   # Create database
   createdb ecommerce_db
   
   # Or using psql
   psql -c "CREATE DATABASE ecommerce_db;"
   ```

6. **Run database migrations**
   ```bash
   alembic upgrade head
   ```

7. **Start the backend server**
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

8. **Start ARQ worker (in another terminal)**
   ```bash
   cd backend
   source venv/bin/activate
   python start_arq_worker.py
   ```

#### Frontend Setup

1. **Navigate to frontend directory**
   ```bash
   cd frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your API URL and Stripe public key
   ```

4. **Start the development server**
   ```bash
   npm run dev
   ```

5. **Access the application**
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

## 🔧 Testing API Connection

After setting up both backend and frontend, test the connection:

```bash
# Install axios for the test script
npm install -g axios

# Run the connection test
node test-api-connection.js
```

This will verify that:
- Backend is running and accessible
- API endpoints are responding correctly
- Frontend can communicate with backend

## 🧪 Testing

### Backend Tests

```bash
cd backend

# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test categories
pytest tests/unit/
pytest tests/integration/

# Run specific test file
pytest tests/unit/test_auth_service.py
```

### Frontend Tests

```bash
cd frontend

# Run all tests
npm test

# Run with coverage
npm run test:coverage

# Run specific test categories
npm run test:api
npm run test:components
npm run test:hooks

# Run tests in watch mode
npm run test:watch
```

## 📚 API Documentation

The API documentation is automatically generated and available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

### Key API Endpoints

#### Authentication
- `POST /v1/auth/register` - User registration
- `POST /v1/auth/login` - User login
- `POST /v1/auth/refresh` - Refresh access token
- `POST /v1/auth/logout` - User logout
- `GET /v1/auth/profile` - Get user profile
- `PUT /v1/auth/profile` - Update user profile

#### Products
- `GET /v1/products` - List products with filtering
- `GET /v1/products/{id}` - Get product details
- `GET /v1/products/categories` - List product categories
- `GET /v1/products/search?q=query` - Search products

#### Cart
- `GET /v1/cart` - Get user's cart
- `POST /v1/cart/add` - Add item to cart
- `PUT /v1/cart/items/{id}` - Update cart item
- `DELETE /v1/cart/items/{id}` - Remove cart item
- `DELETE /v1/cart/clear` - Clear entire cart

#### Orders
- `GET /v1/orders` - List user's orders
- `POST /v1/orders` - Create new order
- `GET /v1/orders/{id}` - Get order details
- `POST /v1/orders/{id}/cancel` - Cancel order

#### Subscriptions
- `GET /v1/subscriptions` - List user's subscriptions
- `POST /v1/subscriptions` - Create subscription
- `PUT /v1/subscriptions/{id}` - Update subscription
- `POST /v1/subscriptions/{id}/pause` - Pause subscription

## 🏗️ Project Structure

```
ecommerce-platform/
├── backend/                 # FastAPI backend
│   ├── api/                # API route handlers
│   ├── core/               # Core utilities (auth, db, config)
│   ├── models/             # SQLAlchemy models
│   ├── schemas/            # Pydantic schemas
│   ├── services/           # Business logic
│   ├── jobs/               # Background tasks
│   ├── tests/              # Test suite
│   ├── alembic/            # Database migrations
│   ├── main.py             # FastAPI app entry point
│   └── requirements.txt    # Python dependencies
├── frontend/               # React frontend
│   ├── src/
│   │   ├── api/           # API client functions
│   │   ├── components/    # React components
│   │   ├── hooks/         # Custom React hooks
│   │   ├── pages/         # Page components
│   │   ├── store/         # Context providers
│   │   ├── utils/         # Utility functions
│   │   └── types/         # TypeScript type definitions
│   ├── public/            # Static assets
│   ├── package.json       # Node.js dependencies
│   └── vite.config.js     # Vite configuration
├── docs/                  # Documentation
├── .github/               # GitHub Actions workflows
├── docker-compose.yml     # Docker Compose configuration
├── test-api-connection.js # API connection test script
└── README.md             # This file
```

## 🔧 Configuration

### Environment Variables

#### Backend (.env)
```env
# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/ecommerce_db

# Redis
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Stripe
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USERNAME=your-email@gmail.com
EMAIL_PASSWORD=your-app-password

# Environment
ENVIRONMENT=development
DEBUG=true
```

#### Frontend (.env)
```env
VITE_API_BASE_URL=http://localhost:8000/v1
VITE_STRIPE_PUBLIC_KEY=pk_test_...
VITE_ENVIRONMENT=development
```

## 🚀 Deployment

### Production Deployment with Docker

1. **Set production environment variables**
   ```bash
   cp .env.example .env
   cp backend/.env.example backend/.env
   cp frontend/.env.example frontend/.env
   # Configure production values
   ```

2. **Build and start services**
   ```bash
   docker-compose -f docker-compose.yml up -d
   ```

3. **Run database migrations**
   ```bash
   docker-compose exec backend alembic upgrade head
   ```

## 🔒 Security

### Security Features Implemented

- **Authentication**: JWT tokens with refresh mechanism
- **Authorization**: Role-based access control
- **Input Validation**: Pydantic models for request validation
- **SQL Injection Protection**: SQLAlchemy ORM with parameterized queries
- **CORS**: Configured for specific origins
- **Rate Limiting**: API rate limiting middleware
- **Password Hashing**: Bcrypt for secure password storage
- **HTTPS**: SSL/TLS encryption in production
- **Security Headers**: Comprehensive security headers
- **Data Sanitization**: Input sanitization and validation

## 🤝 Contributing

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. **Make your changes**
4. **Add tests for your changes**
5. **Run the test suite**
   ```bash
   # Backend tests
   cd backend && pytest
   
   # Frontend tests
   cd frontend && npm test
   ```
6. **Commit your changes**
   ```bash
   git commit -m 'Add some amazing feature'
   ```
7. **Push to the branch**
   ```bash
   git push origin feature/amazing-feature
   ```
8. **Open a Pull Request**

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Built with ❤️ by the development team**
    <a href="#features">Features</a> •
    <a href="#tech-stack">Tech Stack</a> •
    <a href="#quick-start">Quick Start</a> •
    <a href="#documentation">Documentation</a> •
    <a href="#contributing">Contributing</a> •
  </p>

  <p align="center">
    <img src="https://img.shields.io/badge/python-3.11+-blue.svg" alt="Python Version" />
    <img src="https://img.shields.io/badge/node-18+-green.svg" alt="Node Version" />
    <img src="https://img.shields.io/badge/PRs-welcome-brightgreen.svg" alt="PRs Welcome" />
  </p>
</div>

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Usage](#usage)
- [Testing](#testing)
- [Documentation](#documentation)
- [Architecture](#architecture)
- [Environment Variables](#environment-variables)
- [Development](#development)
- [Deployment](#deployment)
- [Contributing](#contributing)
- [Contact](#contact)

---

## 🌟 Overview

Banwee is a full-featured, production-ready e-commerce platform designed for scalability, performance, and developer experience. Built with modern technologies and best practices, it provides a complete solution for online retail businesses with support for multiple user roles, payment processing, inventory management, and comprehensive analytics.

The platform features a React-based frontend with TypeScript for type safety, a FastAPI backend for high-performance async operations, and includes advanced features like location-based internationalization and automated email workflows.

## ✨ Features

### Customer Features
- 🛒 **Shopping Cart** - Add, update, and manage cart items
- 💳 **Secure Checkout** - Stripe integration for secure payment processing
- 📦 **Order Tracking** - Track orders from placement to delivery
- ⭐ **Product Reviews** - Rate and review purchased products
- ❤️ **Wishlist** - Save favorite products for later
- 🔐 **User Authentication** - Secure registration and login with JWT tokens
- 📧 **Email Confirmations** - Automated order confirmations and updates
- 🌍 **Internationalization** - Auto-detect location and set language/currency for 21+ countries
- 📱 **Responsive Design** - Optimized for desktop, tablet, and mobile devices
- 💰 **Price Negotiation** - Interactive price negotiation system with AI-powered agents
- 🔍 **Advanced Search** - Intelligent search with autocomplete, fuzzy matching, and relevance ranking

### Admin Features
- 📊 **Analytics Dashboard** - Comprehensive sales, user, and product analytics
- 👥 **User Management** - Manage customers, suppliers, and admin accounts
- 📦 **Product Management** - Create, update, and organize products with variants
- 🏷️ **Promo Codes** - Create and manage discount codes
- 📈 **Sales Reports** - Export analytics data in CSV and Excel formats
- ⚙️ **System Settings** - Configure maintenance mode and file uploads
- 🎨 **Activity Logs** - Track all user actions and system events

### Supplier Features
- 📦 **Inventory Management** - Manage product stock and variants
- 📊 **Sales Analytics** - View performance metrics for supplied products

### Technical Features
- 🚀 **Async Operations** - FastAPI with async/await for high performance
- 📧 **Email System** - email templates with Mailgun integration
- 🎨 **Modern UI** - Tailwind CSS with custom theming
- 🔒 **Security** - JWT authentication, password hashing, CORS protection
- 🧪 **Property-Based Testing** - Comprehensive test coverage with Hypothesis
- 📝 **API Documentation** - Auto-generated Swagger/ReDoc documentation
- 🖼️ **CDN Image Delivery** - GitHub + jsDelivr for fast image loading
- 🤖 **AI Negotiation Engine** - Intelligent price negotiation with buyer/seller agents
- 🔍 **PostgreSQL Full-Text Search** - Advanced search with trigram matching and fuzzy search

---

## 🛠️ Tech Stack

### Frontend
- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite
- **Styling**: Tailwind CSS
- **State Management**: React Context API
- **Routing**: React Router v6
- **HTTP Client**: Axios
- **Forms**: React Hook Form + Zod validation
- **Charts**: Recharts, Chart.js
- **UI Components**: Lucide React icons, Framer Motion
- **Payment**: Stripe React SDK
- **Testing**: Vitest, React Testing Library, fast-check (PBT)

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL 16 with SQLAlchemy 2.0 (async)
- **Caching**: Redis 7
- **Background Tasks**: FastAPI Background Tasks with async/await
- **Authentication**: JWT with python-jose
- **Email**: Mailgun API
- **Payment**: Stripe API
- **Testing**: Pytest, Hypothesis (PBT)
- **Migrations**: Alembic (automatic on startup)
- **ASGI Server**: Uvicorn

### Infrastructure
- **Database**: Neon PostgreSQL (Cloud)
- **Cache**: Upstash Redis (Cloud)
- **Image CDN**: GitHub + jsDelivr

---

## 📦 Prerequisites

### System Requirements
- Python 3.11 or higher
- Node.js 18 or higher
- Git

### Cloud Services (Pre-configured)
- Neon PostgreSQL (database URL already in `.env`)
- Upstash Redis (cache URL already in `.env`)

### Optional Services
- Stripe account (for payment processing)
- Mailgun account (for email confirmations)
- GitHub account (for image storage)

**Note**: No local database installation required - cloud databases are pre-configured and ready to use.

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11 or higher
- Node.js 18 or higher
- Git

**Note**: Docker has been removed from this project. The application now uses cloud databases (Neon PostgreSQL and Upstash Redis) for simplified deployment.

### Cloud Database Setup

This application uses cloud databases instead of local Docker containers:

- **Database**: Neon PostgreSQL (already configured in `.env`)
- **Cache**: Upstash Redis (already configured in `.env`)

No additional database setup is required - the cloud databases are ready to use.

### One-Command Setup

**The fastest way to get started:**

```bash
# Clone the repository
git clone https://github.com/Oahse/banweemvp.git
cd banweemvp

# Start the application (initializes database and starts servers)
./start-app.sh
```

This script will:
1. Set up Python virtual environment
2. Install all dependencies
3. Initialize and seed the database
4. Start both backend and frontend servers

### Manual Setup

If you prefer to set up manually:

#### 1. Clone the repository
```bash
git clone https://github.com/Oahse/banweemvp.git
cd banweemvp
```

#### 2. Initialize Database
```bash
# Initialize database with sample data
./init-database.sh

# Or without sample data
./init-database.sh --no-seed
```

#### 3. Start Backend
```bash
cd backend
source .venv/bin/activate  # Virtual environment is created by init script
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

#### 4. Start Frontend
```bash
cd frontend
npm install
npm run dev
```

### Access the Application

Once running, you can access:

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

### Default Credentials

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@banwee.com | admin123 |
| Supplier | supplier1@banwee.com | supplier1123 |
| Customer | customer1@example.com | customer1123 |

### Available Scripts

| Script | Description |
|--------|-------------|
| `./start-app.sh` | Complete setup and start (recommended) |
| `./init-database.sh` | Initialize database only |
| `./deploy-to-github.sh` | Commit and push changes to GitHub |

### Troubleshooting

**Database connection issues:**
- Verify your `.env` file contains the correct `POSTGRES_DB_URL`
- Check your internet connection (cloud database required)

**Port conflicts:**
```bash
# Check if ports are in use
lsof -i :5173  # Frontend
lsof -i :8000  # Backend
```

**Python environment issues:**
```bash
# Recreate virtual environment
cd backend
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 🧪 Testing

### Backend Tests
```bash
cd backend
pytest                          # Run all tests
pytest -v                       # Verbose output
pytest tests/test_specific.py   # Run specific test file
pytest -k "test_name"           # Run tests matching pattern
```

### Frontend Tests
```bash
cd frontend
npm test                        # Run all tests
npm test -- --run               # Run tests once (no watch mode)
npm test -- --coverage          # Run with coverage report
```

### Integration Tests
```bash
cd backend
pytest tests/test_final_integration.py -v
```

## 💻 Usage

### Accessing the Application

Once the application is running, you can access:

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Documentation (Swagger)**: http://localhost:8000/docs
- **API Documentation (ReDoc)**: http://localhost:8000/redoc
### Default Credentials

The seeded database includes the following test accounts:

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@banwee.com | admin123 |
| Supplier | supplier1@banwee.com | supplier1123 |
| Customer | customer1@example.com | customer1123 |

### Key Workflows

#### For Customers
1. Browse products by category or use advanced search
2. Use price negotiation feature on product pages
3. Add items to cart
4. Create an account or login
5. Add shipping address
6. Complete checkout with Stripe
7. Track order status
8. Leave product reviews

#### Price Negotiation Feature
The platform includes an innovative price negotiation system:
- Click "Negotiate Price" on any product page
- Set your target price and maximum limit
- Choose negotiation style (aggressive, balanced, friendly)
- AI agents simulate realistic buyer-seller negotiations
- Accept or reject final negotiated prices

#### For Admins
1. Login with admin credentials
2. Access admin dashboard at `/admin`
3. View analytics and reports
4. Manage users, products, and orders
5. Configure system settings
6. Export data for analysis

#### For Suppliers
1. Login with supplier credentials
2. Access supplier dashboard
3. Manage product inventory
4. View sales analytics
5. Respond to low stock alerts

---

## 📚 Documentation

All project documentation is now located in the `docs/` directory.

- **[API.md](./docs/API.md)** - Complete API endpoint reference and usage guide.
- **[MIGRATION.md](./docs/MIGRATION.md)** - Database migration guide.
- **[ENVIRONMENT.md](./docs/ENVIRONMENT.md)** - Environment configuration guide.
- **[EMAIL_USE_CASES.txt](./docs/EMAIL_USE_CASES.txt)** - Quick reference for all 45 email use cases.

### Live Documentation
- **Backend API Docs**: http://localhost:8000/docs (Swagger UI)
- **Backend API Docs**: http://localhost:8000/redoc (ReDoc)

---

## 🏗️ Architecture

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Frontend                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  React + TypeScript + Vite                           │  │
│  │  - Context API (State Management)                    │  │
│  │  - React Router (Navigation)                         │  │
│  │  - Axios (HTTP Client)                               │  │
│  │  - Tailwind CSS (Styling)                            │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ HTTP
                            ▼
┌────────────────────────────────────────────────────────────┐
│                         Backend                            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  FastAPI + Python 3.11                               │  │
│  │  - Async/Await Operations                            │  │
│  │  - JWT Authentication                                │  │
│  │  - SQLAlchemy 2.0 (Async)                            │  │
│  │  - Pydantic Validation                               │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────┘

```

### Key Components

#### Frontend Architecture
- **Pages**: Route-level components (Home, ProductList, Checkout, Admin Dashboard)
- **Components**: Reusable UI components (ProductCard, CartItem, Header)
- **Contexts**: Global state management (Auth, Cart, Wishlist, Theme, Locale)
- **APIs**: Service layer for backend communication
- **Hooks**: Custom React hooks for common functionality

#### Backend Architecture
- **Routes**: API endpoint definitions with FastAPI routers
- **Services**: Business logic layer (OrderService, ProductService, etc.)
- **Models**: SQLAlchemy ORM models for database tables
- **Schemas**: Pydantic models for request/response validation
- **Tasks**: FastAPI Background Tasks for async operations
- **Core**: Shared utilities (database, auth, exceptions, logging)

### Database Schema

Key tables include:
- **users**: User accounts with roles (customer, supplier, admin)
- **products**: Product catalog with variants
- **orders**: Order records with items and status tracking
- **cart**: Shopping cart items
- **wishlist**: Saved products
- **reviews**: Product reviews and ratings
- **activity_logs**: System activity tracking
- **system_settings**: Configurable application settings

### Security Architecture
- JWT-based authentication with access and refresh tokens
- Password hashing with bcrypt
- CORS protection with configurable origins
- SQL injection prevention via SQLAlchemy ORM
- XSS protection via React's built-in escaping
- CSRF protection for state-changing operations
- Rate limiting on sensitive endpoints
- Secure environment variable management

## ⚙️ Environment Variables

### Backend Environment Variables

All backend environment variables should be configured in `backend/.env`. See `backend/.env.example` for a complete template.

#### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `POSTGRES_DB_URL` | Complete PostgreSQL connection URL | `postgresql+asyncpg://banwee:banwee_password@postgres:5432/banwee_db` |
| `SECRET_KEY` | JWT secret key (min 32 chars) | Generate with `openssl rand -hex 32` |
| `REDIS_URL` | Redis connection URL | `rediss://default:***@upstash.io:6379` |

#### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DOMAIN` | Application domain | `localhost` |
| `ENVIRONMENT` | Environment name | `local` |
| `FRONTEND_URL` | Frontend URL for CORS | `http://localhost:5173` |
| `BACKEND_CORS_ORIGINS` | Allowed CORS origins (comma-separated) | `http://localhost:5173` |
| `ALGORITHM` | JWT algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token expiration | `30` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token expiration | `7` |

#### Email Configuration (Mailgun)

| Variable | Description | Required |
|----------|-------------|----------|
| `MAILGUN_API_KEY` | Mailgun API key | Yes for email features |
| `MAILGUN_DOMAIN` | Mailgun domain | Yes for email features |
| `MAILGUN_FROM_EMAIL` | From email address | Yes for email features |

#### Payment Configuration (Stripe)

| Variable | Description | Required |
|----------|-------------|----------|
| `STRIPE_SECRET_KEY` | Stripe secret key | Yes for payments |
| `STRIPE_PUBLIC_KEY` | Stripe public key | Yes for payments |
| `STRIPE_WEBHOOK_SECRET` | Stripe webhook secret | Yes for webhooks |

#### Social Authentication (Optional)

| Variable | Description |
|----------|-------------|
| `GOOGLE_CLIENT_ID` | Google OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | Google OAuth client secret |
| `FACEBOOK_APP_ID` | Facebook app ID |
| `FACEBOOK_APP_SECRET` | Facebook app secret |
| `TIKTOK_CLIENT_KEY` | TikTok client key |
| `TIKTOK_CLIENT_SECRET` | TikTok client secret |

### Frontend Environment Variables

All frontend environment variables should be configured in `frontend/.env`. See `frontend/.env.example` for a complete template.

#### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `VITE_API_BASE_URL` | Backend API URL | `http://localhost:8000/v1` |
| `VITE_STRIPE_PUBLIC_KEY` | Stripe publishable key | `pk_test_...` |

#### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_APP_NAME` | Application name | `Banwee` |
| `VITE_APP_URL` | Application URL | `http://localhost:5173` |
| `VITE_GOOGLE_CLIENT_ID` | Google OAuth client ID | - |
| `VITE_FACEBOOK_APP_ID` | Facebook app ID | - |
| `VITE_TIKTOK_CLIENT_ID` | TikTok client ID | - |

### Security Best Practices

1. **Never commit `.env` files** - They contain sensitive credentials
2. **Use strong SECRET_KEY** - Generate with `openssl rand -hex 32`
3. **Rotate credentials regularly** - Especially in production
4. **Use environment-specific values** - Different keys for dev/staging/prod
5. **Limit CORS origins** - Only allow trusted domains in production
6. **Use HTTPS in production** - Never send credentials over HTTP

## 🔧 Development

### Database Migrations

Migrations are handled automatically when the application starts. For manual migration operations:

```bash
# Navigate to backend directory
cd backend
source .venv/bin/activate

# Create new migration (after model changes)
alembic revision --autogenerate -m "Description of changes"

# Check migration status
alembic current

# View migration history
alembic history
```

For more details, see [MIGRATION.md](./docs/MIGRATION.md).

### Code Quality

```bash
# Backend linting
cd backend
flake8

# Frontend linting
cd frontend
npm run lint
```

## 🚢 Deployment

### Production Considerations

1. **Environment Variables**: Use secure environment variables for all sensitive data
2. **Database**: Use managed PostgreSQL service (AWS RDS, DigitalOcean, etc.)
3. **CORS**: Configure allowed origins in backend settings
4. **HTTPS**: Enable SSL/TLS for secure communication
5. **Image Storage**: Use environment variables for GitHub token or migrate to S3/CDN
6. **Monitoring**: Set up logging and error tracking (Sentry, LogRocket)
7. **Scaling**: Use load balancers and multiple backend instances
8. **Backups**: Implement automated database backups
9. **CDN**: Use CDN for static assets (Cloudflare, AWS CloudFront)
10. **Security**: Enable rate limiting, implement WAF rules

### Build for Production

#### Frontend
```bash
cd frontend
npm run build
# Output will be in frontend/dist
# Deploy to: Vercel, Netlify, AWS S3 + CloudFront, or any static host
```

#### Backend
```bash
cd backend
# Use a production ASGI server like gunicorn with uvicorn workers
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind localhost:8000
# Deploy to: AWS EC2, DigitalOcean Droplet, Heroku, or any VPS
```

### Recommended Hosting Platforms

- **Frontend**: Vercel, Netlify, AWS Amplify, Cloudflare Pages
- **Backend**: AWS EC2/ECS, DigitalOcean, Heroku, Railway
- **Database**: Neon PostgreSQL (already configured)
- **Cache**: Upstash Redis (already configured)
- **Full Stack**: AWS, Google Cloud Platform, Azure, DigitalOcean

---

## 🤝 Contributing

We welcome contributions from the community! Here's how you can help:

### Getting Started

1. **Fork the repository**
   ```bash
   git clone https://github.com/yourusername/banweemvp.git
   cd banweemvp
   ```

2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes**
   - Follow the existing code style
   - Write tests for new features
   - Update documentation as needed

4. **Run tests**
   ```bash
   # Backend tests
   cd backend
   pytest

   # Frontend tests
   cd frontend
   npm test -- --run
   ```

5. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   ```

6. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

7. **Create a Pull Request**
   - Go to the original repository
   - Click "New Pull Request"
   - Select your feature branch
   - Describe your changes in detail

### Contribution Guidelines

- **Code Style**: Follow PEP 8 for Python, ESLint rules for TypeScript
- **Commits**: Use conventional commit messages (feat, fix, docs, style, refactor, test, chore)
- **Tests**: Maintain or improve test coverage
- **Documentation**: Update README and relevant docs for new features
- **Issues**: Check existing issues before creating new ones
- **Pull Requests**: Keep PRs focused on a single feature or fix

### Development Workflow

1. Check the [Issues](https://github.com/Oahse/banweemvp/issues) page for open tasks
2. Comment on an issue to claim it
3. Follow the contribution steps above
4. Wait for code review and address feedback
5. Once approved, your PR will be merged

### Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on the code, not the person
- Help others learn and grow

---



---

## 📧 Contact

### Project Maintainer

- **GitHub**: [@Oahse](https://github.com/Oahse)
- **Project Repository**: [banweemvp](https://github.com/Oahse/banweemvp)

### Support

- **Issues**: [GitHub Issues](https://github.com/Oahse/banweemvp/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Oahse/banweemvp/discussions)
- **Email**: support@banwee.com (if applicable)

### Social Media

- **LinkedIn**: [Banwee Platform](https://linkedin.com/company/banwee)
- **Twitter**: [@BanweePlatform](https://twitter.com/banweeplatform)
- **Facebook**: [Banwee](https://facebook.com/banwee)
- **Instagram**: [@banwee](https://instagram.com/banwee)



---

## 🙏 Acknowledgments

- FastAPI for the excellent async Python framework
- React team for the powerful UI library
- Stripe for secure payment processing
- Mailgun for reliable email delivery
- Apache Kafka for robust message streaming
- All contributors who have helped improve this project



---

<div align="center">
  <p>Made with ❤️ by the Banwee Team</p>
  <p>
    <a href="#table-of-contents">Back to Top ↑</a>
  </p>
</div>
