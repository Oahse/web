# Use a lightweight Python base image
FROM python:3.11-slim-bookworm

# Set the working directory in the container
WORKDIR /app

# Install system dependencies required for building Python packages (e.g., asyncpg)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy only the requirements file first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the core directory
COPY core core/

# Copy the rest of the application code
COPY . .

# Set Python path to include the /app directory, allowing Python to find modules
ENV PYTHONPATH=/app

# Command to run the negotiator consumer worker
CMD ["python", "consumer_worker.py"]
