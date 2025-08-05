# A2A Math Operations Agent
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the agent code and package files
COPY src/ ./src/
COPY scripts/ ./scripts/
COPY pyproject.toml .
COPY docker_entrypoint.py .

# Install the package in development mode
RUN pip install -e .

# Create non-root user (after installs are complete)
RUN useradd --create-home --user-group appuser
USER appuser

# Set environment variables
ENV PYTHONPATH=/app
ENV A2A_PORT=8002
ENV HOST=0.0.0.0
ENV LLM_PROVIDER=none

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8002/.well-known/agent-card || exit 1

# Expose port
EXPOSE 8002

# Command to run the agent
CMD ["python", "docker_entrypoint.py"]