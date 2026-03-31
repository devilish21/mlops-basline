# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Expose port
EXPOSE 8000

# Set environment variables
ENV API_KEY="enterprise-secret-key"
ENV PYTHONPATH="/app"
ENV PYTHONUNBUFFERED=1

# Direct Uvicorn execution (DevOps-friendly for K8s logs and scaling)
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--log-config", "src/logger_config.json"]
