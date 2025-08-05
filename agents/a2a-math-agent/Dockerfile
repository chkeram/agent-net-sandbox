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

# Copy the agent code
COPY math_agent.py .
COPY test_agent.py .

# Create non-root user
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
CMD ["python", "math_agent.py"]