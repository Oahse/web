# Use a lightweight Python base image
FROM python:3.11-slim-buster

# Set the working directory in the container
WORKDIR /app

# Copy only the requirements file first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Command to run the negotiator consumer worker
CMD ["python", "consumer_worker.py"]
