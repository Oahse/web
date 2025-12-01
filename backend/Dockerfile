# Use Alpine Python for smaller image size
FROM python:3.11-alpine

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apk add --no-cache \
    gcc \
    musl-dev \
    postgresql-dev \
    libffi-dev \
    openssl-dev \
    cargo \
    rust \
    curl

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Make migration script executable
RUN chmod +x migrate.sh

# Set Python path
ENV PYTHONPATH=/app
ENV POSTGRES_DB_URL=postgresql+asyncpg://banwee:banwee_password@postgres:5432/banwee_db

# Expose port
EXPOSE 8000

# Run migrations and start server
CMD ["sh", "-c", "./migrate.sh && uvicorn main:app --host 0.0.0.0 --port 8000"]
