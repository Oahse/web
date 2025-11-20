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

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/banwee/platform.git
   cd banwee-platform
   ```

2. **Backend Setup**
   ```bash
   cd backend
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   cp .env.example .env
   # Edit .env to use SQLite for development
   # DATABASE_URL=sqlite:///./test.db
   python init_db.py
   uvicorn main:app --reload
   ```

3. **Frontend Setup**
   ```bash
   cd frontend
   npm install
   cp .env.example .env.local
   # Edit .env.local to match your backend API URL
   # VITE_API_URL=http://localhost:8000
   npm run dev
   ```

4. **Access the Application**
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

## 🧪 Testing

### Run All Tests
```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```
