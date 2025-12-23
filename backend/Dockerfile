# Use Alpine Python for smaller image size
FROM python:3.11-alpine

# Set working directory inside the container
WORKDIR /app

# Install system dependencies required for building Python packages (e.g., psycopg2-binary)
# and for other utilities like curl (used in healthchecks).
RUN apk add --no-cache \
    gcc \
    musl-dev \
    postgresql-dev \
    libffi-dev \
    openssl-dev \
    cargo \
    rust \
    curl \
    python3-dev \
    linux-headers \
    librdkafka-dev

# Copy Python dependency requirements file
COPY requirements.txt .

# Install Python dependencies using pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire backend application code into the container
COPY . .

# Make the migration script executable
RUN chmod +x migrate.sh

# Set Python path to include the /app directory, allowing Python to find modules
ENV PYTHONPATH=/app/backend
# Explicitly set the PostgreSQL database URL for the backend application.
# This uses the 'postgres' service name for inter-container communication within Docker.
ENV POSTGRES_DB_URL=postgresql+asyncpg://banwee:banwee_password@postgres:5432/banwee_db

# Explicitly set PATH to ensure executables like uvicorn are found
ENV PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:$PATH"

# Expose port 8000, which is where the FastAPI application will listen
EXPOSE 8000

# Command to run when the container starts:
# 1. Execute database migrations (./migrate.sh).
# 2. Start the Uvicorn server for the FastAPI application.
CMD ["sh", "-c", "./migrate.sh && python -m uvicorn main:app --host 0.0.0.0 --port 8000"]