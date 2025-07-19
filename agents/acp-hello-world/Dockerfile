# Use Python 3.11 slim image for smaller size
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better Docker layer caching
COPY requirements.txt .
COPY pyproject.toml .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY src/ ./src/
COPY agent-manifest.yaml .
COPY acp-descriptor.json .

# Create a non-root user for security
RUN adduser --disabled-password --gecos '' --shell /bin/bash agentuser \
    && chown -R agentuser:agentuser /app
USER agentuser

# Expose the port the app runs on
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Set the Python path
ENV PYTHONPATH=/app/src

# Command to run the application
CMD ["python", "-m", "uvicorn", "hello_agent.app:app", "--host", "0.0.0.0", "--port", "8000"]