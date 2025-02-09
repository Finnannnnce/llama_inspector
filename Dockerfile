# Use Python 3.11 slim image as base
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create necessary directories
RUN mkdir -p /app/.cache /app/config /app/docs

# Copy source code and configurations
COPY main.py /app/
COPY src/ /app/src/
COPY contracts/ /app/contracts/
COPY config/ /app/config/
COPY docs/ /app/docs/

# Set cache directory permissions
RUN chmod -R 777 /app/.cache

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Create non-root user
RUN useradd -m appuser && \
    chown -R appuser:appuser /app
USER appuser

# Set default command
CMD ["python", "main.py"]