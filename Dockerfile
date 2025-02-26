# Use slim Python image for smaller footprint
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install git -y --no-install-recommends \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Copy requirements first (for better caching)
COPY requirements.txt .

# Install Python dependencies with specific optimizations
RUN pip install --no-cache-dir -r requirements.txt

# Create necessary directories
RUN mkdir -p temp static logs

# Copy application code
COPY . .

# Expose the port
EXPOSE 8000

# Run with Hypercorn (as seen in your restart_server.sh)
CMD ["hypercorn", "main:app", "--bind", "0.0.0.0:8000", "--worker-class", "uvloop", "--workers", "2"]