<div align="center">
  <img src="frontend/public/banwe_logo_green.png" alt="Banwee Logo" width="200"/>
  
  # Banwee E-commerce Platform

  A comprehensive, modern e-commerce platform built with FastAPI and React.
</div>

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 14+ (for production) or SQLite (for development)
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/banwee/platform.git
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
   # Edit .env file with your configuration:
   # - DATABASE_URL=sqlite:///./db1.db (for development)
   # - SECRET_KEY=your-secret-key
   # - STRIPE_SECRET_KEY=your-stripe-key (if using payments)
   
   # Initialize database
   python init_db.py
   
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
   # Edit .env file with your configuration:
   # - VITE_API_URL=http://localhost:8000
   # - VITE_STRIPE_PUBLIC_KEY=your-stripe-public-key (if using payments)
   
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

- [API Documentation](./API_DOCUMENTATION.md) - Complete API endpoint reference
- [Environment Variables](./backend/ENVIRONMENT_VARIABLES.md) - Configuration guide
- Backend API Docs: http://localhost:8000/docs (when running)

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
