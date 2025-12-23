# Use a lightweight Python base image
FROM python:3.11-slim-bookworm

# Set the working directory in the container
WORKDIR /app

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

# Command to run the scheduler
CMD ["python", "main.py"]
