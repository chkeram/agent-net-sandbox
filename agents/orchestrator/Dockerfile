# Multi-Protocol Agent Orchestrator Dockerfile
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

# Create wheels
RUN pip install --upgrade pip wheel
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /build/wheels -r requirements.txt

# Production stage
FROM python:3.11-slim

# Set build arguments
ARG BUILD_ENV=production

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    ca-certificates \
    netbase \
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
COPY --chown=orchestrator:orchestrator scripts/ ./scripts/
COPY --chown=orchestrator:orchestrator pyproject.toml ./

# Copy environment configuration
COPY --chown=orchestrator:orchestrator .env ./.env

# Set container labels for agent discovery
LABEL agent.protocol="orchestrator" \
      agent.type="orchestrator" \
      agent.name="Multi-Protocol Agent Orchestrator" \
      agent.version="0.1.0" \
      agent.port="8004" \
      agent.capabilities="routing,discovery,management" \
      maintainer="Agent Network Sandbox"

# Switch to non-root user
USER orchestrator

# Set environment variables
ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV ORCHESTRATOR_HOST=0.0.0.0
ENV ORCHESTRATOR_PORT=8004
ENV ORCHESTRATOR_ENVIRONMENT=production
ENV ORCHESTRATOR_LOG_LEVEL=INFO
ENV ORCHESTRATOR_DEBUG=false

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8004/health || exit 1

# Expose orchestrator port
EXPOSE 8004

# Run the orchestrator application
CMD ["python", "-m", "orchestrator.main"]