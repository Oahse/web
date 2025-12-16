<div align="center">
  <img src="frontend/public/banwe_logo_green.png" alt="Banwee Logo" width="200"/>
  
  # Banwee E-commerce Platform

  <p align="center">
    <strong>A comprehensive, modern e-commerce platform built with FastAPI and React</strong>
  </p>

  <p align="center">
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
  - [Docker Setup (Recommended)](#docker-setup-recommended)
  - [Local Development Setup](#local-development-setup)
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

The platform features a React-based frontend with TypeScript for type safety, a FastAPI backend for high-performance async operations, and includes advanced features like location-based internationalization, real-time notifications, and automated email workflows.

## ✨ Features

### Customer Features
- 🛒 **Shopping Cart** - Add, update, and manage cart items with real-time updates
- 💳 **Secure Checkout** - Stripe integration for secure payment processing
- 📦 **Order Tracking** - Track orders from placement to delivery
- ⭐ **Product Reviews** - Rate and review purchased products
- ❤️ **Wishlist** - Save favorite products for later
- 🔐 **User Authentication** - Secure registration and login with JWT tokens
- 📧 **Email Notifications** - Automated order confirmations and updates
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
- 🔔 **Notification System** - Real-time notifications for important events
- ⚙️ **System Settings** - Configure maintenance mode, file uploads, and notifications
- 🎨 **Activity Logs** - Track all user actions and system events

### Supplier Features
- 📦 **Inventory Management** - Manage product stock and variants
- 📊 **Sales Analytics** - View performance metrics for supplied products
- 🔔 **Low Stock Alerts** - Automated notifications for inventory management

### Technical Features
- 🚀 **Async Operations** - FastAPI with async/await for high performance
- 🔄 **Real-time Updates** - WebSocket support for live notifications
- 📧 **Email System** - email templates with Mailgun integration
- 🎨 **Modern UI** - Tailwind CSS with custom theming
- 🔒 **Security** - JWT authentication, password hashing, CORS protection
- 🐳 **Docker Support** - Complete containerized deployment
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
- **Task Queue**: Celery with Redis broker
- **Authentication**: JWT with python-jose
- **Email**: Mailgun API
- **Payment**: Stripe API
- **Testing**: Pytest, Hypothesis (PBT)
- **Migrations**: Alembic
- **ASGI Server**: Uvicorn

### Infrastructure
- **Containerization**: Docker & Docker Compose
- **Database**: PostgreSQL 16
- **Cache/Queue**: Redis 7
- **Image CDN**: GitHub + jsDelivr

---

## 📦 Prerequisites

### For Docker Setup (Recommended)
- Docker 20.10+
- Docker Compose 2.0+

### For Local Development
- Python 3.11 or higher
- Node.js 18 or higher
- PostgreSQL 14 or higher
- Redis 6 or higher
- Git

### Optional Services
- Stripe account (for payment processing)
- Mailgun account (for email notifications)
- GitHub account (for image storage)

---

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose (recommended)
- OR: Python 3.11+, Node.js 18+, PostgreSQL 14+, Redis

### Docker Setup (Recommended)

**The fastest way to get started with Docker:**

#### Prerequisites
- Docker 20.10+ and Docker Compose 2.0+
- 4GB+ RAM available for containers
- 10GB+ free disk space

#### Step-by-Step Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/Oahse/banweemvp.git
   cd banweemvp
   ```

2. **Configure environment variables**
   ```bash
   # Backend configuration (already configured for Docker)
   cp backend/.env.example backend/.env
   
   # Frontend configuration (already configured for Docker)
   cp frontend/.env.example frontend/.env
   
   # Optional: Update with your API keys for full functionality
   # - Stripe keys for payment processing
   # - Mailgun keys for email notifications
   # - Social auth keys for OAuth login
   ```

3. **Start all services**
   ```bash
   # Start all services in the background
   docker-compose up -d
   
   # Or use the convenience script
   ./docker-start.sh
   ```

4. **Verify services are running**
   ```bash
   # Check service status
   docker-compose ps
   
   # All services should show "healthy" or "running" status:
   # - PostgreSQL (healthy)
   # - Redis (healthy)  
   # - Backend (healthy)
   # - Frontend (healthy)
   # - Celery Worker (running)
   # - Celery Beat (running)
   ```

5. **Access the application**
   - **Frontend**: http://localhost:5173
   - **Backend API**: http://localhost:8000
   - **API Documentation**: http://localhost:8000/docs
   - **Health Check**: http://localhost:8000/health/live

6. **Optional: Seed with sample data**
   ```bash
   # Add sample products, users, and orders
   ./seed-database.sh
   ```

#### Docker Services Overview

| Service | Port | Description |
|---------|------|-------------|
| Frontend | 5173 | React/Vite development server |
| Backend | 8000 | FastAPI application server |
| PostgreSQL | 5432 | Database server |
| Redis | 6379 | Cache and message broker |
| Celery Worker | - | Background task processor |
| Celery Beat | - | Periodic task scheduler |

#### Default Credentials (After Seeding)
- **Admin**: `admin@banwee.com` / `adminpass`
- **Supplier**: `supplier@banwee.com` / `supplierpass`
- **Customer**: `customer@banwee.com` / `customerpass`

#### Docker Commands

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f [service_name]

# Stop services
docker-compose down

# Rebuild services (after code changes)
docker-compose build
docker-compose up -d

# Clean restart (removes volumes - WARNING: deletes data)
docker-compose down -v
docker-compose up -d

# Access service shell
docker-compose exec backend bash
docker-compose exec frontend sh
```

#### Troubleshooting Docker Setup

**Services not starting:**
```bash
# Check Docker daemon is running
docker info

# Check service logs
docker-compose logs backend
docker-compose logs frontend

# Restart specific service
docker-compose restart backend
```

**Database connection issues:**
```bash
# Check PostgreSQL is healthy
docker-compose ps postgres

# Test database connection
docker-compose exec backend python -c "from core.database import db_manager; print('DB OK')"
```

**Port conflicts:**
```bash
# Check if ports are in use
lsof -i :5173  # Frontend
lsof -i :8000  # Backend
lsof -i :5432  # PostgreSQL
lsof -i :6379  # Redis

# Stop conflicting services or change ports in docker-compose.yml
```

**Performance issues:**
```bash
# Check Docker resource usage
docker stats

# Increase Docker memory limit in Docker Desktop settings
# Recommended: 4GB+ RAM, 2+ CPU cores
```

### Local Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/Oahse/banweemvp.git
   cd banwee-platform
   ```

2. **Backend Setup**
   ```bash
   cd backend
   
   # Create and activate virtual environment
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   
   # Install dependencies
   pip install -r requirements.txt
   
   # Configure environment variables
   cp .env.example .env
   # Edit .env file - change POSTGRES_SERVER to localhost
   
   # Initialize database
   python init_db.py --seed
   
   # Start the backend server
   uvicorn main:app --reload
   ```

3. **Frontend Setup**
   ```bash
   cd frontend
   
   # Install dependencies
   npm install
   
   # Configure environment variables
   cp .env.example .env
   
   # Start the development server
   npm run dev
   ```

4. **Access the Application**
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000
   - API Documentation (Swagger): http://localhost:8000/docs
   - Alternative API Docs (ReDoc): http://localhost:8000/redoc

### GitHub Image Upload Configuration (Optional)

The platform supports uploading product images to GitHub for CDN delivery via jsDelivr:

1. Create a GitHub repository for image storage
2. Generate a GitHub Personal Access Token with `repo` permissions
3. Update `frontend/src/lib/github.tsx` with your repository details:
   - `GITHUB_OWNER`: Your GitHub username
   - `GITHUB_REPO`: Your repository name
   - `GITHUB_BRANCH`: Branch to use (typically `main`)
4. Encrypt your GitHub token and update the `encryptedToken` variable

**Note**: For production, store the GitHub token in environment variables instead of hardcoding it.

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
| Admin | admin@banwee.com | adminpass |
| Supplier | supplier@banwee.com | supplierpass |
| Customer | customer@banwee.com | customerpass |

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
- Real-time negotiation rounds with WebSocket updates
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

### Setup & Configuration
- **[SETUP_COMPLETE.md](./SETUP_COMPLETE.md)** - Complete setup overview and checklist
- **[DOCKER_SETUP_GUIDE.md](./DOCKER_SETUP_GUIDE.md)** - Docker setup, commands, and troubleshooting
- **[LATEST_UPDATES_SUMMARY.md](./LATEST_UPDATES_SUMMARY.md)** - Latest features and updates
- **[API_DOCUMENTATION.md](./API_DOCUMENTATION.md)** - Complete API endpoint reference

### Email System
- **[EMAIL_BRANDING_GUIDE.md](./EMAIL_BRANDING_GUIDE.md)** - Email template branding and customization
- **[EMAIL_TEMPLATE_CUSTOMIZATION_GUIDE.md](./EMAIL_TEMPLATE_CUSTOMIZATION_GUIDE.md)** - Template customization guide
- **[EMAIL_USE_CASES_QUICK_REFERENCE.txt](./EMAIL_USE_CASES_QUICK_REFERENCE.txt)** - All 45 email use cases

### SEO & Marketing
- **[SEO_OPTIMIZATION_GUIDE.md](./SEO_OPTIMIZATION_GUIDE.md)** - Comprehensive SEO optimization guide

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
                            │ HTTP/WebSocket
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
         │                    │                    │
         │                    │                    │
         ▼                    ▼                    ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  PostgreSQL  │    │    Redis     │    │    Celery    │
│   Database   │    │    Cache     │    │   Workers    │
│              │    │   + Broker   │    │              │
└──────────────┘    └──────────────┘    └──────────────┘
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
- **Tasks**: Celery background tasks for async operations
- **Core**: Shared utilities (database, auth, exceptions, logging)

### Database Schema

Key tables include:
- **users**: User accounts with roles (customer, supplier, admin)
- **products**: Product catalog with variants
- **orders**: Order records with items and status tracking
- **cart**: Shopping cart items
- **wishlist**: Saved products
- **reviews**: Product reviews and ratings
- **notifications**: User notifications
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
| `POSTGRES_USER` | PostgreSQL username | `banwee` |
| `POSTGRES_PASSWORD` | PostgreSQL password | `banwee_password` |
| `POSTGRES_SERVER` | PostgreSQL host (use `postgres` for Docker, `localhost` for local) | `postgres` or `localhost` |
| `POSTGRES_PORT` | PostgreSQL port | `5432` |
| `POSTGRES_DB` | PostgreSQL database name | `banwee_db` |
| `SECRET_KEY` | JWT secret key (min 32 chars) | Generate with `openssl rand -hex 32` |
| `REDIS_URL` | Redis connection URL (use `redis://redis:6379/0` for Docker) | `redis://redis:6379/0` |

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
| `VITE_API_BASE_URL` | Backend API URL | `http://localhost:8000/api/v1` |
| `VITE_STRIPE_PUBLIC_KEY` | Stripe publishable key | `pk_test_...` |

#### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_APP_NAME` | Application name | `Banwee` |
| `VITE_APP_URL` | Application URL | `http://localhost:5173` |
| `VITE_GOOGLE_CLIENT_ID` | Google OAuth client ID | - |
| `VITE_FACEBOOK_APP_ID` | Facebook app ID | - |
| `VITE_TIKTOK_CLIENT_ID` | TikTok client ID | - |

### Docker Environment Variables

When using Docker, environment variables are automatically configured for container networking:

#### Pre-configured for Docker
The included `.env` files are already configured for Docker deployment:

**Backend (`backend/.env`):**
```bash
# Database (configured for Docker service names)
POSTGRES_SERVER=postgres
POSTGRES_DB_URL=postgresql+asyncpg://banwee:banwee_password@postgres:5432/banwee_db
REDIS_URL=redis://redis:6379/0

# CORS (configured for Docker networking)
BACKEND_CORS_ORIGINS=http://localhost:5173,http://0.0.0.0:5173,http://127.0.0.1:5173
```

**Frontend (`frontend/.env`):**
```bash
# API endpoint (configured for Docker host networking)
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

#### Optional Service Configuration
To enable full functionality, add your API keys to `backend/.env`:

```bash
# Stripe (for payment processing)
STRIPE_SECRET_KEY=sk_test_your_stripe_secret_key
STRIPE_PUBLIC_KEY=pk_test_your_stripe_public_key

# Mailgun (for email notifications)
MAILGUN_API_KEY=your_mailgun_api_key
MAILGUN_DOMAIN=mg.yourdomain.com
MAILGUN_FROM_EMAIL=Banwee <noreply@yourdomain.com>

# Social Authentication (optional)
GOOGLE_CLIENT_ID=your_google_client_id
FACEBOOK_APP_ID=your_facebook_app_id
TIKTOK_CLIENT_KEY=your_tiktok_client_key
```

And to `frontend/.env`:
```bash
# Stripe (for payment processing)
VITE_STRIPE_PUBLIC_KEY=pk_test_your_stripe_public_key

# Social Authentication (optional)
VITE_GOOGLE_CLIENT_ID=your_google_client_id
VITE_FACEBOOK_APP_ID=your_facebook_app_id
VITE_TIKTOK_CLIENT_ID=your_tiktok_client_id
```

#### Docker-specific considerations:
- Service names are used for inter-container communication (`postgres`, `redis`)
- Host networking is used for browser-to-backend communication (`localhost:8000`)
- Environment variables are passed through `docker-compose.yml`
- Sensitive variables should never be committed to git

### Security Best Practices

1. **Never commit `.env` files** - They contain sensitive credentials
2. **Use strong SECRET_KEY** - Generate with `openssl rand -hex 32`
3. **Rotate credentials regularly** - Especially in production
4. **Use environment-specific values** - Different keys for dev/staging/prod
5. **Limit CORS origins** - Only allow trusted domains in production
6. **Use HTTPS in production** - Never send credentials over HTTP

## 🔧 Development

### Database Migrations

When you make changes to models:

```bash
cd backend
# Create migration
alembic revision --autogenerate -m "Description of changes"
# Apply migration
alembic upgrade head
```

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
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
# Deploy to: AWS EC2, DigitalOcean Droplet, Heroku, or any VPS
```

#### Docker Production Deployment
```bash
# Build production images
docker-compose -f docker-compose.prod.yml build

# Deploy with orchestration
# Use Kubernetes, Docker Swarm, or AWS ECS for production
```

### Recommended Hosting Platforms

- **Frontend**: Vercel, Netlify, AWS Amplify, Cloudflare Pages
- **Backend**: AWS EC2/ECS, DigitalOcean, Heroku, Railway
- **Database**: AWS RDS, DigitalOcean Managed Database, Supabase
- **Redis**: AWS ElastiCache, Redis Cloud, DigitalOcean Managed Redis
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

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

### MIT License Summary

- ✅ Commercial use
- ✅ Modification
- ✅ Distribution
- ✅ Private use
- ❌ Liability
- ❌ Warranty

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

- **LinkedIn**: [Banwee Platform](#)
- **Twitter**: [@BanweePlatform](#)
- **Facebook**: [Banwee](#)
- **Instagram**: [@banwee](#)

---

## 🙏 Acknowledgments

- FastAPI for the excellent async Python framework
- React team for the powerful UI library
- Stripe for secure payment processing
- Mailgun for reliable email delivery
- All contributors who have helped improve this project

---

## 📸 Screenshots

### Customer Experience

#### Homepage
![Homepage](docs/screenshots/homepage.png)
*Modern, responsive homepage with featured products and categories*

#### Product Listing
![Product Listing](docs/screenshots/product-listing.png)
*Browse products with filtering and sorting options*

#### Product Details
![Product Details](docs/screenshots/product-details.png)
*Detailed product view with reviews and variants*

#### Shopping Cart
![Shopping Cart](docs/screenshots/cart.png)
*Intuitive cart management with real-time updates*

#### Checkout
![Checkout](docs/screenshots/checkout.png)
*Secure checkout with Stripe integration*

### Admin Dashboard

#### Analytics Dashboard
![Admin Dashboard](docs/screenshots/admin-dashboard.png)
*Comprehensive analytics with charts and metrics*

#### Product Management
![Product Management](docs/screenshots/admin-products.png)
*Easy product creation and management*

#### Order Management
![Order Management](docs/screenshots/admin-orders.png)
*Track and manage all orders*

#### User Management
![User Management](docs/screenshots/admin-users.png)
*Manage customers, suppliers, and admins*

---

## 🎬 Demo

### Live Demo
Visit our live demo: [https://banwee-demo.com](#) *(Coming Soon)*

### Video Walkthrough
Watch a complete walkthrough: [YouTube Demo](#) *(Coming Soon)*

---

<div align="center">
  <p>Made with ❤️ by the Banwee Team</p>
  <p>
    <a href="#table-of-contents">Back to Top ↑</a>
  </p>
</div>
