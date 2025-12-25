# Docker Setup Guide

Complete guide for running the application using Docker, including development and production setups.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Development Setup](#development-setup)
- [Production Setup](#production-setup)
- [Services Overview](#services-overview)
- [Environment Configuration](#environment-configuration)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Software
- Docker 24.0+
- Docker Compose 2.0+
- Git

### System Requirements
- **Memory**: 4GB RAM minimum, 8GB recommended
- **Storage**: 10GB free space minimum
- **CPU**: 2 cores minimum, 4 cores recommended

### Installation
```bash
# Install Docker (Ubuntu/Debian)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker --version
docker-compose --version
```

## Quick Start

### 1. Clone Repository
```bash
git clone <repository-url>
cd <project-directory>
```

### 2. Environment Setup
```bash
# Copy environment files
cp .env.example .env
cp backend/.env.example backend/.env

# Edit environment variables (see Environment Configuration section)
nano .env
nano backend/.env
```

### 3. Start All Services
```bash
# Start all services in development mode
docker-compose up -d

# Or use the startup script
./docker-start.sh
```

### 4. Verify Setup
```bash
# Check all services are running
docker-compose ps

# Check logs
docker-compose logs -f

# Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

## Development Setup

### Docker Compose Configuration
The `docker-compose.yml` file defines all services:

```yaml
version: '3.8'

services:
  # PostgreSQL Database
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init-scripts:/docker-entrypoint-initdb.d
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Redis Cache
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Kafka Message Broker
  kafka:
    image: confluentinc/cp-kafka:latest
    depends_on:
      - zookeeper
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://localhost:9092
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
    ports:
      - "9092:9092"

  # Zookeeper (for Kafka)
  zookeeper:
    image: confluentinc/cp-zookeeper:latest
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
      ZOOKEEPER_TICK_TIME: 2000

  # Backend API
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    environment:
      - DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}
      - REDIS_URL=redis://redis:6379
      - KAFKA_BOOTSTRAP_SERVERS=kafka:9092
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app
      - backend_uploads:/app/uploads
    command: >
      sh -c "
        alembic upgrade head &&
        uvicorn main:app --host 0.0.0.0 --port 8000 --reload
      "

  # Frontend
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    depends_on:
      - backend
    ports:
      - "3000:3000"
    volumes:
      - ./frontend:/app
      - /app/node_modules
    environment:
      - REACT_APP_API_URL=http://localhost:8000

volumes:
  postgres_data:
  redis_data:
  backend_uploads:
```

### Development Commands

#### Start Services
```bash
# Start all services
docker-compose up -d

# Start specific service
docker-compose up -d postgres redis

# Start with logs
docker-compose up
```

#### Stop Services
```bash
# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v

# Stop specific service
docker-compose stop backend
```

#### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend

# Last 100 lines
docker-compose logs --tail=100 backend
```

#### Execute Commands
```bash
# Run command in backend container
docker-compose exec backend python manage.py migrate

# Open shell in backend container
docker-compose exec backend bash

# Run one-time command
docker-compose run --rm backend alembic upgrade head
```

#### Database Operations
```bash
# Run migrations
docker-compose exec backend alembic upgrade head

# Create new migration
docker-compose exec backend alembic revision --autogenerate -m "Description"

# Access PostgreSQL
docker-compose exec postgres psql -U ${POSTGRES_USER} -d ${POSTGRES_DB}

# Backup database
docker-compose exec postgres pg_dump -U ${POSTGRES_USER} ${POSTGRES_DB} > backup.sql

# Restore database
docker-compose exec -T postgres psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} < backup.sql
```

### Hot Reloading
Development setup includes hot reloading:

- **Backend**: FastAPI auto-reloads on code changes
- **Frontend**: React development server with hot module replacement
- **Database**: Persistent data with volume mounts

## Production Setup

### Production Docker Compose
Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 30s
      timeout: 10s
      retries: 3

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3

  kafka:
    image: confluentinc/cp-kafka:latest
    depends_on:
      - zookeeper
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:9092
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
    restart: unless-stopped

  zookeeper:
    image: confluentinc/cp-zookeeper:latest
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
      ZOOKEEPER_TICK_TIME: 2000
    restart: unless-stopped

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    environment:
      - DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}
      - REDIS_URL=redis://redis:6379
      - KAFKA_BOOTSTRAP_SERVERS=kafka:9092
      - ENVIRONMENT=production
    volumes:
      - backend_uploads:/app/uploads
      - backend_logs:/app/logs
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.prod
    depends_on:
      - backend
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
      - backend_uploads:/var/www/uploads
    depends_on:
      - backend
      - frontend
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
  backend_uploads:
  backend_logs:
```

### Production Dockerfile (Backend)
Create `backend/Dockerfile.prod`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["gunicorn", "main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
```

### Production Frontend Dockerfile
Create `frontend/Dockerfile.prod`:

```dockerfile
# Build stage
FROM node:18-alpine as build

WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

COPY . .
RUN npm run build

# Production stage
FROM nginx:alpine

COPY --from=build /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

### Production Deployment
```bash
# Build and start production services
docker-compose -f docker-compose.prod.yml up -d --build

# Run migrations
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head

# Check status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f
```

## Services Overview

### PostgreSQL Database
- **Port**: 5432
- **Purpose**: Primary data storage
- **Health Check**: `pg_isready`
- **Data Persistence**: `postgres_data` volume

**Connection:**
```bash
# From host
psql -h localhost -p 5432 -U ${POSTGRES_USER} -d ${POSTGRES_DB}

# From container
docker-compose exec postgres psql -U ${POSTGRES_USER} -d ${POSTGRES_DB}
```

### Redis Cache
- **Port**: 6379
- **Purpose**: Caching, session storage, task queue
- **Health Check**: `redis-cli ping`
- **Data Persistence**: `redis_data` volume

**Connection:**
```bash
# From host
redis-cli -h localhost -p 6379

# From container
docker-compose exec redis redis-cli
```

### Kafka Message Broker
- **Port**: 9092
- **Purpose**: Event streaming, async messaging
- **Dependencies**: Zookeeper
- **Topics**: Auto-created as needed

**Testing:**
```bash
# List topics
docker-compose exec kafka kafka-topics --bootstrap-server localhost:9092 --list

# Create topic
docker-compose exec kafka kafka-topics --bootstrap-server localhost:9092 --create --topic test-topic

# Produce messages
docker-compose exec kafka kafka-console-producer --bootstrap-server localhost:9092 --topic test-topic

# Consume messages
docker-compose exec kafka kafka-console-consumer --bootstrap-server localhost:9092 --topic test-topic --from-beginning
```

### Backend API
- **Port**: 8000
- **Framework**: FastAPI
- **Auto-reload**: Enabled in development
- **Health Check**: `/health` endpoint

**Endpoints:**
- API Documentation: http://localhost:8000/docs
- Health Check: http://localhost:8000/health
- Metrics: http://localhost:8000/metrics

### Frontend
- **Port**: 3000
- **Framework**: React
- **Hot Reload**: Enabled in development
- **Build**: Static files served by Nginx in production

## Environment Configuration

This section details how to configure environment variables for the Docker Compose setup.

### File Structure

The project uses `.env` files to manage environment variables for different parts of the application.

- **`banwee/`**
  - `docker-compose.yml`
  - **`backend/`**
    - `.env`: Backend environment variables
    - `.env.example`: Backend example configuration
  - **`frontend/`**
    - `.env`: Frontend environment variables
    - `.env.example`: Frontend example configuration

### Setup Process

1.  **Copy Example Files**:
    Before running the application, you need to create your own `.env` files by copying the provided examples:
    ```bash
    cp backend/.env.example backend/.env
    cp frontend/.env.example frontend/.env
    ```

2.  **Update Configuration**:
    Edit the newly created `.env` files with your actual values for secrets, API keys, and other settings.

### Main Environment File (`.env`)
```bash
# Database Configuration
POSTGRES_DB=myapp
POSTGRES_USER=myuser
POSTGRES_PASSWORD=mypassword

# Redis Configuration
REDIS_URL=redis://redis:6379

# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS=kafka:9092

# Application Settings
ENVIRONMENT=development
DEBUG=true
SECRET_KEY=your-secret-key-here

# External Services
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
EMAIL_SMTP_HOST=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_USERNAME=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
```

### Backend Environment File (`backend/.env`)
```bash
# Database
DATABASE_URL=postgresql://myuser:mypassword@postgres:5432/myapp

# Redis
REDIS_URL=redis://redis:6379

# Kafka
KAFKA_BOOTSTRAP_SERVERS=kafka:9092

# Security
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-here
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=30

# External APIs
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# File Storage
UPLOAD_DIR=/app/uploads
MAX_FILE_SIZE=10485760  # 10MB

# Logging
LOG_LEVEL=INFO
LOG_FILE=/app/logs/app.log
```

### Frontend Environment File (`frontend/.env`)
```bash
# API Configuration
REACT_APP_API_URL=http://localhost:8000
REACT_APP_WS_URL=ws://localhost:8000/ws

# Stripe
REACT_APP_STRIPE_PUBLISHABLE_KEY=pk_test_...

# Features
REACT_APP_ENABLE_ANALYTICS=true
REACT_APP_ENABLE_NOTIFICATIONS=true

# Build Configuration
GENERATE_SOURCEMAP=false
```

### Service Connections

The connection URLs for services differ based on the environment:

-   **Development (`ENVIRONMENT=local`)**:
    -   Database: `localhost:5432`
    -   Redis: `localhost:6379`
    -   Kafka: `localhost:9092`
-   **Production (`ENVIRONMENT=production`)**:
    -   Database: `postgres:5432` (using the Docker service name)
    -   Redis: `redis:6379` (using the Docker service name)
    -   Kafka: `kafka:29092` (using the Docker service name)

### Security Considerations

-   **Never commit `.env` files** to version control.
-   Use strong, unique secrets for all production environments.
-   Rotate API keys and other credentials regularly.
-   Use test Stripe keys for development and live keys for production.

### Validation

The application automatically validates environment variables on startup. You can also run the validation script manually:

```bash
python backend/validate_environment.py
```

## Monitoring and Logging

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service with timestamps
docker-compose logs -f -t backend

# Filter logs
docker-compose logs backend | grep ERROR

# Export logs
docker-compose logs --no-color backend > backend.log
```

### Monitor Resources
```bash
# Container stats
docker stats

# Service-specific stats
docker stats $(docker-compose ps -q backend)

# Disk usage
docker system df

# Clean up unused resources
docker system prune -a
```

### Health Checks
```bash
# Check service health
docker-compose ps

# Manual health check
curl http://localhost:8000/health

# Database health
docker-compose exec postgres pg_isready -U ${POSTGRES_USER}

# Redis health
docker-compose exec redis redis-cli ping
```

## Backup and Restore

### Database Backup
```bash
# Create backup
docker-compose exec postgres pg_dump -U ${POSTGRES_USER} ${POSTGRES_DB} > backup_$(date +%Y%m%d_%H%M%S).sql

# Automated backup script
#!/bin/bash
BACKUP_DIR="./backups"
mkdir -p $BACKUP_DIR
docker-compose exec postgres pg_dump -U ${POSTGRES_USER} ${POSTGRES_DB} > $BACKUP_DIR/backup_$(date +%Y%m%d_%H%M%S).sql
```

### Database Restore
```bash
# Restore from backup
docker-compose exec -T postgres psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} < backup.sql

# Or restore with docker run
docker run --rm -i postgres:15 psql -h host.docker.internal -U ${POSTGRES_USER} -d ${POSTGRES_DB} < backup.sql
```

### Volume Backup
```bash
# Backup volumes
docker run --rm -v postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_data.tar.gz -C /data .

# Restore volumes
docker run --rm -v postgres_data:/data -v $(pwd):/backup alpine tar xzf /backup/postgres_data.tar.gz -C /data
```

## Troubleshooting

### Common Issues

#### 1. Port Already in Use
```bash
# Find process using port
lsof -i :8000

# Kill process
kill -9 <PID>

# Or change port in docker-compose.yml
ports:
  - "8001:8000"  # Use different host port
```

#### 2. Database Connection Issues
```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# Check logs
docker-compose logs postgres

# Test connection
docker-compose exec postgres pg_isready -U ${POSTGRES_USER}

# Reset database
docker-compose down -v
docker-compose up -d postgres
```

#### 3. Permission Issues
```bash
# Fix file permissions
sudo chown -R $USER:$USER .

# Fix Docker permissions
sudo usermod -aG docker $USER
newgrp docker
```

#### 4. Out of Memory
```bash
# Check memory usage
docker stats

# Increase Docker memory limit
# Docker Desktop: Settings > Resources > Memory

# Clean up unused containers
docker system prune -a
```

#### 5. Build Failures
```bash
# Clean build cache
docker-compose build --no-cache

# Remove old images
docker image prune -a

# Rebuild specific service
docker-compose build --no-cache backend
```

### Debugging Commands

#### Container Inspection
```bash
# Inspect container
docker inspect <container_name>

# Check environment variables
docker-compose exec backend env

# Check running processes
docker-compose exec backend ps aux

# Check disk space
docker-compose exec backend df -h
```

#### Network Issues
```bash
# List networks
docker network ls

# Inspect network
docker network inspect <network_name>

# Test connectivity
docker-compose exec backend ping postgres
docker-compose exec backend telnet redis 6379
```

#### Performance Issues
```bash
# Monitor resource usage
docker stats

# Check container logs for errors
docker-compose logs backend | grep -i error

# Profile application
docker-compose exec backend python -m cProfile -o profile.stats main.py
```

### Recovery Procedures

#### Complete Reset
```bash
# Stop all services
docker-compose down -v

# Remove all containers and images
docker system prune -a

# Remove volumes (WARNING: This deletes all data)
docker volume prune

# Restart from scratch
docker-compose up -d --build
```

#### Service-Specific Reset
```bash
# Reset backend only
docker-compose stop backend
docker-compose rm -f backend
docker-compose build --no-cache backend
docker-compose up -d backend
```

## Performance Optimization

### Production Optimizations
```yaml
# docker-compose.prod.yml optimizations
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '0.5'
        reservations:
          memory: 512M
          cpus: '0.25'
    
  postgres:
    command: >
      postgres
      -c max_connections=100
      -c shared_buffers=256MB
      -c effective_cache_size=1GB
      -c maintenance_work_mem=64MB
      -c checkpoint_completion_target=0.9
      -c wal_buffers=16MB
      -c default_statistics_target=100
```

### Scaling Services
```bash
# Scale backend service
docker-compose up -d --scale backend=3

# Use load balancer (nginx)
# Configure upstream in nginx.conf
upstream backend {
    server backend_1:8000;
    server backend_2:8000;
    server backend_3:8000;
}
```

This guide covers comprehensive Docker setup for both development and production environments. For specific deployment scenarios or advanced configurations, refer to the Docker and Docker Compose documentation.