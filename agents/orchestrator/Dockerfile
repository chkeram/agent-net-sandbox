# Multi-stage build for production-ready orchestrator
FROM python:3.11-slim as builder

# Set build arguments
ARG BUILD_ENV=production

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /build

# Copy requirements
COPY requirements.txt .
COPY requirements-dev.txt .

# Create wheels
RUN pip install --upgrade pip wheel
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /build/wheels -r requirements.txt

# If development build, also include dev dependencies
RUN if [ "$BUILD_ENV" = "development" ] ; then \
    pip wheel --no-cache-dir --no-deps --wheel-dir /build/wheels -r requirements-dev.txt ; \
    fi

# Production stage
FROM python:3.11-slim

# Set build arguments
ARG BUILD_ENV=production

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Create app directory and user
RUN groupadd -r orchestrator && useradd -r -g orchestrator -d /app -s /bin/bash orchestrator
WORKDIR /app

# Copy wheels from builder stage
COPY --from=builder /build/wheels /wheels

# Install Python packages
RUN pip install --no-cache /wheels/* && rm -rf /wheels

# Create necessary directories
RUN mkdir -p /app/logs /app/data && \
    chown -R orchestrator:orchestrator /app

# Copy application code
COPY --chown=orchestrator:orchestrator src/ ./src/
COPY --chown=orchestrator:orchestrator pyproject.toml ./
COPY --chown=orchestrator:orchestrator .env.example ./.env

# Switch to non-root user
USER orchestrator

# Set environment variables
ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose ports
EXPOSE 8000 9090

# Run application
CMD ["uvicorn", "orchestrator.app:app", "--host", "0.0.0.0", "--port", "8000"]