FROM python:3.12-slim

WORKDIR /app

# Install system dependencies if needed
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY config/ ./config/
COPY examples/ ./examples/

# Create data directory for blockchain storage
RUN mkdir -p /app/data

# Expose default port (will be overridden in docker-compose)
EXPOSE 8080

# Default command (will be overridden in docker-compose)
CMD ["python", "src/node.py", "--config", "config/node1.json"]