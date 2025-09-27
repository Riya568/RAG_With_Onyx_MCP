FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY backend/requirements/ ./requirements/
RUN pip install --no-cache-dir -r requirements/default.txt

# Copy application code
COPY backend/ .

# Set environment variables
ENV PYTHONPATH=/app
ENV FILE_STORE_TYPE=gcp

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Run the application
CMD ["python", "onyx/main.py"]
