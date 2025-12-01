<div align="center">
  <img src="frontend/public/banwe_logo_green.png" alt="Banwee Logo" width="200"/>
  
  # Banwee E-commerce Platform

  A comprehensive, modern e-commerce platform built with FastAPI and React.
</div>

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose (recommended)
- OR: Python 3.11+, Node.js 18+, PostgreSQL 14+, Redis

### Docker Setup (Recommended)

**The fastest way to get started:**

```bash
# 1. Launch all services
./docker-start.sh

# 2. Seed database with sample data
./seed-database.sh

# 3. Access the application
# Frontend: http://localhost:5173
# Backend: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

**Default credentials:**
- Admin: `admin@banwee.com` / `adminpass`
- Supplier: `supplier@banwee.com` / `supplierpass`

📖 **See [DOCKER_SETUP_GUIDE.md](./DOCKER_SETUP_GUIDE.md) for complete Docker documentation**

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

## 📚 Documentation

### Setup & Configuration
- **[SETUP_COMPLETE.md](./SETUP_COMPLETE.md)** - ✅ Complete setup overview and checklist
- **[DOCKER_SETUP_GUIDE.md](./DOCKER_SETUP_GUIDE.md)** - Docker setup, commands, and troubleshooting
- **[LATEST_UPDATES_SUMMARY.md](./LATEST_UPDATES_SUMMARY.md)** - 🆕 Latest features and updates
- **[API_DOCUMENTATION.md](./API_DOCUMENTATION.md)** - Complete API endpoint reference

### Email System
- **[EMAIL_BRANDING_GUIDE.md](./EMAIL_BRANDING_GUIDE.md)** - Email template branding and customization
- **[EMAIL_TEMPLATE_CUSTOMIZATION_GUIDE.md](./EMAIL_TEMPLATE_CUSTOMIZATION_GUIDE.md)** - Template customization guide
- **[EMAIL_USE_CASES_QUICK_REFERENCE.txt](./EMAIL_USE_CASES_QUICK_REFERENCE.txt)** - All 45 email use cases

### SEO & Marketing
- **[SEO_OPTIMIZATION_GUIDE.md](./SEO_OPTIMIZATION_GUIDE.md)** - 🆕 Comprehensive SEO optimization guide

### Live Documentation
- Backend API Docs: http://localhost:8000/docs (when running)

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

When using Docker, environment variables can be set in:
1. `.env` file in the project root (for docker-compose)
2. Individual service `.env` files (backend/.env, frontend/.env)

Docker-specific considerations:
- Use service names for hosts (e.g., `postgres` instead of `localhost`)
- The `docker-compose.yml` file passes environment variables to containers
- Sensitive variables should be stored in `.env` files (not committed to git)

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
2. **Database**: Use PostgreSQL instead of SQLite
3. **CORS**: Configure allowed origins in backend settings
4. **HTTPS**: Enable SSL/TLS for secure communication
5. **Image Storage**: Consider using environment variables for GitHub token
6. **Monitoring**: Set up logging and error tracking

### Build for Production

```bash
# Frontend build
cd frontend
npm run build
# Output will be in frontend/dist

# Backend
cd backend
# Use a production ASGI server like gunicorn with uvicorn workers
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker
```
